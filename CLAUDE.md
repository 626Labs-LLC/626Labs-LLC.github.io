# 626 Labs Portfolio Hub — repo guide

The marketing site at **626labs.dev**, hosted on GitHub Pages. Plus the
admin dashboard, image pipeline, bot workflows, and side-tools that grew up
around it.

> **Persona:** This repo inherits The Architect from `~/.claude/CLAUDE.md`.
> No need to re-establish — just adds project context below.

---

## Tech Stack & Voice

- **Site shell:** Hand-written HTML + vanilla JS + inline CSS. No framework
  on the marketing surface, no build step. `index.html` is a generated
  artifact of the active theme — chrome/layout edits belong in
  `themes/<active-slug>/shell.html` (see **Theme rotation** below); a direct
  `index.html` edit gets silently reverted by the next render.
- **Widget app:** `apps/widget-bacon-trail/` — Vite + TypeScript. The only
  build pipeline in the repo. Output committed to `widget-bacon-trail/`
  (root) so GitHub Pages serves it directly at `/widget-bacon-trail/`.
- **Admin:** Babel-in-browser React (`admin/*.jsx`). No build step;
  reads/writes via the GitHub Contents API with a fine-grained PAT.
- **Brand:** Cyan `#17d4fa` + magenta `#f22f89` — always paired. Dark navy
  `#0f1f31` field. Space Grotesk display, Inter body, JetBrains Mono code
  + small UPPERCASE meta labels with +0.12em tracking.
- **Voice:** Builder-to-builder, second person, sentence case. No
  "empower / leverage / seamlessly / unlock / unleash." Em-dashes minimal; commas, periods, colons by default.
  No emoji in UI copy or marketing surfaces. Tagline: *Imagine Something Else.*

## Design system

The canonical brand spec lives at `~/.claude/skills/626labs-design/`
(globally available — same skill applies across every 626 Labs repo).
Use `colors_and_type.css` as the token source and `ui_kits/` as the
pattern reference. The local `Design/` folder is for repo-specific
references and one-off design artifacts.

---

## What's where

| Path | What it is |
|---|---|
| `index.html` | The live site. Hand-written shell with `SITE_JSON:<zone>:start/end` markers that get filled by render-hub.py. The About star map's CSS + JS live in the static shell; its markup + data blob are emitted by `render_about()` (config: `about.starMap` in site.json — remove the block to disable the panel). Versions in star tooltips come from a runtime fetch of `data/plugin-versions.json`, never from the render. |
| `content/site.json` | Source of truth for everything editorial — hero, products, pluginFamily, lab, play, about, support, contact, labRuns. |
| `content/stories/*.md` | Long-form case studies. Edited via the admin's Stories tab. |
| `admin/` + `admin-dashboard.html` | Babel-in-browser React admin. PAT-auth against this repo. Edits site.json, uploads to assets/, manages stories, surfaces bot run status. |
| `apps/widget-bacon-trail/` | The embedded Birthday Bacon Trail widget. Bundle output lives at `widget-bacon-trail/` (root) so GH Pages serves it at `/widget-bacon-trail/`. The `functions/` subdir is a separate Firebase Cloud Functions project (`logPlay` endpoint, deployed to `guestbuzz-cineperks`) — see its own README. |
| `assets/` | Screenshots, OG images, favicons, brand exports. `assets/brand/` has the canonical icon + banners (built by `scripts/export-brand.py`). `assets/screenshots/<product>/` is what the admin uploader writes to. |
| `Design/` | Brand reference + the design skill's UI kit. |
| `scripts/` | Site pipeline. `.py` for the renderer + image work (render-hub, build-thumbnails, export-brand, build-admin-favicon); `.mjs` for the bot data jobs (refresh-bacon-shards, track-traffic). |
| `tools/bgremove/` | Standalone CV background remover with a Claude-vision agent loop. See *Tools* below. |
| `mcp-portfolio-server/` | Local stdio MCP server exposing portfolio content (resume, projects, Field Notes) to AI assistants. Read tools hit `site.json`/`content/stories`; write tools wrap the guarded `scripts/site.py`. See its README. |
| `.github/workflows/` | 9 bot workflows that push to main, 1 dashboard API bot, 1 link checker, and 1 on-demand visual-diff sweep. All push-to-main workflows have retry+rebase loops. |
| `fonts/` | Variable TTFs for the brand (Space Grotesk, Inter, Inter Italic, JetBrains Mono). SIL OFL. |
| `themes/`, `content/themes.json`, `themes.html` | The monthly theme rotation: theme source dirs, the active/queue/archive registry, and the gallery page rendered from it. See **Theme rotation** below. |

