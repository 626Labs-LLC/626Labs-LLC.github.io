# 626 Labs Portfolio Hub — repo guide

The marketing site at **626labs.dev**, hosted on GitHub Pages. Plus the
admin dashboard, image pipeline, bot workflows, and side-tools that grew up
around it.

> **Persona:** This repo inherits The Architect from `~/.claude/CLAUDE.md`.
> No need to re-establish — just adds project context below.

---

## Tech Stack & Voice

- **Site shell:** Hand-written HTML + vanilla JS + inline CSS. No framework
  on the marketing surface, no build step. Edit `index.html` only inside
  zones the renderer doesn't touch.
- **Widget app:** `apps/widget-bacon-trail/` — Vite + TypeScript. The only
  build pipeline in the repo. Output committed to `widget-bacon-trail/`
  (root) so GitHub Pages serves it directly at `/widget-bacon-trail/`.
- **Admin:** Babel-in-browser React (`admin/*.jsx`). No build step;
  reads/writes via the GitHub Contents API with a fine-grained PAT.
- **Brand:** Cyan `#17d4fa` + magenta `#f22f89` — always paired. Dark navy
  `#0f1f31` field. Space Grotesk display, Inter body, JetBrains Mono code
  + small UPPERCASE meta labels with +0.12em tracking.
- **Voice:** Builder-to-builder, second person, sentence case. No
  "empower / leverage / seamlessly / unlock / unleash." Em-dashes welcome.
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
| `index.html` | The live site. Hand-written shell with `SITE_JSON:<zone>:start/end` markers that get filled by render-hub.py. |
| `content/site.json` | Source of truth for everything editorial — hero, products, lab, play, about, support, contact, thinking, labRuns. |
| `content/stories/*.md` | Long-form case studies. Edited via the admin's Stories tab. |
| `admin/` + `admin-dashboard.html` | Babel-in-browser React admin. PAT-auth against this repo. Edits site.json, uploads to assets/, manages stories, surfaces bot run status. |
| `apps/widget-bacon-trail/` | The embedded Birthday Bacon Trail widget. Bundle output lives at `widget-bacon-trail/` (root) so GH Pages serves it at `/widget-bacon-trail/`. |
| `assets/` | Screenshots, OG images, favicons, brand exports. `assets/brand/` has the canonical icon + banners (built by `scripts/export-brand.py`). `assets/screenshots/<product>/` is what the admin uploader writes to. |
| `Design/` | Brand reference + the design skill's UI kit. |
| `scripts/` | Site pipeline: render-hub, refresh-bacon-shards, track-traffic, build-thumbnails, export-brand, build-admin-favicon. |
| `tools/bgremove/` | Standalone CV background remover with a Claude-vision agent loop. See *Tools* below. |
| `.github/workflows/` | 4 bot workflows that push to main. All have retry+rebase loops as of 2026-04-27. |
| `fonts/` | Variable TTFs for the brand (Space Grotesk, Inter, Inter Italic, JetBrains Mono). SIL OFL. |

---

## How the site rebuilds

- Edit `content/site.json` (admin or by hand) → push.
- `rebuild-hub.yml` runs `scripts/render-hub.py` → rewrites `index.html`.
- GitHub Pages redeploys.
- `python3 scripts/render-hub.py --check` is idempotent; CI uses it to detect drift.

## The 4 bot workflows on main

| Workflow | Trigger | Notes |
|---|---|---|
| `build-widget.yml` | Push to `apps/widget-bacon-trail/src/**` | Vite-builds the widget, commits the bundle to `widget-bacon-trail/`. |
| `refresh-bacon-shards.yml` | Daily 06:00 UTC | Pulls bacon shard data from Firestore (uses `FIREBASE_SA_JSON` secret). |
| `rebuild-hub.yml` | Push to `content/site.json` | Re-runs render-hub.py and commits drift. |
| `track-traffic.yml` | Daily 06:00 UTC | Pulls GitHub traffic metrics (uses `TRAFFIC_PAT` secret). |

All four use a retry+rebase loop on `git push` to handle the race where two
bots try to push to main simultaneously.

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

### Site renderer — `scripts/render-hub.py`

Rebuilds `index.html` from `content/site.json`. `--check` for drift detection.

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

- Don't hand-edit `index.html` inside the `SITE_JSON:` zones — render-hub.py
  rewrites them. Edit `content/site.json` instead.
- Don't put secrets in the system prompt or any committed file. Tools use
  `os.environ` (`ANTHROPIC_API_KEY` for the bgremove agent, repo PATs for
  bot workflows via `secrets.*`).
- Don't `git push --force` to main — bot workflows assume linear history.
- Don't write a new file under `assets/brand/` — that directory is
  generated. Write to a different folder under `assets/`.
- Don't edit the widget bundle at `widget-bacon-trail/` directly — edit
  `apps/widget-bacon-trail/src/`, push, and let `build-widget.yml` rebuild.
