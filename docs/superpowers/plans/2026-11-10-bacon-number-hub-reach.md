# Bacon number hub reach Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Precompute whether each birthday actor's stored Bacon number is reachable under the hub widget's rules, carry that onto the shards as `hubReachable`, and have the result card say "(path not available here)" plus an invite to the full game at wsyatm.626labs.dev.

**Architecture:** A pure Node module (`scripts/hub-reach-lib.mjs`) holds the hub's ranking rules, a memoized depth-limited route search over injected TMDB getters, and the cache freshness rules. A weekly CLI (`scripts/refresh-hub-reach.mjs`) drives it against live TMDB with pacing and a budget and writes `widget-bacon-trail/data/hub-reach.json`. The nightly shard refresh merges that cache into each shard actor. The widget reads one more field and picks its copy.

**Tech Stack:** Node 20 ESM, `node:test`, pytest (CI gate) wrapping node tests, GitHub Actions, Vite + React + TS + vitest in the widget.

**Spec:** `docs/superpowers/specs/2026-11-10-bacon-number-hub-reach-design.md`

## Global Constraints

- Hub rules, mirrored exactly from `apps/widget-bacon-trail/src/services/tmdbService.ts`: an actor's films are `person/{id}/movie_credits` `cast`, scored `(popularity ?? 0) * Math.log(1 + Math.max(0, vote_count ?? 0))`, sorted desc, first 45. A film's cast is `movie/{id}/credits` `cast` sorted by `order` asc (missing order = `Number.MAX_SAFE_INTEGER`), first 27. Kevin Bacon is TMDB `4724`.
- The question per actor is only: a hub route with at most `stored` films? Search depth is bounded by `stored` (1, 2 or 3 today).
- Cache file: `widget-bacon-trail/data/hub-reach.json`, shape `{ "<actorId>": { "stored": 2, "reachable": true, "checkedAt": "YYYY-MM-DD" } }`, keys sorted numerically ascending, 2-space JSON, one trailing newline.
- Staleness: an entry is stale when missing, when `entry.stored !== stored`, or when `reachable === false` and `checkedAt` is more than 28 days before today. A stale entry merges as unknown (field absent). `reachable: true` never expires on age.
- Recheck order each run: unchecked, then stored-number changed, then oldest `false`.
- Unknown means no claim: no caveat, light invite.
- Copy (exact): light invite `Having fun? Play the full game at wsyatm.626labs.dev.`; full-game invite `The full game has more films and fuller casts. Sign up at wsyatm.626labs.dev.`; caveat appended to the Bacon line as ` (path not available here)` before the final period: `Maya Hawke has a Bacon number of 2 (path not available here).` The domain text in both invites is the link, to `https://wsyatm.626labs.dev/bacon-trail`.
- Reuse `VITE_TMDB_API_KEY` (already a repo secret). No new secrets.
- Voice: sentence case, no emoji, periods at the end.
- Never commit a locally built widget bundle; `build-widget.yml` owns `widget-bacon-trail/*.js|css`.
- **Task 5 merges only after** `https://wsyatm.626labs.dev/bacon-trail` loads with a valid cert and signup works there. Tasks 1-4 may merge anytime.

## Review Focus

1. **The job hasn't run yet, or never reached an actor.** Expected: shard has no `hubReachable`, card shows the plain line and the light invite. Pinned in Task 4 (merge with empty cache) and Task 5 (`hubReachable` undefined).
2. **Cache says unreachable but the player wins at exactly the stored number.** The player just proved a route exists. Expected: "That's the shortest route.", no caveat, light invite. Pinned in Task 5.
3. **TMDB 404 for a deleted person or film.** Expected: treated as no films / no cast, the search continues, the job doesn't crash. Pinned in Task 3.
4. **Budget runs out mid-actor.** Expected: that actor is left as it was in the cache (not written as `false`), everything finished earlier is written. Pinned in Task 1 (search throws `BudgetExceeded`) and Task 3 (CLI keeps prior entry).
5. **Cache file missing or malformed on the nightly shard run.** Expected: every actor merges as unknown, the nightly run still writes shards and exits 0. Pinned in Task 4.

---

### Task 1: Hub ranking rules and route search

**Files:**
- Create: `scripts/hub-reach-lib.mjs`
- Create: `scripts/hub-reach-lib.test.mjs`
- Create: `tests/test_hub_reach.py`

