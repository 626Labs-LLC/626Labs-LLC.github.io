# Solstice Countdown: December 2026 theme design

Approved by Este 2026-11-07 ("Go") against the sheet
`Design/explorations/2026-11-07-december-bakeoff/sheet-solstice-countdown.html`
(artifact https://claude.ai/artifact/LWR9FPNiUGH1AkCPLzwd4v).

## Intent

December, for an audience in 171 Store markets: festive without belonging to
any one culture. The year winds down and the next one comes in. Este's
picture: "inspired by Cyan Fade, space at the top, earthy at the bottom", then
"combine Solstice and Countdown... bring up the countdown about 10 days before
the new year. That's a joint thing for everybody across the world who uses a
calendar." And: the countdown's pieces sit on Solstice's background; they do
not bring a background of their own.

## Goals

- One dark theme, slug `solstice-countdown`, month `2026-12`, all eleven files,
  `theme-doctor --browser --require-browser` PASS, queued in
  `content/themes.json` before 2026-12-01.
- Home: one body gradient from deep space (top) through dusk and a cyan
  horizon to loam and umber (bottom). A seeded star canvas plus aurora ribbons
  in the sky. A horizon glow line divides Work from the founding.
- Phases, by the VISITOR's local clock, in the browser (the site is static):
  - `solstice`, 1 to 21 Dec: the sky as above, a horizon note naming 21 December.
  - `countdown`, 22 to 31 Dec: string lights across the top of the same sky,
    one firework on load, a countdown panel in the hero to local midnight on
    1 January 2027 (days, hours, minutes; seconds join on the last day).
  - `newyear`, from local midnight: "Happy 2027." until January's theme lands.
- Countdown label names the zone: zone city, then the long zone name, then
  "your time" (Este's ranking). Retired IANA IDs map to current names
  (Calcutta to Kolkata, Kiev to Kyiv, Saigon to Ho Chi Minh City...).
- Every other page (product, reading, utility) is the same dark world:
  space-to-dusk at the top, flat dark ground for reading. No sky canvas, no
  countdown there.

## Non-goals and anti-goals

- No snow, trees, religious or single-culture symbols. December is summer in
  half the markets; the solstice and the calendar's turn are the shared events.
- Not a costume: it still reads as a studio that ships.
- The countdown never blocks content, never needs a deploy, never phones home.
- No brand-spacing sweep here ("626Labs" closed up sitewide is its own project).
  The theme's own new strings use "626Labs"; inherited shell strings stay
  until that sweep.

## Constraints

- AA on every text pair, graded against the worst tone it sits on, declared in
  `theme.json` `contrastPairs`.
- Archivo (already self-hosted) for display and body; JetBrains Mono for code
  only. EsteFont Pro stays on the founding quote and About's pull quotes
  (`tests/test_brand_hand.py`).
- Brand cyan `#17d4fa` and magenta `#f22f89` as light (aurora, stars, bulbs,
  sparks, rules). Raw magenta is never type; `#ff6fa8` is the magenta that may be.
- `prefers-reduced-motion`: static sky, frozen bulbs, no firework.
- The games read the contract tokens (PR #302); this theme defines `--ok` and
  `--warn`.

## How (decided)

- Base: copy `themes/cyan-fade/` (Archivo, renderer hooks, EsteFont, every
  archetype already token-driven). Treatment prefix `--cf-*` becomes `--sc-*`.
- Dark retune of the 47-name contract: accents are the brand inks themselves
  (`--cyan` #17d4fa, `--magenta` #ff6fa8), `--ink-950` is deep space (type on
  an accent fill).
- From the sheet: glass cards (8% white fill, 16% white line, 14px radius) for
  product rows and game cards; the flagship on `#0f3042` with a cyan frame and
  glow; gold `#f3c77a` for dates.
- The band (cyan-fade's one magenta surface, the founding) becomes the horizon
  zone: founding sits just below the glow line on the sweep, no fill of its own.
- Rasters: `raster` block with a space field, ink `#F1F5F9`, cyan dim, glow on.

## Gotcha to carry

`rotate-theme.yml` fires at 09:00 UTC on the 1st. Midnight on 1 January in
UTC-10 and further west (Hawaii, some Pacific islands) is 10:00 UTC or later,
so those visitors would lose the countdown before zero. Move the cron to
12:00 UTC (every zone has passed midnight by then; harmless for other months).

## Left to the builder

Exact dress values per archetype, aurora placement on non-home pages (none by
default), the countdown's position at 390px.
