# Task 5 report: whole-theme gate, the record, the queue, the held PR

**Status:** DONE_WITH_CONCERNS (two findings the brief did not anticipate, both reported in the PR body rather than hidden or reverted)
**Branch:** `feat/slate-broadsheet`, HEAD `b50f46f` on top of `213b1bb`
**PR:** https://github.com/626Labs-LLC/626Labs-LLC.github.io/pull/115, held, targeting `main`, label `visual-diff`, NOT merged
**Date:** 2026-09-03 / 04

## Commits this task

| SHA | Message | What |
|---|---|---|
| `bd07347` | `fix(pages): thesis title and privacy label take solid ink, theme-neutral AA` | `thesis.html` `.hero-l h1 .gt { color: var(--cyan); }` (gradient, clip, transparent fill dropped); `privacy.html` `.tldr-label { color: var(--fg-2); }`. 2 files, +2/-5. |
| `93eb8d1` | `docs(design): the Slate Broadsheet preview record, 29 captures for the judge` | `Design/explorations/2026-09-03-paper-and-ink/theme-preview/<page>-<width>.png`, 29 files, ~40 MB. |
| `b50f46f` | `feat(themes): queue the Slate Broadsheet for the October rotation` | `content/themes.json` queue `["slate-broadsheet"]`; `themes.html` re-rendered (+9 lines, the Queued card). |

`content/site.json` untouched. `content/themes.json` `active` never flipped in any commit (flipped in the working tree for under two minutes to render the plugin previews, restored by `git checkout`, blob `42736c7` before and after). No rendered slate page in any commit.

## Step 1: the gate

`python scripts/theme-doctor.py slate-broadsheet --browser --require-browser` at `213b1bb`: 24 contrast lines (six pairs on four archetypes: 9.18 / 6.90 / 5.22 / 5.64 / 4.65 / 4.85, all pass), `PASS slate-broadsheet`, **exit 0**. No gate finding, no check rejected anything the design got right, so no gate change on this branch. Log: scratchpad `t5-doctor.log`.

## Step 2: the record

`render-hub.py --theme slate-broadsheet --out <scratch>/t5-preview` (index plus the nine theme-css pages). Served the repo root with the preview laid over it (`t5-shoot.py`, a `SimpleHTTPRequestHandler` whose `translate_path` prefers the preview dir), Chromium via Playwright at DPR 1, `reduced_motion: reduce`, lazy images forced eager and the page scrolled through in 600px steps before capture, fonts awaited, off-origin allowed except `gc.zgo.at`.

| Capture | scrollWidth/clientWidth at 1440 / 768 / 390 | console | pageerrors |
|---|---|---|---|
| index | 1440/1440, 768/768, 390/390 (h 10727 / 15416 / 23998) | 1 (the analytics abort) | 0 |
| press | equal at all three | 1 | 0 |
| privacy | equal | 1 | 0 |
| thesis | equal | 1 | 0 |
| workflow | equal | 1 | 0 |
| conundrum | equal | 1 | 0 |
| rororo | equal | 1 | 0 |
| vibe-cartographer (registry flipped) | equal | 0 | 0 |
| plugins (registry flipped) | equal | 0 | 0 |
| about + slate `reading.css` link (1440, 390) | equal | 1 | 0 |

The one console line everywhere is `Failed to load resource: net::ERR_FAILED`, the harness's own abort of `gc.zgo.at/count.js`. `document.fonts.check("16px 'Source Serif 4'")` true on every capture; body background `rgb(58,67,80)`.

The thesis and privacy captures were taken with the Step 3 edits already in the working tree, so the record shows what the 1st ships (solid cyan "sustainable.", `--fg-2` label).

**Plugin-page restore, evidenced.** Registry flipped by script, `render-plugin-pages.py` (15 rendered), shot, `git checkout -- content/themes.json` (`git hash-object` `42736c7` = index blob), `render-plugin-pages.py` again (15 rendered back), then the CRLF phantom: 15 pages ` M` with `git hash-object` == `git ls-files -s` blob on all 15, `git checkout --` each. Tracked status afterwards: exactly `thesis.html`, `privacy.html` (my Step 3 edits). `render-plugin-pages.py --check`: up to date.