**Interfaces:**
- Produces:
  - `KEVIN_BACON_ID = 4724`, `FILMS_PER_ACTOR = 45`, `CAST_PER_FILM = 27`
  - `topFilms(creditsCast: Array<{id, popularity?, vote_count?}>): number[]` film ids, hub order
  - `topCast(movieCast: Array<{id, order?}>): number[]` actor ids, hub order
  - `class BudgetExceeded extends Error`
  - `createSearch({ getFilms: (actorId) => Promise<number[]>, getCast: (movieId) => Promise<number[]> }): { reachableWithin(actorId: number, maxFilms: number): Promise<boolean> }`. Getters already apply `topFilms`/`topCast`; the search memoizes getter results and `(actorId, k)` answers for the life of the search object. Getter errors (including `BudgetExceeded`) propagate.

- [ ] **Step 1: Write the failing tests** in `scripts/hub-reach-lib.test.mjs` (`// Run: node --test scripts/hub-reach-lib.test.mjs`, same style as `scripts/store-series.test.mjs`). Use an in-memory fixture graph: `films = { A: [10, 11], B: [12], C: [13] }`, `cast = { 10: [A, B], 11: [A], 12: [B, C], 13: [C, 4724] }` with numeric ids.
  - `topFilms ranks by popularity*ln(1+votes) and keeps 45`: 50 entries, assert length 45 and that an entry with popularity 100, vote_count 0 ranks below popularity 2, vote_count 1000.
  - `topCast sorts by order, missing order last, keeps 27`: 30 entries with shuffled orders and two missing; assert first id is order 0, the two missing are dropped past 27.
  - `direct route is 1 film`: `reachableWithin(C, 1) === true`.
  - `route length is bounded by maxFilms`: `reachableWithin(B, 1) === false`, `reachableWithin(B, 2) === true`, `reachableWithin(A, 2) === false`, `reachableWithin(A, 3) === true`.
  - `memoizes getter calls`: count getter calls; two `reachableWithin(A, 3)` calls hit each film/actor getter at most once.
  - `a getter error propagates`: getter throws `new BudgetExceeded()`; `reachableWithin` rejects with `BudgetExceeded`.
- [ ] **Step 2: Run to verify fail.** `node --test scripts/hub-reach-lib.test.mjs` → FAIL, module not found.
- [ ] **Step 3: Implement** in `scripts/hub-reach-lib.mjs`. `topFilms`/`topCast` copy the widget's sort exactly (constraints). Search algorithm (the part the tests don't fully determine):

```js
// reachableWithin(a, k): some film f in films(a) has 4724 in cast(f)  (k >= 1),
// or (k >= 2) some c in cast(f), c !== a, has reachableWithin(c, k - 1).
// Check every film for a direct hit before recursing into any co-actor
// (iterative-deepening order keeps shallow answers cheap).
// Memo: Map key `${a}:${k}`. A true at k implies true at every k' >= k;
// a false at k implies false at every k' <= k. Consult both directions.
```

- [ ] **Step 4: Write the pytest wrapper** `tests/test_hub_reach.py`: skip if `shutil.which("node") is None` (pattern: `tests/test_asset_kind.py`); run `node --test scripts/hub-reach-lib.test.mjs` from repo root, assert `returncode == 0`, print stdout on failure.
- [ ] **Step 5: Run.** `node --test scripts/hub-reach-lib.test.mjs` → all pass; `python -m pytest tests/test_hub_reach.py -q` → passed.
- [ ] **Step 6: Commit.** `git add scripts/hub-reach-lib.mjs scripts/hub-reach-lib.test.mjs tests/test_hub_reach.py && git commit -m "feat(bacon-reach): the hub's ranking rules and a bounded route search"`

### Task 2: Cache freshness, queue and merge rules

**Files:**
- Modify: `scripts/hub-reach-lib.mjs`
- Modify: `scripts/hub-reach-lib.test.mjs`

**Interfaces:**
- Consumes: nothing from Task 1 beyond the module.
- Produces:
  - `FALSE_MAX_AGE_DAYS = 28`
  - `isFresh(entry: {stored, reachable, checkedAt} | undefined, stored: number, today: string): boolean`
  - `hubReachableFor(actor: {id, baconNumber?}, cache: object, today: string): boolean | undefined` — `undefined` when `baconNumber` isn't an integer ≥ 1, or the entry isn't fresh; else `entry.reachable`.
  - `buildQueue(actors: Array<{id, baconNumber?}>, cache: object, today: string): Array<{id, stored}>` — only actors with integer `baconNumber >= 1` whose entry isn't fresh; order: no entry, then `entry.stored !== stored`, then stale `false` by `checkedAt` ascending; ties by `stored` ascending then id. Dedupe ids.
  - `serializeCache(cache: object): string` — numeric-ascending keys, entry key order `stored, reachable, checkedAt`, 2-space, trailing `\n`.

