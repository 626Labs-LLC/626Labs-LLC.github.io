// Postbuild: mirror apps/widget-bacon-trail/data/birthdays/ into the build
// output so the widget's runtime fetch path `/widget-bacon-trail/data/birthdays/MM-DD.json`
// resolves on GitHub Pages. Vite's library build does not copy loose data by
// default; this script handles it.
//
// Runs from apps/widget-bacon-trail/ (package.json `build` script).

import { cp, mkdir, stat, copyFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SRC_DATA = path.resolve(HERE, '..', 'data');
const DEST_DATA = path.resolve(HERE, '..', '..', '..', 'widget-bacon-trail', 'data');
const SRC_BIRTHDAYS = path.join(SRC_DATA, 'birthdays');
const DEST_BIRTHDAYS = path.join(DEST_DATA, 'birthdays');
const SRC_STATS = path.join(SRC_DATA, 'stats.json');
const DEST_STATS = path.join(DEST_DATA, 'stats.json');

async function main() {
  await mkdir(DEST_DATA, { recursive: true });

  // Birthday shards — the core data for the pick-actor screen.
  if (existsSync(SRC_BIRTHDAYS)) {
    const srcStat = await stat(SRC_BIRTHDAYS);
    if (srcStat.isDirectory()) {
      await cp(SRC_BIRTHDAYS, DEST_BIRTHDAYS, { recursive: true });
      console.log(`[copy-shards] copied ${SRC_BIRTHDAYS} -> ${DEST_BIRTHDAYS}`);
    }
  } else {
    console.warn(`[copy-shards] birthdays source missing: ${SRC_BIRTHDAYS} — skipping (expected before first seed).`);
  }

  // Lifetime-stats snapshot — used by StatsLine. Survives the Vite
  // emptyOutDir wipe by being re-copied from its source each build.
  if (existsSync(SRC_STATS)) {
    await copyFile(SRC_STATS, DEST_STATS);
    console.log(`[copy-shards] copied ${SRC_STATS} -> ${DEST_STATS}`);
  } else {
    console.warn(`[copy-shards] stats.json missing: ${SRC_STATS} — skipping (expected before first shard-refresh run).`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
