# Site Management Plane — M2.2 (Write CLI verbs) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Finish the agent write CLI — the verbs deferred from M2 core: a general product-field edit, `add-plugin`, `upload-shot`, and `story`, all on a format-preserving JSON editor and behind the same guarded-validate flow.

**Architecture:** Extend `scripts/site.py` with two format-preserving editor primitives — `set_field_in_text` (scoped scalar swap) and `array_append_in_text` (handles empty + non-empty arrays) — verified to produce minimal, valid-JSON diffs. Verbs wrap them in `guarded_apply`. Contracts come from the admin (`admin/app.jsx`), not assumption.

**Tech Stack:** Python 3.12 stdlib; pytest.

**Verified contracts:**
- New product skeleton (admin/app.jsx:77): `{ id, title, tagline, description, tags: [], status: "wip", repo, npm, install, screenshots: [] }`.
- Screenshot file path (app.jsx:655): `assets/screenshots/<id>/<Date.now()>-<slug>.<ext>`, slug = lowercased, `[^a-z0-9]+`→`-`, trimmed.
- Screenshot array element (app.jsx:659): `{ id: "shot-<ts>-<rand>", path, name, size }`. Max 6 (app.jsx:633).
- **No thumbnail** — the admin doesn't thumbnail screenshots; neither do we.
- `render_product_visual` uses `banner`, NOT `screenshots` (render-hub.py:443) — so registering a screenshot does not change `index.html`; the doctor's asset-existence check enforces the copied file exists.

**Spec:** `docs/superpowers/specs/2026-05-23-site-management-plane-design.md` §Milestone 2.

---

## Task 1: Editor primitives (pure-testable)

**Files:** Modify `scripts/site.py`; Modify `tests/test_site_cli.py`

- [ ] **Step 1: Write failing tests** (append to `tests/test_site_cli.py`)
```python
ARR_NONEMPTY = '{\n  "family": [\n    { "id": "a" },\n    { "id": "b" }\n  ]\n}\n'
ARR_EMPTY = '{\n  "items": []\n}\n'


def test_array_append_nonempty_is_valid_and_additive():
    out = site_cli.array_append_in_text(ARR_NONEMPTY, "family", '{ "id": "c" }')
    import json
    data = json.loads(out)
    assert [e["id"] for e in data["family"]] == ["a", "b", "c"]
    # the "b" line gains a comma; "a" untouched
    assert '{ "id": "a" }' in out


def test_array_append_empty_array():
    out = site_cli.array_append_in_text(ARR_EMPTY, "items", '{ "id": "x" }')
    import json
    assert json.loads(out)["items"] == [{"id": "x"}]


def test_set_field_in_text_scoped():
    sample = ('{ "products": [\n'
              '  { "id": "p1", "tagline": "old" },\n'
              '  { "id": "p2", "tagline": "keep" }\n] }\n')
    out = site_cli.set_field_in_text(sample, "p1", "tagline", "new")
    assert '"tagline": "new"' in out
    assert '"tagline": "keep"' in out  # p2 untouched
    assert out.count('"tagline"') == 2


def test_set_field_in_text_missing_field_raises():
    import pytest
    sample = '{ "products": [ { "id": "p1", "tagline": "x" } ] }\n'
    with pytest.raises(ValueError):
        site_cli.set_field_in_text(sample, "p1", "nope", "y")
```

- [ ] **Step 2: Run, verify fail.**

