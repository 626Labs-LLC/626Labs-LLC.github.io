# 626 Labs year in review

An interactive timeline of the estate, July 2025 to 2026-09-29: 77 dated events in five eras, an estate-wide commit heatmap, and a Microsoft Store install map. It was built as a private page first; nothing here links from the site.

## Files

| File | What it is |
|---|---|
| `page.tpl.html` | Layout, styles and script. Placeholders `__DATA__`, `__MAP__`, `__ACT__`. |
| `page-data.json` | The events shown on the page, plus the header stats. |
| `map.json` | Country geometry (Natural Earth, 110m) and Store installs per market, from `data/store-analytics.json` as of 2026-09-27. |
| `activity.json` | Commits per day across the estate's local clones, bots excluded, plus the Galaxy Genesis history. |
| `build-map.mjs` | How `map.json` was made. Needs `world-atlas`, `topojson-client`, `d3-geo`, `i18n-iso-countries`. |
| `build.py` | `python docs/year-in-review/build.py out.html` inlines the data into one self-contained page. |

## Evidence rules

Every event carries a `confidence`: `verified` (a commit, tag, release, Partner Center date, or a machine timestamp), `inferred` (date derived), or `user-stated` (Este's account, not yet backed by a record). The page tags the last two as approx.

Store publish dates come from Partner Center `firstPublishedDate`. The Droplet's first boot is the cloud-init instance directory's birth time.

## Two traps in the numbers

- **GitHub release downloads are not an audience.** About 99% of ROROROblox's counter is installed apps polling manifests. See `scripts/asset-kind.mjs`. The page uses Store installs and daily users instead.
- **The Store market table has no documented time window.** Read its counts as relative sizes, not as 30-day figures.

## Deliberately not committed

The research working files (raw lane output, billing, incident notes, employer-adjacent PriceScout material) stay local. This repo is served publicly, so only what the page shows is here.
