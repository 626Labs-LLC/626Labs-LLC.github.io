# Privacy

The Birthday Bacon Trail widget collects no user data. Not a single byte.

## What we don't do

- **No analytics.** No Google Analytics, no Plausible, no Mixpanel, no first-party beacon, no server-side log that captures visitor identity.
- **No cookies.** The widget sets zero cookies. It reads zero cookies.
- **No browser storage.** `localStorage`, `sessionStorage`, `IndexedDB`, `WebSQL` — all untouched.
- **No fingerprinting.** No device enumeration, no canvas tricks, no font probes.
- **No accounts.** Visitors don't sign up, sign in, identify themselves, or supply any personal information.
- **No tracking pixels.** No iframe-based trackers, no third-party scripts beyond TMDB's image CDN (which serves posters but doesn't correlate visitors across sessions).

## What requests happen

Rendering the widget triggers these network calls from the visitor's browser:

| Call | To | Purpose | Carries visitor data? |
|---|---|---|---|
| `GET /widget-bacon-trail/widget.{js,css}` | 626labs.dev (GitHub Pages) | Load the widget bundle | No |
| `GET /widget-bacon-trail/data/birthdays/{MM-DD}.json` | 626labs.dev (GitHub Pages) | Load today's birthday actors | No |
| `GET https://api.themoviedb.org/3/person/{id}/movie_credits` | TMDB | Fetch a picked actor's filmography | No — request carries the widget's read-only API key only |
| `GET https://api.themoviedb.org/3/movie/{id}/credits` | TMDB | Fetch a picked movie's cast | No |
| `GET https://image.tmdb.org/t/p/w185/*` | TMDB image CDN | Render actor / poster thumbnails | No |

TMDB sees the visitor's IP address (because TCP connections require one) and a `User-Agent` header — unavoidable baseline of every web request. It does not receive any data identifying who the visitor is, what page they came from inside 626labs.dev (no `Referer` correlation by us), or what other sessions they've had.

## Data retention

Zero. We store nothing about visitors — whether on the client or on any server.

## If this ever changes

Any future feature that collects visitor data will:

1. Get a privacy policy update documenting what, why, and how long.
2. Ship behind an explicit opt-in (not opt-out).
3. Respect `Do Not Track` and `prefers-reduced-motion` signals.

As of the current version ([see CHANGELOG](./CHANGELOG.md)), no such feature exists.

## Contact

Questions about this policy: **estevan.hernandez@gmail.com**.
