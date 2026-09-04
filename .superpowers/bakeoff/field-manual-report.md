# The Field Manual — bake-off report

Sheet: `Design/explorations/2026-09-03-paper-and-ink/sheet-field-manual.html`
Screenshots: `shot-field-manual-1440.png`, `shot-field-manual-390.png` (same directory)
Built 2026-09-03 on `feat/paper-and-ink-bakeoff`.

## Thesis

The lab is a catalog of tools, so the page is the catalog: one specification table, ten numbered engineering plates, numbered paragraphs, and a record-of-changes list, set on editorial.css's paper as if pulled through a letterpress in 1962. Warmth comes from the paper grain, the double rules, the impression highlight under display type, and a serif prose column, not from decoration. The brand pair prints as ink, never as a surface: a darkened cyan for numerals and links, a darkened magenta for revision marks, and both at full strength only in the printer's color-control strip in the footer.

## Tokens (`--pi-field-manual-*`)

WCAG 2.1 relative luminance; paper L values: `--ed-paper` 0.9137, `--ed-paper-soft` 0.9541, `--ed-paper-deep` 0.8326, zebra tint (ink at .035 over paper, resolves to hex EFEEE9) 0.8538.

| Token | Value | Role | vs paper | vs paper-soft | vs paper-deep | vs zebra tint |
|---|---|---|---|---|---|---|
| `--pi-field-manual-link` | hex 0A6478 | link ink, section and paragraph numerals, table item numbers, nav hover | 6.20 | 6.46 | 5.68 | 5.82 |
| `--pi-field-manual-revision` | hex 9E1A58 | revision-mark ink: the document-control stamp, figure numbers, table fig refs, door link | 7.03 | 7.32 | 6.44 | 6.59 |
| `--pi-field-manual-rule` | ink at alpha .32 | table hairlines, plate mats (decorative) | n/a | | | |
| `--pi-field-manual-tint` | ink at alpha .035 | zebra rows (decorative surface) | n/a | | | |
| `--pi-field-manual-emboss` | white at alpha .6 | letterpress highlight under display type (decorative) | n/a | | | |
| `--pi-field-manual-scan` | white at alpha .045 | scanlines inside plate placeholders (decorative) | n/a | | | |

Base inks re-derived on the zebra tint because it is a surface this sheet introduces: `--ed-ink` 14.34, `--ed-ink-2` 10.50, `--ed-ink-3` 4.65. The tint is never stacked on `--ed-paper-deep`, where `--ed-ink-3` would drop to 4.25 and fail. Every pair clears 4.5:1 at body size.

`--ed-link` (2.58:1) and `--ed-ink-muted` (2.59:1) are not used as text anywhere; every anchor sets its own color.

## Plates and dark rasters

Each product is a plate: a `--ed-ink` block at 16:10 (the flagship at 21:9), with `--brand-gradient-soft` and a 3px scanline pattern over it so the placeholder reads as a dimmed CRT rather than a void. The raster sits inside a 10px paper mat with a hairline border and two registration ticks, then a caption rule and a figure caption: `Fig. N` in revision ink, the item name in Space Grotesk, the flagship's tagline in italic serif on the right. Fig. 1 runs full width above Table 1; Figs. 2 to 10 form a three-column grid (two at 768, two at 390). The build swaps the placeholder for the screenshot and keeps the mat, so the dark image is framed instead of floating on paper.

## Table 1 at 390px

Above 640px it is a real four-column table (No. / Item / Description / Fig.) with a double rule on the head, hairline rows, zebra tint, and a 2px closing rule. At 640px and below the `<table>` reflows into a stacked ledger: `thead` is visually hidden (kept for readers), each `tr` becomes a three-column grid with areas `"no item fig" / "no desc desc"`, and every cell drops its fixed width. The wrapper carries `overflow-x: auto` as a fence only; nothing triggers it at any tested width. Measured, not eyeballed: see the h-scroll numbers below.

## Where the dateline lives

A document-control stamp: mono, revision-ink text and a doubled magenta border (`box-shadow` ring over a 2px border), rotated 1.5 degrees on desktop, straight at 390. At 1440 it sits top-right of the hero grid opposite the headline (top 133px, right 1253px). At 768 and 390 it moves to the top of the hero above the eyebrow, full width at 390 (top 158px, bottom 223px). The verbatim line `Theme: October 2026 · this site changes monthly · see all themes` is intact; `THEME:` is uppercased by CSS only and `see all themes` links `/themes.html`.

## H-scroll (Playwright, Chromium, `documentElement.scrollWidth` vs `clientWidth`)

| Width | scrollWidth | clientWidth | Page height | Result |
|---|---|---|---|---|
| 1440 | 1440 | 1440 | 4298 | PASS |
| 768 | 768 | 768 | 5134 | PASS |
| 390 | 390 | 390 | 5318 | PASS |

Zero console errors and zero page errors at all three widths.

## Token gate

```
PASS Design/explorations/2026-09-03-paper-and-ink/sheet-field-manual.html: colors confined to declared --pi-* tokens.
```

## Specimen fidelity

49 of 49 specimen strings present verbatim (scripted check: every nav label, hero line, product name and tagline including the two truncated ones, both founding paragraphs, all four Field Note titles, dates and summaries, the footer, the dateline). Invented microcopy is limited to the manual's own furniture: `01 · Work`, `03 · Field Notes`, `Table 1`, column heads `No. / Item / Description / Fig.`, `Fig. N`, paragraph numerals `2.1` `2.2`, entry numerals `3.1` to `3.4`, section refs (`Table 1 · Figs. 1 to 10`, `Paras. 2.1 to 2.2`, `Record of changes`), and the word `Note` on the pull quote's box.

## Class vocabulary

`nav`, `nav-inner`, `nav-links`, `wrap`, `hero`, `hero-inner`, `eyebrow`, `section`, `section-head`, `products`, `product` (each Table 1 row), `field-notes`, `field-note`, `field-note-title`, `field-note-subtitle`, `field-note-date`, `footer-inner`. Not used: `contact`, `support`. The specimen carries no copy for either section, and an empty section would have been added chrome.

## Judged and left out

- **Product name appears twice** (table row and plate caption). This is the manual's cross-reference idiom, kept on purpose; the tagline appears twice only for the flagship.
- **Field Note titles are not links.** The specimen gives no URLs and the real site's story slugs are not in the pack, so a dead `href="#"` seemed worse than a plain heading. The build links them.
- **No page folios, running heads, or a fake document number** (`TM 626-1` and the like). Tempting for the idiom, but all invented copy, and a judge reading `FM 626` on a homepage would be right to ask what it means.
- **No color flood anywhere.** The brand pair is a 72px accent rule ahead of the hero's accent line, the two derived inks, and the 14px swatches in the color-control strip. `--brand-cyan` and `--brand-magenta` at full strength appear only in that strip.
- **Grain is `position: absolute` over the body, not `fixed`.** Fixed reads as a screen effect and leaves a seam in full-page captures; absolute makes it the paper.
- **`Lab` and `Contact` nav links point at `/#lab` and `/#contact`** since the sheet has no such sections.

## Known gaps

- `--font-serif` resolves to Georgia on Windows (Source Serif 4 is not self-hosted). Pre-existing base-layer gap shared by every sheet.
- The scanline and duotone overlay inside the plate placeholders is a stand-in; the real screenshot decides how much of the mat's contrast is needed.
