<!-- SPECIMEN: real site copy, verbatim from content/site.json and content/stories as of 2026-10-01. Do not edit wording. -->
# November bake-off: specimen pack (2026-10-01)

Every sheet renders THIS content and nothing else. The only variable across sheets is chrome: type, color, motif, structure. Judge the treatment, not the words.

Refreshed from the September pack: the hero changed (three shelves, not one), Celestia 3 leads the product order, Conundrum is second, and two Field Notes have shipped since. Descriptions that run long are cut at a clause boundary, never mid-word.

## 0. Wayfinding sentence (required on every sheet, present at every width; it no longer has to sit in the first viewport)

> Theme: November 2026 · this site changes monthly · [see all themes](/themes.html)

Style it in the sheet's own idiom: a manual's document-control stamp, a catalog colophon, an imprint line. Present on every page is the contract; the September verdict relaxed "first viewport at 390."

## 1. Nav

Work · Field Notes · Lab · About · Contact

## 2. Hero

- eyebrow: 626Labs LLC · Fort Worth, TX
- headline: Astrology engines, dev tools, streetwear.
- accent: Imagine Something Else.
- subhead: A NASA-grade astrology app, Claude Code plugins for builders who ship for real, and merch designed by its own AI pipeline. Three shelves, one lab.

## 3. Products (render at least these ten, in this order; the first is the flagship)

- **Celestia 3**: NASA-grade astrology AI.
- **Conundrum by Este**: The 626 Labs merch shop — streetwear-grade prints designed by an AI pipeline and sold print-on-demand on Etsy.
- **Vibe Cartographer**: Vibe coding with a map.
- **Vibe Iterate**: Maintain your Atlas.
- **Vibe Insights**: The /insights you wish you had.
- **Vibe Keystone**: Map the repo before the agent starts.
- **Vibe Doc**: Point it at your codebase and it finds the docs you're missing — ADRs, runbooks, threat models, specs.
- **Vibe Test**: Put your code to the test before somebody else does.
- **Vibe Thesis**: Long-form research, drafted with discipline.
- **Thesis Engine**: Surface topics. Gather sources. Seed the thesis.

## 4. The founding (section 02)

- eyebrow: 02 · The founding
- headline: 626 Labs builds exact-fit software.
- pull quote: I build tools, because care doesn't always scale.

> 626 Labs builds exact-fit software. The founding argument is simple: it has never been easier to have the exact tools we need, and too much money has been going to too many companies for tools that only half fit. So we build and maintain our own, at a quality that rivals enterprise software, made to enhance the work people do instead of taking their jobs. We are here to make great products, even if only a handful of people need them. That's ok.

> The line the lab was built on belongs to its founder: "I build tools, because care doesn't always scale." It is translation: take the care a person already has and build it into something that keeps working after their attention has to move on.

- door: Read the whole story -> about.html

## 5. Field Notes (render these four, newest first)

- **Containment for Frontier AI** (2026-09-28)
  Containment is an architecture, not a sandbox setting. Revised after a summer of real escapes.
- **The words were the easy part** (2026-09-09)
  RoRoRo shipped in six languages. The translating took an afternoon; finding every place the product speaks took the rest.
- **RoRoRo grew eyes, hands, and a heartbeat** (2026-07-03)
  The Roblox multi-launcher you could recommend on camera now has three plugins (perception, action, and a keep-alive), wired together by a consent-gated bridge that never leaves your machine.
- **The first 626 Labs Day** (2026-06-26)
  Today is 6/26/26, the first 626 Day since 626 Labs existed. The whole surface is shipped and live in one window: 14 Claude Code plugins and 6 Microsoft Store apps, one new and two with major updates this week.

## 6. Footer

626 Labs LLC · Fort Worth, TX · Imagine Something Else.

## Base-layer constraints every sheet inherits

- `--ed-link` (`#0FA8C9`) fails AA on every paper tone and on any kraft or manila ground. No sheet may use it as a text color. Declare your own AA link ink as a `--pi-<slug>-*` token and document the ratio in the sheet's header comment.
- On a ground darker than cream, re-derive every ink. The September Field Manual's full ink set (`--ed-ink-3` captions, its cyan link, its magenta revision mark) fails on manila and kraft. Compute against the grain-composited tone, not the raw hex: the grain darkens the ground about 9 percent at its peaks, and that is what a visitor sees.
- Source Serif 4 is self-hosted now (`/fonts/fonts.css`); the September "Georgia fallback" note is retired.
- `colors_and_type.css` paints `h1` white and `p` in a light ink for the dark site. Every text element on a light or mid ground re-inks.
