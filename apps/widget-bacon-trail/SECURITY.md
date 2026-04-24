# Security

## Posture

The Birthday Bacon Trail widget is designed to leak nothing. Two deliberate architectural choices uphold that:

1. **Zero user-data collection at runtime.** The widget does not write to Firestore, does not set cookies, does not use `localStorage` or `sessionStorage`, and does not issue any analytics beacons. No PII touches the wire; there is no wire that would receive it.
2. **Zero Firestore traffic at runtime.** The widget reads only the public static shard at `/widget-bacon-trail/data/birthdays/MM-DD.json`, which is regenerated nightly by a server-side GitHub Action. Firestore credentials exist only in the Action's runtime environment, never in the widget bundle.

## External calls the widget makes

1. **Shard fetch**: `GET /widget-bacon-trail/data/birthdays/{MM-DD}.json` from the same origin as the embedding page. Static JSON; cacheable; public.
2. **TMDB `GET /person/{id}/movie_credits`**: triggered only when a visitor picks an actor.
3. **TMDB `GET /movie/{id}/credits`**: triggered only when a visitor picks a film.
4. **TMDB image CDN (`image.tmdb.org`)**: for actor and movie posters as they render.

No POST requests. No authenticated requests (TMDB v3 accepts an API key as a query param; see below). Every outbound origin is explicit and public.

## Secrets in the widget bundle

The built `widget.js` contains a single baked value: `VITE_TMDB_API_KEY`, a TMDB v3 read-only API key. TMDB's [terms of use](https://www.themoviedb.org/documentation/api/terms-of-use) explicitly permit client-side distribution of v3 read-only keys. The key:

- Cannot mutate any TMDB data.
- Is rate-limited per requesting IP, not per key.
- Is rotatable by Este via [TMDB settings](https://www.themoviedb.org/settings/api); rotation is a one-secret swap + one CI rebuild.

If a TMDB key is ever suspected compromised:

1. Rotate the key in TMDB settings.
2. Update the `VITE_TMDB_API_KEY` secret in the `626Labs-LLC/626Labs-LLC.github.io` repo.
3. Trigger the `build-widget.yml` workflow (any push to `apps/widget-bacon-trail/src/` or manual dispatch) to rebuild the bundle with the new key.

## Secrets outside the widget bundle

- `FIREBASE_SA_JSON` — Firebase service account for the `guestbuzz-cineperks` project, scoped to `Cloud Datastore User` (read-only). Used only by the nightly shard-refresh Action. Never baked into the widget bundle. Rotate via Firebase console → Service accounts → new key, then update the GitHub secret.

Both secrets live in GitHub Actions repository secrets and are never printed to logs (the workflows echo presence checks without surfacing contents).

## Content Security Policy

The hub (`626labs.dev`) does not currently set a CSP. If one is ever added, it needs to permit:

- `connect-src`: `https://api.themoviedb.org`, plus the hub's own origin for the shard fetch.
- `img-src`: `https://image.tmdb.org`, plus the hub's own origin.
- `script-src`: the hub's own origin (widget script is self-hosted).

## Reporting a vulnerability

Email **estevan.hernandez@gmail.com** with the subject line `SECURITY — widget-bacon-trail`. Please include:

- A description of the vulnerability and its impact.
- Steps to reproduce.
- Any suggested remediation.

We'll respond within 5 business days. Responsible disclosure is welcomed — please don't file the issue publicly before we've had a chance to respond.

## Threat model snapshot

| Threat | Exposure |
|---|---|
| PII exfiltration | None — widget collects no PII |
| Session hijacking | None — widget has no session |
| XSS via user input | None — widget has no user input fields that render unescaped |
| CSRF | None — no authenticated state-changing requests |
| TMDB key abuse | Read-only scope; rate-limited per IP; rotatable |
| Firestore credential abuse | Server-side only; scoped to read-only Cloud Datastore User on one project |
| Supply-chain attack on dependencies | Mitigated by `npm audit --prod` gate + small dep tree (react, react-dom, lucide-react — no runtime Firebase) |

## Dependencies

Runtime dependencies are intentionally minimal:

- `react@^19.2.1`
- `react-dom@^19.2.1`
- `lucide-react@^0.555.0`

No runtime Firebase SDK, no axios, no `node-fetch`. The build toolchain has more (Vite, TypeScript, vitest, Tailwind 4) but none ships in the bundle served to visitors.

Audit run via `npm audit --prod`. Results documented in the [CHANGELOG](./CHANGELOG.md).
