# Theme Rotation M1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the monthly theme-rotation machinery and prove it by extracting today's Phosphor Blueprint look as theme #1, with the live homepage rendering byte-identical.

**Architecture:** A theme is `themes/<slug>/{shell.html,tokens.css,theme.json}` — the shell carries the page skeleton and the twelve `SITE_JSON:` zone markers, tokens carry treatment plus layout CSS, and one shared `render-hub.py` fills the zones for any theme. `content/themes.json` is the single switch (active/queue/archive). `theme-doctor.py` gates entry to the queue; a scheduled workflow freezes the outgoing theme to a noindex archive and promotes the next one, committing only if every gate passes. Spec: `docs/superpowers/specs/2026-08-03-theme-rotation-design.md`.

**Tech Stack:** Python 3.11 (renderer, doctor, freezer, pytest), static HTML/CSS, GitHub Actions.

## Global Constraints

- Branch `feat/theme-rotation-m1` from fresh `origin/main`. Trailer on every commit: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`; conventional commits; no emoji.
- **Backward compatibility is absolute:** `python scripts/render-hub.py` with NO flags must behave exactly as today (same output path, same content). Every existing gate keeps passing at every task boundary: `render-hub.py --check` exit 0, `pytest tests/ -q`, `site-doctor.py --report` PASS.
- **The extraction must be byte-identical.** After Task T2, `index.html` rendered from the extracted theme must be byte-for-byte what `origin/main` has. Any diff is a DESIGN FINDING (report it, stop, do not paper over it) — per the spec's named risk, wrong seams mean the design gets revisited, not the implementation ground through.
- The twelve zones that must survive extraction, exactly: `hero`, `hero-chips`, `products`, `lab-pool`, `thinking`, `founding`, `stories`, `lab-runs`, `play`, `about`, `support`, `contact`.
- `site.json` is content and stays theme-agnostic; `themes.json` is presentation state. Never merge them.
- Archives are frozen copies, never re-rendered; they get `noindex` + a dated banner and are excluded from `sitemap.xml` and from lychee link-checking.
- No new runtime dependencies. Standard library plus what the repo already uses.

## File map

| File | Task | Responsibility |
|---|---|---|
| `themes/phosphor-blueprint/{shell.html,tokens.css,theme.json}` | T2 | Today's look, extracted |
| `content/themes.json` | T1 | The registry: active, queue, archive |
| `scripts/theme_registry.py` | T1 | Load/validate/mutate the registry (shared by doctor, freezer, workflow) |
| `scripts/render-hub.py` | T2 | `--theme <slug>` and `--out <dir>`; default path unchanged |
| `scripts/theme-doctor.py` | T3 | The contract gate |
| `scripts/freeze-theme.py` | T4 | Copy + noindex + banner into `themes/archive/YYYY-MM/` |
| `.github/workflows/rotate-theme.yml` | T5 | Scheduled rotation, gates, abort-and-issue |
| `themes.html` | T6 | The gallery, rendered from the registry |
| `tests/test_theme_registry.py`, `tests/test_theme_doctor.py`, `tests/test_freeze_theme.py` | T1/T3/T4 | Unit coverage |
| `CLAUDE.md` | T6 | Build/queue/preview/rollback docs |

Archive location note: frozen output lives at `themes/archive/YYYY-MM/` in the repo and is served at `/themes/archive/YYYY-MM/`. The gallery is `themes.html` served at `/themes.html`. (Root `themes/` holds theme sources; sources are not served as pages because they contain no rendered HTML except shells, which carry unfilled zone markers. T3 Step 5 asserts shells are never published.)

---

### Task T1: The registry

**Files:**
- Create: `content/themes.json`, `scripts/theme_registry.py`, `tests/test_theme_registry.py`

**Interfaces:**
- Produces (consumed by T2-T6):
  - `load(root: Path = ROOT) -> dict` — parsed registry.
  - `active_slug(reg: dict) -> str`
  - `theme_dir(slug: str, root: Path = ROOT) -> Path` → `root/"themes"/slug`
  - `validate(reg: dict, root: Path = ROOT) -> list[str]` — returns failure strings, empty when valid. Rules: `active` is a non-empty string whose theme dir exists and contains all three files; `queue` is a list of slugs with existing dirs and no duplicates; `active` not also in `queue`; every `archive` entry has `slug`, `month` (YYYY-MM), `url`; archive months unique.
  - `rotate(reg: dict, month: str) -> dict` — pure function: returns a NEW registry with `queue[0]` promoted to active, the old active appended to archive as `{slug, month, url: f"/themes/archive/{month}/"}`, and `queue[1:]` retained. Raises `ValueError("queue is empty")` when the queue is empty. Does not touch disk.

- [ ] **Step 1: Write the failing tests**

```python
import json, sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import theme_registry as tr


