# The Monograph: bake-off report

Sheet: `Design/explorations/2026-09-03-paper-and-ink/sheet-monograph.html`
Screenshots: `shot-monograph-1440.png`, `shot-monograph-390.png` (same directory)
Branch: `feat/paper-and-ink-bakeoff`

## Thesis

The homepage as an exhibition catalog: one display serif, margins that are the design, and every product mounted as a numbered plate so a visitor arriving from August's black CRT reads a second studio, not a broken one. The brand's cyan and magenta become two printing inks (cyan for links, magenta for numerals) plus exactly two hairline rules, never a flood. Restraint is only expensive if the rhythm holds at 390, so the plate spread collapses to a catalog's list of plates rather than ten screenfuls.

## Tokens (`--pi-monograph-*`), WCAG 2.1 ratios

Paper tones text sits on: `--ed-paper` F7F5F0 (L 0.9137), `--ed-paper-soft` FAFAF7 (L 0.9541, plate mat), `--ed-paper-deep` EFEBE2 (L 0.8326, founding band).

| Token | Value | vs paper | vs soft | vs deep | Use |
|---|---|---|---|---|---|
| `--pi-monograph-link` | `#0A6B83` | 5.60 | 5.83 | 5.13 | every link at rest, nav and title hover |
| `--pi-monograph-plate` | `#B01A62` | 6.08 | 6.33 | 5.57 | plate numbers, section numerals, link hover |
| `--pi-monograph-shadow` | `rgba(15,31,49,.18)` | decorative | | | drop under the plate mat |
| `--pi-monograph-scan` | `rgba(255,255,255,.04)` | decorative | | | 1px scanline inside the raster placeholder |

All text pairs clear 4.5:1 on every paper tone they appear on. Base-layer pairs reused and re-derived (ink 15.29 / 15.93 / 14.00; ink-2 11.19 / 11.66 / 10.25; ink-3 4.96 / 5.17 on paper and soft only; `--ink-300` on `--ed-ink` 7.43 for the mono label inside a raster). `--ed-link` is never text. `--ed-ink-muted` (2.59) is hairlines only. The full table is in the sheet's header comment.

Gotcha caught in review: `colors_and_type.css` paints `h1` white (`--fg-1`) and `p` in `--ink-200` for the dark site. The first render had an invisible headline. The sheet now pins `h1, h2, h3, p` to `--ed-ink` at the base. The winning build's `tokens.css` needs the same override or the whole home page inherits the dark site's text colours.

## How the plates frame dark rasters

Each screenshot is a plate: a 16:10 block of `--ed-ink` (with the faint scanline so it reads as a lit screen, not a hole) sits inside a mat of `--ed-paper-soft`, one shade lighter than the page, with a `--ed-rule-strong` hairline edge and a soft drop (`--pi-monograph-shadow`). The lighter mat lifts the dark raster off the warm paper, so the darkest object on the page reads as mounted, not as a defect. Below: the plate number in magenta ink with a hairline running out to the margin, the title in the serif, the tagline in ink-2. Plate I (the flagship) gets its own spread with the caption aligned to the plate's foot; Plates II to X face each other two to a spread at 1440, Plate X sitting alone on its recto the way a catalog's last plate does.

## Where the dateline lives

The catalog's imprint line: centered directly under the nav, before the hero, on every width. Inter 12px uppercase, ink-3, with "see all themes" in link ink and underlined. Measured at 390: top 89px, bottom 136px, inside the first viewport with no scroll. At 1440 and 768: 68 to 104px.

## Keeping 390 from reading as empty

- Below 900px the two-plate spread becomes the list of plates: thumbnail mat beside number, title, tagline, one hairline per row. Ten products fit in about 1,100px instead of ten screenfuls. Plate I keeps its full mat so the frame is demonstrated at every width.
- The vertical beat scales (`clamp(64px, 12vw, 176px)`), so the air that is 176px at 1440 is 64px at 390.
- The hero loses its screenful min-height at 480px and the headline holds at 52 to 64px, filling the width.
- Field Note dates fold from the margin column to above the title.
- Page heights: 7,632px at 1440, 5,941px at 768, 5,362px at 390.

## Horizontal scroll (Playwright, `document.documentElement`)

| Width | scrollWidth | clientWidth | Equal |
|---|---|---|---|
| 1440 | 1440 | 1440 | yes |
| 768 | 768 | 768 | yes |
| 390 | 390 | 390 | yes |

Measured with no `overflow-x: hidden` anywhere (an early draft had it on `body`; removed so the number is honest). Zero console errors and zero page errors at all three widths.

## Token gate

```
PASS Design/explorations/2026-09-03-paper-and-ink/sheet-monograph.html: colors confined to declared --pi-* tokens.
```

## Specimen fidelity

49 specimen strings checked against the rendered text: 0 missing. The two truncated taglines (Vibe Doc's "then w", Sanduhr's "pace yoursel") are rendered as given. No emoji. Em-dash count in the sheet equals the specimen's (4), so none were added.

## Judged and left out

- **Contact and Support sections.** The specimen carries no copy for them, and the brief says render nothing beyond it. The class vocabulary used is `nav`, `hero`, `section`, `products`, `product`, `field-notes`, `field-note`, `footer-inner`, plus the archetype's `eyebrow`, `wrap`, `product-desc`, `field-note-eyebrow`, `field-note-title`, `field-note-subtitle`, `thinking`, `thinking-link`.
- **A second dateline in the colophon.** Tempting as catalog idiom, but a repeated sentence is added copy. One imprint, at the top.
- **Field Note URLs.** The specimen gives none, so all four titles link to `/editorial/` rather than invented slugs.
- **Any cyan or magenta surface.** No tinted chips, no washes, no gradient text. Two inks and two rules is the whole budget.
- **Source Serif 4.** Not self-hosted in `/fonts/fonts.css`, so the display serif resolves to Georgia on Windows and Iowan Old Style on macOS. Sized for Georgia, the wider case. The winning build should either self-host Source Serif 4 or commit to the fallback.
- **Roman numerals** are the plate labels. Not copy, chrome; but if the judge reads them as too precious, arabic numerals are a one-line swap.