Eyeballed crops (scratchpad `t5-crop-*.png`): the broadsheet front page with masthead, dateline, strip, lead, four-note rail with the "More Field Notes (6)" expander, plate on its mat; thesis with the cyan headline word; privacy with the paper label on the gradient field.

## Step 3: the named exception

Edits as specified. Blast radius:

- `visual-diff.py origin/main --widths 1440,390 --self-check`: **PASS, exit 0**, 40 pages, 1024s, 26 coverage notes (all pre-existing non-coverage; one `index.html@390` 369-px blip not reproduced on recapture, demoted). Run at `--widths 1440,390` deliberately, the same shape as both real sweeps, so it is the noise baseline for what they measure.
- `visual-diff.py origin/main --pages thesis.html privacy.html --widths 1440,390`: **exit 1, 92 findings, thesis.html 46 + privacy.html 46, nothing else.** thesis: pixel 13,845 px at 1440 / 3,893 at 390 inside the headline bbox; computed 23/80,640 all on `span.gt`. privacy: pixel 596 px at both widths inside the label bbox; computed 21/64,080 all on `div.tldr-label` (`rgb(23,212,250)` to `rgb(168,194,217)`). 85s.

Decision logged to the dashboard (`V14L0A2xCde1MBEgSi3k`).

## Step 4: site gates and the full sweep

At `93eb8d1` (re-run after the resume, same result): `render-hub.py --check` 0; `render-plugin-pages.py --check` 0; `pytest tests/ -q` **465 passed**; `site-doctor.py --report` **checks: PASS**.

