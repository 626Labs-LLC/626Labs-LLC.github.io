import { KEVIN_BACON_TMDB_ID, type Actor } from '../types';

// Single-line wrapper — isolated so we can unit-test the rule by passing in
// synthetic cast arrays, and so spec callers have one place to import from
// if the rule ever changes (e.g., "find Bacon OR a Bacon co-star").
export function castIncludesBacon(cast: Actor[]): boolean {
  return cast.some((actor) => actor.id === KEVIN_BACON_TMDB_ID);
}