- [ ] **Step 3: Implement primitives** (in `scripts/site.py`, after `set_status_in_text`)
```python
def _product_block_span(text: str, product_id: str) -> tuple[int, int]:
    """(start, end) char span of a product object, bounded by the next id."""
    m = re.search(r'"id":\s*"' + re.escape(product_id) + r'"', text)
    if not m:
        raise ValueError(f"product not found: {product_id}")
    start = m.end()
    nxt = re.search(r'"id":\s*"', text[start:])
    end = start + nxt.start() if nxt else len(text)
    return start, end


def set_field_in_text(text: str, product_id: str, field: str, new_value: str) -> str:
    """Replace a product's string field value in place, preserving formatting."""
    start, end = _product_block_span(text, product_id)
    block = text[start:end]
    pat = re.compile(r'("' + re.escape(field) + r'":\s*")([^"]*)(")')
    new_block, n = pat.subn(r"\g<1>" + new_value.replace("\\", "\\\\") + r"\g<3>",
                            block, count=1)
    if n != 1:
        raise ValueError(f"string field '{field}' not found for {product_id}")
    return text[:start] + new_block + text[end:]


def array_append_in_text(text: str, array_key: str, element_text: str,
                         search_from: int = 0) -> str:
    """Append element_text to the named array, preserving formatting. Handles
    empty and non-empty arrays. Returns format-preserving, valid JSON."""
    m = re.search(r'"' + re.escape(array_key) + r'":\s*\[', text[search_from:])
    if not m:
        raise ValueError(f"array not found: {array_key}")
    open_idx = search_from + m.end()
    depth, i = 1, open_idx
    while depth:
        c = text[i]
        depth += (c == "[") - (c == "]")
        i += 1
    close = i - 1
    inner = text[open_idx:close]
    line_start = text.rfind("\n", 0, close) + 1
    array_indent = text[line_start:close]
    elem_indent = array_indent + "  "
    if inner.strip() == "":          # empty array
        return text[:open_idx] + "\n" + elem_indent + element_text + "\n" + array_indent + text[close:]
    before = text[:close].rstrip()   # non-empty: comma after prev last element
    return before + ",\n" + elem_indent + element_text + "\n" + array_indent + text[close:]
```

- [ ] **Step 4: Run, verify pass.**

- [ ] **Step 5: Commit**
```bash
git add scripts/site.py tests/test_site_cli.py
git commit -m "feat(cli): format-preserving editor primitives (array append, field set)"
```

---

## Task 2: `set-product` (and fold in set-status)

**Files:** Modify `scripts/site.py`

- [ ] **Step 1: Add the verb** (append a `cmd_set_product`)
```python
def cmd_set_product(args) -> int:
    data = json.loads(SITE_JSON.read_text(encoding="utf-8"))
    product = next((p for p in data.get("products", []) if p.get("id") == args.id), None)
    if product is None:
        print(f"no product with id: {args.id}", file=sys.stderr)
        return 2
    if str(product.get(args.field)) == args.value:
        print(f"{args.id}.{args.field} is already '{args.value}' — no change.")
        return 0
    text = SITE_JSON.read_text(encoding="utf-8")
    try:
        new_text = set_field_in_text(text, args.id, args.field, args.value)
    except ValueError as e:
        print(f"cannot set {args.id}.{args.field}: {e}", file=sys.stderr)
        return 2
    ok, detail = guarded_apply(SITE_JSON, new_text)
    if not ok:
        print(f"refused: {args.id}.{args.field} -> {args.value} fails the doctor:\n{detail}",
              file=sys.stderr)
        return 1
    print(f"set {args.id}.{args.field} -> {args.value} (validated).")
    return _maybe_commit(args, f"content: set {args.id} {args.field}")
```
And extract the commit tail used by set-status/set-product into a helper:
```python
def _maybe_commit(args, message, paths=("content/site.json", "index.html")) -> int:
    if getattr(args, "commit", False):
        if _on_main():
            print("refusing to commit on main — switch to a branch.", file=sys.stderr)
            return 1
        subprocess.run(["git", "add", *paths], check=True)
        subprocess.run(["git", "commit", "-m", message], check=True)
        print("committed.")
    return 0
```
Update `cmd_set_status` to end with `return _maybe_commit(args, f"content: set {args.id} status to {args.status}")` (replace its inline commit block).

- [ ] **Step 2: Register in `build_parser`**
```python
    sp = sub.add_parser("set-product", help="set a product string field (guarded)")
    sp.add_argument("id"); sp.add_argument("field"); sp.add_argument("value")
    sp.add_argument("--commit", action="store_true")
    sp.set_defaults(fn=cmd_set_product)
```

