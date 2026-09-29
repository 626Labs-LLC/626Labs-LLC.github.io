/**
 * asset-kind.mjs — what a release asset's download_count actually counts.
 *
 * GitHub's counter is per asset, and not every asset is something a person
 * downloads. Apps that self-update or check a manifest fetch small release
 * assets on every run, so a repo's lifetime total can be dominated by installed
 * copies polling, not by anyone getting the app. Measured on ROROROblox
 * 2026-09-29: ~50,300 of ~50,800 downloads were config polling, 383 were
 * installers.
 *
 *   installer : a person got the app or a plugin (exe, msi, msix, zip, ...)
 *   update    : Squirrel/Velopack delta or full packages an installed copy pulls
 *   polling   : manifests, compat/known-issue lists, catalogs, signatures
 *   other     : anything unrecognised (certs, checksums, notes)
 */

const POLLING = [
  /^known-issues\.json(\.sig)?$/i,
  /^roblox-compat\.json(\.sig)?$/i,
  /^plugins-catalog\.json(\.sig)?$/i,
  /^releases\.[a-z0-9.-]+\.json$/i, // releases.win.json and friends
  /^assets\.[a-z0-9.-]+\.json$/i,
  /^RELEASES$/,
  /\.sig$/i,
];
const UPDATE = [/\.nupkg$/i];
const INSTALLER = [/\.(exe|msi|msix|msixbundle|appx|appxbundle|zip|dmg|pkg|deb|rpm|appimage|gz)$/i];

export const KINDS = ['installer', 'update', 'polling', 'other'];

export function assetKind(name) {
  if (POLLING.some((re) => re.test(name))) return 'polling';
  if (UPDATE.some((re) => re.test(name))) return 'update';
  if (INSTALLER.some((re) => re.test(name))) return 'installer';
  return 'other';
}

/** Sum an {assetName: count} map into {installer, update, polling, other}. */
export function bucketAssets(assets) {
  const out = { installer: 0, update: 0, polling: 0, other: 0 };
  for (const [name, n] of Object.entries(assets)) out[assetKind(name)] += n;
  return out;
}