---

## How the site rebuilds

- Edit `content/site.json` (admin or by hand) → push.
- `rebuild-hub.yml` runs `scripts/render-hub.py` → rewrites `index.html`.
- GitHub Pages redeploys.
- `python3 scripts/render-hub.py --check` is idempotent; CI uses it to detect drift.

## CI workflows

The 9 bot workflows that push to main:

| Workflow | Trigger | Notes |
|---|---|---|
| `build-widget.yml` | Push to `apps/widget-bacon-trail/src/**` | Vite-builds the widget, commits the bundle to `widget-bacon-trail/`. Bakes `VITE_TMDB_API_KEY` (required) and `VITE_STATS_ENDPOINT` (optional — widget degrades to no play counts if unset) into the IIFE bundle at build time. |
| `refresh-bacon-shards.yml` | Daily 06:00 UTC | Pulls bacon shard data from Firestore (uses `FIREBASE_SA_JSON` secret). |
| `rebuild-hub.yml` | Push to `content/site.json` or `content/stories/**` | Builds Field Note social cards (`build-og-cards.py` → `assets/og/`) then re-runs render-hub.py and commits drift. Needs `Pillow`+`numpy` (in `requirements.txt`). |
| `track-traffic.yml` | Daily 06:00 UTC | Auto-discovers all public, non-fork, non-archived repos under `estevanhernandez-stack-ed` (user) and `626Labs-LLC` (org), then pulls GitHub traffic metrics for each. Uses `TRAFFIC_PAT` (user-scope, needs Administration:Read on every tracked repo) and `TRAFFIC_PAT_ORG` (optional org-scope override — without it, org repos fall back to GH_TOKEN and 403 on the Traffic API). |
| `track-downloads.yml` | Daily 06:15 UTC | Snapshots release-asset `download_count` for every repo in `data/repos.json` that ships release assets → `data/download-stats.json` (current detail) + `data/downloads.csv` (daily lifetime totals; day-over-day diff = downloads that day). Public data — implicit `GITHUB_TOKEN` only. |
| `fetch-site-stats.yml` | Daily 06:30 UTC | Pulls GoatCounter visit stats for `626labs.dev` and writes `data/site-stats.json` (uses `GOATCOUNTER_TOKEN` secret). |
| `refresh-rororo-plugins.yml` | Daily 06:45 UTC | Reads the same `plugins-catalog.json` the RoRoRo app reads (off ROROROblox's latest release), enriches each entry with live release version/date/installs → `data/rororo-plugins.json`. `rororo-plugins.html` and the plugins section of `rororo.html` render from it client-side; warns on catalog-vs-release drift. |
| `refresh-plugin-versions.yml` | Daily 07:00 UTC | Reads each plugin repo's latest tag (`content/plugin-repos.json` → GitHub API), writes `data/plugin-versions.json`, re-renders plugin pages so version chips can't drift. Default `GITHUB_TOKEN` reads public tags — no extra secret. |
| `rotate-theme.yml` | Monthly, 09:00 UTC on the 1st + `workflow_dispatch` | Promotes `content/themes.json`'s `queue[0]` to active, unattended. See **Theme rotation** below for the full contract — this row is just the CI-table entry. No extra secret beyond the implicit `GITHUB_TOKEN`. |

**Full secrets inventory:** `FIREBASE_SA_JSON`, `TRAFFIC_PAT`, `TRAFFIC_PAT_ORG`, `GOATCOUNTER_TOKEN`, `VITE_TMDB_API_KEY`, `VITE_STATS_ENDPOINT`, `MCP_VERSION_TRUTH_KEY`. Plus the implicit `GITHUB_TOKEN` that GH Actions injects per-job.

All nine use a retry+rebase loop on `git push` to handle the race where two
bots try to push to main simultaneously.

Plus three that never commit to this repo:

| Workflow | Trigger | Notes |
|---|---|---|
| `version-truth-reconcile.yml` | Daily 08:00 UTC (~3am Chicago) | Corrects drifted 626 dashboard project versions to the latest shipped (non-prerelease) GitHub release per linked repo, via the MCP REST API with the scoped `version-truth-bot` agent key (`MCP_VERSION_TRUTH_KEY`, manage_projects only). Refuses to write past 8 drifts in one run (systemic-change fuse). Dispatch with `dry_run` to preview. |
| `link-check.yml` | Push to `**/*.html` or `**/*.md`, weekly Mon 13:00 UTC | Lychee link-check. Opens an issue on broken links during scheduled runs only. Excludes `themes/archive` — frozen months aren't maintained pages. |
| `visual-diff.yml` | `workflow_dispatch`, or the `visual-diff` label on a PR | Runs `scripts/visual-diff.py` against a base ref. **Never on push, never inside `rotate-theme.yml`** — see *Two-tree visual diff* under **Tools**. Routes the harness's three exit codes to three different outcomes: 0 posts a summary and passes, 1 lists every finding and fails, 2 fails saying nothing was compared. Artifacts (`report.json`, base/head PNGs, console log) upload on a PASS too. |

---

## Theme rotation

626labs.dev's design rotates monthly: a new theme queues, gets gated, and
takes over on the 1st — unattended. Retired themes freeze at a permanent,
dated URL instead of disappearing, so the rotation becomes its own
portfolio piece. `/themes.html` is the indexed gallery (rendered straight
from the registry, so it can never disagree with what's actually live);
`content/themes.json` is the single switch that decides what's live.

**What a theme is** — `themes/<slug>/` containing **eleven** files, all
of which `theme-doctor` requires and will name if absent. Two at the root:

| File | What it is |
|---|---|
| `tokens.css` | The base token layer `themes.html` and `index.html` link: palette, texture, motion, and any layout CSS the theme needs (grid density, card anatomy). Must define every `archetypes.REQUIRED_TOKENS` name. |
| `theme.json` | `{name, slug, thesis, month, status, contrastPairs}` — `contrastPairs` is a list of `[fg-var, bg-var]` pairs `theme-doctor` checks against WCAG AA. `status` is informational only; the gallery and rotation never read it — `content/themes.json` (the registry) is what actually decides. |

…and nine under `themes/<slug>/archetypes/`: the four archetype shells
`home.html`, `product.html`, `reading.html`, `utility.html` (each one the
page skeleton for its archetype — nav, footer, skip link, section
order/presence, and for `home.html` the twelve `SITE_JSON:<zone>:start/end`
markers `render-hub.py` fills), and the five stylesheets `product.css`,
`product-tokens.css`, `utility.css`, `reading.css`, `reading-tokens.css`.

> **There is no `shell.html`.** This section used to name one as the first
> of "exactly three files", and steps 1, 4 and the queueing note repeated
> it. No theme in the repo has ever had that file — A2/A3 accepted a legacy
> `shell.html` OR `archetypes/home.html`, and A4 removed the fallback when
> it extracted the last two archetypes. An author following the old step 1
> literally built a theme missing nine of its eleven required files and
> found out from `theme-doctor`.

Two of
those pair up: **`product.css` is the element dress** (`body`, `a:hover`,
`section.hero`, `.card`, `.btn`) that `render-plugin-pages.py` inlines into
its 15 generated pages, while **`product-tokens.css` is custom-property
definitions and nothing else** — that is a gate, not a convention. The
hand-authored product pages (`conundrum.html`, `rororo-plugins.html`,
`rororo.html`, `mod-launcher-games.html`) link
the token half so they take the palette without inheriting a dress written
for someone else's markup. `tokens.css`, `product-tokens.css`,
`utility.css` and `reading.css` must each define every
`archetypes.REQUIRED_TOKENS` name.

**The borrowed dress — `utility.css`, `press.html` and `privacy.html`.**
Those two pages borrow **100% of their chrome** from the active theme.
Measured against the live DOM, not inferred: 49 of `utility.css`'s 50
selectors match `press.html`, 48 match `privacy.html`, and the overlap with
each page's own `<style>` is **exactly zero**. Their own styles dress their
CONTENT (the asset grid, the policy prose); nav, hero, footer, links, field
and type all arrive from the theme, with nothing page-side to fall back on.
So a theme that satisfies the token contract and skips the dress renders
both pages on the browser's blank default, in Times New Roman, with blue
underlined links — and before this gate existed, `theme-doctor` passed
exactly that theme at exit 0, unattended, on the 1st.

`theme-doctor --browser` now grades both pages by **outcome, never by
selector manifest**. A manifest would fail a theme that puts the field on
`html` instead of `body`, or on `body::before`, or on the page's own
full-bleed overlay div — all correct designs. Instead each page is rendered
twice in one load, with its theme stylesheet enabled and disabled, and every
page-owned region (`html, body, body > div`, `nav.nav`, `header.page-hero`,
`main`, `footer`) must render **differently** between the two. Nothing in
`theme-doctor.py` parses a color; fingerprints are compared as opaque
strings, so `oklch()`, `lab()` and `color-mix()` all pass. Three element
assertions ride alongside, for the things a differential structurally cannot
see: body type is not the browser's own, `h1.page-title` outscales a bare UA
heading, and every `a.inline-link` is distinguishable from the prose it sits
in. What each of those does NOT constrain is in
`check_page_renders_dressed`'s docstring — read it before assuming a failure
is your theme's fault.

The custom-property reads-check is scoped the same way: a `var()` read is
graded against what **that page's own resolution group** loads, not against
every definition anywhere in the theme directory. `tokens.css` defining a
`--pb-*` name no longer satisfies a read in `archetypes/utility.css`, which
`press.html` and `privacy.html` are the only consumers of. Groups are
derived from the code that serves the pages (`render-hub.py`'s
`THEME_CSS_HREFS`, `render-plugin-pages.py`'s inlined concatenation,
`about.html`'s dress picker, and the theme's own `archetypes/home.html`), so
repointing a page's stylesheet moves its group in the same commit.

**Building one:**

1. Branch, create `themes/<slug>/` with all eleven files above — `tokens.css` and `theme.json` at the root, the nine archetype shells and stylesheets under `archetypes/`. Mirror `themes/phosphor-blueprint/` as the reference extraction; copying its directory and re-tokenizing is the intended path, and is also how a theme inherits the `--pb-*` treatment names the hand-authored pages fall back from.
2. `python scripts/theme-doctor.py <slug>` must PASS before anything else. This is the ONLY gate standing between a theme and unattended monthly rotation, so it has to fail honestly: zone markers present, chrome intact (skip-link/nav/footer/analytics), every internal link resolves, and every declared `contrastPairs` clears AA (>= 4.5). Add `--browser` (needs `playwright` installed) for horizontal-scroll (1440/768/390px) and zero-console-error checks — without playwright installed those two checks skip with a one-line note, the local convenience path. The scheduled rotation installs playwright and runs `--browser --require-browser`, which turns that same skip into a gate FAILURE — the one unattended run of this gate can't be allowed to rubber-stamp a rotation because the browser path silently didn't run.
3. Preview it against real content: `python scripts/render-hub.py --theme <slug> --out <dir>` renders that theme's shell to `<dir>/index.html`, plus copies of the eight hand-authored `theme-css` pages (`press.html`, `privacy.html`, `thesis.html`, `workflow.html`, `conundrum.html`, `rororo-plugins.html`, `rororo.html`, `mod-launcher-games.html`) with their stylesheet `<link>` repointed at `<slug>`. Everything lands in `<dir>` and nothing else is touched — no feed, sitemap, story pages, or `themes.html`, no `conundrum.html` gallery zones, and nothing is written back into the repo tree. Those eight keep root-relative asset paths, so serve them from the **repo root** with `<dir>`'s copies laid over the top; opening one straight off disk resolves no CSS.
4. PR the eleven files, `theme-doctor` output pasted in. **`theme-doctor` is not wired into a PR-triggered CI check** — run it locally before requesting review; the only automated run today is inside `rotate-theme.yml`, gating the theme that's about to go live.
5. Merge. Merging changes NOTHING live — a theme only takes effect once its slug lands in `content/themes.json`'s `queue`.

**Queueing:** append the slug to `"queue"` in `content/themes.json` (a normal PR to `main`). Queue order is FIFO — position in the list is rotation order, not a date. `scripts/theme_registry.validate()` enforces basic sanity (no dupes, the active theme never also sitting in the queue, every queued theme's required files present).

**Rotation** (`.github/workflows/rotate-theme.yml`, cron `0 9 1 * *` UTC + `workflow_dispatch`):

1. Empty queue → open a "Theme queue is empty" issue, change nothing, exit. (`dry_run: true` skips even the issue — just logs it.)
2. Freeze the outgoing theme (`scripts/freeze-theme.py <month>`) — see **Archives** below.
3. `active = queue.shift()`; append the outgoing theme to `archive[]`.
4. Re-render the site (`render-hub.py`, no flags) — this also re-renders `themes.html`'s gallery against the new registry state.
5. Gate stack, in order: `theme-doctor.py <new-active> --browser`, `render-hub.py --check`, `pytest tests/ -q`, `site-doctor.py --check`.
6. Any gate failure → nothing committed. Every step downstream chains off the prior step's implicit success, so one failure stops the whole tail; an issue opens with the failed run's link. The site stays at its last verified state — **the site can only ever move from one verified state to another.**
7. `dry_run: true` runs every gate and stages the diff (`git add -A && git diff --stat --cached`) but commits and pushes nothing — use it to sanity-check a queued theme before the 1st actually arrives.
8. Success → one commit (`content/themes.json`, `index.html`, `feed.xml`, `sitemap.xml`, `conundrum.html`, `themes.html`, `editorial/`, `themes/archive/`), pushed with the same retry+rebase loop every other bot workflow in this repo uses.

**Archives:** frozen at rotation time to `themes/archive/<YYYY-MM>/index.html` — a COPY of the already-rendered homepage, never re-rendered again. Two injections: `<meta name="robots" content="noindex">`, and a banner reading "the site as it looked in \<Month Year\>." It carries local copies of every linked stylesheet it needs, so a later retokenize of `tokens.css` or the base `/Design/*.css` layer can't silently repaint it — except fonts, the Bacon Trail widget CSS, and `/assets/*` images, an accepted and documented sharing boundary (see `scripts/freeze-theme.py`'s module docstring for the exact rationale on each). `freeze()` refuses to overwrite an existing archive month — write-once, never re-frozen. Archives are excluded from `sitemap.xml` and from `link-check.yml`'s lychee scan — they're history, not maintained pages.

**Rollback:** `content/themes.json` is the ONLY switch. `git revert` the rotation commit and the previous `active`/`queue`/`archive` state comes right back — no script needed. The frozen archive written during that rotation already exists on disk either way (freeze is a one-way, additive action; reverting the registry commit doesn't and shouldn't delete it).

---

## Tools

Repo-local utilities that aren't the site itself but ship from this repo:

### Image background removal — `tools/bgremove/`

For any image cut: logos, banners, ad assets, screenshots, social posts.
Two entry points:

- **`tools/bgremove/bgremove.py`** — pure CV. Six modes: color-key, contour,
  grabcut, matting, ai (rembg), auto. Batch mode via directory input.
- **`tools/bgremove/agent.py`** — Claude vision wraps the CLI. Picks the
  best mode, runs it, evaluates the result, retries up to N attempts,
  returns the best one. Needs `ANTHROPIC_API_KEY` in env.

For most work, use the agent:

```
python3 tools/bgremove/agent.py path/to/image.png -o cut.png
```

Tracks per-attempt sidecars (`<output>.attempt1.png`, `.attempt2.png`)
and copies the best to your `-o` path. See the file's docstring for the
full mode rundown and tradeoffs.

### Brand exports — `scripts/export-brand.py`

Regenerates `assets/brand/` (transparent icon at 256/512/1024 + banner
PNGs at 1500x500, 1280x640, 1200x630). Re-run after brand changes.
No `--check` flag — verify visually by opening `icon-transparent-512.png`
and one banner.

### Field Note social cards — `scripts/build-og-cards.py`

Generates a branded 1200x630 OG/social card per local Field Note into
`assets/og/<slug>.png` (navy field + cyan/magenta glow, title hero,
hairline, dek, footer). `render-hub.py` points each story page's
`og:image` and BlogPosting `image` at the card when it exists, else falls
back to `assets/brand/medium-header-1500x600.png`. **CI owns `assets/og/`**
— `rebuild-hub.yml` (ubuntu) builds the cards before rendering on any push
to `content/stories/**`, so a new or retitled story gets its card without a
manual step. Run `python scripts/build-og-cards.py` only for a local
preview, and **don't commit cards regenerated on a non-Linux box** — a
pinned Pillow is byte-stable run-to-run on one OS but its bundled FreeType
rasterizes a few bytes differently across platforms, so a local Windows
`--check` will show a harmless diff against the ubuntu-committed cards. Let
rebuild-hub regenerate them. (`--check` byte-compares and exits nonzero on
any missing/stale card, like `render-hub.py --check`.)

### Site renderer — `scripts/render-hub.py`

Rebuilds `index.html` from `content/site.json`. `--check` for drift detection.
Counts/lists in prose can use `{{fact:KEY}}` tokens — they resolve at render
time from `scripts/site_facts.py` (e.g. `{{fact:claude_plugins}}`,
`{{fact:live_plugin_names}}`, `{{fact:cmd_vibe-cartographer_word}}`). An unknown
token fails the render loudly, so a typo never ships.

### Agent management CLI — `scripts/site.py`

The agent equivalent of the admin dashboard. `facts`/`get`/`doctor`/`render`/`ops`
to inspect; `set-status` to mutate with validate-before-commit guardrails (the
edit auto-reverts if it would fail the doctor). See `AGENTS.md`.

### Content health — `scripts/site-doctor.py`

The checkup + CI gate. `--report` for an on-demand health printout (derived
facts, supplement reminders, drift); `--check` exits nonzero on any failure (CI
uses this). Validates prose-vs-facts (a curated registry), dangling local-asset
references, and render drift. Facts derive via `scripts/site_facts.py`; truths
that can't be derived locally (Microsoft Store releases, a plugin's command
count) live in `content/facts-supplement.json` — re-confirm those periodically.
The `content-health.yml` workflow runs the doctor on PRs and weekly.

### Two-tree visual diff — `scripts/visual-diff.py`

Answers one question: **did this branch move anything a visitor can see?**
Serves a base git ref and the working tree on two local ports, renders both
in the same Chromium, and compares three channels — full-frame pixels,
computed styles (78 properties per element plus `::before`/`::after`), and
hover states. No golden images, no threshold, no masking: a single differing
pixel is a finding. Golden PNGs were rejected for the reason
`build-og-cards.py` already documents — FreeType rasterizes differently
across platforms, so references committed from the ubuntu runner would diff
against every Windows run forever.

```
python scripts/visual-diff.py origin/main
python scripts/visual-diff.py origin/main --pages press.html privacy.html
python scripts/visual-diff.py origin/main --widths 1440,390 --channels pixel,computed
python scripts/visual-diff.py origin/main --self-check   # base vs base
```

- **The base ref is positional and must come FIRST.** `--pages` is
  `nargs="+"`, so a trailing ref gets swallowed into the page list.
- **Exit codes: 0** nothing moved, **1** at least one channel reported a
  difference, **2** the run could not be made (bad ref, no playwright, a
  browser that would not launch, a bug in the harness). Never conflate 1 and
  2 — 2 means nothing was compared, which is not a pass.
- **Run `--self-check` before believing a non-zero result.** It points both
  servers at the base tree; anything it reports is capture noise, not a
  regression. It is how five harness defects were found before this shipped.
- The page list derives from `content/page-archetypes.json`, so a new page
  joins the sweep the commit it is mapped to an archetype. 39 today.
- **A full sweep is 17.5 minutes** (39 pages × 3 widths × 3 channels).
  `--widths 1440,390` is the cheaper shape; `--channels pixel,computed`
  cheaper still. That cost is why it is on-demand only.
- **Read the module docstring's non-coverage list before trusting a green
  run.** `:focus`, `:active`, print styles, later animation keyframes, the
  4th element of a hover signature, and anything semantic are all unsampled.
  A test pins that list so it cannot quietly erode.

CI wiring is `.github/workflows/visual-diff.yml` — `workflow_dispatch` or
the `visual-diff` PR label. It is deliberately **not** on push (the runtime)
and deliberately **not** in `rotate-theme.yml` (on the 1st every pixel is
supposed to move, so a pixel gate there is meaningless). Both prohibitions
are pinned by a test against the module docstring.

### Admin favicon — `scripts/build-admin-favicon.py`

Regenerates `assets/favicon-admin.png` — the gradient-square browser-tab
icon for the admin dashboard so it reads distinctly from the main site
favicon. Re-run if the brand cyan/magenta tokens change.

### Local widget dev — `apps/widget-bacon-trail/`

For local iteration on the Bacon Trail widget: `cd apps/widget-bacon-trail
&& npm run dev` runs Vite's dev server. Push to `main` (any change under
`src/`) lets `build-widget.yml` rebuild and commit the bundle. Don't
hand-edit the bundle output at `widget-bacon-trail/`.

