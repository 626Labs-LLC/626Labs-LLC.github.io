import { describe, it, expect } from 'vitest';
import { generateRounds, pointsFor } from './rounds';
import { MOVIES } from '../shared/movies';

describe('generateRounds', () => {
  it('produces the requested number of rounds, 4 posters each, answer present', () => {
    for (let i = 0; i < 20; i++) {
      const rounds = generateRounds(8);
      expect(rounds).toHaveLength(8);
      for (const r of rounds) {
        expect(r.posters).toHaveLength(4);
        expect(r.posters.map((p) => p.movieId)).toContain(r.correctMovieId);
        // no duplicate posters within a round
        expect(new Set(r.posters.map((p) => p.movieId)).size).toBe(4);
      }
    }
  });

  it('never repeats a tagline within a session', () => {
    for (let i = 0; i < 20; i++) {
      const taglines = generateRounds(8).map((r) => r.tagline);
      expect(new Set(taglines).size).toBe(taglines.length);
    }
  });

  it('the correct answer really carries the shown tagline', () => {
    for (const r of generateRounds(8)) {
      const answer = MOVIES.find((mv) => mv.id === r.correctMovieId);
      expect(answer?.tagline).toBe(r.tagline);
    }
  });

  it('the roster carries enough taglined movies for a session', () => {
    const eligible = MOVIES.filter((mv) => mv.tagline && mv.posterUrl);
    expect(eligible.length).toBeGreaterThanOrEqual(16);
  });
});

describe('pointsFor', () => {
  it('follows the 10/5/2 ladder', () => {
    expect(pointsFor(0)).toBe(10);
    expect(pointsFor(1)).toBe(5);
    expect(pointsFor(2)).toBe(2);
    expect(pointsFor(3)).toBe(2);
  });
});
