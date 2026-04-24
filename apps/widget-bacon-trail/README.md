# Birthday Bacon Trail — widget

An embeddable React widget that runs a stripped-down version of the Birthday Bacon Trail game. The visitor picks one of today's birthday actors, walks a movie-cast chain, and tries to find Kevin Bacon within six films. Built for a small card on [626labs.dev](https://626labs.dev/#play) and designed to be re-embeddable anywhere a script tag can run.

Full game lives at [`apps/bacon-trail/`](../../../QuizShow/apps/bacon-trail/) in the QuizShow monorepo. This widget is a compact fork optimized for portfolio placement — no accounts, no leaderboard, no writes.

---

## Embed (one-shot)

Drop three lines into any page:

```html
<link rel="stylesheet" href="/widget-bacon-trail/widget.css" />
<div id="bacon-widget"></div>
<script src="/widget-bacon-trail/widget.js" defer></script>
<script>
  window.addEventListener('DOMContentLoaded', function () {
    window.BaconTrailWidget.init({
      container: document.getElementById('bacon-widget'),
      ctaUrl: '/#work',
      ctaLabel: 'See the full suite →',
    });
  });
</script>
```

That's it. Widget is self-contained, ~67 KB JS gzipped + ~3 KB CSS gzipped, zero peer deps at the consumer side.

## Config API

```ts
BaconTrailWidget.init({
  container: HTMLElement,    // required — DOM node to mount into
  theme?: 'dark' | 'light',   // default 'dark'; 'light' logs a warning (not implemented in v1)
  brandColor?: string,        // default '#17d4fa' (626 Labs cyan); reserved, not used in v1
  brandLogo?: string,         // default undefined; reserved, not used in v1
  ctaUrl?: string,            // default '/#work' — anchors the "See the full suite →" link
  ctaLabel?: string,          // default 'See the full suite →'
  firebaseConfig?: null,      // reserved for future use; widget has zero Firebase traffic at runtime
});

BaconTrailWidget.destroy(container: HTMLElement): void;
```

`init` is idempotent — re-calling against the same container unmounts any prior tree before remounting. `destroy` is safe to call on an unmounted container.

## What visitors do

