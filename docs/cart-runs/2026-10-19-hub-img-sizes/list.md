# Run List: hub-img-sizes

- [ ] **1. Generated product pages emit img width and height for every local image**
  Spec ref: `626Labs-LLC/626Labs-LLC.github.io#248 > body; dashboard task-1792462985402-b6ng54vqw`
  What to build: In `scripts/render-product-pages.py`, a helper that resolves an image src (relative to the page's output directory, or root-relative from the repo root) and returns `' width="W" height="H"'` from Pillow, or "" when the file is missing or the src is a URL. Apply it at the five sites that emit an `<img>` without sizes: hero logo, hero app icon, `block_showcase`, `_shot` (gallery and wide), and the merch image in the shop block. `shots` keeps its uploader-metadata path and uses the helper only as a fallback. CSS untouched. Re-render all pages. Size M.
  Acceptance: Done when every `<img ` in every file `render-product-pages.py --list-outputs` names carries both `width=` and `height=` and the numbers equal the file's pixel size; `render-product-pages.py --check` is clean after the render; a test in `tests/test_render_product_pages.py` walks every generated page and asserts it, plus a unit test for the resolver (relative, root-relative, missing, URL).
  Verify: Run `python scripts/render-product-pages.py && python scripts/render-product-pages.py --check && python -m pytest tests/test_render_product_pages.py tests/test_render_hub.py -q -p no:cacheprovider --basetemp=<outside the tree>` and confirm all pass; then `python -m pytest tests/ -q` and `python scripts/site-doctor.py --check`.
  Stop class: go

- [ ] **2. Pin the Sanduhr gallery exactly and correct the platforms test comment**
  Spec ref: `626Labs-LLC/626Labs-LLC.github.io#249 > items 1 and 2; dashboard task-1792462985403-rptuwsszf`
  What to build: In `tests/test_render_product_pages.py`, replace the `>= 11` floor in the Sanduhr Mac page test with an assertion derived from the pageSpec: count the gallery items plus wide shots plus showcase images in `products[sanduhr].pageSpec` and assert the rendered page has exactly that many `gallery-shot` / `showcase-frame` elements, each src appearing once. Correct the comment on `test_a_badge_kind_must_be_known`: the block is still live on the rororo page (`content/site.json` `rororo` pageSpec), so the direct call pins the badge check, not the block's only coverage. Size S.
  Acceptance: Done when the test fails if a gallery item is duplicated or dropped from the render (verify by a temporary in-test mutation or reasoning on the assertion), passes on the current page, and the comment names rororo as the live user of the platforms block.
  Verify: Run `python -m pytest tests/test_render_product_pages.py -q -p no:cacheprovider --basetemp=<outside the tree>` and confirm it passes.
  Stop class: go
