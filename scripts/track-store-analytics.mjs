#!/usr/bin/env node
/**
 * Snapshot Microsoft Store analytics for the six 626 Labs Store apps into
 * data/store-analytics.json.
 *
 * Reads the legacy Dev Center analytics API (manage.devcenter.microsoft.com) with the
 * same Entra application the Store Listing Console's submission tools use:
 * STORE_TENANT_ID / STORE_CLIENT_ID / STORE_CLIENT_SECRET from the environment.
 * v1 auth: /oauth2/token with `resource`, NOT the v2 `scope` endpoint — the wrong pair
 * mints a token that authenticates fine and is rejected by every call.
 *
 * Endpoints (all verified live 2026-09-11): usagedaily, installs, appacquisitions,
 * ratings, failurehits. Rows come back segmented (market x deviceType x packageVersion),
 * so daily metrics are summed client-side per date. The API rate-limits aggressively
 * (429s observed between rapid calls), so every request is paced — the whole run is
 * ~30 calls and takes about two minutes on purpose.
 *
 * Store analytics lag ~2-3 days behind real time; the window ends "today" and the last
 * couple of dates simply have no rows yet. That is the API, not a bug.
 */

import { writeFileSync, mkdirSync } from "node:fs";

const APPS = {
  "9NMJCS390KWB": "RoRoRo",
  "9N53V6RRJK95": "626 Mod Launcher",
  "9PBX8F5TR0VR": "SnapSnip",
  "9PKKLK6R5WFL": "Right Click to PNG",
  "9MV9G4XFJ8S0": "RBX15 Classic Shirt and Pants Maker",
  "9NH3NK2RGCF5": "Sanduhr für Claude",
};

const BASE = "https://manage.devcenter.microsoft.com/v1.0/my/analytics";
const WINDOW_DAYS = 30;
// Reviews and ratings are pulled lifetime, not 30-day: a 30-day window hid 7 of RoRoRo's
// 10 reviews on the first run, and lifetime is what the star average and the reviews list
// actually mean. 2026-04-01 predates the first Store publish (2026-05-06) for every app.
const LIFETIME_START = "2026-04-01";
const PACE_MS = 2500;

const env = (n) => {
  const v = process.env[n];
  if (!v) {
    console.error(`missing env: ${n}`);
    process.exit(1);
  }
  return v;
};

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function token() {
  const tenant = env("STORE_TENANT_ID");
  const body = new URLSearchParams({
    grant_type: "client_credentials",
    client_id: env("STORE_CLIENT_ID"),
    client_secret: env("STORE_CLIENT_SECRET"),
    resource: "https://manage.devcenter.microsoft.com",
  });
  const r = await fetch(`https://login.microsoftonline.com/${tenant}/oauth2/token`, {
    method: "POST",
    body,
  });
  if (!r.ok) throw new Error(`token: HTTP ${r.status}`);
  return (await r.json()).access_token;
}

async function pull(tok, endpoint, appId, extra = "", startOverride = null) {
  const end = new Date().toISOString().slice(0, 10);
  const start = startOverride || new Date(Date.now() - WINDOW_DAYS * 86400e3).toISOString().slice(0, 10);
  const url = `${BASE}/${endpoint}?applicationId=${appId}&startDate=${start}&endDate=${end}&top=10000${extra}`;
  for (let attempt = 1; attempt <= 5; attempt++) {
    let r;
    try {
      r = await fetch(url, { headers: { Authorization: `Bearer ${tok}` } });
    } catch (e) {
      // Network hiccup — treat like a transient server error and back off.
      if (attempt === 5) throw new Error(`${endpoint}/${appId}: ${e.message}`);
      await sleep(3000 * attempt);
      continue;
    }
    // 429 rate limit and 5xx gateway/timeouts (504 seen on failurehits) are both
    // transient — back off and retry rather than abandoning the whole run.
    if (r.status === 429 || r.status >= 500) {
      if (attempt === 5) throw new Error(`${endpoint}/${appId}: HTTP ${r.status} after ${attempt} attempts`);
      await sleep(4000 * attempt);
      continue;
    }
    if (!r.ok) throw new Error(`${endpoint}/${appId}: HTTP ${r.status}`);
    return (await r.json()).Value ?? [];
  }
  throw new Error(`${endpoint}/${appId}: retries exhausted`);
}

// Sum segmented rows into one record per date for the named numeric fields.
function byDate(rows, fields) {
  const out = {};
  for (const row of rows) {
    const d = (row.date ?? "").slice(0, 10);
    if (!d) continue;
    out[d] ??= Object.fromEntries(fields.map((f) => [f, 0]));
    for (const f of fields) out[d][f] += row[f] ?? 0;
  }
  return Object.fromEntries(Object.entries(out).sort());
}