- [ ] **Step 1: Write failing tests:**
  - `fresh true never expires`: `{stored:2, reachable:true, checkedAt:'2025-01-01'}`, stored 2, today `2026-11-10` → `true`.
  - `false expires after 28 days`: checkedAt `2026-10-13` (28 days) → fresh; `2026-10-12` (29 days) → not fresh.
  - `stored change makes an entry stale`: entry stored 3, current 2 → not fresh.
  - `hubReachableFor returns undefined for Kevin (0), no number, or stale`; returns `false` for a fresh false.
  - `buildQueue order`: actors with ids 1..5, all stored 2 except where noted, today `2026-11-10`: 1 has no entry, 2 has stored mismatch, 3 a stale false checked `2026-09-01`, 4 a stale false checked `2026-08-01`, 5 a fresh true → `[1, 2, 4, 3]`.
  - `serializeCache sorts keys numerically`: keys `"10","9"` → `"9"` first; ends with `"}\n"`.
- [ ] **Step 2: Run to verify fail.** `node --test scripts/hub-reach-lib.test.mjs` → new tests FAIL.
- [ ] **Step 3: Implement** the four functions. Dates are `YYYY-MM-DD` UTC strings; compute age with `Date.UTC` on the parts, not local time.
- [ ] **Step 4: Run.** `node --test scripts/hub-reach-lib.test.mjs` → pass; `python -m pytest tests/test_hub_reach.py -q` → passed.
- [ ] **Step 5: Commit.** `git commit -am "feat(bacon-reach): cache freshness, recheck queue and merge rules"`

### Task 3: The weekly reach job

**Files:**
- Create: `scripts/refresh-hub-reach.mjs`
- Create: `scripts/refresh-hub-reach.test.mjs`
- Modify: `tests/test_hub_reach.py` (also run the new test file)
- Create: `.github/workflows/refresh-hub-reach.yml`
- Modify: `CLAUDE.md` (CI table row, counts: "18 files: 13 bot workflows" → 19/14, "The 13 bot workflows" → 14, "All thirteen" → "All fourteen")

**Interfaces:**
- Consumes: `topFilms`, `topCast`, `createSearch`, `BudgetExceeded`, `buildQueue`, `serializeCache` (Tasks 1-2).
- Produces:
  - `createTmdb({ apiKey, fetchImpl = fetch, minIntervalMs = 30, maxCalls = Infinity, sleep }): { getFilms, getCast, calls() }` — paces requests at least `minIntervalMs` apart; on 429 or 5xx retries up to 4 times with backoff (honor `Retry-After` seconds when present); on 404 returns `[]`; every attempt counts toward `maxCalls`, and the call that would exceed it throws `BudgetExceeded` before fetching.
  - `run({ shardDir, cachePath, today, tmdb, deadline: number /* epoch ms */, perActorMaxCalls = 20000, log = console.log }): Promise<{ checked, reachable, unreachable, skipped }>` — loads shards and cache (missing cache = `{}`), builds the queue, and for each actor runs `reachableWithin(id, stored)` on a fresh `createSearch` whose getters share one run-wide response cache; writes `{stored, reachable, checkedAt: today}` on an answer; on `BudgetExceeded` from the per-actor cap, leaves that actor's prior entry untouched and continues; stops the loop when `Date.now() > deadline` or the run-wide cap trips. Writes the cache with `serializeCache` once at the end (and after every 25 answers, so a killed job keeps its progress).
  - CLI: `node scripts/refresh-hub-reach.mjs [--max-minutes 330] [--max-calls N] [--only <id,id>]`; reads `VITE_TMDB_API_KEY`; shard dir `apps/widget-bacon-trail/data/birthdays`; cache `widget-bacon-trail/data/hub-reach.json`; exits 1 with a clear message if the key is missing.

- [ ] **Step 1: Write failing tests** in `scripts/refresh-hub-reach.test.mjs` with a fake `fetchImpl` serving the Task 1 fixture graph as TMDB-shaped JSON and a no-op `sleep`:
  - `404 reads as empty`: person 99 returns 404 → `getFilms(99)` resolves `[]`.
  - `429 retries then succeeds`: first response 429 with `Retry-After: 1`, second 200 → resolves; `calls() === 2`.
  - `maxCalls throws BudgetExceeded before fetching`: `maxCalls: 1`, second call rejects with `BudgetExceeded`, fake fetch saw 1 request.
  - `run writes answers and keeps an over-budget actor's prior entry`: temp dir with one shard holding actors C (stored 1), A (stored 3), cache has A as `{stored:3, reachable:false, checkedAt:'2026-01-01'}`; `perActorMaxCalls: 3` so A trips the cap → cache after run has C `{stored:1, reachable:true, checkedAt:today}` and A unchanged.
  - `run treats a missing cache file as empty`.
