# Technical Spec — Birthday Bacon Trail Widget

Anchors: [`docs/scope.md`](./scope.md) · [`docs/prd.md`](./prd.md) · [`docs/builder-profile.md`](./builder-profile.md)

---

## Stack choices

| Layer | Tech | Version | Why |
|---|---|---|---|
| UI framework | React | 19.x | Matches `apps/widget/` and `apps/bacon-trail/` in the QuizShow monorepo. React 19's `useTransition` helps with the skeleton-UI-no-spinner pattern. |
| Build tool | Vite | 5.x | Same as both sibling widgets. Library-mode build (`build.lib`) produces a single UMD/IIFE bundle for `<script>` embedding. |
| Language | TypeScript | 5.x | Strict mode. Types extracted from existing `apps/bacon-trail/types.ts` + `services/actorService.ts` where applicable. |
| Styling | Tailwind CSS 4 + inline CSS vars | 4.x | Matches the sibling widgets' postcss config. Inline CSS custom properties pipe in the 626 Labs design tokens (loaded from the design skill's `colors_and_type.css`). |
| State | React local state (`useReducer`) | — | One reducer for the widget state machine (actor-pick → movie-pick → co-actor-pick → result). No Redux, no Zustand; the state lives only for the duration of a round. |
| HTTP | `fetch` (native) | — | No Axios. Matches both sibling widgets. |
| External APIs | TMDB v3 (direct) + Firestore (build-time only) | — | Runtime = TMDB. Build-time = Firestore (nightly Action only; widget never talks to Firestore). |

---

## Architecture overview

Three-tier separation:

```
┌──────────────────────────────────────────────────────────────┐
│ RUNTIME (runs in the visitor's browser)                      │
│                                                              │
│   ┌────────────────┐     ┌────────────────────────┐         │
│   │ Widget bundle  │────▶│ /widget-bacon-trail/   │          │
│   │  (React + TS)  │     │   data/birthdays/      │          │
│   └────────────────┘     │   MM-DD.json           │          │
│           │              └────────────────────────┘          │
│           │              (served by GitHub Pages)            │
│           │                                                  │
│           └──────────▶ TMDB v3 API                           │
│                       (person/:id/movie_credits)             │
│                       (movie/:id/credits)                    │
└──────────────────────────────────────────────────────────────┘
                                ▲
                                │ (widget fetches)
┌──────────────────────────────────────────────────────────────┐
│ BUILD + DEPLOY (CI)                                          │
│                                                              │
│   ┌─────────────────┐                                        │
│   │ Vite build      │─────▶ widget-bacon-trail/widget.js     │
│   │ apps/widget-    │       (committed to hub repo)          │
│   │   bacon-trail/  │                                        │
│   └─────────────────┘                                        │
│                                                              │
│   ┌─────────────────┐                                        │
│   │ Nightly Action  │─────▶ apps/widget-bacon-trail/data/    │
│   │ (6am UTC cron)  │        birthdays/MM-DD.json × 366      │
│   │ firebase-admin  │                                        │
│   └─────────────────┘                                        │
│           ▲                                                  │
└───────────┼──────────────────────────────────────────────────┘
            │
┌───────────────────────────────────┐
│ DATA SOURCE (external)            │
│                                   │
│  guestbuzz-cineperks Firestore    │
│   actorDatabase collection        │
│   (10,000 curated actors)         │
└───────────────────────────────────┘
```

The widget has **zero runtime Firestore dependency**. Firestore is touched only by the nightly GitHub Action, which materializes shards into the hub repo. At runtime, the widget fetches a single static JSON file from GitHub Pages.

---

## File structure

