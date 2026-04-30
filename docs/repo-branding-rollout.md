# Repo branding rollout — checklist

Single-page punch list for getting branded social previews + README banners onto every public 626 Labs repo. Generated 2026-04-29 from `data/repos.json` + the per-repo asset inventory in `assets/brand/`.

## What goes on each repo

| Surface | Asset size | Where to set it |
|---|---|---|
| **Social preview** (the card that renders when the repo is shared on social media) | 1280×640 | `https://github.com/<owner>/<repo>/settings` → scroll to *Social preview* → *Edit* → upload |
| **README banner** (top-of-page header) | 1500×500 | Edit `README.md`, prepend an `<img>` tag pointing at the raw URL on the hub repo (see template below) |
| **Repo avatar** (the icon on the org/user page) | 1024×1024 | For org-owned repos: org Settings → Profile picture. For user repos: it's the user avatar — usually skipped. |

### Raw URL template

For any asset committed to `626Labs-LLC/626Labs-LLC.github.io`:

```
https://raw.githubusercontent.com/626Labs-LLC/626Labs-LLC.github.io/main/<asset-path>
```

### README banner snippet template

Drop at the very top of `README.md`, before the `# Title`:

```markdown
<p align="center">
  <img src="https://raw.githubusercontent.com/626Labs-LLC/626Labs-LLC.github.io/main/<asset-path>" alt="<repo display name>" width="100%"/>
</p>
```

---

## The plugin family

**Status:** social previews already uploaded by Este (2026-04-29). README banners optional follow-up.

| Repo | Owner | Social preview asset | README banner asset | SP done? | README done? |
|---|---|---|---|---|---|
| `vibe-cartographer` | estevanhernandez-stack-ed | `assets/brand/plugins/vibe-cartographer-banner-1280x640.png` | `assets/brand/plugins/vibe-cartographer-banner-1500x500.png` | ✅ | ☐ |
| `Vibe-Doc` | estevanhernandez-stack-ed | `assets/brand/plugins/vibe-doc-banner-1280x640.png` | `assets/brand/plugins/vibe-doc-banner-1500x500.png` | ✅ | ☐ |
| `vibe-plugins` (marketplace) | estevanhernandez-stack-ed | `assets/brand/vibe-plugins-banner-1280x640.png` | `assets/brand/vibe-plugins-banner-1500x500.png` | ✅ | ☐ |
| `vibe-keystone` | estevanhernandez-stack-ed (or in vibe-plugins monorepo slot) | `assets/brand/plugins/vibe-keystone-banner-1280x640.png` | `assets/brand/plugins/vibe-keystone-banner-1500x500.png` | ✅ | ☐ |
| `vibe-test` | estevanhernandez-stack-ed | `assets/brand/plugins/vibe-test-banner-1280x640.png` | `assets/brand/plugins/vibe-test-banner-1500x500.png` | ✅ | ☐ |
| `vibe-sec` | estevanhernandez-stack-ed | `assets/brand/plugins/vibe-sec-banner-1280x640.png` | `assets/brand/plugins/vibe-sec-banner-1500x500.png` | ✅ | ☐ |
| `vibe-thesis` | estevanhernandez-stack-ed | `assets/brand/plugins/vibe-thesis-banner-1280x640.png` | `assets/brand/plugins/vibe-thesis-banner-1500x500.png` | ✅ | ☐ |
| `thesis-engine` | estevanhernandez-stack-ed | `assets/brand/plugins/thesis-engine-banner-1280x640.png` | `assets/brand/plugins/thesis-engine-banner-1500x500.png` | ✅ | ☐ |

---

## Native apps

**Status:** assets generated 2026-04-29. Awaiting upload.

Per-app banners use each repo's existing icon as the centered glyph (Sanduhr's hourglass, RTClickPng's PNG-document mark) rather than a procedurally drawn glyph. RBX15 falls back to the 626 Labs hex since the repo doesn't ship its own app icon.

| Repo | Owner | Social preview asset | README banner asset | SP done? | README done? |
|---|---|---|---|---|---|
| `Sanduhr_f-r_Claude` | estevanhernandez-stack-ed | `assets/brand/apps/sanduhr-banner-1280x640.png` | `assets/brand/apps/sanduhr-banner-1500x500.png` | ☐ | ☐ |
| `RTClickPng` | estevanhernandez-stack-ed | `assets/brand/apps/rtclickpng-banner-1280x640.png` | `assets/brand/apps/rtclickpng-banner-1500x500.png` | ☐ | ☐ |
| `RBX15-Shirt-and-Pants` | estevanhernandez-stack-ed | `assets/brand/apps/rbx15-shirt-pants-banner-1280x640.png` | `assets/brand/apps/rbx15-shirt-pants-banner-1500x500.png` | ☐ | ☐ |

---

## Lab / meta

| Repo | Owner | Social preview asset | README banner asset | SP done? | README done? |
|---|---|---|---|---|---|
| `626Labs-LLC.github.io` (this repo) | 626Labs-LLC | `assets/brand/medium-header-1280x640.png` | `assets/brand/medium-header-1500x500.png` | ☐ | n/a (site is the README) |

---

## Direct links — Settings → Social preview

For batched upload sessions, copy these URLs:

- https://github.com/estevanhernandez-stack-ed/Sanduhr_f-r_Claude/settings
- https://github.com/estevanhernandez-stack-ed/RTClickPng/settings
- https://github.com/estevanhernandez-stack-ed/RBX15-Shirt-and-Pants/settings
- https://github.com/626Labs-LLC/626Labs-LLC.github.io/settings

Each opens the repo Settings page; scroll down to *Social preview* and upload the matching `assets/brand/.../*-banner-1280x640.png`.

---

## What's NOT in this list

Browsing `data/repos.json` after tomorrow's track-traffic run will surface every public repo, not just the ones with first-class banners. For repos without first-class banners (Replit projects, experiments, side tools), the **generic 626 Labs banner** at `assets/brand/medium-header-1280x640.png` works as a default — it just shows the lab identity rather than a per-repo glyph.

---

## Re-rendering

All three banner-export scripts are re-runnable:

```bash
python3 scripts/export-medium-header.py        # the lab's editorial header
python3 scripts/export-vibe-plugins-logo.py    # the marketplace co-brand mark
python3 scripts/export-plugin-icons.py         # all 7 plugins (per-glyph)
python3 scripts/export-app-icons.py            # all native apps (per-app icon)
```

Edit each script's data list to add a new entry — every output size (1500×500, 1280×640, 1024 square) regenerates automatically.