---

## Common tasks

| You want to… | Path |
|---|---|
| Edit a site section (hero, products, etc.) | Admin → that tab → save |
| Edit a story | Admin → Stories tab |
| Add a new product screenshot | Admin → Products → drop into screenshot zone |
| Cut a background from an image | `python3 tools/bgremove/agent.py <img>` |
| Update the brand palette / typography | Edit `Design/colors_and_type.css` (and the `626labs-design` skill if global), then `python3 scripts/export-brand.py` |
| Regenerate a brand banner / icon | `python3 scripts/export-brand.py` |
| Check why the site looks stale | `python3 scripts/render-hub.py --check` |
| See bot run status | Admin → Ops tab |
| Preview a theme without touching the live site | `python3 scripts/render-hub.py --theme <slug> --out <dir>` |
| Gate a theme before opening its PR | `python3 scripts/theme-doctor.py <slug> --browser` |
| Check whether a branch moved any pixels | `python3 scripts/visual-diff.py origin/main` (base ref FIRST), or put the `visual-diff` label on the PR |
| Queue a theme for the next rotation | Append its slug to `"queue"` in `content/themes.json` |
| Roll back a bad rotation | `git revert` the `chore(themes): rotate to ...` commit |
| Ship a new top-level page | Merge (the sitemap updates itself) → then GSC: URL Inspection → Request Indexing for the new URL at search.google.com/search-console. Agents: list the new public URL(s) in every ship report — this step is part of the workflow, not optional polish. Sitemap re-submission is never needed (same URL; Google re-reads it). |

