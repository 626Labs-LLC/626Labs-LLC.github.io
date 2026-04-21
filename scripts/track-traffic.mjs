#!/usr/bin/env node
// Fetch GitHub traffic (clones + views) for the plugin repos and merge into
// data/traffic.csv. The GitHub traffic API only retains 14 days of history,
// so this script runs daily and accumulates the rolling window into a
// permanent CSV committed to the repo.
//
// Env: GH_TOKEN — fine-grained PAT with Administration:Read on each repo.

import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';

const REPOS = [
  'estevanhernandez-stack-ed/vibe-cartographer',
  'estevanhernandez-stack-ed/Vibe-Doc',
  'estevanhernandez-stack-ed/vibe-plugins',
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

async function main() {
  const map = await loadExisting();
  let fetched = 0;
  for (const repo of REPOS) {
    const rows = await fetchRepoWindow(repo);
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
  console.log(`traffic snapshot: ${sorted.length} rows total, ${fetched} refreshed this run`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
