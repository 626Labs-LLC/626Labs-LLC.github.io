# 626 Labs year in review

An interactive timeline of the estate, July 2025 to 2026-09-29: 90 dated events in five eras, an estate-wide commit heatmap, and a Microsoft Store install map. It was built as a private page first; nothing here links from the site.

## Files

| File | What it is |
|---|---|
| `page.tpl.html` | Layout, styles and script. Placeholders `__DATA__`, `__MAP__`, `__ACT__`. |
| `page-data.json` | The events shown on the page, plus the header stats. |
| `map.json` | Country geometry (Natural Earth, 110m) and Store installs per market, from `data/store-analytics.json` as of 2026-09-27. |
| `activity.json` | Commits per day across the estate's local clones, bots excluded, plus the Galaxy Genesis history. |
| `build-map.mjs` | How `map.json` was made. Needs `world-atlas`, `topojson-client`, `d3-geo`, `i18n-iso-countries`. |
| `build.py` | Inlines the data into one page. `build.py out.html` is standalone; `build.py out.html --theme <slug>` is the hosted build (see Theming). |

## Evidence rules

Every event carries a `confidence`: `verified` (a commit, tag, release, Partner Center date, or a machine timestamp), `inferred` (date derived), or `user-stated` (Este's account, not yet backed by a record). The page tags the last two as approx.

Store publish dates come from Partner Center `firstPublishedDate`. The Droplet's first boot is the cloud-init instance directory's birth time.

## Two traps in the numbers

- **GitHub release downloads are not an audience.** About 99% of ROROROblox's counter is installed apps polling manifests. See `scripts/asset-kind.mjs`. The page uses Store installs and daily users instead.
- **The Store market table has no documented time window.** Read its counts as relative sizes, not as 30-day figures.

## Theming

The page keeps only namespaced `--y-*` tokens. Standalone, they hold their own light and dark palette and load Google Fonts. Hosted (`--theme <slug>`), `build.py` maps them onto the hub's theme contract (`--bg-0`, `--bg-1`, `--fg-1`, `--fg-3`, `--border-2`, `--cyan`, `--magenta`, `--ok`, `--warn`, `--font-*`) and links `/fonts/fonts.css` and `/themes/<slug>/tokens.css`. A rotation is then one slug in one `<link>`. Verified against `phosphor-blueprint` (live) and `slate-broadsheet` (takes over 2026-10-01).

Promoting it to a real page is separate work: pick an archetype in `content/page-archetypes.json`, add the page to `THEME_CSS_HREFS` in `scripts/render-hub.py` so the rotation rewrites its theme link, and rebuild with `--theme`. Nothing here does that yet, and nothing under `docs/` is in the sitemap.

## Not committed

The research working files stay local. This repo is served publicly, so only what the page shows is here.
