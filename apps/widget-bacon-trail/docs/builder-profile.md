# Builder Profile — Birthday Bacon Trail Widget

**Date:** 2026-04-23
**Builder:** Estevan (returning, 5th Cart project started, targeting #4 shipped)
**Project:** Birthday Bacon Trail Widget
**Codename:** `widget-bacon-trail`
**Project root:** `~/Projects/626labs-hub/apps/widget-bacon-trail/`
**Artifacts root:** `apps/widget-bacon-trail/docs/`

---

## Profile state going in

- **Persona:** architect
- **Mode (vibe-cartographer):** builder
- **Pacing:** brisk
- **Tone:** terse and direct
- All TTLs fresh — `last_confirmed: 2026-04-22`. Zero decay prompts needed; unified profile stamped yesterday during RTClickPng retro.
- Pulled from unified profile at `~/.claude/profiles/builder.json` (schema v1).

### Builder snapshot (relevant to this project)

- **Technical level:** experienced
- **Known-stack alignment:** TypeScript, React 19, Vite, TailwindCSS, Firebase — all stamped, nothing new for this build.
- **AI-agent experience:** deep. Runs Claude Code as an autonomous build system with structured checklists, subagent delegation, and verification hooks.
- **Deepening-round habit:** zero when the vision is formed. Intervention budget spent mid-command on load-bearing decisions, not on exploratory rounds.
- **Handoff tolerance:** neutral tool. Will swap agents mid-build when one is stuck; agents should not optimize to avoid handoff, they should optimize to not need it.

### Changes since last project

- **Last project:** Right Click PNG (RTClickPng) — shipped 2026-04-22 to Microsoft Store (app #3 in portfolio). 24-hour build across two agent sessions.
- **No preference updates** — everything still fresh from the RTClickPng stamping.
- **No stack additions** needed for this project — widget lives inside the known React 19 + Vite + Firebase universe.

---

## Project goals (triple outcome)

1. **Ship an embeddable Bacon Trail widget** — a ~400×600 card that runs a stripped Birthday Bacon Trail game (pick-birthday-actor → pick-movie → pick-cast-actor → result). No nickname prompt, no leaderboard, no share button.
2. **Embed it on 626labs.dev** as the inaugural widget in a new "also we make games" section — a play surface that surfaces the Lobby Engagement Suite without requiring visitors to leave the hub. (A future ship will bring the CinePerks movie trivia widget in alongside it with its own 626 Labs treatment; not in this scope.)
3. **Reuse existing infrastructure** — share QuizShow's Firebase project for the actor data (read-only), reuse the game's existing TMDB-fetching services, avoid any new backend work.

### Underlying craft goal (architect)

Prove that a game-genre sub-product can be lifted out of a monorepo and re-homed into a portfolio site without duplicating infrastructure. The widget is a test of the *"Work from the future"* motto — if the embed contract is clean, future Lobby Engagement Suite apps (Reel Words, Reel Battles, etc.) plug in the same way.

---

## Mottos bound to this project

- **"Everything is in scope at 626Labs LLC"** — nickname prompt, leaderboard, share-score, anonymous user ID: all cut without apology.
- **"Work from the future. We are already behind."** — ship the embed contract cleanly the first time so the next 3 games plug in with config changes, not copy-paste.
- **"Leave the builder self-sufficient — with or without us."** — prefer static data pipelines over runtime backend dependencies where feasible. The widget should degrade gracefully if Firebase or TMDB is unreachable.

---

## Design direction

- **626 Labs design treatment** applied to the widget chrome: navy background, cyan (`#17d4fa`) / magenta (`#f22f89`) accents, mono typography for labels and data chips.
- **Game-content palette inside the chrome** may preserve some of the Bacon Trail's amber / yellow where it signals *"this is game content"* vs. *"this is site chrome."* Final call during `/spec`.
- **Sibling parity** with the CinePerks movie trivia widget — same card dimensions, same config-via-props contract, same `"See the full suite →"` CTA pattern instead of a signup flow.

---

## Architecture docs / reference code

- **"Proof" block** drafted 2026-04-23 pre-`/scope` (PROJECT, PARENT, IDEA, GAMEPLAY, DATA, CONFIG API, REUSE, CUT, OPEN QUESTIONS). Feeds directly into the `/scope` interview as raw input.
- [`~/Projects/QuizShow/apps/bacon-trail/`](~/Projects/QuizShow/apps/bacon-trail/) — full-game source. State machine, screens, services.
- [`~/Projects/QuizShow/apps/widget/`](~/Projects/QuizShow/apps/widget/) — the embed-widget pattern to clone (config API, `Widget.tsx` shell, `INTEGRATION.md`).
- [`~/Projects/WeSeeYouAtTheMovies/frontend/src/components/BirthdayBaconTrail/`](~/Projects/WeSeeYouAtTheMovies/frontend/src/components/BirthdayBaconTrail/) — prior adaptation; trim the user/auth wrapper, keep the state machine structure.
- [`~/Projects/626labs-hub/`](~/Projects/626labs-hub/) — deploy target. Hub's render pipeline (`scripts/render-hub.py`), admin dash, and sub-page patterns (`sanduhr/`) are all known. `apps/` is a new top-level directory for the hub.

---

## Build mode

**Autonomous with checkpoints** — same shape as Sanduhr + RTClickPng. Key adaptations for this project per builder's explicit instruction:

- **Spawn parallel Explore agents** during `/build` for independent research tasks. Examples of independent threads: (a) size the actorDatabase, (b) confirm TMDB key handling pattern in WSYATM, (c) verify `apps/widget` builds cleanly, (d) check hub's GitHub Pages deploy output for `apps/` directory support.
- **Verification hooks between checklist items** — don't advance a step until validity is confirmed programmatically (e.g., a Vite build succeeds, a Firestore query returns, an embed snapshot renders). Builder has a preference for catching regressions at the step boundary, not at the end.
- **Agent handoff is tolerated and sometimes preferred.** Prior builds (RTClickPng) shipped via handoff; retrospective discipline applies (diagnose root cause, don't retreat through tech stacks).

---

## Pacing

- **Build starts today** (2026-04-23). `/scope` → `/prd` → `/spec` can stretch across the afternoon; no forced single-session ship.
- **No urgency.** Sanduhr Product Hunt launch (also today) is handled separately and does not block this project.
- **Multi-session ship is expected and fine.** (See Este's 2026-04-22 reflection: Cartographer should celebrate multi-session builds, not pressure single-session.)

---

## New territory

**None significant.** One minor wrinkle worth flagging for `/spec`: the widget is refactored *from* a QuizShow monorepo app *into* a `626labs-hub` sub-app. Cross-repo code lift + hub-deploy fusion is novel-ish — specifically, this is the first time `626labs-hub` will host an `apps/` directory with its own Vite build output alongside the existing Python-rendered static site. Build-artifact pathing and GitHub Pages publication of a sub-app need confirmation during `/spec`.

---

## Scope-phase open questions (to carry into `/scope`)

1. **Data architecture for birthday actors** — three candidates: (a) daily-regenerated JSON shards under `data/birthdays/MM-DD.json`, (b) live Firestore queries, (c) fully static precomputed graph. Preliminary lean: **daily JSON sharding** for birthday data + live TMDB for movies/cast. Real decision in `/scope`.
2. **TMDB API key handling** — baked client-side (read-only, standard pattern), Cloud Function proxy (server-side), or sidestepped entirely via Option 1c fully-static graph.
3. **Deploy path** — does the widget bundle live at `626labs.dev/widget-bacon-trail/` (hub-hosted build artifact), at its own URL and iframed, or bundled into the hub's `index.html` build?
4. **Visual treatment** — full 626 Labs palette for the entire widget, or preserve Bacon Trail amber inside the chrome for game-content contrast?

---

## Energy / engagement

Coming in from a long morning — Sanduhr Product Hunt launch, hub render-pipeline fixes (SwiftUI meta cleanup, badge pair, RTClickPng story draft). Engagement still high, decisive answers, vision already formed for the widget's shape. Expect zero deepening rounds; course-corrects saved for load-bearing decisions during `/spec` and `/build`.

---

## Prior SDD experience

**Extensive.** Fifth Cart project started (targeting fourth ship). Previously completed:

1. **Sanduhr für Claude** — native desktop widget, shipped to MS Store + GitHub Releases.
2. **Vibe Test** — Claude Code plugin, shipped to npm + marketplace.
3. **Right Click PNG** — Windows shell extension, shipped to MS Store 2026-04-22.

All three went autonomous-with-checkpoints. All three shipped within their intended window. Pattern: zero deepening rounds, 2-3 mid-command course-corrects on load-bearing decisions, retrospectives capture misses in a specific memory file for future projects to inherit.

Scoring this project's `/reflect` at practitioner level is expected.
