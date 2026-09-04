# Paper and Ink — October's theme bake-off (M2b)

**Date:** 2026-09-03
**Status:** Approved direction (brainstormed 2026-08-04; Este, 2026-09-03: "let's do the paper and ink bake off now")
**Deadline:** a doctored theme in `content/themes.json`'s `queue` before 2026-10-01 09:00 UTC, or the rotation no-ops again the way it did on 2026-09-01 (issue #106).

## Why

August's theme is a black CRT. The point of the rotation is range: a printed page after a lit monitor reads as two studios. Paper and ink is the pivot that proves it.

## The three sheets

All three are print, from three traditions, and each implies a different *layout*, not only a palette:

- **The Broadsheet** — newspaper. Multi-column grid, hairline rules, a dateline, dense headline hierarchy with real decks. Products become columned listings; Field Notes a front-page rail. Fast, informational, ink-heavy.
- **The Monograph** — exhibition catalog. Enormous margins, one commanding display serif, products as plates with numbered captions, one idea per screenful. Slow, expensive, confident. The most severe departure from a dense CRT dashboard.
- **The Field Manual** — letterpress technical manual. Numbered sections, specification tables, engineering plates, printed-document texture. The closest match to what the lab *is* — a catalog of tools — rendered as if printed in 1962.

**The wayfinding contract, on all three:** a small dateline — *Theme: October 2026 · this site changes monthly · see all themes* — linking `/themes.html`. Not a shared visual invariant; a sentence that turns the seam into the story. Without it a visitor landing on a page still wearing the old dress thinks the site is broken. With it, they think it is alive.

## How the bake-off runs

Mirrors `Design/explorations/2026-07-12-about-treatments/`, the round that chose the About page's treatment:

1. One specimen pack (`specimen.md`) of real site copy — hero, ten products, the founding block, four Field Notes, nav, footer, dateline. Every sheet renders it verbatim. Este judges chrome, not words.
2. Three sheets at `Design/explorations/2026-09-03-paper-and-ink/sheet-<slug>.html`, each a complete homepage specimen, each built by a separate implementer with no sight of the others.
3. `check-tokens.py` gates token discipline: every color is a `var()` of an `--ed-*`/`--brand-*`/`--ink-*` token, or a raw color bound to exactly one `--pi-<slug>-*` declaration in the sheet's own `:root`.
4. Every sheet: AA on every text/background pair it introduces, documented inline with ratios; no horizontal scroll at 1440/768/390, measured not eyeballed; and **no use of `--ed-link` as text** — it is 2.58:1 on paper, a known base-layer defect.
5. A gallery `index.html`, a `judging-README.md` with the case for each and a KEEP / KILL / REMIX line per sheet, and 1440 + 390 screenshots.
6. Este rules. The winner (or remix) becomes the eleven-file theme, passes `theme-doctor --browser --require-browser`, and lands in `queue`.

## What the winner must satisfy later (the sheets are not held to this)

The theme contract is eleven files, 47 required tokens, four archetype dresses with token-only siblings, and every gate PR #96 and #97 added. Sheets are single pages. The winning build is held to all of it. Sheets should still use the home archetype's class vocabulary where natural (`hero`, `products`, `product`, `field-notes`, `field-note`, `section`, `nav`, `footer-inner`, `contact`, `support`) so the winning build is a lift, not a rewrite.

## Out of scope

- Building the eleven-file theme. That follows the verdict.
- The About page, which keeps Long Now Terminal by ruling.
- Any change to `content/site.json`.

## Risks named

- **A light theme on a site whose every product screenshot is dark.** Monograph's plates and Broadsheet's listings will frame dark rasters on paper. Sheets should show how — a plate mat, a hairline frame, a drop — rather than leave it to the build.
- **The dateline is easy to make invisible.** If a judge cannot find it at 390px, the sheet has failed the one contract all three share.
- **Three implementers, one specimen, no cross-talk.** That is the point. A sheet that drifts from the specimen to look better is judged on the drift.