```
626labs-hub/
├── apps/
│   └── widget-bacon-trail/
│       ├── package.json
│       ├── tsconfig.json
│       ├── vite.config.ts              # library-mode build → ../../widget-bacon-trail/
│       ├── postcss.config.js           # Tailwind 4 postcss setup (match apps/widget)
│       ├── .env.example                # template showing VITE_TMDB_API_KEY= (gitignored actual)
│       ├── .gitignore                  # node_modules, dist, .env.local
│       ├── src/
│       │   ├── index.tsx               # entry: exports BaconTrailWidget.init/destroy
│       │   ├── Widget.tsx              # root component, config props, state reducer
│       │   ├── state.ts                # useReducer, typed actions + state shape
│       │   ├── types.ts                # Actor, Movie, TrailStep, Outcome
│       │   ├── components/
│       │   │   ├── BirthdayActorGrid.tsx       # Epic 2: pick starting actor
│       │   │   ├── MovieList.tsx               # Epic 3: pick a film
│       │   │   ├── CoActorGrid.tsx             # Epic 4: pick a co-actor
│       │   │   ├── ResultCard.tsx              # Epic 5: found / out-of-films
│       │   │   ├── TrailBreadcrumb.tsx         # top-of-widget trail viz
│       │   │   ├── FilmCounter.tsx             # "Film N / 6" indicator
│       │   │   ├── SkeletonCard.tsx            # no-spinner loading UI
│       │   │   └── ErrorCard.tsx               # inline retry UI
│       │   ├── services/
│       │   │   ├── tmdbService.ts              # fetch wrappers for TMDB v3
│       │   │   ├── shardService.ts             # fetch + parse today's birthday shard
│       │   │   └── baconCheck.ts               # "is TMDB id 4724 in this cast?"
│       │   ├── styles/
│       │   │   ├── tokens.css                  # imported from 626labs-design + scoped
│       │   │   └── widget.css                  # component styles (Tailwind utilities)
│       │   └── lib/
│       │       └── brand.ts                    # 626 Labs color/type token constants
│       ├── data/
│       │   └── birthdays/
│       │       ├── .gitkeep
│       │       ├── 01-01.json
│       │       ├── 01-02.json
│       │       └── ... (366 files after first Action run)
│       └── docs/
│           ├── builder-profile.md
│           ├── scope.md
│           ├── prd.md
│           ├── spec.md                 # ← you are here
│           └── checklist.md            # ← written next by /checklist
│
├── widget-bacon-trail/                 # ← Vite outDir; committed build artifact
│   ├── widget.js                       # UMD bundle, ~150 KB gzipped target
│   ├── widget.css                      # ~20 KB gzipped target
│   └── widget.js.map                   # sourcemap for debugging
│
├── scripts/
│   ├── refresh-bacon-shards.mjs        # nightly Action runs this
│   └── (existing: track-traffic.mjs, render-hub.py, etc.)
│
└── .github/workflows/
    └── refresh-bacon-shards.yml        # 0 6 * * * cron + workflow_dispatch
```

### Why this layout

- **Source at `apps/widget-bacon-trail/src/`**: keeps monorepo-style workspace hygiene. Matches QuizShow's convention; if Este ever moves this into QuizShow later, the path translates directly.
- **Build artifact at `widget-bacon-trail/` (root)**: mirrors the existing `sanduhr/` sub-app pattern. Short URL (`/widget-bacon-trail/widget.js`), served by GitHub Pages without any config change.
- **Data at `apps/widget-bacon-trail/data/birthdays/`**: kept next to the source so it's clear what owns it. But the widget fetches from `/widget-bacon-trail/data/birthdays/MM-DD.json` at runtime — which means the build step needs to *also* copy the data dir into the root output. (Alternative: widget fetches from `/apps/widget-bacon-trail/data/birthdays/MM-DD.json` — longer URL but no duplication. Picked the short-URL path below.)

---

## Data flow — runtime

### State machine

```
     ┌────────┐
     │ mount  │
     └───┬────┘
         ▼
  ┌──────────────┐      fetch today's shard
  │  loading     │──────────────────────────┐
  └──────┬───────┘                          │
         ▼                                  ▼
  ┌──────────────┐                 ┌─────────────────┐
  │ pick-actor   │                 │ error (retry)   │
  └──────┬───────┘                 └─────────────────┘
         │ (user picks birthday actor)
         ▼
  ┌──────────────┐      fetch /person/:id/movie_credits
  │ pick-movie   │────────────────────────────────────┐
  └──────┬───────┘                                    │
         │ (user picks film)                          │
         ▼                                            ▼
  ┌────────────────────────┐                ┌─────────────────┐
  │ fetching cast          │                │ error (retry)   │
  │ + film counter ++      │                └─────────────────┘
  └──────┬─────────────────┘
         │ fetch /movie/:id/credits
         ▼
      [is TMDB id 4724 (Kevin Bacon) in cast?]
         │
    ┌────┴────┐
    │         │
   yes       no
    │         │
    ▼         ▼
┌────────┐   ┌──────────────┐
│ result │   │ pick-co-actor │
│ FOUND  │   └──────┬────────┘
└────────┘          │ (user picks co-actor)
                    │
         ┌──────────┴──────────┐
         │                     │
   films < 6                films = 6
         │                     │
         ▼                     ▼
    loop to pick-movie     ┌─────────┐
                           │ result  │
                           │ OUT-    │
                           │ OF-FILM │
                           └─────────┘
```

