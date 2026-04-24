# Privacy

The Birthday Bacon Trail widget collects **no visitor data** — no identity, no session, no tracking. As of v0.2.0, it does record a single anonymous aggregate counter per completed round. Details below.

## What the widget does collect (v0.2.0+)

When a round ends, the widget sends **one anonymous POST** to a Firebase Cloud Function containing exactly two fields:

```json
{ "outcome": "found" | "out-of-films", "filmCount": 1 }
```

- `outcome` — whether the player found Kevin Bacon or hit the 6-film cap.
- `filmCount` — how many films were walked before the round ended (integer 1–6).

There is **no visitor ID** attached. No cookie, no session, no browser fingerprint, no Referer correlation by us. The payload is validated server-side — any extra fields are rejected with a 400 so nothing can piggy-back a visitor identifier through this endpoint even accidentally.

The function increments a **single shared document** in Firestore (`stats/play-counters`) using atomic `FieldValue.increment(1)`:

- `totalPlayed`
- `totalFound` or `totalOutOfFilms` (depending on outcome)
- `wins1` through `wins6` (distribution across win-length)

The widget then reads a nightly static snapshot of those counters (`/widget-bacon-trail/data/stats.json`) to display lifetime totals like *"5,432 rounds · 1,876 found Bacon"* to future visitors. That snapshot is regenerated once per day by the existing GitHub Action and committed as a static file — no per-request read of Firestore happens at runtime.

## What we don't do

- **No analytics.** No Google Analytics, Plausible, Mixpanel, Segment, or first-party per-user beacon.
- **No cookies.** Zero `Set-Cookie` headers. Zero cookie reads.
- **No browser storage.** `localStorage`, `sessionStorage`, `IndexedDB` — all untouched.
- **No fingerprinting.** No device enumeration, canvas, font probing.
- **No accounts.** Visitors don't identify themselves in any way.
- **No tracking pixels.** No third-party scripts beyond TMDB's image CDN.
- **No IP logging by us.** Google Cloud Functions captures connecting IP at infrastructure level (unavoidable baseline of all HTTP), but we never read it, correlate it, or persist it.

## What requests happen

Rendering the widget triggers these network calls from the visitor's browser:

| Call | To | Purpose | Carries visitor data? |
|---|---|---|---|
| `GET /widget-bacon-trail/widget.{js,css}` | 626labs.dev (GitHub Pages) | Load the widget bundle | No |
| `GET /widget-bacon-trail/data/birthdays/{MM-DD}.json` | 626labs.dev (GitHub Pages) | Load today's birthday actors | No |
| `GET /widget-bacon-trail/data/stats.json` | 626labs.dev (GitHub Pages) | Read lifetime-counter snapshot | No |
| `GET https://api.themoviedb.org/3/person/{id}/movie_credits` | TMDB | Fetch a picked actor's filmography | No — request carries the widget's read-only API key only |
| `GET https://api.themoviedb.org/3/movie/{id}/credits` | TMDB | Fetch a picked movie's cast | No |
| `GET https://image.tmdb.org/t/p/w185/*` | TMDB image CDN | Render actor / poster thumbnails | No |
| `POST https://…/logPlay` | Firebase Cloud Functions | Record `{outcome, filmCount}` on round end | **No identity** — literally those two numeric/enum fields only |

TMDB and Google Cloud see the visitor's IP address (because TCP connections require one) and a `User-Agent` header — unavoidable baseline of every web request. Neither service is configured by us to log or correlate; they each have their own privacy posture.

## Data retention

- **Per-visitor**: zero. We store nothing about visitors.
- **Aggregate counters**: indefinite. A single doc in Firestore accumulates totals forever. No per-round rows — just counters, so no per-round record exists that could be correlated back to any visitor even in principle.

## If this ever changes

Any future feature that collects more than the current anonymous aggregate will:

1. Update this document describing what, why, and how long.
2. Ship behind an explicit opt-in (not opt-out).
3. Respect `Do Not Track` and `prefers-reduced-motion` signals.

## Contact

Questions about this policy: **estevan.hernandez@gmail.com**.
