// The hub's Bacon-number ranking rules and a bounded route search.
// Mirrors apps/widget-bacon-trail/src/services/tmdbService.ts so a route the
// job finds is a route a player can actually walk on the hub.

export const KEVIN_BACON_ID = 4724;
export const FILMS_PER_ACTOR = 45;
export const CAST_PER_FILM = 27;

export class BudgetExceeded extends Error {
  constructor(message = "request budget exceeded") {
    super(message);
    this.name = "BudgetExceeded";
  }
}

// Film ids in hub order: popularity * ln(1 + votes) desc, first 45.
export function topFilms(creditsCast) {
  const score = (m) => (m.popularity ?? 0) * Math.log(1 + Math.max(0, m.vote_count ?? 0));
  return [...creditsCast].sort((a, b) => score(b) - score(a)).slice(0, FILMS_PER_ACTOR).map((m) => m.id);
}

// Actor ids in hub order: billing order asc, missing order last, first 27.
export function topCast(movieCast) {
  const order = (a) => a.order ?? Number.MAX_SAFE_INTEGER;
  return [...movieCast].sort((a, b) => order(a) - order(b)).slice(0, CAST_PER_FILM).map((a) => a.id);
}

// reachableWithin(a, k): some film of a has Bacon in its cast (k >= 1), or
// (k >= 2) some co-actor in those casts reaches him within k - 1 films.
// Every film is checked for a direct hit before recursing into any co-actor.
export function createSearch({ getFilms, getCast }) {
  const filmsMemo = new Map();
  const castMemo = new Map();
  const minTrue = new Map(); // actor -> smallest k known true
  const maxFalse = new Map(); // actor -> largest k known false

  const memo = (map, key, fn) => {
    if (!map.has(key)) map.set(key, fn(key));
    return map.get(key);
  };

  async function reachableWithin(actorId, maxFilms) {
    if (maxFilms < 1) return false;
    if (minTrue.has(actorId) && minTrue.get(actorId) <= maxFilms) return true;
    if (maxFalse.has(actorId) && maxFalse.get(actorId) >= maxFilms) return false;

    const filmIds = await memo(filmsMemo, actorId, getFilms);
    const casts = [];
    for (const f of filmIds) casts.push(await memo(castMemo, f, getCast));

    let found = casts.some((c) => c.includes(KEVIN_BACON_ID));
    if (!found && maxFilms >= 2) {
      const tried = new Set([actorId]);
      outer: for (const c of casts) {
        for (const co of c) {
          if (tried.has(co)) continue;
          tried.add(co);
          if (await reachableWithin(co, maxFilms - 1)) { found = true; break outer; }
        }
      }
    }

    if (found) minTrue.set(actorId, Math.min(minTrue.get(actorId) ?? Infinity, maxFilms));
    else maxFalse.set(actorId, Math.max(maxFalse.get(actorId) ?? 0, maxFilms));
    return found;
  }

  return { reachableWithin };
}