---

## Conventions

- **Commits:** Conventional commits — `feat`, `fix`, `chore`, `ci`, `docs`,
  `refactor`. Inferred from the recent log; no hard policy.
- **No build artifacts in repo, with one exception:** `widget-bacon-trail/`
  (the Vite bundle output) IS checked in — GitHub Pages serves it directly,
  so the build artifact has to be in the tree.
- **Image filenames:** the admin's screenshot uploader generates them
  automatically (`<timestamp>-<slug>.<ext>` under
  `assets/screenshots/<product-id>/`). Don't bypass the uploader.
- **Brand assets in `assets/brand/`** are read-only outputs of
  `scripts/export-brand.py`. Don't hand-edit; re-run the script.

---

## Decisions log

Significant decisions log to the **626Labs Dashboard** via MCP
(`mcp__626Labs__manage_decisions` — action `log`). Search past decisions
for this repo with action `search`, filtering by project ID. Tag every new
entry with the bound project ID.

Project binding happens automatically on session start via
`mcp__626Labs__manage_projects findByRepo` against `git config --get
remote.origin.url`. The Architect handles this without ceremony.

---

## What NOT to do

- Don't hand-edit `index.html` — it's a generated artifact of the active
  theme's `shell.html`. Content edits (SITE_JSON zones) go in
  `content/site.json`; chrome/layout edits go in
  `themes/<active-slug>/shell.html`. Either way, render-hub.py rewrites
  `index.html` and silently reverts a direct edit.
- Don't put secrets in the system prompt or any committed file. Tools use
  `os.environ` (`ANTHROPIC_API_KEY` for the bgremove agent, repo PATs for
  bot workflows via `secrets.*`).
- Don't `git push --force` to main — bot workflows assume linear history.
- Don't write a new file under `assets/brand/` — that directory is
  generated. Write to a different folder under `assets/`.
- Don't edit the widget bundle at `widget-bacon-trail/` directly — edit
  `apps/widget-bacon-trail/src/`, push, and let `build-widget.yml` rebuild.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **626labs-hub** (2424 symbols, 5028 relationships, 138 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/626labs-hub/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/626labs-hub/context` | Codebase overview, check index freshness |
| `gitnexus://repo/626labs-hub/clusters` | All functional areas |
| `gitnexus://repo/626labs-hub/processes` | All execution flows |
| `gitnexus://repo/626labs-hub/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
