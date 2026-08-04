# Bespoke Page Conformance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the last six bespoke pages into the theme system so all 39 public pages recolor together each month, with no page's appearance changing today.

**Architecture:** Each page loses its private `:root` token block, gains a renderer-owned `theme-css` zone linking the active theme's archetype stylesheet, and keeps its own layout rules rewritten to consume theme tokens. This reuses exactly the mechanism M2a built for press/privacy (`UTILITY_CSS_HREFS` + `render_theme_css_link` in render-hub.py). Spec: `docs/superpowers/specs/2026-08-04-bespoke-conformance-design.md`.

**Tech Stack:** Python 3.12 (render-hub, pytest), static HTML/CSS, Playwright for pixel verification.

## Global Constraints

- Branch `feat/bespoke-conformance` from fresh `origin/main`. Trailer on every commit: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`; conventional commits; no emoji.
- **Uniform dress, not uniform layout.** Each page KEEPS its own layout rules in its own file. Do NOT move layout into the theme, and do NOT rewrite page markup to the archetype vocabulary — vocabulary gates a THEME's dress, not a page.
- **Every page renders 0-pixel identical at 1440/768/390 versus `origin/main`.** Use `scripts/freeze-theme.py`'s `_DETERMINISTIC_CAPTURE_INIT_SCRIPT` (seeded `Math.random`, frozen clock) for every comparison so nondeterminism is never mistaken for regression. Serve both trees (an `origin/main` worktree and the working tree) on separate ports.
- **The mechanism to reuse, verbatim in shape:** `render-hub.py` lines ~823-870 define `UTILITY_CSS_HREFS` (a dict of page path → archetype CSS relative path) and `render_theme_css_link(slug, css_rel_path)`, and main() substitutes a `<!-- SITE_JSON:theme-css:start -->` / `:end` zone in each mapped page. press.html is the reference implementation — read it before writing anything.
- **A literal that no token should absorb stays a literal.** Do not grow `REQUIRED_TOKENS` (43 entries in `scripts/archetypes.py`) to swallow every one-off value; that turns the contract into a junk drawer every future theme must satisfy. Per page, record which literals stayed and why.
- Archetype assignments are already in `content/page-archetypes.json`: thesis/workflow are `reading`; conundrum/rororo/rororo-plugins/mod-launcher-games are `product`. Reading pages link `archetypes/reading.css`; product pages link `archetypes/product.css`.
- Gates at every task boundary: `python scripts/render-hub.py --check` exit 0, `python scripts/render-plugin-pages.py --check` clean, `python -m pytest tests/ -q` (125 currently pass), `python scripts/site-doctor.py --report` PASS, `python scripts/theme-doctor.py phosphor-blueprint` PASS.
- `content/site.json` untouched. No new dependencies.

## File map

| File | Task | What changes |
|---|---|---|
| `thesis.html`, `workflow.html` | Task 1 | Token block out, theme-css zone in, literals → tokens |
| `conundrum.html`, `rororo-plugins.html` | Task 2 | Same |
| `rororo.html`, `mod-launcher-games.html` | Task 3 | Same, plus live-feed behavior verified |
| `scripts/render-hub.py` | Tasks 1-3 | Each page added to the theme-css zone map |
| `scripts/archetypes.py` | Tasks 1-3 | `REQUIRED_TOKENS` grows only if a page genuinely needs a token the set lacks |
| `tests/test_render_hub.py` | Task 1 | Coverage that the new pages resolve their href from the active theme |
| — | Task 4 | Scratch-theme proof, whole-site verification, held PR |

---

### Task 1: The reading pair — thesis.html and workflow.html

**Files:**
- Modify: `thesis.html` (476 lines CSS, 115 rules, 34 own tokens), `workflow.html` (522 lines, 145 rules, 39 own tokens), `scripts/render-hub.py`, `tests/test_render_hub.py`

**Interfaces:**
- Consumes: `render_theme_css_link(slug, css_rel_path) -> str` and the `UTILITY_CSS_HREFS` pattern in render-hub.py (~lines 823-870); `theme_registry.active_slug`.
- Produces: both pages carry a `theme-css` zone resolved from the active theme, linking `archetypes/reading.css`. The map that Task 2 and Task 3 extend is whatever you name it — if `UTILITY_CSS_HREFS` is now a misnomer because it serves reading and product pages too, rename it to something accurate (e.g. `THEME_CSS_HREFS`) in this task and update its existing three entries; say so in your report so Task 2/Task 3 use the right name.

- [ ] **Step 1: Read the reference** — `press.html` lines 15-25 (the zone), `scripts/render-hub.py` 823-870 (the map and the renderer), and how main() substitutes it (~line 2191). Also read `themes/phosphor-blueprint/archetypes/reading.css` so you know which tokens and rules the theme already provides.
- [ ] **Step 2: Capture the baseline** — with an `origin/main` worktree served on one port and the working tree on another, capture thesis.html and workflow.html at 1440/768/390 using the deterministic init script. Keep these images; Step 6 compares against them.
- [ ] **Step 3: Convert thesis.html** — delete its `:root` block; insert the `theme-css` zone in `<head>` before its `<style>`; rewrite its remaining rules' hardcoded colors/fonts/spacing to `var(--token)` where an equivalent exists in `REQUIRED_TOKENS`. Where a value has no equivalent, keep the literal and note it.
- [ ] **Step 4: Convert workflow.html** the same way.
- [ ] **Step 5: Wire the renderer** — add both pages to the href map with `archetypes/reading.css`, and add them to main()'s theme-css substitution and to the `--check` staleness list, following exactly how press/privacy are handled.
- [ ] **Step 6: Prove identity** — re-render, re-capture both pages at all three widths, byte-compare against Step 2's images. All six comparisons must be 0-pixel. Any diff STOPS the task: report the page, the width, the magnitude, and your read of the cause.
- [ ] **Step 7: Test the wiring** — add a test asserting both pages' hrefs are derived from the registry's active slug (mirror the existing coverage for press/privacy in `tests/test_render_hub.py`).
- [ ] **Step 8: Gates + commit**

```bash
git add thesis.html workflow.html scripts/render-hub.py scripts/archetypes.py tests/test_render_hub.py
git commit -m "feat(themes): thesis and workflow take the theme's reading dress

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: The small product pair — conundrum.html and rororo-plugins.html

