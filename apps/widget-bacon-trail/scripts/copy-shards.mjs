// Postbuild: mirror apps/widget-bacon-trail/data/birthdays/ into the build
// output so the widget's runtime fetch path `/widget-bacon-trail/data/birthdays/MM-DD.json`
// resolves on GitHub Pages. Vite's library build does not copy loose data by
// default; this script handles it.
//
// Runs from apps/widget-bacon-trail/ (package.json `build` script).

import { cp, mkdir, stat } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SRC = path.resolve(HERE, '..', 'data', 'birthdays');
const DEST = path.resolve(HERE, '..', '..', '..', 'widget-bacon-trail', 'data', 'birthdays');

async function main() {
  if (!existsSync(SRC)) {
    console.warn(`[copy-shards] source missing: ${SRC} — skipping (expected before first seed).`);
    return;
  }
  const srcStat = await stat(SRC);
  if (!srcStat.isDirectory()) {
    throw new Error(`[copy-shards] source is not a directory: ${SRC}`);
  }

  await mkdir(path.dirname(DEST), { recursive: true });
  await cp(SRC, DEST, { recursive: true });

  console.log(`[copy-shards] copied ${SRC} -> ${DEST}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
