import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { fetchTodayShard, getTodayKey } from '../services/shardService';

describe('getTodayKey', () => {
  it('returns MM-DD format with zero-padding', () => {
    expect(getTodayKey(new Date(2026, 3, 5))).toBe('04-05'); // April 5 (0-indexed month)
    expect(getTodayKey(new Date(2026, 10, 23))).toBe('11-23');
    expect(getTodayKey(new Date(2026, 0, 1))).toBe('01-01');
    expect(getTodayKey(new Date(2026, 11, 31))).toBe('12-31');
  });
});

describe('fetchTodayShard', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it('fetches and parses the expected URL for today', async () => {
    const mockShard = {
      date: '04-23',
      actors: [
        { id: 1, name: 'John Hannah', profilePath: '/abc.jpg', popularity: 2.4, baconNumber: 2 },
      ],
    };
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      json: async () => mockShard,
    } as Response);

    const actors = await fetchTodayShard(new Date(2026, 3, 23));
    expect(fetch).toHaveBeenCalledWith(
      '/widget-bacon-trail/data/birthdays/04-23.json',
      expect.any(Object)
    );
    expect(actors).toHaveLength(1);
    expect(actors[0]?.name).toBe('John Hannah');
  });

  it('retries on failure before giving up', async () => {
    (fetch as ReturnType<typeof vi.fn>)
      .mockRejectedValueOnce(new Error('network'))
      .mockRejectedValueOnce(new Error('network'))
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        json: async () => ({ date: '04-23', actors: [] }),
      } as Response);

    const actors = await fetchTodayShard(new Date(2026, 3, 23));
    expect(actors).toEqual([]);
    expect(fetch).toHaveBeenCalledTimes(3); // initial + 2 retries
  });

  it('throws on 404 after retries', async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: async () => ({}),
    } as Response);

    await expect(fetchTodayShard(new Date(2026, 3, 23))).rejects.toThrow(/404/);
  });

  it('throws on malformed JSON (missing actors array)', async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      json: async () => ({ date: '04-23' }), // no actors
    } as Response);

    await expect(fetchTodayShard(new Date(2026, 3, 23))).rejects.toThrow(/Malformed shard/);
  });
});
