# Decisions: hub-img-sizes

## D1
- **Decision:** Mode unattended, base `origin/main`.
- **Why:** Local clock 21:43, inside the late window; the builder confirmed ("unattended please"). Checkout was on `main`, 0 behind, 0 ahead.
- **Alternative not taken:** Attended run in the working tree with a checkpoint.
- **Item:** run
- **How to reverse:** n/a; the run is local only.

## D2
- **Decision:** Missing files and URL srcs get no width/height attributes; no fetch at render time.
- **Why:** The renderer has never touched the network, and a missing file is already a site-doctor finding (dangling asset), not the renderer's to hide. `shots` already emits sizes only when the uploader metadata carries them.
- **Alternative not taken:** Failing the render on a missing image.
- **Item:** 1
- **How to reverse:** Raise in the helper instead of returning "".

## D3
- **Decision:** #249's "no page exercises the platforms block" half is dropped as stale; item 2 corrects the test comment instead.
- **Why:** `content/site.json` line 2551: the `rororo` pageSpec carries a `platforms` block, so every render exercises it. The review's claim came from the Sanduhr diff alone.
- **Alternative not taken:** A fixture page for the block.
- **Item:** 2
- **How to reverse:** Remove the block from rororo and revisit.

## D4
- **Decision:** Close-out gates ran as the repo's own stack (render-product-pages, render-hub and render-plugin-pages `--check`, `pytest tests/`, `site-doctor --check`) instead of the vibe-test and vibe-sec gates.
- **Why:** Both are Claude skills with no CLI on this box, so they are not runnable inside an unattended loop; the reference names that case as an environmental fallback.
- **Alternative not taken:** Treating the absent gates as a finding.
- **Item:** run close-out
- **How to reverse:** Run `/vibe-test:gate` and `/vibe-sec:gate` on `cart/hub-img-sizes` in an attended session.

## D5
- **Decision:** `_shot` gained a `product` argument and `build()` threads `_root` into the product dict, beside the existing `_content`, so the block functions keep their `(b, product)` signature; a product with no `productPage` sizes against the repo root.
- **Why:** The worker's call. A module-level "current page" would have been shorter but hidden; the product dict already carries render context.
- **Alternative not taken:** A module global set per page.
- **Item:** 1
- **How to reverse:** Replace `_size`'s lookup; the five call sites stay.
