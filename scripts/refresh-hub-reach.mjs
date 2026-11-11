// Weekly job: for every actor in the birthday shards with a stored Bacon
// number, ask TMDB whether the hub's own ranking rules can actually walk a
// route of that length, and write the verdicts to
// apps/widget-bacon-trail/data/hub-reach.json. Budgeted and resumable: anything
// not answered this run stays unknown, never false.
//
//   node scripts/refresh-hub-reach.mjs [--max-minutes 330] [--max-calls N] [--only id,id]
import { readFileSync, writeFileSync, readdirSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { topFilms, topCast, BudgetExceeded, createSearch, buildQueue, serializeCache, gaveUpEntry } from "./hub-reach-lib.mjs";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const TMDB_BASE = "https://api.themoviedb.org/3";
const RETRIES = 4;
const MAX_RETRY_AFTER_MS = 60000;
const defaultSleep = (ms) => new Promise((r) => setTimeout(r, ms));

export function createTmdb({ apiKey, fetchImpl = fetch, minIntervalMs = 30, maxCalls = Infinity, sleep = defaultSleep }) {
  let calls = 0;
  let last = 0;

  async function request(path) {
    const url = `${TMDB_BASE}${path}?api_key=${apiKey}`;
    for (let attempt = 0; attempt <= RETRIES; attempt++) {
      if (calls >= maxCalls) throw new BudgetExceeded("run call cap reached");
      calls++;
      const wait = last + minIntervalMs - Date.now();
      if (wait > 0) await sleep(wait);
      last = Date.now();

      let res;
      try {
        res = await fetchImpl(url);
      } catch (err) {
        if (attempt === RETRIES) throw new Error(`TMDB ${path}: ${err.message}`);
        await sleep(1000 * 2 ** attempt);
        continue;
      }
      if (res.status === 404) return null;
      if (res.ok) return res.json();
      if (res.status === 429 || res.status >= 500) {
        if (attempt === RETRIES) throw new Error(`TMDB ${path}: HTTP ${res.status} after ${RETRIES} retries`);
        const ra = Number(res.headers?.get?.("retry-after"));
        await sleep(Number.isFinite(ra) && ra > 0 ? Math.min(ra * 1000, MAX_RETRY_AFTER_MS) : 1000 * 2 ** attempt);
        continue;
      }
      throw new Error(`TMDB ${path}: HTTP ${res.status}`);
    }
  }

  return {
    getFilms: async (actorId) => topFilms((await request(`/person/${actorId}/movie_credits`))?.cast ?? []),
    getCast: async (filmId) => topCast((await request(`/movie/${filmId}/credits`))?.cast ?? []),
    calls: () => calls,
  };
}

function loadActors(shardDir) {
  const actors = [];
  for (const f of readdirSync(shardDir).filter((n) => n.endsWith(".json")).sort()) {
    const shard = JSON.parse(readFileSync(join(shardDir, f), "utf8"));
    for (const a of shard.actors ?? []) actors.push(a);
  }
  return actors;
}

function writeCache(cachePath, cache) {
  mkdirSync(dirname(cachePath), { recursive: true });
  writeFileSync(cachePath, serializeCache(cache));
}

export async function run({ shardDir, cachePath, today, tmdb, deadline, perActorMaxCalls = 20000, log = console.log, only = null }) {
  const cache = existsSync(cachePath) ? JSON.parse(readFileSync(cachePath, "utf8")) : {};
  let queue = buildQueue(loadActors(shardDir), cache, today);
  if (only) queue = queue.filter((q) => only.has(q.id));

  // Run-wide response cache. Successful results only (a 404 -> [] is a
  // success); a rejected fetch is never stored, so one actor's budget trip or
  // transient error cannot poison the next actor that touches the same film.
  const filmsCache = new Map();
  const castCache = new Map();
  const result = { attempted: 0, checked: 0, reachable: 0, unreachable: 0, skipped: 0, errored: 0 };
  let sinceSave = 0;

  for (const { id, stored } of queue) {
    if (Date.now() > deadline) { log("deadline reached, stopping"); break; }

    result.attempted++;
    let spent = 0;
    const shared = (store, fetcher) => async (key) => {
      if (store.has(key)) return store.get(key);
      if (Date.now() > deadline) throw new BudgetExceeded("deadline reached");
      if (++spent > perActorMaxCalls) {
        const e = new BudgetExceeded("per-actor cap reached");
        e.scope = "actor";
        throw e;
      }
      const value = await fetcher(key);
      store.set(key, value);
      return value;
    };
    const search = createSearch({ getFilms: shared(filmsCache, tmdb.getFilms), getCast: shared(castCache, tmdb.getCast) });

    try {
      const reachable = await search.reachableWithin(id, stored);
      cache[id] = { stored, reachable, checkedAt: today };
      result.checked++;
      reachable ? result.reachable++ : result.unreachable++;
      log(`${id} ${stored} -> ${reachable ? "reachable" : "unreachable"}`);
      if (++sinceSave >= 25) { writeCache(cachePath, cache); sinceSave = 0; }
    } catch (err) {
      if (err instanceof BudgetExceeded && err.scope !== "actor") {
        // Run-wide cap or deadline: the in-flight actor stays unwritten.
        log(`${id} ${stored} -> ${err.message}, stopping`);
        break;
      }
      result.skipped++;
      if (err instanceof BudgetExceeded) {
        cache[id] = gaveUpEntry(cache[id], stored, today);
        log(`${id} ${stored} -> over-budget, ${cache[id].reachable === null ? "marked gave-up" : "kept prior answer"}`);
      } else {
        result.errored++;
        log(`${id} ${stored} -> error (${err.message}), left unknown`);
      }
    }
  }

  writeCache(cachePath, cache);
  log(`done: ${result.checked} checked (${result.reachable} reachable, ${result.unreachable} unreachable), ${result.skipped} skipped, ${tmdb.calls()} TMDB calls`);
  return result;
}

// A run that tried actors and got no answer from any of them (a revoked key,
// say) must turn the job red. Capped actors and early stops are not failures.
export function allFailed(result) {
  return result.attempted > 0 && result.errored === result.attempted;
}

function parseArgs(argv) {
  const out = { maxMinutes: 330, maxCalls: Infinity, only: null };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--max-minutes") out.maxMinutes = Number(argv[++i]);
    else if (argv[i] === "--max-calls") out.maxCalls = Number(argv[++i]);
    else if (argv[i] === "--only") out.only = new Set(argv[++i].split(",").map(Number));
    else throw new Error(`unknown argument ${argv[i]}`);
  }
  return out;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const apiKey = process.env.VITE_TMDB_API_KEY;
  if (!apiKey) {
    console.error("VITE_TMDB_API_KEY is not set; the reach job needs it to read TMDB.");
    process.exit(1);
  }
  const args = parseArgs(process.argv.slice(2));
  const tmdb = createTmdb({ apiKey, maxCalls: args.maxCalls });
  const result = await run({
    shardDir: join(ROOT, "apps/widget-bacon-trail/data/birthdays"),
    cachePath: join(ROOT, "apps/widget-bacon-trail/data/hub-reach.json"),
    today: new Date().toISOString().slice(0, 10),
    tmdb,
    deadline: Date.now() + args.maxMinutes * 60000,
    only: args.only,
  });
  if (allFailed(result)) {
    console.error(`every attempted actor errored (${result.errored}/${result.attempted}); failing the job`);
    process.exitCode = 1;
  }
}
