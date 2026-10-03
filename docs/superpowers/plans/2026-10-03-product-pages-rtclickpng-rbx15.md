# Product pages: Right Click PNG and RBX15

**Date:** 2026-10-03. **Dashboard task:** `task-1790031559314-uoaz3qt02` (In Progress).
**Este's ruling:** build both pages; hold SnapSnip, it's being rebuilt. Plan down to the screenshots each page needs.

Both apps are live Store apps that today exist on the hub only as a row in the home contents list. Each gets its own hand-authored product page on the `rororo.html` / `mod-launcher-games.html` model, ending in the per-country reach map the Store geography pull already feeds.

## The page shape (both pages)

Same skeleton `rororo.html` uses, cut to what each app has to say. Hand-authored HTML, palette from the theme's `archetypes/product-tokens.css` through the renderer-owned `theme-css` zone, so Slate dresses it now and Cyan Fade on Nov 1 with no per-page theme work.

| Section | Right Click PNG | RBX15 |
|---|---|---|
| Hero | Name, one-line pitch, Store badge, GitHub link, repo meter | Same |
| The problem | The `.webp` that won't paste | Placing art vs painting clothes |
| What it does | Convert / Copy / batch / settings | Layers, fills that wrap, gradients that span, word art |
| See it work | Five shots (below) | Six shots (below) |
| How it's built | C++/WinRT shell extension + .NET 9 AOT engine, seven decoders, 85 tests; the 24-hour build with Vibe Cartographer, linked to its Field Note | Electron app; layer compositing, the 585×559 grid |
| Trust | Offline by design: no network, no telemetry, original never touched | No account, no Roblox connection, fonts are the only fetch; the trademark block |
| Reach | `reach-map` for `9PKKLK6R5WFL` | `reach-map` for `9MV9G4XFJ8S0` |

**Copy source:** the approved Store copy in `store-listing-console/apps/<app>/copy/listing-copy.md` (both approved 2026-09-10, copy-reviewer SHIP). Lift, don't redraft, then run it through `copy-reviewer` for the hub's voice rules.

**One truth fix before any copy ships.** RBX15 is Electron (`package.json`: `electron ^41`). The approved Store copy calls it "a native Windows editor" and the hub's product row carries a `native` tag. The page says "Windows desktop app" and drops `native`; flag the Store copy for the next submission.

**Version check.** RBX15 4.1.0 (2026-07-21) added gradients, patterns and fills that wrap the body. Every screenshot on file shows V4.0, so none of them shows the feature the copy leads with.

## Screenshots

Capture conditions for every new shot: Windows 11 at 100% scale, a clean desktop and Explorer (no personal folders, no other apps' tray clutter), dark mode to sit on the hub's dark plates, PNG. Full window or a deliberate crop; no fragment strips.

### Right Click PNG: 5 shots, 0 usable

On file (`store-listing-console/apps/rtclickpng/assets/screenshots/`): a 621×437 settings crop and a 629×117 context-menu strip. Both are fragments. The settings crop also prints the user's `AppData\Local\Packages` path, so it can't go on a public page as is.

The five come straight from the repo's own unexecuted plan (`RTClickPng/docs/ms-store-submission-playbook.md`, "Screenshots to capture"):

| # | Shot | What must be visible | Status |
|---|---|---|---|
| 1 | **Context menu on a `.webp`** (hero) | Explorer with a `.webp` selected, the Right Click to PNG group open, Convert to PNG and Copy as PNG visible | Need; the strip on file is the cropped version of this |
| 2 | **The toast after Convert** | The summary toast plus the new `.png` next to the original in the same folder | Need |
| 3 | **The paste landing** | A Copy as PNG result pasted into Teams, Slack, Discord or Figma, ideally the app that rejected the `.webp` | Need |
| 4 | **Settings window** | Both toggles (JPEG variants, confirm before overwriting), branded title bar; settings path cropped out or showing a neutral user | Need re-take; current crop leaks the user path |
| 5 | **Batch** | A multi-selection (mixed `.heic`, `.avif`, `.webp`) with the menu open, then the single summary toast | Need |

Optional sixth for the build section: the Vibe Cartographer checklist or the 85-tests run, if the Field Note doesn't already carry one.

### RBX15: 6 shots, 2 usable as fallbacks

On file: seven full-window captures in `RBX15-Shirt-and-Pants/docs/screenshots/app-*.png` (also the Store's seven). Two are proper windows: `app-home.png` (1465×976) and `app-layers.png` (1465×1155, layers panel and drip assets on the template). The other five are crops 168 to 499 px tall. All of them show V4.0.

| # | Shot | What must be visible | Status |
|---|---|---|---|
| 1 | **The money shot** (hero) | One gradient sweeping across all torso panels, or a dot or camo pattern tiling unbroken across the seams. That's the 4.1 feature and the Store copy names it | Need; nothing on file shows 4.1 fills |
| 2 | **Layers** | The layer stack with Dupe, Hide and Del, several layers composed on the template | Have `app-layers.png` (V4.0); re-take on 4.1 for the version chip |
| 3 | **Live fill editing** | The fill angle or colors changing, with every connected panel updating. A before/after pair or a short GIF | Need |
| 4 | **Word art** | The Text tab with a styled word and the preview, then the word on the canvas | Have the 1453×274 strip; need the full window with the word placed |
| 5 | **Pants** | The pants template with a pattern running down both legs, so the page isn't shirts only | Need |
| 6 | **The export** | The finished 585×559 PNG beside the template, or the Download template button. Proves "what you export is what Roblox expects" | Need |

Optional: the shirt worn on an in-game avatar. It's the most persuasive image for this audience, but it needs a Roblox upload and a capture, and the trademark rules (nominative use only, no Roblox branding as decoration) apply.

## Wiring each page into the hub

The full add-a-page surface, per page:

1. `rtclickpng.html` / `rbx15.html` at the repo root, from `mod-launcher-games.html` as the closest template (Store app, repo link, reach map, no plugin catalog).
2. `scripts/render-hub.py`: a path constant, an entry in `THEME_CSS_HREFS` (`archetypes/product-tokens.css`) and in `THEME_CSS_ONLY_PAGES`.
3. `content/page-archetypes.json`: map the page to `product` (`archetypes.validate` fails on an unmapped public page).
4. `content/site.json`: the product's `productPage`. That flips the home row's click-through, and the page-pane mod resolves to the new page with no change on its side.
5. The page carries the repo meter (`data-repo`), the reach map (`data-app`), GoatCounter, and `/assets/reach-map.js` + `/repo-meter/meter.*`.
6. Screenshots go in through the admin uploader (`assets/screenshots/<product-id>/`, uploader-named), never hand-named into `assets/`.
7. Gates: `theme-doctor` on both themes with `--browser`, `render-hub --check`, `site-doctor --check`, pytest; a visual-diff label on the PR.
8. After merge: GSC → URL Inspection → Request Indexing for both new URLs.

## Order

1. Este captures the 11 shots: 5 for Right Click PNG on a clean Win11 profile, 6 for RBX15 on 4.1. That's the only step that needs his machine. The same captures refresh both Store listings, which have carried fragment screenshots since launch.
2. Build Right Click PNG's page first. Its copy is final and its story (24 hours, Vibe Cartographer, offline by design) is the stronger one.
3. Build RBX15's after the Electron/native wording is settled.
4. SnapSnip: on hold until the rebuild ships. Same plan shape when it does.
