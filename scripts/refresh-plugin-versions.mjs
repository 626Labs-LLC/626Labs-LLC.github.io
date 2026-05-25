#!/usr/bin/env node
/**
 * refresh-plugin-versions.mjs — hub-native "live version" job.
 *
 * Reads content/plugin-repos.json (id -> owner/repo), asks the GitHub API for
 * each repo's tags, picks the highest semver, and writes data/plugin-versions.json
 * (id -> "vX.Y.Z"). render-plugin-pages.py bakes those into each plugin page's
 * version chip, so the hub's versions can't silently drift from the released tags
 * — no third-party badge images, just refreshed data the renderer consumes.
 *
 * Runs in CI (refresh-plugin-versions.yml, daily) using the implicit GITHUB_TOKEN
 * for rate limits; works unauthenticated locally too (12 calls is well under the
 * anonymous limit). A repo with no tags is simply omitted — the renderer falls
 * back to the hand-set version in plugin-pages.json heroMeta.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const REPOS = JSON.parse(readFileSync(join(ROOT, "content", "plugin-repos.json"), "utf8")).repos;
const OUT = join(ROOT, "data", "plugin-versions.json");
const TOKEN = process.env.GITHUB_TOKEN || process.env.GH_TOKEN || "";

const headers = {
  "User-Agent": "626labs-hub-version-refresh",
  Accept: "application/vnd.github+json",
  ...(TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {}),
};

// "v1.2.3" / "1.2" -> comparable [1,2,3]; non-semver tags sort lowest.
function semverKey(tag) {
  const m = String(tag).replace(/^v/i, "").match(/^(\d+)(?:\.(\d+))?(?:\.(\d+))?/);
  return m ? [+(m[1] || 0), +(m[2] || 0), +(m[3] || 0)] : [-1, 0, 0];
}
function cmpDesc(a, b) {
  const ka = semverKey(a), kb = semverKey(b);
  for (let i = 0; i < 3; i++) if (kb[i] !== ka[i]) return kb[i] - ka[i];
  return 0;
}

async function latestTag(repo) {
  const res = await fetch(`https://api.github.com/repos/${repo}/tags?per_page=100`, { headers });
  if (!res.ok) throw new Error(`${repo}: HTTP ${res.status}`);
  const tags = (await res.json()).map((t) => t.name).filter((n) => /^v?\d+\./i.test(n));
  if (!tags.length) return null;
  tags.sort(cmpDesc);
  return tags[0];
}

const out = {};
let failures = 0;
for (const [id, repo] of Object.entries(REPOS)) {
  try {
    const tag = await latestTag(repo);
    if (tag) {
      out[id] = tag.startsWith("v") ? tag : `v${tag}`;
      console.log(`  ${id.padEnd(20)} ${repo.padEnd(45)} ${out[id]}`);
    } else {
      console.log(`  ${id.padEnd(20)} ${repo.padEnd(45)} (no tags — skipped)`);
    }
  } catch (e) {
    failures++;
    console.error(`  ${id.padEnd(20)} ${repo.padEnd(45)} ERROR ${e.message}`);
  }
}

// Stable key order so the committed file diffs cleanly day to day.
const sorted = Object.fromEntries(Object.keys(out).sort().map((k) => [k, out[k]]));
writeFileSync(OUT, JSON.stringify(sorted, null, 2) + "\n");
console.log(`Wrote ${Object.keys(sorted).length} versions -> data/plugin-versions.json` + (failures ? ` (${failures} failed)` : ""));
process.exit(failures && !Object.keys(sorted).length ? 1 : 0);
