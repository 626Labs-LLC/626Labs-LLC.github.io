// Run: node --test scripts/refresh-hub-reach.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { BudgetExceeded } from "./hub-reach-lib.mjs";
import { createTmdb, run } from "./refresh-hub-reach.mjs";

const A = 1, B = 2, C = 3;
const films = { [A]: [10, 11], [B]: [12], [C]: [13] };
const cast = { 10: [A, B], 11: [A], 12: [B, C], 13: [C, 4724] };

const json = (body, status = 200, headers = {}) => ({
  ok: status >= 200 && status < 300,
  status,
  headers: { get: (k) => headers[k] ?? headers[k.toLowerCase()] ?? null },
  json: async () => body,
});

// TMDB-shaped fake: person 99 is a 404, anything unknown is empty.
const fakeFetch = (log = []) => async (url) => {
  log.push(url);
  const p = url.match(/\/person\/(\d+)\/movie_credits/);
  if (p) {
    const id = Number(p[1]);
    if (id === 99) return json({}, 404);
    return json({ cast: (films[id] ?? []).map((f) => ({ id: f, popularity: 1, vote_count: 1 })) });
  }
  const m = url.match(/\/movie\/(\d+)\/credits/);
  if (m) return json({ cast: (cast[Number(m[1])] ?? []).map((id, i) => ({ id, order: i })) });
  return json({}, 404);
};
const noSleep = async () => {};

test("404 reads as empty", async () => {
  const t = createTmdb({ apiKey: "k", fetchImpl: fakeFetch(), sleep: noSleep });
  assert.deepEqual(await t.getFilms(99), []);
});

test("429 retries then succeeds", async () => {
  let n = 0;
  const waits = [];
  const fetchImpl = async () => (++n === 1 ? json({}, 429, { "retry-after": "1" }) : json({ cast: [{ id: 10, popularity: 1, vote_count: 1 }] }));
  const t = createTmdb({ apiKey: "k", fetchImpl, sleep: async (ms) => { waits.push(ms); } });
  assert.deepEqual(await t.getFilms(1), [10]);
  assert.equal(t.calls(), 2);
  assert.ok(waits.includes(1000), "honors Retry-After");
});

test("maxCalls throws BudgetExceeded before fetching", async () => {
  const seen = [];
  const t = createTmdb({ apiKey: "k", fetchImpl: fakeFetch(seen), maxCalls: 1, sleep: noSleep });
  await t.getFilms(1);
  await assert.rejects(() => t.getFilms(2), BudgetExceeded);
  assert.equal(seen.length, 1);
});

test("persistent 5xx gives up after retries with a plain error, not a false answer", async () => {
  const t = createTmdb({ apiKey: "k", fetchImpl: async () => json({}, 503), sleep: noSleep });
  await assert.rejects(() => t.getFilms(1), (e) => !(e instanceof BudgetExceeded));
  assert.equal(t.calls(), 5);
});

const setup = (shardActors, cache) => {
  const dir = mkdtempSync(join(tmpdir(), "hubreach-"));
  const shardDir = join(dir, "birthdays");
  mkdirSync(shardDir);
  writeFileSync(join(shardDir, "01-01.json"), JSON.stringify({ date: "01-01", actors: shardActors }));
  const cachePath = join(dir, "data", "hub-reach.json");
  if (cache) { mkdirSync(join(dir, "data")); writeFileSync(cachePath, JSON.stringify(cache)); }
  return { shardDir, cachePath };
};
const quiet = () => {};

test("run writes answers and keeps an over-budget actor's prior entry", async () => {
  const prior = { stored: 3, reachable: false, checkedAt: "2026-01-01" };
  const { shardDir, cachePath } = setup(
    [{ id: C, baconNumber: 1 }, { id: A, baconNumber: 3 }],
    { [A]: prior },
  );
  const tmdb = createTmdb({ apiKey: "k", fetchImpl: fakeFetch(), sleep: noSleep, minIntervalMs: 0 });
  const res = await run({ shardDir, cachePath, today: "2026-11-10", tmdb, deadline: Date.now() + 60000, perActorMaxCalls: 3, log: quiet });
  const out = JSON.parse(readFileSync(cachePath, "utf8"));
  assert.deepEqual(out[C], { stored: 1, reachable: true, checkedAt: "2026-11-10" });
  assert.deepEqual(out[A], prior);
  assert.equal(res.skipped, 1);
  assert.equal(res.checked, 1);
});

test("run treats a missing cache file as empty", async () => {
  const { shardDir, cachePath } = setup([{ id: C, baconNumber: 1 }]);
  assert.equal(existsSync(cachePath), false);
  const tmdb = createTmdb({ apiKey: "k", fetchImpl: fakeFetch(), sleep: noSleep, minIntervalMs: 0 });
  const res = await run({ shardDir, cachePath, today: "2026-11-10", tmdb, deadline: Date.now() + 60000, log: quiet });
  assert.equal(res.reachable, 1);
  assert.equal(JSON.parse(readFileSync(cachePath, "utf8"))[C].reachable, true);
});

test("a transient error leaves the actor unknown and does not poison the shared cache", async () => {
  // Film 13's credits fail through every retry for actor C's turn; later actors must still succeed.
  let failures = 0;
  const base = fakeFetch();
  const fetchImpl = async (url) => {
    if (failures < 5 && /\/movie\/13\/credits/.test(url)) { failures++; throw new Error("network"); }
    return base(url);
  };
  const { shardDir, cachePath } = setup([{ id: C, baconNumber: 1 }, { id: 5, baconNumber: 1 }]);
  films[5] = [13];
  const tmdb = createTmdb({ apiKey: "k", fetchImpl, sleep: noSleep, minIntervalMs: 0 });
  await run({ shardDir, cachePath, today: "2026-11-10", tmdb, deadline: Date.now() + 60000, log: quiet });
  delete films[5];
  const out = JSON.parse(readFileSync(cachePath, "utf8"));
  assert.equal(out[C], undefined, "errored actor stays unknown");
  assert.equal(out[5].reachable, true, "later actor reads the film fresh");
});
