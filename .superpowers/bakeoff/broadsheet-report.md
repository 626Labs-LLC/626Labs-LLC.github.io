# The Broadsheet: bake-off report

Sheet: `Design/explorations/2026-09-03-paper-and-ink/sheet-broadsheet.html`
Screenshots: `shot-broadsheet-1440.png`, `shot-broadsheet-390.png` (same directory)
Date: 2026-09-03

## Thesis

A visitor who saw August's black CRT should land on October and read a second studio, not a stylesheet that lost its background, so the page commits to the whole newspaper tradition at once: a masthead set between a heavy rule and a hairline, a dateline row, a section index strip, a lead story, a boxed front-page rail, section fronts with reversed folio tabs, and columned listings under real `column-rule`s. The wayfinding sentence is not decoration bolted on; it is the dateline itself, the line every newspaper prints under the masthead, so the seam between months is the first thing the page says. Cyan and magenta survive only as a printer's color bar in the ears and footer, a 56px caption rule under each plate, and the underline of the founding door: spot color on newsprint, never a flood.

## Tokens (`--pi-broadsheet-*`) and ratios

WCAG 2.1 relative luminance, ratio = (Lmax + .05) / (Lmin + .05). Paper tones: ed-paper F7F5F0, ed-paper-soft FAFAF7, ed-paper-deep EFEBE2. "+ fiber" is the worst-case composite of the 3 percent grain over that tone (F0EFEA, E8E5DD).

| Token | Value | Role | vs paper | vs paper-soft | vs paper-deep | vs paper + fiber | vs deep + fiber |
|---|---|---|---|---|---|---|---|
| `--pi-broadsheet-link` | `#086882` | link ink, text 11 to 22px | 5.82 | 6.06 | 5.33 | 5.46 | 4.99 |
| `--pi-broadsheet-link-hover` | `#A8175C` | hover and focus ink, text | 6.55 | 6.83 | 6.00 | 6.14 | 5.62 |
| `--pi-broadsheet-fiber` | `rgba(15,31,49,.03)` | paper grain hairlines, decorative | n/a | n/a | n/a | n/a | n/a |
| `--pi-broadsheet-screen` | `rgba(247,245,240,.14)` | halftone dot screen over the ink plate, decorative | n/a | n/a | n/a | n/a | n/a |

All text pairs clear 4.5:1 at every size used. Reused base pairs, informational: ed-paper on ed-ink (reversed tabs, rail label) 15.29; ed-ink on paper 15.29; ed-ink-2 on paper 11.19; ed-ink-3 on paper 4.96 and on paper + fiber 4.65. One warning carried into the build: ed-ink-3 on ed-paper-deep with the grain composited is 4.25:1, a fail. This sheet never puts ink-3 on deep paper (it does not use deep paper at all).

`--ed-link` (2.58:1 on paper) is not used as text anywhere. Every anchor routes through `--pi-broadsheet-link`.

## Framing dark rasters on paper

Two scales, same treatment, so the build has the pattern at both sizes:

- **Front-page plate** (hero, under the deck, 16:9). A `--ed-paper-soft` mat with 6px of padding inside a 1px `--ed-ink` keyline, then the raster block in `--ed-ink` with a 4px halftone dot grid of `--pi-broadsheet-screen` laid over it via `radial-gradient`, plus a faint scan band so the placeholder has a subject. Under it a caption with a 56px `--ed-accent-rule` (cyan to magenta) rule and a mono `PLATE` kicker in ink-2, body in ink-3 Inter 13px.
- **Listing plate** (the flagship listing, 300px wide at 1440, 240px at 768, full width at 390). Same mat and screen with 4px padding, caption at 12px. It proves the frame survives at column width, which is what the build's nine other listings will need if they ever carry thumbnails.

The screen is the point: a dot pattern of paper over ink is what a press does to a photograph, so the dark rectangle reads as printed, not as a hole cut in the page.

## Where the dateline lives

Directly under the masthead's double rule at every width, as its own row with a hairline below: `Fort Worth, TX` folio left, the wayfinding sentence centered in 12px Inter 600, `Monthly edition` folio right, `see all themes` underlined in link ink. At 390 the row collapses to a centered single column, the sentence bumps to 13px, and the link sits at y = 191, well inside the first screen. Measured link positions: y = 214 at 1440, y = 164 at 768, y = 191 at 390. The nav strip sits beneath it; nothing pushes it below the fold.

## Horizontal scroll (Playwright, Chromium, `documentElement.scrollWidth` vs `clientWidth`)

| Width | scrollWidth | clientWidth | Result |
|---|---|---|---|
| 1440 | 1440 | 1440 | no h-scroll |
| 768 | 768 | 768 | no h-scroll |
| 390 | 390 | 390 | no h-scroll |

Zero console errors and zero page errors at all three widths. The only element outside the viewport is the offscreen skip link at left: -9999px, which is by design and does not extend the scroll width.

## Token gate

```
PASS Design/explorations/2026-09-03-paper-and-ink/sheet-broadsheet.html: colors confined to declared --pi-* tokens.
```

## Specimen fidelity

Every specimen string checked against the rendered DOM text: the dateline, five nav items, hero eyebrow, headline, accent, subhead, all ten products in order (including the two truncated descriptions, rendered as-is), the founding eyebrow `02 · The founding` with its middle dot, headline, pull quote, both paragraphs, the door, all four Field Notes with dates and deks, and the footer line. Invented chrome is limited to: `Skip to content`, `626labs.dev` (ears), `Fort Worth, TX` and `Monthly edition` (dateline folios), `01 · Work` (the section head, numbered to match the specimen's `02 · The founding`), `Ten listings, one flagship` and `Front rail` (folio text), `No. 01` to `No. 10` (listing folios), and the two plate captions.

## Judged and left out

- **A `--ed-paper-deep` band for the rail or the founding.** Tempting for section-front separation, but with the grain composited ink-3 fails there, and the rule-only treatment is more newspaper anyway. Hairlines separate; tint is a magazine move.
- **Yellow in the color bar.** A real CMYK bar has it; the brand does not. Cyan, magenta, ink only.
- **Blackletter or a display serif for the masthead.** Source Serif 4 is not self-hosted and no third font ships in `/fonts/`, so the masthead sets in the editorial serif stack (Georgia on Windows) at 124px, bold `626` and italic `Labs`. It holds. Adding a webfont for one word was not worth the weight.
- **Product screenshots in every listing.** Ten dark rectangles would flood the page and undo the restraint the plate treatment buys. The flagship carries the listing-scale plate; the other nine are type only, which is how a section front lists things.
- **A repeated dateline in the footer colophon.** It would duplicate specimen copy; the footer keeps its one line and the color bar.
- **`overflow-x: hidden` on `html`/`body`.** Removed before measuring so the scroll numbers reflect the layout and not a mask.
- **Contact and support sections.** The specimen carries no copy for them, so the sheet does not invent any; `footer-inner` is the only footer-region class used from the archetype vocabulary.
