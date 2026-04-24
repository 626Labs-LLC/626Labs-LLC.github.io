# Changelog

All notable changes to the Birthday Bacon Trail widget. Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] — 2026-04-23

First shippable version of the widget. Embedded live on [626labs.dev/#play](https://626labs.dev/#play).

### Added

- Stripped-down Birthday Bacon Trail gameplay: pick today's birthday actor → pick a film → win if Bacon is in the cast, else pick a co-actor and loop. Six films max per round.
- Two-row "Your Path" trail breadcrumb with films on top, actors below, dashed connector. Ends on Kevin Bacon's portrait card on a won round.
- Paginated film picker (9 films per page, `popularity × log(voteCount + 1)` sort so zero-vote derivative entries sink below legitimate films).
- Paginated co-actor grid (9 per page).
- Search box on the film screen — case-insensitive substring match, clears on subject change.
- Trail-walked films and actors filtered out from future picks so the widget can't send a visitor in a loop.
- Result card with `--success` celebration for found, `--danger` for out-of-films. Banner line replaces the trail box in the top slot on the result screen.
- Edge-glow celebration animation on the widget perimeter for `found` state. 8-second one-shot cycling through cyan → magenta → success-green. Respects `prefers-reduced-motion`.
- Screen-reader live region announces each state transition.
- Daily shard pipeline ([`.github/workflows/refresh-bacon-shards.yml`](../../.github/workflows/refresh-bacon-shards.yml)): regenerates 366 birthday shards nightly from Firestore, content-diff commits only.
- CI build pipeline ([`.github/workflows/build-widget.yml`](../../.github/workflows/build-widget.yml)): typecheck + test + build + bundle-size gate (≤150 KB gz js, ≤20 KB gz css) on every push to widget source. Commits rebuilt bundle back to the hub.

### Security / Privacy

- Zero runtime Firestore traffic; widget reads only the nightly-regenerated static shards.
- Zero user-data collection (no cookies, no localStorage, no analytics, no accounts).
- TMDB API key baked client-side per TMDB's terms (read-only v3); rotatable via one CI secret swap.
- `npm audit --prod`: zero high/critical vulnerabilities as of ship.
- Dependency surface deliberately small: React 19 + ReactDOM + lucide-react. No runtime Firebase SDK.

### Metrics at ship

- `widget.js`: 66.88 KB gzipped (45% of 150 KB budget)
- `widget.css`: 3.06 KB gzipped (15% of 20 KB budget)
- 57 tests green (17 reducer, 5 service, 5 bacon-check, 30 component)
- First Contentful Paint on live hub: ~650 ms
- Widget interactive: ~530 ms post-DOMContentLoaded
- Accessibility: 0/7 interactive elements missing `aria-label`; focus ring visible; WCAG AA contrast passes on primary text

### Not yet

- Light-theme rendering (the `theme: 'light'` config option logs a warning and falls through to dark in v1).
- Multi-language support (English only, default TMDB locale).
- Bounded precomputed actor-movie-cast graph (deferred; would eliminate runtime TMDB calls but adds ~10-15 MB static asset).
- Kid-friendly content filter.
- Integration test suite (Playwright E2E deferred; manual QA covered by the Item 7 report).
