# Supported-games page (mod-launcher-games.html) — design

**Date:** 2026-07-08
**Status:** Spec (approved in-conversation). Hub-repo feature; consumes the 626-game-manifest feed's public JSON. Small — one page + one site.json touch.

## The problem

The feed publishes a public, self-updating supported-games surface (`supported-games.json`, CORS-open raw URL; 150 games and growing), but 626labs.dev has nowhere to show it. The launcher's product entry exists in `content/site.json` (`products[20]`, id `mod-launcher`) with no dedicated page — while the RoRoRo product has the established pattern this needs: a root sub-page that client-renders from JSON (`rororo-plugins.html`).

## Decisions

1. **A dedicated root page, `mod-launcher-games.html`** — the rororo-plugins precedent, applied to the launcher.
2. **Client-side fetch of the feed's raw URL** (`https://raw.githubusercontent.com/estevanhernandez-stack-ed/626-game-manifest/main/supported-games.json`) — the page self-updates as curation lands; no site rebuild, no data job, no new secrets.
3. **Repo conventions govern:** hand-written HTML + vanilla JS + inline CSS, no framework, no build step. Brand tokens from the design skill (`colors_and_type.css` as source): navy `#0f1f31` field, cyan `#17d4fa` + magenta `#f22f89` always paired, Space Grotesk display / Inter body / JetBrains Mono meta, uppercase meta labels +0.12em tracking. Voice: builder-to-builder, sentence case, no emoji, no corporate speak. Mirror `rororo-plugins.html`'s head/font wiring (local `/fonts` @font-faces).

## Page anatomy (top to bottom)

1. **Header** — site-consistent nav back to the hub (mirror rororo-plugins' header), page title "Supported games", the launcher's one-line identity + links: GitHub releases, Microsoft Store listing.
2. **Counts hero** — rendered from `counts`: "**150 games** — 104 engine-curated · 46 Nexus-only", plus the generated-date in mono meta ("feed updated 2026-07-08"). Native text in brand type — no shields iframe on our own page.
3. **Featured rail** — games with `featured`, sorted by rank: cover-card grid (portrait 2:3), name + engine chip under each.
4. **All games** — two tier sections:
   - *Engine-curated* — "quick-pick setup: the launcher knows the engine and mod folder." Rows: name · engine chip · Steam link · Nexus link.
   - *Nexus-only* — "identified on Nexus; engine detected from the game folder at runtime." Rows: name · Steam link · Nexus link.
   Sorted by name within sections (the JSON arrives sorted — preserve its order).
5. **Footer CTA** — "Missing a game? Request it" → the feed repo's game-request issue template; "raw data for your own tools" → the JSON URL; standard site footer.

## Data contract

`supported-games.json` schemaVersion **1**: `{ schemaVersion, generatedUtc, counts{total,engineCurated,nexusOnly}, games[{ id, name, tier, steamAppId?, steamUrl?, engine?, modPath?, featured?, nexusUrl? }] }` — optional fields **omitted** (not null); check presence. The page tolerates unknown extra fields (additive changes don't bump the schema) and hard-checks `schemaVersion === 1` (mismatch → the failure state below, never a broken render).

## Covers (client-side reality)

- `<img loading="lazy">` straight off Steam's public CDN: `https://cdn.cloudflare.steamstatic.com/steam/apps/<steamAppId>/library_600x900.jpg`. Images need no CORS — this works in-browser for nearly all games.
- The launcher's store-API fallback for brand-new titles is **not** available client-side (that API doesn't send CORS headers) — so `onerror` (and missing `steamAppId`) swaps a **branded placeholder tile**: game initial in Space Grotesk on the navy field with the cyan/magenta pairing — the same placeholder language the launcher itself uses. Never a broken-image glyph.

## Error handling

- Fetch failure / non-200 / schema mismatch → hide the dynamic sections, show one quiet line: "The live list is momentarily unavailable — see the full list on GitHub." linking to the feed repo's `SUPPORTED-GAMES.md`. No infinite spinner; a small mono "loading" state only during fetch.
- Zero-game or missing-section edge cases degrade to empty sections without layout breakage.

## Wiring into the hub

- `content/site.json` `products[20]` (mod-launcher): add the page link the way the product schema expresses links (inspect the entry + a product that links to a sub-page — e.g. how RoRoRo's entry points at rororo-plugins; mirror exactly). Pushing site.json triggers `rebuild-hub.yml` → renderer updates `index.html`. **Never hand-edit inside `index.html`'s rendered zones.**
- The new page is static and outside every workflow's trigger paths — no CI changes.

## Testing / verification

- Open the page locally (file:// or a local static server) against the LIVE feed URL: counts render, featured rail ordered, covers load, a known CDN-404 title (DEATH STRANDING 2) shows the branded placeholder, tier sections + links correct, request-a-game link lands on the issue template.
- Simulate failure (temporarily bad URL) → the GitHub-fallback line renders.
- Mobile-width pass (the site is responsive; cards wrap, rows stack).
- `python3 scripts/render-hub.py --check` after the site.json touch (drift guard, per repo CI).

## Non-goals

- No search/filter on the page (the list is ~150 rows in two sections; YAGNI until it isn't).
- No client-side store-API cover fallback (CORS-blocked; placeholder is the honest answer).
- No screenshots/media per game, no per-game detail pages.
- No changes to the feed, the JSON schema, or the launcher.

## Success criteria

- 626labs.dev/mod-launcher-games.html renders the live list, on-brand, with zero rebuild coupling to the feed — a curation PR in the feed repo updates the page within a minute, untouched.
- The launcher product entry on the hub links to it; the page links back out to GitHub/Store/request-a-game.
- Graceful under every failure (feed down, cover 404, schema bump): honest fallbacks, never a broken surface.