- [ ] **Step 3: Smoke test**
```bash
python scripts/site.py set-product vibe-cartographer tagline "Vibe coding with a map."   # no-op
python scripts/site.py set-product vibe-cartographer tagline "Vibe coding, mapped."        # change
git diff --stat content/site.json    # 1 line
git checkout -- content/site.json index.html
```

- [ ] **Step 4: Commit**
```bash
git add scripts/site.py
git commit -m "feat(cli): set-product guarded field edit; share commit helper"
```

---

## Task 3: `add-plugin`

**Files:** Modify `scripts/site.py`; Modify `tests/test_site_cli.py`

- [ ] **Step 1: Test the skeleton builder** (append)
```python
def test_product_skeleton_shape():
    el = site_cli.product_skeleton("vibe-demo", "Vibe Demo", "A demo.", claude_code=True)
    import json
    obj = json.loads(el)
    assert obj == {
        "id": "vibe-demo", "title": "Vibe Demo", "tagline": "A demo.",
        "description": "", "tags": [], "status": "wip",
        "repo": "", "npm": "", "install": "", "claudeCode": True, "screenshots": [],
    }
```

- [ ] **Step 2: Implement** (in `scripts/site.py`)
```python
def product_skeleton(pid: str, title: str, tagline: str, claude_code: bool) -> str:
    obj = {
        "id": pid, "title": title, "tagline": tagline, "description": "",
        "tags": [], "status": "wip", "repo": "", "npm": "", "install": "",
        "claudeCode": claude_code, "screenshots": [],
    }
    return json.dumps(obj, ensure_ascii=False)


def cmd_add_plugin(args) -> int:
    data = json.loads(SITE_JSON.read_text(encoding="utf-8"))
    if any(p.get("id") == args.id for p in data.get("products", [])):
        print(f"product id already exists: {args.id}", file=sys.stderr)
        return 2
    text = SITE_JSON.read_text(encoding="utf-8")
    element = product_skeleton(args.id, args.title, args.tagline or "",
                              claude_code=args.claude_code)
    new_text = array_append_in_text(text, "products", element)
    ok, detail = guarded_apply(SITE_JSON, new_text)
    if not ok:
        print(f"refused: add-plugin {args.id} fails the doctor:\n{detail}", file=sys.stderr)
        return 1
    print(f"added product '{args.id}' (status: wip). Fill in description/tags/repo "
          f"next, and create its landing page in content/plugin-pages.json if it's a "
          f"Claude Code plugin.")
    return _maybe_commit(args, f"content: add product {args.id}")
```

- [ ] **Step 3: Register**
```python
    ap2 = sub.add_parser("add-plugin", help="append a skeleton product (guarded)")
    ap2.add_argument("id"); ap2.add_argument("--title", required=True)
    ap2.add_argument("--tagline", default="")
    ap2.add_argument("--claude-code", dest="claude_code", action="store_true")
    ap2.add_argument("--commit", action="store_true")
    ap2.set_defaults(fn=cmd_add_plugin)
```

- [ ] **Step 4: Smoke test (then revert)**
```bash
python scripts/site.py add-plugin vibe-demo --title "Vibe Demo" --tagline "A demo." --claude-code
python -c "import json; print('count', len(json.load(open('content/site.json'))['products']))"  # 16
python scripts/site.py doctor --check ; echo "exit:$?"
git checkout -- content/site.json index.html
```

- [ ] **Step 5: Run suite + commit**
```bash
python -m pytest -q
git add scripts/site.py tests/test_site_cli.py
git commit -m "feat(cli): add-plugin appends a guarded skeleton product"
```

---

## Task 4: `upload-shot`

**Files:** Modify `scripts/site.py`; Modify `tests/test_site_cli.py`

- [ ] **Step 1: Test the slug + element builder** (append)
```python
def test_screenshot_slug():
    assert site_cli.screenshot_slug("My Cool Shot!.PNG") == ("my-cool-shot", ".png")
    assert site_cli.screenshot_slug("x.jpeg") == ("x", ".jpeg")
    assert site_cli.screenshot_slug("....png") == ("shot", ".png")
```

