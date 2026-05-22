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

// GoatCounter's /stats/total endpoint started returning 404 when given
// date-only strings — its OpenAPI spec calls for "date-time, rounded to
// the hour". Send full RFC3339 datetimes so /stats/total accepts the
// request. The other endpoints have always been lenient about date-only
// but accept the stricter format too, so we standardize on it.
function isoHourFloor(ms) {
  return new Date(ms).toISOString().slice(0, 13) + ':00:00Z';
}

const today = isoDate(Date.now());
const start = isoDate(Date.now() - DAYS * 24 * 60 * 60 * 1000);
const startParam = isoHourFloor(Date.now() - DAYS * 24 * 60 * 60 * 1000);
const endParam = isoHourFloor(Date.now());
const params = `start=${encodeURIComponent(startParam)}&end=${encodeURIComponent(endParam)}`;

async function gc(endpoint, attempts = 4) {
  // GoatCounter's free-tier API rate-limits aggressively (~5 req/sec), and
  // around its daily stats-aggregation window (~06:30 UTC — exactly when this
  // job is scheduled) /stats/total intermittently returns a transient 404:
  // the request is well-formed and the token is valid, the resource is just
  // briefly unavailable. So we retry on 429, 404, and 5xx (and on network
  // errors), not 429 alone — otherwise the `attempts: 8` on /stats/total is
  // dead weight, because a 404 used to throw on the first try.
  //
  // 429 carries a wait-hint in its body:
  //   {"error": "rate limited exceeded; try again in 992.116994ms"}
  // We honor that hint; everything else uses exponential backoff (1.5s, 3s,
  // 6s, ...) capped at 30s.
  const url = `${GC_BASE}${endpoint}`;
  const retryable = (status) => status === 429 || status === 404 || status >= 500;
  const backoff = (attempt) => Math.min(30000, Math.round(1500 * Math.pow(2, attempt)));
  for (let attempt = 0; attempt < attempts; attempt++) {
    let res;
    try {
      res = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
          'User-Agent': '626labs-hub-site-stats',
        },
      });
    } catch (err) {
      // Network / DNS hiccup — retryable.
      if (attempt < attempts - 1) {
        const waitMs = backoff(attempt);
        console.warn(`  retry ${attempt + 1}/${attempts - 1} on ${endpoint} after ${waitMs}ms (network: ${err.message})`);
        await new Promise(r => setTimeout(r, waitMs));
        continue;
      }
      throw new Error(`GET ${endpoint} -> network error: ${err.message}`);
    }
    if (res.ok) return res.json();
    const body = await res.text();
    if (retryable(res.status) && attempt < attempts - 1) {
      const m = res.status === 429 ? body.match(/(\d+(?:\.\d+)?)\s*ms/i) : null;
      const hint = m ? Math.ceil(parseFloat(m[1])) : null;
      // 429: server's wait-hint + 250ms cushion. Otherwise exponential backoff.
      const waitMs = hint ? hint + 250 : backoff(attempt);
      console.warn(`  retry ${attempt + 1}/${attempts - 1} on ${endpoint} after ${waitMs}ms (${res.status})`);
      await new Promise(r => setTimeout(r, waitMs));
      continue;
    }
    throw new Error(`GET ${endpoint} -> ${res.status}: ${body.slice(0, 200)}`);
  }
}

// Soft fetch: tolerate individual endpoint failures so one persistently-
// rate-limited call doesn't break the entire snapshot. `attempts` is
// forwarded to gc() — pass a higher value for endpoints that must succeed
// (see /stats/total, which is load-bearing for the admin's top-bar totals).
async function softGc(endpoint, attempts) {
  try {
    return { ok: true, data: await gc(endpoint, attempts) };
  } catch (err) {
    console.warn(`! ${endpoint}: ${err.message}`);
    return { ok: false, error: err.message };
  }
}

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

console.log(`Fetching GoatCounter stats for 626labs.dev — ${start} → ${today}`);

// Sequential — Promise.all bursts trip GoatCounter's free-tier rate limit.
// Inter-call delay (300ms) gives the bucket time to refill so the retry-on-429
// path inside gc() rarely needs to fire.
async function step(label, endpoint, attempts) {
  const res = await softGc(endpoint, attempts);
  await sleep(300);
  return res;
}

// /stats/total is the source of truth for the admin's top-bar totals
// (data.total.total / total_unique). If it nulls out, the admin renders
// 0 with no visual tell — which is how "the bar shows zeros, refresh
// fixes it" failures land. Bump retries to 8 and abort on failure so we
// preserve the previous good snapshot rather than overwriting with nulls.
const total     = await step('total',     `/stats/total?${params}`, 8);
if (!total.ok) {
  console.error(`! /stats/total failed after retries — aborting without overwriting ${OUT_PATH}.`);
  console.error(`  reason: ${total.error}`);
  console.error(`  the previous snapshot stays in place; next scheduled run will retry.`);
  process.exit(1);
}
const hits      = await step('hits',      `/stats/hits?${params}&limit=${HITS_LIMIT}`);
const refs      = await step('refs',      `/stats/toprefs?${params}&limit=${REFS_LIMIT}`);
const locations = await step('locations', `/stats/locations?${params}&limit=${LOCATIONS_LIMIT}`);
const browsers  = await step('browsers',  `/stats/browsers?${params}&limit=${BROWSERS_LIMIT}`);
const systems   = await step('systems',   `/stats/systems?${params}&limit=${SYSTEMS_LIMIT}`);

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
