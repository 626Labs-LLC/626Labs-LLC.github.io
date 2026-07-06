#!/usr/bin/env node
/**
 * refresh-rororo-plugins.mjs — live data for the RoRoRo web plugin marketplace.
 *
 * The RoRoRo app's in-app marketplace reads plugins-catalog.json off the main
 * repo's latest release; this job reads the SAME catalog so the web view can
 * never disagree with the app about what exists. It then enriches every entry
 * with live release truth from each plugin's own repo — latest shipped version,
 * release date, lifetime plugin.zip installs — so the page stays correct even
 * when the hand-maintained catalog lags a release (it warns when that happens).
 *
 * Writes data/rororo-plugins.json; rororo-plugins.html and the plugins section
 * on rororo.html render from it client-side. Runs daily in CI
 * (refresh-rororo-plugins.yml) with the implicit GITHUB_TOKEN; all data is
 * public so it works unauthenticated locally too (~5 API calls).
 */
import { writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';

const CATALOG_URL =
  'https://github.com/estevanhernandez-stack-ed/ROROROblox/releases/latest/download/plugins-catalog.json';
const HOST_REPO = 'estevanhernandez-stack-ed/ROROROblox';
const HOST_STORE_URL = 'https://apps.microsoft.com/detail/9NMJCS390KWB';
const OUT = 'data/rororo-plugins.json';

const TOKEN = process.env.GITHUB_TOKEN || process.env.GH_TOKEN || '';
const apiHeaders = {
  'User-Agent': '626labs-hub-rororo-marketplace',
  Accept: 'application/vnd.github+json',
  ...(TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {}),
};

const bareVersion = (tag) => String(tag).replace(/^v/i, '');

function slugFromInstallUrl(installUrl) {
  // https://github.com/<owner>/<repo>/releases/latest/download/ -> owner/repo
  const m = installUrl.match(/github\.com\/([^/]+\/[^/]+)\/releases\//i);
  if (!m) throw new Error(`unparseable installUrl: ${installUrl}`);
  return m[1];
}

async function api(pathname) {
  const res = await fetch(`https://api.github.com${pathname}`, { headers: apiHeaders });
  if (!res.ok) throw new Error(`GET ${pathname} -> ${res.status}`);
  return res.json();
}

async function main() {
  const res = await fetch(CATALOG_URL, {
    headers: { 'User-Agent': apiHeaders['User-Agent'] },
  });
  if (!res.ok) throw new Error(`catalog fetch -> ${res.status}`);
  const catalog = await res.json();
  if (!Array.isArray(catalog) || catalog.length === 0) {
    throw new Error('catalog empty or malformed — refusing to write');
  }

  const plugins = [];
  for (const entry of catalog) {
    const slug = slugFromInstallUrl(entry.installUrl);
    const releases = await api(`/repos/${slug}/releases?per_page=100`);
    const shipped = releases.filter((r) => !r.draft && !r.prerelease);
    const latest = shipped[0] ?? null;
    const installs = releases
      .filter((r) => !r.draft)
      .flatMap((r) => r.assets ?? [])
      .filter((a) => a.name === 'plugin.zip')
      .reduce((sum, a) => sum + a.download_count, 0);

    const liveVersion = latest ? bareVersion(latest.tag_name) : entry.latestVersion;
    if (liveVersion !== entry.latestVersion) {
      console.warn(
        `::warning::catalog drift on ${entry.id}: catalog says ${entry.latestVersion}, ` +
        `latest shipped release is ${liveVersion} — bump docs/store/plugins-catalog.json in ROROROblox`,
      );
    }

    plugins.push({
      id: entry.id,
      name: entry.name,
      description: entry.description,
      publisher: entry.publisher,
      version: liveVersion,
      releasedAt: latest ? (latest.published_at || '').slice(0, 10) : null,
      ...(entry.minHostVersion ? { minHostVersion: entry.minHostVersion } : {}),
      installs,
      repoUrl: `https://github.com/${slug}`,
      installUrl: entry.installUrl,
      zipUrl: `${entry.installUrl}plugin.zip`,
    });
    console.log(`${entry.id}: v${liveVersion} (${latest?.published_at?.slice(0, 10) ?? 'n/a'}), ${installs} installs`);
  }
  plugins.sort((a, b) => a.name.localeCompare(b.name));

  const hostLatest = await api(`/repos/${HOST_REPO}/releases/latest`);
  const setup = (hostLatest.assets ?? []).find((a) => a.name === 'RORORO-win-Setup.exe');
  const host = {
    version: bareVersion(hostLatest.tag_name),
    releasedAt: (hostLatest.published_at || '').slice(0, 10),
    storeUrl: HOST_STORE_URL,
    setupUrl:
      setup?.browser_download_url ??
      `https://github.com/${HOST_REPO}/releases/latest`,
    releasesUrl: `https://github.com/${HOST_REPO}/releases`,
  };

  await mkdir(path.dirname(OUT), { recursive: true });
  await writeFile(
    OUT,
    JSON.stringify(
      {
        $comment:
          'RoRoRo web marketplace data. Catalog identity comes from the same ' +
          'plugins-catalog.json the app reads; version/date/installs come from ' +
          'each plugin repo’s live releases.',
        host,
        plugins,
      },
      null,
      2,
    ) + '\n',
  );
  console.log(`wrote ${plugins.length} plugins + host v${host.version} -> ${OUT}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