Full sweep `visual-diff.py origin/main --widths 1440,390`, run as three foreground batches (14/13/13 pages from `page_list()`, the tool's 10-minute ceiling; the self-check took 17 minutes) in `t5-vd-full{1,2,3}.log`: 436s + 346s + 328s. **435 findings on 10 pages, 30 clean.**

| Page | Findings | Cause |
|---|---|---|
| thesis.html | 46 | Step 3 |
| privacy.html | 46 | Step 3 |
| about.html | 41 | serif (below) |
| editorial/index.html | 46 | serif |
| editorial/2026-05-24-vibe-walk-launch/ | 40 | serif |
| editorial/2026-05-29-same-code-triple-thinking/ | 46 | serif |
| editorial/2026-06-26-the-first-626-day/ | 46 | serif |
| editorial/2026-07-03-rororo-grew-a-family/ | 38 | serif |
| editorial/vibe-insights-build-2026-05-23/ | 46 | serif |
| editorial/vibe-wrap-build-2026-05-23/ | 40 | serif |
| every other page (30, incl. all 15 plugin pages, press, workflow, conundrum, rororo, themes, legal, 404) | 0 | |

**FINDING 1 (not anticipated by the brief or the plan): the Source Serif 4 addition changes eight live pages today.** `Design/editorial.css:29` declares `--font-serif: 'Source Serif 4', 'Iowan Old Style', 'Georgia', serif` on `origin/main` (unchanged on the branch). No `@font-face` existed, so the eight pages that link `editorial.css` fell to Iowan/Georgia. `387a28a`'s two `@font-face` blocks in `fonts/fonts.css` make the stack resolve; the pages reflow (every finding is a height/position, zero `font-family` values differ, and the failing set is exactly the eight `editorial.css` consumers; `thesis.html`/`workflow.html` read `--font-serif` zero times and are unaffected beyond Step 3). The spec called this "also fixes the Georgia fallback on the editorial layer"; the plan's Step 3 said "expect 0 findings because nothing live changes." The sweep is the truth. Not reverted (October needs the font, and the rotation cannot add an `@font-face` on the 1st); named in the PR body as a second live change with a recommendation to let it land. Decision logged (`8IZUit3zA2SbUXqXmeYE`).

## Step 5: the queue

`content/themes.json` queue `["slate-broadsheet"]`. `python -c "...; print(r.validate(r.load()))"` printed **`[]`**. Plain `render-hub.py` rebuilt only `themes.html` (+9 lines: `theme-card queued`, "Queued", "October 2026", "The Slate Broadsheet", "The page is printed, not lit."); `about.html` unchanged (queued themes are deliberately not offered to the picker, `render-hub.py:980`); `render-hub.py --check` exit 0. Committed `b50f46f`.

**FINDING 2 (by design, but a third live change):** `render_themes_gallery` renders the queue, and `--check` grades `themes.html`, so queueing moves the live gallery. Targeted `visual-diff.py origin/main --pages themes.html --widths 1440,390` after the commit: 48 findings, page +183px at 1440 (1928 to 2111), +173px at 390, 429/426 computed values on the card and what it pushes down. Stated in the PR body.

**Dry run:** `rotate-theme.yml`'s `workflow_dispatch` takes only `dry_run`, and its checkout step hardcodes `ref: main`, so a dispatch at `feat/slate-broadsheet` would gate main's empty queue and only log "Queue is empty". Not fired; it is Este's to fire after merge (`gh workflow run rotate-theme.yml -f dry_run=true`).

## Step 6: the PR

https://github.com/626Labs-LLC/626Labs-LLC.github.io/pull/115, `feat(themes): the Slate Broadsheet, queued for October`, base `main`, 23 commits (includes #114's eight, `699d016..16d3c29`; body says #114 closes as superseded on merge). Body order as specified, plus the serif section between the exception and the gallery note. Ends with the sanctioned trailer. Label `visual-diff` applied at creation so the CI sweep runs. **Not merged.**

`gh pr checks 115 --watch`: `doctor` (content-health.yml) **pass**, 22s. `sweep` (visual-diff.yml, the label) **fail**, 18m49s, run 33837248548: that is the workflow's exit-1 route ("differences found"), the expected outcome for a branch that moves pixels. CI ran the same shape as the local sweeps (base `74b56af`, `--widths 1440,390`, three channels): **500 findings on 11 pages, 29 clean** in 1082s. The 11 are the local sweep's 10 (thesis, privacy, about, the seven `editorial/` pages) plus `themes.html`, which entered after the queue commit `b50f46f`. No other page moved in CI either. Note the first attempt never swept: `gh pr create --label visual-diff` fired `opened` (label not yet attached, `if:` skipped, run 33837148686) and `labeled` (run 33837148702) within the same second, and the per-PR `cancel-in-progress` group cancelled the labeled run at 2s. Re-triggered by removing and re-adding the label. The workflow comment that says a PR created with the label is "the ordinary case" is not true for `gh pr create --label`; see concern 7.

## Concerns and hand-offs

1. **The brief's "nothing live moves" was two pages short of three-page classes.** Step 3 was named; the serif on eight editorial-layer pages and the gallery card were not. Future theme plans should run the full sweep BEFORE writing the "expect 0 findings" line; a face or token that a live stylesheet already reads is a live change.
2. **The record weighs ~40 MB** (29 full-page PNGs, the 390 captures up to 24,000px tall). Committed as the brief asked; if repo weight matters, a follow-up can quantize or move them to a release asset.
3. **`render-hub.py` has no `--help`**; the bare flag runs a real render (it reported no change, tree stayed clean). Worth an argparse guard.
4. **Foreground ceiling vs sweep length.** A 40-page two-width sweep runs 17 minutes as a self-check and ~18 minutes as three batches; anything longer than 10 minutes has to be batched by `--pages` or backgrounded. The batches used `page_list()` itself, so coverage is the same 40.
5. **GitNexus `detect_changes` could not run** (no `mcp__gitnexus__*` tool in this session); the change scope was verified by `git diff --stat` per commit and the sweep instead.
6. **Scratch artifacts** (all `t5-*` prefixed): `t5-doctor.log`, `t5-shoot.py`, `t5-shoot-{pages,plugins,about}.json`, `t5-vd-selfcheck{,.log}`, `t5-vd-two{,.log}`, `t5-vd-full{1,2,3}{,.log}`, `t5-vd-themes{,.log}`, `t5-pr-body.md`, `t5-pr-checks.log`.
7. **`visual-diff.yml` double-fires on `gh pr create --label`.** `opened` arrives without the label (the CLI attaches it in a second call), so that run skips; the `labeled` run that should sweep gets cancelled by the per-PR `cancel-in-progress` group when the `opened` run is still queued alongside it. Net: zero sweeps on creation. Cheapest fix: exclude `opened` runs from the concurrency group, or make the group key include `github.event.action`. Until then: add the label after creation, or remove and re-add it.

## Final fix wave

The whole-branch review's rotation-morning simulation (progress.md, "FINAL WHOLE-BRANCH REVIEW") aborted at two gates with slate active. This wave lands the two fixes plus the write-once archive fix, and re-runs the simulation at the new HEAD until every gate is green.

**Commit:** `4fa8f99` `fix(themes): rotation morning ships — capture before render, archive base href, reads test accepts the token file as reader`. Six files: `.github/workflows/rotate-theme.yml`, `scripts/freeze-theme.py`, `scripts/render-hub.py`, `tests/test_freeze_theme.py`, `tests/test_theme_doctor.py`, `themes/slate-broadsheet/tokens.css`. `content/site.json` and `content/themes.json` untouched.

### C1: the pytest gate (`tests/test_theme_doctor.py`)

`test_dropping_a_treatment_prefix_from_one_group_fails_that_group` asserted every reads-error starts with `expected_reader` (`archetypes/product.css` for the `product-tokens.css` case) and names `consumer` (`plugins/*/index.html`). That is Phosphor Blueprint's shape. Slate's `product-tokens.css` reads `--sb-ground`, `--sb-hair-color`, `--sb-rule-color` inside itself, so stripping the private definitions makes the token file the first reader to report, in BOTH groups it belongs to (the hand-authored product pages load it alone; the plugin pages load it with `product.css`). Fix: a reads-error may start with `expected_reader` OR the stripped label itself; its group must be one the label belongs to (derived from `resolution_groups`, not spelled); `consumer` must still be among those groups and named by at least one error. `assert errs` is unchanged.

**Mutation:** replaced `errs = _reads_errors_for_live_theme({label: stripped})` with `errs = []`, ran the three parametrized cases: `3 failed, 120 deselected in 0.56s`, each on `AssertionError: deleting <label>'s private token definitions produced no error`. Restored; `grep -c MUTATION` is 0.

### C2: the render-drift gate (`rotate-theme.yml`)

"Capture the incoming theme's screenshot" moved from after "Render the new active theme" to before it, with a comment naming `_theme_thumbnail_href` as the reason. `capture_theme_screenshot` renders via `--theme <slug> --out <tmp>` and never reads the committed pages, so the swap changes nothing about what it captures. The order comment at the top of the file now names the capture. `yaml.safe_load` parses; no `${{ }}` inside a comment; `test_render_hub.py`'s derived-page-list test still passes (it reads command lines, not step order).

### I1: the write-once archive (`scripts/freeze-theme.py`)

`freeze()` injects `<base href="/">` right after the robots meta. The localized stylesheet hrefs were bare filenames (`href="tokens.css"`), which `<base>` would have re-pointed to `/tokens.css`; they are now root-absolute archive paths (`/themes/archive/<month>/<file>`). Two more `<base>` consequences, checked in the browser: fragment links (`href="#work"`, seven of them plus the skip link) stay as written because the page's own `wireNav` intercepts every `a[href^="#"]` click and scrolls in-page (with scripts off they resolve to the live homepage's section, accepted and documented); the nav mark's `stroke="url(#navg)"` resolves as a same-document reference regardless of base (CSS Values 4 local urls). Module docstring extended beside the other accepted boundaries. Tests: `test_freeze_injects_base_href_so_relative_paths_resolve_against_the_live_root` added; the three tests asserting bare-filename hrefs updated to the archive-absolute form. `tests/test_freeze_theme.py`: 13 passed.

