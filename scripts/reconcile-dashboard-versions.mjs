/**
 * version-truth reconcile — nightly dashboard version corrector.
 *
 * For every 626Labs dashboard project with a linked GitHub repo, compare the
 * stored `version` against the latest SHIPPED release (newest non-draft,
 * non-prerelease by publish date) and correct drift via the MCP REST API.
 * Prereleases are never recorded. Repos with zero releases are skipped with a
 * note — a bare tag isn't "shipped" (keystone: latest_tag vs version splits
 * take judgment, so the bot stays out of them).
 *
 * Auth: MCP_VERSION_TRUTH_KEY — a scoped agent key (version-truth-bot,
 * allowedTools: [manage_projects]) stored in Actions secrets. GITHUB_TOKEN
 * optional (rate limit headroom on public reads).
 *
 * DRY_RUN=1 reports drift without writing.
 * Safety valve: more than MAX_CORRECTIONS drifts in one run means something
 * systemic (API change, mass rename) — report and fail instead of writing.
 */
import { appendFileSync } from 'node:fs';

const MCP_BASE = 'https://us-central1-project-626labs.cloudfunctions.net/mcp';
const KEY = process.env.MCP_VERSION_TRUTH_KEY;
const GH_TOKEN = process.env.GITHUB_TOKEN || process.env.GH_TOKEN || '';
const DRY_RUN = process.env.DRY_RUN === '1' || process.env.DRY_RUN === 'true';
const MAX_CORRECTIONS = 8;

if (!KEY) {
  console.error('MCP_VERSION_TRUTH_KEY missing — refusing to run.');
  process.exit(1);
}

async function mcp(tool, body) {
  const res = await fetch(`${MCP_BASE}/api/${tool}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${KEY}`,
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`${tool} ${body.action}: HTTP ${res.status} ${await res.text().then((t) => t.slice(0, 200))}`);
  }
  const json = await res.json();
  // REST wraps the MCP handler result: { success, agent, tool, result }.
  // The handler's payload is result.content[0].text — usually JSON, sometimes
  // a plain confirmation string. Tolerate both.
  const text = json?.result?.content?.[0]?.text;
  if (typeof text !== 'string') return json;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

async function gh(path) {
  const res = await fetch(`https://api.github.com${path}`, {
    headers: {
      Accept: 'application/vnd.github+json',
      'User-Agent': '626labs-version-truth-bot',
      ...(GH_TOKEN ? { Authorization: `Bearer ${GH_TOKEN}` } : {}),
    },
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`GitHub ${path}: HTTP ${res.status}`);
  return res.json();
}

// "v1.9.0.0", "vibe-sec-v1.2.3", "3.1.0" → "1.9.0.0" / "1.2.3" / "3.1.0"
function numericVersion(s) {
  const m = String(s ?? '').match(/(\d+\.\d+(?:\.\d+){0,2})/);
  return m ? m[1] : null;
}

const projects = await mcp('manage_projects', { action: 'list' });
if (!Array.isArray(projects)) {
  console.error('manage_projects list did not return an array — API shape changed?');
  console.error(JSON.stringify(projects).slice(0, 300));
  process.exit(1);
}

const linked = projects.filter(
  (p) => p?.githubRepo?.fullName && p.status !== 'Archived'
);
console.log(`${projects.length} projects, ${linked.length} with linked repos`);

const corrections = [];
const skips = [];

for (const p of linked) {
  const full = p.githubRepo.fullName.replace(/\.git$/i, '');
  let releases;
  try {
    releases = await gh(`/repos/${full}/releases?per_page=30`);
  } catch (err) {
    skips.push(`${p.name}: ${err.message}`);
    continue;
  }
  if (!releases) {
    skips.push(`${p.name}: repo ${full} not found (rename? private?)`);
    continue;
  }
  const shipped = releases
    .filter((r) => !r.draft && !r.prerelease)
    .sort((a, b) => new Date(b.published_at) - new Date(a.published_at))[0];
  if (!shipped) {
    skips.push(`${p.name}: no shipped (non-prerelease) releases — left alone`);
    continue;
  }

  const liveNum = numericVersion(shipped.tag_name);
  const storedNum = numericVersion(p.version);
  if (!liveNum) {
    skips.push(`${p.name}: tag ${shipped.tag_name} has no parseable version`);
    continue;
  }
  if (liveNum === storedNum) continue;

  corrections.push({
    projectId: p.id,
    name: p.name,
    stored: p.version ?? '(unset)',
    live: `v${liveNum}`,
    tag: shipped.tag_name,
  });
}

const summary = [];
if (corrections.length === 0) {
  summary.push(`version-truth: no drift across ${linked.length} linked projects.`);
} else if (corrections.length > MAX_CORRECTIONS) {
  summary.push(
    `version-truth: REFUSING to write — ${corrections.length} drifts (> ${MAX_CORRECTIONS}) looks systemic. Review manually:`
  );
  for (const c of corrections) summary.push(`  ${c.name}: ${c.stored} -> ${c.live} (${c.tag})`);
  console.log(summary.join('\n'));
  writeStepSummary(summary);
  process.exit(1);
} else {
  for (const c of corrections) {
    if (DRY_RUN) {
      summary.push(`DRY: ${c.name}: ${c.stored} -> ${c.live} (tag ${c.tag})`);
      continue;
    }
    await mcp('manage_projects', { action: 'update', projectId: c.projectId, version: c.live });
    summary.push(`corrected ${c.name}: ${c.stored} -> ${c.live} (tag ${c.tag})`);
  }
  summary.unshift(
    `version-truth: ${DRY_RUN ? 'would correct' : 'corrected'} ${corrections.length} of ${linked.length} linked projects.`
  );
}
for (const s of skips) summary.push(`skip: ${s}`);

console.log(summary.join('\n'));
writeStepSummary(summary);

function writeStepSummary(lines) {
  if (process.env.GITHUB_STEP_SUMMARY) {
    appendFileSync(
      process.env.GITHUB_STEP_SUMMARY,
      ['### version-truth reconcile', '', '```', ...lines, '```', ''].join('\n')
    );
  }
}
