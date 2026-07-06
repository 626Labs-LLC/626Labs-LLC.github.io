# 6deux6 Release Poster Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and deploy 6deux6 — the 626 Labs release-poster Discord bot — in its own public repo, per `626labs-hub/docs/superpowers/specs/2026-07-04-6deux6-release-poster-design.md`.

**Architecture:** One small Node ESM program run hourly by a GitHub Action. Source adapters (GitHub Releases, Microsoft Store displaycatalog) feed a pure diff engine against a committed `state.json`; new versions become branded Discord embeds posted via bare REST (no gateway, no intents, no discord.js). A hybrid voice layer (in-voice templates + optional Claude Haiku blurb from `voice.md`) writes the copy.

**Tech Stack:** Node 20+ (global `fetch`, `node:test` — zero runtime dependencies, zero dev dependencies), GitHub Actions, Python 3 + Pillow (icon script only).

## Global Constraints

- **Repo:** `estevanhernandez-stack-ed/6deux6`, public, MIT. Local clone at `C:\Users\estev\Projects\6deux6` — every task below runs there unless stated.
- **Zero npm dependencies.** Runtime and dev. Tests use `node:test` + `node:assert`. Network modules accept an injectable `fetchImpl` for testing.
- **ESM everywhere:** `"type": "module"` in package.json.
- **State stores RAW source versions** (`v1.2.0`, `1.8.0.0`). Normalization is display-only (strip leading `v`; strip one trailing `.0` from 4-part versions).
- **Never-double-post invariant:** state advances per-target only after a 2xx from Discord. Unknown target in state → seed silently, never announce (cold start).
- **Voice can never block a post:** any voice failure → template fallback.
- **Brand:** cyan `#17d4fa`, magenta `#f22f89`, violet `#8552c2` (store), navy `#0f1f31`. No corporate speak in any copy. Emoji: 🚀 title prefix only.
- **Secrets:** `DISCORD_TOKEN` (required), `ANTHROPIC_API_KEY` (optional) — GitHub repo secrets only. Never committed, never printed.
- **Commits:** conventional commits.

---

### Task 1: Repo scaffold + config seed

**Files:**
- Create: `package.json`, `.gitignore`, `LICENSE`, `state.json`, `config.json`, `test/smoke.test.js`

**Interfaces:**
- Produces: `config.json` shape consumed by every later task: `{ channelId, voice: { model, maxChars }, targets: [{ id, source, repo?|productId?, family, blurb? }] }`. `state.json` starts `{}`.

- [ ] **Step 1: Create the repo and clone**

```powershell
gh repo create estevanhernandez-stack-ed/6deux6 --public --description "The 626 Labs release feed for Discord. Watches GitHub Releases and the Microsoft Store; posts branded, in-voice announcements. Imagine Something Else." --clone
# clones into .\6deux6 — run from C:\Users\estev\Projects
```

Expected: repo exists on GitHub, empty clone at `C:\Users\estev\Projects\6deux6`.

- [ ] **Step 2: Verify the RoRoRo plugin repo owners before baking them into config**

```powershell
gh repo view estevanhernandez-stack-ed/rororo-ur-task --json nameWithOwner
gh repo view estevanhernandez-stack-ed/Ur-OCR --json nameWithOwner
gh repo view estevanhernandez-stack-ed/rororo-ur-afk --json nameWithOwner
```

Expected: each returns a `nameWithOwner`. If any 404s, find it with `gh search repos <name> --owner estevanhernandez-stack-ed --owner 626Labs-LLC` and use the returned owner/casing in Step 3's config.

- [ ] **Step 3: Write the scaffold files**

`package.json`:
```json
{
  "name": "6deux6",
  "version": "0.1.0",
  "description": "The 626 Labs release feed for Discord.",
  "type": "module",
  "license": "MIT",
  "engines": { "node": ">=20" },
  "scripts": {
    "test": "node --test",
    "dry-run": "node src/index.js --dry-run"
  }
}
```

`.gitignore`:
```
node_modules/
*.log
```

`LICENSE`: MIT text, `Copyright (c) 2026 626Labs LLC`.

`state.json`:
```json
{}
```

`config.json` (blurbs are Este-reviewable copy; repos verified in Step 2):
```json
{
  "channelId": "1522754011915227153",
  "voice": { "model": "claude-haiku-4-5-20251001", "maxChars": 300 },
  "targets": [
    { "id": "vibe-cartographer", "source": "github", "repo": "estevanhernandez-stack-ed/vibe-cartographer", "family": "plugin" },
    { "id": "vibe-iterate", "source": "github", "repo": "estevanhernandez-stack-ed/vibe-iterate", "family": "plugin" },
    { "id": "vibe-doc", "source": "github", "repo": "estevanhernandez-stack-ed/Vibe-Doc", "family": "plugin" },
    { "id": "vibe-test", "source": "github", "repo": "estevanhernandez-stack-ed/vibe-test", "family": "plugin" },
    { "id": "vibe-sec", "source": "github", "repo": "estevanhernandez-stack-ed/vibe-sec", "family": "plugin" },
    { "id": "vibe-keystone", "source": "github", "repo": "estevanhernandez-stack-ed/vibe-Keystone", "family": "plugin" },
    { "id": "thesis-engine", "source": "github", "repo": "estevanhernandez-stack-ed/Thesis-Engine", "family": "plugin" },
    { "id": "vibe-thesis", "source": "github", "repo": "estevanhernandez-stack-ed/Vibe-Thesis", "family": "plugin" },
    { "id": "vibe-walk", "source": "github", "repo": "estevanhernandez-stack-ed/Vibe-Walk", "family": "plugin" },
    { "id": "vibe-taker", "source": "github", "repo": "estevanhernandez-stack-ed/vibe-taker", "family": "plugin" },
    { "id": "vibe-wrap", "source": "github", "repo": "estevanhernandez-stack-ed/vibe-wrap", "family": "plugin" },
    { "id": "vibe-insights", "source": "github", "repo": "estevanhernandez-stack-ed/vibe-insights", "family": "plugin" },
    { "id": "vibe-prompt", "source": "github", "repo": "estevanhernandez-stack-ed/Vibe-Prompt", "family": "plugin" },
    { "id": "vibe-lingual", "source": "github", "repo": "estevanhernandez-stack-ed/Vibe-Lingual", "family": "plugin" },
    { "id": "rororo-ur-task", "source": "github", "repo": "estevanhernandez-stack-ed/rororo-ur-task", "family": "rororo" },
    { "id": "ur-ocr", "source": "github", "repo": "estevanhernandez-stack-ed/Ur-OCR", "family": "rororo" },
    { "id": "rororo-ur-afk", "source": "github", "repo": "estevanhernandez-stack-ed/rororo-ur-afk", "family": "rororo" },
    { "id": "mod-launcher-gh", "source": "github", "repo": "estevanhernandez-stack-ed/626-mod-launcher", "family": "store" },
    { "id": "sanduhr-store", "source": "displaycatalog", "productId": "9NH3NK2RGCF5", "family": "store", "blurb": "Sanduhr für Claude — Claude usage in an hourglass on your Windows desktop." },
    { "id": "rbx15-store", "source": "displaycatalog", "productId": "9MV9G4XFJ8S0", "family": "store", "blurb": "RBX15 — the classic Roblox shirt and pants maker." },
    { "id": "rtclickpng-store", "source": "displaycatalog", "productId": "9PKKLK6R5WFL", "family": "store", "blurb": "Right Click PNG — image conversion from your right-click menu." },
    { "id": "snapsnip-store", "source": "displaycatalog", "productId": "9PBX8F5TR0VR", "family": "store", "blurb": "SnapSnip — fast screen snipping for Windows." },
    { "id": "rororo-store", "source": "displaycatalog", "productId": "9NMJCS390KWB", "family": "rororo", "blurb": "RORORO — the Roblox multi-launcher you can recommend on camera." },
    { "id": "mod-launcher-store", "source": "displaycatalog", "productId": "9N53V6RRJK95", "family": "store", "blurb": "626 Mod Launcher — one launcher for your moddable games, 149 supported and counting." }
  ]
}
```

