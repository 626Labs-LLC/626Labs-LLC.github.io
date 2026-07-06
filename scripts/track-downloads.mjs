#!/usr/bin/env node
/**
 * track-downloads.mjs — release-asset download counts across the estate.
 *
 * GitHub keeps a lifetime download_count on every release asset but exposes
 * no history; this job snapshots the counters daily so trends exist. It reads
 * the repo list from data/repos.json (the discovery sidecar track-traffic.mjs
 * writes) and, for each repo that has release assets, records:
 *
 *   1. data/download-stats.json — full current detail: per repo, per release,
 *      per asset counts + rollups. The rororo-plugins page and admin read this.
 *   2. data/downloads.csv       — one row per day per repo with the lifetime
 *      total (date,repo,downloads). Day-over-day diff = downloads that day.
 *
 * Unlike the Traffic API this data is public, so the implicit GITHUB_TOKEN is
 * enough in CI (no PAT). Works unauthenticated locally but ~90 repos will eat
 * the anonymous rate limit — export GITHUB_TOKEN (or GH_TOKEN) instead.
 * Draft releases are skipped (their assets aren't publicly downloadable);
 * prereleases are included and flagged — RC downloads are real usage.
 */
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';

const REPOS_PATH = 'data/repos.json';
const OUT_JSON = 'data/download-stats.json';
const OUT_CSV = 'data/downloads.csv';
const CSV_HEADER = 'date,repo,downloads';

const TOKEN = process.env.GITHUB_TOKEN || process.env.GH_TOKEN || '';
const headers = {
  'User-Agent': '626labs-hub-download-tracker',
  Accept: 'application/vnd.github+json',
  ...(TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {}),
};

async function releases(fullName) {
  // Two pages (200 releases) covers every repo in the estate with headroom.
  const all = [];
  for (let page = 1; page <= 2; page++) {
    const res = await fetch(
      `https://api.github.com/repos/${fullName}/releases?per_page=100&page=${page}`,
      { headers },
    );
    if (!res.ok) throw new Error(`releases HTTP ${res.status}`);
    const batch = await res.json();
    all.push(...batch);
    if (batch.length < 100) break;
  }
  return all;
}

async function main() {
  const discovered = JSON.parse(await readFile(REPOS_PATH, 'utf8')).repos;
  if (!discovered?.length) {
    console.error(`No repos in ${REPOS_PATH}. Run track-traffic.mjs first.`);
    process.exit(1);
  }

  const products = {};
  let failures = 0;
  for (const { full_name } of discovered) {
    let rels;
    try {
      rels = await releases(full_name);
    } catch (err) {
      failures++;
      console.warn(`! ${full_name}: ${err.message}`);
      continue;
    }
    const recorded = [];
    for (const rel of rels) {
      if (rel.draft) continue;
      const assets = {};
      let relTotal = 0;
      for (const a of rel.assets ?? []) {
        assets[a.name] = a.download_count;
        relTotal += a.download_count;
      }
      if (Object.keys(assets).length === 0) continue;
      recorded.push({
        tag: rel.tag_name,
        published: (rel.published_at || '').slice(0, 10),
        ...(rel.prerelease ? { prerelease: true } : {}),
        total: relTotal,
        assets,
      });
    }
    if (recorded.length === 0) continue; // repo ships no release assets — not a product surface
    const total = recorded.reduce((sum, r) => sum + r.total, 0);
    products[full_name] = { total, releases: recorded };
    console.log(`${full_name}: ${total} downloads across ${recorded.length} releases`);
  }

  if (Object.keys(products).length === 0) {
    console.error('Nothing fetched — refusing to overwrite outputs with empty data.');
    process.exit(1);
  }

  const sorted = Object.fromEntries(
    Object.keys(products).sort().map((k) => [k, products[k]]),
  );
  await mkdir(path.dirname(OUT_JSON), { recursive: true });
  await writeFile(
    OUT_JSON,
    JSON.stringify(
      {
        $comment:
          'Lifetime release-asset download counts (drafts excluded, prereleases flagged). ' +
          'Snapshot only — daily history lives in downloads.csv.',
        products: sorted,
      },
      null,
      2,
    ) + '\n',
  );

  // Merge today's totals into the CSV time series (upsert on date|repo).
  const today = new Date().toISOString().slice(0, 10);
  const rows = new Map();
  try {
    const [hdr, ...lines] = (await readFile(OUT_CSV, 'utf8')).trim().split('\n');
    if (hdr !== CSV_HEADER) throw new Error(`CSV header mismatch: ${hdr}`);
    for (const line of lines) {
      if (!line) continue;
      const [date, repo] = line.split(',');
      rows.set(`${date}|${repo}`, line);
    }
  } catch (err) {
    if (err.code !== 'ENOENT') throw err;
  }
  for (const [repo, { total }] of Object.entries(sorted)) {
    rows.set(`${today}|${repo}`, `${today},${repo},${total}`);
  }
  const csv = [CSV_HEADER, ...[...rows.keys()].sort().map((k) => rows.get(k))].join('\n') + '\n';
  await writeFile(OUT_CSV, csv);

  console.log(
    `wrote ${Object.keys(sorted).length} products -> ${OUT_JSON}, ` +
    `${rows.size} rows -> ${OUT_CSV}` +
    (failures ? ` (${failures} repos failed)` : ''),
  );
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
