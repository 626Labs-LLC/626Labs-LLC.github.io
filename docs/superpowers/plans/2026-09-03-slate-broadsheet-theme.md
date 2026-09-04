# The Slate Broadsheet Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the judged remix sheet into `themes/slate-broadsheet/`, an eleven-file theme that passes every gate and sits in `content/themes.json`'s queue before 2026-10-01 09:00 UTC.

**Architecture:** Seed the theme directory by copying Phosphor Blueprint (the documented path), then replace it piece by piece: tokens first so every gate is green from the start, then the four archetype dresses, each built from the remix sheet's idiom. The design is fixed at `Design/explorations/2026-09-03-paper-and-ink/sheet-slate-broadsheet.html`; nothing here redesigns it. Spec: `docs/superpowers/specs/2026-09-03-slate-broadsheet-theme-design.md`.

**Tech Stack:** static HTML/CSS, Python 3.12 (theme-doctor, render-hub, render-plugin-pages, build-fonts with fontTools+brotli), Playwright.

## Global Constraints

- Branch `feat/slate-broadsheet` (stacked on `feat/paper-and-ink-bakeoff`, PR #114). Conventional commits; trailer `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`; no emoji anywhere except the one sanctioned PR-body trailer.
- **The design is the remix sheet.** Every archetype dress is that sheet's idiom applied to that archetype's markup. A builder who improves on the sheet has drifted; a builder who copies its tokens and furniture faithfully has not.
- **Slug `slate-broadsheet`, name "The Slate Broadsheet", month `2026-10`, ground `#3A4350` as `--sb-ground`.** The 47 `REQUIRED_TOKENS` (`scripts/archetypes.py`) must be defined in ALL FOUR of `tokens.css`, `archetypes/product-tokens.css`, `archetypes/reading-tokens.css`, `archetypes/utility.css`. `product-tokens.css` and `reading-tokens.css` are tokens-only (gated). No `--pb-*` name anywhere. No reference to `phosphor-blueprint` anywhere in the theme, including relative hrefs (`check_theme_references_only_itself`).
- **Matte.** No glow, bloom, scanline, grid, gradient field, or `.pb-scanlines` rule. Page markup keeps that div; the theme paints nothing on it.
- **AA:** every text/ground pair 4.5:1 (3:1 large), documented with ratios where a new pair is introduced. Magenta `#f22f89` is 2.64:1 on slate and is never text. `--ed-link` is never text.
- **Every token any consumer reads resolves in that consumer's own group.** Groups: `{utility.css}` alone for press/privacy; `{product.css + product-tokens.css}` for the 15 generated pages; `{product-tokens.css}` alone for the four bespoke product pages; `{reading-tokens.css}` alone for thesis/workflow; `{reading.css}` + `Design/editorial.css` for about; `{archetypes/home.html + tokens.css}` + widget.css for index; `{tokens.css}` for themes.html.
- **The gate that matters:** `python scripts/theme-doctor.py slate-broadsheet --browser --require-browser` exit 0. Per-task, a builder may tolerate failures in archetypes it does not own and must report them; Task 5 requires the whole thing green. `--browser` needs Playwright; if chromium is missing, `python -m playwright install chromium`.
- **Nothing on this branch changes the live site.** `content/themes.json` is touched only in Task 5 to append the slug to `queue`. `render-hub.py --check`, `render-plugin-pages.py --check`, `pytest tests/ -q`, `site-doctor.py --report` must stay green throughout — the theme is present but not active.
- Retry `git commit` on index lock; Tasks 2, 3 and 4 run concurrently on disjoint files.

## File map

| File | Task |
|---|---|
| `fonts/SourceSerif4-Variable.ttf`, `fonts/SourceSerif4-Italic-Variable.ttf`, their `.woff2`, `fonts/fonts.css`, `scripts/build-fonts.py` | 1 |
| `themes/slate-broadsheet/tokens.css`, `theme.json`, `archetypes/product-tokens.css`, `archetypes/reading-tokens.css`, the token block of `archetypes/utility.css` | 1 |
| `themes/slate-broadsheet/archetypes/home.html` | 2 |
| `themes/slate-broadsheet/archetypes/product.html`, `product.css` | 3 |
| `themes/slate-broadsheet/archetypes/utility.html`, `utility.css` (dress half), `reading.html`, `reading.css` | 4 |
| `content/themes.json` (queue), `assets/themes/slate-broadsheet.png` if the gallery needs it pre-rotation, `CLAUDE.md` if any instruction changed | 5 |

---

### Task 1: Foundation — fonts, tokens, and a theme that passes the static doctor before any dress changes

**Files:**
- Create: `themes/slate-broadsheet/` (copy of `themes/phosphor-blueprint/`, then edited), `fonts/SourceSerif4-Variable.ttf`, `fonts/SourceSerif4-Italic-Variable.ttf`, both `.woff2`
- Modify: `scripts/build-fonts.py`, `fonts/fonts.css`, `tests/` if a font count is pinned

**Interfaces:**
- Produces: the `--sb-*` treatment token names (report them), the exact value of every one of the 47 tokens (in the files), and the serif face name `'Source Serif 4'` available via `/fonts/fonts.css`. Tasks 2-4 consume all three.

- [ ] **Step 1: Self-host Source Serif 4.** Add the variable roman and italic TTFs (SIL OFL, from the upstream release) to `fonts/` following exactly how `scripts/build-fonts.py` already fetches and converts JetBrains Mono (`JBMONO_URL` pattern), run it to produce the woff2 pair, add two `@font-face` blocks to `fonts/fonts.css` mirroring the Inter pair (weight range, `font-display: swap`). Verify in a browser that a page reading `--font-serif` renders Source Serif 4 and not Georgia.
- [ ] **Step 2: Seed the theme.** `cp -r themes/phosphor-blueprint themes/slate-broadsheet`. Then `grep -rn "phosphor" themes/slate-broadsheet` and replace every reference, including the four hardcoded slugs in `archetypes/home.html` and any in comments, so `check_theme_references_only_itself` passes before anything else.
- [ ] **Step 3: Rewrite `tokens.css`.** Base block: all 47 names for slate. `--bg-0: var(--sb-ground)` `#3A4350`; `--bg-1`/`--bg-2` one and two steps lighter (the remix sheet's mat and rail tones); `--fg-1/2/3/muted` from the paper-tones-inverted ink ramp the sheet declares, every one 4.5:1 on `--bg-0` and `--bg-1`; `--cyan` unchanged (5.64:1 link ink); `--magenta` unchanged but never text; `--border-1/2` pale hairlines at low alpha; `--border-accent` cyan at alpha; `--brand-gradient` and `-soft` kept as the color bar recipe only; `--inner-stroke`, `--ok`, spacing, radii, durations, ease from PB unchanged where the sheet does not override; `--font-display` Space Grotesk, `--font-body` `'Source Serif 4', 'Iowan Old Style', Georgia, serif`, `--font-mono` JetBrains Mono. Then a `--sb-*` treatment block for the newspaper furniture the sheet declares (rule weights, mat tone, folio tab, screen). Delete the entire `--pb-*` block and every CRT rule that follows it. Pin `h1, h2, h3, h4, h5, h6, p { color: var(--fg-1) }` at the base so the dark-site base stylesheet cannot leave a heading white on slate.
- [ ] **Step 4: Rewrite the three other token files.** `archetypes/product-tokens.css` and `archetypes/reading-tokens.css`: the same 47 in slate, tokens only, nothing else. `archetypes/utility.css`: replace its token block with the same 47 in slate; leave its dress half for Task 4 (it will still be PB's dress for now, and that is expected).
- [ ] **Step 5: `theme.json`.** `{"name": "The Slate Broadsheet", "slug": "slate-broadsheet", "thesis": "The page is printed, not lit.", "month": "2026-10", "status": "queued", "contrastPairs": [["--fg-1","--bg-0"],["--fg-2","--bg-0"],["--fg-3","--bg-1"],["--cyan","--bg-0"]]}`.
- [ ] **Step 6: Gate.** `python scripts/theme-doctor.py slate-broadsheet` (static) must PASS: 47/47 in all four token files, tokens-only on the two token files, reads-check clean per group, no foreign slug, contrast pairs graded with ratios. Then `--browser`: report which archetype checks pass and which fail; failures in the dress half of product/utility/reading are EXPECTED at this stage (they still wear PB's dress on slate tokens) and are handed to Tasks 2-4. The home shell will also still be PB's; note it. Then the four site gates (`render-hub --check`, `render-plugin-pages --check`, `pytest`, `site-doctor --report`) must all stay green — the theme is not active.
- [ ] **Step 7: Commit**

```bash
git add fonts scripts/build-fonts.py themes/slate-broadsheet tests
git commit -m "feat(themes): seed the Slate Broadsheet, slate tokens in all four files, Source Serif 4 self-hosted

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: The home shell — the remix sheet becomes `archetypes/home.html` with all twelve zones

**Files:**
- Modify: `themes/slate-broadsheet/archetypes/home.html`

**Interfaces:**
- Consumes: Task 1's tokens and `--sb-*` names; the remix sheet as the design; PB's `archetypes/home.html` as the zone-marker and machinery reference (3,025 lines: the twelve `SITE_JSON:<zone>:start/end` markers, the About star-map markup and JS, the Bacon Trail and game widget mounts, the lab-runs frames, analytics, skip link).
- Produces: a shell `render-hub.py --theme slate-broadsheet --out <dir>` fills from `content/site.json` with no unknown-zone or missing-zone error.

- [ ] **Step 1: Inventory the zones.** From PB's shell, list every `SITE_JSON` marker and what render-hub emits into it (read `render_*` functions in `scripts/render-hub.py` for the markup each zone produces: the shell wraps it, it does not author it). The shell's job is chrome and section skeletons around those markers.
- [ ] **Step 2: Port the sheet's six zones.** Masthead, dateline row with folios, section index (the nav), lead story (hero) with drop cap and plate, front rail (stories), the `01 · Work` section front with the flagship plate and columned listings (products), the founding features page, and the footer with the color bar and the imprint line. The sheet's inline `<style>` becomes the shell's inline `<style>`, retokenized to Task 1's names where it declared its own.
- [ ] **Step 3: Design the six zones the sheet never showed**, in the same idiom, per the spec: hero-chips as a mono "by the numbers" folio line; thinking as a section front with lead plus listings; lab-runs as the photo page with plates on pale mats; play with the widgets lifted onto mats and puzzle-page furniture, widgets keeping their own chrome; about with the star map on a mat under a folio tab; support/contact/lab-pool as the back page's classified columns under `04 · Notices`.
- [ ] **Step 4: Carry the machinery.** The star-map CSS and JS, widget mounts, lab-run frame behavior, and any inline script PB's shell carried must survive verbatim unless the design replaces the element. Nothing in `content/site.json` changes.
- [ ] **Step 5: Render and look.** `python scripts/render-hub.py --theme slate-broadsheet --out <scratch>`; serve the repo root with the preview laid over it; screenshot 1440/768/390 full page. Every zone present and populated with real content. No horizontal scroll at any width, measured. Zero console errors. The widgets mount. The star map draws.
- [ ] **Step 6: Gate.** `theme-doctor slate-broadsheet --browser`: the `home` archetype's checks (zones, chrome, links, contrast, h-scroll, console, pageerror) must pass; report the state of the other three archetypes without fixing them.
- [ ] **Step 7: Commit** — `feat(themes): the Slate Broadsheet home shell, twelve zones` with the trailer.

---

### Task 3: The product dress — a plugin page as a section front

**Files:**
- Modify: `themes/slate-broadsheet/archetypes/product.html`, `themes/slate-broadsheet/archetypes/product.css`

**Interfaces:**
- Consumes: Task 1's tokens (`product-tokens.css` is done; do not touch it); the remix sheet's idiom; PB's `product.html` shell and `product.css` dress as the vocabulary reference (`top`, `hero`, `work`, `brain`, `install`, `family`, `family-card`, `card`, `section-head`); `scripts/render-plugin-pages.py`'s concatenation (dress first because `product.css` opens with `@import`).
- Produces: a dress that renders all 15 generated pages and, via `product-tokens.css` only, the four bespoke product pages.

- [ ] **Step 1: Read what a plugin page is.** `render-plugin-pages.py` and `content/plugin-pages.json`: the components, the live version chip, the JSON-LD, the install block, the family strip. Behavior survives untouched.
- [ ] **Step 2: Design the section front.** One product per page: a reduced masthead (the paper's nameplate, small, top-left, with the section index), a headline that is the product name in Space Grotesk, the tagline as the deck in serif italic, the screenshot as the lead plate on a pale mat with a `PLATE` caption, the description as columned body with a drop cap, the install block as a boxed how-to (hairline box, mono), the family strip as columned listings under a `Also in this section` folio, the footer with the color bar and the imprint line.
- [ ] **Step 3: Write `product.html` and `product.css`.** `product.css` keeps `@import url('/fonts/fonts.css')` as its first rule. Retarget every PB rule; delete every CRT rule. `.pb-scanlines` gets no rule.
- [ ] **Step 4: Render the real pages.** Temporarily set `content/themes.json` `active` to `slate-broadsheet` in the working tree, run `python scripts/render-plugin-pages.py`, serve, screenshot `vibe-cartographer/index.html` and `plugins/index.html` at 1440/768/390, confirm the version chip resolves and the JSON-LD is intact, then **restore `content/themes.json` byte-identical and re-run `render-plugin-pages.py`** so the tree carries no rendered slate pages. `git status` must show only your two theme files.
- [ ] **Step 5: Gate.** `theme-doctor slate-broadsheet --browser`: the `product` archetype's checks must pass, including the reads-check for the `{product.css + product-tokens.css}` group and `{product-tokens.css}` alone. Report the others without fixing them.
- [ ] **Step 6: Commit** — `feat(themes): the Slate Broadsheet product dress` with the trailer. Retry on index lock.

---

### Task 4: The utility and reading dresses — press, privacy, and About's toggle

**Files:**
- Modify: `themes/slate-broadsheet/archetypes/utility.html`, `utility.css` (dress half), `reading.html`, `reading.css`

**Interfaces:**
- Consumes: Task 1's tokens (`reading-tokens.css` and utility's token block are done); the remix sheet's idiom; `press.html` and `privacy.html` as the markup `utility.css` must dress (every selector it needs: `nav.nav`, `.nav-inner`, `.nav-links`, `header.page-hero`, `.page-hero-inner`, `.eyebrow`, `h1.page-title`, `.page-meta`, `main`, `.wrap`, `footer`, `.footer-inner`, `.footer-meta`, `.footer-links`, `a.inline-link`); `about.html`'s `.lnt-*` vocabulary and its picker (`scripts/theme-doctor.py`'s `check_page_renders_dressed` and `VOCABULARY["reading"]`).
- Produces: press and privacy pass the region differential and the three element assertions under this theme; about's picker offers a slate reading dress that renders every `.lnt-*` element.

- [ ] **Step 1: Utility.** Dress press and privacy as inside pages of the paper: the nameplate small in the nav, the page title as a section head with a folio tab, body on the measure, hairline rules, links in cyan with a pale underline, footer with the color bar. Add the imprint sentence as generated content on `.footer-inner::after` (no link possible; documented limit). Every one of the eleven selectors above gets a rule, so the region differential differs on nav, hero, main, footer and the field.
- [ ] **Step 2: Reading.** `reading.css` dresses every `.lnt-*` selector PB's `reading.css` dresses (list them from PB's file; the doctor requires the seven vocabulary classes as selectors). Slate broadsheet idiom: the record rails become folio columns, the frontispiece a masthead, pull quotes in serif italic with a hairline. `reading.html` is the archetype shell the doctor renders; port it. Verify about.html with the slate dress linked over its own style (the picker's action) renders every element and no `.lnt-*` element is left unstyled.
- [ ] **Step 3: Preview the real pages.** `render-hub.py --theme slate-broadsheet --out <scratch>` emits press, privacy, thesis, workflow repointed; serve from repo root with the preview over it; screenshot all four at 1440/768/390. Zero h-scroll, zero console errors, thesis and workflow readable on slate tokens with their own layouts intact.
- [ ] **Step 4: Gate.** `theme-doctor slate-broadsheet --browser`: `utility` and `reading` archetype checks pass, `check_page_renders_dressed` passes on press and privacy under this theme, contrast graded for both archetypes.
- [ ] **Step 5: Commit** — `feat(themes): the Slate Broadsheet utility and reading dresses` with the trailer. Retry on index lock.

---

### Task 5: Whole-theme gate, previews for the record, queue, held PR

**Files:**
- Modify: `content/themes.json` (append slug to `queue`), `CLAUDE.md` if any instruction changed, `docs/theme-archetypes.md` if any contract fact changed

- [ ] **Step 1: The gate.** `python scripts/theme-doctor.py slate-broadsheet --browser --require-browser` exit 0, every archetype, every live page, contrast graded on all four. If any check rejects something the design got right, that is a finding about the gate: report it with evidence, fix the gate, and say so in the PR.
- [ ] **Step 2: The record.** Preview render; screenshots at 1440/768/390 of index, one plugin page, `plugins/index.html`, press, privacy, thesis, workflow, about with the slate reading dress toggled; commit them under `Design/explorations/2026-09-03-paper-and-ink/theme-preview/` for the judge.
- [ ] **Step 3: Site gates with the theme merely present.** `render-hub.py --check` 0, `render-plugin-pages.py --check` 0, `pytest tests/ -q`, `site-doctor.py --report` PASS, `visual-diff.py origin/main --self-check` runs, and a real `visual-diff.py origin/main` reports 0 findings because nothing live changed.
- [ ] **Step 4: Queue it.** Append `"slate-broadsheet"` to `content/themes.json`'s `queue`. `python -c "import sys; sys.path.insert(0,'scripts'); import theme_registry as r; r.validate(r.load())"` passes. Then run the rotation's own rehearsal: `gh workflow run rotate-theme.yml -f dry_run=true` on this branch if the workflow allows a ref, else document that the dry run is Este's to fire after merge.
- [ ] **Step 5: PR, held.** Title `feat(themes): the Slate Broadsheet, queued for October`. Body: the design in one paragraph, the eleven files, the four token-file gate results, the dress-differential result on press/privacy, the screenshots, the font addition and why, the two wayfinding limits (press/privacy footer has the sentence but no link; thesis/workflow have neither), the gate findings if any, and that merging changes nothing live until the 1st. End with exactly `🤖 Generated with [Claude Code](https://claude.com/claude-code)`. `gh pr checks --watch`. **Do not merge.**

---

## Self-review notes

- **Spec coverage:** all eleven files (T1-T4), fonts (T1 S1), the six undesigned zones named per the spec (T2 S3), dress-first concatenation (T3 S3), the borrowed-dress gate (T4 S1/S4), About's toggle (T4 S2), the imprint limits recorded (T4 S1, T5 S5), the queue (T5 S4), visual-diff correctly a non-gate (T5 S3), the "a rejected correct theme is a gate finding" rule (T5 S1).
- **Parallelism:** T2, T3, T4 write disjoint files and read only T1's outputs; each gates its own archetype and reports the others. T5 is the single full green.
- **The restore step in T3 S4 is load-bearing.** Flipping `active` locally to render real plugin pages is the only way to preview them under a queued theme; forgetting to restore ships slate onto main. The step says byte-identical and `git status` clean.