- [ ] **Step 2: Implement** (in `scripts/site.py`)
```python
import shutil
import time

ASSETS = ROOT / "assets"


def screenshot_slug(filename: str) -> tuple[str, str]:
    m = re.search(r"\.[A-Za-z0-9]+$", filename or "")
    ext = (m.group(0) if m else ".png").lower()
    base = re.sub(r"\.[A-Za-z0-9]+$", "", filename or "")
    base = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-") or "shot"
    return base, ext


def cmd_upload_shot(args) -> int:
    src = Path(args.image)
    if not src.exists():
        print(f"image not found: {src}", file=sys.stderr)
        return 2
    data = json.loads(SITE_JSON.read_text(encoding="utf-8"))
    product = next((p for p in data.get("products", []) if p.get("id") == args.id), None)
    if product is None:
        print(f"no product with id: {args.id}", file=sys.stderr)
        return 2
    if "screenshots" not in product:
        print(f"{args.id} has no screenshots field — add it via the admin first.",
              file=sys.stderr)
        return 2
    if len(product["screenshots"]) >= 6:
        print(f"{args.id} already has 6 screenshots — remove one first.", file=sys.stderr)
        return 2
    base, ext = screenshot_slug(src.name)
    ts = int(time.time() * 1000)
    rel = f"assets/screenshots/{args.id}/{ts}-{base}{ext}"
    dest = ROOT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    element = json.dumps(
        {"id": f"shot-{ts}", "path": rel, "name": src.name, "size": dest.stat().st_size},
        ensure_ascii=False,
    )
    text = SITE_JSON.read_text(encoding="utf-8")
    start, end = _product_block_span(text, args.id)
    new_block = array_append_in_text(text[start:end], "screenshots", element)
    new_text = text[:start] + new_block + text[end:]
    ok, detail = guarded_apply(SITE_JSON, new_text)
    if not ok:
        dest.unlink(missing_ok=True)   # roll back the copied file too
        print(f"refused: upload-shot {args.id} fails the doctor:\n{detail}", file=sys.stderr)
        return 1
    print(f"uploaded {rel} and registered on {args.id} (validated).")
    return _maybe_commit(args, f"content: add screenshot to {args.id}",
                         paths=("content/site.json", "index.html", rel))
```

- [ ] **Step 3: Smoke test with a throwaway image (then revert)**
```bash
python -c "from pathlib import Path; Path('/tmp/t.png').write_bytes(b'\\x89PNG\\r\\n\\x1a\\n' + b'0'*64)"
python scripts/site.py upload-shot vibe-cartographer /tmp/t.png
python scripts/site.py doctor --check ; echo "exit:$?"
git checkout -- content/site.json index.html
git clean -fd assets/screenshots/vibe-cartographer/   # remove the test image
```
Expected: registers + doctor passes (file exists). Note: `_product_block_span` is reused so the screenshots array is found inside the right product.

- [ ] **Step 4: Run suite + commit**
```bash
python -m pytest -q
git add scripts/site.py tests/test_site_cli.py
git commit -m "feat(cli): upload-shot — copy + name + register screenshot (guarded)"
```

---

## Task 5: `story new` / `story list`

**Files:** Modify `scripts/site.py`; Modify `tests/test_site_cli.py`

- [ ] **Step 1: Test the slug + frontmatter** (append)
```python
def test_story_frontmatter():
    fm = site_cli.story_scaffold("My First Note")
    assert fm.startswith("---\n")
    assert 'title: "My First Note"' in fm
    assert "## " in fm  # has a body heading stub
```

