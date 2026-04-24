# Cloud Function — `logPlay`

Anonymous aggregate counter for Birthday Bacon Trail rounds. Receives a single fire-and-forget POST per completed round, atomically increments counters in Firestore. Zero visitor data on the wire.

## What it does

- Accepts `POST` with JSON body `{outcome: 'found' | 'out-of-films', filmCount: number}`.
- Validates shape (rejects anything else with a 400).
- Writes to `stats/play-counters` in the `guestbuzz-cineperks` Firestore project, using `FieldValue.increment(1)` on:
  - `totalPlayed`
  - `totalFound` *or* `totalOutOfFilms` depending on outcome
  - `wins{N}` (1–6) when outcome is `found`
- Returns `204 No Content` on success.

## Deploy

One-time setup (you'll do this once):

```sh
cd apps/widget-bacon-trail/functions

# First-time install — generates package-lock.json (no `npm ci` yet because
# the lockfile hasn't been created).
npm install

# firebase.json and .firebaserc in this directory already pin the project
# to guestbuzz-cineperks, so `firebase use` + `firebase login` are the
# only interactive steps.
firebase login          # if you haven't authenticated the CLI before
firebase deploy --only functions:logPlay
```

Subsequent deploys from the same directory can use `npm ci` normally once `package-lock.json` exists.

You'll get back a URL like:

```
https://us-central1-guestbuzz-cineperks.cloudfunctions.net/logPlay
```

Save that URL as a new GitHub Actions secret named **`VITE_STATS_ENDPOINT`** on this repo. The `build-widget.yml` workflow bakes it into the widget bundle alongside `VITE_TMDB_API_KEY` on the next push.

## Firestore security rules

The counter doc is written only by this function via the admin SDK (which bypasses rules). Client-side writes via the Firebase SDK should be disallowed. Add these rules to `firestore.rules` in the project (or merge into your existing rules):

```
match /stats/{statsDoc} {
  // Server-only writes via firebase-admin. Block all client mutation.
  allow write: if false;
  // Public reads are fine — the nightly GitHub Action reads this doc
  // via admin SDK anyway, but if any client ever needs it, readable.
  allow read: if true;
}
```

Deploy with `firebase deploy --only firestore:rules`.

## Source

See `index.js` in this directory. Single file. ~60 lines. No dependencies beyond `firebase-admin` and `firebase-functions`.

## Observability

Cloud Function logs go to Google Cloud Logging automatically. A 400-rate spike means someone (probably a bot) is sending malformed payloads — expected, nothing to act on unless volume spikes.
