#!/usr/bin/env node
// Fetch GoatCounter site stats for 626labs.dev and write a single JSON
// snapshot to data/site-stats.json. The admin's Analytics panel reads
// this committed JSON via the GitHub Contents API.
//
// We do this server-side instead of letting the admin hit GoatCounter
// directly because:
//   1. GoatCounter's free-tier API rate-limits aggressively (429s on
//      back-to-back calls).
//   2. /stats/hits in particular doesn't pass CORS preflight from the
//      browser, even with a valid Authorization header.
//   3. The token then doesn't have to live in any visitor's localStorage.
//
// Env: GOATCOUNTER_TOKEN — API token with at least `count` + `read stats`
// permission. Generate at https://626labs.goatcounter.com/user/api.
//
// Range: rolling 30 days.

import { writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';

const GC_BASE = 'https://626labs.goatcounter.com/api/v0';
const OUT_PATH = 'data/site-stats.json';
const DAYS = 30;
const HITS_LIMIT = 20;
const REFS_LIMIT = 20;
const LOCATIONS_LIMIT = 12;
const BROWSERS_LIMIT = 8;
const SYSTEMS_LIMIT = 6;

const token = process.env.GOATCOUNTER_TOKEN;
if (!token) {
  console.error('GOATCOUNTER_TOKEN is required');
  process.exit(1);
}

function isoDate(ms) {
  return new Date(ms).toISOString().slice(0, 10);
}

const today = isoDate(Date.now());
const start = isoDate(Date.now() - DAYS * 24 * 60 * 60 * 1000);
const params = `start=${start}&end=${today}`;

async function gc(endpoint) {
  const url = `${GC_BASE}${endpoint}`;
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
      'User-Agent': '626labs-hub-site-stats',
    },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`GET ${endpoint} -> ${res.status}: ${body.slice(0, 200)}`);
  }
  return res.json();
}

// Soft fetch: tolerate individual endpoint failures so one rate-limited
// call doesn't break the entire snapshot.
async function softGc(endpoint) {
  try {
    return { ok: true, data: await gc(endpoint) };
  } catch (err) {
    console.warn(`! ${endpoint}: ${err.message}`);
    return { ok: false, error: err.message };
  }
}

console.log(`Fetching GoatCounter stats for 626labs.dev — ${start} → ${today}`);

const [total, hits, refs, locations, browsers, systems] = await Promise.all([
  softGc(`/stats/total?${params}`),
  softGc(`/stats/hits?${params}&limit=${HITS_LIMIT}`),
  softGc(`/stats/toprefs?${params}&limit=${REFS_LIMIT}`),
  softGc(`/stats/locations?${params}&limit=${LOCATIONS_LIMIT}`),
  softGc(`/stats/browsers?${params}&limit=${BROWSERS_LIMIT}`),
  softGc(`/stats/systems?${params}&limit=${SYSTEMS_LIMIT}`),
]);

const errors = [total, hits, refs, locations, browsers, systems]
  .map((r, i) => r.ok ? null : { endpoint: ['total','hits','refs','locations','browsers','systems'][i], error: r.error })
  .filter(Boolean);

const payload = {
  generatedAt: new Date().toISOString(),
  source: 'goatcounter',
  site: '626labs.dev',
  range: { start, end: today, days: DAYS },
  total:     total.ok     ? total.data     : null,
  hits:      hits.ok      ? hits.data      : null,
  refs:      refs.ok      ? refs.data      : null,
  locations: locations.ok ? locations.data : null,
  browsers:  browsers.ok  ? browsers.data  : null,
  systems:   systems.ok   ? systems.data   : null,
  errors: errors.length ? errors : undefined,
};

await mkdir(path.dirname(OUT_PATH), { recursive: true });
await writeFile(OUT_PATH, JSON.stringify(payload, null, 2) + '\n', 'utf8');
console.log(`Wrote ${OUT_PATH} — ${payload.total?.total ?? '?'} views, ${payload.total?.total_unique ?? '?'} unique over ${DAYS} days.`);

if (errors.length) {
  console.warn(`${errors.length} endpoint(s) failed; partial snapshot written.`);
  // Partial success — don't fail the workflow; admin will surface what we got.
  process.exit(0);
}
