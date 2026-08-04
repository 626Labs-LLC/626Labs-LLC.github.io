# Theme Archetypes M2a Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every public page rotatable by expressing a theme as four archetype dresses instead of one homepage shell, and prove the contract with an About-page theme toggle.

**Architecture:** An archetype is a markup contract; a theme is a dress for it. Four archetypes (`home`, `product`, `reading`, `utility`) each define a fixed semantic class vocabulary. Pages declare their archetype in `content/page-archetypes.json`. Phosphor Blueprint's four dresses are EXTRACTED from today's live pages, never redesigned, and every migrated page must render visually identical. Spec: `docs/superpowers/specs/2026-08-04-theme-archetypes-design.md`.

**Tech Stack:** Python 3.12 (two renderers, doctor, pytest), static HTML/CSS, vanilla JS for the toggle, Playwright for verification and screenshots.

## Global Constraints

- Branch `feat/theme-archetypes` from fresh `origin/main`. Trailer on every commit: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`; conventional commits; no emoji.
- **Every migrated page renders VISUALLY IDENTICAL to today** under Phosphor Blueprint: 0-pixel screenshot diff at 1440/768/390 plus computed-style spot checks, the M1 T2 precedent. A page that cannot be expressed in its archetype without inventing markup is a FINDING about the archetype boundaries — report it and stop; do not bend the vocabulary per page.
- **THREE page-generation mechanisms exist and the plan respects all three.** (1) `index.html`: shell + `SITE_JSON:` zones via render-hub. (2) Nine hand-authored standalone pages (about, conundrum, rororo, rororo-plugins, mod-launcher-games, press, privacy, thesis, workflow, themes, 404): full HTML files, some carrying zones. (3) The 14 plugin pages + `plugins/index.html`: ASSEMBLED from components by `render-plugin-pages.py` with a single `STYLE` constant — the renderer owns that markup, so a theme dresses those pages via theme-supplied CSS rather than a shell.
- Backward compatibility at every task boundary: `python scripts/render-hub.py --check` exit 0, `python scripts/render-plugin-pages.py` no-op when nothing changed, `python -m pytest tests/ -q`, `python scripts/site-doctor.py --report` PASS, `python scripts/theme-doctor.py phosphor-blueprint` PASS.
- No theme may use `--ed-link` as a text color (known base-layer AA failure, 2.58:1 on paper).
- `content/site.json` is content and stays untouched by this milestone. `admin-dashboard.html` is excluded entirely (internal tool).
- No new runtime dependencies.

## File map

| File | Task | Responsibility |
|---|---|---|
| `docs/theme-archetypes.md` | A1 | The written vocabulary — the contract itself |
| `content/page-archetypes.json` | A1 | Page → archetype mapping (data, not code) |
| `scripts/archetypes.py` | A1 | Load/validate the mapping + vocabulary constants |
| `themes/phosphor-blueprint/archetypes/{home,product,reading,utility}.html` | A2-A4 | PB's four dresses, extracted |
| `themes/phosphor-blueprint/archetypes/product.css` | A5 | Theme-supplied CSS for renderer-assembled plugin pages |
| `scripts/render-hub.py` | A2-A4 | Archetype-aware rendering for mechanisms 1 and 2 |
| `scripts/render-plugin-pages.py` | A5 | `STYLE` sourced from the active theme |
| `scripts/theme-doctor.py` | A6 | Gate all four archetypes + vocabulary enforcement |
| `about.html` + `scripts/render-hub.py` | A7 | The easter-egg toggle |
| `scripts/freeze-theme.py`, `.github/workflows/rotate-theme.yml`, `themes.html` | A8 | Screenshots + self-dressing gallery |

---

### Task A1: The contract — vocabulary, mapping, validation

**Files:**
- Create: `docs/theme-archetypes.md`, `content/page-archetypes.json`, `scripts/archetypes.py`, `tests/test_archetypes.py`

**Interfaces:**
- Produces (used by every later task):
  - `ARCHETYPES = ("home", "product", "reading", "utility")`
  - `VOCABULARY: dict[str, set[str]]` — per archetype, the required semantic class names.
  - `load(root=ROOT) -> dict` — the page→archetype mapping.
  - `archetype_for(page: str, mapping: dict) -> str` — raises `KeyError` naming the page when unmapped.
  - `validate(mapping: dict, root=ROOT) -> list[str]` — every mapped page exists on disk; every public page on disk is mapped; every value is a known archetype. Returns failure strings, empty when valid.

- [ ] **Step 1: Write the failing tests**

```python
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import archetypes as az


