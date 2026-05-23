# Site Management Plane — M2 (Agent Write CLI) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Give an IDE agent the admin dashboard's powers from the shell — read the site's state and edit it *with guardrails*, so a mutation can't ship drift.

**Architecture:** `scripts/site.py` is an argparse dispatcher over the M1 contract. Read verbs inspect; the mutation verb (`set-status`) does a **format-preserving surgical edit** (no parse→dump — that would explode the hand-formatted JSON), then validates via render + doctor and **auto-reverts** if validation fails. `--commit` is opt-in and refuses on `main`.

**Tech Stack:** Python 3.12 stdlib (`argparse`, `json`, `re`, `subprocess`, `pathlib`); pytest.

**Spec:** `docs/superpowers/specs/2026-05-23-site-management-plane-design.md` §Milestone 2.

**Scope (v1, this PR):** dispatcher + read verbs (`facts`, `get`, `doctor`, `render`, `ops`) + `set-status` (guarded) + `AGENTS.md` + tests.
**Deferred to M2.2:** `set` (arbitrary dotpath), `add-plugin`, `upload-shot`, `story` — all need a format-preserving JSON array/object editor, which is its own focused build.

---

## File structure

| File | Responsibility |
|---|---|
| `scripts/site.py` | **Create.** CLI dispatcher + verbs + guarded-edit core. |
| `AGENTS.md` | **Create.** Declares `python scripts/site.py` the canonical management surface. |
| `tests/test_site_cli.py` | **Create.** Surgical-edit correctness + guarded revert + read-verb smoke. |

---

## Task 1: Surgical edit + guarded-apply core (pure-testable)

**Files:** Create `scripts/site.py`; Test `tests/test_site_cli.py`

- [ ] **Step 1: Write failing tests**

`tests/test_site_cli.py`:
```python
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
_spec = importlib.util.spec_from_file_location("site_cli", ROOT / "scripts" / "site.py")
site_cli = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(site_cli)

SAMPLE = '''{
  "products": [
    {
      "id": "vibe-sec",
      "status": "wip",
      "tags": []
    },
    {
      "id": "vibe-x",
      "status": "live"
    }
  ]
}
'''


def test_set_status_in_text_changes_only_target():
    out = site_cli.set_status_in_text(SAMPLE, "vibe-sec", "live")
    assert '"id": "vibe-sec"' in out
    assert out.count('"status": "live"') == 2   # vibe-sec flipped + vibe-x unchanged
    assert '"status": "wip"' not in out
    # vibe-x block untouched
    assert SAMPLE.split('"id": "vibe-x"')[1] == out.split('"id": "vibe-x"')[1]


def test_set_status_in_text_not_found():
    import pytest
    with pytest.raises(ValueError):
        site_cli.set_status_in_text(SAMPLE, "nope", "live")


def test_guarded_apply_reverts_on_failure(tmp_path):
    f = tmp_path / "src.json"
    f.write_text("ORIGINAL", encoding="utf-8")
    ok, detail = site_cli.guarded_apply(
        f, "MUTATED",
        render_fn=lambda: None,
        validate_fn=lambda: (False, "boom"),
    )
    assert ok is False and "boom" in detail
    assert f.read_text(encoding="utf-8") == "ORIGINAL"   # reverted


def test_guarded_apply_keeps_on_success(tmp_path):
    f = tmp_path / "src.json"
    f.write_text("ORIGINAL", encoding="utf-8")
    ok, _ = site_cli.guarded_apply(
        f, "MUTATED",
        render_fn=lambda: None,
        validate_fn=lambda: (True, ""),
    )
    assert ok is True
    assert f.read_text(encoding="utf-8") == "MUTATED"   # kept
```

- [ ] **Step 2: Run, verify fail** — `python -m pytest tests/test_site_cli.py -v` → module/func not found.

