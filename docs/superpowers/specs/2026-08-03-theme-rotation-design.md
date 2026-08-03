# Monthly theme rotation — approved design (M1: the machinery)

**Date:** 2026-08-03
**Status:** Approved design, pre-implementation
**Scope:** M1 only — the rotation machinery, proved by extracting the current Phosphor Blueprint look as theme #1. M2 (the first genuinely new theme) is a committed follow-on with its own spec.

## Intent

626labs.dev rotates its theme monthly: planned, staged ahead, and rotated
automatically, without ever degrading the portfolio experience. Past themes stay
walkable at permanent URLs, so the rotation becomes its own portfolio piece —
twelve shipped design systems a year, each visitable, proving range that a static
site cannot claim.

## Decisions (brainstormed 2026-08-03)

1. **Depth:** treatment AND section layout change month to month (not palette-only).
2. **Trail:** retiring themes are archived and visitable at permanent URLs.
3. **Switch:** themes are queued ahead and a scheduled workflow rotates on the 1st,
   unattended; approval happens once, when a theme is built.
4. **Architecture consequence (decided in design):** archived themes FREEZE. They
   are dated static artifacts, never re-rendered. An old theme cannot rot if it
   never re-renders, and "the site as it looked in August 2026" is the honest
   framing for a portfolio.

## What a theme is

`themes/<slug>/` containing:

- `shell.html` — the page skeleton: section order and presence, wrapper markup,
  nav, footer, skip link, the `SITE_JSON:` zone markers the renderer fills.
- `tokens.css` — the treatment layer: palette, type, texture, motion, and the
  layout CSS (grid structure, densities, card anatomy).
- `theme.json` — `{name, slug, thesis, month, status}` where status is one of
  `queued | live | archived`.
- Optional `assets/` for theme-specific imagery.

**The renderer is NOT forked.** One `render-hub.py` with its existing shared
emitters serves every theme. Layout variation comes from the shell (section order
and structure) and CSS (hero shape, grid density, card anatomy). Twelve divergent
markup generators is the failure mode this design exists to avoid.

**Escape hatch, not built in M1:** a theme may later register an emitter override
if it genuinely needs different markup. M1 does not implement this; if a theme in
practice needs it, that is a finding worth a follow-up spec.

## The theme contract (`scripts/theme-doctor.py`)

No theme enters the queue until it passes. This gate is what makes unattended
rotation safe:

- WCAG AA contrast on every text/background pair the theme declares.
- No horizontal scroll at 1440, 768, and 390 px.
- Every section enabled in site.json is present in the rendered output; every
  section the theme omits is explicitly disabled, not silently dropped.
- Nav, skip link, footer, and the analytics snippet all present.
- All internal links resolve (no 404s introduced by the shell).
- Renders against real `content/site.json`, never placeholder content.
- Zero browser console errors.

`theme-doctor.py <slug>` exits nonzero on any failure and prints what failed.
CI runs it on any PR touching `themes/**`.

## Registry and rotation

`content/themes.json`:

```json
{
  "active": "phosphor-blueprint",
  "queue": ["<slug>", "<slug>"],
  "archive": [
    { "slug": "phosphor-blueprint", "month": "2026-08", "url": "/themes/2026-08/" }
  ]
}
```

**Building a theme:** branch, build the three files, `theme-doctor` green, PR,
merge into the QUEUE. Merging changes nothing live.

**Preview:** `python scripts/render-hub.py --theme <slug> --out <dir>` renders any
theme without touching the live output, for local review at any time.

**Rotation workflow** (`.github/workflows/rotate-theme.yml`, cron on the 1st,
plus `workflow_dispatch`):

1. If `queue` is empty: change nothing, open an issue saying the queue is empty, exit.
2. Freeze the outgoing theme (see below).
3. `active = queue.shift()`; append the outgoing theme to `archive[]`.
4. Re-render the site.
5. Run the full gate stack: `theme-doctor.py`, `site-doctor.py --check`, `pytest`,
   `render-hub.py --check`.
6. Commit and push only if every gate passes. On any failure: abort with zero
   changes committed and open an issue with the failure output.

The site can only move from one verified state to another.

## Freezing (the archive)

At rotation, the outgoing theme's already-rendered pages are COPIED to
`/themes/YYYY-MM/`. Never re-rendered, then or ever. Two injections into each
frozen page:

- `<meta name="robots" content="noindex">` — twelve frozen homepages must never
  compete with the live one in search.
- A banner: "Archived: the site as it looked in <Month YYYY>" with a link to the
  live site.

Frozen pages carry their own copy of the theme's CSS so later token changes
cannot alter them. Images remain shared under `/assets/`, so archives may drift
if an asset is deleted; that tradeoff is accepted, and the banner's dated framing
makes it honest. Archives are excluded from `sitemap.xml`.

## The gallery (`/themes/`)

An indexed page listing every theme: name, thesis, month, screenshot, and a live
link to walk it. This page is the portfolio artifact and IS indexed; the archives
under it are not. It renders from `content/themes.json` so it can never disagree
with the registry.

## M1 deliverables

1. `themes/phosphor-blueprint/` — the CURRENT look extracted into the three-file
   structure. Acceptance: the rendered homepage is pixel-identical to today's
   (byte-identical HTML where possible; any diff must be explained and approved).
2. `content/themes.json` registry.
3. `scripts/theme-doctor.py` + tests.
4. `render-hub.py --theme <slug> --out <dir>` preview support (default behavior,
   with no flags, stays exactly as today).
5. The freezer (a script the workflow calls; independently runnable).
6. `.github/workflows/rotate-theme.yml`.
7. `/themes/` gallery page, rendered from the registry.
8. Docs: a section in the repo CLAUDE.md covering how to build, queue, preview,
   and roll back a theme.

## Rollback

`content/themes.json` is the single switch. Reverting the rotation commit
restores the previous active theme; the frozen archive of it already exists and
is unaffected. Document this in the CLAUDE.md section.

## Out of scope (M1)

- Designing any new theme (that is M2, with its own bake-off).
- Emitter overrides / per-theme markup generators.
- Per-visitor theme choice or a theme picker on the live site.
- Rotating anything other than the marketing site (plugin pages, about.html, and
  product pages keep their current treatments unless a later spec says otherwise).
- Automated screenshots for the gallery (M1 accepts manually captured images;
  automating capture is a candidate follow-up).

## Risks named

- **Extraction is the real test.** If Phosphor Blueprint cannot be expressed in
  shell + tokens without markup surgery, the seams are wrong and the design needs
  revisiting before any second theme is built. Treat a failed pixel-identical
  extraction as a design finding, not an implementation bug.
- **Archive link rot:** frozen pages link to live URLs that may later 404. The
  dated banner mitigates; a link check over archives is deliberately NOT run
  (they are historical artifacts, not maintained pages) and lychee must exclude
  `/themes/YYYY-MM/`.
- **Queue starvation:** an empty queue on the 1st is a no-op plus an issue, never
  a broken site.

## Inputs needed

None for M1. Every input exists in the repo today.
