// Run: node --test scripts/hub-reach-lib.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { KEVIN_BACON_ID, FILMS_PER_ACTOR, CAST_PER_FILM, topFilms, topCast, BudgetExceeded, createSearch, isFresh, hubReachableFor, buildQueue, serializeCache } from "./hub-reach-lib.mjs";

const A = 1, B = 2, C = 3;
const films = { [A]: [10, 11], [B]: [12], [C]: [13] };
const cast = { 10: [A, B], 11: [A], 12: [B, C], 13: [C, 4724] };

const graph = () => {
  const calls = { films: {}, cast: {} };
  return {
    calls,
    getFilms: async (a) => { calls.films[a] = (calls.films[a] ?? 0) + 1; return films[a] ?? []; },
    getCast: async (m) => { calls.cast[m] = (calls.cast[m] ?? 0) + 1; return cast[m] ?? []; },
  };
};

test("constants match the widget", () => {
  assert.equal(KEVIN_BACON_ID, 4724);
  assert.equal(FILMS_PER_ACTOR, 45);
  assert.equal(CAST_PER_FILM, 27);
});

test("topFilms ranks by popularity*ln(1+votes) and keeps 45", () => {
  const entries = Array.from({ length: 50 }, (_, i) => ({ id: i, popularity: 1, vote_count: 1 }));
  entries.push({ id: 900, popularity: 100, vote_count: 0 });
  entries.push({ id: 901, popularity: 2, vote_count: 1000 });
  const ids = topFilms(entries);
  assert.equal(ids.length, 45);
  assert.equal(ids[0], 901);
  assert.ok(!ids.includes(900), "zero-vote film scores 0 and falls off");
});

test("topFilms tolerates missing popularity and vote_count", () => {
  assert.deepEqual(topFilms([{ id: 1 }, { id: 2, popularity: 5, vote_count: 3 }]), [2, 1]);
});

test("topCast sorts by order, missing order last, keeps 27", () => {
  const orders = Array.from({ length: 28 }, (_, i) => i);
  const shuffled = orders.map((o, i) => orders[(i * 11) % 28]);
  const entries = shuffled.map((o) => ({ id: 100 + o, order: o }));
  entries.push({ id: 7000 }, { id: 7001 });
  const ids = topCast(entries);
  assert.equal(ids.length, 27);
  assert.equal(ids[0], 100);
  assert.ok(!ids.includes(7000) && !ids.includes(7001));
});

test("topCast keeps missing-order entries after ordered ones", () => {
  assert.deepEqual(topCast([{ id: 1 }, { id: 2, order: 3 }, { id: 3, order: 0 }]), [3, 2, 1]);
});

test("direct route is 1 film", async () => {
  const g = graph();
  assert.equal(await createSearch(g).reachableWithin(C, 1), true);
});

test("route length is bounded by maxFilms", async () => {
  const s = createSearch(graph());
  assert.equal(await s.reachableWithin(B, 1), false);
  assert.equal(await s.reachableWithin(B, 2), true);
  assert.equal(await s.reachableWithin(A, 2), false);
  assert.equal(await s.reachableWithin(A, 3), true);
});

test("memoizes getter calls", async () => {
  const g = graph();
  const s = createSearch(g);
  await s.reachableWithin(A, 3);
  await s.reachableWithin(A, 3);
  for (const n of Object.values(g.calls.films)) assert.ok(n <= 1);
  for (const n of Object.values(g.calls.cast)) assert.ok(n <= 1);
});

test("a getter error propagates", async () => {
  const s = createSearch({
    getFilms: async () => { throw new BudgetExceeded(); },
    getCast: async () => [],
  });
  await assert.rejects(() => s.reachableWithin(A, 3), BudgetExceeded);
});

const TODAY = "2026-11-10";

test("fresh true never expires", () => {
  assert.equal(isFresh({ stored: 2, reachable: true, checkedAt: "2025-01-01" }, 2, TODAY), true);
});

test("false expires after 28 days", () => {
  assert.equal(isFresh({ stored: 2, reachable: false, checkedAt: "2026-10-13" }, 2, TODAY), true);
  assert.equal(isFresh({ stored: 2, reachable: false, checkedAt: "2026-10-12" }, 2, TODAY), false);
});

test("stored change makes an entry stale", () => {
  assert.equal(isFresh({ stored: 3, reachable: true, checkedAt: TODAY }, 2, TODAY), false);
  assert.equal(isFresh(undefined, 2, TODAY), false);
});

test("hubReachableFor returns undefined for Kevin (0), no number, or stale", () => {
  const cache = { 1: { stored: 2, reachable: false, checkedAt: TODAY }, 2: { stored: 2, reachable: true, checkedAt: TODAY }, 3: { stored: 2, reachable: true, checkedAt: TODAY } };
  assert.equal(hubReachableFor({ id: 1, baconNumber: 2 }, cache, TODAY), false);
  assert.equal(hubReachableFor({ id: 2, baconNumber: 0 }, cache, TODAY), undefined);
  assert.equal(hubReachableFor({ id: 3 }, cache, TODAY), undefined);
  assert.equal(hubReachableFor({ id: 2, baconNumber: 3 }, cache, TODAY), undefined);
  assert.equal(hubReachableFor({ id: 9, baconNumber: 2 }, cache, TODAY), undefined);
});

test("buildQueue order", () => {
  const actors = [1, 2, 3, 4, 5].map((id) => ({ id, baconNumber: 2 }));
  const cache = {
    2: { stored: 3, reachable: true, checkedAt: TODAY },
    3: { stored: 2, reachable: false, checkedAt: "2026-09-01" },
    4: { stored: 2, reachable: false, checkedAt: "2026-08-01" },
    5: { stored: 2, reachable: true, checkedAt: TODAY },
  };
  assert.deepEqual(buildQueue(actors, cache, TODAY).map((q) => q.id), [1, 2, 4, 3]);
  assert.deepEqual(buildQueue([...actors, { id: 1, baconNumber: 2 }, { id: 6, baconNumber: 0 }], cache, TODAY).length, 4);
});

test("serializeCache sorts keys numerically", () => {
  const out = serializeCache({ 10: { stored: 2, reachable: true, checkedAt: TODAY }, 9: { checkedAt: TODAY, reachable: false, stored: 3 } });
  assert.ok(out.indexOf('"9"') < out.indexOf('"10"'));
  assert.ok(out.endsWith("}
"));
  assert.ok(out.indexOf('"stored"') < out.indexOf('"reachable"'));
});
