// Matchup generator — ported from WSYATM's movieService.ts (vibe-taker
// bundle box-office-heads-up v1). Tier-adjacency pairing keeps contests
// competitive: a tier-1 monster never faces a tier-4 sleeper unless the
// pool runs dry late in a session.
import { MOVIES, shuffle, type Movie } from '../shared/movies';

export type Matchup = {
  movieA: Movie;
  movieB: Movie;
  round: number;
};

const ADJACENT_TIERS: Record<number, number[]> = {
  1: [1, 2],
  2: [1, 2, 3],
  3: [2, 3, 4],
  4: [3, 4],
};

export function generateMatchups(totalRounds = 10): Matchup[] {
  const pool = shuffle(MOVIES);
  const used = new Set<string>();
  const matchups: Matchup[] = [];

  for (let round = 1; round <= totalRounds; round++) {
    const first = pool.find((mv) => !used.has(mv.id));
    if (!first) break;
    used.add(first.id);

    const validTiers = ADJACENT_TIERS[first.tier];
    const partner = pool.find(
      (mv) => !used.has(mv.id) && validTiers.includes(mv.tier)
    );

    if (!partner) {
      const fallback = pool.find((mv) => !used.has(mv.id));
      if (!fallback) break;
      used.add(fallback.id);
      matchups.push({ movieA: first, movieB: fallback, round });
    } else {
      used.add(partner.id);
      if (Math.random() > 0.5) {
        matchups.push({ movieA: first, movieB: partner, round });
      } else {
        matchups.push({ movieA: partner, movieB: first, round });
      }
    }
  }

  return matchups;
}

export function getWinner(matchup: Matchup): Movie {
  return matchup.movieA.openingWeekend >= matchup.movieB.openingWeekend
    ? matchup.movieA
    : matchup.movieB;
}

export function getFunFact(matchup: Matchup): string | null {
  const winner = getWinner(matchup);
  const loser =
    winner.id === matchup.movieA.id ? matchup.movieB : matchup.movieA;
  return winner.funFact ?? loser.funFact ?? null;
}
