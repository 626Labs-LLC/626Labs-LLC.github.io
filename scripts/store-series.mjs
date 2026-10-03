/**
 * Accumulating per-app install series for the Microsoft Store apps.
 *
 * data/store-analytics.json is a sliding 30-day window, overwritten every run, so
 * history falls off the back of it. data/store-installs-series.json is the
 * accumulator: one map of date -> number per app, per metric, that only grows.
 *
 *   { updatedAt, apps: { <storeId>: { name, installs: { "YYYY-MM-DD": n },
 *                                     acquisitions: { "YYYY-MM-DD": n } } } }
 *
 * Merge rules, measured against 31 snapshot commits (2026-09-11 to 2026-10-02):
 *   - Installs (successfulInstallCount) land 2-3 days late and are never revised,
 *     so a date is written once and never rewritten.
 *   - Acquisitions (acquisitionQuantity) are revised for up to ~2 days after they
 *     first appear, so dates within the trailing 3 days of the run date (run date
 *     minus 3 through run date, inclusive) are overwritten; older dates are frozen.
 *     A date the series has never seen is always written, whatever its age.
 *   - Nothing is ever deleted: not a date, not an app. An app missing from this run
 *     (a failed pull) keeps its history untouched.
 *
 * Pure functions only. No I/O here; the tracker and the backfill own the files.
 */

export const SERIES_PATH = "data/store-installs-series.json";
export const ACQUISITION_REVISION_DAYS = 3;

/** Pull a plain number out of a daily value: `{ field: n }` or a bare number. */
export function extractNumber(value, field) {
  const n = value !== null && typeof value === "object" ? value[field] : value;
  return typeof n === "number" && Number.isFinite(n) ? n : null;
}

/** date -> number for one metric, from a snapshot's `{ date: { field: n } }` map. */
export function dailyNumbers(daily, field) {
  const out = {};
  for (const [date, value] of Object.entries(daily ?? {})) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) continue;
    const n = extractNumber(value, field);
    if (n !== null) out[date] = n;
  }
  return out;
}

/** YYYY-MM-DD for `days` days before the given YYYY-MM-DD (UTC calendar math). */
export function shiftDate(date, days) {
  const t = Date.parse(`${date}T00:00:00Z`) - days * 86400e3;
  return new Date(t).toISOString().slice(0, 10);
}

const sortedByDate = (m) => Object.fromEntries(Object.entries(m).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0)));

/**
 * Merge one run's `apps` object (the shape store-analytics.json carries) into the
 * previous series. Returns a new series; neither input is mutated.
 *
 * @param {object|null} previous  last series, or null/undefined on the first run
 * @param {object} apps           this run's snapshot.apps
 * @param {string} runDate        YYYY-MM-DD the run is anchored to (UTC)
 * @param {string} [updatedAt]    ISO timestamp stamped on the result
 */
export function mergeSeries(previous, apps, runDate, updatedAt = new Date().toISOString()) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(runDate ?? "")) throw new Error(`mergeSeries: bad runDate ${runDate}`);
  const cutoff = shiftDate(runDate, ACQUISITION_REVISION_DAYS);
  const out = {};

  for (const [id, prev] of Object.entries(previous?.apps ?? {})) {
    out[id] = {
      name: prev?.name ?? id,
      installs: { ...(prev?.installs ?? {}) },
      acquisitions: { ...(prev?.acquisitions ?? {}) },
    };
  }

  for (const [id, app] of Object.entries(apps ?? {})) {
    const cur = (out[id] ??= { name: app?.name ?? id, installs: {}, acquisitions: {} });
    if (app?.name) cur.name = app.name;

    for (const [date, n] of Object.entries(dailyNumbers(app?.installsDaily, "successfulInstallCount"))) {
      if (!(date in cur.installs)) cur.installs[date] = n;
    }
    for (const [date, n] of Object.entries(dailyNumbers(app?.acquisitionsDaily, "acquisitionQuantity"))) {
      if (!(date in cur.acquisitions) || date >= cutoff) cur.acquisitions[date] = n;
    }
  }

  for (const app of Object.values(out)) {
    app.installs = sortedByDate(app.installs);
    app.acquisitions = sortedByDate(app.acquisitions);
  }
  return { updatedAt, apps: out };
}

/** Pretty JSON matching the house style of the other data files. */
export function serializeSeries(series) {
  return JSON.stringify(series, null, 1) + "\n";
}
