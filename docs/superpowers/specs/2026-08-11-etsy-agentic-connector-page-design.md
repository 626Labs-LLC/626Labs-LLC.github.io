# 626Labs Etsy Agentic Connector — product page

**Date:** 2026-08-11
**Branch:** `feat/etsy-connector-page`
**URL:** `https://626labs.dev/etsy-mcp.html`

A hand-authored product page for a connector that is in private testing, not
generally available. Every claim on it has to be true on the day it ships, and
has to stay true while the product is still moving. That constraint decides
most of what follows: no repo link (there is no public repo), no badges, no
screenshots, no availability CTA, and the two documentation URLs render as text
rather than as links, because they 404 today.

## Shape

A root-level `.html` file dressed by the active theme, following
`conundrum.html` and `mod-launcher-games.html` — not a generated page.
`render-plugin-pages.py` owns 15 pages built from `content/plugin-pages.json`,
and every one is a Claude Code plugin with a repo, a release, and install
copy. This product is none of those.

The page links the active theme's `archetypes/product-tokens.css` through a
renderer-owned `SITE_JSON:theme-css` zone and keeps its own layout in an inline
`<style>`. That is the split the repo already enforces: the token half is
vocabulary every page wants, the dress half (`archetypes/product.css`) is
element rules written for the generated templates' markup, and a hand-authored
page that links it inherits rules it was never designed for.

Two constraints on that inline CSS, both pinned by tests in
`tests/test_render_hub.py` once the page joins `CONVERTED_PAGES`:

1. Every `var()` read is in `archetypes.REQUIRED_TOKENS`, declared by the page
   itself, or carries a fallback. A theme that satisfies the contract exactly
   and ships no treatment must not strand the page.
2. The page never redefines a contracted token. Page-local aliases
   (`--page-hairline: var(--pb-hairline, var(--border-1))`) are how the
   Phosphor Blueprint treatment reaches it without putting a copy of `--bg-0`
   somewhere the rotation cannot reach.

## Content

Five sections. The hero one-liner, the trust bullets, and the status paragraph
are the user's copy, used close to verbatim — they are the parts most likely to
be read by someone deciding whether to trust the thing with their shop.

1. **Hero.** Title, the one-liner as the dek, and a mono status line:
   private testing, read-only, not yet publicly available.
2. **What it does.** Etsy Open API v3, any MCP client, Claude as the reference
   client. Capabilities: shop snapshots, listing performance, orders, reviews,
   day-over-day movers computed from snapshot history. Closes on the page's one
   hard callout: zero tools modify your Etsy shop.
3. **Trust.** The core of the page, and the reason it exists. Five rows, each a
   plain claim: sign-in happens only on etsy.com's own consent screen; the four
   read-only scopes named in mono (`listings_r`, `shops_r`, `transactions_r`,
   `feedback_r`) with a one-line gloss each; tokens encrypted at rest with
   AES-256-GCM; full CSV export anytime, deletion immediate on request, and
   automatic purge 30 days after disconnect; no scraping, official API plus
   optional seller-provided CSV imports labeled by source.
4. **Status.** In active development, private testing with Conundrum by Este,
   public availability planned after Etsy Commercial Access and the Anthropic
   Connectors Directory. Links to `conundrum.html`, a sibling page.
5. **Footer block.** `estevan@626labs.dev`, then the privacy and docs URLs as
   mono text labeled "coming online with the beta."

Nav: brand to `index.html`, then Products, Field Notes, and a CTA anchoring to
the trust section. There is nothing to download, so the CTA points at the thing
a visitor actually came to evaluate.

`og:image` falls back to the brand banner. No connector artwork exists, and a
borrowed thumbnail would misrepresent the product.

## Wiring

| File | Edit | Why it is required |
|---|---|---|
| `etsy-mcp.html` | new | the page |
| `content/page-archetypes.json` | `"etsy-mcp.html": "product"` | `archetypes.validate()` errors on an unmapped public page |
| `scripts/render-hub.py` | `ETSY_MCP_HTML` + `THEME_CSS_HREFS` + `THEME_CSS_ONLY_PAGES` | a test pins those two to exact set equality in both directions |
| `scripts/render-hub.py` | `PRODUCT_SIGILS["etsy-mcp"]` | unknown ids silently inherit vibe-cartographer's map sigil |
| `scripts/theme-doctor.py` | `BROWSER_CHECK_LIVE_PAGES` + the gate docstring's counts | `test_the_browser_gate_opens_every_previewable_theme_css_page` asserts this equals the derived previewable set |
| `tests/test_theme_doctor.py` | the literal pin at the page tuple | hand-written literal, asserted verbatim |
| `tests/test_render_hub.py` | `CONVERTED_PAGES` | puts the page under both rotation-safety tests |
| `content/site.json` | product entry | the homepage card |

The CI workflows need no edit. `rebuild-hub.yml` and `rotate-theme.yml` derive
their page lists from `render-hub.py --list-renderer-owned-pages`, and a test
fails if either hand-names a page. `sitemap.xml` derives from the root `*.html`
files on disk.

### Homepage card

`id: etsy-mcp`, `status: "wip"`, `claudeCode: false`, `repo: null`, tags
`[MCP, Etsy, read-only, In development]` with the last on the `wip` tone.
`productPage: "etsy-mcp.html"`, label "How it works". Last in the array, after
`pod-pipeline`, so a not-yet-available card does not push live products down.

This is the first `status: "wip"` product and the first use of the `wip` tag
tone. Both paths exist in the renderer (`article.product.wip` at 0.85 opacity,
`.tag.wip` in warn amber) and neither has ever been exercised. `productPage`
takes precedence over the wip branch in `render_product_foot`, so the card's
foot link points at the page rather than at a "Framework doc" repo link that
would 404.

No derived fact moves. `claude_plugins`, `claude_plugins_wip`, and
`live_plugin_names` all filter on `claudeCode is True`; `windows_native_count`
filters on a Windows tag. This entry sets neither.

## Verification

`render-hub.py` then `--check`; `theme-doctor.py phosphor-blueprint --browser`;
`site-doctor.py --report`; `pytest tests/ -q`.

The browser gate is the one that matters here — adding the page to
`BROWSER_CHECK_LIVE_PAGES` means the unattended monthly rotation now opens it
at 1440/768/390px and fails the rotation if it scrolls sideways or logs a
console error. That is the point: a page nothing opens is a page the rotation
can silently break.

After merge: request indexing for `https://626labs.dev/etsy-mcp.html` in Google
Search Console. Sitemap resubmission is not needed.

## Not doing

- No public repo link. There is none, and a dead link on a trust page is worse
  than an absent one.
- No `assets/` artwork, no OG card, no screenshots.
- No lychee exclusion for `etsy-agentic-connector.web.app`. An exclusion added
  now to cover a URL that is deliberately dead would go on hiding real breakage
  after the beta ships.
- No Field Note. The product is not announced yet.
