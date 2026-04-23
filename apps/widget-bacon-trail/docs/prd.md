# PRD — Birthday Bacon Trail Widget

## Summary

A ~400×600 embeddable React widget that runs a stripped version of the Birthday Bacon Trail game: pick-birthday-actor → pick-movie (win if Bacon is in cast) → pick-co-actor → loop until a film with Bacon is picked, or 6 films walked → result. Ships as a Vite-built bundle inside the `626labs-hub` repo at `apps/widget-bacon-trail/`. Embeds on 626labs.dev as the single widget in a new `<section class="play">` on the hub. A future ship will bring the CinePerks movie trivia widget in alongside it.

Anchor: [`docs/scope.md`](./scope.md) — the full scope with load-bearing decisions resolved.

---

## Users and stories

### P1 — Portfolio visitor *(primary)*

Arrives at 626labs.dev from a Vibe plugin README, a Product Hunt launch referral, a LinkedIn post, or a Reddit thread. Has 30 seconds to form an impression. Wants to feel the work, not just read about it.

- **Story P1.1** — As a portfolio visitor, I want to see today's Kevin Bacon birthday actors already loaded when I land on the widget, so I can start playing within one click of scrolling to it.
- **Story P1.2** — As a portfolio visitor, I want the widget to respond immediately to my picks, so I don't feel like I'm waiting on a backend while playing a casual game.
- **Story P1.3** — As a portfolio visitor, I want the widget to show me a clean result card when I find Bacon (or don't), so the round has a satisfying close before I move on.
- **Story P1.4** — As a portfolio visitor, I want a clear "there's more like this" CTA at the end of a round, so I can follow my interest into the full Lobby Engagement Suite if the widget hooked me.

### P2 — Builder *(secondary)*

The hub's author. Using the widget as public proof that the Lobby Engagement Suite is production-ready.

- **Story P2.1** — As the builder, I want the widget to run for 24+ hours without ops attention so it's trustworthy as a portfolio surface.
- **Story P2.2** — As the builder, I want the data pipeline to be visible and auditable in the repo (shards, GitHub Action logs, workflow file) so I can answer "how does this stay fresh?" at a glance.
- **Story P2.3** — As the builder, I want the embed contract for this widget to be reusable, so the next three Lobby Engagement Suite games (Reel Battles, Reel Words, Heads Up) plug in with config changes, not copy-paste.

### P3 — Explicit non-users

- **Theater / hotel customers.** Their widget is CinePerks Trivia (the sibling in `apps/widget/`). No rewards flow, no signup, no memberId pattern on this widget.
- **Competitive multiplayer players.** Live multiplayer is a different product.
- **Kid-filtered audiences.** Deferred to v2 per scope.

---

## Epic 1 — Widget shell + embed contract [MUST-HAVE]

The outer frame: config-via-props, single `init()` entry point, container-div mounting, unmount/teardown hygiene.

### User stories

- **1.1** — As the builder, I want to embed the widget with a single script tag + `init({ container, ...config })` call, matching the CinePerks widget's API, so the hub's `index.html` gains a play surface with three lines of HTML.
- **1.2** — As the builder, I want the widget to cleanly unmount if its container is removed from the DOM, so SPA navigation on future hub redesigns doesn't leak listeners or memory.

### Acceptance criteria

- `widget.js` exports a global `BaconTrailWidget.init(config)` function that mounts a React tree into `config.container`.
- Config API surface: `{ container, theme?, brandColor?, brandLogo?, ctaUrl?, ctaLabel?, firebaseConfig?: null }` — but `firebaseConfig` is intentionally **never used** in v1 (we load static shards, not Firestore); it's in the API only for forward compatibility with shared widget shell patterns.
- Defaults if no config passed: `theme='dark'`, `brandColor='#17d4fa'`, `ctaUrl='/#work'`, `ctaLabel='See the full suite →'`.
- `BaconTrailWidget.destroy(container)` unmounts the tree cleanly and removes any global listeners the widget added.
- Bundle loads with a single `<script>` tag; no ES module imports required on the consumer's side.
- Shares no global mutable state with the CinePerks widget (so both can coexist on the hub page without interfering).

### Edge cases

- Container is not in the DOM at call time → log a warning, no-op, don't throw.
- `init()` called twice with the same container → destroy the previous tree, mount fresh.
- `theme='light'` requested → v1 renders dark anyway (light theme is a later item); log a one-line info-level note to console.

---

## Epic 2 — Birthday actor pick screen [MUST-HAVE]

The first screen. Loads today's birthday actors from the static shard, displays a grid of 6 picks, lets the user shuffle or select.

### User stories

- **2.1** — As the visitor, I want to see 6 actor faces with names and years, picked from today's birthdays, so the game immediately feels *topical* rather than generic.
- **2.2** — As the visitor, I want a "Different actors" shuffle button if none of the initial 6 interest me, so I have agency before I commit to a round.

### Acceptance criteria

- On mount, fetches `/apps/widget-bacon-trail/data/birthdays/MM-DD.json` (where `MM-DD` is today's date in the user's local time zone).
- Renders 6 actors in a 3×2 grid, each card showing: profile image (from TMDB), name, birth year.
- Actors are sorted by `popularity` descending; actors with known `baconNumber` ≤ 6 are preferred (matches `actorService.ts` logic in the full game).
- If the day's shard has ≥ 7 actors, a "Different actors" button appears that reshuffles to the next 6 in the pool.
- If the day's shard has < 6 actors, fall back to showing "Popular birthdays this week" (pull shards for ±3 days) or show fewer cards gracefully.
- Selecting an actor advances to Epic 3's screen with a transition ≤ 220ms (per brand motion tokens).
- Trail breadcrumb at the top of the widget starts empty.

### Edge cases

- Shard fetch fails (network error, 404, malformed JSON) → show an inline error card with *"Couldn't load today's Kevin Bacon lineup. Try again?"* and a retry button. Do not crash the widget.
- User is in a time zone where "today" has zero birthday actors in the DB (rare — most days have 15-30) → fall back to the ±3-day pool.
- Actor's profile image fails to load → show an initials avatar placeholder (2-letter initials on a navy background with cyan border).
- User rapidly clicks multiple actors → debounce; only the first click advances, subsequent clicks ignored until the transition completes.

---

## Epic 3 — Movie pick screen + win check [MUST-HAVE]

The branching screen. Shows the selected actor's top movies, lets the user pick one. **This is where the win condition fires**: picking a movie whose cast includes Kevin Bacon triggers the win — no need to pick Bacon manually from the cast. Degrees are counted in **films**, not actor/movie pairs.

### User stories

- **3.1** — As the visitor, I want to see a scrollable list of the actor's top ~20 movies with posters, so I can pick one I recognize or one that looks like a Bacon connector.
- **3.2** — As the visitor, I want the current film count visible at the top so I know how many films I have left before the round ends.
- **3.3** — As the visitor, when I pick a movie that turns out to have Bacon in its cast, I want the widget to recognize the win immediately — I picked that movie *for a reason*, I shouldn't have to then also manually pick Bacon from a grid to confirm it.

### Acceptance criteria

- On mount, fetches `/person/{actorId}/movie_credits` from TMDB (reusing `tmdbService.ts` pattern from the full game).
- Renders the actor's `cast` movies, sorted by `popularity` descending, showing top 20.
- Each card shows: poster, title, release year.
- Film counter reads *"Film N / 6"* where N is the number of films that will be used if this pick is made — i.e., on the actor-pick screen it shows the *next* film's index.
- On movie selection:
  - Increment film counter: N → N + 1.
  - Fetch `/movie/{movieId}/credits` from TMDB.
  - Add the movie to the trail breadcrumb.
  - **Check cast for Kevin Bacon (TMDB id `4724`).** If present: transition directly to Epic 5 with `outcome='found'` and `filmCount=N`. Skip Epic 4 entirely.
  - If Bacon is *not* in cast: advance to Epic 4 (co-actor pick) with the fetched cast.
- Transition to Epic 4 or Epic 5: ≤ 220 ms per brand motion.
- Loading state during `movie_credits` + `movie/{id}/credits` double-fetch: skeleton cards, **not** a spinner.

### Edge cases

- TMDB `person/{id}/movie_credits` fetch fails → error card with retry; preserves the selected actor so retrying doesn't re-pick.
- TMDB `movie/{id}/credits` fetch fails (after user picks) → error card with retry on the movie selection; trail breadcrumb doesn't advance until cast is fetched.
- Actor has < 20 movies → render fewer cards without padding.
- Actor has 0 movies in TMDB credits (rare but possible for obscure entries) → "Oops, no films we can trace from this actor. [Pick someone else]" with a back button.
- Movie has no poster → show a navy card with the title in Space Grotesk centered.
- User's film counter is already at 6 when this screen renders → the 6th movie pick is the last chance; if its cast doesn't have Bacon, transition to Epic 5 with `outcome='out-of-films'`.

---

## Epic 4 — Co-actor pick screen [MUST-HAVE]

Shown only when Epic 3's movie selection did *not* include Kevin Bacon in cast. Reveals the film's top cast so the user can pick a co-actor whose next film will continue the chain. **No win condition fires here** — Bacon is known to not be in this cast (already checked in Epic 3).

### User stories

- **4.1** — As the visitor, I want to see the top 15 cast members of the movie I picked, with their faces, so I can recognize someone whose filmography might lead to Bacon.
- **4.2** — As the visitor, I want the picked co-actor to be disabled in future rounds (can't pick the same actor twice) so the chain has forward progress.

### Acceptance criteria

- Receives cast data from Epic 3's pre-fetch (no re-fetch needed).
- Renders the top 15 cast members by billing order, showing image + name + character name (if space allows).
- Kevin Bacon is **guaranteed not present** in this cast (Epic 3's win check would have fired). No Bacon marker needed.
- Selecting a co-actor adds the actor to the trail breadcrumb and loops back to Epic 3 with that actor as the new subject.
- Actors already in the current round's trail are visually deemphasized (`opacity: 0.4`) and not clickable — prevents walking in a loop.
- Transition back to Epic 3: ≤ 220 ms.

### Edge cases

- Cast list has < 15 members → show fewer.
- Cast member image fails to load → initials avatar.
- All cast members are already in the trail (extreme case: tiny-cast movie at step 5) → show *"This film's cast is already on your trail. [Back]"* with a back button to Epic 3.
- User's film counter is at 6 and they're on this screen → they've hit the ceiling without finding Bacon; transition to Epic 5 with `outcome='out-of-films'` rather than letting them pick another co-actor.

---

## Epic 5 — Result card [MUST-HAVE]

The closing moment. Summarizes the round and offers replay / follow-through.

### User stories

- **5.1** — As the visitor, I want to see a celebration moment if I found Bacon, with the exact film count and a visualization of the trail I walked, so the win feels concrete.
- **5.2** — As the visitor, I want a polite "out of steps" ending if I didn't find Bacon, that doesn't feel punitive and gives me a clear path to play again.
- **5.3** — As the visitor, I want a *"See the full suite →"* link from the result card, so a hooked visitor can follow into the Lobby Engagement Suite.

### Acceptance criteria

- **Found state** — headline: *"You found Bacon in {N} film{s}."* using `--success` treatment (no `--warning` glow — clean green celebration). Trail breadcrumb shows the full walk collapsed: `{birthday actor} → {film 1} → {co-actor 1} → {film 2} → … → {winning film — Kevin Bacon in cast}`. "Play Again" button (cyan→magenta gradient), "See the full suite →" text link.
- **Out-of-films state** — headline: *"Didn't find Bacon in 6 films. Try a different starting actor?"* using `--danger` as a single small indicator (no red wash). Trail breadcrumb shows the walk. "Play Again" + "See the full suite →" same as Found.
- **Play Again** resets the full widget state to Epic 2 with a new randomized pull of 6 birthday actors from the shard.
- Result transitions in at ≤ 380ms. No fade-on-scroll, no bouncy spring — per brand motion.

### Edge cases

- Trail contains 6 actors + 6 movies = 12 breadcrumb nodes → collapses to a compact representation (maybe `{actor} → {movie} → {actor}...` with ellipses on hover-expand, or a two-row stacked layout).
- Visitor rapid-clicks "Play Again" → debounce; single re-shuffle fires.
- No "shareable" / "copy score" button in v1 (explicitly cut in scope).

---

## Epic 6 — Daily shard pipeline [MUST-HAVE]

The non-runtime infrastructure that keeps today's birthday shard fresh.

### User stories

- **6.1** — As the builder, I want a GitHub Action that regenerates all 366 birthday shards nightly, so the widget's data stays current without manual intervention.
- **6.2** — As the builder, I want the action's logs to be clearly scoped (not mixed into other CI noise), so I can debug a stuck sync in under a minute.

### Acceptance criteria

- New workflow file at `.github/workflows/refresh-bacon-shards.yml`, cron `0 6 * * *` UTC.
- Workflow runs a Node.js script at `scripts/refresh-bacon-shards.mjs` that:
  - Authenticates to Firestore using a secret (reuses `TRAFFIC_PAT` or new `BACON_FIREBASE_KEY` — exact auth approach locked in `/spec`).
  - Queries `actorDatabase` 366 times (one per `birthDateKey`) OR does one bulk fetch + in-memory grouping, whichever the spec picks as more efficient.
  - Writes each to `apps/widget-bacon-trail/data/birthdays/MM-DD.json`.
  - Commits + pushes the changes to `main` using the `github-actions[bot]` identity (same pattern as `track-traffic.yml`).
- Workflow guards against self-trigger: `if: github.actor != 'github-actions[bot]'` (same pattern as `rebuild-hub.yml`).
- Workflow can also be triggered manually via `workflow_dispatch`.
- Each shard file format:
  ```json
  {
    "date": "04-23",
    "generatedAt": "2026-04-23T06:00:00Z",
    "actors": [{ "id": 12345, "name": "...", "profilePath": "/abc.jpg", "birthday": "1949-09-22", "popularity": 2.4134, "baconNumber": 2 }, ...]
  }
  ```

### Edge cases

- Firestore query fails (auth, quota, transient) → workflow fails loudly, logs the error, does not commit stale data. Repo still serves the last-known-good shards until next run.
- Firestore schema changes add/remove fields → script is tolerant, writes only known fields, logs a warning on unknown fields.
- Shard content identical to previous run → still commits the file (with a fresh `generatedAt`) for audit clarity; or skips commit if bytes are identical to avoid noise. Decision locked in `/spec`.

---

## Epic 7 — Hub embed section [MUST-HAVE]

Wiring the widget into 626labs.dev's `index.html`.

### User stories

- **7.1** — As the visitor, I want a clearly-named section on the hub that tells me "also, we make games" before showing the widgets, so the transition from product grid → playable widget is explained.
- **7.2** — As the builder, I want the embed wiring to live in `content/site.json` + `scripts/render-hub.py` (the existing render pipeline), so it survives rebuilds and the admin dash can later edit it.

### Acceptance criteria

- New `<section class="play">` added to `index.html`, positioned between the Lab Shelf and the About section.
- Section header: *"Also, we make games."* (sentence-case, h2, Space Grotesk). Subhead: *"Try one."*
- **Single widget in this ship** — the Birthday Bacon Trail widget alone. The CinePerks movie trivia widget is NOT embedded on the hub in this scope; that's a future ship (at which point it gets its own 626 Labs design treatment and the `.play` section grows to 2-up).
- Widget mounted via `<script src="/apps/widget-bacon-trail/dist/widget.js">` + an inline init call: `BaconTrailWidget.init({ container: document.getElementById('bacon-widget'), ctaUrl: '/#work' })`.
- Layout is flex/grid-ready for a future second widget: centered single-column now, converts cleanly to `grid-template-columns: 1fr 1fr` when the second widget arrives (code the CSS now; just don't render the second slot).
- Section marker for the Python renderer: `<!-- SITE_JSON:play:start -->` / `<!-- SITE_JSON:play:end -->`, matching the existing partial-render pattern.
- `render-hub.py` gains a `render_play_section()` function that emits the section from `content/site.json` config (enable/disable, widget list).
- **`apps/widget/` (the existing CinePerks source) is NOT touched** by this ship. Its branding, code, and build stay exactly as they are in QuizShow.

### Edge cases

- Script tag fails to load (CDN hiccup, CSP issue) → hub renders the section with a graceful *"Widget unavailable"* placeholder in each slot. Does not break page layout.
- Visitor has JS disabled → same graceful fallback; section still renders with a placeholder explaining the widget needs JS.
- User agent is a search engine crawler → section renders with static "Try our games at [link]" text for SEO + indexability.

---

## Cross-cutting requirements

### Performance budget

- Widget JS bundle: **≤ 150 KB gzipped** (hard ceiling; measured via Vite's build output).
- Widget CSS: **≤ 20 KB gzipped**.
- First paint: **≤ 300 ms** after script loads on the hub.
- Interaction latency (screen → screen): **≤ 1.5 s** average on a typical broadband connection (TMDB response + render).
- Lighthouse score on the hub after embed: performance score drops by **≤ 5 points** from baseline.

### Responsive behavior

- Desktop: widget renders at 400 × 600 (±20 px tolerance).
- Tablet: widget renders at 360 × 540.
- Mobile (≤ 480px viewport): widget fills container width, height auto; grids collapse from 3×2 to 2×3.
- Touch targets: minimum 44×44 (iOS HIG compliance, baseline accessibility).

### Error handling

- Every network call (shard fetch, TMDB fetch) has an inline retry UI.
- No errors thrown to the hub page (widget catches and contains all failures).
- No `alert()` / `confirm()` — inline UI only.
- Console errors only for genuinely unexpected conditions.

### Accessibility

- All interactive elements are keyboard-reachable (tab + enter).
- Focus ring is cyan (matches brand accent).
- All images have `alt` text (actor name, movie title).
- Screen-reader-friendly live region announces film picks (*"Film 3 of 6: Pulp Fiction. Kevin Bacon not in cast — choose a co-actor to continue."*) and the result moment (*"Found Kevin Bacon in the cast of A Few Good Men — won in 4 films."*).
- Color contrast meets WCAG AA for all text.

### Analytics *(deferred — Later)*

- Not in MVP. When added, fire events for: widget mount, actor pick, movie pick, cast-actor pick, found-Bacon, out-of-steps, play-again click, CTA click.
- Event sink TBD (existing `data/traffic.csv` pipeline? new lightweight beacon? `/spec` or v2 decides).

---

## Priority ladder

### Must-have (v1 ship)

- Epics 1–7 above.
- Works on desktop + mobile.
- Daily shard pipeline running.
- No analytics.
- English-only.
- Hard-coded 626 Labs brand palette.
- One instance on the hub.

### Later (v2+)

- Analytics pipeline (Epic 8 when added).
- Precomputed bounded graph (eliminates TMDB live calls).
- Kid-friendly filter.
- Multi-language support.
- Multiple theme variants via config.
- Light-theme rendering.
- Share-score / viral output.
- "Replay with different starting actor" (pick-your-actor mode).
- Leaderboard surface on the full game's dedicated URL (not in the widget).

### Never (cut forever, per scope)

- User accounts / anonymous IDs.
- Nickname prompt.
- Rewards / signup / member-detect flow.
- In-widget leaderboard.

---

## Open questions deferred to `/spec`

1. **TMDB API key handling** — client-side baked read-only key vs. Cloud Function proxy. *Scope defers this, spec resolves.*
2. **GitHub Action auth** — reuse existing `TRAFFIC_PAT` secret (with expanded scope to include the `guestbuzz-cineperks` Firestore project) OR create a new `BACON_FIREBASE_KEY` dedicated secret. Security boundary decision.
3. **Vite build output path** — `apps/widget-bacon-trail/dist/widget.js` vs. `widget-bacon-trail/widget.js` at the hub root. Deploy-pipeline hygiene decision.
4. **Shard-commit idempotency** — skip commit if bytes identical to avoid noise commits, or always commit with a fresh `generatedAt` for audit?
5. **Responsive breakpoints** — exact viewport thresholds for the grid collapse; probably aligned to the hub's existing breakpoints but need confirmation.

Each of these is flagged in `/spec`; Este has committed to answering them when `/spec` asks.

---

## Requirements confirmed by builder on 2026-04-23

The five decisions I flagged for review were all answered in chat; applied to the epics above:

- **A.** Starting grid: **6 actors, 3×2.** Confirmed. Actor ranking comes from the existing `actorDatabase` fields: primary sort `popularity` descending, preference filter `baconNumber ≤ 6` (matches `actorService.ts` pattern from the full game).
- **B.** Trail max depth: **6 films.** Corrected from my initial phrasing (*"6 steps"*). Degrees are counted in films, not in actor/movie pick pairs. Each film picked advances the counter by one; co-actor picks are transitions, not degrees.
- **C.** Found-state palette: **`--success` alone** (dropped the `--warning` glow for a cleaner celebration).
- **D.** Widget dimensions: **400 × 600** baseline, with flexibility — the hub is ours, so these can be retuned during `/spec` or `/build` if the design needs it.
- **E.** Win mechanic: **movie selection triggers win, not actor selection.** When a visitor picks a film whose cast includes Kevin Bacon, they win immediately. No Bacon-marker in the cast grid. No manual Bacon pick. Epic 3 owns the win check on the `movie_credits` fetch.

Hub-embed clarifications also confirmed:

- CinePerks widget is **not** already on the hub. This ship does **not** embed it. Future ship brings it over with its own 626 Labs treatment.
- `apps/widget/` is left untouched in this project.
