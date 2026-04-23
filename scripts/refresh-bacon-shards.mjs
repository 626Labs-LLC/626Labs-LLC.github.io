#!/usr/bin/env node
// Refresh Birthday Bacon Trail shard files from the QuizShow Firestore
// actorDatabase collection. Runs nightly via .github/workflows/refresh-bacon-shards.yml.
//
// Writes 366 per-day JSON files to two locations so both dev and prod
// resolve the same URL:
//   apps/widget-bacon-trail/data/birthdays/MM-DD.json  (source-of-truth, used by dev server)
//   widget-bacon-trail/data/birthdays/MM-DD.json       (served by GitHub Pages at /widget-bacon-trail/...)
//
// No `generatedAt` field — freshness is tracked via git log of the data
// directory (per docs/spec.md > Data flow — build time).
//
// Auth: reads firebase-admin default credentials from
// GOOGLE_APPLICATION_CREDENTIALS env (set by the workflow to a service
// account JSON file written from the FIREBASE_SA_JSON secret).

import { initializeApp, applicationDefault } from 'firebase-admin/app';
import { getFirestore } from 'firebase-admin/firestore';
import { writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(HERE, '..');
const SRC_DIR = path.join(REPO_ROOT, 'apps', 'widget-bacon-trail', 'data', 'birthdays');
const OUT_DIR = path.join(REPO_ROOT, 'widget-bacon-trail', 'data', 'birthdays');

const COLLECTION = 'actorDatabase';

function fmtDateKey(month, day) {
  return `${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

// Build the full list of 366 MM-DD keys so any day with zero birthdays still
// emits an empty shard rather than returning 404 at runtime.
function allDayKeys() {
  const keys = [];
  const daysInMonth = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]; // leap Feb
  for (let m = 1; m <= 12; m++) {
    for (let d = 1; d <= daysInMonth[m - 1]; d++) {
      keys.push(fmtDateKey(m, d));
    }
  }
  return keys;
}

async function main() {
  initializeApp({ credential: applicationDefault() });
  const db = getFirestore();

  console.log(`[refresh-bacon-shards] reading ${COLLECTION} …`);
  const snap = await db.collection(COLLECTION).get();
  console.log(`[refresh-bacon-shards] fetched ${snap.size} actor docs`);

  // Group by birthDateKey
  const byKey = new Map();
  for (const doc of snap.docs) {
    const data = doc.data();
    const bday = data.birthDateKey;
    if (!bday || typeof bday !== 'string') continue;
    const actor = {
      id: Number(data.id) || Number(doc.id),
      name: data.name ?? '',
      profilePath: data.profilePath ?? null,
      birthday: data.birthday ?? null,
      popularity: typeof data.popularity === 'number' ? data.popularity : undefined,
      baconNumber: typeof data.baconNumber === 'number' ? data.baconNumber : undefined,
    };
    if (!byKey.has(bday)) byKey.set(bday, []);
    byKey.get(bday).push(actor);
  }

  // Sort each day's actors: known bacon-number first (ascending), then by
  // popularity desc. Matches the existing actorService.ts preference.
  for (const actors of byKey.values()) {
    actors.sort((a, b) => {
      const aKnown = typeof a.baconNumber === 'number' && a.baconNumber <= 6;
      const bKnown = typeof b.baconNumber === 'number' && b.baconNumber <= 6;
      if (aKnown !== bKnown) return aKnown ? -1 : 1;
      return (b.popularity ?? 0) - (a.popularity ?? 0);
    });
  }

  await mkdir(SRC_DIR, { recursive: true });
  await mkdir(OUT_DIR, { recursive: true });

  let written = 0;
  for (const key of allDayKeys()) {
    const actors = byKey.get(key) ?? [];
    const payload = { date: key, actors };
    // Pretty-print with 2-space indent so diffs are readable. No trailing
    // newline on the JSON object itself; one newline at EOF.
    const body = `${JSON.stringify(payload, null, 2)}\n`;
    await writeFile(path.join(SRC_DIR, `${key}.json`), body, 'utf8');
    await writeFile(path.join(OUT_DIR, `${key}.json`), body, 'utf8');
    written++;
  }

  console.log(`[refresh-bacon-shards] wrote ${written} shards × 2 locations`);
  console.log(`[refresh-bacon-shards] src: ${SRC_DIR}`);
  console.log(`[refresh-bacon-shards] out: ${OUT_DIR}`);
}

main().catch((err) => {
  console.error('[refresh-bacon-shards] FAILED:', err);
  process.exit(1);
});