### State shape (TypeScript)

```typescript
type WidgetState =
  | { status: 'loading' }
  | { status: 'error'; message: string; retry: () => void }
  | { status: 'pick-actor'; actors: Actor[]; poolIndex: number }
  | { status: 'pick-movie'; subject: Actor; movies: Movie[]; filmCount: number }
  | { status: 'fetching-cast'; subject: Actor; movie: Movie; filmCount: number }
  | { status: 'pick-co-actor'; castInMovie: Actor[]; filmCount: number }
  | { status: 'result'; outcome: 'found' | 'out-of-films'; filmCount: number; trail: TrailStep[] };

type Actor = {
  id: number;
  name: string;
  profilePath: string | null;
  birthday?: string;
  popularity?: number;
  baconNumber?: number;
};

type Movie = {
  id: number;
  title: string;
  posterPath: string | null;
  releaseYear: number | null;
  popularity: number;
};

type TrailStep =
  | { kind: 'actor'; actor: Actor }
  | { kind: 'movie'; movie: Movie; baconInCast: boolean };
```

### Actions

- `SHARD_LOADED(actors: Actor[])`
- `ACTOR_PICKED(actor: Actor)` → fetch `/person/:id/movie_credits` → `MOVIES_LOADED`
- `MOVIES_LOADED(movies: Movie[])`
- `MOVIE_PICKED(movie: Movie)` → filmCount++, fetch `/movie/:id/credits` → `CAST_LOADED`
- `CAST_LOADED(cast: Actor[])` → check for Bacon (id `4724`):
  - If present: `RESULT(outcome: 'found')`
  - If absent and filmCount < 6: `STAY_ON_CO_ACTOR(cast)`
  - If absent and filmCount === 6: `RESULT(outcome: 'out-of-films')`
- `CO_ACTOR_PICKED(actor: Actor)` → back to pick-movie with new subject
- `PLAY_AGAIN` → reset to `loading` state, refetch today's shard (fresh random pull)
- `SHUFFLE_ACTORS` → advance poolIndex, show next 6 actors from shard

### HTTP endpoints

| Endpoint | When | Retry policy |
|---|---|---|
| `GET /widget-bacon-trail/data/birthdays/{MM-DD}.json` | On mount + on Play Again | 2 retries with exponential backoff (500ms, 1s), then error state |
| `GET https://api.themoviedb.org/3/person/{id}/movie_credits?api_key=…` | After actor pick | 2 retries, same pattern |
| `GET https://api.themoviedb.org/3/movie/{id}/credits?api_key=…` | After movie pick (BEFORE co-actor screen) | 2 retries, same pattern |
| `GET https://image.tmdb.org/t/p/w185/{path}` | Actor/movie image loads | Native `<img>` error handler → initials avatar fallback |

Each TMDB call sets `Accept: application/json` and caches responses in a `Map<string, Promise<...>>` for the duration of a widget round (avoids re-fetching `person_credits` if Play Again picks the same starting actor — unlikely but cheap).

---

## Data flow — build time (nightly Action)

### `scripts/refresh-bacon-shards.mjs`

```
1. Parse GOOGLE_APPLICATION_CREDENTIALS → firebase-admin init
2. Query actorDatabase collection, projecting only needed fields
   (id, name, profilePath, birthday, birthDateKey, popularity, baconNumber)
3. Group actors by birthDateKey → Map<MM-DD, Actor[]>
4. Sort each day's group by popularity desc, then baconNumber asc
5. For each MM-DD from 01-01 to 12-31:
   - Build output: { date: "MM-DD", actors: [...] }
   - Write to apps/widget-bacon-trail/data/birthdays/MM-DD.json
6. git diff the data/ dir:
   - If no changes: log "no data drift, exiting clean" and exit 0
   - If changes: git add + commit with message
     "chore(bacon-shards): refresh {N} day(s) of birthday data"
   - git push
```

**No `generatedAt` field in the JSON files** (per idempotency decision). Freshness is tracked via git log of the `data/birthdays/` directory. If the widget ever needs to surface freshness, it can read the HTTP `Last-Modified` header from GitHub Pages on the shard fetch.

### `.github/workflows/refresh-bacon-shards.yml`

