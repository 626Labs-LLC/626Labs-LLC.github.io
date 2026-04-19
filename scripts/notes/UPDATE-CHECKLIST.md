# Hub Update Checklist

When something changes in the 626 Labs ecosystem, this recipe tells you what — if anything — needs to change on **626labs.dev**. Most numbers update automatically via shields.io; most copy and screenshots are curated and need a human touch.

---

## Auto vs manual at a glance

| Signal | Handled by | You do |
|---|---|---|
| npm version badge | `shields.io/npm/v/...` | nothing |
| GitHub release badge | `shields.io/github/v/release/...` | nothing |
| Total downloads | `shields.io/npm/dt/...` (masked when "too new") | nothing |
| License badge | `shields.io/npm/l/...` | nothing |
| YouTube thumbnails | `img.youtube.com/vi/<id>/hqdefault.jpg` | nothing — unless the video is deleted |
| Card descriptions | — | edit `index.html` |
| "Coming soon" → shipped | — | see recipe below |
| Lab shelf pool | — | edit `LAB_POOL` at bottom of `index.html` |
| Dashboard screenshots | — | re-screenshot + overwrite files |
| Framework doc link | — | update `href` in `index.html` |
| Logo / favicon | — | drop new `logo.png`, re-run `scripts/crop-icon.py` |

---

## Recipes (by event)

### 🚀 I shipped a new plugin version

- **Version bumps, feature set same:** do nothing. Shields refreshes within ~5 min.
- **Description is now out of date:** edit the relevant card in the Products grid. Keep the badges / install / link rows intact.
- **New install command or platform:** update the `<div class="install">` block and the links row.

### 🧪 A plugin moves from "coming soon" to shipped

1. Find the card in `<section class="products">`.
2. Swap `class="card coming-soon"` → `class="card"`.
3. Remove the `<span class="status">coming soon</span>` from the `<h3>`.
4. Add the standard shipped-plugin structure — copy Cart or Vibe Doc as a template:
    - `<div class="badges">` with `npm/v`, `npm/dt` (mark `data-maskable="true"`), `npm/l` shields
    - `<div class="install">` with the marketplace add command
    - `<div class="links">` with GitHub · npm · (optional CLI) row
5. Commit: `hub: promote <plugin> to shipped`

### 🎬 I released a new app worth showing on the shelf

Edit `LAB_POOL` at the bottom of `index.html`.

- **Has a YouTube demo:** add `video: "<videoId>"` — the thumbnail autoloads from `img.youtube.com`.
- **Has a screenshot:** drop it at `assets/thumb-<slug>.png` (ideally 16:9, ≥1280px wide) and add `image: "assets/thumb-<slug>.png"`.
- **Neither:** add the entry anyway — it'll render text-only. Or hold the entry until you have a visual.

Write a concrete `desc` that matches what the screenshot/video actually shows. Commit: `hub: add <name> to lab shelf`.

### 📺 I have a fresh demo video

- Upload to YouTube on [@ItsJustEste](https://www.youtube.com/@ItsJustEste).
- Grab the video ID from the URL.
- Add `video: "<id>"` to the matching `LAB_POOL` entry (or swap the existing one).
- No need to save a thumbnail — it pulls from `img.youtube.com`.

### 🖼️ The Lab Dashboard UI changed

Screenshot the Universe bubble view and the Operations (project cards) view.

- Save as `assets/dashboard-universe.png` and `assets/dashboard-projects.png` (overwrite the existing files).
- Commit: `hub: refresh dashboard screenshots`.

### 🧭 The Self-Evolving Framework doc moved

Currently the "Thinking behind it" section links to:
`https://github.com/estevanhernandez-stack-ed/vibe-cartographer/blob/main/docs/self-evolving-plugins-framework.md`

If the doc migrates into the monorepo (or anywhere else), update that single `href` in `index.html`.

### 🎨 The brand / logo changed

1. Overwrite `logo.png` at the repo root with the new 1080×1080 (or larger) PNG.
2. Re-run: `python3 scripts/crop-icon.py` — regenerates `favicon-626.png` + `assets/icon-626.png` from the top portion of the logo.
3. If the brand colors also changed, update the `:root` tokens in `index.html` and all `rgba()` literals. Keep them in sync with `Design/colors_and_type.css`.
4. Commit: `hub: refresh brand assets`.

### 🎁 I'm launching Vibe Launch / Vibe Sec publicly

- Add a new Products-grid card (clone Vibe Test as a template).
- Update the About section's plugin list if the new product changes the four-plugin lineup (Cartographer · Doc · Test · Sec).
- Log a decision via the 626 Labs Dashboard.

---

## Don't touch without thinking

- `LAB_POOL` entries with `video:` — deleting the YouTube video kills the thumbnail.
- `favicon-626.png` / `assets/icon-626.png` — generated. Edit the source (`logo.png`) and re-run the script instead.
- The `maskStaleBadges()` JS function — it's what hides the "package not found or too new" shields automatically. Leave it alone.
- `scripts/build-thumbnails.py` — regenerates Writer's Studio logo, Replit cert frame, book-cover crop. Re-run if any of those assets need refreshing.

---

## Cadence

- **On any product repo release:** glance at that card. Usually nothing to do.
- **Monthly:** skim the shelf. Rotate in a new app if something's worth showing.
- **Quarterly:** full audit — re-read About / Thinking / Products / Hero copy. Update anything that's drifted.
- **Weekly link check:** the `.github/workflows/link-check.yml` workflow runs every Monday morning. If it opens an issue listing broken links, fix those.

---

## Handy paths

```
index.html                            ← the whole site
Design/                               ← brand source of truth (mirrors the installed skill)
assets/                               ← screenshots, thumbnails, icons
sanduhr/                              ← Sanduhr product sub-page
scripts/crop-icon.py                  ← regenerate favicon from logo
scripts/build-thumbnails.py           ← regenerate derived thumbnails
scripts/notes/copy-brief.md           ← voice-agent copy brief
scripts/notes/UPDATE-CHECKLIST.md     ← this file
scripts/notes/VIBE-ECOSYSTEM-BRIEFING.md  ← original session briefing
scripts/notes/copy-diff.md            ← copy-pass changelog
.github/FUNDING.yml                   ← Sponsor button config
.github/workflows/link-check.yml      ← weekly + on-push link checker
```
