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
 *
 * ON THE BENCH. The same run writes data/bench.json, the homepage strip of
 * public repos ranked by commits in the last `bench.windowDays` days (config
 * in content/site.json's `bench` block; no block or `enabled: false` writes
 * nothing). Showcased repos reuse the counts above; every other public repo
 * in data/repos.json (the list track-traffic.yml keeps) is fetched for the
 * short window only, so a repo the site does not show yet appears the day it
 * heats up. Commits rank; summed unique visitors from data/traffic.csv only
 * break ties, because clone counts are mostly automation. /repo-meter/bench.js
 * reads the file in the browser, for the same --check reason.
 *
 *   data/bench.json
 *   { "generatedAt": "...", "windowDays": 14, "minCommits": 3,
 *     "items": [ { "repo", "title", "href", "blurb", "featured",
 *                  "commits", "lastCommit" } ] }
 */
import { readFileSync, writeFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const OUT = join(ROOT, "data", "repo-activity.json");
const BENCH_OUT = join(ROOT, "data", "bench.json");
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

// ─── on the bench ──────────────────────────────────────────────────

const lower = (s) => String(s || "").toLowerCase();

/** `text` cut at a word boundary to at most `max` characters. */
export function clip(text, max = 120) {
  const t = String(text || "").replace(/\s+/g, " ").trim();
  if (t.length <= max) return t;
  const cut = t.slice(0, max - 1);
  return cut.slice(0, Math.max(cut.lastIndexOf(" "), 40)).replace(/[\s,;:.-]+$/, "") + "…";
}

/** A site.json link as the browser will follow it from any page. */
function siteHref(p) {
  const raw = p.productPage || p.liveUrl || p.storeUrl || "";
  if (!raw) return "";
  if (/^https?:\/\//.test(raw) || raw.startsWith("/")) return raw;
  return "/" + raw;
}

/**
 * What the strip shows for each repo, keyed by lowercased owner/repo:
 * { title, href, blurb, featured }. A repo one product names takes that
 * product's title and page; a repo several products share (the plugin
 * monorepo) keeps its own name and its GitHub link. `featured` is true for
 * any repo the site already shows or links, false for one it does not.
 */
export function buildCatalog(root = ROOT) {
  const cat = {};
  const publicRepos = JSON.parse(readFileSync(join(root, "data", "repos.json"), "utf8")).repos || [];
  for (const r of publicRepos) {
    cat[lower(r.full_name)] = { title: r.name, href: r.html_url, blurb: clip(r.description), featured: false };
  }
  const ensure = (repo) => {
    const k = lower(repo);
    if (!cat[k]) cat[k] = { title: String(repo).split("/")[1], href: `https://github.com/${repo}`, blurb: "", featured: false };
    return cat[k];
  };
  const siteText = readFileSync(join(root, "content", "site.json"), "utf8");
  const site = JSON.parse(siteText);
  let products = site.products;
  if (products && !Array.isArray(products)) products = products.items || Object.values(products);
  products = (products || []).filter(Boolean);
  // Any repo the site links anywhere is already shown to a visitor.
  for (const m of siteText.matchAll(/github\.com\/([\w.-]+\/[\w-]+(?:\.[\w-]+)*)/g)) {
    ensure(m[1].replace(/\.git$/, "")).featured = true;
  }
  const byRepo = {};
  const add = (repo, p) => {
    const list = (byRepo[lower(repo)] ||= { repo, products: [] });
    if (!list.products.includes(p)) list.products.push(p);
  };
  for (const p of products) if (p.repo) add(p.repo, p);
  const plug = JSON.parse(readFileSync(join(root, "content", "plugin-repos.json"), "utf8")).repos || {};
  const byId = Object.fromEntries(products.map((p) => [p.id, p]));
  for (const [id, repo] of Object.entries(plug)) if (byId[id]) add(repo, byId[id]);
  for (const { repo, products: list } of Object.values(byRepo)) {
    const entry = ensure(repo);
    entry.featured = true;
    if (list.length !== 1) continue;
    const p = list[0];
    entry.title = p.title || entry.title;
    entry.href = siteHref(p) || entry.href;
    // The site's own words beat the GitHub description, which is written
    // for contributors: the tagline, else the description's first sentence.
    const first = String(p.description || "").replace(/<[^>]+>/g, "").split(/(?<=[.!?])\s/)[0];
    if (p.tagline || first) entry.blurb = clip(p.tagline || first, 140);
  }
  return cat;
}

/** Summed unique visitors per lowercased repo since `start` (YYYY-MM-DD). */
export function visitorsSince(csv, start) {
  const out = {};
  const lines = String(csv || "").split(/\r?\n/).filter(Boolean);
  const head = (lines.shift() || "").split(",");
  const iDate = head.indexOf("date"), iRepo = head.indexOf("repo"), iVis = head.indexOf("unique_visitors");
  if (iDate < 0 || iRepo < 0 || iVis < 0) return out;
  for (const line of lines) {
    const c = line.split(",");
    if (c[iDate] >= start) out[lower(c[iRepo])] = (out[lower(c[iRepo])] || 0) + (parseInt(c[iVis], 10) || 0);
  }
  return out;
}

/** First day of a `windowDays`-long window that ends on `today` (UTC). */
export function windowStart(today, windowDays) {
  return new Date(Date.parse(today + "T00:00:00Z") - (windowDays - 1) * 86400000).toISOString().slice(0, 10);
}

/**
 * The strip's rows. Commits inside the window rank; visitors only break a
 * tie; the repo name settles what is left, so the order is stable. A repo
 * under `minCommits` or on the `exclude` list never appears.
 */
export function rankBench({ today, config, activity, visitors = {}, catalog = {}, publicRepos = null }) {
  const { count = 5, windowDays = 14, minCommits = 3, exclude = [] } = config || {};
  const start = windowStart(today, windowDays);
  const skip = new Set(exclude.map(lower));
  // The strip is for PUBLIC repos. When the caller knows the public list, a
  // repo outside it never ranks, whatever the token that fetched its
  // commits could see: a maintainer's own token reads private repos (the
  // flagship's is private by design) that the CI token 404s.
  const open = publicRepos ? new Set(publicRepos.map(lower)) : null;
  const cat = Object.fromEntries(Object.entries(catalog).map(([k, v]) => [lower(k), v]));
  const vis = Object.fromEntries(Object.entries(visitors).map(([k, v]) => [lower(k), v]));
  const rows = [];
  for (const [repo, days] of Object.entries(activity || {})) {
    if (skip.has(lower(repo))) continue;
    if (open && !open.has(lower(repo))) continue;
    const inWindow = Object.keys(days || {}).filter((d) => d >= start && d <= today).sort();
    const commits = inWindow.reduce((n, d) => n + days[d], 0);
    if (commits < minCommits) continue;
    const c = cat[lower(repo)] || {};
    rows.push({
      repo,
      title: c.title || repo.split("/")[1],
      href: c.href || `https://github.com/${repo}`,
      blurb: c.blurb || "",
      featured: Boolean(c.featured),
      commits,
      lastCommit: inWindow[inWindow.length - 1],
    });
  }
  rows.sort((a, b) => b.commits - a.commits
    || (vis[lower(b.repo)] || 0) - (vis[lower(a.repo)] || 0)
    || a.repo.localeCompare(b.repo));
  return rows.slice(0, count);
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
  if (process.argv.includes("--bench-only")) {
    // Rebuild data/bench.json from the activity file as committed, fetching
    // only the public repos it lacks. The way to refresh the strip locally:
    // a full local run with a maintainer's token would also write private
    // repos' counts into data/repo-activity.json.
    await writeBench(JSON.parse(readFileSync(OUT, "utf8")));
    return;
  }
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
  await writeBench(out);
}

/** data/bench.json, from the counts just fetched plus every other public repo. */
async function writeBench(activityFile) {
  const config = JSON.parse(readFileSync(join(ROOT, "content", "site.json"), "utf8")).bench;
  if (!config || config.enabled === false) { console.log("bench: off in site.json, nothing written"); return; }
  const today = new Date().toISOString().slice(0, 10);
  const start = windowStart(today, config.windowDays || 14);
  const activity = {};
  for (const [repo, rec] of Object.entries(activityFile.repos)) activity[repo] = rec.days;
  const have = new Set([...Object.keys(activityFile.repos), ...activityFile.missing].map(lower));
  const skip = new Set((config.exclude || []).map(lower));
  const publicRepos = JSON.parse(readFileSync(join(ROOT, "data", "repos.json"), "utf8")).repos || [];
  for (const r of publicRepos) {
    const repo = r.full_name;
    if (have.has(lower(repo)) || skip.has(lower(repo))) continue;
    try {
      const got = await fetchCommits(repo, start + "T00:00:00Z");
      if (!got.missing) activity[repo] = bucket(got.commits);
    } catch (err) {
      console.error(`  bench ${repo}: ${err.message}`);
    }
  }
  const visitors = visitorsSince(readFileSync(join(ROOT, "data", "traffic.csv"), "utf8"), start);
  const items = rankBench({
    today, config, activity, visitors, catalog: buildCatalog(),
    publicRepos: publicRepos.map((r) => r.full_name),
  });
  const bench = { generatedAt: new Date().toISOString(), windowDays: config.windowDays || 14, minCommits: config.minCommits ?? 3, items };
  writeFileSync(BENCH_OUT, JSON.stringify(bench, null, 1) + "\n");
  console.log(`wrote ${BENCH_OUT}: ${items.map((i) => `${i.repo} ${i.commits}`).join(", ") || "no repo over the floor"}`);
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  main().catch((err) => { console.error(err); process.exit(1); });
}