def _reg():
    return {"active": "a", "queue": ["b", "c"], "archive": []}


def test_rotate_promotes_and_archives():
    out = tr.rotate(_reg(), "2026-09")
    assert out["active"] == "b"
    assert out["queue"] == ["c"]
    assert out["archive"] == [
        {"slug": "a", "month": "2026-09", "url": "/themes/archive/2026-09/"}
    ]


def test_rotate_is_pure():
    reg = _reg()
    tr.rotate(reg, "2026-09")
    assert reg == _reg()


def test_rotate_empty_queue_raises():
    with pytest.raises(ValueError, match="queue is empty"):
        tr.rotate({"active": "a", "queue": [], "archive": []}, "2026-09")


def test_validate_flags_missing_theme_dir(tmp_path):
    (tmp_path / "themes").mkdir()
    errs = tr.validate({"active": "ghost", "queue": [], "archive": []}, root=tmp_path)
    assert any("ghost" in e for e in errs)


def test_validate_flags_duplicate_queue(tmp_path):
    for slug in ("a", "b"):
        d = tmp_path / "themes" / slug
        d.mkdir(parents=True)
        for f in ("shell.html", "tokens.css", "theme.json"):
            (d / f).write_text("x", encoding="utf-8")
    errs = tr.validate({"active": "a", "queue": ["b", "b"], "archive": []}, root=tmp_path)
    assert any("duplicate" in e.lower() for e in errs)


