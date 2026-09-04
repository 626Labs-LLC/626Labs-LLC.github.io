# October needs — Play in the nav, the CRT off every page, the imprint link, the reading-dress gate

**Date:** 2026-09-04
**Status:** Approved direction (Este: "let's finish off the list of needs and make sure we have removed the crt from everything, make sure the Play area is represented on the top bar").
**Branch:** `feat/october-needs` off `main` (`d4244e7`, the Slate Broadsheet merged and queued).
**Deadline:** merged before 2026-10-01 09:00 UTC so the first real rotation carries it.

## The four pieces

**1. Play in the top bar.** The nav is theme-owned shell markup, not renderer output. Both `themes/slate-broadsheet/archetypes/home.html` and `themes/phosphor-blueprint/archetypes/home.html` list Work, Plugins, Thinking, Field Notes, Lab, About, Sponsor, Contact. Add `Play` linking `#play` after Lab in the header nav and in the footer nav of both shells. Phosphor Blueprint is live, so its change re-renders `index.html` today; that is intended — the section exists on the live site and is unreachable from its own nav.

**2. The CRT off the three pages that never took a theme.** `404.html`, `bacon-trail/index.html` and `sanduhr/index.html` still carry private `--pb-*` blocks and paint their own field, grid, scanlines and bloom. Under any future theme they stay Phosphor Blueprint forever. Convert them the way the six bespoke pages were converted in PR #96: delete the private token block, add the renderer-owned `theme-css` zone (`THEME_CSS_HREFS` + `THEME_CSS_ONLY_PAGES`), link the theme's token file for their archetype (`product-tokens.css` for bacon-trail and sanduhr, `tokens.css` for 404), rewrite reads to contract names with `var(--pb-X, var(--contracted))` fallback chains where a treatment name is read, keep every layout rule in the page, and prove **true 0-pixel at 1440/768/390 versus `main`** with the committed `scripts/visual-diff.py` — including its hover channel. The 404 page's "structurally bare" ruling from M2a is narrowed: it stays structurally bare, it stops being a private copy of one theme.

**Residue stays until October.** The already-converted pages carry dead `.pb-scanlines` divs and CRT rules whose fallbacks resolve to transparent under slate. They are live and visible under Phosphor Blueprint until the 1st, so removing them now repaints September's site. That cleanup is a separate branch after the rotation, when the archive is frozen and nothing depends on them.

**3. A real "see all themes" link on the plugin pages.** `render_footer()` in `scripts/render-plugin-pages.py` owns the footer of the 15 generated pages, so no theme can put a link there. Emit an imprint line in that footer: `Theme: <name> · this site changes monthly · <a href="/themes.html">see all themes</a>`, reading `<name>` from the active theme's `theme.json` so it is right in every month. Then retire the generated-content imprints that were the workaround: `product.css`'s `footer .row::after`, `utility.css`'s `.footer-inner::after`, and the slate home shell's hardcoded "October 2026" becomes the theme name. One imprint per page, with a link, from one source of truth. This changes the 15 live pages under Phosphor Blueprint today by one footer line; intended.

**4. The doctor's reading-dress gap.** `_run_browser_checks_all` serves `about.html` bare for the reading archetype, so a theme's `reading.css` is never loaded in the browser phase and was verified for slate only by its builder's own harness. Make the browser phase inject the picker's `<link>` to the theme's `reading.css` after about's inline style — exactly what the easter-egg toggle does — so a reading dress that 404s a font, breaks layout, or leaves `.lnt-*` elements on browser defaults fails the gate. Add a test that fails when the injection is removed.

## Not in this branch, and why

- **Stripping dead CRT residue from converted pages** — repaints September; October's cleanup.
- **Generated brand rasters** — `scripts/export-brand.py` and `scripts/build-og-cards.py` bake Phosphor Blueprint's grid and bloom into banners, the Discord splash, the favicon and every Field Note's social card. Those are brand assets seen on X and Discord, not site pages. Whether they follow the monthly theme or stay the brand's launch look is Este's call, asked separately.
- **The `.wrap`/`.nav-inner` vocabulary ruling** from PR #97 — Este's call, asked separately.

## Gates

Everything PR #96, #97 and #115 built: `render-hub.py --check`, `render-plugin-pages.py --check`, `pytest`, `site-doctor.py --report`, `theme-doctor.py slate-broadsheet --browser --require-browser` AND `theme-doctor.py phosphor-blueprint --browser --require-browser` (both themes must pass; PB is live for three more weeks). `visual-diff.py main --widths 1440,390` reports findings on exactly: `index.html` (the Play link), the 15 plugin pages (the imprint line), and nothing else — the three converted pages must be 0-pixel. Then the rotation-morning simulation from PR #115's final review, re-run with slate active, every gate green.