### Minors

`_theme_render_opts` docstring: `railLimit` folds the overflow into a `<details>` block, no "door". `themes/slate-broadsheet/tokens.css` header: `theme.json`'s `status` is informational, nothing reads it, PB's says `live`, read the registry.

### Live tree (theme inactive), before commit

`render-hub.py --check` 0, `render-plugin-pages.py --check` 0, `site-doctor.py --check` 0, `pytest tests/ -q`: `467 passed in 5.75s`.

### The proof: rotation morning re-run at `4fa8f99`

Scratch: `git clone` of the repo into the scratchpad, HEAD verified `4fa8f99b91e58393c9f69738b993076ce427b1b7` on both sides. Steps in the corrected workflow order, each logged with its exit code:

| Step | Exit | Verbatim last line |
|---|---|---|
| `freeze-theme.py 2026-09` | 0 | `froze theme to ...\sim-tree\themes\archive\2026-09` |
| `freeze-theme.py --screenshot phosphor-blueprint ...` | 0 | `captured phosphor-blueprint -> assets\themes\phosphor-blueprint.png` |
| `theme_registry.rotate(reg, "2026-09")` (the workflow's own snippet) | 0 | `new_active=slate-broadsheet`; registry now `active: slate-broadsheet`, `queue: []`, `archive: [{phosphor-blueprint, 2026-09, /themes/archive/2026-09/}]` |
| `freeze-theme.py --screenshot slate-broadsheet ...` (now BEFORE render) | 0 | `captured slate-broadsheet -> assets\themes\slate-broadsheet.png` |
| `render-hub.py` | 0 | |
| `render-plugin-pages.py` | 0 | |
| **Gate** `theme-doctor.py slate-broadsheet --browser --require-browser` | **0** | `PASS slate-broadsheet` |
| **Gate** `render-hub.py --check` | **0** | `index.html, feed.xml, sitemap.xml and 6 Field Note page(s) are up to date.` |
| **Gate** `render-plugin-pages.py --check` | **0** | `plugin pages up to date.` |
| **Gate** `pytest tests/ -q` | **0** | `466 passed in 5.51s` |
| **Gate** `site-doctor.py --check` | **0** | (silent on pass; 0 bytes of output) |

466 vs the live tree's 467: the queue-time static gate parametrizes over `content/themes.json`'s active plus queued slugs, two themes before rotation and one after. The theme-doctor browser checks print nothing on success; `--require-browser` turns an unavailable browser into a gate failure, so exit 0 means they ran.

**Archive audit.** Scratch root served on an ephemeral port, `/themes/archive/2026-09/` loaded in Chromium with off-origin blocked, scrolled end to end: **35 first-party responses, 0 at 4xx or above.** `<base>.href` is the origin root; stylesheets applied are `/themes/archive/2026-09/tokens.css`, `/widget-bacon-trail/widget.css` (the documented live exclusion), `/themes/archive/2026-09/widget-box-office__widget.css`, `/themes/archive/2026-09/widget-tag-that-line__widget.css`; body font resolves to Inter; polygon stroke `url("#navg")`; clicking `a[href="#work"]` leaves the URL at `/themes/archive/2026-09/`. First attempt of this audit failed before loading anything: Git Bash rewrote the `/themes/archive/2026-09/` argument to a Windows path; rerun with `MSYS_NO_PATHCONV=1`.

**What the rotation commit would carry** (scratch `git status`): `content/themes.json`, `index.html`, `themes.html`, `about.html`, the nine theme-css pages, the 15 plugin pages, `assets/themes/phosphor-blueprint.png` (recaptured), new `assets/themes/slate-broadsheet.png` and `themes/archive/2026-09/` (index.html plus three localized stylesheets).

**Teardown.** Scratch clone deleted. Live tree: no tracked changes; `content/themes.json` still `active: phosphor-blueprint`, `queue: ["slate-broadsheet"]`, `archive: []`; no `themes/archive/`; `assets/themes/` holds only `phosphor-blueprint.png`.

### PR #115

Body updated: the "pytest 465 passed" line now says the four site gates were measured with the theme INACTIVE (467 today), followed by a "Rotation morning, simulated with slate active" paragraph naming the two aborted gates, the fixes, the archive fix, and the green re-run; the "Rotation rehearsal" section says the workflow cannot be fired from a branch but the gate stack was; "What merging changes" notes the workflow and freeze changes are inert until the 1st. Everything else kept, trailer intact.

`gh pr checks 115` on `4fa8f99`: `doctor` **pass**, 22s (run 33839727380). `sweep` **fail**, 18m8s (run 33839727320), the exit-1 route ("visual-diff found differences (exit 1)"), base `74b56af`, 40 pages, `--widths 1440,390`, three channels, 1038s: **500 findings on 11 pages, 29 clean**, the identical set to the pre-fix run (thesis 46, privacy 46, about 46, the seven `editorial/` pages 39 to 46, themes.html 48). Nothing this wave touched renders on a swept page, so the set did not move. The report commit that follows is docs-only and re-triggers both checks; its results are the same shape by construction.
