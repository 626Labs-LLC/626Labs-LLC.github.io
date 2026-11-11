# Bacon Trail: true Bacon numbers, honest about the hub's reach

Status: draft for Este's review, builder-checked 2026-11-10. Hub widget at `apps/widget-bacon-trail/`.

## Intent

The result card names the starting actor's Bacon number (shipped in #310, ported from WeSeeYouAtTheMovies PR #84). Este's call: **the number stays true**. The stored number comes from the CinePerks actorDatabase, computed over a wider graph than the hub game allows. When the hub can't walk a route that short, the card says so plainly, and points the player at the full game on WeSeeYouAtTheMovies, at its new domain `wsyatm.626labs.dev`. Every other result card gets a lighter standing invite to the same game.

Why: a lie on the card ("Bacon number 2" when the player can't find a 2-film route here, and never could) reads as the game being broken. Saying "path not available here" turns the gap into a reason to try the full game.

## Goals

- The displayed number is the true one: the stored number, or the player's own count when they beat it (the #310 rule stays).
- When the hub's rules cannot produce a route at the stored number, the line says `(path not available here)` and the card links to the full game.
- When the route is reachable here, the card reads as it does today, plus the light invite.
- The hub knows reachability ahead of time. No live graph search in the browser.

## Non-goals

- Changing the hub's game rules (top 45 films per actor, top 27 cast per film, 6 films max). The caveat exists *because* the hub keeps its smaller game.
- Recomputing true Bacon numbers. CinePerks owns those; WSYATM is recomputing its own under its D74 (separate Firebase project, not ours).
- Writing anything back to any Firestore.

## Anti-goals

- **A link to a domain that doesn't serve.** No invite ships until `https://wsyatm.626labs.dev/bacon-trail` loads with a valid cert and signup works there.
- **A false "not available here".** If reachability is unknown (not checked yet, check failed), the card makes no claim either way. Silence over a wrong caveat.
- **A number the player just beat**, or "shortest route" on a route that wasn't (the #310 rule).

## Copy

Este approved the shape; exact wording is the builder's within these lines (voice rules: sentence case, no emoji, periods at the end).

| Situation | Bacon line | Invite |
|---|---|---|
| Reachable here, win at stored n | `Maya Hawke has a Bacon number of 2. That's the shortest route.` | light |
| Reachable here, longer win or loss | `Maya Hawke has a Bacon number of 2.` | light |
| Not reachable here (win or loss) | `Maya Hawke has a Bacon number of 2 (path not available here).` | full-game |
| Player beat stored n | `Maya Hawke has a Bacon number of 2.` (player's count, never shortest) | light |
| Reachability unknown | as "reachable here" rows, no caveat | light |
| No stored number | no Bacon line | light |
| Kevin on his birthday (#309) | unchanged | light |

- **Light invite** (my wording, Este's "having fun, try it at…"): `Having fun? Play the full game at wsyatm.626labs.dev.`
- **Full-game invite** (Este's "for the full game sign up at…"): `The full game has more films and fuller casts. Sign up at wsyatm.626labs.dev.` It promises no specific route, on purpose (my call): the full game's picker offers its own ~20 of today's birthday actors (US Eastern) from its own database, so the player may not be able to start from the same actor there, and WSYATM's numbers live in a separate Firebase project and can differ. Its graph is roughly a superset of the hub's (every film with votes, top 50 cast), which is what "more films and fuller casts" says and no more.
- Both link to `https://wsyatm.626labs.dev/bacon-trail`. Logged-out visitors are redirected to `/login`, which shows signup first, so one link serves both cases. Plain link, same tab behavior as the existing CTA (builder's call), no tracking params unless GoatCounter outbound already needs one.

## How the hub knows reachability

A precompute, mirroring the widget exactly (`src/services/tmdbService.ts`):

- An actor's films: TMDB `person/{id}/movie_credits` cast, scored `popularity * ln(1 + max(0, vote_count))`, top 45.
- A film's cast: `movie/{id}/credits` cast sorted by `order` (missing order last), top 27.
- A route of n films: n hops actor → film (in actor's top 45) → co-actor (in film's top 27), the last film's top 27 containing Kevin Bacon (4724). Revisits are allowed in the search; the widget forbids them, but a shortest route never revisits, so this doesn't change the answer.

The question per actor is only: **is there a hub route with at most `stored` films?** Every stored number today is 1, 2 or 3 (275 / 4,168 / 479 actors; 2,930 have none; one is Kevin at 0). So the search is bounded at depth 3.

Suggested approach (builder may improve): memoized depth-limited search. `F0` = films whose top-27 cast includes Bacon. `reach(a, k)` = some film in top45(a) has Bacon in its top 27 (k ≥ 1), or has a top-27 co-actor c with `reach(c, k-1)`. Cache every TMDB response for the run; overlap between popular actors is heavy.

**Where it runs:** a new weekly workflow (TMDB data drifts slowly), reusing `VITE_TMDB_API_KEY`, with a retry+rebase push loop like every other bot here. It writes a committed cache, `widget-bacon-trail/data/hub-reach.json`: `{ "<actorId>": { "stored": 2, "reachable": true, "checkedAt": "2026-11-15" } }`. An entry is stale when the shard's stored number differs from the cached `stored`, or when it is `reachable: false` and older than 28 days (my call: TMDB popularity, votes and billing move the top-45 and top-27 cuts, so a "no route" can turn untrue while the stored number stays put; silence over a wrong caveat). The shard merge treats a stale entry as unknown (no `hubReachable`). A `true` doesn't expire: a route the job found is a route a player can find, and a later cut that removes it costs only a missing caveat. Recheck order each run: unchecked, then stored-number changed, then oldest `false`. A run can be budgeted (time or call cap) and resume next week; unchecked actors simply show no caveat.

**How the widget gets it:** `scripts/refresh-bacon-shards.mjs` (nightly) merges the cache into each shard actor as `hubReachable: true | false` (absent = unknown). The widget reads one more field off the actor it already has. No extra fetch at result time.

**Budget (estimate, builder to measure):** depth 1 is ~1 credits call per actor. Depth 2 is ~45 cast calls plus up to ~1,200 co-actor credits calls per actor before caching, most shared across actors. Depth 3 is the expensive tail (479 actors). TMDB allows roughly 40-50 requests per second; pace below that. First full run may take more than one weekly window, and that's fine (see budgeting above).

## Constraints

- No live search in the browser; the widget stays one static shard fetch plus TMDB calls it already makes.
- The cache and shards are public static files. `hubReachable` reveals nothing a player can't learn by playing.
- `site.json`-style surgical edit rules don't apply here (JSON written by bots), but keep the cache's key order stable so weekly diffs stay small.
- Bundle rebuilds happen in CI (`build-widget.yml`); don't commit a local bundle.

## Order of work

1. Domain live: `wsyatm.626labs.dev` serving with a valid cert, and the domain in the weseeyouatthemovies Firebase Auth authorized domains (Este, in progress 2026-11-10; DNS CNAME verified).
2. Reachability job + cache + shard merge. Can merge before the domain is live: the widget ignores `hubReachable` until step 3.
3. Widget copy: caveat + both invites, in one PR, merged only after step 1 checks out.

## Left to the builder

- Search algorithm details, caching, pacing, the run budget.
- Exact link placement and styling on the card (under the Bacon line, above the trail, is the starting guess).
- Whether the workflow also runs on `workflow_dispatch` for a first backfill (probably yes).
- Tests: the display rule table above as unit tests; the search against a small fixture graph.
