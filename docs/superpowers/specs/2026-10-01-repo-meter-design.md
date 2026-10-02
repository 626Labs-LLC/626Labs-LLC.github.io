# Repo meter: a commit-activity grid on every showcased project

**Date:** 2026-10-01. **Asked for by:** Este ("add the repo meter like we have on the timeline to each of our projects we showcase"). **Calls made by Este:** every surface that links a repo; the compact day grid, not a sparkline.

## What it is

The year-in-review timeline carries a `.pulse` rail: one cell per day, one row per week, commits across the whole estate, bots excluded. The repo meter is that grid, per repository, shrunk to a card: the last 26 weeks, seven rows, one column per week, a one-line summary beside it. It answers "is this thing alive?" at a glance on every page that shows a project.

## Where it appears

Every showcase surface that already links a repository:

| Surface | Count | Source of the repo |
|---|---|---|
| Home product rows (`render_product`) | 21 of 24 products carry `repo` in `content/site.json` | the product's `repo` |
| Generated plugin pages (`render-plugin-pages.py`, the hero) | 15 | the matching product's `repo` in site.json by id, else `content/plugin-repos.json` |
| `rororo.html`, `rororo-plugins.html`, `mod-launcher-games.html`, `conundrum.html` | 1 + 5 + 2 + 1 | hand-placed `<div class="repo-meter" data-repo="...">` |

`etsy-mcp.html`, Conundrum's and SnapSnip's home rows carry no public repo and get no meter. The `/plugins/` family index does not get fifteen meters on one page in this round.

Three plugins (`vibe-keystone`, `vibe-thesis`, `thesis-engine`) map to the `vibe-plugins` monorepo in site.json and to solo repos in `plugin-repos.json`. The meter follows site.json: the monorepo is where their commits land; the solo repos are the shipping surface the version chip reads. Both are true, and the meter is about activity.

## Data

A daily bot, `refresh-repo-activity.yml` (06:40 UTC, implicit `GITHUB_TOKEN`, public repos only), runs `scripts/refresh-repo-activity.mjs`:

1. Collects the repo set: every `repo` in `site.json` products, every entry in `plugin-repos.json`, and every `data-repo="owner/repo"` attribute found in the public HTML at the repo root (so a hand-authored page registers itself by carrying the element).
2. For each repo, `GET /repos/{owner}/{repo}/commits?since=<today minus 182 days>&per_page=100`, up to five pages. Commits whose author is a bot (`author.type == "Bot"`, a login ending in `[bot]`, or no GitHub author and a committer name containing `github-actions`) are dropped, the same rule the timeline applied. Counts by the commit author date, UTC.
3. Writes `data/repo-activity.json`:

```json
{
  "fetchedAt": "2026-10-02T06:40:00Z",
  "windowDays": 182,
  "repos": {
    "estevanhernandez-stack-ed/ROROROblox": {
      "days": { "2026-09-30": 4, "2026-09-29": 1 },
      "total": 212,
      "lastCommit": "2026-09-30",
      "truncated": false
    }
  },
  "missing": ["owner/private-or-gone"]
}
```

Repos that 404 or 403 land in `missing` and render NOTHING: the element stays empty and takes no height. (The first cut said "no public activity"; Celestia3 is private, the runner's token 404s it, and a dead-looking line on the flagship was worse than no line.) The push uses the same retry+rebase loop every bot in this repo uses. `GET /stats/commit_activity` was rejected: it counts bots, and the hub repo alone commits by bot every day.

## Rendering

**Runtime, never baked.** The renderers emit an empty `<div class="repo-meter" data-repo="owner/repo" aria-label="Commit activity for <name>"></div>`; `/repo-meter/meter.js` fetches `/data/repo-activity.json` once per page and fills every meter. The bot's daily write therefore never dirties `render-hub.py --check` or `render-plugin-pages.py --check`, the same reason version chips fetch `plugin-versions.json` at runtime.

**One stylesheet, contract tokens only.** `/repo-meter/meter.css` colors cells with the theme's own names (`--cyan` at four opacities for levels one to four, a `--border-1` inset for empty days, `--fg-3` and `--font-body` for the summary), so every theme dresses the meter without knowing it exists. Slate shows brand-cyan cells on slate; Cyan Fade shows deep-cyan cells on paper and on the sweep. A theme may override `.repo-meter` in its dress; none has to.

**The grid.** 26 columns (weeks, oldest left), 7 rows (Sunday to Saturday), 8px cells, 2px gap: 258 by 68px. Levels are per repo, by quartile of that repo's non-zero days, so a quiet repo still shows its own rhythm. Each cell carries a `title` ("Sep 30, 2026: 4 commits"). The summary line reads "212 commits in 26 weeks, last Sep 30"; a repo with no record in the file renders no meter at all. The meter's container is `aria-label`ed with the summary once it fills; before the fetch resolves, and if it fails, the element stays empty and takes no height.

**Where on the row.** Home: after the tags, before the CTA row. Plugin page: under the version chip in the hero. Hand-authored pages: wherever the repo link already sits.

## Gates it has to clear

- `theme-doctor`: both home shells and the plugin page shell gain a `<link>` to `/repo-meter/meter.css`, which joins their resolution groups as a reader; every `var()` it reads is a contract name, defined in every group. `check_internal_links` resolves the new paths.
- `render-hub --check` and `render-plugin-pages --check` stay byte-stable across bot writes (nothing from the data file is rendered).
- `site-doctor --check`: the two new static files are not dangling.
- Tests: `render_product` emits the meter exactly when `repo` is set; the plugin page emits it in the hero; the bot's bot-filter and date bucketing are unit-tested on a fixture; the data file's shape is pinned.

## Not in this round

The `/plugins/` family cards; a meter on the year-in-review page (it has the estate rail); per-repo links from the meter to GitHub's own graph; private repos (no token with private scope exists in CI, by design).
