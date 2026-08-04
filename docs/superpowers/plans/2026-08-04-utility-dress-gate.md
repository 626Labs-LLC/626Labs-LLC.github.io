# Utility Dress Gate + Committed Visual Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make it impossible for a theme to silently undress `press.html` and `privacy.html`, and leave behind a re-runnable visual harness so the next milestone does not rebuild one from scratch.

**Architecture:** Those two pages keep borrowing their chrome from the active theme's `archetypes/utility.css` — the dependency stays and the gate learns to check it. Three mechanisms: render both pages in the pre-rotation browser gate and assert computed outcomes rather than selector shapes; remove the one fragile part of the dependency (the font import) by having the pages self-import a repo-global asset; and scope `check_theme_reads_only_what_it_defines` per resolution group so `{utility.css}`-alone is graded honestly. Spec: `docs/superpowers/specs/2026-08-04-utility-dress-gate-design.md`.

**Tech Stack:** Python 3.12 (theme-doctor, pytest), Playwright, static HTML/CSS, GitHub Actions.

## Global Constraints

- Branch `feat/utility-dress-gate` already exists at `e1f1bba` (the spec commit) and is where all work happens. **It stacks on `feat/bespoke-conformance` (PR #96), which must merge before this one.** Do not merge either.
- Conventional commits; trailer `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`; no emoji anywhere except the single sanctioned PR-body trailer.
- **`press.html` and `privacy.html` must render 0-pixel identical to `origin/main` at 1440/768/390.** Filters ON, no masking, no envelope, using the shipped `scripts/freeze-theme.py` init script including its SMIL freeze.
- **Gate on computed outcome, never on a selector manifest.** A theme setting the field on `html` instead of `body` must pass. Assertions constrain what must be TRUE, never what values it must be. Keep them few and load-bearing — this is the same discipline `REQUIRED_TOKENS` needed on a new surface.
- Every gate added ships with a test **verified failing** against the un-gated implementation. A gate you have not seen fail is not a gate.
- `content/site.json` untouched. No new dependencies.
- Gates before each commit: `python scripts/render-hub.py --check` exit 0, `python scripts/render-plugin-pages.py --check` clean, `python -m pytest tests/ -q` (174 pass at HEAD), `python scripts/site-doctor.py --report` PASS (`--check` exits 1 SILENTLY — use `--report`), `python scripts/theme-doctor.py phosphor-blueprint --browser` PASS.

## What the two pages actually borrow

Measured, not guessed — identical across both pages. Do not re-derive this by guessing; re-measure if you need it.

| Selector | Properties taken from the theme |
|---|---|
| `*` | `box-sizing` |
| `html, body` | `margin`, `padding` |
| `body` | `background`, `color`, `font-family`, `font-size`, `line-height`, `overflow-x`, `-webkit-font-smoothing` |
| `a` | `color`, `text-decoration` |
| `a.inline-link` (+`:hover`) | `color`, `border-bottom`, `transition` |
| `h1, h2, h3, h4` | `font-family`, `letter-spacing` |
| `nav.nav` | `position`, `top`, `z-index`, `background`, `border-bottom`, `backdrop-filter` |
| `header.page-hero` | `position`, `padding`, `border-bottom`, `overflow` |
| `h1.page-title` (+`.accent`) | `color`, `font-size`, `font-weight`, `letter-spacing`, `line-height`, `margin`, gradient clip |
| `footer` | `background`, `border-top`, `padding` |
| `h1` | `text-shadow` |

## File map

| File | Task | What changes |
|---|---|---|
| `press.html`, `privacy.html` | 1 | Self-import `/fonts/fonts.css` |
| `scripts/theme-doctor.py` | 1, 2 | Both pages into `BROWSER_CHECK_LIVE_PAGES`; computed-outcome assertions; per-group reads-check scoping |
| `tests/test_theme_doctor.py` | 1, 2 | Coverage for every gate added, plus the three untested behaviors inherited from PR #96 |
| `scripts/visual-diff.py` | 3 | New — the committed two-tree harness |
| `tests/test_visual_diff.py` | 3 | New |
| `.github/workflows/visual-diff.yml` | 4 | New — dispatch + opt-in PR label |

---

### Task 1: Gate the borrowed dress

**Files:**
- Modify: `press.html`, `privacy.html`, `scripts/theme-doctor.py`, `tests/test_theme_doctor.py`

**Interfaces:**
- Consumes: `BROWSER_CHECK_LIVE_PAGES` (`scripts/theme-doctor.py:193`), `_run_browser_checks_all`, `_check_viewport`, and the off-origin isolation in `scripts/browser_origin.py`.
- Produces: a named computed-outcome check other tasks do not call. Report its function name and signature — Task 4 references it when proving a broken theme fails.

- [ ] **Step 1: Read the ground truth.** `press.html` and `privacy.html` in full (each has its own `<style>`; the borrowing is narrower than "everything"), `themes/phosphor-blueprint/archetypes/utility.css`, and how `_run_browser_checks_all` builds its target set. Confirm the borrow table above by measurement before you rely on it.
- [ ] **Step 2: Capture the baseline.** Both pages at 1440/768/390 against an `origin/main` worktree, shipped init script with SMIL freeze. Run a base-vs-base self-check first so a nondeterministic page cannot masquerade as a regression later.
- [ ] **Step 3: Self-import the fonts.** Add `/fonts/fonts.css` to each page's own `<style>` or `<head>`, matching how the six pages converted in PR #96 do it. `fonts.css` is a repo-global asset, not a theme asset, so this removes the single most fragile part of the dependency. The import is idempotent — the theme's own import staying is harmless.
- [ ] **Step 4: Add both pages to `BROWSER_CHECK_LIVE_PAGES`** and confirm they are previewable (there is a runtime hard-fail if a listed page was not emitted — make sure you do not trip it).
- [ ] **Step 5: Write the computed-outcome assertions.** In the browser check, for both pages: `body` resolves a non-transparent background AND a font-family whose first family is not a browser default serif/sans keyword; `nav.nav` resolves a non-transparent background and a numeric `z-index`; `h1.page-title` resolves a font-size above the body's and a non-default weight; `footer` resolves a non-transparent background; `a` resolves a color measurably different from `body`'s color. Assert outcomes only — no assertion may reference a selector's presence in the theme's CSS, and none may pin a specific value.
- [ ] **Step 6: Prove the gate fails.** Build a scratch theme whose `utility.css` drops the load-bearing rules while still defining all required tokens. Confirm `theme-doctor` exits 0 on it BEFORE your change and exits 1 AFTER, and that the failure message names which outcome was missing. Delete the scratch theme; confirm `git status` is clean of it.
- [ ] **Step 7: Prove nothing moved.** Re-capture both pages at all three widths; 6/6 true 0-pixel required. Add a computed-style channel. Any diff STOPS the task.
- [ ] **Step 8: Test it.** Each assertion gets a test that fails when that assertion is removed. Verify each by removal, not by assertion.
- [ ] **Step 9: Gates + commit**

```bash
git add press.html privacy.html scripts/theme-doctor.py tests/test_theme_doctor.py
git commit -m "feat(themes): gate the dress press and privacy borrow

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Scope the reads-check per resolution group, and cover what PR #96 left untested

**Files:**
- Modify: `scripts/theme-doctor.py`, `tests/test_theme_doctor.py`

**Interfaces:**
- Consumes: `check_theme_reads_only_what_it_defines` (`scripts/theme-doctor.py:566`), `EXTERNAL_STYLESHEETS` (`:563`), its call site (`:1227`).
- Produces: the reads-check now takes a resolution group rather than the whole theme. Report the new signature.

- [ ] **Step 1: Reproduce the hole three times.** The check pools `defined` across every theme stylesheet, but no consumer loads every theme stylesheet. Three groups actually ship: `{utility.css}` alone (press/privacy), `{product.css + product-tokens.css}` alone (the 15 generated plugin pages — `render-plugin-pages.py` concatenates exactly those two, no `tokens.css`), and `{reading.css + reading-tokens.css}`. Delete the `--pb-*` definitions from `utility.css` alone, then from `product-tokens.css` alone, then from `reading-tokens.css` alone; confirm the check reports 0 errors each time and that `check_required_tokens` also passes. Record the three results.
- [ ] **Step 2: Scope it.** Rewrite the check to grade per resolution group: a name read by a group must be defined within that same group. Derive the groups from what the code actually serves, not a hand-written list that can drift — `THEME_CSS_HREFS` and `render-plugin-pages.py`'s concatenation are the sources of truth.
- [ ] **Step 3: Scope the external source too.** `EXTERNAL_STYLESHEETS = ("Design/editorial.css",)` is currently pooled theme-wide, so `product.css` could read an `--ed-*` name and pass despite no product consumer loading editorial.css. Attach each external source to the group that actually loads it.
- [ ] **Step 4: Confirm the three reproductions now fail.** Same three deletions from Step 1; each must now produce an error naming the group and the undefined name.
- [ ] **Step 5: Cover the two other untested behaviors.** `grep` confirms `tests/` references neither `check_theme_reads_only_what_it_defines` nor `EXTERNAL_STYLESHEETS`, and the "none of the N declared contrastPairs resolve" error added in PR #96 is unpinned — the three tests touching `_check_archetype` all pass `pairs=None`, exercising only the other branch. Write a test for each, and verify each fails when its line is deleted. This is a repeat of a class this codebase already caught once, where a one-character typo made the doctor print "unverified" and exit 0.
- [ ] **Step 6: Gates + commit**

```bash
git add scripts/theme-doctor.py tests/test_theme_doctor.py
git commit -m "fix(themes): grade each stylesheet group by what that group actually loads

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Commit the visual harness

**Files:**
- Create: `scripts/visual-diff.py`, `tests/test_visual_diff.py`

**Interfaces:**
- Consumes: `scripts/freeze-theme.py`'s `_DETERMINISTIC_CAPTURE_INIT_SCRIPT` and its SMIL freeze (`window.__freezeSvgAnimations`); `scripts/browser_origin.py` for off-origin isolation.
- Produces: a CLI Task 4 wires into CI. Report its exact invocation, its exit-code contract, and where it writes artifacts.

- [ ] **Step 1: Read the four harnesses PR #96 built.** They are described in `.superpowers/sdd/2026-08-04-bespoke-conformance/task-{1,2,3,4}-report.md` — pixel, computed-style, hover, and dress-reachability. Consolidate rather than reinvent; those reports also record several traps already paid for, including a hover harness that reported a false pass and was caught only by disbelieving a convenient result.
- [ ] **Step 2: Build the two-tree runner.** Serve a base ref (from a throwaway worktree) and the working tree on separate ports. **Never golden images** — a pinned Pillow is byte-stable on one OS but FreeType rasterizes differently across platforms, so committed references built on ubuntu would diff forever on Windows.
- [ ] **Step 3: The pixel channel.** Full-frame, filters ON, no masking, no envelope, at a configurable width list defaulting to 1440/768/390. Use the shipped init script and freeze SMIL — an unfrozen SVG animation reads as up to 1.18% "noise" at 390px and cost a prior milestone real time.
- [ ] **Step 4: The computed-style channel.** Sample across every element; report differing values with element and property named.
- [ ] **Step 5: The hover channel, with the blocker fixed.** The subject list MUST union the `:hover` rules of every stylesheet the page LINKS, not only the page's own — the PR #96 derivation samples only page-owned rules, which reports false passes on exactly `press.html` and `privacy.html`, which own none of their hover rules. Keep the `element.matches(':hover')` self-assertion in the same evaluate call that reads the values, and keep failing loudly rather than swallowing hover exceptions. Read the hovered element's whole subtree, since a hover rule can repaint a descendant.
- [ ] **Step 6: Prove every channel bites.** Perturb a token and confirm each channel fails and names affected selectors. Then the one that matters: change a `:hover` rule in `utility.css` and confirm the hover channel fails on press/privacy — that is the case the old derivation missed and the reason this task exists.
- [ ] **Step 7: Document the non-coverage in the module docstring.** `:focus-visible`, `:active`, `::selection`, print and forced-colors stylesheets are unsampled; no two-tree diff can distinguish an intended redesign from an accident. A committed harness that reads as more coverage than it has is worse than none.
- [ ] **Step 8: Test it.** Unit-test the parts that do not need a browser — group derivation, hover-subject union, exit-code contract, argument handling.
- [ ] **Step 9: Gates + commit**

```bash
git add scripts/visual-diff.py tests/test_visual_diff.py
git commit -m "feat(scripts): commit the two-tree visual harness

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Wire it into CI, verify the branch, ship held

**Files:**
- Create: `.github/workflows/visual-diff.yml`
- Modify: `CLAUDE.md` (document the harness and the utility gate under the existing tools/theme sections)

- [ ] **Step 1: Wire the workflow.** `workflow_dispatch` with a base-ref input, plus an opt-in PR label. **Never on every push** — a full sweep is 12+ minutes. **Never inside `rotate-theme.yml`** — on the 1st every pixel is supposed to move, so a pixel gate there is meaningless. Install Playwright the way `rotate-theme.yml` does.
- [ ] **Step 2: Prove the whole thing end to end.** Build a scratch theme that satisfies every token requirement but drops load-bearing `utility.css` rules; confirm `theme-doctor --browser --require-browser` FAILS it and names what is missing. Then confirm the same scratch theme visibly re-dresses press and privacy when its rules are intact — the gate must reject a broken theme without rejecting a merely different one. Delete the scratch theme.
- [ ] **Step 3: Whole-site verification.** Every page in `content/page-archetypes.json` at 1440 and 390 versus `origin/main`, using the harness you just committed — its first real job is verifying its own branch. Base-vs-base self-check first. True 0-pixel required everywhere.
- [ ] **Step 4: Full gates.** `render-hub.py --check`, `render-plugin-pages.py --check`, `pytest tests/ -q`, `site-doctor.py --report`, `theme-doctor.py phosphor-blueprint --browser --require-browser`.
- [ ] **Step 5: Push and open the PR, HELD.** Title `feat(themes): the borrowed dress gets a gate`. Body: what changed and why press/privacy keep wearing the theme rather than owning their dress; the computed-outcome approach and why a selector manifest was rejected; the three reproductions of the reads-check hole and their closure; the harness's channels, its invocation, and its documented non-coverage; the whole-site pixel table. **State plainly that this stacks on PR #96 and must merge after it.** End with exactly `🤖 Generated with [Claude Code](https://claude.com/claude-code)` and no other emoji. Run `gh pr checks --watch`. **Do not merge.**

---

## Self-review notes

- **Spec coverage:** browser rendering (T1 S4), computed-outcome gate (T1 S5, rejecting the selector manifest per the spec's explicit reasoning), font self-import (T1 S3), per-group reads scoping (T2), the three untested behaviors (T2 S5), the harness with its hover blocker fixed (T3 S5) and non-coverage documented (T3 S7), CI wiring with both prohibitions (T4 S1), and the "prove a broken theme fails" success criterion (T1 S6, T4 S2). Out-of-scope items — splitting utility, redesigning either page, September, and the four batched PR #96 follow-ups — appear nowhere.
- **Every gate is proven by failure**, never by existence: T1 S6, T1 S8, T2 S1/S4/S5, T3 S6. That is the discipline the prior milestone converged on after a harness reported a false pass.
- **Type consistency:** T1 reports its check's name and signature for T4 Step 2; T2 reports the reads-check's new signature; T3 reports the CLI invocation and exit-code contract that T4 Step 1 wires and T4 Step 3 runs.