```yaml
name: Refresh Bacon Shards
on:
  schedule:
    - cron: '0 6 * * *'       # 06:00 UTC daily
  workflow_dispatch:

concurrency:
  group: refresh-bacon-shards
  cancel-in-progress: false

jobs:
  refresh:
    runs-on: ubuntu-latest
    if: github.actor != 'github-actions[bot]'   # same anti-recursion pattern as rebuild-hub.yml
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Write service account key
        run: |
          echo "${{ secrets.FIREBASE_SA_JSON }}" > /tmp/sa.json
      - name: Install firebase-admin
        run: npm install firebase-admin@^12
      - name: Refresh shards
        env:
          GOOGLE_APPLICATION_CREDENTIALS: /tmp/sa.json
        run: node scripts/refresh-bacon-shards.mjs
      - name: Commit + push if changed
        run: |
          if [[ -n "$(git status --porcelain apps/widget-bacon-trail/data/)" ]]; then
            git config user.name 'github-actions[bot]'
            git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
            git add apps/widget-bacon-trail/data/
            git commit -m "chore(bacon-shards): refresh $(date -u +%Y-%m-%d)"
            git push
          else
            echo "No data drift."
          fi
```

Secrets required:

- `FIREBASE_SA_JSON` — read-only service account JSON from the `guestbuzz-cineperks` Firebase project. Builder creates this during `/build` item 1 (Firestore project console → Service accounts → Generate new private key → scope to `Cloud Datastore User` role).

---

## External dependencies

### Runtime (shipped in widget bundle)

| Package | Version | Bundle impact | Purpose |
|---|---|---|---|
| `react` | ^19.2 | ~45 KB gz | UI framework |
| `react-dom` | ^19.2 | (included) | DOM renderer |
| `lucide-react` | ^0.555 | ~8 KB gz (tree-shaken) | Play icon, chevron, retry icon — per `626labs-design` guidance |
| (no firebase) | — | — | **Deliberately excluded** — widget never talks to Firestore at runtime |
| (no firebase-admin) | — | — | Server-only dep, never touches the bundle |
| (no axios) | — | — | Use `fetch` |

**Bundle budget ≤ 150 KB gzipped** per PRD. Expected composition:

- React + ReactDOM tree-shaken: ~50 KB gz
- Widget code + components: ~30-40 KB gz
- Tailwind utilities (purged): ~10 KB gz
- lucide-react icons (tree-shaken to used set): ~5 KB gz
- Total estimate: **~95-110 KB gz** — comfortably under budget.

### Build-time

| Package | Version | Purpose |
|---|---|---|
| `vite` | ^5 | Build tool |
| `@vitejs/plugin-react` | ^5 | React transform |
| `typescript` | ^5 | Type checking |
| `tailwindcss` | ^4 | Utility-first CSS |
| `@tailwindcss/postcss` | ^4 | PostCSS integration |
| `postcss` | ^8 | CSS pipeline |
| `autoprefixer` | ^10 | Vendor prefixes |

### Nightly-Action-only

| Package | Version | Purpose |
|---|---|---|
| `firebase-admin` | ^12 | Firestore server-side access |

