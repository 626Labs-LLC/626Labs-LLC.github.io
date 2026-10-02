#!/usr/bin/env node
/**
 * refresh-repo-activity.mjs — the data behind every repo meter on the site.
 *
 * The year-in-review page carries a commit-activity grid for the whole
 * estate. The repo meter is that grid per repository, on every page that
 * shows a project (see docs/superpowers/specs/2026-10-01-repo-meter-design.md).
 * This job writes the one file those meters read at runtime:
 *
 *   data/repo-activity.json
 *   {
 *     "fetchedAt": "...", "windowDays": 182,
 *     "repos": { "owner/repo": { "days": { "YYYY-MM-DD": n }, "total": n,
 *                                "lastCommit": "YYYY-MM-DD" | null,
 *                                "truncated": false } },
 *     "missing": ["owner/private-or-gone"]
 *   }
 *
 * WHICH REPOS. The union of: every product `repo` in content/site.json, every
 * entry in content/plugin-repos.json, and every data-repo="owner/repo"
 * attribute in the public HTML at the repo root (so a hand-authored page
 * registers its repo just by carrying the meter element). Sorted, deduped.
 *
 * HOW COUNTED. GET /repos/{r}/commits?since=<today minus windowDays> paged
 * at 100, up to MAX_PAGES. Bot commits are dropped: the hub repo alone
 * commits by bot several times a day, and the point of the meter is the
 * person. The rule matches the timeline's: author.type == "Bot", a login
 * ending in "[bot]", or no linked GitHub author and a committer name
 * mentioning github-actions. Days bucket on the commit AUTHOR date, UTC.
 * /stats/commit_activity was rejected because it counts the bots.
 *
 * A repo that 404s or 403s lands in `missing` and renders as "no public
 * activity". Runs in CI with the implicit GITHUB_TOKEN; works locally with
 * `GITHUB_TOKEN=$(gh auth token)`. Nothing here is rendered into a page by
 * render-hub or render-plugin-pages, so the daily write never dirties
 * their --check: the meters fetch this file in the browser.
 */
import { readFileSync, writeFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const OUT = join(ROOT, "data", "repo-activity.json");
const WINDOW_DAYS = 182;
const MAX_PAGES = 15; // 1,500 commits; ROROROblox and Celestia3 pass 500 inside the window
const TOKEN = process.env.GITHUB_TOKEN || process.env.GH_TOKEN || "";

const headers = {
  "User-Agent": "626labs-hub-repo-activity",
  Accept: "application/vnd.github+json",
  ...(TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {}),
};

export function isBot(commit) {
  const login = commit.author?.login || "";
  if (commit.author?.type === "Bot") return true;
  if (/\[bot\]$/i.test(login)) return true;
  const name = commit.commit?.committer?.name || "";
  const aname = commit.commit?.author?.name || "";
  if (!commit.author && /github-actions/i.test(name + " " + aname)) return true;
  return false;
}

/** The repo set, from the three places a showcased project names one. */
export function collectRepos(root = ROOT) {
  const out = new Set();
  const site = JSON.parse(readFileSync(join(root, "content", "site.json"), "utf8"));
  let products = site.products;
  if (products && !Array.isArray(products)) products = products.items || Object.values(products);
  for (const p of products || []) if (p && p.repo) out.add(String(p.repo).trim());
  const plug = JSON.parse(readFileSync(join(root, "content", "plugin-repos.json"), "utf8")).repos || {};
  for (const r of Object.values(plug)) out.add(String(r).trim());
  for (const f of readdirSync(root)) {
    if (!f.endsWith(".html")) continue;
    const html = readFileSync(join(root, f), "utf8");
    for (const m of html.matchAll(/data-repo="([^"\s]+\/[^"\s]+)"/g)) out.add(m[1].trim());
  }
  return [...out].filter((r) => /^[\w.-]+\/[\w.-]+$/.test(r)).sort((a, b) => a.localeCompare(b));
}

/** Bucket a list of API commit objects into {day: count}, bots excluded. */
export function bucket(commits) {
  const days = {};
  for (const c of commits) {
    if (isBot(c)) continue;
    const iso = c.commit?.author?.date || c.commit?.committer?.date;
    if (!iso) continue;
    const day = iso.slice(0, 10);
    days[day] = (days[day] || 0) + 1;
  }
  return days;
}

async function fetchCommits(repo, since) {
  const all = [];
  for (let page = 1; page <= MAX_PAGES; page++) {
    const url = `https://api.github.com/repos/${repo}/commits?since=${since}&per_page=100&page=${page}`;
    const res = await fetch(url, { headers });
    if (res.status === 404 || res.status === 403 || res.status === 451) return { missing: true, status: res.status };
    if (res.status === 409) return { commits: [], truncated: false }; // empty repo
    if (!res.ok) throw new Error(`${repo}: HTTP ${res.status}`);
    const batch = await res.json();
    all.push(...batch);
    if (batch.length < 100) return { commits: all, truncated: false };
  }
  return { commits: all, truncated: true };
}

async function main() {
  const repos = collectRepos();
  const since = new Date(Date.now() - WINDOW_DAYS * 86400000).toISOString();
  const out = { fetchedAt: new Date().toISOString(), windowDays: WINDOW_DAYS, repos: {}, missing: [] };
  for (const repo of repos) {
    try {
      const r = await fetchCommits(repo, since);
      if (r.missing) { out.missing.push(repo); console.log(`  ${repo}: missing (${r.status})`); continue; }
      const days = bucket(r.commits);
      const sorted = Object.keys(days).sort();
      const total = Object.values(days).reduce((a, b) => a + b, 0);
      const ordered = {};
      for (const k of sorted) ordered[k] = days[k];
      out.repos[repo] = { days: ordered, total, lastCommit: sorted.length ? sorted[sorted.length - 1] : null, truncated: r.truncated };
      console.log(`  ${repo}: ${total} commits, last ${out.repos[repo].lastCommit}${r.truncated ? " (truncated)" : ""}`);
    } catch (err) {
      console.error(`  ${repo}: ${err.message}`);
      out.missing.push(repo);
    }
  }
  out.missing.sort();
  writeFileSync(OUT, JSON.stringify(out, null, 1) + "\n");
  console.log(`wrote ${OUT}: ${Object.keys(out.repos).length} repos, ${out.missing.length} missing`);
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  main().catch((err) => { console.error(err); process.exit(1); });
}
