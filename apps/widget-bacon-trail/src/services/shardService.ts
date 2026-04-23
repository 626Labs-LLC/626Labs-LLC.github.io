import type { Actor, BirthdayShard } from '../types';

// Runtime base — where the widget fetches shards from. Overridable for
// tests (vitest mocks the `fetch` URL directly; dev mode uses the default
// because Vite proxies from the hub root at the same path).
const SHARD_BASE = '/widget-bacon-trail/data/birthdays';

// Format today's date as MM-DD in the user's local time zone. Fallback-safe
// against unusual locale behaviors: pads month + day to two digits manually.
export function getTodayKey(now: Date = new Date()): string {
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${month}-${day}`;
}

async function fetchShardUrl(url: string, attempts = 2): Promise<BirthdayShard> {
  let lastError: unknown;
  for (let attempt = 0; attempt <= attempts; attempt++) {
    try {
      const res = await fetch(url, { headers: { Accept: 'application/json' } });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const body = (await res.json()) as BirthdayShard;
      if (!Array.isArray(body.actors)) {
        throw new Error('Malformed shard: missing or non-array `actors`.');
      }
      return body;
    } catch (err) {
      lastError = err;
      if (attempt < attempts) {
        const delayMs = 500 * Math.pow(2, attempt);
        await new Promise((resolve) => setTimeout(resolve, delayMs));
      }
    }
  }
  throw lastError;
}

// Fetch today's birthday shard. Callers pass the current Date (or omit for
// `new Date()`). Returns the raw Actor[] since that's what the reducer
// consumes.
export async function fetchTodayShard(now: Date = new Date()): Promise<Actor[]> {
  const key = getTodayKey(now);
  const url = `${SHARD_BASE}/${key}.json`;
  const shard = await fetchShardUrl(url);
  return shard.actors;
}

// Optional helper for future "show birthdays around today" fallback when the
// current day's shard has < BIRTHDAY_GRID_SIZE entries. Unused in v1 but kept
// typed and importable.
export async function fetchShardsAroundToday(
  now: Date = new Date(),
  radiusDays = 3
): Promise<Actor[]> {
  const base = new Date(now.getTime());
  const keys = new Set<string>();
  for (let offset = -radiusDays; offset <= radiusDays; offset++) {
    const d = new Date(base.getTime());
    d.setDate(base.getDate() + offset);
    keys.add(getTodayKey(d));
  }
  const shards = await Promise.allSettled(
    [...keys].map((k) => fetchShardUrl(`${SHARD_BASE}/${k}.json`))
  );
  const actors: Actor[] = [];
  for (const s of shards) {
    if (s.status === 'fulfilled') actors.push(...s.value.actors);
  }
  return actors;
}
