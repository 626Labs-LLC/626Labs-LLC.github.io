# Asset roundup — raw harvest from the estate

Harvested 2026-07-08 from every personal repo under `Projects\`. One folder per app/plugin, curated to canonical brand assets: primary icons/logos (largest variant only, MSIX scale-armies skipped), store images, and organized screenshot folders.

This is **raw material**, not finished exports. Curated/final brand assets live in `assets/brand/apps/` and `assets/brand/plugins/` using the `<slug>-<kind>-<dims>.png` convention.

## Provenance notes

- Sources are each repo's own assets (`docs/store-assets/`, `windows/msix/Images/`, `public/icons/`, etc.). Filenames preserved except where renamed to disambiguate (QuizShow per-app favicons, SnipSnap `logo-1240.png` = Square310x310 scale-400).
- Duplicate clones: harvested from kebab-case canonicals only (`Cleanup-Ranger`, `Safety_Assistant`, `Chef-I-s`). As of 2026-10-03 the first two directories are gone; the space-named clones (`Cleanup Ranger`, `Safety Assistant`) carry the same remotes and are what the refresh reads.
- Excluded on purpose: coverage-report favicons, `_old`/`.old` copies, git worktrees, older 626Labs dashboard siblings, `Safety Assistant/data/incoming/` (app data, not marketing), loose unorganized root screenshots (Boutique, attached_assets).
- Excluded pending tenant call: PriceScout*, theatre-operations-platform, CompReport (work-adjacent).

## Finding an asset: `index.json`

Don't hand-type paths into this tree. `index.json` lists every product folder:

```json
{ "id": "sanduhr", "name": "Sanduhr für Claude", "siteId": "sanduhr",
  "repo": "estevanhernandez-stack-ed/Sanduhr_f-r_Claude", "sourceDir": "docs/store-assets",
  "harvested": "2026-07-08", "icon": "assets/roundup/sanduhr/icon-1024-rgb.png",
  "logo": "...", "hero": null, "screenshots": ["..."], "other": ["..."] }
```

- Paths are repo-root-relative; prefix `/` for the live URL on 626labs.dev.
- `siteId` is the `content/site.json` products id when the product is on the site (folder ids differ: `rororoblox` is `rororo`, `rbx15-shirt-and-pants` is `rbx15-shirt-pants`, `snipsnap` and `powertoys-snipsnap` are both `snapsnip`). `name` comes from site.json when there is a `siteId`.
- `icon` / `logo` / `hero` are picked by name and dimensions (largest square mark, lockup or non-square logo, hero/banner or wide); every other image is under `screenshots` or `other`. A heuristic, not a curator: check the file before putting it on a page.
- `gaps` lists site products with no folder here and folders with no icon.
- `harvested` is the date a product's files were last copied in; `generated` is the newest of those.

`site-doctor.py --check` fails when `index.json` names a missing file, when an image here is missing from `index.json`, or when anything but an image (other than this README and `index.json`) lands in the tree.

## Refreshing

`scripts/refresh-roundup.py` re-harvests from the sibling repos. It reads `C:\Users\estev\Projects` directly, so it runs on Este's Windows box only and refuses to run in CI.

```
python scripts/refresh-roundup.py                 # dry run: new / changed / gone per product
python scripts/refresh-roundup.py --apply         # copy new + changed images, rewrite index.json
python scripts/refresh-roundup.py --apply --prune # also delete images whose source is gone
python scripts/refresh-roundup.py --index-only    # rewrite index.json from this tree only (CI-safe)
```

What each product harvests (its clone, files and directories) is the `PRODUCTS` mapping at the top of the script; add a product there, not by copying files in by hand. After adding or removing anything here by hand, run `--index-only` or the doctor fails.

## Images only

Everything here is served publicly on 626labs.dev (the site has `.nojekyll`, so GitHub Pages serves the whole tree). Keep it to images. Store submission docs (listing copy, reviewer letters, release playbooks and runbooks) live in each app's own repo under `docs/store/`, never here: copies of them were removed 2026-10-03, because they described internal release process on the brand site and went stale against their originals.