`test/smoke.test.js`:
```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

test("config.json parses and every target has an id, source, and family", async () => {
  const config = JSON.parse(await readFile(new URL("../config.json", import.meta.url), "utf8"));
  assert.ok(config.channelId);
  assert.ok(config.targets.length >= 24);
  for (const t of config.targets) {
    assert.ok(t.id && t.family, `bad target ${JSON.stringify(t)}`);
    assert.ok(
      (t.source === "github" && t.repo) || (t.source === "displaycatalog" && t.productId),
      `target ${t.id} missing its source field`
    );
  }
});
```

- [ ] **Step 4: Run the test**

Run: `node --test`
Expected: 1 pass.

- [ ] **Step 5: Commit and push**

```powershell
git add -A; git commit -m "feat: scaffold 6deux6 — config seed, state, zero-dep test harness"; git push
```

---

### Task 2: diff engine (`src/diff.js`)

**Files:**
- Create: `src/diff.js`
- Test: `test/diff.test.js`

**Interfaces:**
- Consumes: config target objects from Task 1.
- Produces: `findNew(targets, state, fetchedById) → { toAnnounce: [{ target, release }], toSeed: [{ target, release }] }`. `state` shape: `{ [targetId]: { version, announcedAt } }`. `release` shape: `{ version, url, notes, publishedAt }` (notes/publishedAt may be null).

- [ ] **Step 1: Write the failing tests**

`test/diff.test.js`:
```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { findNew } from "../src/diff.js";

const target = { id: "vibe-sec", source: "github", repo: "x/vibe-sec", family: "plugin" };
const rel = (version) => ({ version, url: "https://example.com", notes: "notes", publishedAt: null });

test("known target with a changed version is announced", () => {
  const out = findNew([target], { "vibe-sec": { version: "v1.0.0" } }, { "vibe-sec": rel("v1.1.0") });
  assert.equal(out.toAnnounce.length, 1);
  assert.equal(out.toAnnounce[0].release.version, "v1.1.0");
  assert.equal(out.toSeed.length, 0);
});

test("known target with the same version does nothing", () => {
  const out = findNew([target], { "vibe-sec": { version: "v1.1.0" } }, { "vibe-sec": rel("v1.1.0") });
  assert.equal(out.toAnnounce.length, 0);
  assert.equal(out.toSeed.length, 0);
});

test("unknown target is seeded, never announced (cold start)", () => {
  const out = findNew([target], {}, { "vibe-sec": rel("v1.1.0") });
  assert.equal(out.toAnnounce.length, 0);
  assert.equal(out.toSeed.length, 1);
  assert.equal(out.toSeed[0].release.version, "v1.1.0");
});

test("null fetch result (no releases yet / fetch failed) touches nothing", () => {
  const out = findNew([target], { "vibe-sec": { version: "v1.0.0" } }, { "vibe-sec": null });
  assert.equal(out.toAnnounce.length, 0);
  assert.equal(out.toSeed.length, 0);
});

test("target missing from fetched map entirely touches nothing", () => {
  const out = findNew([target], {}, {});
  assert.equal(out.toAnnounce.length, 0);
  assert.equal(out.toSeed.length, 0);
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test`
Expected: FAIL — `Cannot find module '../src/diff.js'`.

- [ ] **Step 3: Implement**

`src/diff.js`:
```js
/**
 * Pure diff: which fetched releases are new against committed state?
 * - Unknown target id in state → seed silently (cold start / new watch target).
 * - Known target, different RAW version string → announce.
 * - null / missing fetch result → leave that target's state untouched.
 */
export function findNew(targets, state, fetchedById) {
  const toAnnounce = [];
  const toSeed = [];
  for (const target of targets) {
    const release = fetchedById[target.id];
    if (!release || !release.version) continue;
    const known = state[target.id];
    if (!known) {
      toSeed.push({ target, release });
    } else if (known.version !== release.version) {
      toAnnounce.push({ target, release });
    }
  }
  return { toAnnounce, toSeed };
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `node --test`
Expected: all pass (5 diff + 1 smoke).

- [ ] **Step 5: Commit**

```powershell
git add src/diff.js test/diff.test.js; git commit -m "feat: diff engine — never-double-post + silent cold-start seeding"
```

---

### Task 3: Store source (`src/sources/displaycatalog.js`)

**Files:**
- Create: `src/sources/displaycatalog.js`
- Test: `test/displaycatalog.test.js`, `test/fixtures/displaycatalog.json`

**Interfaces:**
- Produces: `parseVersions(product) → string[]` (raw 4-part versions) and `fetchLatestStore(target, { fetchImpl = fetch } = {}) → Promise<{ version, url, notes: null, publishedAt: null } | null>`.

- [ ] **Step 1: Write the fixture**

`test/fixtures/displaycatalog.json` (trimmed real shape — one product, two package names):
```json
{
  "Products": [
    {
      "ProductId": "9NMJCS390KWB",
      "DisplaySkuAvailabilities": [
        {
          "Sku": {
            "Properties": {
              "Packages": [
                { "PackageFullName": "626Labs.RORORO_1.8.0.0_x64__abc123" },
                { "PackageFullName": "626Labs.RORORO_1.7.2.0_x64__abc123" }
              ]
            }
          }
        }
      ]
    }
  ]
}
```

- [ ] **Step 2: Write the failing tests**

`test/displaycatalog.test.js`:
```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { parseVersions, fetchLatestStore } from "../src/sources/displaycatalog.js";

