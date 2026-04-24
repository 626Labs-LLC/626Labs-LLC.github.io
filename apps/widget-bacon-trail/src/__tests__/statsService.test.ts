import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { fetchLifetimeStats, EMPTY_STATS } from '../services/statsService';

describe('fetchLifetimeStats', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('parses a well-formed snapshot', async () => {
    const payload = {
      totalPlayed: 1234,
      totalFound: 567,
      totalOutOfFilms: 667,
      winsByFilms: { '1': 100, '2': 200, '3': 150, '7': 99 }, // 7 is out-of-range, filtered
      updatedAt: '2026-04-24T06:00:00Z',
    };
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => payload,
    } as Response);

    const stats = await fetchLifetimeStats();
    expect(stats.totalPlayed).toBe(1234);
    expect(stats.totalFound).toBe(567);
    expect(stats.totalOutOfFilms).toBe(667);
    expect(stats.winsByFilms[1]).toBe(100);
    expect(stats.winsByFilms[2]).toBe(200);
    expect(stats.winsByFilms[3]).toBe(150);
    expect(stats.winsByFilms[7]).toBeUndefined(); // out of 1-6 range
    expect(stats.updatedAt).toBe('2026-04-24T06:00:00Z');
  });

  it('returns EMPTY_STATS on 404', async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue({ ok: false } as Response);
    const stats = await fetchLifetimeStats();
    expect(stats).toEqual(EMPTY_STATS);
  });

  it('returns EMPTY_STATS on network error', async () => {
    (fetch as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('offline'));
    const stats = await fetchLifetimeStats();
    expect(stats).toEqual(EMPTY_STATS);
  });

  it('returns EMPTY_STATS on malformed JSON', async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => 'garbage',
    } as Response);
    const stats = await fetchLifetimeStats();
    expect(stats).toEqual(EMPTY_STATS);
  });

  it('coerces non-number fields safely', async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => ({ totalPlayed: 'lots', totalFound: null }),
    } as Response);
    const stats = await fetchLifetimeStats();
    expect(stats.totalPlayed).toBe(0);
    expect(stats.totalFound).toBe(0);
  });
});
