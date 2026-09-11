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

async function pull(tok, endpoint, appId, extra = "") {
  const end = new Date().toISOString().slice(0, 10);
  const start = new Date(Date.now() - WINDOW_DAYS * 86400e3).toISOString().slice(0, 10);
  const url = `${BASE}/${endpoint}?applicationId=${appId}&startDate=${start}&endDate=${end}&top=10000${extra}`;
  for (let attempt = 1; attempt <= 4; attempt++) {
    const r = await fetch(url, { headers: { Authorization: `Bearer ${tok}` } });
    if (r.status === 429) {
      // Rate limited — the API says "try again in 2 seconds" and means it.
      await sleep(4000 * attempt);
      continue;
    }
    if (!r.ok) throw new Error(`${endpoint}/${appId}: HTTP ${r.status}`);
    return (await r.json()).Value ?? [];
  }
  throw new Error(`${endpoint}/${appId}: rate-limited after 4 attempts`);
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

  for (const [id, name] of Object.entries(APPS)) {
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

    const ratings = await pull(tok, "ratings", id);
    const stars = { oneStar: 0, twoStars: 0, threeStars: 0, fourStars: 0, fiveStars: 0 };
    for (const row of ratings) for (const k of Object.keys(stars)) stars[k] += row[k] ?? 0;
    app.ratingsWindow = { ...stars, rows: ratings.length };
    await sleep(PACE_MS);

    const failures = await pull(tok, "failurehits", id);
    const byFailure = {};
    for (const row of failures) {
      const key = row.failureName ?? row.failureHash ?? "unknown";
      byFailure[key] ??= { failureName: row.failureName, failureHash: row.failureHash, eventCount: 0, deviceCount: 0 };
      byFailure[key].eventCount += row.eventCount ?? 0;
      byFailure[key].deviceCount += row.deviceCount ?? 0;
    }
    app.failuresWindow = Object.values(byFailure).sort((a, b) => b.eventCount - a.eventCount);
    await sleep(PACE_MS);

    snapshot.apps[id] = app;
    console.log(`${name}: usage dates=${Object.keys(app.usageDaily).length} installs dates=${Object.keys(app.installsDaily).length} ratings rows=${app.ratingsWindow.rows} failures=${app.failuresWindow.length}`);
  }

  mkdirSync("data", { recursive: true });
  writeFileSync("data/store-analytics.json", JSON.stringify(snapshot, null, 1) + "\n");
  console.log("wrote data/store-analytics.json");
};

main().catch((e) => {
  console.error(e.message ?? e);
  process.exit(1);
});
