# 626labs.dev goes Phosphor Blueprint — design spec

**Date:** 2026-07-07
**Status:** Approved design, pre-implementation
**Project:** 626 Labs — Portfolio Hub (dashboard ID `qNCk86nujUfrHEbRU2jy`)
**Treatment source:** `Design/colors_and_type.css` (`--pb-*` group) + `Design/preview/treatment-phosphor-blueprint.html` + the winning sheet at `Design/explorations/2026-07-07-treatments/phosphor-blueprint.html`

## Decision

The whole public site converts to Phosphor Blueprint — absolute-black drafting grid, CRT scanlines, near-black glass panels, cyan bloom, phosphor-persistence hovers. Navy retires as the site's field. **This pass converts `index.html` only**; the rest of the estate follows in later passes. Editorial (light-paper) pages are permanently excluded by the treatment's own rule.

## Coverage matrix (sitemap-derived, 30 URLs + 404)

Este's constraint: coverage is a checklist, not a vibe. Every public URL classified:

| Bucket | URLs | This pass | Later |
|---|---|---|---|
| Homepage `/` (index.html) | 1 | **CONVERT** | — |
| Plugin/product pages (`/vibe-*`, `/sanduhr/`, `/bacon-trail/`, `/thesis-engine/`, `/plugins/`) | 16 | verify unaffected | Pass 2: restyle `render-plugin-pages.py` template |
| Standalone dark pages (`press.html`, `privacy.html`, `rororo.html`, `workflow.html`, `thesis.html`, `404.html`) | 6 | verify unaffected | Pass 3: hand-convert (each has its own inline shell) |
| Editorial (`/editorial/` + 6 story pages) | 7 | **verify untouched + formatting intact** | NEVER — light layer, excluded by treatment rule |

Pass-2/3 follow-ups get logged as dashboard tasks at ship time so they don't evaporate.

## Conversion approach — token swap (approach A, approved)

`index.html`'s inline `<style>` routes sections through semantic tokens. The conversion re-points the semantic layer and adds the treatment kit:

1. **Token layer.** Add the `--pb-*` group (copied verbatim from `Design/colors_and_type.css`) to `:root`. Re-point: `--bg-0` → `rgb(0,0,0)`; `--bg-1` → near-black glass `rgba(0,0,0,.6)`; `--bg-2` → `rgba(0,0,0,.72)`; `--border-1/2` → cyan-tinted hairlines (`rgba(23,212,250,.14)` / `.25`). Body `background` becomes the drafting-grid stack (fine 24px + coarse 120px cyan lines on black). All new colors are rgba-of-token or pure black — zero new hexes.
2. **Scanline overlay.** One `<div class="pb-scanlines" aria-hidden="true"></div>` immediately after `<body>`. Fixed, `pointer-events: none`, `z-index` above content but below nav dropdowns/modals if any (audit stacking during build). Ships at `.42` alpha with the proven escape hatch: drop toward `.3` if long copy shimmers.
3. **Signature moments.** Hero H1 + stat values: `--pb-bloom-cyan` text-shadow. Primary CTAs: `--pb-trail` on real `:hover`. Nav: `rgba(0,0,0,.72)` glass + cyan hairline bottom. Protection/scrim gradients: fade to black, not navy. Terminal titlebars (`626 // session` chrome): **sparingly** — lab-run/code-flavored cards only; exact placement judged on screenshots during build, never on every product card.
4. **Article care (Este's constraint).** The homepage's Field Note / Thinking / Stories cards are formatting-fragile: their type hierarchy, line-length, and card spacing must survive conversion pixel-faithful — re-skin the surface (background/border/glow), never the type layout. Screenshots of these sections at all three widths are mandatory review artifacts.
5. **Legibility dials.** Under 720px: fine grid off (coarse 120px only) to cut noise; scanlines stay. No new animation — `prefers-reduced-motion` untouched. Contrast: current text tokens on pure black have HIGHER contrast than on navy; spot-check `--text-mute` smallest uses anyway.

## What must not change

- `SITE_JSON:*` zones — renderer-owned; zero edits inside them. `render-hub.py --check` green is the proof.
- Content, copy, structure, IA. This is a re-skin.
- `content/site.json`, `scripts/`, workflows, editorial templates, plugin-page templates.
- `Design/` (treatment source is read-only this pass).

## The second sweep (Este's constraint — own phase, fresh eyes)

After conversion, a dedicated stray hunt before the PR is opened:

1. **Token stray grep:** every `#0f1f31|#192e44|#223a54|navy` literal remaining in `index.html` is either justified (e.g., a meta theme-color decision made deliberately) or a bug. `<meta name="theme-color">` gets decided explicitly (→ black).
2. **Full-page scroll screenshots** at 1440 / 768 / 390: every section top to bottom, hunting navy islands, unstyled hovers, grid seams, glass panels that went opaque, scanline artifacts over images.
3. **Interactive states:** nav links, CTA hover/focus, card hovers, skip-link focus, form controls in the contact section.
4. **No-leak verification:** one plugin page, one standalone page, `/editorial/` + one story page rendered locally — byte-identical to pre-conversion (git confirms) and visually intact (screenshots). Article formatting inspected deliberately, per constraint.
5. **Gates:** `python scripts/render-hub.py --check` exit 0; `python scripts/site-doctor.py --report` then `--check` exit 0 (doctor fails silently — use `--report` to see why first).

## Ship

Fresh branch off freshly-fetched `origin/main` (daily bots churn it; the Discord branch keeps its own work). Screenshots in the PR body at all three widths. Merge is Este's call; GH Pages deploys from main. Known temporary mismatch, accepted: OG/social banners stay navy until a follow-up brand-asset pass (logged as a task, not forgotten).

## Out of scope

- Plugin pages, standalone pages, admin, widget, OG/social assets, favicon (all logged as follow-up tasks at ship).
- Editorial pages: excluded permanently (light layer).
- Copy changes of any kind.