1. Widget mounts. Shows today's birthday actors (up to 6 in a 3 × 2 grid).
2. Visitor picks an actor → widget fetches their top 27 films (sorted by `popularity × log(vote_count)` so classic titles don't sink below re-releases).
3. Visitor picks a film. Widget fetches the cast. If Kevin Bacon (TMDB id `4724`) is in that cast, visitor wins — the widget's border pulses through cyan → magenta → success-green, and the result card names the film count.
4. If Bacon isn't in the cast, visitor picks a co-actor → widget fetches *their* films → loop. Six films max; hit the cap without finding Bacon and the round closes out gracefully.
5. Play Again resets state; CTA link drops the visitor into 626labs.dev's Work section.

Full acceptance criteria per epic: [`docs/prd.md`](./docs/prd.md).

---

## Local development

```sh
cd apps/widget-bacon-trail

# 1. Install
npm ci

# 2. One-time: paste your TMDB v3 read-only key into .env.local
cp .env.example .env.local
# …then edit .env.local with your key

# 3. Dev server
npm run dev
```

Open `http://localhost:3003/dev.html`. Vite's dev server loads `dev.html` (a standalone harness), and a small middleware proxies `/widget-bacon-trail/data/birthdays/*` from the hub's repo directory so the shard-fetch resolves identically in dev and prod.

### Scripts

- `npm run dev` — Vite dev server on `:3003` with HMR
- `npm run build` — production build → `../../widget-bacon-trail/{widget.js,widget.css}` + post-step copies `data/birthdays/` into the served tree
- `npm run preview` — serves the built bundle for manual QA
- `npm run test` — vitest run (57 tests cover reducer, services, components)
- `npm run typecheck` — `tsc --noEmit` against strict config

### Test coverage

| Surface | Tests | What's checked |
|---|---:|---|
| Reducer (`state.ts`) | 17 | every state transition, loop prevention, 6-film cap, Bacon-found trail extension |
| `baconCheck` | 5 | id-strict matching, edge cases around shared names |
| Shard service | 5 | happy path, retry, 404, malformed JSON |
| Components | 30 | all 9 components smoke-render + key behaviors (search, pagination, trail filter, result states) |

---

## Data pipeline

Birthday actors come from the Firestore `actorDatabase` collection (project `guestbuzz-cineperks`) but **the widget never talks to Firestore at runtime.** Instead:

- A nightly GitHub Action ([`.github/workflows/refresh-bacon-shards.yml`](../../.github/workflows/refresh-bacon-shards.yml)) runs at 06:00 UTC.
- It reads `actorDatabase`, groups by `birthDateKey`, sorts (known-Bacon-number first, then popularity desc), and writes 366 per-day JSON files.
- Shards land at `apps/widget-bacon-trail/data/birthdays/MM-DD.json` (source) and `widget-bacon-trail/data/birthdays/MM-DD.json` (served by GitHub Pages).
- Widget fetches exactly one shard per visit — today's. Each shard is ~5-10 KB uncompressed, ~2-3 KB gzipped.

Movie and cast data comes live from TMDB v3 per game (one request per movie picked + one per cast fetch). TMDB's rate limits are IP-scoped and generous; a delightful-portfolio-moment workload doesn't come close.

## Deploy pipeline

Pushing to `main` triggers one of two workflows, both of which commit artifacts back to the repo so GitHub Pages serves fresh files on every deploy:

| Trigger | Workflow | What happens |
|---|---|---|
| `apps/widget-bacon-trail/src/**`, `package.json`, `vite.config.ts`, etc. | [`build-widget.yml`](../../.github/workflows/build-widget.yml) | `npm ci` → typecheck → test → build with `VITE_TMDB_API_KEY` from repo secrets → bundle-size gate (≤150 KB gz js, ≤20 KB gz css) → commit `widget-bacon-trail/widget.{js,css}` |
| Daily cron (06:00 UTC) + manual dispatch | [`refresh-bacon-shards.yml`](../../.github/workflows/refresh-bacon-shards.yml) | `firebase-admin` reads Firestore → regenerates 366 shards → content-diff commit (no-op if Firestore hasn't changed) |

## Secrets

The widget has no runtime secrets. At build time:

- `VITE_TMDB_API_KEY` — TMDB v3 read-only key. Local dev reads from `.env.local`; CI reads from GitHub Actions secret of the same name. Baked into the built bundle (which is public — TMDB's terms permit client-side use of read-only v3 keys).

The nightly shard job has one secret:

- `FIREBASE_SA_JSON` — service account JSON for the `guestbuzz-cineperks` Firebase project, scoped to `Cloud Datastore User` (read-only). Never committed; only referenced by the refresh workflow.

---

## Architecture

Three-tier separation:

```
┌─────────────────────────────────────────────────────┐
│ RUNTIME (browser)                                   │
│   Widget bundle (React 19 + TS)                     │
│     ├─ shard fetch  →  /widget-bacon-trail/data/    │
│     └─ tmdb fetch   →  api.themoviedb.org/3/        │
└─────────────────────────────────────────────────────┘
                         ▲
                         │ served by GitHub Pages
┌─────────────────────────────────────────────────────┐
│ BUILD + DEPLOY (CI)                                 │
│   Vite library build  →  widget.{js,css}            │
│   Nightly Action      →  data/birthdays/*.json      │
└─────────────────────────────────────────────────────┘
                         ▲
                         │ firebase-admin, build-time only
┌─────────────────────────────────────────────────────┐
│ DATA (external)                                     │
│   Firestore actorDatabase (10,000 curated actors)   │
│   TMDB v3 API (movies, casts, images)               │
└─────────────────────────────────────────────────────┘
```

Full technical blueprint: [`docs/spec.md`](./docs/spec.md).

## Performance

On a typical broadband connection against `626labs.dev/#play`:

- First Contentful Paint: **~650 ms** (hub content + widget together)
- Widget script load: **~100 ms**
- Shard fetch: **~60 ms**
- Widget interactive (first actor card rendered): **~530 ms** post-DCL

QA screenshots + raw numbers: [`docs/qa-item7/REPORT.md`](./docs/qa-item7/REPORT.md).

## Accessibility

- All interactive elements have `aria-label` attributes
- Focus ring visible at 1.6 px solid brand-cyan with 1.6 px offset
- Screen-reader `status` live region announces state transitions (*"Film 3 of 6. Pulp Fiction. Kevin Bacon not in cast — choose a co-actor to continue."*)
- Color contrast passes WCAG AA for all primary text
- `prefers-reduced-motion` suppresses the edge-glow celebration

---

## Contributing

Pull requests welcome. See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the short version.

## License

MIT. See [`LICENSE`](./LICENSE).
