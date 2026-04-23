# Birthday Bacon Trail Widget (widget-bacon-trail)

## Idea

An embeddable React widget that runs a stripped-down version of the Birthday Bacon Trail game — the user picks one of today's birthday actors, walks a movie-cast chain, and tries to find Kevin Bacon within six films. Picking a film whose cast includes Bacon is the win. Designed to live as a ~400×600 card on 626labs.dev. Goal is delight + "we actually ship games" proof, not theater-rewards conversion.

The widget is a second-generation artifact of the Lobby Engagement Suite: the full game lives at [`apps/bacon-trail/`](~/Projects/QuizShow/apps/bacon-trail/) in the QuizShow monorepo; this is a compact, embeddable fork optimized for portfolio placement.

## Who It's For

**Primary user:** a 626labs.dev visitor — a fellow builder, a founder, a hiring engineer, a plugin user — stopping by the hub after hearing about one of the Vibe plugins or following a Product Hunt link. They have 30 seconds. They're not committed. They want a glimpse of what 626 Labs ships beyond the tooling, and they want to see taste-plus-function, not just screenshots.

**Specific unmet need:** there is currently no interactive moment on 626labs.dev. The hub lists products, describes a framework, explains the lab — but nothing on the page *plays back*. A visitor never gets to feel the work. The Birthday Bacon Trail game is uniquely suited to fix this: it's bounded, quickly-loved, and carries a recognizable cultural hook (Six Degrees of Kevin Bacon).

**Secondary user:** the builder himself. This widget is a public demonstration that the Lobby Engagement Suite is production-grade — a card that runs on a portfolio site every day without ops babysitting. If it works here, it will work on any theater's or hotel's web frontend when the suite goes to market.

**Explicit non-users:**

- *Theater customers* — that's what CinePerks Trivia Widget (the sibling in `apps/widget/`) is for. This widget has no rewards/signup flow and shouldn't grow one.
- *Leaderboard players* — competitive multiplayer is a product of the full game, not the widget.
- *Kid-friendly filtered audiences* — deferred to v2; the widget ships with the default Bacon Trail actor set.

## Inspiration & References

**Architectural mentor:**

- [**CinePerks Trivia Widget**](~/Projects/QuizShow/apps/widget/) — the sibling widget in the same monorepo. Defines the embed contract we are cloning (config-via-props, `theme / brandColor / brandLogo`, `CinePerksWidget.init({ container, ...config })` script-tag invocation). Our widget's config API is a near-superset of this one. `INTEGRATION.md` in that directory documents the pattern in detail.

**Source material (the game):**

- [`apps/bacon-trail/`](~/Projects/QuizShow/apps/bacon-trail/) — the full Birthday Bacon Trail app. State machine, screens, service layer all usable as references. ~20 files, ~2000 lines.
- [`WeSeeYouAtTheMovies/frontend/src/components/BirthdayBaconTrail/`](~/Projects/WeSeeYouAtTheMovies/frontend/src/components/BirthdayBaconTrail/) — the prior lift-and-adapt into WSYATM. Useful as a *"here's how we already stripped the auth and nickname systems"* reference, but it still assumes a user context; we go further and ship without user state at all.

