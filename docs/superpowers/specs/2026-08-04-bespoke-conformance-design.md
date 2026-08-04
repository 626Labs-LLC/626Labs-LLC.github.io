# Bespoke page conformance — approved design (M2a.5)

**Date:** 2026-08-04
**Status:** Approved design, pre-implementation
**Scope:** Bring the six remaining bespoke pages into the theme system so all 39 public pages wear the same dress, before September's first rotation.

## Why

Este's ruling (2026-08-04): "I want all the pages to be uniform," and on cost:
"if it's a heavy cost now, but it'll be easier in the future, then it's worth it."

After M2a, 25 of 39 pages take their dress from the active theme. Six do not:
`thesis.html`, `workflow.html` (reading), and `conundrum.html`, `rororo.html`,
`rororo-plugins.html`, `mod-launcher-games.html` (product). A visitor landing on
a September homepage and clicking into an August-looking product page does not
read the rotation as intentional; they read the site as broken. Uniformity is
what makes the monthly change legible as a choice.

## What the six pages actually are

Measured, not guessed: 2,255 lines of inline CSS, 607 rules, and **each page
declares 29 to 39 of its own design tokens.** These are not six bespoke designs
resisting a system. They are six private photocopies of the design system, each
taken at whatever moment the page was built. It is the same pathology the M2a
final review found in Phosphor Blueprint itself, where 38 of 43 tokens were
being supplied by hardcoded page-local fallbacks rather than by the theme.

The work is therefore mechanical, not creative: delete the photocopied token
block, consume the theme's tokens, keep the page's layout rules, verify nothing
moved.

## The decision that shapes everything: uniform dress, not uniform layout

Each page KEEPS its own layout rules, written in terms of theme tokens. Layout
differs between these pages because their CONTENT differs — a merch gallery is
not a game feed — and that difference is correct.

**The consequence, stated plainly so it is chosen rather than discovered:** each
month these six pages will RECOLOR (palette, type, texture, chrome), not
RE-LAYOUT. Their structure stays put until a page is individually redesigned.

The alternative — moving each page's layout rules into the theme's archetype
CSS so every theme supplies the layout — was rejected: it would require every
future month's theme to style a merch gallery, a game feed, a plugin catalog and
more, which makes a monthly cadence unsustainable. Sustainability of the
rotation outranks maximal per-page transformation.

## The work, per page

1. Remove the page's private `:root` token block.
2. Link the active theme's CSS through the same renderer-owned zone mechanism
   M2a built for press/privacy (`render-hub.py`'s theme-css zone, resolved from
   `theme_registry.active_slug`), so a future theme actually reaches the page.
3. Rewrite any hardcoded color/type/spacing literals in the page's remaining
   rules to consume theme tokens. A literal that has no token equivalent is a
   finding: either it belongs in `REQUIRED_TOKENS` or the rule is page-specific
   enough to keep its literal — decide per case and record which in the report.
4. Keep the page's layout rules inline, in its own file.
5. Verify 0-pixel identity at 1440/768/390 versus `origin/main`, using
   `freeze-theme.py`'s deterministic capture init script (seeded RNG, frozen
   clock) so nondeterminism is not mistaken for regression.

## Archetype and vocabulary

Each page's archetype is already declared in `content/page-archetypes.json`
(reading for thesis/workflow, product for the other four). This milestone does
NOT force their markup to the archetype vocabulary — the vocabulary gate applies
to a THEME's dress, not to individual pages, and rewriting page markup would
break the pixel gate for no gain. Vocabulary conformance for these pages remains
a per-page decision for whenever each is next redesigned.

## Success criteria

- All six pages consume the active theme's CSS; none carries a private token block.
- All six render 0-pixel identical to today under Phosphor Blueprint.
- Flipping `content/themes.json`'s active theme visibly recolors all six (proven
  by rendering against a scratch second theme with distinct token values, then
  discarding it — this is the test that the wiring is real rather than nominal).
- `REQUIRED_TOKENS` grows if these pages need tokens the set lacks, and Phosphor
  Blueprint defines every one.
- All existing gates stay green: 125 tests, both renderers' `--check`,
  site-doctor, theme-doctor with `--browser`.

## Out of scope

- Redesigning any page.
- Forcing page markup to the archetype vocabulary.
- September's theme (M2b: the paper-and-ink bake-off follows this).
- The remaining frozen surfaces by prior ruling: 404.html and legal/* stay
  structurally bare; about.html keeps Long Now Terminal as its default.

## Risks named

- **A page may carry a literal that no token can express** (a one-off accent, a
  bespoke gradient). Do not invent a token to absorb every literal — that grows
  `REQUIRED_TOKENS` into a junk drawer every future theme must satisfy. Keep
  genuinely page-specific literals and say so.
- **rororo.html and mod-launcher-games.html have live data-driven sections**
  (plugin catalog, game feed). Their runtime behavior must survive; verify the
  feeds still render after the CSS surgery, not just that pixels match on load.
- **conundrum.html carries the shop gallery and its GoatCounter click events.**
  Verify the events still fire after the change.

## Inputs needed

None. Every decision is recorded above.
