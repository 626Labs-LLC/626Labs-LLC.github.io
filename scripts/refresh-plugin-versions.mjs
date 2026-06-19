#!/usr/bin/env node
/**
 * refresh-plugin-versions.mjs — hub-native "live data" job for the plugin family.
 *
 * Reads content/plugin-repos.json (id -> owner/repo) and, for each repo, asks the
 * GitHub API for two things:
 *
 *   1. Tags  -> highest semver -> data/plugin-versions.json  (id -> "vX.Y.Z")
 *   2. Tree  -> commands/skills/agents counts -> data/plugin-stats.json
 *               (id -> { commands, skills, agents })
 *
 * render-plugin-pages.py bakes both into each plugin page — the version chip and
 * the capability chip — so neither can silently drift from the source repo. No
 * third-party badge images, just refreshed data the renderer consumes. The counts
 * mirror what Claude Code shows in its pre-install preview (files under commands/
 * and agents/, plus SKILL.md skill dirs).
 *
 * Runs in CI (refresh-plugin-versions.yml, daily) using the implicit GITHUB_TOKEN
 * for rate limits; works unauthenticated locally too (~24 calls is well under the
 * anonymous limit). A repo we can't read is simply omitted from that file — the
 * renderer falls back to the hand-set heroMeta version and shows no capability chip.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const REPOS = JSON.parse(readFileSync(join(ROOT, "content", "plugin-repos.json"), "utf8")).repos;
const OUT_VERSIONS = join(ROOT, "data", "plugin-versions.json");
const OUT_STATS = join(ROOT, "data", "plugin-stats.json");
const TOKEN = process.env.GITHUB_TOKEN || process.env.GH_TOKEN || "";

const headers = {
  "User-Agent": "626labs-hub-version-refresh",
  Accept: "application/vnd.github+json",
  ...(TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {}),
};

// "v1.2.3" / "1.2" / "vibe-sec-v0.9.0" -> comparable [1,2,3]; non-semver tags sort lowest.
function semverKey(tag) {
  const bare = String(tag).replace(/^.*?-v?(?=\d)/i, '').replace(/^v/i, '');
  const m = bare.match(/^(\d+)(?:\.(\d+))?(?:\.(\d+))?/);
  if (!m) return [-1, 0, 0];
  return [Number(m[1] || 0), Number(m[2] || 0), Number(m[3] || 0)];
}
function cmpDesc(a, b) {
  const ka = semverKey(a), kb = semverKey(b);
  for (let i = 0; i < 3; i++) if (kb[i] !== ka[i]) return kb[i] - ka[i];
  return 0;
}

async function latestTag(repo) {
  const res = await fetch(`https://api.github.com/repos/${repo}/tags?per_page=100`, { headers });
  if (!res.ok) throw new Error(`tags HTTP ${res.status}`);
  const tags = (await res.json()).map((t) => t.name).filter((n) => /(?:^|-)v?\d+\./i.test(n));
  if (!tags.length) return null;
  tags.sort(cmpDesc);
  return tags[0];
}

// Skip vendored / test / fixture trees so a plugin never counts its own test
// SKILL.md fixtures or a dependency's command files as capabilities.
const EXCLUDE = /(^|\/)(node_modules|\.git|tests?|__tests__|fixtures?|examples?)(\/|$)/i;

// Count what Claude Code's pre-install preview counts, from the repo file tree:
//   commands = *.md under any commands/ dir (README excluded)
//   skills   = SKILL.md files (one per skill dir), at any depth
//   agents   = *.md under any agents/ dir (README excluded)
// Path-based, so it works whether the plugin sits at the repo root or a subdir,
// and whether commands are flat or namespaced into subfolders.
function countCaps(paths) {
  let commands = 0, skills = 0, agents = 0;
  for (const path of paths) {
    if (EXCLUDE.test(path)) continue;
    const base = path.split("/").pop().toLowerCase();
    if (base === "skill.md") { skills++; continue; }
    if (!base.endsWith(".md") || base === "readme.md") continue;
    if (/(^|\/)commands\//i.test(path)) commands++;
    else if (/(^|\/)agents\//i.test(path)) agents++;
  }
  return { commands, skills, agents };
}

async function capabilities(repo) {
  // HEAD resolves to the repo's default branch; recursive=1 returns the full tree
  // in one call. These repos are small, so the truncated flag should never trip.
  const res = await fetch(`https://api.github.com/repos/${repo}/git/trees/HEAD?recursive=1`, { headers });
  if (!res.ok) throw new Error(`tree HTTP ${res.status}`);
  const body = await res.json();
  if (body.truncated) console.warn(`  ${repo}: tree truncated — capability counts may be low`);
  const paths = (body.tree || []).filter((n) => n.type === "blob").map((n) => n.path);
  return countCaps(paths);
}

const versions = {};
const stats = {};
let failures = 0;
for (const [id, repo] of Object.entries(REPOS)) {
  try {
    const tag = await latestTag(repo);
    if (tag) {
      const bare = String(tag).replace(/^.*?-v?(?=\d)/i, '').replace(/^v/i, '');
      versions[id] = 'v' + bare;
    }
    const caps = await capabilities(repo);
    stats[id] = caps;
    const vchip = (versions[id] || "(no tag)").padEnd(10);
    console.log(`  ${id.padEnd(20)} ${repo.padEnd(45)} ${vchip} ${caps.commands}c ${caps.skills}s ${caps.agents}a`);
  } catch (e) {
    failures++;
    console.error(`  ${id.padEnd(20)} ${repo.padEnd(45)} ERROR ${e.message}`);
  }
}

// Stable key order so the committed files diff cleanly day to day.
function sortedByKey(obj) {
  return Object.fromEntries(Object.keys(obj).sort().map((k) => [k, obj[k]]));
}
writeFileSync(OUT_VERSIONS, JSON.stringify(sortedByKey(versions), null, 2) + "\n");
writeFileSync(OUT_STATS, JSON.stringify(sortedByKey(stats), null, 2) + "\n");
console.log(
  `Wrote ${Object.keys(versions).length} versions -> data/plugin-versions.json, ` +
  `${Object.keys(stats).length} stat sets -> data/plugin-stats.json` +
  (failures ? ` (${failures} failed)` : "")
);
// Fail only if we got nothing useful at all (same posture as before: a few
// per-repo failures are tolerated — the renderer degrades gracefully).
process.exit(failures && !Object.keys(versions).length && !Object.keys(stats).length ? 1 : 0);