- [ ] **Step 2: Run to verify fail.** `node --test scripts/refresh-hub-reach.test.mjs` → FAIL.
- [ ] **Step 3: Implement** `createTmdb`, `run`, and the CLI guard (`if (import.meta.url === pathToFileURL(process.argv[1]).href)`). Per-actor cap: wrap the shared getters in a counter that throws `BudgetExceeded` past `perActorMaxCalls` *uncached* calls for the current actor. Log one line per actor: `id stored -> reachable|unreachable|over-budget`, and a summary.
- [ ] **Step 4: Add the test file to the pytest wrapper**; run `python -m pytest tests/test_hub_reach.py -q` → passed.
- [ ] **Step 5: Write `.github/workflows/refresh-hub-reach.yml`**: `schedule: cron '30 8 * * 0'` (Sundays 08:30 UTC) + `workflow_dispatch` with optional `max_minutes` (default `330`); `concurrency: refresh-hub-reach`; `timeout-minutes: 350`; `if: github.actor != 'github-actions[bot]'`; `permissions: contents: write`; Node 20; `env: VITE_TMDB_API_KEY: ${{ secrets.VITE_TMDB_API_KEY }}`; run the CLI with `--max-minutes`; commit only `widget-bacon-trail/data/hub-reach.json` as `chore(bacon-reach): refresh $(date -u +%Y-%m-%d)` using the exact retry+rebase loop from `refresh-bacon-shards.yml`. No `pull_request` trigger.
- [ ] **Step 6: Local smoke run** (needs a TMDB key in env): `node scripts/refresh-hub-reach.mjs --only 1903874,4175 --max-minutes 5` → two log lines with answers and a cache file containing both ids. Do **not** commit the smoke cache; delete it (`git checkout -- widget-bacon-trail/data/hub-reach.json` or remove if new). Record the call counts in the PR body: they are the first real budget data.
- [ ] **Step 7: Update `CLAUDE.md`**: add the CI table row (weekly Sun 08:30 UTC, reads shards + TMDB, writes `widget-bacon-trail/data/hub-reach.json`, reuses `VITE_TMDB_API_KEY`, budgeted and resumable, a `false` older than 28 days merges as unknown) and fix the three counts named in Files.
- [ ] **Step 8: Commit.** `git add scripts/refresh-hub-reach.mjs scripts/refresh-hub-reach.test.mjs tests/test_hub_reach.py .github/workflows/refresh-hub-reach.yml CLAUDE.md && git commit -m "feat(bacon-reach): weekly job checks each actor's number against the hub's rules"`

### Task 4: Shards carry `hubReachable`

**Files:**
- Modify: `scripts/refresh-bacon-shards.mjs`
- Modify: `scripts/hub-reach-lib.mjs`, `scripts/hub-reach-lib.test.mjs`

**Interfaces:**
- Consumes: `hubReachableFor` (Task 2).
- Produces:
  - `loadCache(cachePath: string): Promise<object>` in `hub-reach-lib.mjs` — returns `{}` and `console.warn`s on a missing file, unreadable file, invalid JSON, or a non-object top level. Never throws.
  - Shard actor objects gain `hubReachable: boolean` only when `hubReachableFor` returns a boolean; the key is omitted otherwise (keeps diffs small and "absent = unknown").

- [ ] **Step 1: Write failing tests:** `loadCache returns {} for a missing file`, `for "not json"`, `for "[]"`; returns the object for a valid file.
- [ ] **Step 2: Run to verify fail.** `node --test scripts/hub-reach-lib.test.mjs` → FAIL.
- [ ] **Step 3: Implement `loadCache`**, then in `refresh-bacon-shards.mjs` load `widget-bacon-trail/data/hub-reach.json` once before grouping, compute `today` as the UTC date, and set `actor.hubReachable` from `hubReachableFor(actor, cache, today)` when it's a boolean. Place the key last in the actor object.
- [ ] **Step 4: Run.** `node --test scripts/hub-reach-lib.test.mjs` → pass; `python -m pytest tests/test_hub_reach.py -q` → passed. `node --check scripts/refresh-bacon-shards.mjs` → no output.
- [ ] **Step 5: Commit.** `git commit -am "feat(bacon-shards): merge hub reachability into each shard actor"`

### Task 5: The card says it (merge only after the domain serves)