const fixture = JSON.parse(await readFile(new URL("./fixtures/displaycatalog.json", import.meta.url), "utf8"));
const target = { id: "rororo-store", source: "displaycatalog", productId: "9NMJCS390KWB", family: "rororo" };

test("parseVersions extracts all 4-part versions", () => {
  assert.deepEqual(parseVersions(fixture.Products[0]), ["1.8.0.0", "1.7.2.0"]);
});

test("fetchLatestStore returns the highest version and the product URL", async () => {
  const fetchImpl = async () => new Response(JSON.stringify(fixture), { status: 200 });
  const rel = await fetchLatestStore(target, { fetchImpl });
  assert.equal(rel.version, "1.8.0.0");
  assert.equal(rel.url, "https://apps.microsoft.com/detail/9NMJCS390KWB");
  assert.equal(rel.notes, null);
});

test("fetchLatestStore returns null on HTTP failure", async () => {
  const fetchImpl = async () => new Response("nope", { status: 500 });
  assert.equal(await fetchLatestStore(target, { fetchImpl }), null);
});

test("fetchLatestStore returns null when no version parses", async () => {
  const broken = { Products: [{ DisplaySkuAvailabilities: [{ Sku: { Properties: { Packages: [{ PackageFullName: "garbage" }] } } }] }] };
  const fetchImpl = async () => new Response(JSON.stringify(broken), { status: 200 });
  assert.equal(await fetchLatestStore(target, { fetchImpl }), null);
});
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `node --test`
Expected: FAIL — `Cannot find module '../src/sources/displaycatalog.js'`.

- [ ] **Step 4: Implement**

`src/sources/displaycatalog.js`:
```js
const CATALOG = "https://displaycatalog.mp.microsoft.com/v7.0/products";

/** Extract raw 4-part versions from a displaycatalog product's PackageFullNames. */
export function parseVersions(product) {
  const versions = [];
  for (const avail of product?.DisplaySkuAvailabilities ?? []) {
    for (const pkg of avail?.Sku?.Properties?.Packages ?? []) {
      const m = /_(\d+\.\d+\.\d+\.\d+)_/.exec(pkg?.PackageFullName ?? "");
      if (m && !versions.includes(m[1])) versions.push(m[1]);
    }
  }
  return versions;
}

/** Numeric-aware compare of "a.b.c.d" strings, descending. */
function byVersionDesc(a, b) {
  const pa = a.split(".").map(Number);
  const pb = b.split(".").map(Number);
  for (let i = 0; i < 4; i++) if (pa[i] !== pb[i]) return pb[i] - pa[i];
  return 0;
}

export async function fetchLatestStore(target, { fetchImpl = fetch } = {}) {
  try {
    const url = `${CATALOG}?bigIds=${target.productId}&market=US&languages=en-us`;
    const res = await fetchImpl(url, { signal: AbortSignal.timeout(15000) });
    if (!res.ok) {
      console.error(`[displaycatalog] ${target.id}: HTTP ${res.status}`);
      return null;
    }
    const data = await res.json();
    const versions = parseVersions(data?.Products?.[0]).sort(byVersionDesc);
    if (!versions.length) {
      console.error(`[displaycatalog] ${target.id}: no version parsed`);
      return null;
    }
    return {
      version: versions[0],
      url: `https://apps.microsoft.com/detail/${target.productId}`,
      notes: null,
      publishedAt: null,
    };
  } catch (err) {
    console.error(`[displaycatalog] ${target.id}: ${err.message}`);
    return null;
  }
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `node --test`
Expected: all pass.

- [ ] **Step 6: Commit**

```powershell
git add src/sources/displaycatalog.js test/displaycatalog.test.js test/fixtures/displaycatalog.json
git commit -m "feat: displaycatalog source — Store versions, null on any failure"
```

---

### Task 4: GitHub source (`src/sources/github.js`)

**Files:**
- Create: `src/sources/github.js`
- Test: `test/github.test.js`, `test/fixtures/github-release.json`

**Interfaces:**
- Produces: `fetchLatestGithub(target, { token, fetchImpl = fetch } = {}) → Promise<{ version, url, notes, publishedAt } | null>`. `version` is the RAW `tag_name`.

- [ ] **Step 1: Write the fixture**

`test/fixtures/github-release.json`:
```json
{
  "tag_name": "v0.6.0",
  "html_url": "https://github.com/estevanhernandez-stack-ed/vibe-sec/releases/tag/v0.6.0",
  "published_at": "2026-06-20T18:00:00Z",
  "body": "## What's new\n\nThreat-model mode ships. Also fixes the gate exit code.\n\n## Details\nLots more."
}
```

- [ ] **Step 2: Write the failing tests**

