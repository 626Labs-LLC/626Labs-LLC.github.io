# The Slate Broadsheet — October's theme, the eleven-file build

**Date:** 2026-09-03
**Status:** Approved direction. The design is the remix sheet at `Design/explorations/2026-09-03-paper-and-ink/sheet-slate-broadsheet.html`, judged and confirmed by Este ("we don't need the crt any more"). This spec is the engineering of that sheet into a rotating theme.
**Deadline:** `content/themes.json` `queue` must carry the slug, doctored, before **2026-10-01 09:00 UTC**.
**Branch:** `feat/slate-broadsheet`, stacked on `feat/paper-and-ink-bakeoff` (PR #114). Rebase onto `main` when #114 merges; the bake-off sheets are reference, not dependencies.

## The design, fixed

A newspaper printed on slate. Structure from the Broadsheet: a masthead between a heavy rule and a hairline, a dateline row with folios, a section index strip, a lead story with a drop cap, a boxed front rail, section fronts with reversed folio tabs, columned listings under real column rules, a features-page founding section, a printer's color bar in the footer. Type from the Field Manual: Space Grotesk on the masthead and every head, a serif on body and decks, JetBrains Mono on all furniture. Ground `#3A4350`, one token, with the editorial paper tones inverted into ink. Cyan is the link ink; magenta is never text on slate (2.64:1) and lives in the color bar and a declared hover tint. Matte throughout: no glow, no bloom, no scanlines, no grid, no gradient fields. The wayfinding sentence lives in the footer as the paper's imprint line.

Slug `slate-broadsheet`. Name "The Slate Broadsheet". Month `2026-10`. Thesis: *the page is printed, not lit.*

## What a theme is, and what this one owes

Eleven files under `themes/slate-broadsheet/`:

| File | Owes |
|---|---|
| `tokens.css` | All 47 `REQUIRED_TOKENS` redefined for slate. A `--sb-*` treatment block for newspaper furniture. NO `--pb-*` names, no CRT rules, nothing painting `.pb-scanlines` (page markup keeps that div; this theme paints nothing on it). Pins `h1..h6, p` ink explicitly: `colors_and_type.css` paints headings white for the dark site and a slate theme must not inherit that by accident. |
| `theme.json` | `{name, slug, thesis, month, status, contrastPairs}` with pairs against the slate ground and any surface a token sits on (`--fg-1/--bg-0`, `--fg-2/--bg-0`, `--fg-3/--bg-1`, link ink / ground). |
| `archetypes/home.html` | The remix sheet, made into the shell: all twelve `SITE_JSON:<zone>` markers (`hero hero-chips products thinking founding stories lab-runs play about support contact lab-pool`), skip link, nav, footer, analytics. The sheet rendered six zones; the other six get the same idiom, designed in the build, see below. |
| `archetypes/product.html` + `product.css` + `product-tokens.css` | The plugin page (23 pages: 14 plugins, the family index, and the four bespoke product pages link `product-tokens.css` only) as a section front for one product. `product.css` is the element dress `render-plugin-pages.py` inlines, dress-first because it opens with `@import`. `product-tokens.css` is tokens only, gated. |
| `archetypes/utility.html` + `utility.css` | press.html and privacy.html borrow 100 percent of their chrome from `utility.css` (49 of 50 selectors reach press). It must dress `nav.nav`, `header.page-hero`, `h1.page-title`, `main`, `footer`, `a.inline-link`, `.wrap`, `.nav-inner` in the broadsheet idiom, and it must pass the region differential and the three element assertions in `check_page_renders_dressed`. Defines all 47 tokens (it is a `REQUIRED_TOKEN_CSS` file). |
| `archetypes/reading.html` + `reading.css` + `reading-tokens.css` | `reading-tokens.css` (tokens only, gated) dresses thesis.html and workflow.html, which own their layouts. `reading.css` dresses the `.lnt-*` vocabulary for about.html's theme picker; About keeps Long Now Terminal as its default by ruling and offers this dress on the toggle. |

Every token file: all 47 names, tokens only, and every `var()` any group reads resolves inside that group (`check_theme_reads_only_what_it_defines`, per resolution group). No reference to another theme's slug in any file (`check_theme_references_only_itself`, including relative hrefs). Copy-and-retokenize from Phosphor Blueprint is the documented path and leaves four hardcoded slugs behind; the check exists because of that.

## The six zones the sheet never showed

Designed in the build, in the sheet's idiom, judged in the preview render:

- **hero-chips** — the stat chips under the hero deck become a mono "by the numbers" line under the lead, folio-styled.
- **thinking** — a section front: folio tab `03 · Thinking`, a lead item with deck, the rest as columned listings.
- **lab-runs** — the photo page. Frames become plates on pale mats with `PLATE` captions, two or three across, the caption rule in cyan-to-magenta.
- **play** — the games page. The Bacon Trail widget and the two game widgets are lifted onto pale mats the way the flagship plate is; the widgets keep their own chrome. Puzzle-page furniture: a folio tab, mono captions.
- **about** — the star map panel keeps its own JS and markup; the section gets the folio tab and a deck. The star canvas sits on a pale mat like any plate.
- **support / contact / lab-pool** — the back page. Classified-ad columns under a `04 · Notices` tab: support links, contact, and the lab pool as short boxed notices with hairline rules.

## Type and fonts

`--font-display: 'Space Grotesk'`, `--font-body: 'Source Serif 4', 'Iowan Old Style', Georgia, serif`, `--font-mono: 'JetBrains Mono'`. Space Grotesk and JetBrains Mono are self-hosted. **Source Serif 4 is not, and this theme's body is serif, so the build self-hosts it**: variable roman and italic TTFs (SIL OFL) added to `fonts/`, converted by `scripts/build-fonts.py` the way JetBrains Mono already is, declared in `fonts/fonts.css`. That is a site-wide asset addition, not a theme file; it also fixes the Georgia fallback on the editorial layer for every page that reads `--font-serif`.

## The wayfinding contract, per page class

"Theme: October 2026 · this site changes monthly · see all themes" linking `/themes.html`.

- **home and product shells** carry it in markup, in the footer, as the imprint line.
- **press and privacy** own their footer markup, so `utility.css` cannot add a link. It adds the sentence as generated content on the footer; the link is absent there. Recorded as a limit. The durable fix is a site-wide footer line in page markup, which is a separate change across 39 pages, not this theme's.
- **thesis and workflow** own everything; the sentence is not present. Same limit, same fix.

## Gates, in order

1. `python scripts/theme-doctor.py slate-broadsheet --browser --require-browser` PASS. This is the only unattended gate before a live rotation.
2. `python scripts/render-hub.py --theme slate-broadsheet --out <dir>` renders the shell and the eight theme-css pages; screenshots at 1440/768/390 of every archetype's representative page (index, one plugin page, press, thesis) for the record and for Este.
3. `render-hub.py --check`, `render-plugin-pages.py --check`, `pytest tests/ -q`, `site-doctor.py --report` all green with the theme merely present (it is not active until the 1st).
4. `theme_registry.validate()` accepts the queue entry.
5. `visual-diff.py` is NOT a gate for this branch: adding a theme moves no live pixel, and a rotation is supposed to move every pixel. Run `--self-check` once to prove the harness still runs; expect 0 findings against `origin/main` since nothing live changes.

## Out of scope

- Changing any page's markup, `content/site.json`, or the About default.
- Removing `.pb-scanlines` divs from pages. Phosphor Blueprint archives, it does not vanish, and its frozen archive needs its markup.
- The site-wide footer imprint line. Follow-up.
- The `.wrap`/`.nav-inner` vocabulary ruling from PR #97. Still open; this theme dresses both anyway.

## Risks named

- **The home shell is 3,025 lines in Phosphor Blueprint.** The remix sheet is 600. The gap is the six un-designed zones plus the widget, star map, and lab-run machinery the sheet never carried. That is where the four weeks go.
- **`.pb-scanlines` sits in every page as a `body > div`.** The field-region differential includes `body > div`; an unpainted div is identical in both states and contributes nothing, so the field region must differ through `html`/`body` themselves. It will: the ground is painted on `body`.
- **A serif body on 23 product pages changes their measure and line count.** Product pages carry live version chips and JSON-LD; behavior must survive, and the preview render is where a wrapped chip or a clipped install block shows up.
- **Every gate on this branch was built to reject a broken theme and accept a correct one.** This is the first theme that exercises them from the author's side. Where a gate rejects something correct, that is a finding about the gate, reported and fixed, not routed around.
