#!/usr/bin/env node
// Fetch GitHub traffic (clones + views) for every public, non-fork,
// non-archived repo under the configured owners (user + org) and merge
// into data/traffic.csv. The GitHub traffic API only retains 14 days of
// history, so this script runs daily and accumulates the rolling window
// into a permanent CSV committed to the repo.
//
// Env: GH_TOKEN — fine-grained PAT with Administration:Read on each repo.
// For "all repos" auto-discovery, the PAT must have access to "All
// repositories" under each owner — otherwise repos without traffic
// permission soft-error and are skipped from this run (older rows for
// those repos remain in the CSV).

import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';

const OWNERS = [
  { type: 'user', name: 'estevanhernandez-stack-ed' },
  { type: 'org',  name: '626Labs-LLC' },
];

const CSV_PATH = 'data/traffic.csv';
const HEADER = 'date,repo,clones,unique_cloners,views,unique_visitors';

const token = process.env.GH_TOKEN;
if (!token) {
  console.error('GH_TOKEN is required');
  process.exit(1);
}

async function ghFetch(urlPath) {
  const res = await fetch(`https://api.github.com${urlPath}`, {
    headers: {
      Authorization: `Bearer ${token}`,
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
  const all = [];
  for (let page = 1; page <= 3; page++) {
    const repos = await ghFetch(`${basePath}&page=${page}`);
    all.push(...repos);
    if (repos.length < 100) break;
  }
  return all
    .filter((r) => !r.private && !r.archived && !r.fork)
    .map((r) => r.full_name);
}

async function discoverRepos() {
  const all = [];
  for (const owner of OWNERS) {
    try {
      const repos = await listPublicRepos(owner);
      console.log(`${owner.type}/${owner.name}: ${repos.length} public non-fork repos`);
      all.push(...repos);
    } catch (err) {
      console.warn(`! list ${owner.type}/${owner.name}: ${err.message}`);
    }
  }
  // Dedupe (defensive — user-listing + org-listing shouldn't overlap).
  return [...new Set(all)];
}

async function fetchRepoWindow(repo) {
  const [clones, views] = await Promise.all([
    ghFetch(`/repos/${repo}/traffic/clones`),
    ghFetch(`/repos/${repo}/traffic/views`),
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
  const repos = await discoverRepos();
  if (repos.length === 0) {
    console.error('No repos discovered. Aborting to avoid overwriting CSV with empty data.');
    process.exit(1);
  }
  console.log(`Tracking ${repos.length} repos total.`);

  const map = await loadExisting();
  let fetched = 0;
  let skipped = 0;
  for (const repo of repos) {
    const rows = await fetchRepoWindowSafe(repo);
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
  console.log(`traffic snapshot: ${sorted.length} rows total, ${fetched} refreshed, ${skipped} repos skipped (no permission or no data)`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
