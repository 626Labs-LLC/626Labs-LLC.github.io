# Store-app video plan — 2026-08-30

Follow-up to the RORORO launch video (PR #103). Same pipeline for every app:
copy `assets/video/rororo/src/`, swap the manifest, screenshots and frames,
render 9:16 / 4:5 / 1:1 / 16:9 from one manifest. Narration in the
ItsJustEste ElevenLabs voice at stability 0.35; digits spelled out for the
voice ("six-two-six"); QoL lists live on brand cards, not the voice track.

## The roster, surveyed against remotes 2026-08-30

| App | Store ID | Latest release | Screenshot state | Verdict |
|---|---|---|---|---|
| 626 Mod Launcher | 9N53V6RRJK95 | v0.19.0 (Aug 19) | `docs/store-assets/screenshots-0.19/` — 7 shots retaken against 0.19 the day it shipped, plus hero/poster/boxart | **CURRENT — first up** |
| SnapSnip (repo: SnipSnap) | 9PBX8F5TR0VR | no GitHub releases; main tip Aug 3 | `docs/screenshots/` — 9 shots from Jul 7 (library, dashboard, collections, profiles) | Usable; confirm shipped Store version with Este first |
| Sanduhr für Claude | 9NH3NK2RGCF5 | v3.3.0.0 (Jul 19, "the Fable release") | 7 theme + 6 window shots, all April (v2 era) | **STALE** — nothing shows the Fable meter or Claude Usage tab the release headlines |
| RBX15 Shirt & Pants | 9mv9g4xfj8s0 | v4.1.0 (Jul 21) | 7 app shots from Apr 20 | **STALE** — v4.1's pattern/gradient region fills (the money feature) aren't in any shot |
| Right Click PNG | 9PKKLK6R5WFL | v0.1.0 (Apr 22) | none — repo has logos only | **NO UI CAPTURES** — needs a bespoke context-menu capture session |

Ground-truth caveat (per the deployment-cadence memory): Store submissions
don't always appear as GitHub releases — SnapSnip has zero releases yet is
live on the Store. Confirm shipped versions with Este before stating any
version on screen.

## Per-app video shape

### 1. 626 Mod Launcher — ready now
- **Hook:** the reversibility promise: "disable a mod without deleting it — lose power mid-toggle and your library survives." Or the drag-a-zip beat: drop, it names the mod, finds the author, installs it where the loader expects.
- **Slides:** library home → game mods view → drag-zip install story (browse-nexus shot) → updates view → saves/snapshots → QoL card (atomic writes, holding folder, no ads/telemetry/account, signed sealed-core = no SmartScreen warning) → QR CTA.
- **Claims source:** v0.19 release notes + repo README. Nexus Mods official acceptance is a strong trust beat (GitHub build).
- **QR:** `626labs.dev/mod-launcher-games.html?ref=tiktok` — the page already exists and lists 149 supported games (626-game-manifest). Needs the same phone-nudge block rororo.html got.
- **Audience note:** gaming TikTok, same posting rhythm as RORORO. Rotate game hashtags (Skyrim, Elden Ring, Stardew) the way RORORO rotates PS99.

### 2. SnapSnip — after version confirmation
- **Hook:** the filename transformation: "Screenshot 2026-04-29 142301.png" → "Outlook — Q3 forecast — 2026-04-29 142301.png". Show the before/after as a still frame; it's the whole product in one image.
- **Slides:** hook card → dashboard → library (dark) → collections manager → redaction presets card (Strict/Balanced/Permissive — a claims-safe privacy beat: no network calls) → QR CTA.
- **Open question for Este:** what version is live on the Store, and does the local `feature/smart-rename` branch (ahead of main since Jul 8) change the pitch?

### 3. Sanduhr — blocked on recapture
- The v3.3 story is strong (Fable meter appearing automatically, Claude Usage dashboard, five glass themes) but no current capture shows it. Needs a capture session on the running app: main widget with Fable bar visible, Claude Usage tab, theme picker.
- Once captured: hook "know your burn rate before 11pm," themes cascade (the five glass themes are visually the best material), usage-calendar slide, privacy card (local-only), QR → `626labs.dev/sanduhr/`.
- Audience is Claude power users — this one belongs on X/LinkedIn at least as much as TikTok; cut the 16:9 first for those surfaces.

### 4. RBX15 — blocked on recapture
- v4.1's wrapping pattern/gradient fills are the demo: paint a camo fill and watch it tile continuously across seams. Static shots from April can't show it; ideally capture the fill being applied (2-3 stills of the same template progressing).
- Roblox-creator audience overlaps RORORO's — cross-promote in captions.
- QR → Store listing (no product page exists; consider whether it earns one first).

### 5. Right Click PNG — bespoke capture, smallest scope
- The product is a context menu; the video is: right-click a .webp → Convert to PNG → paste into Discord/Figma. Three staged captures (menu open, file appearing, paste landing) tell it.
- The "idea to Store in 24 hours, built with Vibe Cartographer" line is a second story for the builder audience — save it for a Field Note or X post, not the ad.
- QR → Store listing.

## Sequencing

1. **Mod Launcher now** — assets current, page exists, biggest audience. Includes adding the phone-nudge to mod-launcher-games.html.
2. **SnapSnip** once Este confirms the live Store version.
3. **Sanduhr and RBX15** ride on capture sessions (both are Este-machine work; the video assembly is same-day once shots exist).
4. **RTClickPng** whenever a capture half-hour appears; smallest production.

## The loop seam (standing pattern, added 2026-08-30)

TikTok loops every video, so the end and the start are one seam — design it as a
sentence that completes on replay. Every video ends "...Imagine something else."
and opens "Like the <product>." First play, the opener reads as an in-media-res
cold open (acceptable: odd-but-intriguing IS a hook); every loop after, the seam
says "Imagine something else. Like the 626 Mod Launcher." and the video becomes a
sentence that never ends. Mechanics: the opening line rides the first slide (9:16)
or the title card (hub cuts); no trailing silence on the final clip; the end
frame's field and composition should rhyme with the first frame's so the cut
lands soft. RORORO and Mod Launcher v1 predate this - retrofit each the next time
its audio is touched (one clip per cut).

## Standing guardrails (carry from the RORORO cut)

- Claims come from each repo's release notes/README — nothing on screen that isn't in the ledger.
- Trademark care: "for Roblox/Claude/Nexus," never "by." Independent-tool disclaimer on CTA frames where a third-party mark is leaned on (Roblox, Anthropic).
- Real UI only. No mockups.
- 15-45s target; feature tours may run to ~50s but every app also gets a 15s cut list in its script file.
- Sparing emoji allowed in TikTok captions (launch-post exception); site surfaces stay emoji-free.