def test_four_archetypes():
    assert az.ARCHETYPES == ("home", "product", "reading", "utility")


def test_every_archetype_has_a_vocabulary():
    for a in az.ARCHETYPES:
        assert az.VOCABULARY[a], f"{a} has no required classes"


def test_archetype_for_known_page():
    mapping = {"index.html": "home", "about.html": "reading"}
    assert az.archetype_for("about.html", mapping) == "reading"


def test_archetype_for_unmapped_page_raises_naming_it():
    with pytest.raises(KeyError, match="ghost.html"):
        az.archetype_for("ghost.html", {"index.html": "home"})


def test_validate_flags_unknown_archetype(tmp_path):
    (tmp_path / "index.html").write_text("x", encoding="utf-8")
    errs = az.validate({"index.html": "spaceship"}, root=tmp_path)
    assert any("spaceship" in e for e in errs)


def test_validate_flags_missing_file(tmp_path):
    errs = az.validate({"ghost.html": "home"}, root=tmp_path)
    assert any("ghost.html" in e for e in errs)


def test_real_mapping_is_valid():
    assert az.validate(az.load()) == []
```

- [ ] **Step 2: Run to verify failure** — `python -m pytest tests/test_archetypes.py -v` → `ModuleNotFoundError: No module named 'archetypes'`.

- [ ] **Step 3: Write the vocabulary doc FIRST**

`docs/theme-archetypes.md` is the contract every theme signs. For each of the four archetypes, document: what pages use it, the required semantic class names with what each means, and the rule that a theme varies CSS and structural arrangement but never invents a new class for an existing semantic element. Derive the vocabulary from what today's pages ACTUALLY use — read index.html, about.html, and a plugin page and name the real classes, do not invent an idealized set. State explicitly that the reading vocabulary is exercised hardest because the About toggle swaps every theme's reading dress onto the same markup.

- [ ] **Step 4: Implement `scripts/archetypes.py`** with `ARCHETYPES`, `VOCABULARY` (populated from the doc), `load`, `archetype_for`, `validate`.

- [ ] **Step 5: Write the mapping**

`content/page-archetypes.json` — every public page. Start from this mapping and correct it against what is actually on disk (`ls *.html */index.html editorial/*/index.html`):

```json
{
  "$comment": "Which archetype dresses each public page. admin-dashboard.html is excluded: internal tool, never themed.",
  "index.html": "home",
  "about.html": "reading",
  "thesis.html": "reading",
  "workflow.html": "reading",
  "editorial/index.html": "reading",
  "conundrum.html": "product",
  "rororo.html": "product",
  "rororo-plugins.html": "product",
  "mod-launcher-games.html": "product",
  "plugins/index.html": "product",
  "privacy.html": "utility",
  "press.html": "utility",
  "themes.html": "utility",
  "404.html": "utility"
}
```
Add every remaining directory page (the 14 plugin pages, sanduhr, bacon-trail, play, thesis-engine, legal) and the six Field Note pages under `editorial/`. Field Notes are `reading`; plugin pages are `product`. If a page's archetype is genuinely ambiguous, put it in the report as a question rather than guessing.

- [ ] **Step 6: Verify + commit** — `python -m pytest tests/ -q` all pass; `python -c "import sys; sys.path.insert(0,'scripts'); import archetypes as az; print(len(az.load()), 'pages mapped')"` prints the count.

```bash
git add docs/theme-archetypes.md content/page-archetypes.json scripts/archetypes.py tests/test_archetypes.py
git commit -m "feat(themes): the archetype contract — vocabulary, mapping, validation

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task A2: Extract the home archetype

**Files:**
- Create: `themes/phosphor-blueprint/archetypes/home.html`
- Modify: `scripts/render-hub.py`

**Interfaces:**
- Consumes: `theme_registry.theme_dir`, `archetypes.load/archetype_for`.
- Produces: `render-hub.py` resolves index.html's shell as `themes/<active>/archetypes/home.html`. `themes/<slug>/shell.html` remains supported as a fallback ONLY if it exists, so nothing breaks mid-migration; A4 removes the fallback.

- [ ] **Step 1: Move the shell** — `git mv themes/phosphor-blueprint/shell.html themes/phosphor-blueprint/archetypes/home.html` (create the dir). The file's contents do not change in this task.
- [ ] **Step 2: Teach the renderer** — where render-hub resolves the shell (it currently reads `theme_dir(slug)/"shell.html"`), resolve `theme_dir(slug)/"archetypes"/f"{archetype}.html"` using the page's archetype from the mapping, falling back to `shell.html` when the archetype file is absent. Keep the destination-comparison behavior intact (`index_changed` compares against the destination file, never the source).
- [ ] **Step 3: Verify identity** — `python scripts/render-hub.py` then `git diff --stat index.html` EMPTY (the file's bytes must not change; only where the shell was read from changed). `python scripts/render-hub.py --check` exit 0.
- [ ] **Step 4: Gates** — `python -m pytest tests/ -q`, `python scripts/site-doctor.py --report` PASS, `python scripts/theme-doctor.py phosphor-blueprint` PASS.
- [ ] **Step 5: Commit**

```bash
git add themes/phosphor-blueprint/archetypes/home.html scripts/render-hub.py
git commit -m "feat(themes): the home archetype

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task A3: The reading archetype (About, thesis, workflow, Field Notes)

**Files:**
- Create: `themes/phosphor-blueprint/archetypes/reading.html`
- Modify: `scripts/render-hub.py` (Field Note page generation + standalone reading pages)

**Interfaces:**
- Produces: every `reading` page renders from the theme's reading archetype. The reading vocabulary from A1 is now real and exercised — A7's toggle depends on it.

- [ ] **Step 1: Build the reading archetype** by extracting the common structure of today's reading pages. about.html (Long Now Terminal treatment), thesis.html, workflow.html, and the generated Field Note pages share a shape: head, nav, an article body, footer, analytics. The archetype carries that structure with the A1 reading vocabulary's class names; per-page content stays where it lives today.
  CRITICAL: about.html currently ships the Long Now Terminal treatment, NOT Phosphor Blueprint. Preserve it exactly — its default look must not change in this milestone (A7 makes it swappable, it never makes it different by default). If honoring both "about keeps LNT" and "reading archetype is PB-dressed" requires the archetype to carry a per-page dress override, implement that override and document it in `docs/theme-archetypes.md`; that is the honest resolution, not a reason to restyle About.
- [ ] **Step 2: Wire the renderer** — reading pages resolve their shell through the archetype path; Field Note page generation (`render_story_pages`) uses the reading archetype rather than its current hardcoded template.
- [ ] **Step 3: Visual identity, per page** — for about.html, thesis.html, workflow.html, editorial/index.html, and TWO Field Note pages: Playwright screenshots at 1440/768/390 before (from `git stash`/`origin/main`) and after, 0-pixel diff required. Any diff STOPS the task and is reported.
- [ ] **Step 4: Gates** — render `--check` exit 0, `pytest tests/ -q`, `site-doctor --report` PASS, `theme-doctor phosphor-blueprint` PASS.
- [ ] **Step 5: Commit**

```bash
git add themes/phosphor-blueprint/archetypes/reading.html scripts/render-hub.py about.html thesis.html workflow.html editorial
git commit -m "feat(themes): the reading archetype

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task A4: The utility and product-standalone archetypes

**Files:**
- Create: `themes/phosphor-blueprint/archetypes/utility.html`, `themes/phosphor-blueprint/archetypes/product.html`
- Modify: `scripts/render-hub.py` (remove the `shell.html` fallback), the standalone pages

**Interfaces:**
- Produces: privacy, press, themes, 404 render from `utility`; conundrum, rororo, rororo-plugins, mod-launcher-games render from `product`. The `shell.html` fallback is GONE — every page resolves through an archetype, and a missing archetype file is a loud error.

- [ ] **Step 1: Extract both archetypes** from today's pages (press.html and privacy.html are the utility reference; conundrum.html and rororo.html are the product reference). Same rule: extract, never redesign.
- [ ] **Step 2: Remove the fallback** — `render-hub.py` no longer falls back to `shell.html`; a missing archetype file raises a clear error naming the expected path.
- [ ] **Step 3: Visual identity** for all seven pages at 1440/768/390, 0-pixel diff required.
- [ ] **Step 4: Gates** (same four) + confirm `themes/phosphor-blueprint/shell.html` no longer exists and nothing references it (`grep -rn "shell.html" scripts/ themes/ docs/ .github/`; update any doc that names it).
- [ ] **Step 5: Commit**

```bash
git add themes/phosphor-blueprint/archetypes scripts/render-hub.py conundrum.html rororo.html rororo-plugins.html mod-launcher-games.html privacy.html press.html themes.html 404.html
git commit -m "feat(themes): the utility and product archetypes, fallback removed

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task A5: The plugin renderer joins the system

**Files:**
- Create: `themes/phosphor-blueprint/archetypes/product.css`
- Modify: `scripts/render-plugin-pages.py`

**Interfaces:**
- Consumes: `theme_registry.load/active_slug/theme_dir`.
- Produces: `render-plugin-pages.py` sources its page CSS from the active theme's `archetypes/product.css` instead of its module-level `STYLE` constant. The 14 plugin pages plus `plugins/index.html` are dressed by the theme; their MARKUP stays renderer-owned (that markup is the product archetype's vocabulary in practice, and A1's doc must reflect the real class names it emits).

- [ ] **Step 1: Move the CSS** — the current `STYLE` constant's contents become `themes/phosphor-blueprint/archetypes/product.css`, byte-for-byte.
- [ ] **Step 2: Read it from the theme** — the renderer loads the active theme's product.css at render time. Keep the emitted output identical: if pages currently inline the CSS in a `<style>` block, keep inlining it (a `<link>` would change every page's bytes and is not this task's business).
- [ ] **Step 3: Verify identity** — `python scripts/render-plugin-pages.py` then `git diff --stat` must show NO changes to any of the 15 pages. This is the whole test: the CSS moved homes without moving a byte of output.
- [ ] **Step 4: Verify the live behaviors survive** — spot-check one plugin page for its version chip and its JSON-LD `softwareVersion` (both must still be present and correct).
- [ ] **Step 5: Gates** + commit

```bash
git add themes/phosphor-blueprint/archetypes/product.css scripts/render-plugin-pages.py
git commit -m "feat(themes): plugin pages dress from the active theme

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task A6: theme-doctor covers all four archetypes

**Files:**
- Modify: `scripts/theme-doctor.py`, `tests/test_theme_doctor.py`

**Interfaces:**
- Consumes: `archetypes.ARCHETYPES/VOCABULARY`.
- Produces: `theme-doctor.py <slug>` renders and checks ALL FOUR archetypes, and enforces the vocabulary.

- [ ] **Step 1: Write the failing tests** — a theme missing an archetype file fails; a theme whose archetype omits a required vocabulary class fails; a theme whose CSS targets a class outside the vocabulary fails; a compliant theme passes. Follow the existing test file's stubbing style so the suite stays fast and offline.
- [ ] **Step 2: Run to verify failure.**
- [ ] **Step 3: Implement** — loop the existing checks (zones where applicable, chrome, internal links, contrast, browser) across all four archetypes, and add `check_vocabulary(html, css, archetype) -> list[str]`. Per-archetype failures name the archetype in the message.
- [ ] **Step 4: Verify** — `python scripts/theme-doctor.py phosphor-blueprint` PASS across all four; `--browser` PASS locally; full suite green.
- [ ] **Step 5: Commit**

```bash
git add scripts/theme-doctor.py tests/test_theme_doctor.py
git commit -m "feat(themes): the doctor gates every archetype and the vocabulary

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task A7: The About easter egg

**Files:**
- Modify: `about.html` (its archetype-rendered output), `themes/phosphor-blueprint/archetypes/reading.html`
- Create: `scripts/render_about_toggle.py` or an addition to render-hub (implementer's call; state it in the report)

**Interfaces:**
- Consumes: `theme_registry.load` (for the list of offerable themes: archive entries + active + About's own default).
- Produces: about.html carries a hidden control that swaps the page's reading dress to any known theme, client-side, remembered in localStorage, defaulting to Long Now Terminal on every fresh visit.

- [ ] **Step 1: Decide and document the discovery mechanism** — a keyboard sequence or a small unlabeled mark; NOT a visible menu (it is an easter egg). State the choice in the report so it can be documented for Este.
- [ ] **Step 2: Emit the theme list** — the page needs each offerable theme's slug, display name, and reading-CSS URL. Archived themes' CSS lives in their frozen archive dir; the live theme's in `themes/<slug>/archetypes/`. Generate this list at render time from the registry so it can never disagree with reality.
- [ ] **Step 3: Implement the swap** — vanilla JS, no dependencies: replace the reading stylesheet's href, persist the choice, restore it on load. Default (no stored choice) is About's own Long Now Terminal dress. Include a visible way back to the default once the picker is open.
- [ ] **Step 4: Verify with Playwright** — open about.html, trigger the easter egg, switch to at least two themes, confirm the page re-dresses without layout breakage and without console errors, reload and confirm persistence, then reset to default and confirm it matches the untouched page.
- [ ] **Step 5: Gates** + commit

```bash
git add about.html themes/phosphor-blueprint/archetypes/reading.html scripts/
git commit -m "feat(about): the theme toggle — every dress on one story

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task A8: Screenshots and the self-dressing gallery

**Files:**
- Modify: `scripts/freeze-theme.py`, `.github/workflows/rotate-theme.yml`, `themes.html`, `scripts/render-hub.py` (gallery rendering)

**Interfaces:**
- Produces: `capture_theme_screenshot(slug: str, out_path: Path) -> Path` (in freeze-theme.py or a sibling module — state which in the report), deterministic: fixed 1440x900 viewport, fonts loaded, animations disabled. The gallery renders in the ACTIVE theme's utility archetype and shows each theme's thumbnail.

- [ ] **Step 1: Implement deterministic capture** and prove determinism: capture the same theme twice and byte-compare the two PNGs.
- [ ] **Step 2: Wire the rotation** — the freeze step captures the retiring theme; the promote step captures the incoming one. Both images land in a predictable path the gallery reads (state the path convention in the report). Add the images to the workflow's commit list.
- [ ] **Step 3: Self-dressing gallery** — themes.html renders from the active theme's utility archetype; cards show thumbnail, name, thesis, month, status, link. A theme with no captured thumbnail yet renders cleanly without one (Phosphor Blueprint has none until its first capture).
- [ ] **Step 4: Verify** — capture PB manually, confirm the gallery shows it; run the gates; confirm the archive/noindex/sitemap behavior from M1 is unchanged.
- [ ] **Step 5: Commit**

```bash
git add scripts/freeze-theme.py .github/workflows/rotate-theme.yml themes.html scripts/render-hub.py assets/themes
git commit -m "feat(themes): capture each theme, dress the gallery in the live one

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task A9: Whole-site verification and the held PR

- [ ] **Step 1: Every public page, visually identical** — Playwright over the full mapping from `content/page-archetypes.json`: each page at 1440 and 390, compared against `origin/main`. 0-pixel diff required everywhere. Produce a table in the report: page, archetype, diff result. ANY non-zero diff stops the task and is reported as a finding.
- [ ] **Step 2: Behavior spot-checks** — a plugin page's version chip and JSON-LD; the About toggle; the homepage star map; the bacon-trail widget; zero console errors on five sampled pages.
- [ ] **Step 3: Full gates** — `render-hub.py --check` exit 0, `render-plugin-pages.py` no-op, `pytest tests/ -q`, `site-doctor.py --report` PASS, `theme-doctor.py phosphor-blueprint --browser` PASS.
- [ ] **Step 4: Push and open the PR, HELD** — title `feat(site): theme archetypes — four dresses cover every page`; body covers the archetype contract, the page mapping, the visual-identity results table, the About easter egg and how to find it, screenshots and the self-dressing gallery, and that M2b (September's paper-and-ink bake-off) follows. Trailer `🤖 Generated with [Claude Code](https://claude.com/claude-code)`. `gh pr checks --watch`. DO NOT MERGE.

---

## Self-review notes

- **Spec coverage:** contract + mapping (A1), four archetypes extracted (A2-A4), second renderer joined (A5), doctor extended incl. vocabulary (A6), About toggle (A7), screenshots + self-dressing gallery (A8), whole-site verification + held PR (A9). September, non-public surfaces, and other-page pickers correctly absent.
- **Deliberate ambiguity resolutions:** about.html keeps Long Now Terminal by default even though its archetype is reading — A3 Step 1 names the per-page dress override as the honest fix rather than restyling About. Plugin-page markup stays renderer-owned; the theme dresses it via product.css (A5), and A1's vocabulary must describe the classes that renderer actually emits.
- **Type consistency:** `archetypes.{ARCHETYPES,VOCABULARY,load,archetype_for,validate}` used identically in A1 tests, A2-A5 wiring, and A6; archetype file path `themes/<slug>/archetypes/<archetype>.html` consistent across A2-A6; `product.css` named consistently in A5 and A6.