- [ ] **Step 3: Implement the core** (`scripts/site.py`)
```python
#!/usr/bin/env python3
"""site.py — agent-facing management CLI for 626labs.dev.

The agent equivalent of the admin dashboard. Read verbs inspect; mutation verbs
edit content with FORMAT-PRESERVING surgical edits (never parse->dump, which
would explode the hand-formatted JSON), then validate via render + doctor and
auto-revert if the edit would introduce drift.

Verbs:
  facts                       print derived facts
  get <section>               print a section of content/site.json
  doctor [--check]            run the health checkup
  render                      re-render index.html + plugin pages
  ops                         recent CI run status (needs gh)
  set-status <id> <live|wip>  flip a product's status (guarded)

Mutation verbs validate before they stand. Default leaves the validated change
in the working tree; --commit commits on the current branch (refuses on main).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
SITE_JSON = ROOT / "content" / "site.json"
sys.path.insert(0, str(SCRIPTS))
import site_facts  # noqa: E402


def set_status_in_text(text: str, product_id: str, new_status: str) -> str:
    """Replace one product's status value in-place, preserving all formatting.
    Locate the product by id, bound the search by the next id so a sibling is
    never touched, and swap the single status value."""
    id_pat = re.compile(r'"id":\s*"' + re.escape(product_id) + r'"')
    m = id_pat.search(text)
    if not m:
        raise ValueError(f"product not found: {product_id}")
    start = m.end()
    nxt = re.search(r'"id":\s*"', text[start:])
    end = start + nxt.start() if nxt else len(text)
    block = text[start:end]
    new_block, n = re.subn(
        r'("status":\s*")(live|wip)(")',
        r"\g<1>" + new_status + r"\g<3>",
        block,
        count=1,
    )
    if n != 1:
        raise ValueError(f"status field not found for {product_id}")
    return text[:start] + new_block + text[end:]


def render_all() -> None:
    for script in ("render-hub.py", "render-plugin-pages.py"):
        subprocess.run([sys.executable, str(SCRIPTS / script)], check=True,
                       capture_output=True, text=True)


def doctor_validate() -> tuple[bool, str]:
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "site-doctor.py"), "--check"],
        capture_output=True, text=True,
    )
    return r.returncode == 0, r.stdout + r.stderr


def guarded_apply(source_path: Path, new_text: str, *,
                  render_fn=render_all, validate_fn=doctor_validate) -> tuple[bool, str]:
    """Write new_text, render, validate. Revert source + re-render on failure."""
    original = source_path.read_text(encoding="utf-8")
    source_path.write_text(new_text, encoding="utf-8", newline="\n")
    render_fn()
    ok, detail = validate_fn()
    if not ok:
        source_path.write_text(original, encoding="utf-8", newline="\n")
        render_fn()
        return False, detail
    return True, detail
```

- [ ] **Step 4: Run, verify pass** — `python -m pytest tests/test_site_cli.py -v` → 4 pass.

- [ ] **Step 5: Commit**
```bash
git add scripts/site.py tests/test_site_cli.py
git commit -m "feat(cli): format-preserving surgical edit + guarded-apply core"
```

---

## Task 2: Verbs + dispatcher

**Files:** Modify `scripts/site.py`

- [ ] **Step 1: Append the verbs + main**
```python
def _on_main() -> bool:
    r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout.strip() in ("main", "master")


def cmd_facts(_args) -> int:
    print(json.dumps(site_facts.facts(), indent=2, ensure_ascii=False))
    return 0


def cmd_get(args) -> int:
    data = json.loads(SITE_JSON.read_text(encoding="utf-8"))
    if args.section not in data:
        print(f"no such section: {args.section}. available: {', '.join(data)}",
              file=sys.stderr)
        return 2
    print(json.dumps(data[args.section], indent=2, ensure_ascii=False))
    return 0


def cmd_doctor(args) -> int:
    argv = ["--check"] if args.check else ["--report"]
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "site-doctor.py"), *argv]
    ).returncode


def cmd_render(_args) -> int:
    render_all()
    print("rendered index.html + plugin pages.")
    return 0


def cmd_ops(_args) -> int:
    try:
        return subprocess.run(["gh", "run", "list", "--limit", "8"]).returncode
    except FileNotFoundError:
        print("gh CLI not found — install it to see CI run status.", file=sys.stderr)
        return 2


def cmd_set_status(args) -> int:
    data = json.loads(SITE_JSON.read_text(encoding="utf-8"))
    product = next((p for p in data.get("products", []) if p.get("id") == args.id), None)
    if product is None:
        print(f"no product with id: {args.id}", file=sys.stderr)
        return 2
    if product.get("status") == args.status:
        print(f"{args.id} is already '{args.status}' — no change.")
        return 0
    text = SITE_JSON.read_text(encoding="utf-8")
    new_text = set_status_in_text(text, args.id, args.status)
    ok, detail = guarded_apply(SITE_JSON, new_text)
    if not ok:
        print(f"refused: setting {args.id} -> {args.status} fails the doctor:\n{detail}",
              file=sys.stderr)
        return 1
    print(f"set {args.id} status -> {args.status} (validated).")
    if args.commit:
        if _on_main():
            print("refusing to commit on main — switch to a branch.", file=sys.stderr)
            return 1
        subprocess.run(["git", "add", "content/site.json", "index.html"], check=True)
        subprocess.run(["git", "commit", "-m",
                        f"content: set {args.id} status to {args.status}"], check=True)
        print("committed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="site.py", description="626labs.dev management CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("facts", help="print derived facts").set_defaults(fn=cmd_facts)
    g = sub.add_parser("get", help="print a section of site.json"); g.add_argument("section"); g.set_defaults(fn=cmd_get)
    d = sub.add_parser("doctor", help="health checkup"); d.add_argument("--check", action="store_true"); d.set_defaults(fn=cmd_doctor)
    sub.add_parser("render", help="re-render site").set_defaults(fn=cmd_render)
    sub.add_parser("ops", help="recent CI runs (needs gh)").set_defaults(fn=cmd_ops)
    s = sub.add_parser("set-status", help="flip a product's status (guarded)")
    s.add_argument("id"); s.add_argument("status", choices=["live", "wip"])
    s.add_argument("--commit", action="store_true", help="commit on current branch (not main)")
    s.set_defaults(fn=cmd_set_status)
    return ap


def main(argv) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 2: Smoke-test the read verbs**
```bash
python scripts/site.py facts | python -c "import sys,json; d=json.load(sys.stdin); print('plugins', d['claude_plugins'])"
python scripts/site.py get hero >/dev/null && echo "get hero OK"
python scripts/site.py doctor --check ; echo "doctor exit:$?"
python scripts/site.py get nope ; echo "expect exit 2:$?"
```
Expected: `plugins 8`; `get hero OK`; doctor exit 0; nope exit 2.

- [ ] **Step 3: Smoke-test the guarded mutation (no-op + real round-trip)**
```bash
python scripts/site.py set-status vibe-sec wip          # already wip -> no change
python scripts/site.py set-status vibe-sec live         # flip -> validated
git diff --stat content/site.json                       # 1 line changed
python scripts/site.py set-status vibe-sec wip          # flip back
git checkout -- content/site.json index.html            # clean up smoke edits
```
Expected: first prints "already 'wip'"; second "set vibe-sec status -> live (validated)."; diff shows the single status line; revert restores.

- [ ] **Step 4: Add a CLI integration test** (append to `tests/test_site_cli.py`)
```python
def test_cmd_facts_runs(capsys):
    rc = site_cli.main(["facts"])
    out = capsys.readouterr().out
    assert rc == 0 and '"claude_plugins"' in out