- [ ] **Step 2: Implement** (in `scripts/site.py`)
```python
STORIES = ROOT / "content" / "stories"


def story_scaffold(title: str) -> str:
    from datetime import date
    return (
        "---\n"
        f'title: "{title}"\n'
        'summary: ""\n'
        f"date: {date.today().isoformat()}\n"
        "---\n\n"
        f"## {title}\n\n"
        "Write the story here.\n"
    )


def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "untitled"


def cmd_story(args) -> int:
    if args.action == "list":
        if not STORIES.exists():
            print("(no stories dir)")
            return 0
        for p in sorted(STORIES.glob("*.md")):
            print(p.name)
        return 0
    # new
    slug = _slugify(args.slug)
    dest = STORIES / f"{slug}.md"
    if dest.exists():
        print(f"story already exists: {dest.relative_to(ROOT)}", file=sys.stderr)
        return 2
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(story_scaffold(args.title or args.slug), encoding="utf-8", newline="\n")
    print(f"created {dest.relative_to(ROOT)} — edit it, then it renders as a Field Note.")
    return 0
```

- [ ] **Step 3: Register**
```python
    st = sub.add_parser("story", help="manage Field Note stories")
    st.add_argument("action", choices=["new", "list"])
    st.add_argument("slug", nargs="?")
    st.add_argument("--title", default="")
    st.set_defaults(fn=cmd_story)
```
Add a guard in `cmd_story`: if `action == "new"` and not `args.slug`, print error + return 2.

- [ ] **Step 4: Smoke test (then revert)**
```bash
python scripts/site.py story list | head
python scripts/site.py story new test-note --title "Test Note"
ls content/stories/test-note.md && rm content/stories/test-note.md
```

- [ ] **Step 5: Run suite + commit**
```bash
python -m pytest -q
git add scripts/site.py tests/test_site_cli.py
git commit -m "feat(cli): story new/list — Field Note scaffolding"
```

---

## Task 6: Docs + PR

**Files:** Modify `AGENTS.md`

- [ ] **Step 1: Update `AGENTS.md`** — move the four verbs out of "Roadmap" into "Write (guarded)":
```markdown
- `python scripts/site.py set-product <id> <field> <value>` — set a product string field.
- `python scripts/site.py add-plugin <id> --title T [--tagline TG] [--claude-code]` — append a skeleton product (status wip).
- `python scripts/site.py upload-shot <product-id> <image>` — copy + name + register a screenshot (max 6).
- `python scripts/site.py story new <slug> --title T` / `story list` — Field Note scaffolding.
```
Replace the Roadmap section with: "Roadmap: the MCP wrapper (M3) exposes these same verbs as `manage_site_content` tools on the Firebase server."

- [ ] **Step 2: Full verify + push + PR**
```bash
python -m pytest -q
python scripts/site-doctor.py --check ; echo "exit:$?"
git add AGENTS.md
git commit -m "docs: AGENTS.md — write verbs promoted out of roadmap"
git push -u origin feat/site-mgmt-m2-2
gh pr create --title "feat: site management plane M2.2 — write CLI verbs" \
  --body "Finishes the agent write CLI: set-product, add-plugin, upload-shot, story — on format-preserving editor primitives (array append + scoped field set), each behind guarded-validate-before-commit. Contracts verified against admin/app.jsx (no thumbnailing; screenshots are stored data render-hub doesn't surface on cards). M3 (MCP wrapper) is next.

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```

---

## Self-review

- **Coverage:** deferred verbs (general set → `set-product`; `add-plugin`; `upload-shot`; `story`) all have tasks. Editor primitives (Task 1) underpin them.
- **Contracts:** product skeleton, screenshot element/naming, max-6, no-thumbnail, banner-not-screenshots — all verified against admin/app.jsx + render-hub.py.
- **Placeholders:** none — full code per step.
- **Type/name consistency:** `set_field_in_text`, `array_append_in_text`, `_product_block_span`, `product_skeleton`, `screenshot_slug`, `story_scaffold`, `_maybe_commit`, `cmd_*` consistent. `array_append_in_text` reused with a sliced product block for nested screenshots arrays.
- **Safety:** every mutation through `guarded_apply` (auto-revert); `upload-shot` also unlinks the copied file on doctor failure; commits refuse on main.
