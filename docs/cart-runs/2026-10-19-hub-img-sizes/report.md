# Run Report: hub-img-sizes

2 merged, 0 held, 0 parked, 0 stopped.

## Ready to push
- **Integration branch:** `cart/hub-img-sizes` (base `ed9d380`, origin/main at run start, 0 behind)
- **Commits:** 2 item commits, each followed by its local merge:
  - `13d0ca1` feat(render): generated pages emit img width and height
  - `510a669` test(render): pin the Sanduhr gallery to its pageSpec; the platforms block is live on rororo
- **Checks:** item 1: `render-product-pages --check` and `render-hub --check` clean, `pytest tests/` 802 passed, `site-doctor --check` exit 0, and disabling `_size` turned the new walk test red. Item 2: `pytest tests/test_render_product_pages.py` 69 passed; a dropped shot and an extra frame both fail the new assertion. Close-out on the integration branch: all three renderers' `--check` clean, 802 passed, site-doctor exit 0. vibe-test and vibe-sec gates substituted per D4.

To push and open the PR:
```bash
git push -u origin cart/hub-img-sizes
gh pr create --base main --head cart/hub-img-sizes --title "feat(render): generated pages emit img width and height; Sanduhr gallery pinned to its pageSpec" --body "Closes #248, closes #249."
```
Pushing waits for your say-so. Tell Cart "push it".

What changed for a visitor: six generated pages (conundrum, rbx15, rororo, rtclickpng, sanduhr, sanduhr/windows) now reserve every image's box before it loads; the other eight had no local images at the five sites. No CSS change.

## Waiting on you
None.

## Parked
None.

## Stopped
None.

## Decisions to skim
Full ledger: `decisions.md`. Highest stakes:
- D2: a missing or remote image gets no size attributes; nothing is fetched at render time.
- D3: #249's platforms half was stale (rororo still renders the block); the test comment was corrected instead.
- D4: vibe-test and vibe-sec gates substituted with the repo's own stack.

## Left untouched
None. The builder's tree was clean at run start and is on `main`, even with origin.