(Installed in the Action runner, not in the widget's `package.json` dependencies — avoids shipping Firebase-admin weight into any future dev dependency graph consumer.)

### External services

| Service | Usage | Auth | Rate limit concerns |
|---|---|---|---|
| TMDB v3 | Runtime per-game | `VITE_TMDB_API_KEY` baked at build | 40 req / 10s per IP. Widget does at most 2 TMDB calls per picked movie, plus ~30 image loads. Well under limit for a portfolio widget. |
| Firestore (`guestbuzz-cineperks`) | Nightly only | Service account JSON | One read per MM-DD = 366 reads/day. Free tier limit is 50K reads/day. Essentially free. |
| GitHub Pages | Serves widget bundle + shards | — | Generous; no concerns. |

---

## Integration with 626labs-hub

### Hub changes

**New section in `index.html`** (the partial-render marker pattern in `scripts/render-hub.py`):

```html
<!-- SITE_JSON:play:start -->
<section class="play" id="play">
  <div class="container">
    <h2>Also, we make games.</h2>
    <p class="lead">Try one.</p>

    <div class="play-grid">
      <div id="bacon-widget" class="play-widget"></div>
      <!-- Future: <div id="cineperks-widget" class="play-widget"></div> -->
    </div>
  </div>
</section>

<script src="/widget-bacon-trail/widget.js"></script>
<link rel="stylesheet" href="/widget-bacon-trail/widget.css" />
<script>
  BaconTrailWidget.init({
    container: document.getElementById('bacon-widget'),
    ctaUrl: '/#work',
    ctaLabel: 'See the full suite →'
  });
</script>
<!-- SITE_JSON:play:end -->
```

### `content/site.json` additions

```json
{
  "play": {
    "enabled": true,
    "header": "Also, we make games.",
    "lead": "Try one.",
    "widgets": [
      {
        "id": "bacon-widget",
        "script": "/widget-bacon-trail/widget.js",
        "stylesheet": "/widget-bacon-trail/widget.css",
        "initFn": "BaconTrailWidget.init",
        "config": { "ctaUrl": "/#work", "ctaLabel": "See the full suite →" }
      }
    ]
  }
}
```

### `scripts/render-hub.py` addition

New `render_play_section(play: dict) -> str` function emits the section HTML from the config above, handling the widget list for forward compatibility (when CinePerks joins the section, add one more entry to `widgets[]`).

### Layout CSS additions to `index.html`

```css
.play-grid {
  display: grid;
  grid-template-columns: 1fr;              /* single widget in v1 */
  gap: var(--s-5);
  justify-items: center;
  max-width: 480px;
  margin: 0 auto;
}
.play-widget {
  width: 100%;
  max-width: 400px;
  aspect-ratio: 2 / 3;                     /* matches widget 400×600 */
  min-height: 540px;
}

@media (min-width: 960px) {
  /* When a second widget is added: */
  .play-grid.two-up {
    grid-template-columns: 1fr 1fr;
    max-width: 900px;
  }
}
```

---

## Widget config API

Matches the CinePerks widget's embed contract, extended for the Bacon Trail's concerns:

```typescript
interface BaconTrailWidgetConfig {
  container: HTMLElement;                  // required
  theme?: 'dark' | 'light';                // default 'dark'; 'light' logs warning in v1 (not implemented)
  brandColor?: string;                     // default '#17d4fa'
  brandLogo?: string;                      // default undefined (no logo chip)
  ctaUrl?: string;                         // default '/#work'
  ctaLabel?: string;                       // default 'See the full suite →'
  firebaseConfig?: null;                   // intentionally unused, forward-compat only
}

// Global exports (UMD):
window.BaconTrailWidget = {
  init(config: BaconTrailWidgetConfig): void;
  destroy(container: HTMLElement): void;
};
```

### init behavior

1. Validate `container` is a DOM node; warn + no-op if not.
2. If previous tree exists on this container, call `destroy` first.
3. Mount React tree with `createRoot(container).render(<Widget {...config} />)`.
4. Store the root in a WeakMap keyed by container so `destroy` can find it.

### destroy behavior

1. Look up root from WeakMap.
2. Call `root.unmount()`.
3. Remove any global listeners the widget added (none expected in v1).

---

## Vite config (`vite.config.ts`)

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: path.resolve(__dirname, '../../widget-bacon-trail'),
    emptyOutDir: true,
    lib: {
      entry: path.resolve(__dirname, 'src/index.tsx'),
      formats: ['umd'],
      name: 'BaconTrailWidget',
      fileName: () => 'widget.js',
    },
    rollupOptions: {
      output: {
        assetFileNames: (info) =>
          info.name && /\.css$/.test(info.name) ? 'widget.css' : '[name][extname]',
        globals: {},
      },
    },
    sourcemap: true,
    target: 'es2019',
  },
  define: {
    // TMDB key baked at build time from env or CI secret
    'import.meta.env.VITE_TMDB_API_KEY': JSON.stringify(process.env.VITE_TMDB_API_KEY || ''),
  },
});
```

Output after `pnpm build`:

```
widget-bacon-trail/
├── widget.js         (UMD bundle, minified)
├── widget.css        (Tailwind purged)
└── widget.js.map     (sourcemap)
```

Also copies `apps/widget-bacon-trail/data/birthdays/` → `widget-bacon-trail/data/birthdays/` during build via a small postbuild script, so the runtime fetch URL `/widget-bacon-trail/data/birthdays/MM-DD.json` resolves without directory translation.

*Alternative considered: widget fetches from `/apps/widget-bacon-trail/data/birthdays/MM-DD.json` directly (no copy, longer URL). Picked the copy approach to keep the public URL surface clean, at the cost of one postbuild script.*

---

## Testing approach

Scope's quality bar sets testable targets. Minimum test surface:

| Layer | What to test | Tool |
|---|---|---|
| State reducer | Every action transition, edge cases (film counter at 6, shard has < 6 actors, Bacon in first cast) | `vitest` |
| Bacon check | `baconCheck.ts` against synthetic cast arrays with/without id 4724 | `vitest` |
| Shard service | Fetch returns well-formed data; error handler on 404 / malformed JSON | `vitest` + mocked `fetch` |
| Component renders | Smoke tests: each screen renders without crashing given state | `@testing-library/react` |
| Build output | Bundle size ≤ 150 KB gz, CSS ≤ 20 KB gz | CI step runs `vite build` + `gzip-size-cli` |
| E2E | Widget loads on a test hub page, user can complete a round (mocked TMDB) | deferred — add to `/vibe-test:audit` later if needed |

Tests live at `apps/widget-bacon-trail/src/**/__tests__/` or co-located as `.test.ts(x)`.

**Build-time test in CI**: Vite build + bundle size check. Fails the build if the widget exceeds 150 KB gz.

---

## Security considerations

- **TMDB key in bundle**: read-only v3 key, TMDB-terms-compliant for client-side use. Rotate if leaked (standard practice). No PII exposure.
- **No Firestore client-side**: widget cannot read or write Firestore at runtime; eliminates security-rules surface area.
- **No user data collected**: widget is stateless, no cookies, no localStorage, no fingerprint. CSP-friendly.
- **Service account JSON in GitHub secret**: scoped to `Cloud Datastore User` role, read-only on `guestbuzz-cineperks`. No write permissions. Rotatable via Firebase console.
- **CSP on 626labs.dev**: widget needs to load images from `image.tmdb.org` and make XHRs to `api.themoviedb.org`. Hub's existing CSP (if any) needs to allow those origins; `/spec` open-item.

---

## Versioning

- Widget bundle versioned via semver in `apps/widget-bacon-trail/package.json`.
- First release: `0.1.0`.
- Build output at `widget-bacon-trail/widget.js` is always the latest; no per-version URLs in v1. (If that becomes needed, we switch to `widget-bacon-trail/v0.1.0/widget.js` with a `latest` symlink or redirect.)
- Breaking changes to the init config API: bump major. No breaking API changes expected in v1.

---

## Open issues for `/checklist`

Everything load-bearing has been resolved above. Remaining concrete items for the checklist phase to plan around:

1. **TMDB key acquisition** — does the builder already have a TMDB v3 API key (likely yes — the sibling widgets use one)? Reuse; if not, create a new one at themoviedb.org. First checklist item.
2. **Service account provisioning** — one-time Firebase console step (create service account in `guestbuzz-cineperks`, download JSON, add as GitHub secret). First checklist item alongside TMDB key.
3. **CSP review** — check hub's current `<meta http-equiv="Content-Security-Policy">` or equivalent header on GitHub Pages; if restrictive, add `image.tmdb.org` and `api.themoviedb.org` exceptions. Early-checklist item.
4. **QuizShow workspace decision** — `apps/widget-bacon-trail/package.json` stands alone (not wired into QuizShow's workspace). If Este wants monorepo-style shared deps later, that's a v2 refactor.
5. **Responsive design QA** — needs in-browser testing on ≥ 3 devices (iPhone, iPad, desktop). Late-checklist item.
6. **Shard-copy postbuild script** — trivial but needs authoring: `cp -r apps/widget-bacon-trail/data widget-bacon-trail/data`. Or wire into Vite config via `vite-plugin-static-copy`.
7. **First shard seed** — before the nightly Action fires, the widget needs *some* shard to fetch. Either run the Action manually via `workflow_dispatch` once during `/build`, or commit a hand-generated seed for today's date as part of the first merged PR.

---

## Summary for `/checklist`

- **7 checklist items** expected: project scaffold + Vite config, state reducer + services, component build (4 screens), tests, shard-refresh Action, hub integration, final QA.
- **Checkpoints** proposed at items 3 (after state + services), 5 (after components + tests), and 7 (before final merge).
- **Build mode**: autonomous with the parallel Explore agents + verification hooks Este specified during `/onboard`.
- **Pacing**: multi-session OK per builder preference; no single-session pressure.
- **Architecture docs complete**; no external architecture doc needed since the spec is self-contained.
