#!/usr/bin/env node
// Fetch GitHub traffic (clones + views) for every public, non-fork,
// non-archived repo under the configured owners (user + org) and merge
// into data/traffic.csv. The GitHub traffic API only retains 14 days of
// history, so this script runs daily and accumulates the rolling window
// into a permanent CSV committed to the repo.
//
// Env:
//   GH_TOKEN     — fine-grained PAT for repos under estevanhernandez-stack-ed.
//   GH_TOKEN_ORG — fine-grained PAT for repos under 626Labs-LLC. Optional;
//                  if unset, falls back to GH_TOKEN (which can't reach the
//                  Traffic API on org repos, so they soft-error and skip).
//
// Why two tokens: GitHub fine-grained PATs only support a single resource
// owner. Repos under your personal account and repos under an org you own
// each need their own PAT. The script picks the right token per repo based
// on the owner parsed from the repo's full_name.
//
// For "all repos" auto-discovery, each PAT must have access to "All
// repositories" under its owner — otherwise repos without traffic
// permission soft-error and are skipped from this run (older rows for
// those repos remain in the CSV).

import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';

const OWNERS = [
  { type: 'user', name: 'estevanhernandez-stack-ed', tokenEnv: 'GH_TOKEN' },
  { type: 'org',  name: '626Labs-LLC',               tokenEnv: 'GH_TOKEN_ORG' },
];

const CSV_PATH = 'data/traffic.csv';
const REPOS_PATH = 'data/repos.json';
const HEADER = 'date,repo,clones,unique_cloners,views,unique_visitors';

// Build the owner → token map. Falls back to GH_TOKEN if a per-owner token
// is missing, so the script keeps working in degraded mode (org repos will
// 403 on the Traffic API and be skipped, same as before this split).
const TOKEN_BY_OWNER = new Map();
for (const owner of OWNERS) {
  const t = process.env[owner.tokenEnv] || process.env.GH_TOKEN;
  if (t) TOKEN_BY_OWNER.set(owner.name, t);
}
if (!process.env.GH_TOKEN) {
  console.error('GH_TOKEN is required (personal-account PAT).');
  process.exit(1);
}

function tokenFor(ownerName) {
  return TOKEN_BY_OWNER.get(ownerName) || process.env.GH_TOKEN;
}

function tokenForRepo(fullName) {
  // full_name is "owner/repo" — route by owner segment.
  const slash = fullName.indexOf('/');
  return tokenFor(slash > 0 ? fullName.slice(0, slash) : '');
}

