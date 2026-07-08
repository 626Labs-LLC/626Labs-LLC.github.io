# Supported-games page Implementation Plan

> Executed INLINE (single-page feature). Spec: `docs/superpowers/specs/2026-07-08-supported-games-page-design.md`.

**Goal:** `mod-launcher-games.html` — client-rendered from the feed's public JSON, on-brand, self-updating; linked from the mod-launcher product entry.

## Tasks

1. **Load the 626labs-design skill** (canonical tokens/type/patterns) + read `rororo-plugins.html` end-to-end (head, fonts, header/footer, card CSS — the structural template) + `colors_and_type.css`.
2. **Build `mod-launcher-games.html`** per the spec's anatomy: counts hero, featured cover rail (Steam CDN imgs, `onerror` → branded initial placeholder), tier sections, request-a-game CTA, failure state, schemaVersion check, lazy images, responsive.
3. **Wire the product link** in `content/site.json` (mirror how RoRoRo's entry points at its sub-page); run `python3 scripts/render-hub.py` (or `--check` + let CI render if local deps are missing).
4. **Verify in a real browser** against the live feed: counts/rail/covers render, DS2 shows the placeholder, links correct, failure state fires with a bad URL, mobile-width sane. Screenshot for Este.
5. **Push to main** (repo norm), confirm Pages deploy, hand over the live URL.

## Gate
- Page renders from the LIVE feed with zero console errors; placeholder + failure paths exercised; `render-hub.py --check` clean after the site.json touch; Pages serves the page at 626labs.dev.