**Spiritual cousin (reveals what we're NOT):**

- [oracleofbacon.org](https://oracleofbacon.org/) — the canonical Six Degrees of Kevin Bacon tool. Bounded actor graph, fully static, runs offline. Not a game loop — it's a lookup. We're explicitly building a *game* experience, not a graph walker. Theirs is the reference for what the bounded-static-graph architecture would look like if we ever picked it; for v1 we don't.

**Design energy:** clean, dark, brand-native. Full 626 Labs palette — navy base, cyan + magenta always paired, semantic warms (`--success`, `--warning`, `--danger`) for state contrast where the game earns heat. Space Grotesk for the widget headline, Inter for body, JetBrains Mono for film counters. No emoji. Polish valued; no polish at expense of shipping. See Decision 4 for the full token breakdown.

## Goals

Triple outcome:

1. **Ship an embeddable widget** — Vite-built, ships a single `widget.js` bundle plus a `widget.css` file and a tiny JS init API. Loads as a script tag on 626labs.dev, renders in a named container div. Weight budget: **≤ 150 KB gzipped JS** (excluding optional Firebase SDK — we're going static daily shards to avoid that dependency).
2. **Embed on 626labs.dev** — a new `<section class="play">` between the Lab Shelf and the About section on `index.html`. Single centered widget in this ship (the Bacon Trail widget); the section is built with a flex/grid-ready layout so a second widget can slot in later without a rewrite. Section has a tight header ("Also, we make games") and the widget renders fully, no click-to-expand gating. CinePerks widget is NOT embedded in this ship — future scope.
3. **Reuse existing infrastructure** — no new Firebase project, no new backend, no new domain. Widget reads from QuizShow's existing `actorDatabase` Firestore collection via a daily-refreshed static shard pipeline; TMDB is called at runtime using a key pattern inherited from WSYATM (final approach locked in `/spec`).

**Underlying craft goal (architect):** prove the widget-embed pattern for the Lobby Engagement Suite. If this ships cleanly, we have an embed contract that the next three games (Reel Battles, Reel Words, Heads Up) can follow without reinventing the frame — every future widget is config changes, not copy-paste.

## Load-bearing decisions (resolved)

Four decisions with downstream architectural consequences, resolved in this scope (not deferred to `/spec`):

### Decision 1 — Birthday-actor data pipeline: **daily JSON shards**

Source of truth remains QuizShow's `actorDatabase` in Firestore (project `guestbuzz-cineperks`). This collection is **already the Bacon-engine-filtered set** — it's not the full TMDB actor universe, it's the curated subset the Bacon Trail game plays with (actors with known Bacon numbers, meaningful popularity, known birthdays). No further filtering needed on our end.

A new GitHub Action (modeled on [`.github/workflows/track-traffic.yml`](~/Projects/626labs-hub/.github/workflows/track-traffic.yml)) runs nightly (cron `0 6 * * *` UTC), queries Firestore for each of the 366 date keys, and writes 366 files to `apps/widget-bacon-trail/data/birthdays/MM-DD.json`. The widget loads exactly one file per visit (today's).

**Measured numbers (2026-04-23 Firestore query):**

- `actorDatabase` row count: **10,000** (the pre-filtered Bacon-eligible set)
- Avg doc size (JSON): **~400 bytes**
- Full DB uncompressed: **~3.84 MB**; gzipped: **~1.15 MB**
- Actors born on 04-23 (sample day): **20** → shard size ~8 KB uncompressed, **~2-3 KB gzipped**
- All 366 shards combined in repo: ~2.8 MB (uncompressed), but client only loads one file per visit

**Rationale:** shards are ~380× smaller per-visit than the full DB; zero runtime Firebase client in the widget bundle (saves ~80 KB gzipped); zero runtime Firestore dependency; files cached by the GitHub Pages CDN; fresh daily; honors *"leave the builder self-sufficient"* (widget runs if QuizShow's Firestore migrates or goes down).

**Alternative considered and cut:** live Firestore queries at runtime. Pros: always fresh, simpler pipeline. Cons: Firebase SDK adds weight; runtime network dependency; security-rules-coupled to QuizShow.

**Alternative considered and cut:** bundle the full 10,000-actor DB as a static asset (1.15 MB gzipped). Simpler pipeline (no daily Action). Rejected: 1.15 MB vs. ~3 KB per-visit is the wrong trade-off on a portfolio hub where the widget is one of several payloads. If the daily Action ever becomes a maintenance pain, this is the cheap fallback.

**Alternative considered and deferred to v2:** fully static precomputed actor-movie-cast graph (oracleofbacon.org pattern). Would eliminate TMDB calls too. At 10,000 curated actors this is now genuinely tractable (~15-30 MB bounded graph). Right answer for v2 if TMDB quota or reliability becomes an issue.

### Decision 2 — Movie / cast data: **live TMDB at runtime**

The game branches unpredictably: any birthday actor → any of their ~20-50 movies → any of that movie's ~15 cast members → and so on. Precomputing every branch path is infeasible without going to the full bounded-graph architecture (deferred to v2).

**Rationale:** inherits the full game's existing `tmdbService.ts` pattern. Known, tested, works.

**What's deferred to `/spec`:** exact key-handling approach (client-side baked key vs. Cloud Function proxy). Both are viable; the trade-off is a key-rotation operational concern, not a scope-shape decision.

### Decision 3 — Deploy target: **bundled into 626labs-hub**

Widget source lives at `~/Projects/626labs-hub/apps/widget-bacon-trail/`. Vite builds to `apps/widget-bacon-trail/dist/`. The hub's GitHub Pages deploy serves that directory at `https://626labs.dev/apps/widget-bacon-trail/dist/widget.js` (or an equivalent short path — locked in `/spec`). The hub's `index.html` includes the widget via a script tag + an init call.

**Rationale:** one repo, one deploy, no cross-origin, no subdomain DNS. The hub already owns the domain and the deploy pipeline. Fits the existing pattern (sub-apps like `sanduhr/` already live inside the hub repo).

**Alternative considered and cut:** deploy to `widget.626labs.dev` or Firebase Hosting, iframe from hub. Cleaner separation but adds DNS + CORS + a second deploy pipeline to maintain. Overkill for this scope.

### Decision 4 — Visual treatment: **626 Labs palette, semantic colors for state contrast**

Full 626 Labs brand system per the `626labs-design` skill. No off-palette colors — earlier drafts proposed preserving Bacon Trail's amber; that's off-brand (`#f59e0b` is not in the token scale).

**Structural palette:**

- **Base**: `--bg-0` / `--bg-2` (deep navy `#0f1f31` → `#192e44`)
- **Signature duo (always paired)**: cyan `#17d4fa` + magenta `#f22f89`
- **Accents**: the cyan→magenta gradient (`linear-gradient(135deg, …)`) for the wordmark-style headline *"Birthday Bacon Trail"*, the Play Again CTA hover state, and the trail-breadcrumb progress line
- **Type**: Space Grotesk for the widget headline, Inter for body copy, JetBrains Mono for film counters and meta labels (uppercase with +0.12em tracking)
- **No emoji** (including the previously-planned 🥓) — replaced with a custom SVG bacon glyph in Lucide line-icon style if a glyph is truly needed for the "found Bacon" moment

**State contrast via semantic colors** (where the game needs warmth or heat, we use tokens from the design system, not invented amber):

- **Win state** ("You found Bacon in N steps!"): `--success` `#2bd99a` (green) as the primary celebratory color, with a soft `--warning` `#ffb454` glow for heat/earned-reward energy. Both are sanctioned semantic tokens tuned for the dark surface.
- **Active step / current progress**: cyan with glow (`--glow-cyan`).
- **Out-of-steps failure state**: `--danger` `#ff5472` as a single small indicator, handled tastefully — no harsh red wash, no shake animation, just a "Didn't find Bacon this time. Play Again?" card.
- **Actor cards at rest**: `--bg-3` with a 1px hairline border `--border-1`; on hover, border shifts to `--border-accent` (cyan).
- **Selected actor / movie**: cyan→magenta gradient border + inner glow.

**Rationale:** honors the brand rule *"always pair cyan and magenta"*; uses the semantic palette's warm tokens where the game earns heat instead of inventing off-brand amber; keeps the widget visually legible as a 626 Labs product on a 626 Labs page.

**Alternative considered and cut:** two-zone palette preserving Bacon Trail's amber inside a 626-Labs chrome. Rejected as off-brand after loading the `626labs-design` skill — the design system has specific semantic tokens (`--warning`, `--success`) for heat/contrast moments, and introducing raw `#f59e0b` from the full game would dilute the brand signal.

**Alternative considered and cut:** full neutral (no cyan/magenta accent). Rejected — the brand system explicitly requires the duo to appear paired on every surface.

## What "Done" Looks Like

A visitor on desktop:

1. Loads `626labs.dev`. Scrolls past hero, products, thinking, lab shelf.
2. Lands on a new `<section class="play">` with the header *"Also, we make games. Try one."*
3. Sees the Birthday Bacon Trail widget card. (Future ship will add CinePerks Trivia as a second card; for now the section has one centered widget.)
4. The card has already loaded today's birthday actors — grid of 6 actor faces with names and birthdays.
5. Picks **Harvey Keitel** (chosen because today happens to be his birthday). Film counter shows *"Film 1 / 6"* on the next screen.
6. Widget fetches Harvey Keitel's top 20 movies via TMDB, shows a scrollable list with posters.
7. Picks **Pulp Fiction**. Widget fetches the cast, checks for Kevin Bacon. Not in cast — widget shows the top 15 co-actors for Keitel's next chain step.
8. Picks **Samuel L. Jackson** as the co-actor. Film counter ticks to *"Film 2 / 6"* on the next screen.
9. Widget fetches Jackson's top 20 movies. Picks **A Few Good Men**. Widget fetches cast — Kevin Bacon is present.
10. Widget transitions immediately to the result card (no need to pick Bacon manually — picking the film that contains him is the win).
11. Result card: *"You found Bacon in 2 films."* Trail breadcrumb showing the chain: Harvey Keitel → Pulp Fiction → Samuel L. Jackson → **A Few Good Men (Kevin Bacon in cast)**. Two buttons: **Play Again** (resets state, new birthday actor options) and **See the full suite →** (links to the Lobby Engagement Suite lab card on the same page, anchor-scroll).

**Quality bar:**

- First paint ≤ 300 ms on the hub (static shard loaded, no blocking network).
- Interaction latency ≤ 1.5 s between screens (TMDB fetch + render).
- No visible loading flicker — skeleton UI during fetches, not spinners.
- Responsive: on mobile, widget stacks and resizes to ~320 × 540.
- Zero console errors, zero unhandled promise rejections, under CSP the hub already uses.
- Graceful degradation: if TMDB fails, show an inline error card ("having trouble reaching movie data — try again") with a retry button. Do not crash the page.

**Distribution bar:** widget bundle is committed to `apps/widget-bacon-trail/dist/` via Vite build, referenced from hub `index.html` via `<script src>`. The GitHub Action that regenerates daily birthday shards also ensures the dist is rebuilt on any widget source change. No manual deploy steps.

## What's Explicitly Cut

**Cut forever (sovereignty of the widget):**

- **User accounts / anonymous IDs** — the widget is stateless. No `useAnonymousId` hook, no Firestore writes, no localStorage persistence of play history.
- **Nickname prompt** — visitors don't identify themselves. Removes an entire screen from the state machine.
- **Leaderboard** — no reads, no writes, no display. If a leaderboard surface is ever wanted, it belongs on the full game at a dedicated URL, not inside a portfolio widget.
- **Share-score link** — no copy-to-clipboard CTA, no Twitter/X intent URL. The widget is a moment, not a viral object.
- **Rewards / signup / member-detect flow** — that's CinePerks-widget territory. Our CTA is *"See the full suite →"*, a link to the Lobby Engagement Suite lab card on the same page.
- **Kid-friendly filter** — deferred; ships with default actor set. If child-safety becomes relevant for a hotel or cinema customer, it goes on their instance of the widget with a config prop (post-v1).
- **Multiple themes / brand-overrides per-instance** — the hub's widget is one instance, one look. Theme API stays on the component for future reuse, but v1 hard-codes to the 626 Labs brand palette.

**Cut from v1, probably back for v2:**

- **Bounded precomputed actor graph** (no TMDB at runtime). Architectural upgrade for when quota or reliability becomes a pain point.
- **Offline mode / service worker caching**. Same trigger: if mobile visitors on flaky connections become a noticeable audience.
- **Replay-with-different-starting-actor** — currently just Play Again (new random pick from today's birthdays). Adding "Pick from yesterday" or "Pick a specific actor" is explicit scope creep.
- **Multi-language support.** English-only, default TMDB locale.

**Cut because it's a different product:**

- **A full game page on the hub** — `626labs.dev/games/bacon-trail` is a separate project. This scope is specifically the widget.
- **A Lobby Engagement Suite landing page on the hub** — also a separate project. The widget's CTA links to the existing lab-card anchor.

## Non-goals (for the scope author's future self)

- This widget does not replace the full `apps/bacon-trail/` app.
- This widget does not change the full game's schema, services, or Firestore usage (read-only from our side).
- This widget does not define patterns for how other suite games will be embedded — those decisions live in their own scope docs, even if this one becomes the template.
- This widget is not a performance benchmark for the hub (the hub has its own perf budget; we just don't regress it).

## Out-of-scope that came up but doesn't belong here

- **Analytics** (how many people play, how far they get, what birthday actor they picked) — could land on top of the existing `data/traffic.csv` pipeline, but that's a separate scope.
- **A "play with friend" mode** — live multiplayer is a different product.
- **A showcase sub-page with multiple embedded instances** — if the two-widget section on the hub proves popular, a `/play/` page with four games is a natural v2; not this scope.

---

## Scope summary (for `/prd` to chew on)

- **Product:** 400×600 embeddable React widget, built with Vite, bundles to a single JS file + CSS file.
- **Consumer:** 626labs.dev hub's `index.html`, via script tag + init call in a new `<section class="play">`.
- **Parent repo:** `626labs-hub` (new `apps/widget-bacon-trail/` directory).
- **Source repo (reference):** `QuizShow`'s `apps/bacon-trail/` and `apps/widget/`.
- **Gameplay:** 3-screen stripped Bacon Trail (birthday actor → movie → co-actor) looping until a film with Bacon in cast is picked, or 6 films walked. Win fires on movie selection, not actor selection.
- **Data:** daily-regenerated JSON shards for birthday actors; live TMDB for movie/cast.
- **Visual:** full 626 Labs palette (navy + cyan + magenta always paired) + semantic warms (`--success`, `--warning`, `--danger`) for state contrast. Space Grotesk / Inter / JetBrains Mono. No emoji.
- **Shipping budget:** ~150 KB gzipped JS bundle, ≤ 300 ms first paint, ≤ 1.5 s interaction latency.
- **Open implementation questions for `/spec`:**
  1. TMDB key handling (client-side baked vs. Cloud Function proxy).
  2. Exact GitHub Action schedule + Firestore query auth (reuse `TRAFFIC_PAT` or new secret).
  3. Vite build output path under the hub's GitHub Pages publish structure.
  4. Responsive breakpoints and grid behavior for the `.play` section on mobile.
