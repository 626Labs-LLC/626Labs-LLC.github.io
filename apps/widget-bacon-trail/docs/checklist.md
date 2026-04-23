# Build Checklist — Birthday Bacon Trail Widget

Anchors: [`docs/scope.md`](./scope.md) · [`docs/prd.md`](./prd.md) · [`docs/spec.md`](./spec.md) · [`docs/builder-profile.md`](./builder-profile.md)

---

## Build Preferences

- **Build mode:** Autonomous with checkpoints
- **Comprehension checks:** N/A (autonomous mode) — verification hooks between items instead (per builder's explicit preference from `/onboard`)
- **Git:** Commit after each item with message `chore(build): complete step N — <title>`. Commits serve as revert points if anything breaks mid-build.
- **Verification:** On — checkpoints after items **3**, **5**, and **7**. Agent pauses, summarizes what was built, builder confirms before continuing.
- **Check-in cadence:** Multi-session OK; no forced single-session ship (per scope's *"leave the builder self-sufficient"* motto + builder's stated preference).
- **Parallel research:** Spawn **Explore sub-agents** for independent research tasks during item execution — examples in each item below.
- **Verification hooks:** After every item, run a scoped check (type-check, test, bundle size, responsive snapshot) before advancing. Hooks fail → stop and fix, don't carry forward.

---

## Checklist

### 1. Project scaffold + env + credentials setup

**Spec ref:** `spec.md > Stack choices` · `spec.md > Vite config` · `spec.md > External dependencies`

**What to build:**

- `apps/widget-bacon-trail/package.json` — React 19, lucide-react, Vite 5, Tailwind 4, TypeScript 5, vitest + @testing-library/react for tests. Standalone (not added to QuizShow workspace).
- `apps/widget-bacon-trail/tsconfig.json` — strict mode, JSX react-jsx, target ES2019.
- `apps/widget-bacon-trail/vite.config.ts` — exactly the library-mode block from `spec.md > Vite config`. `outDir: '../../widget-bacon-trail/'`, UMD output, sourcemap on.
- `apps/widget-bacon-trail/postcss.config.js` — Tailwind 4 + autoprefixer, same shape as `apps/widget/postcss.config.js`.
- `apps/widget-bacon-trail/.env.example` — documents `VITE_TMDB_API_KEY=<your-key-here>`.
- `apps/widget-bacon-trail/.gitignore` — `node_modules`, `dist`, `.env.local`, `.env`, `/tmp`.
- `apps/widget-bacon-trail/src/index.tsx` — empty stub exporting `BaconTrailWidget = { init, destroy }` with console-log bodies (real impl in item 5).
- **TMDB key acquisition** — reuse the existing `VITE_TMDB_API_KEY` used by `apps/bacon-trail` and `apps/widget`. Place it in `apps/widget-bacon-trail/.env.local` (gitignored). Also add as GitHub Actions secret `VITE_TMDB_API_KEY` for CI builds.
- **Firebase service account provisioning** — one-time step in the Firebase console for project `guestbuzz-cineperks`:
  1. Service accounts → Generate new private key → download JSON.
  2. Role: **Cloud Datastore User** (read-only is enough for Firestore access).
  3. Paste the JSON contents as GitHub Actions secret `FIREBASE_SA_JSON` in the `626labs-hub` repo.

**Acceptance:**

- `pnpm install` (or `npm install`) at `apps/widget-bacon-trail/` succeeds with no peer-dep warnings.
- `pnpm build` produces `../../widget-bacon-trail/widget.js` (even if the output is a stub at this point).
- `VITE_TMDB_API_KEY` is readable in `import.meta.env` during dev (`pnpm dev` runs without the "TMDB key missing" warning the sibling widgets print).
- `FIREBASE_SA_JSON` secret exists in GitHub Actions repo secrets (visible in Settings → Secrets).
- No secrets committed to git — verify with `git status` before first commit.

**Verify (hooks):**

1. `pnpm build` succeeds.
2. `ls ~/Projects/626labs-hub/widget-bacon-trail/widget.js` shows the output file.
3. `grep -R 'AIzaSy\|tmdb\|TMDB_API_KEY' apps/widget-bacon-trail/ --include='*.ts' --include='*.tsx'` shows no key in source, only env-var reads.
4. `git status` shows no `.env.local` staged.

**Parallel research:** none needed; all context is in spec.

**Effort:** 1-2h (plus ~5 min Firebase console work).

---

### 2. Types + state reducer + services (non-UI)

**Spec ref:** `spec.md > Data flow — runtime > State shape` · `spec.md > Data flow — runtime > Actions` · `spec.md > File structure`

**What to build:**

- `src/types.ts` — exact TypeScript shapes from `spec.md`: `Actor`, `Movie`, `TrailStep`, `WidgetState`, `BaconTrailWidgetConfig`.
- `src/state.ts` — `useReducer` with the action union from `spec.md > Actions` (`SHARD_LOADED`, `ACTOR_PICKED`, `MOVIES_LOADED`, `MOVIE_PICKED`, `CAST_LOADED`, `CO_ACTOR_PICKED`, `PLAY_AGAIN`, `SHUFFLE_ACTORS`, plus an `ERROR` action). Reducer is a pure function; no fetches inside.
- `src/services/tmdbService.ts` — `fetchMovieCreditsForActor(actorId)` and `fetchCastForMovie(movieId)` returning typed promises. Direct `fetch()` calls to TMDB v3. Retry wrapper: 2 attempts with 500 ms + 1 s backoff, then throws.
- `src/services/shardService.ts` — `fetchTodayShard()` resolves `{date: string, actors: Actor[]}`. URL: `/widget-bacon-trail/data/birthdays/{MM-DD}.json` where MM-DD is today in the user's local time. Same retry pattern as TMDB.
- `src/services/baconCheck.ts` — `castIncludesBacon(cast: Actor[]): boolean` — single-line wrapper checking for TMDB id `4724`. Isolated so it's trivially testable.
- `src/**/__tests__/state.test.ts` — vitest suite covering every transition in the state machine, including edge cases (film counter at 6, shard has < 6 actors, Bacon in first cast).
- `src/**/__tests__/baconCheck.test.ts` — synthetic cast with/without Bacon.
- `src/**/__tests__/shardService.test.ts` — mocked `fetch` for happy path, 404, malformed JSON.

**Acceptance:**

- `pnpm test` shows ≥ 15 tests passing across the three test files.
- `pnpm build` still succeeds (index.tsx can now import the types + services to prove they compile).
- Zero `any` in the diff.
- `tmdbService.ts` and `shardService.ts` have no React imports — pure service layer.

**Verify (hooks):**

1. `pnpm test` green.
2. `pnpm tsc --noEmit` green (strict-mode type check).
3. `pnpm build` green.
4. `grep -R 'any' src/ --include='*.ts'` returns no `: any` or `as any` lines (excluding test mocks).

**Parallel research:** spawn one Explore subagent mid-item with: *"Check `~/Projects/QuizShow/apps/bacon-trail/services/` for the exact TMDB response shape returned by `/person/{id}/movie_credits` and `/movie/{id}/credits` — what fields do we actually consume? Return a typed summary in under 150 words so we don't hit TMDB's API during development to discover schema."*

**Effort:** 2-3h.

---

### 3. Shard pipeline + first seed ← CHECKPOINT 1

**Spec ref:** `spec.md > Data flow — build time` · `spec.md > .github/workflows/refresh-bacon-shards.yml`

**What to build:**

- `scripts/refresh-bacon-shards.mjs` — the full Node script from `spec.md`. Uses `firebase-admin`, queries `actorDatabase`, groups by `birthDateKey`, writes 366 files to `apps/widget-bacon-trail/data/birthdays/MM-DD.json`. No `generatedAt` field in output.
- `.github/workflows/refresh-bacon-shards.yml` — the YAML from `spec.md`, including the `contents: write` permission, anti-recursion guard, `FIREBASE_SA_JSON` secret usage, and the content-diff commit block.
- `apps/widget-bacon-trail/data/birthdays/.gitkeep` — empty placeholder so the directory exists before the first run.
- **First-seed via `workflow_dispatch`**: manually trigger the workflow from the GitHub UI (or `gh workflow run refresh-bacon-shards.yml`). Confirm it commits all 366 shards on first run.

**Acceptance:**

- `scripts/refresh-bacon-shards.mjs` runs locally (`GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa.json node scripts/refresh-bacon-shards.mjs`) without error.
- After first CI run: `apps/widget-bacon-trail/data/birthdays/` contains all 366 `MM-DD.json` files, each with the schema `{date, actors[]}`.
- Each shard has **no `generatedAt` field** (per idempotency decision).
- Re-running the workflow against unchanged Firestore data produces **no new commit** (content-diff logic works).
- `git log apps/widget-bacon-trail/data/` shows exactly one commit after the first run.

**Verify (hooks):**

1. `cat apps/widget-bacon-trail/data/birthdays/04-23.json | jq .actors | length` returns a number ≥ 15 (validates the seed for our known test day).
2. `grep -r generatedAt apps/widget-bacon-trail/data/` returns nothing.
3. Second `workflow_dispatch` run on same day → CI output says `"No data drift."` and exits without committing.
4. Last 3 lines of the workflow's `refresh` job logs show successful Firestore read + write + commit (or no-op).

**CHECKPOINT 1 — pause and summarize to builder before continuing:**

- Data pipeline is working end-to-end from Firestore → shards committed to repo.
- First 366 shards seeded.
- Types + services tested in isolation (from item 2).
- Ready to start building UI.

**Parallel research:** spawn Explore subagent: *"Look at `~/Projects/626labs-hub/.github/workflows/track-traffic.yml` and `rebuild-hub.yml`. Identify the exact anti-recursion guard pattern, concurrency block, and permissions block used. Return a 50-word summary so `refresh-bacon-shards.yml` matches conventions."*

**Effort:** 1-2h.

---

### 4. Component build — 4 screens + supporting UI

**Spec ref:** `spec.md > File structure` (components tree) · `prd.md > Epic 2-5` · `scope.md > Decision 4` · `626labs-design` skill tokens

**What to build:**

- `src/styles/tokens.css` — import / inline the needed color + type tokens from the `626labs-design` skill's `colors_and_type.css`. Scoped to `.bacon-trail-widget` so the widget doesn't leak styles to the hub.
- `src/lib/brand.ts` — TypeScript constants for the palette and typography tokens used inline (e.g., `BRAND.cyan = '#17d4fa'`).
- `src/components/BirthdayActorGrid.tsx` — Epic 2. Renders 6 actors (3×2), cards with profile image + name + birth year. Includes "Different actors" button if shard has ≥ 7 pool members.
- `src/components/MovieList.tsx` — Epic 3. Scrollable list (not a grid — spec says "scrollable list"), top 20 movies sorted by popularity. Each card: poster + title + year.
- `src/components/CoActorGrid.tsx` — Epic 4. 3×5 or 5×3 grid of top 15 cast. Deemphasize actors already in the trail. **No Bacon marker** (Bacon never reaches this screen).
- `src/components/ResultCard.tsx` — Epic 5. Found state uses `--success` only (no `--warning`). Trail breadcrumb rendered. "Play Again" (cyan→magenta gradient button) + "See the full suite →" text link.
- `src/components/TrailBreadcrumb.tsx` — running display of the walk: `{actor} → {movie} → {actor} → ...`. Collapses on small widths.
- `src/components/FilmCounter.tsx` — "Film N / 6" in JetBrains Mono, uppercase, +0.12em tracking.
- `src/components/SkeletonCard.tsx` — loading state cards at the right dimensions. Pulse animation via Tailwind's `animate-pulse`. **Never a spinner.**
- `src/components/ErrorCard.tsx` — inline error UI with retry button. Prop: `{message: string, onRetry: () => void}`.
- `src/styles/widget.css` — widget-scoped styles + Tailwind utility overrides.

**Components consume state, don't own it** — all state lives in `Widget.tsx` (item 5); these are dumb render components.

**Acceptance:**

- Every component renders without crashing given its props (smoke-test via `@testing-library/react`).
- `BirthdayActorGrid` renders 6 cards given 6 actors, and shuffles to a different set on button click.
- `CoActorGrid` deemphasizes actors whose ids are already in the trail (opacity 0.4, non-clickable).
- `ResultCard` found state shows `--success` color (green `#2bd99a`); out-of-films state shows `--danger` color (`#ff5472`).
- No emoji in rendered HTML.
- Touch targets ≥ 44×44 on interactive elements.
- `pnpm tsc --noEmit` green.
- Component CSS adheres to 626 Labs palette — no stray `#f59e0b` or off-brand colors.

**Verify (hooks):**

1. `pnpm test` — smoke tests + existing logic tests all pass.
2. `pnpm build` — CSS bundle under 20 KB gz (use `gzip-size` or equivalent).
3. `grep -R '#f59e0b\|amber\|🥓' src/` returns nothing.
4. Visual check: run `pnpm dev` with a mocked state and eyeball each screen against the 626 Labs design skill's `preview/` cards.

**Parallel research:** spawn 2 Explore subagents in parallel:
- **A.** *"Read `~/Projects/QuizShow/apps/bacon-trail/components/` for how each screen handles loading, error, and transition states. Return the patterns worth stealing (skeletons, transition durations, etc.) in under 200 words."*
- **B.** *"Read `~/Projects/626labs-hub/Design/colors_and_type.css` (or `~/.claude/skills/626labs-design/colors_and_type.css`) and extract only the CSS custom properties we need for this widget (bg-0/1/2, fg-1/2/3, cyan, magenta, success, warning, danger, border tokens, type tokens, easing). Return as a ready-to-paste `tokens.css` under 80 lines."*

**Effort:** 4-6h. Largest item.

---

### 5. Widget shell + init/destroy + end-to-end playthrough ← CHECKPOINT 2

**Spec ref:** `spec.md > Widget config API` · `spec.md > Data flow — runtime` · `prd.md > Epic 1`

**What to build:**

- `src/Widget.tsx` — root React component. Takes `BaconTrailWidgetConfig` as props. Owns the `useReducer` from item 2. Orchestrates fetches (via `useEffect` side effects) and renders the current-state's component.
- `src/index.tsx` — UMD entry. Exports `window.BaconTrailWidget = { init, destroy }`:
  - `init(config)`: validates `container`, destroys any prior tree on same container (WeakMap lookup), calls `createRoot(container).render(<Widget {...config} />)`.
  - `destroy(container)`: looks up root in WeakMap, calls `root.unmount()`.
- Wire state transitions from user picks into reducer actions. `useEffect` hooks fire the TMDB calls after `ACTOR_PICKED` and `MOVIE_PICKED` actions.
- Bacon check fires inside the `MOVIE_PICKED` → `CAST_LOADED` transition: if `castIncludesBacon(cast)`, dispatch `RESULT(outcome: 'found')`. Skip co-actor screen entirely.
- Film-count enforcement: after `CAST_LOADED` with `!baconInCast && filmCount === 6`, dispatch `RESULT(outcome: 'out-of-films')`.
- Error surfaces: every fetch wraps in try/catch; on failure, dispatch `ERROR(message, retry)` which renders `ErrorCard` in place of the current screen, preserving the state to retry from.

**Acceptance:**

- `pnpm dev` renders a working widget in a standalone test harness (`dev.html` or similar).
- Full manual playthrough: pick actor → pick movie → pick co-actor → pick movie → find Bacon → see result. Works end to end.
- Play Again button works (returns to pick-actor with a fresh random pull from today's shard).
- Film counter advances correctly.
- Trail breadcrumb shows the walk.
- Refresh the page with network offline → shows graceful error card, not a crash.
- Two instances on the same page don't interfere (manual test: mount the widget twice into two different containers; confirm they can play independently).

**Verify (hooks):**

1. Manual playthrough — builder-confirmed, not just agent-confirmed.
2. `pnpm test` — all logic + component tests still green.
3. `pnpm build` — bundle ≤ 150 KB gz (use `gzip-size-cli` or check Vite's output — fail the verify if exceeded).
4. Browser dev-tools Network tab check: widget fires 1 shard fetch + N TMDB calls per round. No unexpected calls (e.g., no Firebase client network traffic).

**CHECKPOINT 2 — pause and summarize to builder before continuing:**

- Widget is functionally complete as a standalone component.
- All 4 screens working, state machine executing cleanly.
- Bundle size under budget.
- Ready to integrate with the hub.

**Parallel research:** spawn Explore subagent: *"Read `~/Projects/QuizShow/apps/widget/src/index.tsx` and `apps/widget/src/Widget.tsx` — how does the CinePerks widget handle init/destroy, and what patterns there are worth matching? Under 200 words."*

**Effort:** 2-3h.

---

### 6. Hub integration — `.play` section

**Spec ref:** `spec.md > Integration with 626labs-hub` · `prd.md > Epic 7`

**What to build:**

- New `content/site.json` block under a top-level `play` key — per `spec.md > content/site.json additions`.
- `scripts/render-hub.py` — add `render_play_section(play: dict) -> str` function that emits the `<section class="play">` HTML between the SITE_JSON markers. Loops over `play.widgets[]` for forward compatibility (so adding CinePerks later is a one-line JSON edit).
- `index.html` — add the `<!-- SITE_JSON:play:start -->` / `<!-- SITE_JSON:play:end -->` markers between the Lab Shelf and the About section. Let the renderer fill them in on the next build.
- `index.html` CSS additions — the `.play-grid` / `.play-widget` rules from `spec.md > Layout CSS additions`.
- **Postbuild shard copy** — add a small post-build step to `apps/widget-bacon-trail/package.json`'s build script: `cp -r data ../../widget-bacon-trail/data` (or equivalent cross-platform; use a `copyfiles` npm util or a Node script). So the widget's fetch URL `/widget-bacon-trail/data/birthdays/MM-DD.json` actually resolves.
- **CSP review** — check hub's current `<meta http-equiv="Content-Security-Policy">` (if any) or the GitHub Pages response headers for CSP. If restrictive, update to allow:
  - `connect-src` includes `https://api.themoviedb.org`
  - `img-src` includes `https://image.tmdb.org`
  - `script-src` stays as-is (widget loads from same-origin)

**Acceptance:**

- `python scripts/render-hub.py` regenerates `index.html` with the new section in place.
- Visiting `http://localhost:<port>/` shows the `<section class="play">` with the widget mounted + playable.
- Mobile-width viewport: widget stacks cleanly, fills width, no horizontal scroll.
- No console errors from CSP violations when the widget calls TMDB.
- `/widget-bacon-trail/data/birthdays/04-23.json` resolves in the browser (confirms the postbuild copy worked).

**Verify (hooks):**

1. `python scripts/render-hub.py` completes without error, diff shows only the new section.
2. `pnpm --filter widget-bacon-trail build` then `ls widget-bacon-trail/data/birthdays/` shows the copied shards at the root.
3. Open the live (or locally-served) hub, scroll to the `.play` section, complete a round.
4. DevTools Network tab: confirm the widget fetches `/widget-bacon-trail/widget.js` + one shard + TMDB calls, no CSP blocks.

**Parallel research:** none critical; hub patterns are well-documented in the render-hub.py file itself.

**Effort:** 2h.

---

### 7. Responsive QA + bundle-size CI gate + E2E smoke ← CHECKPOINT 3

**Spec ref:** `prd.md > Cross-cutting requirements` · `spec.md > Testing approach`

**What to build:**

- CI step in `.github/workflows/` (either a new `widget-bacon-trail-check.yml` or folded into an existing workflow): on any PR that touches `apps/widget-bacon-trail/` or `widget-bacon-trail/`, run:
  - `pnpm install`
  - `pnpm build`
  - `gzip-size widget-bacon-trail/widget.js` — fail if > 150 KB
  - `gzip-size widget-bacon-trail/widget.css` — fail if > 20 KB
  - `pnpm test` — all tests pass
- **Responsive QA** — manual pass on three device classes:
  - Mobile: iPhone 14 Pro viewport (375 × 812). Widget stacks, fills width.
  - Tablet: iPad viewport (768 × 1024). Widget renders at 400 × 600.
  - Desktop: 1440 × 900. Widget renders at 400 × 600, section is centered.
- **Accessibility sweep** — one manual a11y pass using the browser's accessibility devtool:
  - All interactive elements tab-reachable.
  - Focus ring visible (cyan).
  - Screen-reader live region announces film picks and result (run VoiceOver or NVDA one playthrough).
  - Color contrast on all text ≥ WCAG AA.
- **Lighthouse run** on the hub with the widget mounted. Perf score drop ≤ 5 points from current baseline (~90).

**Acceptance:**

- CI gate lands green. Bundle sizes recorded in the workflow summary.
- Responsive screenshots at 3 breakpoints captured and linked in the item's commit message.
- A11y sweep passes (no contrast violations, keyboard-nav works, screen-reader announcements fire).
- Lighthouse perf delta ≤ 5 points.

**Verify (hooks):**

1. CI run on PR shows bundle size ≤ 150 KB gz + ≤ 20 KB gz.
2. Screenshots attached or linked.
3. Lighthouse-CLI output attached or linked.

**CHECKPOINT 3 — pause and summarize to builder before continuing:**

- Widget works across mobile / tablet / desktop.
- Bundle under budget, gated in CI.
- A11y basics pass.
- Only documentation + security verification remains.

**Parallel research:** spawn Explore subagent: *"Run Lighthouse against `626labs.dev/` (pre-widget-embed baseline) and report perf/accessibility/SEO scores. We'll diff against the post-embed score in item 7."*

**Effort:** 2h.

---

### 8. Documentation & Security Verification

**Spec ref:** `spec.md > Security considerations` · mandatory per Cart's checklist pattern

**What to build:**

- `apps/widget-bacon-trail/README.md` — integration guide patterned on `apps/widget/INTEGRATION.md`. Covers: what the widget does, config API, embed snippet, local dev, build, deploy. Under 300 lines.
- `apps/widget-bacon-trail/CONTRIBUTING.md` — short, states "single-maintainer for now" + how to run locally.
- `apps/widget-bacon-trail/SECURITY.md` — two sections: (1) widget's security posture — zero PII collected, zero Firestore at runtime, TMDB key is read-only + rotatable, (2) how to report vulnerabilities.
- `apps/widget-bacon-trail/PRIVACY.md` — short. No user data, no cookies, no localStorage, no analytics in v1.
- `apps/widget-bacon-trail/CHANGELOG.md` — Keep-a-Changelog format. v0.1.0 entry with today's date.
- `apps/widget-bacon-trail/LICENSE` — MIT (matches the rest of the builder's public work).
- **Docs cleanup** — make sure scope.md, prd.md, spec.md, checklist.md are internally consistent. Patch any stale references.
- **Secrets scan**:
  - `git ls-files | xargs grep -l 'AIzaSy\|firebase_private_key\|FIREBASE_SA_JSON\|service_account'` → must return nothing except documentation references with example values.
  - `git log -p apps/widget-bacon-trail/` → scan for accidentally-committed secrets in history.
  - Confirm `.gitignore` covers `.env`, `.env.local`, `/tmp`, service-account JSON patterns.
- **Dependency audit**:
  - `pnpm audit --prod` → zero high/critical vulnerabilities.
  - `pnpm outdated` → note any drifts; don't chase minors in this pass.
- **Deployment security**:
  - GitHub Pages serves the widget — confirm HTTPS-only (default).
  - CSP on hub includes widget origins if applicable.
  - GitHub Actions secret `FIREBASE_SA_JSON` is scoped to `contents: write` permission only; no broader access.
  - The service account itself has Cloud Datastore User (read-only) only; no write role.

**Acceptance:**

- All docs exist and are accurate.
- Secrets scan returns clean.
- `pnpm audit --prod` shows no high/critical.
- README's embed snippet matches the actual init call in `index.html`.
- `git diff` between checklist items 1-7 is an auditable trail — every commit has a meaningful message.

**Verify (hooks):**

1. `cat apps/widget-bacon-trail/README.md | head -40` — opening is the tagline + one-paragraph summary + embed snippet.
2. Grep patterns above all return clean.
3. `pnpm audit --prod` exit code 0.
4. Service-account-JSON is **not** in any committed file.

**Parallel research:** none needed.

**Effort:** 1-2h.

---

## Effort summary

| Item | Title | Effort | Cumulative |
|---|---|---|---|
| 1 | Scaffold + env + credentials | 1-2h | 1-2h |
| 2 | Types + reducer + services | 2-3h | 3-5h |
| 3 | Shard pipeline + seed ← CP1 | 1-2h | 4-7h |
| 4 | Components + design treatment | 4-6h | 8-13h |
| 5 | Shell + init + playthrough ← CP2 | 2-3h | 10-16h |
| 6 | Hub integration | 2h | 12-18h |
| 7 | Responsive + CI + a11y ← CP3 | 2h | 14-20h |
| 8 | Docs + security verification | 1-2h | 15-22h |

**Total estimate: 15-22 hours wall-clock**, across as many sessions as Este wants. Autonomous between checkpoints.

## Dependencies graph

```
    1 (scaffold)
     │
     ├──▶ 2 (types + services)
     │        │
     │        └──▶ 4 (components)
     │                 │
     └──▶ 3 (shards) ──▶ 5 (shell + playthrough) ←── CP2
                                │
                                └──▶ 6 (hub integration)
                                          │
                                          └──▶ 7 (QA + CI) ←── CP3
                                                    │
                                                    └──▶ 8 (docs + security)
```

Items 2 and 3 can run in parallel after item 1 finishes — they have no mutual dependency. Every other item is gated on its listed prerequisites.

## When to spawn parallel agents

Per builder's `/onboard` preference: parallel Explore agents for independent research. Items 2, 3, 4, 5, and 7 each have a specific `Parallel research:` block naming what to spawn. Pattern: kick off the Explore agent first, continue implementation in main session while it runs, absorb results at the next context-switch point.

## When to hand off to a different agent

Per builder profile: handoff is a neutral tool, not a failure. Indicators to consider a handoff:
- Two consecutive failed attempts at the same diagnostic step (item 5 bundle-size failures, item 6 CSP debugging).
- An opaque failure where the agent's hypothesis keeps shifting without evidence.
- Checkpoint review reveals the agent has drifted from spec decisions.

Not indicators to hand off: verification failures that simply need fixing (fix them), one round of "huh, that's weird" from the agent (let it debug).

## Closing note

Spec is self-contained; no external architecture docs were needed. All four questions in `/prd` were resolved during `/spec`. Build can run from here without re-asking the builder unless a genuinely new load-bearing decision surfaces (at which point: raise it at the next checkpoint, not mid-item).