**Files:**
- Modify: `conundrum.html` (220 lines CSS, 59 rules, 33 own tokens), `rororo-plugins.html` (235 lines, 65 rules, 29 own tokens), `scripts/render-hub.py`

**Interfaces:**
- Consumes: the href map and `render_theme_css_link` (Task 1 may have renamed the map — check the current name in render-hub.py rather than assuming).
- Produces: both pages linking `archetypes/product.css` from the active theme.

- [ ] **Step 1: Capture the baseline** for both pages at 1440/768/390 with the deterministic init script, against an `origin/main` worktree.
- [ ] **Step 2: Convert conundrum.html** — token block out, `theme-css` zone in, literals to tokens where an equivalent exists. NOTE this page has a crisp-lift pattern (the merch gallery deliberately sits above the scanline overlay at z-index 61, nav at 70) and GoatCounter outbound-click events on `data-etsy` links — neither may break.
- [ ] **Step 3: Convert rororo-plugins.html** the same way.
- [ ] **Step 4: Wire both** into the href map, main()'s substitution, and the `--check` list.
- [ ] **Step 5: Prove identity** — 0-pixel at all three widths for both pages. Any diff STOPS the task.
- [ ] **Step 6: Verify behavior** — serve the working tree, open conundrum.html, and confirm with Playwright that a gallery card click still fires a GoatCounter event with an `etsy-click/<slug>` path (stub `window.goatcounter.count` before clicking and assert on the captured argument, preventing navigation). Confirm the crisp-lift still holds: `.merch-grid` computed z-index 61, `.topnav` 70.
- [ ] **Step 7: Gates + commit**