def test_real_registry_is_valid():
    assert tr.validate(tr.load()) == []
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_theme_registry.py -v`
Expected: collection error / `ModuleNotFoundError: No module named 'theme_registry'`.

- [ ] **Step 3: Implement**

`content/themes.json`:

```json
{
  "$comment": "Presentation state for 626labs.dev. active = live theme; queue = approved themes awaiting rotation (FIFO); archive = frozen past themes. Content lives in site.json and stays theme-agnostic.",
  "active": "phosphor-blueprint",
  "queue": [],
  "archive": []
}
```

`scripts/theme_registry.py`:

```python
#!/usr/bin/env python3
"""The theme registry: one switch for which theme is live.

active = the live theme. queue = approved themes awaiting rotation (FIFO).
archive = frozen past themes, never re-rendered.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "content" / "themes.json"
REQUIRED_FILES = ("shell.html", "tokens.css", "theme.json")
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def load(root: Path = ROOT) -> dict:
    return json.loads((root / "content" / "themes.json").read_text(encoding="utf-8"))


def active_slug(reg: dict) -> str:
    return reg["active"]


def theme_dir(slug: str, root: Path = ROOT) -> Path:
    return root / "themes" / slug


def _theme_complete(slug: str, root: Path) -> list[str]:
    d = theme_dir(slug, root)
    if not d.is_dir():
        return [f"theme dir missing: {d}"]
    return [f"theme {slug} missing {f}" for f in REQUIRED_FILES if not (d / f).exists()]


def validate(reg: dict, root: Path = ROOT) -> list[str]:
    errs: list[str] = []
    active = reg.get("active")
    if not isinstance(active, str) or not active:
        errs.append("active must be a non-empty slug")
    else:
        errs += _theme_complete(active, root)
    queue = reg.get("queue", [])
    if not isinstance(queue, list):
        errs.append("queue must be a list")
        queue = []
    if len(set(queue)) != len(queue):
        errs.append("queue has duplicate slugs")
    if active in queue:
        errs.append(f"active theme {active} must not also sit in the queue")
    for slug in queue:
        errs += _theme_complete(slug, root)
    months = []
    for entry in reg.get("archive", []):
        for key in ("slug", "month", "url"):
            if key not in entry:
                errs.append(f"archive entry missing {key}: {entry}")
        month = entry.get("month", "")
        if month and not MONTH_RE.match(month):
            errs.append(f"archive month not YYYY-MM: {month}")
        months.append(month)
    if len(set(months)) != len(months):
        errs.append("archive has duplicate months")
    return errs


def rotate(reg: dict, month: str) -> dict:
    """Pure: promote queue[0] to active, archive the outgoing theme."""
    queue = list(reg.get("queue", []))
    if not queue:
        raise ValueError("queue is empty")
    outgoing = reg["active"]
    return {
        **{k: v for k, v in reg.items() if k not in ("active", "queue", "archive")},
        "active": queue[0],
        "queue": queue[1:],
        "archive": list(reg.get("archive", []))
        + [{"slug": outgoing, "month": month, "url": f"/themes/archive/{month}/"}],
    }
```

- [ ] **Step 4: Verify** — `python -m pytest tests/test_theme_registry.py -v` all pass EXCEPT `test_real_registry_is_valid`, which fails until T2 creates the theme dir. Mark that expected-fail in your report; it turns green in T2 Step 6.
- [ ] **Step 5: Commit**

```bash
git add content/themes.json scripts/theme_registry.py tests/test_theme_registry.py
git commit -m "feat(themes): the registry, one switch for the live theme

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task T2: Extract Phosphor Blueprint + `--theme`/`--out`

**Files:**
- Create: `themes/phosphor-blueprint/{shell.html,tokens.css,theme.json}`
- Modify: `scripts/render-hub.py` (paths near line 51; `main()` near line 1870)

**Interfaces:**
- Consumes: `theme_registry.load/active_slug/theme_dir`.
- Produces: `render-hub.py --theme <slug> --out <dir>` renders that theme's shell to `<dir>/index.html` and writes nothing else (no feed, no sitemap, no story pages). Default invocation (no flags) renders the ACTIVE theme's shell to `index.html` and everything else exactly as today.

- [ ] **Step 1: Extract the shell**

`themes/phosphor-blueprint/shell.html` starts as a byte-copy of today's `index.html` from `origin/main`. Then move the theme's CSS out: cut the `--pb-*` token declarations, the `.pb-scanlines` rule, and the PB override block into `tokens.css`, replacing them in the shell with `<link rel="stylesheet" href="/themes/phosphor-blueprint/tokens.css">` in `<head>`. Everything else — all twelve zone markers, nav, footer, structural CSS, the star-map JS, the GoatCounter snippet — stays in the shell untouched.

CAUTION: `index.html` currently contains rendered zone CONTENT. The shell must keep the markers and may keep the current content between them (the renderer overwrites it). Do not hand-empty the zones; that risks marker damage.

`theme.json`:

```json
{
  "name": "Phosphor Blueprint",
  "slug": "phosphor-blueprint",
  "thesis": "The drawing is the monitor. A CRT phosphor kit over a two-scale drafting grid on absolute black.",
  "month": "2026-08",
  "status": "live"
}
```

- [ ] **Step 2: Add the flags to render-hub.py**

Near the path constants (line ~51), add:

```python
import theme_registry
```
(the script already inserts `scripts/` on `sys.path` for `site_facts`; mirror that import style)

In `main(argv)`, before `src = INDEX_HTML.read_text(...)`, resolve the source and destination:

```python
    theme_slug = None
    if "--theme" in argv:
        theme_slug = argv[argv.index("--theme") + 1]
    out_dir = None
    if "--out" in argv:
        out_dir = Path(argv[argv.index("--out") + 1])

    reg = theme_registry.load()
    slug = theme_slug or theme_registry.active_slug(reg)
    shell = theme_registry.theme_dir(slug) / "shell.html"
    src = shell.read_text(encoding="utf-8") if shell.exists() else INDEX_HTML.read_text(encoding="utf-8")
    dest = (out_dir / "index.html") if out_dir else INDEX_HTML
```

Then replace later uses of `INDEX_HTML.write_text(out, ...)` with `dest.write_text(out, ...)` (creating `dest.parent` when `out_dir` is set), and make the preview path return early after writing the page: when `out_dir` is set, skip the feed, sitemap, story-page, and orphan-prune blocks entirely, print `f"preview written: {dest}"`, and return 0. `--check` behavior is unchanged and always operates on the default path.

- [ ] **Step 3: Verify byte-identical extraction**

```bash
git stash list >/dev/null   # ensure clean tree first
cp index.html /tmp/index-before.html
python scripts/render-hub.py
diff /tmp/index-before.html index.html && echo "BYTE-IDENTICAL"
```
Expected: `BYTE-IDENTICAL`, and `git diff --stat index.html` empty.
**If it differs: STOP.** Do not adjust the shell to force a match. Report the exact diff as a design finding per the plan's Global Constraints.

- [ ] **Step 4: Verify preview mode**

```bash
python scripts/render-hub.py --theme phosphor-blueprint --out /tmp/preview
```
Expected: `preview written: /tmp/preview/index.html`; that file is byte-identical to `index.html`; and `git status --porcelain` shows NO changes to `feed.xml`, `sitemap.xml`, or `editorial/` (preview must not touch them).

- [ ] **Step 5: Full gates** — `python scripts/render-hub.py --check` exit 0; `python -m pytest tests/ -q` all pass (including `test_real_registry_is_valid`, now green); `python scripts/site-doctor.py --report` PASS.
- [ ] **Step 6: Commit**

```bash
git add themes/phosphor-blueprint scripts/render-hub.py
git commit -m "feat(themes): extract Phosphor Blueprint as theme one, add preview rendering

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task T3: theme-doctor, the contract

**Files:**
- Create: `scripts/theme-doctor.py`, `tests/test_theme_doctor.py`

**Interfaces:**
- Consumes: `theme_registry`, `render-hub.py --theme/--out` (T2).
- Produces: CLI `python scripts/theme-doctor.py <slug>` → exit 0 when the theme passes, 1 with a printed failure list otherwise. Importable checks, each `(html: str, css: str) -> list[str]`: `check_zones`, `check_chrome`, `check_internal_links`. Browser-dependent checks live behind `--browser` (see Step 3) so the unit suite stays fast and offline.

- [ ] **Step 1: Write the failing tests**

```python
import importlib.util, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("theme_doctor", ROOT / "scripts" / "theme-doctor.py")
td = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(td)

ZONES = ("hero", "hero-chips", "products", "lab-pool", "thinking", "founding",
         "stories", "lab-runs", "play", "about", "support", "contact")


def _good_html():
    zones = "\n".join(f"<!-- SITE_JSON:{z}:start --><!-- SITE_JSON:{z}:end -->" for z in ZONES)
    return f"""<html><head></head><body>
      <a class="skip-link" href="#main">Skip</a><nav>x</nav>
      {zones}<footer>f</footer>
      <script data-goatcounter="https://626labs.goatcounter.com/count"></script>
    </body></html>"""


def test_zones_pass_when_all_present():
    assert td.check_zones(_good_html(), "") == []


def test_zones_flag_a_missing_zone():
    html = _good_html().replace("<!-- SITE_JSON:products:start --><!-- SITE_JSON:products:end -->", "")
    errs = td.check_zones(html, "")
    assert any("products" in e for e in errs)


def test_chrome_flags_missing_skip_link():
    errs = td.check_chrome(_good_html().replace('class="skip-link"', 'class="x"'), "")
    assert any("skip" in e.lower() for e in errs)


def test_chrome_flags_missing_analytics():
    errs = td.check_chrome(_good_html().replace("data-goatcounter", "data-nothing"), "")
    assert any("analytics" in e.lower() or "goatcounter" in e.lower() for e in errs)


def test_internal_links_flag_a_dead_target():
    html = _good_html().replace("<nav>x</nav>", '<nav><a href="/nope-does-not-exist.html">x</a></nav>')
    errs = td.check_internal_links(html, "")
    assert any("nope-does-not-exist" in e for e in errs)


def test_live_theme_passes_static_checks():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert td.check_zones(html, "") == []
    assert td.check_chrome(html, "") == []
```

- [ ] **Step 2: Run to verify failure** — `python -m pytest tests/test_theme_doctor.py -v` → FAIL (file not found / attributes missing).

- [ ] **Step 3: Implement**

`scripts/theme-doctor.py`: a `main(argv)` that renders the named theme to a temp dir via `render-hub.py --theme <slug> --out <tmp>`, reads the produced HTML and the theme's `tokens.css`, runs the three static checks plus contrast, and prints results.

- `check_zones`: every slug in the twelve-zone list has both `SITE_JSON:<z>:start` and `:end` present.
- `check_chrome`: page contains `class="skip-link"`, a `<nav`, a `<footer`, and `data-goatcounter`.
- `check_internal_links`: for each `href="..."` that is not `http`, `mailto:`, `#`, or empty — resolve against the repo root and assert the target file (or `<dir>/index.html`) exists.
- `check_contrast(css)`: parse `--*` custom properties whose values are hex colors, and for each declared foreground/background PAIR named in the theme's `theme.json` optional `"contrastPairs": [["--fg","--bg"], ...]` compute WCAG ratio and require ≥ 4.5. When `contrastPairs` is absent, emit ONE advisory line (`"no contrastPairs declared — contrast unverified"`) and do NOT fail; the pairs are how a theme states what it wants checked, and phosphor-blueprint declares them in T3 Step 4.
- `--browser` flag: when passed, additionally drive Playwright (via the repo's MCP tooling is not available to a script; use `playwright` if installed, else print `"browser checks skipped: playwright not installed"` and do not fail) to assert no horizontal scroll at 1440/768/390 and zero console errors. The scheduled workflow calls `--browser`.

Print `PASS <slug>` or the failure list + `FAIL <slug>`; exit accordingly.

- [ ] **Step 4: Declare phosphor-blueprint's contrast pairs**

Add to `themes/phosphor-blueprint/theme.json` a `"contrastPairs"` array naming its real text/background token pairs (read `tokens.css` for the actual names; e.g. `[["--fg-1","--pb-field"],["--fg-2","--pb-field"],["--fg-3","--pb-panel"]]`). Run `python scripts/theme-doctor.py phosphor-blueprint` — expect PASS. If a real pair fails AA, that is a genuine finding about the live site: report it, do not silence the check.

- [ ] **Step 5: Shells are never published** — assert `themes/**/shell.html` is not reachable as a site page: confirm `render_sitemap` does not enumerate it (`python scripts/render-hub.py && grep -c "themes/" sitemap.xml` → 0) and note it in the report.
- [ ] **Step 6: Commit**

```bash
git add scripts/theme-doctor.py tests/test_theme_doctor.py themes/phosphor-blueprint/theme.json
git commit -m "feat(themes): theme-doctor, the contract that makes rotation safe

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task T4: The freezer

**Files:**
- Create: `scripts/freeze-theme.py`, `tests/test_freeze_theme.py`

**Interfaces:**
- Consumes: `theme_registry`.
- Produces: `freeze(month: str, root: Path = ROOT) -> Path` — copies the CURRENT rendered `index.html` plus the active theme's `tokens.css` into `root/"themes"/"archive"/month/`, injecting `<meta name="robots" content="noindex">` into `<head>` and a dated banner as the first element inside `<body>`; rewrites the page's stylesheet href to the local frozen copy; returns the archive dir. CLI: `python scripts/freeze-theme.py <YYYY-MM>`.

- [ ] **Step 1: Write the failing tests**

```python
import importlib.util, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("freeze_theme", ROOT / "scripts" / "freeze-theme.py")
fz = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fz)


def _site(tmp_path):
    (tmp_path / "content").mkdir()
    (tmp_path / "content" / "themes.json").write_text(
        '{"active":"t","queue":[],"archive":[]}', encoding="utf-8")
    d = tmp_path / "themes" / "t"
    d.mkdir(parents=True)
    (d / "tokens.css").write_text(":root{--x:#fff}", encoding="utf-8")
    (d / "shell.html").write_text("<html></html>", encoding="utf-8")
    (d / "theme.json").write_text('{"name":"T","slug":"t"}', encoding="utf-8")
    (tmp_path / "index.html").write_text(
        '<html><head><link rel="stylesheet" href="/themes/t/tokens.css"></head>'
        '<body><main>hi</main></body></html>', encoding="utf-8")
    return tmp_path


def test_freeze_creates_archive_with_noindex_and_banner(tmp_path):
    out = fz.freeze("2026-09", root=_site(tmp_path))
    html = (out / "index.html").read_text(encoding="utf-8")
    assert 'name="robots"' in html and "noindex" in html
    assert "September 2026" in html
    assert (out / "tokens.css").exists()


def test_freeze_rewrites_stylesheet_to_local_copy(tmp_path):
    out = fz.freeze("2026-09", root=_site(tmp_path))
    html = (out / "index.html").read_text(encoding="utf-8")
    assert 'href="tokens.css"' in html
    assert "/themes/t/tokens.css" not in html


def test_freeze_refuses_to_overwrite(tmp_path):
    root = _site(tmp_path)
    fz.freeze("2026-09", root=root)
    try:
        fz.freeze("2026-09", root=root)
        assert False, "expected refusal"
    except FileExistsError:
        pass
```

- [ ] **Step 2: Run to verify failure** — FAIL, module missing.
- [ ] **Step 3: Implement** `scripts/freeze-theme.py` satisfying exactly those behaviors. Banner markup (inserted immediately after `<body>`):

```html
<div style="background:#111;color:#eee;font:14px/1.5 system-ui;padding:10px 16px;text-align:center">
  Archived: the site as it looked in September 2026. <a href="/" style="color:#17d4fa">Go to the live site</a>.
</div>
```
(month name derived from the `YYYY-MM` argument; no hardcoded month in source.)

- [ ] **Step 4: Verify** — `python -m pytest tests/test_freeze_theme.py -v` all pass.
- [ ] **Step 5: Exclusions** — add `themes/archive` to `sitemap.xml` generation exclusions (`SITEMAP_EXCLUDE` in render-hub.py) and to `.github/workflows/link-check.yml`'s `--exclude-path`. Verify: `python scripts/render-hub.py && grep -c "themes/archive" sitemap.xml` → 0.
- [ ] **Step 6: Commit**

```bash
git add scripts/freeze-theme.py tests/test_freeze_theme.py scripts/render-hub.py .github/workflows/link-check.yml
git commit -m "feat(themes): freeze retiring themes to dated noindex archives

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task T5: The rotation workflow

**Files:**
- Create: `.github/workflows/rotate-theme.yml`

**Interfaces:**
- Consumes: `theme_registry.rotate`, `freeze-theme.py`, `theme-doctor.py`, `render-hub.py`.

- [ ] **Step 1: Write the workflow** — `on: schedule: - cron: '0 9 1 * *'` (09:00 UTC on the 1st) plus `workflow_dispatch` with a `dry_run` boolean input. Steps, in order, with `set -euo pipefail`:
  1. Checkout; setup Python 3.11; `pip install -r requirements.txt`.
  2. Read the registry. If `queue` is empty: `gh issue create --title "Theme queue is empty" --body "Rotation ran on $(date -u +%F) with nothing queued. The site is unchanged."` and exit 0.
  3. `python scripts/freeze-theme.py "$(date -u +%Y-%m)"`.
  4. Rotate the registry (a small inline `python -c` that calls `theme_registry.rotate` and writes `content/themes.json`).
  5. `python scripts/render-hub.py`.
  6. Gates, all must pass: `python scripts/theme-doctor.py "$NEW_ACTIVE" --browser`, `python scripts/render-hub.py --check`, `python -m pytest tests/ -q`, `python scripts/site-doctor.py --check`.
  7. If `dry_run`: print the diff (`git diff --stat`) and exit WITHOUT committing.
  8. Commit and push with the retry+rebase loop the repo's other push-to-main workflows use (copy the pattern from `rebuild-hub.yml`), message `chore(themes): rotate to <slug> for <Month YYYY>` + the standard trailer.
  9. `if: failure()` — `gh issue create` titled `Theme rotation failed on <date>` with the run URL, and confirm nothing was pushed.

- [ ] **Step 2: Validate the YAML** — `python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/rotate-theme.yml'))"` prints nothing and exits 0.
- [ ] **Step 3: Dry-run proof** — after push (T6 ships the branch), the workflow is dispatchable with `dry_run: true`. Note in the report that a real dry run cannot execute until the branch merges; do not merge to test.
- [ ] **Step 4: Commit**

```bash
git add .github/workflows/rotate-theme.yml
git commit -m "feat(themes): scheduled rotation that can only move between verified states

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task T6: The gallery, docs, and the held PR

**Files:**
- Create: `themes.html`
- Modify: `scripts/render-hub.py` (a `render_themes_gallery()` + zone substitution), `CLAUDE.md`

**Interfaces:**
- Consumes: `theme_registry.load`.

- [ ] **Step 1: Build the gallery** — `themes.html` as a hand-authored root page in the ACTIVE theme's visual language (link `/themes/phosphor-blueprint/tokens.css`), matching `press.html`'s head/nav/footer/GoatCounter patterns. Title "Themes · 626 Labs"; canonical `https://626labs.dev/themes.html`. One `<!-- SITE_JSON:themes:start -->/:end` zone holding the cards.
- [ ] **Step 2: Render the cards** — add `render_themes_gallery(reg: dict) -> str` to render-hub.py emitting one card per theme: name, thesis, month, status, and a link (live theme → `/`; archived → its `url`; queued → no link, a "queued" chip). Wire `out = substitute_zone(out, "themes", render_themes_gallery(theme_registry.load()))` into the themes.html render path (mirror how conundrum.html's zones are handled: read, substitute, write only when changed, and include it in `--check`).
- [ ] **Step 3: Document it** — a "Theme rotation" section in `CLAUDE.md`: what a theme is (three files), how to build one, `theme-doctor` as the entry gate, how to preview (`--theme/--out`), how queueing works, what rotation does on the 1st, where archives live, and rollback (revert the rotation commit; `content/themes.json` is the only switch).
- [ ] **Step 4: Full gates** — `python scripts/render-hub.py`, `--check` exit 0, `pytest tests/ -q`, `site-doctor.py --report` PASS, `python scripts/theme-doctor.py phosphor-blueprint` PASS, `grep -c "themes.html" sitemap.xml` → 1.
- [ ] **Step 5: Browser verification** — serve the repo root; check `/themes.html` renders its card, `/` is unchanged from production, no console errors, no h-scroll at 390.
- [ ] **Step 6: Ship, HELD** — push; `gh pr create` titled `feat(site): monthly theme rotation, machinery and theme one`; body covers: the byte-identical extraction result, what theme-doctor checks, how rotation behaves (including empty-queue and failure paths), the archive/noindex decision, rollback, and the new URL `https://626labs.dev/themes.html` for GSC Request Indexing after merge; trailer `🤖 Generated with [Claude Code](https://claude.com/claude-code)`. `gh pr checks --watch`. DO NOT MERGE.

---

## Self-review notes

- **Spec coverage:** three-file theme + no renderer fork (T2), registry (T1), contract (T3), freeze/noindex/banner/exclusions (T4), queued scheduled rotation with abort-and-issue (T5), gallery + docs + rollback (T6). Escape hatch, new themes, theme picker, automated screenshots: all correctly absent per the spec's out-of-scope.
- **Known intentional expected-fail:** `test_real_registry_is_valid` fails in T1 and passes in T2 — called out in both tasks.
- **Type consistency:** `theme_registry.{load,active_slug,theme_dir,validate,rotate}` used identically in T1 tests, T2 wiring, T3, T4, T5, T6; archive URL shape `/themes/archive/YYYY-MM/` consistent across `rotate()`, the freezer, and the exclusions.
