// Refresh the movie-game runtime datasets served by GitHub Pages.
//
// Source of truth: apps/widget-movie-games/data/roster.json — the curated
// film list (opening weekends, taglines, fun facts). This script turns it
// into the two runtime files the widgets fetch at mount:
//
//   widget-box-office/data/movies.json    — every roster entry with a poster
//   widget-tag-that-line/data/pool.json   — curated taglined entries + a
//                                           TMDB popular/top-rated sweep
//
// With TMDB_API_KEY set (CI passes the repo's VITE_TMDB_API_KEY secret) it
// also resolves posterPaths for roster entries that lack one (TMDB title+
// year search) and widens the tagline pool from TMDB. Without a key it
// degrades gracefully: no network, runtime files rebuilt from whatever the
// roster already resolves — so a local run is always safe.
//
// Opening-weekend numbers are NEVER fetched — TMDB doesn't carry them and
// the roster's hand-verified figures are the game's source of truth.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const ROSTER = path.join(ROOT, 'apps', 'widget-movie-games', 'data', 'roster.json');
const OUT_MOVIES = path.join(ROOT, 'widget-box-office', 'data', 'movies.json');
const OUT_POOL = path.join(ROOT, 'widget-tag-that-line', 'data', 'pool.json');

const API_KEY = process.env.TMDB_API_KEY ?? '';
const TMDB = 'https://api.themoviedb.org/3';
// Sweep breadth: 2 pages each of popular + top_rated ≈ 80 candidates/run.
const SWEEP = [
  ['popular', 1], ['popular', 2],
  ['top_rated', 1], ['top_rated', 2],
];

async function tmdb(pathname, params = {}) {
  const url = new URL(TMDB + pathname);
  url.searchParams.set('api_key', API_KEY);
  url.searchParams.set('language', 'en-US');
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  const res = await fetch(url);
  if (!res.ok) throw new Error(`TMDB ${pathname} -> HTTP ${res.status}`);
  return res.json();
}

function normTitle(t) {
  return t.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
}

async function resolvePoster(entry) {
  // Exact-normalized-title match within ±1 year, searched twice: first with
  // TMDB's hard primary_release_year filter, then without it (a roster year
  // one off from TMDB's primary date otherwise filters the real film out —
  // that exact miss once matched American Sniper to its making-of doc).
  // No blind first-result fallback: a wrong poster is worse than none.
  const want = normTitle(entry.title);
  const attempts = [
    { query: entry.title, primary_release_year: entry.year },
    { query: entry.title },
  ];
  for (const params of attempts) {
    const data = await tmdb('/search/movie', params);
    const hit = (data.results ?? []).find((r) => {
      const year = parseInt((r.release_date ?? '').slice(0, 4), 10);
      return (
        r.poster_path &&
        Math.abs((year || 0) - entry.year) <= 1 &&
        (normTitle(r.title) === want || normTitle(r.original_title ?? '') === want)
      );
    });
    if (hit) return hit.poster_path;
  }
  return null;
}

async function main() {
  const roster = JSON.parse(fs.readFileSync(ROSTER, 'utf8'));
  const generated = new Date().toISOString();
  let resolved = 0;
  let sweepCount = 0;

  if (API_KEY) {
    for (const entry of roster) {
      if (entry.posterPath) continue;
      try {
        const p = await resolvePoster(entry);
        if (p) {
          entry.posterPath = p;
          resolved += 1;
        } else {
          console.warn(`no poster match: ${entry.title} (${entry.year})`);
        }
      } catch (err) {
        console.warn(`poster lookup failed for ${entry.title}: ${err.message}`);
      }
    }
    if (resolved > 0) {
      // Cache resolutions back into the roster so future keyless runs keep
      // the full postered set.
      fs.writeFileSync(ROSTER, JSON.stringify(roster, null, 2) + '\n');
    }
  } else {
    console.log('TMDB_API_KEY unset — skipping poster resolution and pool sweep.');
  }

  const postered = roster.filter((m) => m.posterPath);
  fs.mkdirSync(path.dirname(OUT_MOVIES), { recursive: true });
  fs.writeFileSync(
    OUT_MOVIES,
    JSON.stringify({ generated, movies: postered }, null, 2) + '\n'
  );

  // Tagline pool: curated first (they carry the classics), TMDB sweep after.
  const curated = postered
    .filter((m) => m.tagline)
    .map((m) => ({
      id: m.id,
      title: m.title,
      year: m.year,
      tagline: m.tagline,
      posterPath: m.posterPath,
      source: 'curated',
    }));
  const seen = new Set(curated.map((e) => normTitle(e.title) + e.year));
  const pool = [...curated];

  if (API_KEY) {
    const candidates = new Map();
    for (const [list, page] of SWEEP) {
      try {
        const data = await tmdb(`/movie/${list}`, { page, region: 'US' });
        for (const r of data.results ?? []) {
          if (r.poster_path && !candidates.has(r.id)) candidates.set(r.id, r);
        }
      } catch (err) {
        console.warn(`sweep ${list} p${page} failed: ${err.message}`);
      }
    }
    for (const r of candidates.values()) {
      try {
        const detail = await tmdb(`/movie/${r.id}`);
        const tagline = (detail.tagline ?? '').trim();
        const year = parseInt((detail.release_date ?? '').slice(0, 4), 10);
        if (!tagline || tagline.length < 8 || !year) continue;
        const key = normTitle(detail.title) + year;
        if (seen.has(key)) continue;
        seen.add(key);
        pool.push({
          id: `t${r.id}`,
          title: detail.title,
          year,
          tagline,
          posterPath: detail.poster_path ?? r.poster_path,
          source: 'tmdb',
        });
        sweepCount += 1;
      } catch (err) {
        console.warn(`detail ${r.id} failed: ${err.message}`);
      }
    }
  }

  fs.mkdirSync(path.dirname(OUT_POOL), { recursive: true });
  fs.writeFileSync(
    OUT_POOL,
    JSON.stringify({ generated, entries: pool }, null, 2) + '\n'
  );

  console.log(
    `roster ${roster.length} (postered ${postered.length}, +${resolved} resolved) · ` +
    `pool ${pool.length} (${curated.length} curated, +${sweepCount} tmdb)`
  );
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
