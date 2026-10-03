#!/usr/bin/env node
/**
 * One-time backfill of data/store-installs-series.json from git history.
 *
 * Every daily commit of data/store-analytics.json is a 30-day window. Walking them
 * oldest to newest and letting the NEWEST snapshot that contains a given app+date
 * win recovers the full history (2026-08-12 onward) with each date's most-revised
 * value. That is deliberately not the live merge rule (installs write-once,
 * acquisitions frozen after 3 days): with every snapshot in hand, the last word
 * on a date is the best one available.
 *
 * Run from the repo root: node scripts/backfill-store-series.mjs
 * Reads git only; writes data/store-installs-series.json. Touches no secrets.
 */

import { execFileSync } from "node:child_process";
import { writeFileSync, mkdirSync } from "node:fs";
import { SERIES_PATH, dailyNumbers, serializeSeries } from "./store-series.mjs";

const SNAPSHOT = "data/store-analytics.json";
const git = (...args) => execFileSync("git", args, { encoding: "utf8", maxBuffer: 256 * 1024 * 1024 });

const shas = git("log", "--reverse", "--format=%H", "--", SNAPSHOT).split(/\r?\n/).filter(Boolean);
if (!shas.length) {
  console.error(`no commits touch ${SNAPSHOT}`);
  process.exit(1);
}

const apps = {};
let updatedAt = null;
let used = 0;
for (const sha of shas) {
  let snap;
  try {
    snap = JSON.parse(git("show", `${sha}:${SNAPSHOT}`));
  } catch (e) {
    console.error(`skip ${sha.slice(0, 8)}: ${e.message.split("\n")[0]}`);
    continue;
  }
  used += 1;
  if (snap.fetchedAt) updatedAt = snap.fetchedAt;
  for (const [id, app] of Object.entries(snap.apps ?? {})) {
    const cur = (apps[id] ??= { name: app?.name ?? id, installs: {}, acquisitions: {} });
    if (app?.name) cur.name = app.name;
    // Later commits overwrite earlier ones: newest snapshot containing the date wins.
    Object.assign(cur.installs, dailyNumbers(app?.installsDaily, "successfulInstallCount"));
    Object.assign(cur.acquisitions, dailyNumbers(app?.acquisitionsDaily, "acquisitionQuantity"));
  }
}

const sorted = (m) => Object.fromEntries(Object.entries(m).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0)));
for (const app of Object.values(apps)) {
  app.installs = sorted(app.installs);
  app.acquisitions = sorted(app.acquisitions);
}

mkdirSync("data", { recursive: true });
writeFileSync(SERIES_PATH, serializeSeries({ updatedAt: updatedAt ?? new Date().toISOString(), apps }));

console.log(`read ${used}/${shas.length} snapshots`);
const all = new Set();
for (const [id, app] of Object.entries(apps)) {
  const d = Object.keys(app.installs);
  const a = Object.keys(app.acquisitions);
  d.forEach((x) => all.add(x));
  a.forEach((x) => all.add(x));
  console.log(`${app.name} (${id}): installs ${d.length} dates [${d[0] ?? "-"}..${d.at(-1) ?? "-"}], acquisitions ${a.length} dates [${a[0] ?? "-"}..${a.at(-1) ?? "-"}]`);
}
const range = [...all].sort();
console.log(`wrote ${SERIES_PATH}: ${range.length} distinct dates, ${range[0]}..${range.at(-1)}`);
