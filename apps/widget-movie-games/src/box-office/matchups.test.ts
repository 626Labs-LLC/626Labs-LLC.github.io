import { describe, it, expect } from 'vitest';
import { generateMatchups, getWinner } from './matchups';
import { MOVIES } from '../shared/movies';

describe('generateMatchups', () => {
  it('produces the requested number of rounds with no repeated movies', () => {
    for (let i = 0; i < 20; i++) {
      const matchups = generateMatchups(10);
      expect(matchups).toHaveLength(10);
      const ids = matchups.flatMap((mu) => [mu.movieA.id, mu.movieB.id]);
      expect(new Set(ids).size).toBe(ids.length);
    }
  });

  it('never pairs a movie against itself', () => {
    for (let i = 0; i < 20; i++) {
      for (const mu of generateMatchups(10)) {
        expect(mu.movieA.id).not.toBe(mu.movieB.id);
      }
    }
  });

  it('getWinner returns the bigger opener', () => {
    for (const mu of generateMatchups(10)) {
      const w = getWinner(mu);
      const l = w.id === mu.movieA.id ? mu.movieB : mu.movieA;
      expect(w.openingWeekend).toBeGreaterThanOrEqual(l.openingWeekend);
    }
  });
});

describe('roster', () => {
  it('every movie has a poster path', () => {
    const missing = MOVIES.filter((mv) => !mv.posterUrl);
    expect(missing.map((mv) => mv.id)).toEqual([]);
  });

  it('tiers follow the opening-weekend thresholds', () => {
    for (const mv of MOVIES) {
      const expected =
        mv.openingWeekend >= 150_000_000 ? 1
        : mv.openingWeekend >= 80_000_000 ? 2
        : mv.openingWeekend >= 40_000_000 ? 3
        : 4;
      expect(mv.tier).toBe(expected);
    }
  });
});
