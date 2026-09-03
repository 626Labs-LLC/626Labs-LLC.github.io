import { describe, it, expect } from 'vitest';
import { generateRounds, pointsFor } from './rounds';
import type { PoolEntry, RawMovie } from '../shared/data';
import roster from '../../data/roster.json';

// Build the curated pool the same way scripts/refresh-game-data.mjs does.
const POOL: PoolEntry[] = (roster as RawMovie[])
  .filter((m) => m.tagline && m.posterPath)
  .map((m) => ({
    id: m.id,
    title: m.title,
    year: m.year,
    tagline: m.tagline!,
    posterPath: m.posterPath!,
    source: 'curated' as const,
  }));

describe('generateRounds', () => {
  it('the roster carries enough taglined+postered movies for a session', () => {
    expect(POOL.length).toBeGreaterThanOrEqual(8);
  });

  it('produces the requested number of rounds, 4 posters each, answer present', () => {
    for (let i = 0; i < 20; i++) {
      const rounds = generateRounds(POOL, 8);
      expect(rounds).toHaveLength(8);
      for (const r of rounds) {
        expect(r.posters).toHaveLength(4);
        expect(r.posters.map((p) => p.movieId)).toContain(r.correctMovieId);
        expect(new Set(r.posters.map((p) => p.movieId)).size).toBe(4);
      }
    }
  });

  it('never repeats a tagline within a session', () => {
    for (let i = 0; i < 20; i++) {
      const taglines = generateRounds(POOL, 8).map((r) => r.tagline);
      expect(new Set(taglines).size).toBe(taglines.length);
    }
  });

  it('the correct answer really carries the shown tagline', () => {
    for (const r of generateRounds(POOL, 8)) {
      const answer = POOL.find((e) => e.id === r.correctMovieId);
      expect(answer?.tagline).toBe(r.tagline);
    }
  });

  it('mixes swept entries into sessions when the pool has them', () => {
    const mixed: PoolEntry[] = [
      ...POOL,
      ...Array.from({ length: 20 }, (_, i) => ({
        id: `t${i}`,
        title: `Swept ${i}`,
        year: 2025,
        tagline: `A perfectly serviceable tagline number ${i}.`,
        posterPath: '/fake.jpg',
        source: 'tmdb' as const,
      })),
    ];
    let sweptSeen = 0;
    for (let i = 0; i < 10; i++) {
      const rounds = generateRounds(mixed, 8);
      sweptSeen += rounds.filter((r) => r.correctMovieId.startsWith('t')).length;
    }
    expect(sweptSeen).toBeGreaterThan(0);
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
