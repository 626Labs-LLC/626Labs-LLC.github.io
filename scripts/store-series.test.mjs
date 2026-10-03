// Run: node --test scripts/store-series.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { mergeSeries, extractNumber, dailyNumbers, shiftDate } from "./store-series.mjs";

const RUN = "2026-10-02";
const AT = "2026-10-02T06:53:00.000Z";

const inst = (n) => ({ successfulInstallCount: n });
const acq = (n) => ({ acquisitionQuantity: n });
const snapApp = (name, installsDaily = {}, acquisitionsDaily = {}) => ({ name, installsDaily, acquisitionsDaily });

test("first run builds the series from objects as plain numbers", () => {
  const s = mergeSeries(null, { A: snapApp("Alpha", { "2026-09-29": inst(34) }, { "2026-09-29": acq(20) }) }, RUN, AT);
  assert.deepEqual(s, {
    updatedAt: AT,
    apps: { A: { name: "Alpha", installs: { "2026-09-29": 34 }, acquisitions: { "2026-09-29": 20 } } },
  });
});

test("installs are write-once, even inside the trailing window", () => {
  const prev = { apps: { A: { name: "Alpha", installs: { "2026-09-01": 10, "2026-10-01": 5 }, acquisitions: {} } } };
  const s = mergeSeries(prev, { A: snapApp("Alpha", { "2026-09-01": inst(99), "2026-10-01": inst(99), "2026-09-30": inst(7) }) }, RUN, AT);
  assert.deepEqual(s.apps.A.installs, { "2026-09-01": 10, "2026-09-30": 7, "2026-10-01": 5 });
});

test("acquisitions inside the trailing 3 days are overwritten", () => {
  const prev = { apps: { A: { name: "Alpha", installs: {}, acquisitions: { "2026-09-29": 1, "2026-09-30": 2, "2026-10-02": 3 } } } };
  const s = mergeSeries(prev, { A: snapApp("Alpha", {}, { "2026-09-29": acq(11), "2026-09-30": acq(12), "2026-10-02": acq(13) }) }, RUN, AT);
  // 2026-09-29 is exactly 3 days back: still inside the window.
  assert.deepEqual(s.apps.A.acquisitions, { "2026-09-29": 11, "2026-09-30": 12, "2026-10-02": 13 });
});

test("acquisitions older than the trailing window are frozen", () => {
  const prev = { apps: { A: { name: "Alpha", installs: {}, acquisitions: { "2026-09-28": 4, "2026-09-01": 5 } } } };
  const s = mergeSeries(prev, { A: snapApp("Alpha", {}, { "2026-09-28": acq(40), "2026-09-01": acq(50) }) }, RUN, AT);
  assert.deepEqual(s.apps.A.acquisitions, { "2026-09-01": 5, "2026-09-28": 4 });
});

test("an old acquisition date the series has never seen is still written", () => {
  const prev = { apps: { A: { name: "Alpha", installs: {}, acquisitions: {} } } };
  const s = mergeSeries(prev, { A: snapApp("Alpha", {}, { "2026-09-10": acq(6) }) }, RUN, AT);
  assert.deepEqual(s.apps.A.acquisitions, { "2026-09-10": 6 });
});

test("never deletes dates that fell out of the window, or apps missing from the run", () => {
  const prev = {
    apps: {
      A: { name: "Alpha", installs: { "2026-08-12": 1 }, acquisitions: { "2026-08-12": 2 } },
      B: { name: "Beta", installs: { "2026-09-01": 3 }, acquisitions: { "2026-09-01": 4 } },
    },
  };
  const s = mergeSeries(prev, { A: snapApp("Alpha", { "2026-09-30": inst(8) }, {}) }, RUN, AT);
  assert.deepEqual(s.apps.A.installs, { "2026-08-12": 1, "2026-09-30": 8 });
  assert.deepEqual(s.apps.A.acquisitions, { "2026-08-12": 2 });
  assert.deepEqual(s.apps.B, prev.apps.B);
});

test("a new app appears alongside existing ones", () => {
  const prev = { apps: { A: { name: "Alpha", installs: { "2026-09-01": 1 }, acquisitions: {} } } };
  const s = mergeSeries(prev, { C: snapApp("Gamma", { "2026-09-30": inst(2) }, { "2026-09-30": acq(1) }) }, RUN, AT);
  assert.deepEqual(Object.keys(s.apps).sort(), ["A", "C"]);
  assert.deepEqual(s.apps.C, { name: "Gamma", installs: { "2026-09-30": 2 }, acquisitions: { "2026-09-30": 1 } });
});

test("does not mutate its inputs", () => {
  const prev = { apps: { A: { name: "Alpha", installs: { "2026-09-01": 1 }, acquisitions: { "2026-10-01": 1 } } } };
  const frozen = JSON.stringify(prev);
  mergeSeries(prev, { A: snapApp("Alpha", { "2026-09-30": inst(2) }, { "2026-10-01": acq(9) }) }, RUN, AT);
  assert.equal(JSON.stringify(prev), frozen);
});

test("extraction: objects and bare numbers in, junk out", () => {
  assert.equal(extractNumber({ successfulInstallCount: 34 }, "successfulInstallCount"), 34);
  assert.equal(extractNumber(0, "successfulInstallCount"), 0);
  assert.equal(extractNumber(12, "acquisitionQuantity"), 12);
  assert.equal(extractNumber({ other: 1 }, "acquisitionQuantity"), null);
  assert.equal(extractNumber(null, "acquisitionQuantity"), null);
  assert.equal(extractNumber("7", "acquisitionQuantity"), null);
  assert.deepEqual(
    dailyNumbers({ "2026-09-01": inst(3), "2026-09-02": inst(0), bogus: inst(1), "2026-09-03": {} }, "successfulInstallCount"),
    { "2026-09-01": 3, "2026-09-02": 0 },
  );
});

test("output dates are sorted and shiftDate does UTC calendar math", () => {
  const s = mergeSeries(null, { A: snapApp("Alpha", { "2026-09-30": inst(1), "2026-09-02": inst(2) }) }, RUN, AT);
  assert.deepEqual(Object.keys(s.apps.A.installs), ["2026-09-02", "2026-09-30"]);
  assert.equal(shiftDate("2026-10-02", 3), "2026-09-29");
  assert.equal(shiftDate("2026-03-01", 1), "2026-02-28");
});

test("rejects a malformed run date", () => {
  assert.throws(() => mergeSeries(null, {}, "10/02/2026", AT));
});