async function ghFetch(urlPath, tokenOverride) {
  const t = tokenOverride || process.env.GH_TOKEN;
  const res = await fetch(`https://api.github.com${urlPath}`, {
    headers: {
      Authorization: `Bearer ${t}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': '626labs-hub-traffic-tracker',
    },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`GET ${urlPath} -> ${res.status}: ${body}`);
  }
  return res.json();
}

const toIsoDate = (ts) => ts.slice(0, 10);

async function loadExisting() {
  try {
    const text = await readFile(CSV_PATH, 'utf8');
    const [hdr, ...rows] = text.trim().split('\n');
    if (hdr !== HEADER) {
      throw new Error(`CSV header mismatch. Expected: ${HEADER}\nGot: ${hdr}`);
    }
    const map = new Map();
    for (const row of rows) {
      if (!row) continue;
      const [date, repo, clones, unique_cloners, views, unique_visitors] = row.split(',');
      map.set(`${date}|${repo}`, {
        date,
        repo,
        clones: +clones,
        unique_cloners: +unique_cloners,
        views: +views,
        unique_visitors: +unique_visitors,
      });
    }
    return map;
  } catch (err) {
    if (err.code === 'ENOENT') return new Map();
    throw err;
  }
}

async function listPublicRepos(owner) {
  const basePath = owner.type === 'org'
    ? `/orgs/${owner.name}/repos?type=public&per_page=100&sort=updated`
    : `/users/${owner.name}/repos?type=owner&per_page=100&sort=updated`;
  // Paginate up to 3 pages (300 repos) defensively. We expect <100 today.
  const ownerToken = tokenFor(owner.name);
  const all = [];
  for (let page = 1; page <= 3; page++) {
    const repos = await ghFetch(`${basePath}&page=${page}`, ownerToken);
    all.push(...repos);
    if (repos.length < 100) break;
  }
  // Return full repo objects (filtered) — main loop pulls full_name from
  // them and we also write a metadata sidecar for the admin to render
  // zero-traffic repos.
  return all.filter((r) => !r.private && !r.archived && !r.fork);
}

// Returns { repos, failures }. The FAILURES half is the whole point, and it
// is worth the changed return type: this function used to swallow a per-owner
// listing error as a console.warn and hand back whatever the other owners
// produced, which read as success to every caller.
//
// On 2026-08-03 GH_TOKEN expired. The user listing started returning 401, the
// org listing kept working, and discovery quietly went from 51 repos to 2.
// main()'s only guard was `length === 0`, and 2 is not 0 — so data/repos.json
// was overwritten with the truncated list and the workflow exited GREEN every
// morning for a month. 49 repos silently stopped being tracked. The traffic
// API only serves a ~14-day trailing window, so that month of views and clones
// is gone and cannot be backfilled.
//
// Nothing in this workflow noticed. track-downloads.yml did, the next morning
// and every morning after, because ITS guard is stricter — it found no repo
// shipping release assets and refused to write empty data. A job downstream
// failed loudly for 20+ days about a fault that belonged here.
async function discoverRepos() {
  const all = [];
  const failures = [];
  for (const owner of OWNERS) {
    try {
      const repos = await listPublicRepos(owner);
      console.log(`${owner.type}/${owner.name}: ${repos.length} public non-fork repos`);
      all.push(...repos);
    } catch (err) {
      console.warn(`! list ${owner.type}/${owner.name}: ${err.message}`);
      failures.push({ owner: `${owner.type}/${owner.name}`, message: err.message });
    }
  }
  // Dedupe by full_name (defensive — user-listing + org-listing shouldn't overlap).
  const seen = new Set();
  const repos = all.filter((r) => {
    if (seen.has(r.full_name)) return false;
    seen.add(r.full_name);
    return true;
  });
  return { repos, failures };
}

async function fetchRepoWindow(repo) {
  // Route the Traffic API call to whichever token has admin:read on this
  // repo's owner. Personal-account repos use GH_TOKEN, org repos use
  // GH_TOKEN_ORG (when set).
  const t = tokenForRepo(repo);
  const [clones, views] = await Promise.all([
    ghFetch(`/repos/${repo}/traffic/clones`, t),
    ghFetch(`/repos/${repo}/traffic/views`, t),
  ]);
  const byDate = new Map();
  for (const c of clones.clones ?? []) {
    const d = toIsoDate(c.timestamp);
    byDate.set(d, {
      date: d,
      repo,
      clones: c.count,
      unique_cloners: c.uniques,
      views: 0,
      unique_visitors: 0,
    });
  }
  for (const v of views.views ?? []) {
    const d = toIsoDate(v.timestamp);
    const existing = byDate.get(d) ?? {
      date: d,
      repo,
      clones: 0,
      unique_cloners: 0,
      views: 0,
      unique_visitors: 0,
    };
    existing.views = v.count;
    existing.unique_visitors = v.uniques;
    byDate.set(d, existing);
  }
  return [...byDate.values()];
}

async function fetchRepoWindowSafe(repo) {
  try {
    return await fetchRepoWindow(repo);
  } catch (err) {
    // Most likely a 403/404 because the PAT doesn't have admin:read on
    // this repo. Skip silently — the CSV keeps prior rows for it.
    console.warn(`! ${repo}: ${err.message.slice(0, 120)}`);
    return [];
  }
}

async function main() {
  const { repos: discovered, failures } = await discoverRepos();

  // Refuse to overwrite outputs with PARTIAL data, not just empty data. An
  // owner that could not be listed is an owner whose repos would silently
  // vanish from data/repos.json and from every downstream consumer of it.
  // Aborting costs one day of traffic rows, which the next run recovers
  // because the API window is trailing; writing a truncated list costs the
  // history of every repo that dropped out, permanently. See discoverRepos.
  //
  // This is deliberately fatal rather than a warning. A listing failure here
  // is always either an expired token or an owner that no longer exists, and
  // both need a human — neither should be absorbed by a green checkmark.
  if (failures.length > 0) {
    for (const f of failures) console.error(`! could not list ${f.owner}: ${f.message}`);
    console.error(
      `Aborting: ${failures.length} of ${OWNERS.length} owners could not be listed. ` +
      `Refusing to overwrite ${REPOS_PATH} with a partial list — check the PAT for ` +
      `the owner(s) above (each needs "All repositories" access under its owner).`
    );
    process.exit(1);
  }

  if (discovered.length === 0) {
    console.error('No repos discovered. Aborting to avoid overwriting CSV with empty data.');
    process.exit(1);
  }
  console.log(`Tracking ${discovered.length} repos total.`);

  // Write the discovery sidecar — admin uses this to render zero-traffic
  // repos as faded rows so the dashboard reflects the full public surface,
  // not just the slice that happened to have visits in the last 14 days.
  const reposPayload = {
    generatedAt: new Date().toISOString(),
    count: discovered.length,
    owners: OWNERS.map((o) => `${o.type}:${o.name}`),
    repos: discovered.map((r) => ({
      full_name: r.full_name,
      owner: r.owner?.login,
      name: r.name,
      description: r.description || null,
      html_url: r.html_url,
      language: r.language || null,
      pushed_at: r.pushed_at,
      stargazers_count: r.stargazers_count || 0,
      archived: !!r.archived,
      fork: !!r.fork,
    })).sort((a, b) => a.full_name.localeCompare(b.full_name)),
  };
  await mkdir(path.dirname(REPOS_PATH), { recursive: true });
  await writeFile(REPOS_PATH, JSON.stringify(reposPayload, null, 2) + '\n');
  console.log(`Wrote ${REPOS_PATH} — ${discovered.length} public repos`);

  // Now pull traffic data for each.
  const map = await loadExisting();
  let fetched = 0;
  let skipped = 0;
  for (const r of discovered) {
    const rows = await fetchRepoWindowSafe(r.full_name);
    if (rows.length === 0) { skipped++; continue; }
    for (const row of rows) {
      map.set(`${row.date}|${row.repo}`, row);
      fetched++;
    }
  }
  const sorted = [...map.values()].sort((a, b) => {
    if (a.date !== b.date) return a.date.localeCompare(b.date);
    return a.repo.localeCompare(b.repo);
  });
  const csv =
    [HEADER, ...sorted.map((r) =>
      [r.date, r.repo, r.clones, r.unique_cloners, r.views, r.unique_visitors].join(',')
    )].join('\n') + '\n';
  await mkdir(path.dirname(CSV_PATH), { recursive: true });
  await writeFile(CSV_PATH, csv);
  console.log(`traffic snapshot: ${sorted.length} rows total, ${fetched} refreshed, ${skipped} repos with no recent traffic or no admin permission`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
