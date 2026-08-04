# Theme archetypes — approved design (M2a)

**Date:** 2026-08-04
**Status:** Approved design, pre-implementation
**Scope:** M2a only — make the whole site rotatable by expressing a theme as four archetype shells instead of one homepage shell, plus the About easter egg, gallery screenshots, and a self-dressing gallery. M2b (September's paper-and-ink theme, designed into these archetypes) is a committed follow-on with its own spec.

## Why this exists

M1 rotates the homepage. Este's ruling (2026-08-04): every page comes into scope, and
the monthly change is a HARD PIVOT — no shared visual invariants between months, so a
visitor cannot mistake September for August. Rotating only the homepage under a hard
pivot would put a visible seam on every nav click. Rotating 35 pages by hand-authoring
35 shells per month is not a cadence anyone can sustain. Archetypes are the resolution:
a theme designs four layouts; the site has thirty-five pages.

## Decisions (brainstormed 2026-08-04)

1. **Hard pivot, site-wide.** No shared invariants required between months.
2. **Four archetypes:** `home`, `product`, `reading`, `utility`. Every page declares one.
3. **About keeps Long Now Terminal as its default** and carries an easter-egg toggle
   that re-dresses that page in any theme the registry knows.
4. **Screenshots are in scope** (they were cut from M1 by inertia; the Playwright
   harness now exists in theme-doctor, which makes them cheap).
5. **The gallery renders in the ACTIVE theme**, not a hardcoded one.
6. **Two milestones:** M2a is this machinery; M2b is September's design.

## The archetype contract

The load-bearing idea: **an archetype is a markup contract; a theme is a dress for it.**

- Each theme provides `themes/<slug>/archetypes/{home,product,reading,utility}.html`
  plus its `tokens.css` and `theme.json`.
- Each archetype defines a FIXED semantic class vocabulary that every theme must use
  (e.g. the reading archetype's article wrapper, section heads, pull quotes, captions,
  figure blocks). Themes vary the CSS and the structural arrangement; they do not
  invent new class names for the same semantic element, because the About toggle
  depends on any theme's reading CSS working against the same markup.
- **The About toggle is the contract's test.** If every theme's reading dress renders
  About correctly, the vocabulary is right. A theme that breaks there is visibly
  broken before it can ship — this is a feature of the design, not a side effect.
- The vocabulary is written down in `docs/theme-archetypes.md` (created by this
  milestone) and enforced by theme-doctor, which fails a theme whose archetype CSS
  references classes outside the vocabulary or omits a required one.

## Page-to-archetype mapping

Every page declares its archetype in one registry (`content/page-archetypes.json`),
so the mapping is data, not code:

- **home:** index.html
- **product:** the 14 per-plugin pages, plugins/index.html, rororo.html,
  rororo-plugins.html, conundrum.html, mod-launcher-games.html, sanduhr/,
  bacon-trail/, play/, thesis-engine/ and the remaining product-ish directory pages
- **reading:** about.html, thesis.html, workflow.html, editorial/index.html and the
  six Field Note pages
- **utility:** privacy.html, press.html, themes.html, 404.html, legal/

`admin-dashboard.html` is excluded entirely (an internal tool, not a public surface);
the implementation plan lists the exact final mapping and any page whose archetype is
genuinely ambiguous gets named there rather than guessed at.

## Renderers

Both renderers become archetype-aware:

- `scripts/render-hub.py` renders index.html and the standalone pages from the active
  theme's matching archetype shell.
- `scripts/render-plugin-pages.py` renders the 14 plugin pages plus the family index
  from the active theme's `product` archetype. Its current single `STYLE` constant
  becomes theme-supplied.
- The zone-substitution mechanism is unchanged; archetype shells carry the same
  `SITE_JSON:` markers their pages need.

Migration is the risky part and gets its own verification: **each page must render
visually identical to today under Phosphor Blueprint's archetypes** (0-pixel diff at
1440/768/390, per the M1 T2 precedent). Phosphor Blueprint's four archetypes are
extracted from today's actual pages, not redesigned.

## The About easter egg

- A hidden control on about.html (discovery mechanism decided in the plan; a keyboard
  sequence or a small unlabeled mark, not a visible menu) reveals a theme picker.
- Picking a theme swaps the page's stylesheet to that theme's reading dress. Every
  theme the registry knows is offered: archived months, the live theme, and About's
  own default.
- Client-side only, no server, no build step per theme. Choice remembered per visitor
  (localStorage); the default on every fresh visit is Long Now Terminal.
- The toggle never changes any other page and never changes what rotation does.

## Screenshots and the gallery

- The freeze step captures the retiring theme; the promote step captures the incoming
  one. Captures are deterministic (fixed viewport, fonts loaded, animation disabled)
  and land in a predictable path the gallery reads.
- `themes.html` renders in the ACTIVE theme's utility archetype and shows each theme
  with its thumbnail, thesis, month, and link. This closes the M1 deferred finding
  where the gallery wore a retired theme.

## Theme-doctor extensions

The contract gate grows to match the larger surface:

- Runs against ALL FOUR archetypes, not one page.
- Enforces the archetype class vocabulary (missing required class, or CSS targeting a
  class outside the vocabulary, fails).
- Contrast, no-horizontal-scroll, chrome, and internal-link checks run per archetype.
- The known base-layer defect stays out of bounds: no theme may use `--ed-link` as a
  text color (2.58:1 on paper). A light theme declares its own link color and passes
  on its own merit.

## Out of scope (M2a)

- Designing September (that is M2b's bake-off: three paper-and-ink sheets, judged,
  winner built into these archetypes and queued).
- Rotating admin-dashboard.html or any non-public surface.
- A visible theme picker on pages other than About.
- October's theme and beyond.

## Risks named

- **Migration is the real work.** Thirty-five pages moving to four shells will surface
  pages that do not fit their archetype cleanly. A page that cannot be expressed
  without inventing markup is a finding about the archetype boundaries, not a page to
  force — report it rather than bending the vocabulary per page.
- **The reading vocabulary carries the most weight** because the About toggle exercises
  it hardest; design it first and let the others follow.
- **Per-plugin pages have live version chips and JSON-LD.** Their behavior must survive
  the theme swap untouched; verify a plugin page's version chip and structured data
  after migration.

## Inputs needed

None for M2a. September's creative direction (paper and ink, three sheets: Broadsheet,
Monograph, Field Manual) is already decided and rides in M2b.
