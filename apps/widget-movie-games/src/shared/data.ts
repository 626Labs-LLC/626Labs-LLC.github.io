// Shared data layer for both game widgets. The datasets live OUTSIDE the
// bundles as runtime JSON served by GitHub Pages (the bacon-shards
// pattern), so a roster or pool update is a data commit — no rebuild:
//
//   /widget-box-office/data/movies.json   {generated, movies: RawMovie[]}
//   /widget-tag-that-line/data/pool.json  {generated, entries: PoolEntry[]}
//
// Source of truth is apps/widget-movie-games/data/roster.json;
// scripts/refresh-game-data.mjs (weekly CI) regenerates both runtime files
// and resolves poster paths via TMDB. Opening-weekend numbers are
// hand-verified in the roster and never fetched.

const TMDB_IMG = 'https://image.tmdb.org/t/p/w342';

export type RawMovie = {
  id: string;
  title: string;
  year: number;
  genre: string;
  rating: string;
  openingWeekend: number;
  posterPath?: string;
  funFact?: string;
  tagline?: string;
};

export type Movie = RawMovie & {
  tier: 1 | 2 | 3 | 4;
  posterUrl: string;
};

export type PoolEntry = {
  id: string;
  title: string;
  year: number;
  tagline: string;
  posterPath: string;
  source: 'curated' | 'tmdb';
};

export function calcTier(opening: number): 1 | 2 | 3 | 4 {
  if (opening >= 150_000_000) return 1;
  if (opening >= 80_000_000) return 2;
  if (opening >= 40_000_000) return 3;
  return 4;
}

export function buildMovie(raw: RawMovie): Movie {
  return {
    ...raw,
    tier: calcTier(raw.openingWeekend),
    posterUrl: raw.posterPath ? `${TMDB_IMG}${raw.posterPath}` : '',
  };
}

export function posterUrl(posterPath: string): string {
  return `${TMDB_IMG}${posterPath}`;
}

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`${url} -> HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

export async function loadRoster(): Promise<Movie[]> {
  const data = await fetchJson<{ movies: RawMovie[] }>(
    '/widget-box-office/data/movies.json'
  );
  const movies = (data.movies ?? []).filter((m) => m.posterPath).map(buildMovie);
  if (movies.length < 10) throw new Error('roster too small to deal a game');
  return movies;
}

export async function loadPool(): Promise<PoolEntry[]> {
  const data = await fetchJson<{ entries: PoolEntry[] }>(
    '/widget-tag-that-line/data/pool.json'
  );
  const entries = (data.entries ?? []).filter((e) => e.tagline && e.posterPath);
  if (entries.length < 8) throw new Error('tagline pool too small to deal a game');
  return entries;
}

export function shuffle<T>(arr: readonly T[]): T[] {
  const copy = [...arr];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

export function formatDollars(amount: number): string {
  if (amount >= 1_000_000_000) return `$${(amount / 1_000_000_000).toFixed(1)}B`;
  if (amount >= 1_000_000) return `$${(amount / 1_000_000).toFixed(1)}M`;
  return `$${amount.toLocaleString()}`;
}

export function formatDollarsFull(amount: number): string {
  return `$${amount.toLocaleString()}`;
}