```bash
git add conundrum.html rororo-plugins.html scripts/render-hub.py scripts/archetypes.py
git commit -m "feat(themes): conundrum and rororo-plugins take the theme's product dress

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: The live-data pair — rororo.html and mod-launcher-games.html

**Files:**
- Modify: `rororo.html` (502 lines CSS, 146 rules, 39 own tokens), `mod-launcher-games.html` (300 lines, 77 rules, 37 own tokens), `scripts/render-hub.py`

**Interfaces:**
- Consumes: the href map and `render_theme_css_link`.
- Produces: both pages linking `archetypes/product.css` from the active theme. After this task, all six bespoke pages are converted.

- [ ] **Step 1: Capture the baseline** for both pages at 1440/768/390 with the deterministic init script. IMPORTANT: both pages fetch live data at runtime (`rororo.html` reads `data/rororo-plugins.json` for its plugin catalog and a version chip; `mod-launcher-games.html` fetches the game manifest from GitHub and renders featured/curated/nexus sections). Capture AFTER their content settles, and use the SAME settle procedure for the after-shots so the comparison is fair.
- [ ] **Step 2: Convert rororo.html** — token block out, `theme-css` zone in, literals to tokens where equivalents exist. Its `#win-latest` version-chip element and the JS that fills it must be untouched.
- [ ] **Step 3: Convert mod-launcher-games.html** the same way; its fetch-and-render script must be untouched.
- [ ] **Step 4: Wire both** into the href map, main()'s substitution, and the `--check` list.
- [ ] **Step 5: Prove identity** — 0-pixel at all three widths for both pages. Any diff STOPS the task.
- [ ] **Step 6: Verify the live feeds still work** — with Playwright: rororo.html's plugin cards render and `#win-latest` shows a version; mod-launcher-games.html's featured/curated/nexus sections populate and its counts appear. Zero console errors on both. A page that renders pixel-identically but whose feed silently died is a FAILURE, not a pass.
- [ ] **Step 7: Gates + commit**

```bash
git add rororo.html mod-launcher-games.html scripts/render-hub.py scripts/archetypes.py
git commit -m "feat(themes): rororo and mod-launcher-games take the theme's product dress

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Prove the wiring is real, verify the site, ship held

**Files:** none permanent — a scratch theme is created and deleted.

**Interfaces:**
- Consumes: everything Tasks 1-3 wired.

- [ ] **Step 1: The scratch-theme proof** — this is the test that the wiring is real rather than nominal. Create `themes/scratch-proof/` as a copy of `themes/phosphor-blueprint/` with LOUD, unmistakable token values (e.g. `--bg-0: #ff00ff`), point `content/themes.json`'s `active` at it, render, and confirm with Playwright that ALL SIX converted pages visibly change (sample a computed background or text color per page and assert it matches the scratch value). Then restore `content/themes.json` to `phosphor-blueprint`, re-render, delete `themes/scratch-proof/`, and confirm `git status` is clean of it. Record the per-page evidence in your report.
- [ ] **Step 2: Whole-site verification** — every page in `content/page-archetypes.json` at 1440 and 390 versus `origin/main`, deterministic init script, 0-pixel required. Known-acceptable exceptions from the prior milestone, which you must confirm rather than assume: `themes.html` differs by its gallery thumbnail; `workflow.html` had sub-0.05% capture noise near its doctrine-diagram glow that reproduced on same-tree self-comparison (if workflow.html now shows a diff, prove which kind it is before calling it acceptable — you converted that page this time).
- [ ] **Step 3: Full gates** — `render-hub.py --check` exit 0, `render-plugin-pages.py --check` clean, `pytest tests/ -q`, `site-doctor.py --report` PASS, `theme-doctor.py phosphor-blueprint --browser` PASS.
- [ ] **Step 4: Push and open the PR, HELD** — title `feat(site): every page wears the theme`. Body covers: what changed (six pages lose private token blocks, gain theme-resolved stylesheets, keep their layouts), the scratch-theme proof results, the whole-site pixel table, the live-feed and GoatCounter behavior checks, which literals stayed literal and why, and the statement that these pages recolor monthly rather than re-layout by design. Trailer `🤖 Generated with [Claude Code](https://claude.com/claude-code)`. `gh pr checks --watch`. DO NOT MERGE.

---

## Self-review notes

- **Spec coverage:** all six pages converted (Tasks 1-3), mechanism reused rather than reinvented (Task 1 Step 1 + 5), literals-stay-literal recorded per task, pixel gate everywhere, the scratch-theme "is the wiring real" success criterion (Task 4 Step 1), live-feed and GoatCounter risks each given their own verification step (Task 2 Step 6, Task 3 Step 6), held PR (Task 4 Step 4). Redesign, vocabulary conformance, September, 404/legal, and about.html are all correctly absent.
- **Naming resolved up front:** `UTILITY_CSS_HREFS` becomes a misnomer once reading and product pages use it; Task 1 renames it and tells Tasks 2 and 3 to check the current name rather than hardcoding either.
- **Type consistency:** `render_theme_css_link(slug, css_rel_path) -> str` used identically in Tasks 1-3; archetype CSS paths `archetypes/reading.css` and `archetypes/product.css` match `content/page-archetypes.json`'s assignments.
