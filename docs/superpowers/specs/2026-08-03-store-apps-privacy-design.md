# Store-apps privacy coverage — approved design

**Date:** 2026-08-03
**Status:** Approved design, pre-implementation
**Scope:** privacy.html becomes the canonical privacy policy for the six Microsoft Store apps — one anchored subsection per app, every claim verified against the app's actual code before it ships.

## Decision (brainstormed 2026-08-03)

**Site-canonical, per-app anchors.** privacy.html gains a "Desktop & Microsoft Store
apps" section; each app gets an anchored subsection whose URL becomes that app's
privacy-policy link in Partner Center. Repo PRIVACY.md files (where they exist)
become pointer-plus-summary to the site. Rejected: repo-canonical files (six
surfaces to keep true, raw GitHub URLs in listings) and six standalone pages
(sitemap/GSC noise, drift surface).

## The section

- New **section 05 — "Desktop & Microsoft Store apps"** inserted after the
  current 04 (Claude Code plugins); current 05-09 renumber to 06-10. privacy.html
  is a hand-authored static page — direct edits, no zones.
- Opens with the shared posture paragraph: local-first, no accounts, no
  advertising, no telemetry except where a subsection says otherwise; uninstall
  removes local data except where noted.
- Six anchored subsections, ids `privacy-rororo`, `privacy-sanduhr`,
  `privacy-mod-launcher`, `privacy-rbx15`, `privacy-snapsnip`,
  `privacy-rtclickpng`. Each answers the same five questions in the same order:
  1. What is collected
  2. Where data lives (exact mechanism: DPAPI vault, Windows Credential Manager
     service name, local files)
  3. What touches the network (every endpoint, when, and under what setting)
  4. Third parties involved (and whose policy governs that leg)
  5. Removal (what uninstall deletes; what survives and how to remove it)

## Known per-app disclosure facts (verified sources; the accuracy gate re-verifies all)

- **RoRoRo:** DPAPI-encrypted account vault tied to the Windows user; login via
  embedded WebView2 on Roblox's own page (password never seen); Roblox-side calls
  during launch; Velopack auto-update (an update check — must be disclosed as a
  network call); signed roblox-compat feed fetch; no telemetry.
- **Sanduhr:** credentials only in Windows Credential Manager (service
  com.626labs.sanduhr), wiped on uninstall; reads claude.ai with the user's own
  session; reads local Claude Code session logs; 30-day local history + CSV
  export; no server, no telemetry.
- **626 Mod Launcher — three network paths, each disclosed separately:**
  1. Game manifest: DIRECT fetch from raw.githubusercontent.com
     (626-game-manifest), signature-verified (.sig), gated on the "auto-update
     definitions" setting, 24h debounce, ships dark until go-live. User IP goes
     to GitHub, not 626 Labs.
  2. CurseForge metadata: via the 626-OWNED proxy
     `626-mod-metadata-proxy.626labs.workers.dev` (Cloudflare Worker holding the
     CurseForge key server-side). The policy states what the endpoint sees
     (request metadata/IP per Cloudflare handling), what 626 Labs logs, and its
     purpose (key custody). **Verification requirement:** inspect the Worker's
     source for logging before the wording ships; the published claim states
     exactly what the code does (default: Workers log nothing unless enabled).
  3. Nexus (GitHub build): OAuth direct to Nexus Mods; Nexus's policy governs
     that leg.
  Plus: local mod files moved (never deleted) to the holding area; no telemetry,
  no account.
- **RBX15:** local editor, no network claims expected — verify.
- **SnapSnip:** on-device redaction; window titles never leave the device;
  telemetry is rule counts, never content — the ONE app with declared telemetry;
  the subsection states the exact payload and destination after verification.
- **RTClickPng:** offline by design — no network calls of any kind, no update
  checks; converted files written beside originals; verify nothing changed.

## The accuracy gate (hard requirement)

Before any subsection ships, a verification agent reads that app's repo (all six
local clones are synced) hunting specifically for: owned endpoints (workers.dev,
626labs.dev, any API base), update checks (Velopack et al.), crash reporting,
analytics SDKs, and any network call the marketing copy doesn't mention. The
policy text is written FROM the verification findings, never from product copy.
SnapSnip has no known public repo — its subsection is drafted from its declared
Store description and flagged in the PR for Este's line-by-line confirmation
(founder is the only truth source).

## Ripples

- Effective-date line and "Changes to this policy" section update.
- RTClickPng and 626-mod-launcher repo PRIVACY.md files become pointer-plus-
  summary linking their site anchors (committed in those repos; conventional
  commits + trailer).
- No sitemap change (same URL); no GSC action.
- Ship: branch + PR, held for Este (legal-adjacent surface, line-by-line review).
- **Este's post-merge checklist (in the ship report):** update six Partner Center
  listings' privacy-policy URLs to
  `https://626labs.dev/privacy.html#privacy-<app>`.

## Out of scope

- The website/plugins sections of privacy.html (untouched except renumbering).
- Terms of service, EULAs, GDPR/CCPA formal machinery (the policy stays plain-
  language; revisit if a lawyer ever joins the party).
- Worker code changes (disclosure only; if verification finds surprise logging,
  that's a finding for Este, not a silent fix).

## Inputs needed

- Este's line-by-line review of all six subsections in the PR (hard gate).
- SnapSnip ground truth if the verification can't reach its source.
