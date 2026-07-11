# Conundrum by Este — site feature design

**Date:** 2026-07-11
**Status:** Approved design, pre-implementation
**Scope:** Feature the Conundrum by Este Etsy shop on 626labs.dev — product card + dedicated page — with the POD pipeline story built in and a one-field upgrade path for when the pipeline repo goes public.

## Context

Conundrum by Este x 626Labs is the print-on-demand merch shop (Etsy, fulfilled via
Printify, shop id 26981185). The engine behind it is the POD pipeline
(`Projects/POD_Pipeline`): Gemini art generation → AI-slop QA → background removal →
PIL text compositing → variant matrix → Printify upload → Etsy publish. The pipeline
is being sanitized for public release in parallel with this work.

The site has zero merch presence today. Conundrum is its own merch brand
(streetwear-meme voice, loud, iykyk) with 626Labs as the parent house — the brand
split is documented in POD_Pipeline's CLAUDE.md and is load-bearing for this design.

## Decisions (made in brainstorming, 2026-07-11)

1. **Surface:** product card in the index grid + dedicated `conundrum.html` page
   (the rororo.html precedent for a standalone product page).
2. **Branding:** PB shell, Conundrum core. The page keeps the site's Phosphor
   Blueprint chrome (nav, grid, dark field, scanlines); the product gallery lifts
   crisp above the scanline overlay (the Bacon Trail crisp-lift pattern) and merch
   copy speaks Conundrum's streetwear voice. The pipeline section returns to 626
   builder-to-builder voice.
3. **Gallery data:** curated picks in site.json (6–9 hero products). No live
   Printify/Etsy sync — no new secrets in this repo's CI.
4. **Sequencing:** page ships now, repo link lands later as a one-field edit when
   sanitization completes. Two announce beats.
5. **Scope amendment:** GoatCounter outbound-click events on Etsy links are IN
   scope (~10 lines, no new services). Everything else in Out of Scope stays out.

## Page structure — conundrum.html

Hand-authored static page, PB treatment, five beats:

1. **Nav** — standard site nav with local `::after` scanlines at z:70
   (established crisp-lift companion pattern).
2. **Hero** — Conundrum logo (source: `POD_Pipeline/conundrum_logo_transparent.png`),
   "Conundrum by Este × 626 Labs" lockup, one-line thesis in Conundrum voice,
   primary CTA to the Etsy shop.
3. **Product gallery** *(renderer-owned zone `conundrum-products`)* — curated
   product cards: mockup image, title, price, Etsy listing link. Crisp-lifted to
   z:61 above the scanline overlay (60) so product photography plays clean.
   Conundrum voice in this zone.
4. **"The machine behind it"** — hand-authored editorial telling the nine-stage
   pipeline story, 626 voice, with load-bearing rules as pull-quotes ("the model
   never writes the words"). Contains renderer-owned zone `conundrum-repo`: a
   "Read the code" CTA that renders ONLY when `conundrum.repoUrl` is set —
   collapses to nothing while null (stories-zone pattern). No "coming soon"
   placeholder ever ships.
5. **Footer** — standard, including the sitewide GoatCounter snippet.

## Data schema — site.json

New top-level `conundrum` key:

```json
"conundrum": {
  "etsyUrl": "https://www.etsy.com/shop/<confirmed-at-build>",
  "repoUrl": null,
  "products": [
    {
      "title": "Fire & Ice Spider Monster Joggers",
      "price": "$46.99",
      "image": "assets/screenshots/conundrum/fire-ice-joggers.jpg",
      "etsyListing": "https://www.etsy.com/listing/…"
    }
  ]
}
```

- `etsyUrl`: shop-level URL. Not present in pipeline data — derive from a live
  listing page at build time and confirm with Este before merge.
- `repoUrl`: null until the public pipeline repo ships; then set → rebuild → the
  repo CTA appears. Phase 2 is this one field.
- `products[]`: curated by hand (Remy handoff or admin edit). Images live under
  `assets/screenshots/conundrum/` so the admin uploader stays compatible.

## Grid card — index.html (via site.json)

One new `products[]` entry: id `conundrum`, status `live`,
`productPage: "conundrum.html"`, `productPageLabel: "Visit the shop"`. Card art
from the Conundrum logo cut, placed under `assets/` per product-art convention
(NOT `assets/brand/` — script-owned). Placement near the consumer products
(rororo, mod-launcher) rather than the dev-tool cluster.

## Renderer

One new function in `scripts/render-hub.py` (`render_conundrum()`), filling the
two zones in conundrum.html from the `conundrum` key, wired into the same build
path as index.html. Consequences that come free:

- `render-hub.py --check` covers zone drift.
- `rebuild-hub.yml` already fires on site.json pushes.
- `render_sitemap()` picks up conundrum.html from disk — zero sitemap work.

## Analytics (scope amendment)

- Pageviews: free via the standard GoatCounter snippet (part of the page pattern).
- Outbound Etsy clicks: GoatCounter event tracking
  (`goatcounter.count({path: 'etsy-click/<slug>', event: true})`) bound to gallery
  links and the hero CTA. ~10 lines, no new services, no secrets. Yields
  click-through-per-product — the actionable number.
- Sales/revenue stays in Etsy's own dashboard. Out of scope (requires Etsy API
  app approval).

## Copy rules

- **No counts baked into copy** ("9 products", "14 socks") — the catalog churns
  with Etsy renewal-fee cuts; stale numbers on a shop page read worse than none.
- Conundrum voice in hero + gallery; 626 voice in the machine section.
- Listing titles quoted verbatim from Etsy where shown.
- No emoji (site surface).

## Guardrails and verification

- **site-doctor:** dangling-asset check covers gallery image paths automatically.
  No new facts-registry entries (copy is count-free).
- **link-check (lychee, weekly):** already checks external links in all HTML and
  opens issues on breakage — this is the dead-listing detector, free. Caveat:
  Etsy bot-detection may 403 lychee; if so, add an exclude and accept the
  coverage loss, reassess.
- **Pre-PR verification:** local render + `site-doctor --report` (NOT bare
  `--check`, which exits silently), then Playwright pass: crisp-lift stacking
  (gallery z:61, nav z:70), mobile width, every Etsy link resolving, click
  events firing in the GoatCounter network call.

## Phase 2 (when pipeline sanitization ships)

1. Set `conundrum.repoUrl` in site.json, push — repo CTA appears via rebuild-hub.
2. Optional: Field Note build story about the pipeline. Decided then, not
   designed now.

## Out of scope, on purpose

- Printify/Etsy API automation (secrets crossing + image hosting; dead-link risk
  already covered by lychee).
- A Conundrum sub-brand design system (treatment-exploration-sized project;
  "PB shell, Conundrum core" delivers the brand feel).
- Per-product pages (thin duplicates of the Etsy listings, which are canonical).
- Purchase/revenue analytics on-site (Etsy API app approval required).

## Inputs needed before/at build

- Etsy shop URL (derive from live listing, confirm with Este).
- Curated product picks: 6–9 heroes. Reassessment keepers are the starting
  slate: Fire & Ice Spider Monster Joggers, Watercolor x Neon Spider Monster
  Joggers, Fire & Ice Spider Monster Shorts, the 8 meme socks (subset). Final
  slate confirmed with Este at implementation.
- Product mockup images exported from Printify (manual pull, committed to
  `assets/screenshots/conundrum/`).
- Conundrum logo cut copied from POD_Pipeline into `assets/`.