def test_cmd_get_unknown_section_errors():
    assert site_cli.main(["get", "definitely-not-a-section"]) == 2
```

- [ ] **Step 5: Run full suite + commit**
```bash
python -m pytest -q
git add scripts/site.py tests/test_site_cli.py
git commit -m "feat(cli): read verbs (facts/get/doctor/render/ops) + guarded set-status"
```

---

## Task 3: AGENTS.md + docs + PR

**Files:** Create `AGENTS.md`; Modify `CLAUDE.md`

- [ ] **Step 1: Create `AGENTS.md`**
```markdown
# Managing this site as an agent

`scripts/site.py` is the agent-facing management surface — the equivalent of the
human admin dashboard. Prefer it over hand-editing content JSON: mutation verbs
validate (render + health doctor) and auto-revert if an edit would ship drift.

## Read
- `python scripts/site.py facts` — derived facts (plugin counts, names, etc.)
- `python scripts/site.py get <section>` — a section of content/site.json
- `python scripts/site.py doctor [--check]` — health checkup
- `python scripts/site.py render` — re-render index.html + plugin pages
- `python scripts/site.py ops` — recent CI run status

## Write (guarded)
- `python scripts/site.py set-status <product-id> <live|wip>` — flip a product's
  status. Validates before it stands; `--commit` commits on the current branch
  (refuses on main).

## Conventions
- Counts/lists in prose use `{{fact:KEY}}` tokens (see scripts/site_facts.py) —
  don't hardcode a number a fact can supply.
- Brand assets in assets/brand/ are generated; don't hand-edit.
- The doctor is the one validator; every write path funnels through it via CI.

Roadmap: add-plugin, upload-shot, story, and general `set` arrive in M2.2 (they
need a format-preserving JSON array/object editor).
```

- [ ] **Step 2: Point CLAUDE.md at it** — under the Tools section add:
```markdown
### Agent management CLI — `scripts/site.py`
The agent equivalent of the admin dashboard. `facts`/`get`/`doctor`/`render`/`ops`
to inspect; `set-status` to mutate with validate-before-commit guardrails. See
`AGENTS.md`.
```

- [ ] **Step 3: Full verify, push, PR**
```bash
python -m pytest -q
python scripts/site-doctor.py --check ; echo "exit:$?"
git add AGENTS.md CLAUDE.md
git commit -m "docs: AGENTS.md — agent management surface + CLAUDE.md pointer"
git push -u origin feat/site-mgmt-m2
gh pr create --title "feat: site management plane M2 — agent write CLI (core)" \
  --body "M2 core: scripts/site.py agent management CLI. Read verbs + guarded set-status (format-preserving surgical edit, validates via render+doctor, auto-reverts on drift). AGENTS.md discoverability. add-plugin/upload-shot/story/set deferred to M2.2 (need a format-preserving JSON array editor).

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```

---

## Self-review

- **Spec coverage:** §M2 verbs — read verbs + guarded mutation pattern + AGENTS.md covered; add-plugin/upload-shot/story/general-set explicitly deferred to M2.2 (documented in AGENTS.md + PR). Guarded mutation flow (apply→render→validate→revert/commit) → Task 1 `guarded_apply` + Task 2 `cmd_set_status`.
- **Placeholder scan:** none — full code in every step.
- **Type/name consistency:** `set_status_in_text`, `render_all`, `doctor_validate`, `guarded_apply`, `cmd_*`, `build_parser`, `main` consistent across tasks. site.py imported in tests via `spec_from_file_location` (hyphen-free module name `site_cli`).
- **Format-preservation:** verified on real data — surgical status edit changes exactly the target line; no parse→dump anywhere.