const main = async () => {
  const tok = await token();
  const snapshot = { fetchedAt: new Date().toISOString(), windowDays: WINDOW_DAYS, apps: {} };

  const errors = [];
  for (const [id, name] of Object.entries(APPS)) {
   try {
    const app = { name };

    // groupby=date is load-bearing on the daily endpoints: without it the API returns
    // whole-window aggregate rows with date: null, and the per-date summer silently
    // drops every one of them (aggregationLevel alone does NOT populate the field —
    // measured, two failed runs). Found on the first real run.
    const DAILY = "&groupby=date&aggregationLevel=day";
    const usage = await pull(tok, "usagedaily", id, DAILY);
    app.usageDaily = byDate(usage, [
      "dailyActiveUsers", "dailyActiveDevices", "dailyNewUsers",
      "dailySessionCount", "engagementDurationMinutes",
    ]);
    await sleep(PACE_MS);

    const installs = await pull(tok, "installs", id, DAILY);
    app.installsDaily = byDate(installs, ["successfulInstallCount"]);
    await sleep(PACE_MS);

    const acq = await pull(tok, "appacquisitions", id, DAILY);
    app.acquisitionsDaily = byDate(acq, ["acquisitionQuantity"]);
    await sleep(PACE_MS);

    // Reviews: lifetime, with text. This is the canonical review list both the Store Pulse
    // dashboard and the reply surface read from. The star average is computed from these,
    // so it's the true lifetime rating rather than a 30-day slice.
    const reviews = await pull(tok, "reviews", id, "", LIFETIME_START);
    app.reviews = reviews.map((r) => ({
      reviewerName: r.reviewerName, rating: r.rating, reviewTitle: r.reviewTitle,
      reviewText: r.reviewText, market: r.market, date: r.date,
      packageVersion: r.packageVersion, isRevised: r.isRevised, id: r.id,
    })).sort((a, b) => new Date(b.date) - new Date(a.date));
    const stars = { oneStar: 0, twoStars: 0, threeStars: 0, fourStars: 0, fiveStars: 0 };
    const K = [null, "oneStar", "twoStars", "threeStars", "fourStars", "fiveStars"];
    for (const r of reviews) if (K[r.rating]) stars[K[r.rating]] += 1;
    const n = reviews.length;
    app.ratingsLifetime = {
      ...stars, total: n,
      average: n ? +(reviews.reduce((s, r) => s + r.rating, 0) / n).toFixed(2) : null,
      oneStarWithText: reviews.filter((r) => r.rating === 1 && (r.reviewText || "").trim()).length,
    };
    await sleep(PACE_MS);

    // Failures grouped by name+hash so real crashes carry an identity. The API also emits
    // one empty-name/empty-hash bucket per app that aggregates unclassified hits — it is
    // NOT a crash and must not read as one (it showed as "309 events / 201 devices" and
    // looked like a storm; the real crash was 1 event on 1 device). Split it out.
    // failurehits is the flakiest endpoint (504s observed) and the least critical field.
    // Soft-fail it: an app keeps its usage, installs and reviews even if crashes can't be
    // fetched this run. failuresWindow becomes null so the dashboard can say "unknown"
    // rather than falsely "no crashes".
    let failures = null;
    try {
      failures = await pull(tok, "failurehits", id, "&groupby=failureName,failureHash");
    } catch (e) {
      errors.push(`${name} failurehits: ${e.message}`);
    }
    const byFailure = {};
    let unclassified = { eventCount: 0, deviceCount: 0 };
    for (const row of (failures || [])) {
      const name = (row.failureName || "").trim();
      const hash = (row.failureHash || "").trim();
      if (!name && !hash) {
        unclassified.eventCount += row.eventCount ?? 0;
        unclassified.deviceCount = Math.max(unclassified.deviceCount, row.deviceCount ?? 0);
        continue;
      }
      const key = hash || name;
      byFailure[key] ??= { failureName: name || null, failureHash: hash || null, eventCount: 0, deviceCount: 0 };
      byFailure[key].eventCount += row.eventCount ?? 0;
      byFailure[key].deviceCount += row.deviceCount ?? 0;
    }
    // null = couldn't fetch this run; [] = fetched, genuinely no crashes.
    app.failuresWindow = failures === null ? null
      : Object.values(byFailure).sort((a, b) => b.eventCount - a.eventCount);
    app.unclassifiedHits = unclassified.eventCount ? unclassified : null;
    await sleep(PACE_MS);

    snapshot.apps[id] = app;
    const fc = app.failuresWindow === null ? "unknown" : app.failuresWindow.length;
    console.log(`${name}: usage=${Object.keys(app.usageDaily).length}d installs=${Object.keys(app.installsDaily).length}d reviews=${app.reviews.length} (${app.ratingsLifetime.average ?? '-'}avg) realFailures=${fc}`);
   } catch (e) {
    // One app's failure must not sink the batch — record it and keep going.
    errors.push(`${name}: ${e.message}`);
    console.error(`${name}: SKIPPED — ${e.message}`);
   }
  }

  if (errors.length) snapshot.errors = errors;
  mkdirSync("data", { recursive: true });
  writeFileSync("data/store-analytics.json", JSON.stringify(snapshot, null, 1) + "\n");
  console.log(`wrote data/store-analytics.json (${Object.keys(snapshot.apps).length}/${Object.keys(APPS).length} apps${errors.length ? ", " + errors.length + " soft errors" : ""})`);
  // Exit non-zero only if NOTHING came back, so CI notices a total failure but tolerates
  // a single flaky endpoint.
  if (!Object.keys(snapshot.apps).length) process.exit(1);
};

main().catch((e) => {
  console.error(e.message ?? e);
  process.exit(1);
});