**Files:**
- Modify: `apps/widget-bacon-trail/src/types.ts` (`Actor.hubReachable?: boolean`; `export const FULL_GAME_URL = 'https://wsyatm.626labs.dev/bacon-trail'`)
- Modify: `apps/widget-bacon-trail/src/lib/baconNumber.ts`
- Modify: `apps/widget-bacon-trail/src/components/ResultCard.tsx`
- Modify: `apps/widget-bacon-trail/src/styles/widget.css`
- Modify: `apps/widget-bacon-trail/src/__tests__/baconNumber.test.ts`, `src/__tests__/components.test.tsx`
- Modify: `apps/widget-bacon-trail/CHANGELOG.md` (0.5.0), `package.json` version `0.5.0`

**Interfaces:**
- Consumes: shard `hubReachable` (Task 4); existing `displayBaconNumber`.
- Produces: `displayBaconNumber({ stored, won, steps, hubReachable?: boolean }): { baconNumber: number | null; shortestRoute: boolean; notHere: boolean }`. `notHere` is true only when `baconNumber !== null`, `hubReachable === false`, and the player did not reach `steps <= stored` on a win (a win at or under the stored number proves a route).

- [ ] **Step 1: Write failing rule tests** in `baconNumber.test.ts`:
  - `notHere on a loss when unreachable`: `{stored:2, won:false, steps:6, hubReachable:false}` → `{baconNumber:2, shortestRoute:false, notHere:true}`.
  - `notHere on a longer win when unreachable`: `{stored:2, won:true, steps:4, hubReachable:false}` → `notHere:true`.
  - `a win at the stored number overrides the cache`: `{stored:2, won:true, steps:2, hubReachable:false}` → `{baconNumber:2, shortestRoute:true, notHere:false}`.
  - `unknown reach makes no claim`: `hubReachable` undefined, loss → `notHere:false`.
  - `no number, no caveat`: `stored` undefined, `hubReachable:false` → `{baconNumber:null, shortestRoute:false, notHere:false}`.
  - Update the five existing expectations to include `notHere:false`.
- [ ] **Step 2: Write failing card tests** in `components.test.tsx` (extend the "Bacon number line" describe; give the start actor a `hubReachable` param):
  - `unreachable loss shows the caveat and the full-game invite`: line text `Maya Hawke has a Bacon number of 2 (path not available here).`; `getByTestId('bacon-invite')` text `The full game has more films and fuller casts. Sign up at wsyatm.626labs.dev.`; the link `getByRole('link', { name: 'wsyatm.626labs.dev' })` has `href` `https://wsyatm.626labs.dev/bacon-trail`.
  - `reachable win shows the light invite`: invite text `Having fun? Play the full game at wsyatm.626labs.dev.`; no `(path not available here)` anywhere.
  - `no number still shows the light invite`.
  - `the birthday card shows the light invite`.
- [ ] **Step 3: Run to verify fail.** `cd apps/widget-bacon-trail && npx vitest run` → new tests FAIL.
- [ ] **Step 4: Implement.** Rule per the Interfaces block. In `ResultCard`, pass `hubReachable: start.hubReachable`; render the caveat inside the existing line (`{name} has a Bacon number of {n}{notHere ? ' (path not available here)' : ''}.`); render one `<p className="btw-result-invite" data-testid="bacon-invite">` after the Bacon line (and on the birthday card after its sub line), with only the domain text as the `<a href={FULL_GAME_URL}>`. CSS: `.btw-result-invite` reuses `.btw-result-sub` metrics; its link uses the widget's existing link color token, underline on hover only if that's the existing pattern in `widget.css`.
- [ ] **Step 5: Run.** `npx vitest run` → all pass; `npx tsc --noEmit -p .` → exit 0.
- [ ] **Step 6: Changelog + version** (0.5.0: the caveat, both invites, where `hubReachable` comes from). Commit: `git add apps/widget-bacon-trail && git commit -m "feat(bacon-trail): say when the true route isn't walkable here, and invite to the full game"`
- [ ] **Step 7: Gate before merge.** `curl -sS -o /dev/null -w "%{http_code}\n" https://wsyatm.626labs.dev/bacon-trail` → `200` (or a 3xx to `/login` on the same host) with no TLS error, and a manual signup check on the domain. Until both hold, the PR stays open with this step unchecked.

## After merge (operational, not code)

- Dispatch `refresh-hub-reach.yml` once for the backfill; expect more than one window to cover all 4,922 numbered actors. Check the summary line for the over-budget count; if most depth-3 actors land over budget, that's expected (they stay unknown) and not a bug.
- The next nightly shard run carries `hubReachable` into the shards; spot-check `widget-bacon-trail/data/birthdays/07-08.json`.
