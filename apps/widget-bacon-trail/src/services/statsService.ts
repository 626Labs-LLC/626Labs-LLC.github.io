import type { Outcome } from '../types';

// Anonymous lifetime counters. Zero visitor data on the wire.
//
// Write path:  fire-and-forget POST to a Cloud Function that validates
//              the payload shape and atomically increments a single
//              Firestore counter doc at stats/play-counters.
// Read path:   a static JSON snapshot regenerated nightly by the same
//              GitHub Action that refreshes birthday shards. Ambient
//              display, not real-time — "up to 24h stale" is fine for
//              lifetime counters.

// Endpoint URL baked at build time. Falls back to undefined if the CI
// secret wasn't populated (dev mode without VITE_STATS_ENDPOINT set
// just skips writes — matches the graceful-degradation pattern).
const STATS_POST_URL = import.meta.env.VITE_STATS_ENDPOINT as string | undefined;
const STATS_READ_URL = '/widget-bacon-trail/data/stats.json';

export interface LifetimeStats {
  totalPlayed: number;
  totalFound: number;
  totalOutOfFilms: number;
  // Wins by film-count bucket (1 through 6).
  winsByFilms: Record<number, number>;
  // ISO timestamp of when the snapshot was written.
  updatedAt: string | null;
}

export const EMPTY_STATS: LifetimeStats = {
  totalPlayed: 0,
  totalFound: 0,
  totalOutOfFilms: 0,
  winsByFilms: {},
  updatedAt: null,
};

// Fetch the nightly stats snapshot. Resolves to EMPTY_STATS on any
// failure (404, parse error, network) so the UI never blocks on this.
export async function fetchLifetimeStats(): Promise<LifetimeStats> {
  try {
    const res = await fetch(STATS_READ_URL, { headers: { Accept: 'application/json' } });
    if (!res.ok) return EMPTY_STATS;
    const body = (await res.json()) as Partial<LifetimeStats> | null;
    if (!body || typeof body !== 'object') return EMPTY_STATS;
    return {
      totalPlayed: toNumber(body.totalPlayed),
      totalFound: toNumber(body.totalFound),
      totalOutOfFilms: toNumber(body.totalOutOfFilms),
      winsByFilms: normalizeWinBuckets(body.winsByFilms),
      updatedAt: typeof body.updatedAt === 'string' ? body.updatedAt : null,
    };
  } catch {
    return EMPTY_STATS;
  }
}

// Fire-and-forget. Never throws. If the endpoint isn't configured
// (dev, or the secret hasn't been baked into the build), silently
// no-ops — the widget still works, just doesn't record the round.
export function logPlay(outcome: Outcome, filmCount: number): void {
  if (!STATS_POST_URL) return;
  const body = JSON.stringify({ outcome, filmCount });
  try {
    // keepalive lets the request complete even if the user navigates
    // away mid-send. No Response is inspected; no await; errors
    // swallowed. sendBeacon would work too but isn't available
    // everywhere with the CORS posture we need.
    void fetch(STATS_POST_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
      keepalive: true,
      mode: 'cors',
    }).catch(() => {});
  } catch {
    // Best-effort only. Never block the UI.
  }
}

function toNumber(v: unknown): number {
  return typeof v === 'number' && Number.isFinite(v) ? v : 0;
}

function normalizeWinBuckets(raw: unknown): Record<number, number> {
  if (!raw || typeof raw !== 'object') return {};
  const out: Record<number, number> = {};
  for (const [k, v] of Object.entries(raw as Record<string, unknown>)) {
    const n = Number.parseInt(k, 10);
    if (Number.isFinite(n) && n >= 1 && n <= 6) {
      out[n] = toNumber(v);
    }
  }
  return out;
}
