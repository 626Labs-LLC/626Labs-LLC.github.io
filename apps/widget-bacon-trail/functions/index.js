// Birthday Bacon Trail — anonymous play-counter beacon.
//
// Accepts a single fire-and-forget POST per completed round and atomically
// increments counters in Firestore at `stats/play-counters`. Zero visitor
// data handled — request body is {outcome, filmCount} only.
//
// Deploy: `firebase deploy --only functions:logPlay` (see README.md).

import { onRequest } from 'firebase-functions/v2/https';
import { initializeApp } from 'firebase-admin/app';
import { getFirestore, FieldValue } from 'firebase-admin/firestore';

initializeApp();

const db = getFirestore();
const STATS_DOC = 'stats/play-counters';

// CORS: allow any origin. Widget may embed on multiple sites eventually, and
// no state-changing writes accept credentials. OPTIONS preflight is handled
// inline to keep the function self-contained.
const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Max-Age': '86400',
};

export const logPlay = onRequest({ cors: false, region: 'us-central1' }, async (req, res) => {
  // Preflight
  if (req.method === 'OPTIONS') {
    Object.entries(CORS_HEADERS).forEach(([k, v]) => res.setHeader(k, v));
    res.status(204).end();
    return;
  }

  Object.entries(CORS_HEADERS).forEach(([k, v]) => res.setHeader(k, v));

  if (req.method !== 'POST') {
    res.status(405).send('Method not allowed');
    return;
  }

  const body = req.body || {};
  const outcome = body.outcome;
  const filmCount = Number(body.filmCount);

  // Strict validation — any extra fields or malformed values get a 400.
  // Keeps the payload anonymous; there's no shape we accept that could
  // carry a visitor identifier.
  if (outcome !== 'found' && outcome !== 'out-of-films') {
    res.status(400).send('invalid outcome');
    return;
  }
  if (!Number.isInteger(filmCount) || filmCount < 1 || filmCount > 6) {
    res.status(400).send('invalid filmCount');
    return;
  }

  const updates = {
    totalPlayed: FieldValue.increment(1),
  };
  if (outcome === 'found') {
    updates.totalFound = FieldValue.increment(1);
    updates[`wins${filmCount}`] = FieldValue.increment(1);
  } else {
    updates.totalOutOfFilms = FieldValue.increment(1);
  }

  try {
    await db.doc(STATS_DOC).set(updates, { merge: true });
    res.status(204).end();
  } catch (err) {
    console.error('[logPlay] firestore write failed', err);
    res.status(500).send('write failed');
  }
});
