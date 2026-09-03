import { describe, it, expect } from 'vitest';
import { generateMatchups, getWinner } from './matchups';
import { buildMovie, calcTier, type RawMovie } from '../shared/data';
import roster from '../../data/roster.json';

const MOVIES = (roster as RawMovie[]).filter((m) => m.posterPath).map(buildMovie);

describe('roster source', () => {
  it('has enough postered movies to deal a game', () => {
    expect(MOVIES.length).toBeGreaterThanOrEqual(10);
  });

  it('has no duplicate title+year entries', () => {
    const keys = (roster as RawMovie[]).map((m) => m.title.toLowerCase() + m.year);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it('every entry has plausible opening-weekend data', () => {
    for (const m of roster as RawMovie[]) {
      expect(m.openingWeekend).toBeGreaterThan(100_000);
      expect(m.openingWeekend).toBeLessThan(500_000_000);
      expect(m.year).toBeGreaterThanOrEqual(1970);
    }
  });

  it('tiers follow the opening-weekend thresholds', () => {
    for (const mv of MOVIES) {
      expect(mv.tier).toBe(calcTier(mv.openingWeekend));
    }
  });
});

describe('generateMatchups', () => {
  it('produces the requested number of rounds with no repeated movies', () => {
    for (let i = 0; i < 20; i++) {
      const matchups = generateMatchups(MOVIES, 10);
      expect(matchups).toHaveLength(10);
      const ids = matchups.flatMap((mu) => [mu.movieA.id, mu.movieB.id]);
      expect(new Set(ids).size).toBe(ids.length);
    }
  });

  it('never pairs a movie against itself', () => {
    for (let i = 0; i < 20; i++) {
      for (const mu of generateMatchups(MOVIES, 10)) {
        expect(mu.movieA.id).not.toBe(mu.movieB.id);
      }
    }
  });

  it('getWinner returns the bigger opener', () => {
    for (const mu of generateMatchups(MOVIES, 10)) {
      const w = getWinner(mu);
      const l = w.id === mu.movieA.id ? mu.movieB : mu.movieA;
      expect(w.openingWeekend).toBeGreaterThanOrEqual(l.openingWeekend);
    }
  });
});
