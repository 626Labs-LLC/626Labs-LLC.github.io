# The rasters follow the theme — brand assets and social cards re-cut for the Slate Broadsheet

**Date:** 2026-09-04
**Status:** Approved direction (Este, 2026-09-04: re-cut the brand rasters slate for October). Design calls below are the Architect's, stated so they can be overridden.
**Branch:** `feat/slate-rasters`, after `feat/october-needs` merges.
**Deadline:** merged before 2026-10-01 09:00 UTC, so the rotation can regenerate the assets on the morning it flips.

## Why

Every raster the site puts in front of the world was baked in Phosphor Blueprint's look on 2026-07-07: black field, two-scale drafting grid, cyan and magenta radial glows, a bloomed mark. They are the brand's most-seen surfaces — X and Discord embeds, link previews, the browser tab — and they are the one place the CRT would outlive the theme that made it. Este's ruling: they follow the theme. That makes "the site changes monthly" true off-site as well as on it.

## What exists, and what each becomes

Two generators own every raster. `assets/brand/` and `assets/og/` are their outputs and are never hand-edited.

| Asset | Generator | Baked field today | Slate treatment |
|---|---|---|---|
| `banner-1200x630`, `-1280x640`, `-1500x500` | `export-brand.py` | black + grid + glows | slate `#3A4350`, paper grain at ~3.5 percent, no grid, no glow; the mark and lockup in paper ink; a printer's color bar (cyan, magenta, paper) as a small strip where the glows used to sit |
| `discord-splash-1920x1080` | `export-brand.py` | same | same recipe at splash scale |
| `medium-header-*` (six sizes), `vibe-plugins-banner-*` (six), `vibe-plugins-square-1024` | `export-brand.py` | same | same recipe |
| `icon-animated-512.gif` | `export-brand.py` | black, glows pulsing lub-dub | **static** slate tile, no pulse. A printed thing does not pulse. The file keeps its name and remains a GIF so Discord and anything that embeds it keeps working. |
| site favicon, `favicon-626` | `export-brand.py` | black, bloomed mark | slate field, mark at full paper and cyan, no bloom. The tab icon follows the month too. |
| `icon-transparent-*`, `logo-lockup-transparent-1080`, `vibe-plugins-mark-transparent-512`, `logo-portrait-*` | `export-brand.py` | none (field-free) | **unchanged.** They carry no field, so they carry no theme. |
| `assets/og/<slug>.png`, one per local Field Note (seven today) | `build-og-cards.py` | black + grid + glows, title hero, cyan-to-magenta hairline | slate field with grain, title in Space Grotesk, dek in Source Serif 4 (now self-hosted), a mono dateline, the color bar as the hairline. `rebuild-hub.yml` owns these on ubuntu; never commit cards built on Windows (FreeType differs, `CLAUDE.md` records why). |
| `assets/favicon-admin.png` | `build-admin-favicon.py` | gradient square | **unchanged.** The admin tab is an internal tool, deliberately distinct from the site favicon, never themed. |

## The design of the generators: theme-aware, not slate-hardcoded

Today both scripts hardcode `PB_FIELD = (0, 0, 0)` and draw `drafting_grid()` and `radial_glow()` unconditionally. Replacing those with slate constants would re-create the same problem for November. Instead:

- Each theme's `theme.json` gains an optional `raster` block: `{"field": "#3A4350", "ink": "#F7F5F0", "dim": "#C3C1BA", "texture": "grain" | "grid" | "none", "glow": false, "colorBar": true}`. Phosphor Blueprint's block records what it does today (`field #000000, texture grid, glow true, colorBar false`); slate's records the treatment above. A theme with no block gets Phosphor Blueprint's values, so nothing regresses for a theme that never thought about rasters.
- `export-brand.py` and `build-og-cards.py` read the block from the ACTIVE theme (`theme_registry.active_slug`), with `--theme <slug>` to build for a queued one. The drawing code branches on `texture` and `glow`; the palette comes from the block. `scripts/css_color.py` already parses any CSS color, so the block may use whatever syntax the theme's tokens use.
- The rotation regenerates: `rotate-theme.yml` runs `export-brand.py` and `build-og-cards.py` after the registry flips and before the gates, and its `git add` list gains `assets/brand/` and `assets/og/`. `rebuild-hub.yml` already rebuilds OG cards on story pushes and will now do so in the active theme's look.
- The archive shares `/assets/*` by documented decision (`freeze-theme.py`'s docstring). A frozen September page will show October's banner if it references one. Accepted and recorded, same as fonts and the widget CSS.

## Gates

- Every regenerated asset opened and looked at, at real size, for the record: banners at 100 percent, the favicon at 16 and 32, the OG card in an actual X/Discord preview shape (1200x630 letterboxed to 1.91:1). `export-brand.py` has no `--check`; the check is eyes, and the screenshots are committed under `Design/explorations/2026-09-03-paper-and-ink/raster-preview/`.
- `build-og-cards.py --check` byte-compares; it runs in CI on ubuntu. Locally on Windows it will show a harmless diff; do not "fix" it by committing.
- Contrast on every raster that carries text: the title on the field, the dek on the field, the dateline on the field, each measured against the slate ground with the same WCAG numbers the theme's tokens carry. Social cards get read on phones in sunlight; nothing under 4.5.
- The `raster` block is validated by `theme-doctor` for the active and queued themes: colors parse, `texture` is one of the three, booleans are booleans. A theme whose block is malformed fails the doctor, not the rotation morning.
- Both `theme-doctor.py phosphor-blueprint` and `slate-broadsheet` pass. Rotation-morning simulation re-run with slate active, now including the two generator steps, every gate green.

## Out of scope

- Product artwork PNGs with a baked navy field (`assets/thumb-*.png`, `sanduhr-card-shot.png`). Hand-made marketing art, case-by-case, recorded since July as the last navy on the site.
- The 626 Day and TikTok social assets under `assets/social/`. Campaign-dated, not theme-bound.
- Any change to the marks themselves. The mark is the brand; the field is the month.

## Risks named

- **The favicon and Discord embed are identity surfaces.** Changing them monthly is what Este chose, and it is the strongest possible statement that the site changes monthly. It also means a visitor's pinned tab looks different in October. Recorded, not hedged.
- **A static GIF where an animated one was.** Anything that cached the animated icon's pulse as "the 626 Labs icon" sees it stop. That is the design.
- **Regenerating rasters on the rotation runner adds Pillow+numpy drawing to the unattended morning.** Both are already in `requirements.txt` and already run on ubuntu in `rebuild-hub.yml`. The new step must be inside the gate order — after the flip, before the gates — so a drawing failure aborts the rotation rather than shipping half a set.