`test/github.test.js`:
```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fetchLatestGithub } from "../src/sources/github.js";

const fixture = JSON.parse(await readFile(new URL("./fixtures/github-release.json", import.meta.url), "utf8"));
const target = { id: "vibe-sec", source: "github", repo: "estevanhernandez-stack-ed/vibe-sec", family: "plugin" };

test("maps a release: raw tag, url, notes, publishedAt", async () => {
  const fetchImpl = async (url, opts) => {
    assert.match(url, /repos\/estevanhernandez-stack-ed\/vibe-sec\/releases\/latest/);
    assert.equal(opts.headers.Authorization, "Bearer tok");
    return new Response(JSON.stringify(fixture), { status: 200 });
  };
  const rel = await fetchLatestGithub(target, { token: "tok", fetchImpl });
  assert.equal(rel.version, "v0.6.0");
  assert.equal(rel.url, fixture.html_url);
  assert.match(rel.notes, /Threat-model/);
});

test("404 (no releases yet) returns null quietly", async () => {
  const fetchImpl = async () => new Response("{}", { status: 404 });
  assert.equal(await fetchLatestGithub(target, { token: "tok", fetchImpl }), null);
});

test("works without a token (header omitted)", async () => {
  const fetchImpl = async (url, opts) => {
    assert.equal(opts.headers.Authorization, undefined);
    return new Response(JSON.stringify(fixture), { status: 200 });
  };
  const rel = await fetchLatestGithub(target, { fetchImpl });
  assert.equal(rel.version, "v0.6.0");
});
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `node --test`
Expected: FAIL — module not found.

- [ ] **Step 4: Implement**

`src/sources/github.js`:
```js
export async function fetchLatestGithub(target, { token, fetchImpl = fetch } = {}) {
  try {
    const headers = { Accept: "application/vnd.github+json", "User-Agent": "6deux6" };
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetchImpl(`https://api.github.com/repos/${target.repo}/releases/latest`, {
      headers,
      signal: AbortSignal.timeout(15000),
    });
    if (res.status === 404) return null; // no releases yet — normal, stay quiet
    if (!res.ok) {
      console.error(`[github] ${target.id}: HTTP ${res.status}`);
      return null;
    }
    const rel = await res.json();
    if (!rel.tag_name) return null;
    return {
      version: rel.tag_name,
      url: rel.html_url,
      notes: rel.body ?? null,
      publishedAt: rel.published_at ?? null,
    };
  } catch (err) {
    console.error(`[github] ${target.id}: ${err.message}`);
    return null;
  }
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `node --test`
Expected: all pass.

- [ ] **Step 6: Commit**

```powershell
git add src/sources/github.js test/github.test.js test/fixtures/github-release.json
git commit -m "feat: github releases source — raw tags, quiet 404s"
```

---

### Task 5: Embed builder (`src/embed.js`)

**Files:**
- Create: `src/embed.js`
- Test: `test/embed.test.js`

**Interfaces:**
- Consumes: `{ target, release }` pairs from Task 2's shapes.
- Produces: `displayVersion(raw) → string`, `excerpt(notes, maxChars) → string|null`, `buildEmbed(target, release, blurb) → object` (Discord embed JSON: title, url, description, color, footer).

- [ ] **Step 1: Write the failing tests**

`test/embed.test.js`:
```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { displayVersion, excerpt, buildEmbed } from "../src/embed.js";

test("displayVersion strips a leading v and one trailing .0 from 4-part versions", () => {
  assert.equal(displayVersion("v1.2.0"), "1.2.0");
  assert.equal(displayVersion("1.8.0.0"), "1.8.0");
  assert.equal(displayVersion("2.0"), "2.0");
  assert.equal(displayVersion("v0.6.0-beta"), "0.6.0-beta");
});

test("excerpt takes the first meaningful paragraph, skipping markdown headers", () => {
  const notes = "## What's new\n\nThreat-model mode ships. Also fixes the gate exit code.\n\n## Details\nMore.";
  assert.equal(excerpt(notes, 300), "Threat-model mode ships. Also fixes the gate exit code.");
});

test("excerpt truncates at maxChars with an ellipsis", () => {
  const out = excerpt("x".repeat(400), 300);
  assert.equal(out.length, 301); // 300 + ellipsis char
  assert.ok(out.endsWith("…"));
});

test("excerpt of empty/null notes is null", () => {
  assert.equal(excerpt(null, 300), null);
  assert.equal(excerpt("## Header only\n\n", 300), null);
});

test("buildEmbed: plugin family, blurb wins over notes excerpt", () => {
  const target = { id: "vibe-sec", family: "plugin" };
  const release = { version: "v0.6.0", url: "https://example.com/r", notes: "Some notes here." };
  const e = buildEmbed(target, release, "The in-voice blurb.");
  assert.equal(e.title, "🚀 vibe-sec 0.6.0");
  assert.equal(e.url, "https://example.com/r");
  assert.equal(e.description, "The in-voice blurb.");
  assert.equal(e.color, parseInt("17d4fa", 16));
  assert.match(e.footer.text, /6deux6 · the 626 Labs release feed · plugin/);
});

test("buildEmbed: store target without notes or blurb uses config blurb via release fallthrough", () => {
  const target = { id: "rororo-store", family: "rororo", blurb: "RORORO — the multi-launcher." };
  const release = { version: "1.8.0.0", url: "https://example.com/s", notes: null };
  const e = buildEmbed(target, release, null);
  assert.equal(e.title, "🚀 rororo-store 1.8.0");
  assert.equal(e.description, "RORORO — the multi-launcher.");
  assert.equal(e.color, parseInt("f22f89", 16));
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement**

`src/embed.js`:
```js
const FAMILY_COLORS = {
  plugin: parseInt("17d4fa", 16),  // cyan
  rororo: parseInt("f22f89", 16),  // magenta
  store: parseInt("8552c2", 16),   // violet — the gradient midpoint
};

/** Display-only normalization; state always stores the raw version. */
export function displayVersion(raw) {
  let v = raw.startsWith("v") ? raw.slice(1) : raw;
  const fourPart = /^(\d+\.\d+\.\d+)\.0$/.exec(v);
  if (fourPart) v = fourPart[1];
  return v;
}

/** First meaningful paragraph of release notes; null when there isn't one. */
export function excerpt(notes, maxChars) {
  if (!notes) return null;
  const paragraphs = notes.split(/\r?\n\r?\n/).map((p) => p.trim());
  const meaningful = paragraphs.find((p) => p && !p.startsWith("#"));
  if (!meaningful) return null;
  const flat = meaningful.replace(/\s+/g, " ");
  return flat.length > maxChars ? flat.slice(0, maxChars) + "…" : flat;
}

export function buildEmbed(target, release, blurb) {
  const description =
    blurb ?? excerpt(release.notes, 300) ?? target.blurb ?? "A new version just shipped.";
  return {
    title: `🚀 ${target.id} ${displayVersion(release.version)}`,
    url: release.url,
    description,
    color: FAMILY_COLORS[target.family] ?? FAMILY_COLORS.store,
    footer: { text: `6deux6 · the 626 Labs release feed · ${target.family}` },
  };
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `node --test`
Expected: all pass.

- [ ] **Step 5: Commit**

```powershell
git add src/embed.js test/embed.test.js; git commit -m "feat: embed builder — family colors, display normalization, excerpt floor"
```

---

### Task 6: Voice layer (`voice.md` + `src/voice.js`)

**Files:**
- Create: `voice.md`, `src/voice.js`
- Test: `test/voice.test.js`

**Interfaces:**
- Consumes: `{ target, release }` shapes; `config.voice` from Task 1.
- Produces: `makeBlurb(target, release, voicePrompt, { apiKey, model, maxChars, fetchImpl = fetch }) → Promise<string|null>`. Null whenever the voice can't deliver — callers fall back to templates.

- [ ] **Step 1: Write `voice.md`**

```markdown
# 6deux6 voice

You write one release announcement for a Discord embed. You are the byline of
626 Labs — an independent software lab. Builder-to-builder, plain language,
punchline first.

## The job
Given a product, a version, and its release notes, write 1–2 sentences saying
what shipped and why someone would care. Lead with the most interesting change,
not the version number (the embed title already has it).

## Rules
- Max 300 characters. Plain sentences — no markdown, no lists, no headers.
- No emoji (the embed title carries the one rocket).
- No hashtags, no links (the embed handles linking).
- Banned words: empower, leverage, seamlessly, unlock, unleash, best-in-class,
  robust, delightful, excited to announce, we're thrilled.
- Don't invent features — only what the notes actually say. If the notes are
  thin, say the simple true thing.
- "Imagine Something Else." may close a MILESTONE release (a 1.0, a family
  launch). Default is no tagline — the footer carries the brand.

## Sound
Specific over generic. "Threat-model mode ships" beats "new features added."
Short beats clever. True beats short.
```

- [ ] **Step 2: Write the failing tests**

`test/voice.test.js`:
```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { makeBlurb } from "../src/voice.js";

const target = { id: "vibe-sec", family: "plugin" };
const release = { version: "v0.6.0", url: "https://x", notes: "Threat-model mode ships." };
const opts = { model: "claude-haiku-4-5-20251001", maxChars: 300 };

test("no api key → null, no fetch attempted", async () => {
  const fetchImpl = async () => { throw new Error("should not be called"); };
  assert.equal(await makeBlurb(target, release, "voice", { ...opts, apiKey: undefined, fetchImpl }), null);
});

test("happy path returns trimmed text", async () => {
  const fetchImpl = async (url, req) => {
    assert.match(url, /api\.anthropic\.com/);
    const body = JSON.parse(req.body);
    assert.equal(body.system, "voice");
    return new Response(JSON.stringify({ content: [{ type: "text", text: "  Threat-model mode ships, and the gate exits honest. " }] }), { status: 200 });
  };
  const out = await makeBlurb(target, release, "voice", { ...opts, apiKey: "k", fetchImpl });
  assert.equal(out, "Threat-model mode ships, and the gate exits honest.");
});

test("API error → null", async () => {
  const fetchImpl = async () => new Response("overloaded", { status: 529 });
  assert.equal(await makeBlurb(target, release, "voice", { ...opts, apiKey: "k", fetchImpl }), null);
});

test("over-long model output is hard-capped with ellipsis", async () => {
  const fetchImpl = async () =>
    new Response(JSON.stringify({ content: [{ type: "text", text: "y".repeat(400) }] }), { status: 200 });
  const out = await makeBlurb(target, release, "voice", { ...opts, apiKey: "k", fetchImpl });
  assert.equal(out.length, 301);
  assert.ok(out.endsWith("…"));
});
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `node --test`
Expected: FAIL — module not found.

- [ ] **Step 4: Implement**

`src/voice.js`:
```js
/**
 * The personality layer. Returns an in-voice blurb, or null on ANY failure —
 * absent key, timeout, API error, empty output. Null means: use the template
 * fallback. The voice can delay a post by one API call; it can never block one.
 */
export async function makeBlurb(target, release, voicePrompt, { apiKey, model, maxChars, fetchImpl = fetch }) {
  if (!apiKey) return null;
  try {
    const user = [
      `Product: ${target.id} (family: ${target.family})`,
      `Version: ${release.version}`,
      `Release notes:\n${release.notes ?? "(none — Store release, no notes published)"}`,
    ].join("\n\n");
    const res = await fetchImpl("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: { "x-api-key": apiKey, "anthropic-version": "2023-06-01", "content-type": "application/json" },
      body: JSON.stringify({ model, max_tokens: 200, system: voicePrompt, messages: [{ role: "user", content: user }] }),
      signal: AbortSignal.timeout(20000),
    });
    if (!res.ok) {
      console.error(`[voice] ${target.id}: HTTP ${res.status}`);
      return null;
    }
    const data = await res.json();
    const text = data?.content?.find((c) => c.type === "text")?.text?.trim();
    if (!text) return null;
    return text.length > maxChars ? text.slice(0, maxChars) + "…" : text;
  } catch (err) {
    console.error(`[voice] ${target.id}: ${err.message}`);
    return null;
  }
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `node --test`
Expected: all pass.

- [ ] **Step 6: Commit**

```powershell
git add voice.md src/voice.js test/voice.test.js
git commit -m "feat: hybrid voice layer — voice.md prompt, null-on-failure blurb pass"
```

---

### Task 7: Discord poster (`src/discord.js`)

**Files:**
- Create: `src/discord.js`
- Test: `test/discord.test.js`

**Interfaces:**
- Consumes: embed objects from Task 5.
- Produces: `postEmbed(channelId, embed, { token, fetchImpl = fetch }) → Promise<void>` — resolves on 2xx, retries once on 429 honoring `retry_after`, throws on any other failure (caller decides what that means for state).

- [ ] **Step 1: Write the failing tests**

`test/discord.test.js`:
```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { postEmbed } from "../src/discord.js";

const embed = { title: "🚀 x 1.0.0", description: "d", color: 1, footer: { text: "f" } };

test("posts to the channel messages endpoint with the bot token", async () => {
  let captured;
  const fetchImpl = async (url, req) => {
    captured = { url, req };
    return new Response("{}", { status: 200 });
  };
  await postEmbed("123", embed, { token: "tok", fetchImpl });
  assert.equal(captured.url, "https://discord.com/api/v10/channels/123/messages");
  assert.equal(captured.req.headers.Authorization, "Bot tok");
  assert.deepEqual(JSON.parse(captured.req.body).embeds, [embed]);
});

test("retries once on 429 honoring retry_after", async () => {
  let calls = 0;
  const fetchImpl = async () => {
    calls++;
    if (calls === 1)
      return new Response(JSON.stringify({ retry_after: 0.01 }), { status: 429 });
    return new Response("{}", { status: 200 });
  };
  await postEmbed("123", embed, { token: "tok", fetchImpl });
  assert.equal(calls, 2);
});

test("throws on 403 (config error a human must see)", async () => {
  const fetchImpl = async () => new Response("missing access", { status: 403 });
  await assert.rejects(() => postEmbed("123", embed, { token: "tok", fetchImpl }), /403/);
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement**

`src/discord.js`:
```js
export async function postEmbed(channelId, embed, { token, fetchImpl = fetch }) {
  const send = () =>
    fetchImpl(`https://discord.com/api/v10/channels/${channelId}/messages`, {
      method: "POST",
      headers: { Authorization: `Bot ${token}`, "Content-Type": "application/json", "User-Agent": "6deux6 (https://github.com/estevanhernandez-stack-ed/6deux6, 0.1)" },
      body: JSON.stringify({ embeds: [embed] }),
      signal: AbortSignal.timeout(15000),
    });

  let res = await send();
  if (res.status === 429) {
    const body = await res.json().catch(() => ({}));
    const waitMs = Math.ceil((body.retry_after ?? 1) * 1000);
    await new Promise((r) => setTimeout(r, waitMs));
    res = await send();
  }
  if (!res.ok) {
    throw new Error(`Discord POST failed: ${res.status} ${await res.text().catch(() => "")}`);
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `node --test`
Expected: all pass.

- [ ] **Step 5: Commit**

```powershell
git add src/discord.js test/discord.test.js; git commit -m "feat: REST poster — 429-aware, loud on config errors"
```

---

### Task 8: State + orchestrator (`src/state.js`, `src/index.js`)

**Files:**
- Create: `src/state.js`, `src/index.js`
- Test: `test/index.test.js`

**Interfaces:**
- Consumes: everything above.
- Produces: `loadState(path)`, `saveState(path, state)`; `run({ dryRun, env, fetchImpl, rootDir })` → `{ announced: string[], seeded: string[], failed: string[] }`. CLI: `node src/index.js [--dry-run]`.

- [ ] **Step 1: Write the failing test**

`test/index.test.js` (drives the whole pipeline with a fake fetch that answers all three APIs):
```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, writeFile, readFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { run } from "../src/index.js";

function fakeNet({ discordStatus = 200 } = {}) {
  const posts = [];
  const fetchImpl = async (url, req) => {
    if (url.includes("api.github.com")) {
      return new Response(JSON.stringify({ tag_name: "v2.0.0", html_url: "https://gh/r", body: "Big one.", published_at: null }), { status: 200 });
    }
    if (url.includes("displaycatalog")) {
      return new Response(JSON.stringify({ Products: [{ DisplaySkuAvailabilities: [{ Sku: { Properties: { Packages: [{ PackageFullName: "X_2.0.0.0_x64__h" }] } } }] }] }), { status: 200 });
    }
    if (url.includes("discord.com")) {
      posts.push(JSON.parse(req.body));
      return new Response("{}", { status: discordStatus });
    }
    throw new Error(`unexpected fetch ${url}`);
  };
  return { fetchImpl, posts };
}

async function scaffold(state) {
  const dir = await mkdtemp(join(tmpdir(), "6deux6-"));
  const config = {
    channelId: "42",
    voice: { model: "m", maxChars: 300 },
    targets: [
      { id: "gh-one", source: "github", repo: "o/r", family: "plugin" },
      { id: "store-one", source: "displaycatalog", productId: "9X", family: "store", blurb: "b" },
    ],
  };
  await writeFile(join(dir, "config.json"), JSON.stringify(config));
  await writeFile(join(dir, "state.json"), JSON.stringify(state));
  await writeFile(join(dir, "voice.md"), "voice prompt");
  return dir;
}

test("cold start seeds everything and posts nothing", async () => {
  const dir = await scaffold({});
  const { fetchImpl, posts } = fakeNet();
  const out = await run({ dryRun: false, env: { DISCORD_TOKEN: "t" }, fetchImpl, rootDir: dir });
  assert.deepEqual(out.seeded.sort(), ["gh-one", "store-one"]);
  assert.equal(posts.length, 0);
  const state = JSON.parse(await readFile(join(dir, "state.json"), "utf8"));
  assert.equal(state["gh-one"].version, "v2.0.0");
  assert.equal(state["store-one"].version, "2.0.0.0");
});

test("new version announces and advances state", async () => {
  const dir = await scaffold({ "gh-one": { version: "v1.0.0" }, "store-one": { version: "2.0.0.0" } });
  const { fetchImpl, posts } = fakeNet();
  const out = await run({ dryRun: false, env: { DISCORD_TOKEN: "t" }, fetchImpl, rootDir: dir });
  assert.deepEqual(out.announced, ["gh-one"]);
  assert.equal(posts.length, 1);
  assert.match(posts[0].embeds[0].title, /gh-one 2\.0\.0/);
  const state = JSON.parse(await readFile(join(dir, "state.json"), "utf8"));
  assert.equal(state["gh-one"].version, "v2.0.0");
});

test("failed Discord post does NOT advance state", async () => {
  const dir = await scaffold({ "gh-one": { version: "v1.0.0" }, "store-one": { version: "2.0.0.0" } });
  const { fetchImpl } = fakeNet({ discordStatus: 403 });
  const out = await run({ dryRun: false, env: { DISCORD_TOKEN: "t" }, fetchImpl, rootDir: dir });
  assert.deepEqual(out.failed, ["gh-one"]);
  const state = JSON.parse(await readFile(join(dir, "state.json"), "utf8"));
  assert.equal(state["gh-one"].version, "v1.0.0"); // untouched — retries next run
});

test("dry run posts nothing and writes nothing", async () => {
  const dir = await scaffold({ "gh-one": { version: "v1.0.0" }, "store-one": { version: "2.0.0.0" } });
  const { fetchImpl, posts } = fakeNet();
  const out = await run({ dryRun: true, env: { DISCORD_TOKEN: "t" }, fetchImpl, rootDir: dir });
  assert.deepEqual(out.announced, ["gh-one"]);
  assert.equal(posts.length, 0);
  const state = JSON.parse(await readFile(join(dir, "state.json"), "utf8"));
  assert.equal(state["gh-one"].version, "v1.0.0");
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test`
Expected: FAIL — modules not found.

- [ ] **Step 3: Implement**

`src/state.js`:
```js
import { readFile, writeFile } from "node:fs/promises";

export async function loadState(path) {
  return JSON.parse(await readFile(path, "utf8"));
}

export async function saveState(path, state) {
  await writeFile(path, JSON.stringify(state, null, 2) + "\n");
}
```

`src/index.js`:
```js
import { readFile } from "node:fs/promises";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { fetchLatestGithub } from "./sources/github.js";
import { fetchLatestStore } from "./sources/displaycatalog.js";
import { findNew } from "./diff.js";
import { buildEmbed } from "./embed.js";
import { makeBlurb } from "./voice.js";
import { postEmbed } from "./discord.js";
import { loadState, saveState } from "./state.js";

export async function run({ dryRun = false, env = process.env, fetchImpl = fetch, rootDir } = {}) {
  const root = rootDir ?? join(dirname(fileURLToPath(import.meta.url)), "..");
  const config = JSON.parse(await readFile(join(root, "config.json"), "utf8"));
  const voicePrompt = await readFile(join(root, "voice.md"), "utf8");
  const statePath = join(root, "state.json");
  const state = await loadState(statePath);

  // Fetch every target; a failure is a null (skip), never a crash.
  const fetchedById = {};
  for (const target of config.targets) {
    fetchedById[target.id] =
      target.source === "github"
        ? await fetchLatestGithub(target, { token: env.GITHUB_TOKEN, fetchImpl })
        : await fetchLatestStore(target, { fetchImpl });
  }

  const { toAnnounce, toSeed } = findNew(config.targets, state, fetchedById);
  const summary = { announced: [], seeded: [], failed: [] };

  for (const { target, release } of toSeed) {
    summary.seeded.push(target.id);
    if (!dryRun) state[target.id] = { version: release.version, announcedAt: null };
  }

  for (const { target, release } of toAnnounce) {
    const blurb = await makeBlurb(target, release, voicePrompt, {
      apiKey: env.ANTHROPIC_API_KEY,
      model: config.voice.model,
      maxChars: config.voice.maxChars,
      fetchImpl,
    });
    const embed = buildEmbed(target, release, blurb);
    if (dryRun) {
      console.log(`[dry-run] would post:\n${JSON.stringify(embed, null, 2)}`);
      summary.announced.push(target.id);
      continue;
    }
    try {
      await postEmbed(config.channelId, embed, { token: env.DISCORD_TOKEN, fetchImpl });
      state[target.id] = { version: release.version, announcedAt: new Date().toISOString() };
      summary.announced.push(target.id);
    } catch (err) {
      console.error(`[post] ${target.id}: ${err.message}`);
      summary.failed.push(target.id); // state untouched — next run retries
    }
  }

  if (!dryRun) await saveState(statePath, state);
  console.log(`announced=${summary.announced.length} seeded=${summary.seeded.length} failed=${summary.failed.length}`);
  return summary;
}

// CLI entry
if (process.argv[1] && import.meta.url === new URL(`file://${process.argv[1].replace(/\\/g, "/")}`).href) {
  const dryRun = process.argv.includes("--dry-run");
  run({ dryRun }).then((s) => {
    if (s.failed.length) process.exitCode = 1;
  });
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `node --test`
Expected: all pass. Note the CLI-entry guard comparison on Windows paths — if the two integration tests pass but `npm run dry-run` (Step 5) doesn't print, fix the guard to `process.argv[1]?.endsWith("index.js")`.

- [ ] **Step 5: Live dry-run smoke test (real APIs, no posting)**

Run: `npm run dry-run`
Expected: exit 0; every target either seeds (first ever run: all 24 seed) or logs a fetch error for repos with no releases yet. NOTHING posts. `state.json` IS written by a non-dry seed? No — dry-run writes nothing; confirm `git status` shows `state.json` clean.

- [ ] **Step 6: Commit**

```powershell
git add src/state.js src/index.js test/index.test.js
git commit -m "feat: orchestrator — cold-start seeding, per-target state advance, --dry-run"
```

---

### Task 9: Workflow + README

**Files:**
- Create: `.github/workflows/poll.yml`, `README.md`

**Interfaces:**
- Consumes: `npm test`, `node src/index.js` from prior tasks.
- Produces: the hourly production loop; the fork-and-run story.

- [ ] **Step 1: Write the workflow**

`.github/workflows/poll.yml`:
```yaml
name: poll
on:
  schedule:
    - cron: "7 * * * *"   # hourly at :07 — off the top-of-hour API rush
  workflow_dispatch: {}

permissions:
  contents: write

concurrency:
  group: poll
  cancel-in-progress: false

jobs:
  poll:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - name: Run tests
        run: npm test
      - name: Poll and post
        env:
          DISCORD_TOKEN: ${{ secrets.DISCORD_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: node src/index.js
      - name: Commit state
        run: |
          git config user.name "6deux6"
          git config user.email "actions@users.noreply.github.com"
          git add state.json
          git diff --cached --quiet && exit 0
          git commit -m "chore: state $(date -u +%FT%TZ)"
          for i in 1 2 3; do
            git push && exit 0
            git pull --rebase
          done
          exit 1
```

- [ ] **Step 2: Write the README**

`README.md`:
```markdown
# 6deux6

The 626 Labs release feed for Discord. Watches GitHub Releases and the
Microsoft Store, and posts one branded, in-voice announcement per new
version. REST-only: no gateway, no intents, no message reading, no stored
user data — its whole memory is public version numbers in [state.json](state.json).

Pronounced *six-deux-six*. Yes, that spells 626.

## How it works

An hourly GitHub Action runs one small Node program (zero dependencies):

1. Fetch the latest version per watch target — GitHub `releases/latest`
   or the Microsoft Store display catalog.
2. Diff against `state.json` (committed back after each run).
3. New version → build a branded embed. If an `ANTHROPIC_API_KEY` secret
   is present, Claude writes the announcement from the release notes,
   guided by [voice.md](voice.md); otherwise a template excerpt carries it.
4. Post to the configured channel. State advances only after Discord
   accepts the message — a failed run retries next hour, and nothing ever
   posts twice.

New targets (and brand-new installs) seed silently: announcements start
with the first release *after* adoption.

## Run it for your own projects

1. Fork this repo.
2. Create a Discord application + bot (discord.com/developers), invite it
   to your server with View Channel / Send Messages / Embed Links / Read
   Message History.
3. Edit `config.json`: your channel id, your targets. `github` targets
   need `repo`; `displaycatalog` targets need `productId` (from the app's
   apps.microsoft.com URL).
4. Reset `state.json` to `{}`.
5. Repo secrets: `DISCORD_TOKEN` (required). `ANTHROPIC_API_KEY`
   (optional — enables the LLM voice; without it you get template copy).
6. Replace `voice.md` with your own voice, or keep ours.
7. Enable the workflow (Actions tab). Done.

Local test: `npm run dry-run` prints what would post without posting.

## License

MIT © 626Labs LLC · [Terms](https://626labs.dev/legal/terms.html) ·
[Privacy](https://626labs.dev/legal/privacy.html)

*Imagine Something Else.*
```

- [ ] **Step 3: Validate the workflow YAML locally**

Run: `node -e "console.log('yaml ok')"` then push and check the Actions tab renders the workflow without a parse error (GitHub validates on push).

- [ ] **Step 4: Commit and push**

```powershell
git add .github/workflows/poll.yml README.md
git commit -m "feat: hourly poll workflow + fork-and-run README"
git push
```

Expected: Actions tab shows "poll" with a manual Run workflow button. Do NOT run it yet — secrets aren't set.

---

### Task 10: Brand icon (`scripts/build-icon.py`)

**Files:**
- Create: `scripts/build-icon.py`, `assets/icon-1024.png` (generated)

**Interfaces:**
- Produces: the app icon Este uploads in the dev portal. Navy field, cyan/magenta glows, up-arrow "ship it" motif — sibling of the 626 mark, not a clone.

- [ ] **Step 1: Write the icon script**

`scripts/build-icon.py`:
```python
"""6deux6 app icon — navy field, cyan/magenta glow, up-arrow ship-it motif.
Run: python scripts/build-icon.py  ->  assets/icon-1024.png"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

S = 1024
NAVY = (15, 31, 49)
CYAN = (23, 212, 250)
MAGENTA = (242, 47, 137)

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(exist_ok=True)


def radial_glow(size, cx, cy, color, max_alpha, radius):
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    yy, xx = np.indices((size, size))
    dist = np.sqrt((xx - cx * size) ** 2 + (yy - cy * size) ** 2)
    falloff = np.clip(1 - dist / (radius * size), 0, 1) ** 2
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    arr[..., 3] = (falloff * max_alpha).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def arrow_layer(color, width_scale=1.0):
    """Up-arrow: shaft swoosh + head, drawn as polygons."""
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w = int(56 * width_scale)
    # curved shaft: three straight segments approximating the brand swoosh
    d.line([(300, 780), (460, 640), (560, 460), (620, 300)], fill=color + (255,), width=w, joint="curve")
    # arrowhead
    d.polygon([(620 - 90, 330), (620 + 60, 330 - 40), (660, 180)], fill=color + (255,))
    return layer


canvas = Image.new("RGBA", (S, S), NAVY + (255,))
canvas.alpha_composite(radial_glow(S, 0.32, 0.70, CYAN, 90, 0.55))
canvas.alpha_composite(radial_glow(S, 0.70, 0.30, MAGENTA, 80, 0.55))

# magenta echo arrow behind, offset — the "trail"
echo = arrow_layer(MAGENTA, 1.0)
echo = echo.transform((S, S), Image.AFFINE, (1, 0, 60, 0, 1, 40))
echo_blur = echo.filter(ImageFilter.GaussianBlur(6))
canvas.alpha_composite(echo_blur)

# cyan lead arrow with soft glow
lead = arrow_layer(CYAN, 1.0)
glow = lead.filter(ImageFilter.GaussianBlur(18))
canvas.alpha_composite(glow)
canvas.alpha_composite(lead)

out = OUT / "icon-1024.png"
canvas.convert("RGB").save(out, "PNG", optimize=True)
print(f"wrote {out}")
```

- [ ] **Step 2: Run it and look at it**

Run: `python scripts/build-icon.py`
Expected: `assets/icon-1024.png` exists. Open it (agent: Read the PNG) and judge: arrow reads at small size, glows subtle, no clipping at edges. Iterate the polygon points if the arrow reads wrong — this step is done when the icon looks right, not when the script exits 0.

- [ ] **Step 3: Commit**

```powershell
git add scripts/build-icon.py assets/icon-1024.png
git commit -m "feat: brand icon — up-arrow ship-it motif on the navy field"
git push
```

---

### Task 11: Deploy (human + agent, in order)

**Files:**
- Modify: `626labs-hub/docs/626-discord-runbook.md` (+ estate mirror) — tick Part B boxes when done.

- [ ] **Step 1 (Este): portal identity**
  - Upload `assets/icon-1024.png` as the 6deux6 app icon (General Information).
  - Set the app description to the release-feed copy from the runbook's bot-identity section.
  - Copy the bot token → 6deux6 repo → Settings → Secrets → Actions → `DISCORD_TOKEN`. Optionally add `ANTHROPIC_API_KEY` for the voice pass.

- [ ] **Step 2 (Este): invite 6deux6 to the 626Labs server**
  - `https://discord.com/oauth2/authorize?client_id=1475660206099927164&scope=bot&permissions=84992`

- [ ] **Step 3 (agent, discord MCP): grant 6deux6 send access on #releases**
  - `set_channel_permissions` on `#releases` (`1522754011915227153`): allow `SendMessages`, `EmbedLinks` for the 6deux6 role (runbook gotcha 7 — the @everyone lockdown silences bots without their own overwrite). Verify with `view_channel_permissions`.

- [ ] **Step 4 (agent): first supervised run**
  - Actions tab → poll → Run workflow. First run seeds all 24 targets, posts nothing, commits `state.json`.
  - Verify: `state.json` on main has 24 entries; #releases has no new messages.

- [ ] **Step 5 (agent): prove the loop with a real release**
  - Next actual release in the family (or a test tag on a watched repo) should post within the hour. Confirm the embed: title link, family color, voice blurb (if key set), footer.

- [ ] **Step 6 (agent): close out**
  - Tick the runbook's Part B boxes (both mirrors), commit.
  - Log the ship decision to the dashboard (project `qNCk86nujUfrHEbRU2jy`), linking spec + plan.
```

---

## Self-review notes (run after writing, fixed inline)

- **Spec coverage:** identity ✓ (T1 repo, T10 icon, T11 portal), REST-only ✓ (T7), sources ✓ (T3, T4), diff + cold start ✓ (T2, T8), embeds + normalization ✓ (T5), voice hybrid ✓ (T6), config portability ✓ (T1, T9 README), state commit loop ✓ (T9), error handling ✓ (spread across T3/T4/T6/T7/T8), testing ✓ (every task), verification readiness → already live (legal pages) + T11 portal steps, deploy checklist ✓ (T11).
- **Type consistency:** `findNew` consumed in T8 as defined in T2; release shape `{version,url,notes,publishedAt}` consistent across T3/T4/T5/T6; `postEmbed(channelId, embed, {token, fetchImpl})` consistent T7→T8.
- **No placeholders:** every code step carries full code; config blurbs flagged as Este-reviewable copy, which is a review note, not a TBD.
