# Asset roundup — raw harvest from the estate

Harvested 2026-07-08 from every personal repo under `Projects\`. One folder per app/plugin, curated to canonical brand assets: primary icons/logos (largest variant only, MSIX scale-armies skipped), store images, and organized screenshot folders.

This is **raw material**, not finished exports. Curated/final brand assets live in `assets/brand/apps/` and `assets/brand/plugins/` using the `<slug>-<kind>-<dims>.png` convention.

## Provenance notes

- Sources are each repo's own assets (`docs/store-assets/`, `windows/msix/Images/`, `public/icons/`, etc.). Filenames preserved except where renamed to disambiguate (QuizShow per-app favicons, SnipSnap `logo-1240.png` = Square310x310 scale-400).
- Duplicate clones: harvested from kebab-case canonicals only (`Cleanup-Ranger`, `Safety_Assistant`, `Chef-I-s`).
- Excluded on purpose: coverage-report favicons, `_old`/`.old` copies, git worktrees, older 626Labs dashboard siblings, `Safety Assistant/data/incoming/` (app data, not marketing), loose unorganized root screenshots (Boutique, attached_assets).
- Excluded pending tenant call: PriceScout*, theatre-operations-platform, CompReport (work-adjacent).

## Images only

Everything here is served publicly on 626labs.dev (the site has `.nojekyll`, so GitHub Pages serves the whole tree). Keep it to images. Store submission docs (listing copy, reviewer letters, release playbooks and runbooks) live in each app's own repo under `docs/store/`, never here: copies of them were removed 2026-10-03, because they described internal release process on the brand site and went stale against their originals.
