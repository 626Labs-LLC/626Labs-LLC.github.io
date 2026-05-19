# RORORO editorial brief — source pack

> Built 2026-05-17 from three parallel subagent passes: app internals, origin/history, and positioning audit. Source material for the upcoming editorial article. All claims cite files; speculation is flagged. Open questions at the bottom are the ones only Este can answer.

---

## What RORORO is, in one paragraph

A native multi-launcher for Roblox on Windows and macOS. Users add alt accounts once via an embedded Roblox login (the password never touches the app process), then click "Launch As" to spawn multiple Roblox clients side by side, each signed into a different saved account. The mechanism is the documented **named-mutex defeat** trick: hold the Windows mutex `ROBLOX_singletonEvent` (or on Mac, run `sem_unlink` on `/RobloxPlayerUniq`) **before** Roblox launches, neutralizing Roblox's single-instance check. The official Roblox client is never modified, injected into, or touched — RORORO is the door, not the lockpick.

Sources: `ROROROblox/README.md:65-74,122-125`, `ROROROblox/PROVENANCE.txt:20-25`, `rororo.html:472-474,552-580`.

---

## The constellation (six public repos, one product)

| Repo | What it is | Stack | Distribution |
|---|---|---|---|
| `estevanhernandez-stack-ed/ROROROblox` | Windows core (the original Store push) | .NET 10 LTS · C# 14 · WPF + WPF-UI · WebView2 · DPAPI · Velopack | MS Store (`9NMJCS390KWB`) + GitHub Releases (`rororo-win-Setup.exe`, sideload MSIX) |
| `estevanhernandez-stack-ed/rororo-mac` | **Mac core — fully native, not Electron** | Swift · SwiftUI · WebKit · Security.framework Keychain · NSStatusItem · Darwin `sem_unlink` · Sparkle 2.x · XCTest (89 tests at v0.1 → ~363 by v0.7) · XcodeGen · Hardened Runtime + Apple-notarized parent app | Homebrew cask + notarized DMG (Sparkle EdDSA appcast on GH Pages, signing keypair lives in 1Password + GH Secrets only — losing it is a one-way break). **Mac App Store explicitly out of scope from the founding instruction** — listed as a non-goal in `docs/spec.md:20` and `docs/prd.md:26`. |
| `estevanhernandez-stack-ed/homebrew-rororo` | Mac distribution tap | Homebrew | `brew tap` |
| `estevanhernandez-stack-ed/rororo-ur-task` | The first plugin — per-window macro recorder | C# · gRPC over named pipe (`\\.\pipe\rororo-plugin-host`) | GitHub Releases · hotkeys `Ctrl+Shift+R/P/Esc` · v0.2.2 |
| `estevanhernandez-stack-ed/Ur-OCR` | Second plugin — screen-region OCR/colour triggers fire keybinds | C# · same plugin contract | GitHub Releases (created 2026-05-16, brand new) |
| (reference, not a 626 repo) | MultiBloxy by Zgoly — the technique origin | — | Cited in `PROVENANCE.txt`; reference binary shipped alongside RORORO with full credit |

Plugin contract is **out-of-process by design** — each plugin is a separate signed EXE talking gRPC over named pipe. Every capability is declared in a manifest, the user sees a **consent sheet** at install and can opt out per-capability, SHA-256 of the manifest is verified before unpack, and plugins crashing can't take RORORO down. The wall is structured this way because **macro/AFK-defeat features cannot ship inside the Microsoft Store binary** (Store policy 10.2.2 — "dynamic inclusion of code that changes described functionality"). Plugins live outside the Store-listed binary, which keeps RORORO Store-eligible while still letting the clan run automation.

---

## Timeline (the 11-day arc)

- **2026-05-03 23:31 CDT** — First commit on ROROROblox. Cart scope, PRD, spec, builder profile, two pre-commit hooks, MultiBloxy reference binary + PROVENANCE.txt already in place. The deciding-to-do-it conversation happened off-record.
- **2026-05-04** — ~30 commits in 21 clock hours. Full v1.1 lands: mutex, DPAPI vault, WebView2 capture + launcher, tray, MainWindow, Velopack, Squad Launch, themed chrome, MSIX signing, Partner Center graphics. v1.1.0.0 locked.
- **2026-05-06 morning** — Microsoft Partner Center rejects under **clause 10.1.1.1 Inaccurate Representation**: *"The product name contains the title of another piece of software or service."* Within hours, an 8-phase surgical rename plan distinguishes user-visible from internal-only strings. By afternoon `ROROROblox` → `RORORO` has shipped (commit `eb579ed`); namespaces, `%LOCALAPPDATA%` paths, repo URL, package Identity preserved because they're not user-visible.
- **2026-05-06 17:28** — Store listing flips to live. Free on the Microsoft Store.
- **2026-05-07** — Cycle 2: per-account FPS limiter via `GlobalBasicSettingsWriter`.
- **2026-05-07 → 2026-05-08** — Cycle 3: default-game widget + local rename. PRD audience rationale: long Roblox game names crowd the Pet Sim 99 clan's UI.
- **2026-05-09 11:54** — `docs(port-reference): add auto-keys bundle from rororo-mac`. **First in-tree evidence that the Mac sibling already exists and has shipped auto-keys.** Captured via vibe-taker as the canonical port reference.
- **2026-05-09 12:38** — Plugin-system v1.4 spec lands. The architectural pivot of RORORO's life (see *Pivots*).
- **2026-05-09 → 2026-05-10** — ~35 commits in 30 hours. gRPC contract, named-pipe transport, manifest + consent + capability gating, registry, SHA-verified installer, supervisor.
- **2026-05-10 19:38** — Scope correction (`07ba8c7`): "Clan Tracker" dropped because it didn't earn the plugin criterion. **`TinyTask` renamed to `RoRoRo Ur Task`** — "plays 'RoRoRo + Your Task' off TinyTask, ties the plugin to the parent product on first read."
- **2026-05-11 11:30** — v1.4.0.0 ships. Plugin host live on Windows.
- **2026-05-11 17:09** — Hub repo adds RORORO Mac card + RoRoRo Ur Task card.
- **2026-05-12 / 13** — v1.4.1.0, v1.4.2.0 polish.
- **2026-05-14** — Creator outreach strategy + Tier 1 outreach batch committed.
- **2026-05-16** — Ur-OCR repo created. Second plugin lands.

**11 days from first commit to launch. 190+ commits across the core repos.**

---

## The "ahas" — load-bearing for the editorial

### 1. The Mac sibling pre-existed Windows

The 2026-05-03 design spec §2 explicitly named macros as *"a Mac-only thing — lives in MaCro, the separate macOS product."* Six days later the Mac auto-keys cycler is imported as a port reference for Windows. The real ordering: Mac multi-launcher (already named `rororo-mac`) existed first → the **Microsoft Store push drove the Windows build** → the rename forced Windows to inherit the Mac product's stutter name. The "Windows is the original" framing on the hub product page is mildly misleading. Worth either correcting or owning explicitly in the editorial.

### 2. The wedge was packaging, not the technique

Quoted verbatim from the r/SideProject post-mortem in `docs/rororo-media-blitz-2026-05-06.md`:

> *"The mutex defeat is documented and old — Zgoly's MultiBloxy did it years ago. What was hard wasn't reimplementing the trick; it was wrapping it in something a non-developer can install, sign, and trust."*

This is the editorial thesis in one sentence. **The problem RORORO solves is trust, not multi-instancing.** Roblox Account Manager broke after Hyperion and upstream went quiet (sketchy forks remained); MultiBloxy itself was an unsigned tray-only binary that SmartScreen flagged; separate Windows user accounts were bulletproof but clunky. RORORO is the *clean, signed, recommendable* version.

### 3. The plugin system was forced by a Store-policy wall, not a feature wishlist

The clan (Pet Sim 99 farmers) was asking for the Mac auto-keys cycler on Windows. Microsoft Store policy 10.2.2 forbids exactly that kind of bundled automation. The plugin host is the architectural escape hatch — **keep the Store binary a clean multi-launcher, ship automation as separately-distributed sideload plugins** with gRPC + capability manifest + consent sheet + SHA-pinned install. Born inside one weekend (May 9–10) to honor both the Store policy and the clan's ask.

### 4. The rename-in-a-day, with surgical separation of user-visible vs. internal

Partner Center rejects v1.1.0.0 on a Wednesday morning. By lunchtime there's an 8-phase rename plan. By afternoon it's shipped. The surgical move: **change only what reviewers see** (Store listing name, in-app strings, README headings, marketing surfaces). **Preserve everything internal** (`626LabsLLC.RORORO` package Identity, `%LOCALAPPDATA%\ROROROblox\`, `ROROROblox-app-singleton` mutex, namespaces, repo URL). The compliance gate became the brand identity — three stutter-syllables of "Roblox," voxel-stack icon mirroring the wordmark.

### 5. Provenance ownership as a brand posture

`PROVENANCE.txt` is at the repo root, not buried. It credits Zgoly by name, lists the upstream release URL, ships the reference binary alongside (with SHA-256), dates the download, names what else was considered (RAM, Dashbloxx, `bloxstrap-multi-instance-integration`, separate Windows users), and explains why a clean reimplementation was needed. The Day +1 X tweet variant calls this *the* most-proud-of move:

> *"The thing I'm most proud of in RORORO isn't the WPF chrome or the Velopack update flow. It's the PROVENANCE.txt."*

The phrase **"reuse without erasure"** lands in the product page footer (`rororo.html:728`). It's a thesis-level idea — a 626 Labs *ethic* with thesis-level depth that hasn't been written up anywhere outside the trust block.

---

## Mac deep findings (added 2026-05-17, after local clone + source pass)

The remote-pass surface intuition ("Mac is simpler because Apple is more permissive") was wrong. The deeper read reframes the asymmetry as **a founding posture, not a platform fact**. Five findings worth folding into the article:

### A. The App Store opt-out predates the code — and the reason is audience-shaped, not principled

Quoted from ADR 0004 §Background line 17 (`rororo-mac/docs/decisions/0004-auto-keys-cycler.md`):

> *"This ADR locks the model and the surface area before any code is written. The feature is **explicitly App-Store-disqualifying** (ethically welded — capability + clear posture) per the founding instruction in `feedback_app_store_posture` memory; this is not a regression to ship."*

The founding memory itself: **"capability ambition + ethical clarity, App Store opt-out accepted."** ADR 0007 Decision 6 reaffirms it. `tools/release/exportOptions.plist:5` is commented `<!-- Apple Developer ID distribution outside the Mac App Store. -->`. **The Mac side never put its hand on the Apple-review gauntlet.**

**The Este reason underneath** (from him directly, 2026-05-17 conversation): *"With the Mac there wasn't really no chance of getting on the Apple Store, so we went ahead and just threw it in there. We figured people that play Roblox on Mac really need something and they're used to going to GitHub for it."* Two facts, both editorially load-bearing:

1. **The opt-out wasn't a principled stance dressed up as ethics, it was a pragmatic read of the gauntlet.** Apple was never going to approve an auto-keys-equipped multi-launcher; the ADR language ("ethically welded") reflects the *posture chosen given the constraint*, not a moral preference for opting out. Don't over-credit the principle.
2. **The Mac Roblox community is already a GitHub-going audience.** It's the underrated audience insight of the project. There is no consumer-grade Mac Roblox tooling distributed through Apple's stores — Nitrogen, Raptor-Manager, celestial-ui all ship via GitHub Releases or `curl | bash`. The user *habit* on Mac is "search GitHub, download the release, drag the .app." Shipping RORORO Mac via signed/notarized DMG + Sparkle + Homebrew tap meets the audience exactly where it already looks. None of the current marketing surfaces names this. **The article should.**

Windows reacted to MS Store policy 10.2.2 *after* the product existed; Mac never even drew the line, because the audience didn't expect Apple-store presence in the first place. The asymmetry isn't "Apple is more permissive" — it's "the Windows audience expects Microsoft Store presence (legitimacy signal), the Mac audience expects GitHub Releases presence (legitimacy signal). Each platform's RORORO ships through the channel that audience trusts."

The atlas entry for v0.5 (FFlag library, PR #2) is the on-record receipt — the runners-up include **"Plugin system w/ separate processes (decline — Windows MS-Store-dodge driver doesn't transfer to Mac)"** in `rororo-mac/.vibe-iterate/atlas.jsonl:1`. Plug-in architecture isn't on Mac's roadmap and won't be, because the constraint that forced it on Windows doesn't apply.

### B. Notarization vs the App Store — the architectural insight

The Mac repo's working model: **notarization gates malware; the App Store gates policy.** RORORO Mac ships the parent `.app` signed with a Developer ID cert + Apple-notarized + stapled, which clears Gatekeeper. The auto-keys macro engine lives *inside* that notarized binary because no policy reviewer reviews notarized-but-not-store-shipped apps. Windows had to *split* the binary (core + sideload plugin) to do the same trick. Mac is one binary because the gauntlet was never run.

The competitive landscape research (`rororo-mac/docs/_research-2026-05-12-distribution.md`) is the deeper read: Nitrogen ships ad-hoc-signed `codesign --force --deep --sign -` to thousands via `curl | bash`. RORORO Mac threads the needle *one step better* — notarized parent, ad-hoc re-sign only at the per-instance copy layer.

### C. Mac is *simpler* at auto-keys, *vastly more complex* at cookie isolation

The ADR chain **0009 → 0010** is the platform asymmetry made concrete. Four layers of compensating architecture, none of which exist on Windows:

1. **Per-instance bundle ID rewrite** — macOS routes cookie storage by `CFBundleIdentifier`, so each per-account `.app` copy must have a stable, unique bundle ID. ADR 0009 is the first correct *public* diagnosis of the `CFBundleIdentifier → HTTPStorages` collision; Nitrogen, Raptor-Manager, and celestial-ui all independently arrived at "rewrite the bundle ID" but never named the root cause.
2. **Ad-hoc `codesign --deep` re-sign** — the plist edit invalidates the cdhash, so each copy needs re-signing.
3. **Private `RORORO.keychain` prepended to the user's search list** — the fresh cdhash isn't in `login.keychain`'s ACL, so Roblox's first launch triggers a macOS password prompt every time. RORORO ships its own keychain with permissive ACL, pre-populated with the items Roblox queries.
4. **Per-launch keychain replant** — Roblox *deletes* the placeholder items during each launch flow. The fix replants them on every Launch As, beating Roblox to the next query.

**The "we used `log stream` to catch Roblox red-handed" moment in ADR 0010 lines 76-112** is the cleanest momentous-hurdle beat in the repo:

> *`10:05:11.077 RobloxPlayer: atomicfile created RORORO.keychain-db.sb-...-Msb2Ll`*
> *`10:05:11.082 RobloxPlayer: committed Msb2Ll to RORORO.keychain-db`*
> *`10:05:11.085 RobloxPlayer: committed QSUgzp to RORORO.keychain-db`*
> *File size drops 22548 → 20460 bytes — exactly one item removed.*

The whole arc (Plan v1 → PoC fails because direct-spawn skips LaunchServices → pivot to per-instance bundle rewrite → 24 hours later, re-sign creates cdhash/keychain ACL bug → ADR 0010 ships the replant fix) plays out in **5 days, 2026-05-11 → 2026-05-15**. Editorial framing: this is the *"fix the engine, not the symptom"* Swiss Ephemeris energy applied to launcher tooling.

### D. The auto-keys engine has unusually deliberate safety architecture

Not just "fire keystrokes at a window." From the source:

- **Serial focus-then-fire**, not concurrent broadcast — eliminates the `CGEventPostToPid` reliability spike. Walks one Roblox window at a time: focus → settle → fire → next. Trade-off explicitly named in ADR 0004: only one account active at any instant, but a 20-min AFK budget gives a 10-account cycle 2-min-per-window headroom.
- **Self-event tagging** — every CGEvent posted carries `kCGEventSourceUserData = 0x524F524F` (ASCII "RORO"). The engagement detector ignores its own keystrokes. Without this, the cycler would pause itself on every keystroke it fired.
- **Three pause states** with deliberately different auto-resume rules: `.userEngaged` resumes after 5s (a mouse twitch is a nudge), `.focusStolen` requires manual Play (focus theft is "where are we?"), `.userRequested` only resumes on user action.
- **Cursor-in-tracked-rect gating** — the user can play in one window while the cycler keeps the others alive. NSEvent's bottom-left vs AX's top-left origin flip is handled explicitly.
- **Cycle-budget validator** — refuses to start if estimated cycle time > 19 minutes. Roblox's AFK timer is ~20.
- **Kill-key chord-tolerance** (PR #5, 2026-05-15) — bare-key kill uses exact match, chord kill uses subset match. The user-reported bug "kill key sometimes doesn't work" turned out to be exact-equality rejecting the chord when a panicked finger brushed a stray Cmd.

ADR 0004 is explicit: **"explicitly App-Store-disqualifying (ethically welded)."** This isn't speculation about Apple — Este wrote it as a constraint.

### E. The kill-switch architecture (in case Roblox ever renames the semaphore)

`rororo-mac/tools/release/roblox-compat.json` is a **remote-overridable config** the in-app `RobloxCompatStore` fetches at boot from gh-pages. Sample shape: `{ "robloxSingletonSemaphoreName": "/RobloxPlayerUniq", "version": 1 }`. From `generate-appcast.sh:24-35`: *"For OUT-OF-BAND updates (no new tag), git-push the updated file directly to the gh-pages branch."* If Roblox renames `/RobloxPlayerUniq`, Este can patch within minutes — no app release, no Sparkle update, no Homebrew cask bump. The `SemaphoreBreakerTests.testCanonicalSemaphoreNameIsRobloxPlayerUniq` test exists to assert the magic string the entire product depends on; the comment acknowledges the test cannot defend against a Roblox rename but flags it as a "contract-checkpoint, not a behavior check."

### Provenance — Mac side credits *two* upstream sources, not one

`PROVENANCE.txt` lines 24-38: **Insadem's `multi-roblox-macos` (Go)** is the direct technique reference for `sem_unlink("/RobloxPlayerUniq")` + `cp -a` + `LSMultipleInstancesProhibited` flip. (Zgoly's MultiBloxy is credited at lines 14-22 as the sibling Windows technique — "not shipped with the Mac port.") Mac PROVENANCE also lists three sibling Mac implementations (Nitrogen / Raptor-Manager / celestial-ui) and names the *differentiator claims* — RORORO Mac is the only Swift-native entrant, the only one with the correct root-cause diagnosis of the cookie-isolation problem, and the only one shipping a Hardened Runtime + notarized parent app.

### Threat-model context the existing surfaces don't carry

`docs/security/threat-model.md` is STRIDE-shaped. The **primary threat actor is "Roblox cheat-vendor / mass distributor"** — i.e., the bad community member who would trojan a copy of RORORO and ship it as a phishing front. The threat model explicitly *de-scopes* "defending against the user attacking their own Mac" and "defending against nation-state adversaries." Editorial color: the security posture is shaped by what the multi-launcher community *actually has* in it, not by abstract OWASP rules.

---

## Current positioning (what already exists in market)

**Promises being made across all surfaces:**
- Free, MIT, open source
- Native on Windows + macOS (not Electron, not a runtime)
- One-click multi-instance via mutex/semaphore — no injection
- Saved-account vault with DPAPI/Keychain, machine-bound
- Password never reaches the app process
- Auto-update (Velopack + Sparkle, both legit)
- Plugin-extensible, capability-gated, consent at install
- No telemetry, no server
- Honest risk language — "low but nonzero ban risk, don't run on accounts you can't afford to lose"
- Disclaimer on every surface: not affiliated with Roblox Corporation; nominative use only

**Taglines already in market (verbatim):**
- "Run multiple Roblox clients. **Side by side, one machine.**" — hero
- "Run six. *Trust the window you're recording.* Own the provenance." — footer axiom
- "Reuse without erasure." — trust section + X thread
- "Owned, not hidden." — section eyebrow
- "The honest part." — trust H2
- "Two platforms, one product."
- "The multi-launcher you can recommend on camera." — creator outreach one-liner
- Site card meta: "Free · Windows + macOS · plugin-extensible"

**Voice discipline check:** Sentence case throughout. Builder-to-builder register. No banned vocabulary (no "empower / leverage / seamlessly / unlock / unleash") on any surface. No emoji in any marketing copy. **One trivial inconsistency:** `rororo.html:574` uses British "coloured" (rest of site is American English).

**One stale claim to fix before the article ships:** `docs/rororo-creator-outreach-2026-05-14.md:114-115` still describes the first plugin as "auto-keys, an AFK-defeat cycler." It's now `RoRoRo Ur Task` (per-window macro recorder). The Tier 1 batch flags this drift explicitly.

---

## The whitespace — what the editorial should add

Things every current surface omits:

1. **The Roblox lineage / Este origin story.** No surface answers *why a builder of plugin frameworks ended up shipping a Roblox tool*. The personal hook is editorial gold.
2. **What "Ur Task" feels like in practice.** Cards and lists, no walkthrough — no contrast with the "fire-blindly" macro tools it replaces.
3. **What the Mac sibling adds beyond parity.** The Mac side ships the auto-keys macro cycler natively — a Windows *plugin*. The architectural asymmetry (Apple has no equivalent of Store policy 10.2.2) is unexplained anywhere.
4. **The Microsoft Store gauntlet for a Roblox-trademark-touching tool.** Mentioned in passing in the r/SideProject post; no full treatment of *getting it approved on the next pass* with nominative-use language.
5. **The plugin contract as a design philosophy.** The product page describes *how* plugins work but never gives the *why* its full thesis — Store-eligibility argument is one sentence; the trust-and-blast-radius reasoning is the real interesting idea.
6. **Numbers / scale.** `anthropic_fellows.md:39` mentions 190 commits and end-to-end gRPC integration tests. No public-facing surface uses them. The bones-and-texture quantitative move is missing.
7. **What's NOT on the roadmap and why.** "Don't run this on accounts you can't afford to lose" is the limit-line; where else did Este *deliberately draw lines*?
8. **"Reuse without erasure" as a reusable ethic.** Used twice in market; never given thesis-length treatment. `content/stories/` has no RORORO story yet — itself a whitespace finding.

---

## Open questions only Este can answer

1. **The specific failure that triggered it.** Which incumbent broke when, for whom in the clan? RAM going quiet post-Hyperion is documented; the *personal* moment isn't.
2. **Mac vs Windows ordering — partially answered (2026-05-17).** Founding posture on Mac was App-Store-opt-out *before any code existed* (`feedback_app_store_posture` memory, referenced in ADR 0004). Mac auto-keys demonstrably shipped before Windows v1.4 plugin host. **Still open:** what was the literal first commit date on `rororo-mac` vs `ROROROblox` (May 3 was the Windows first commit), and how do you want to frame the order in public? "Mac was the real one and Windows was the Store push" is one defensible read; "they were sibling builds that shipped on different gauntlets" is another.
3. **Is the clan named publicly?** Will any quotes from clan members make it into the editorial? Outreach docs say *the* clan, implying a specific identifiable group.
4. **Naming process for "RORORO" post-rename.** Was there a brainstorm round that considered TripleStax / TripleR etc. and explicitly chose the stutter + voxel-icon tie?
5. **Active user counts / install counts.** Microsoft Store and Homebrew both report download numbers in their dashboards — neither is in any committed file. (For "bones" evidence in the article.)
6. **Whether Roblox has reacted to RORORO specifically.** No documented incident in the files read. Probably below the visibility tier where Roblox legal engages — but worth confirming.
7. **The Sanduhr / RORORO pair.** Recent media-blitz commits pair them; not researched here. Flag if the article touches Sanduhr too.
8. **Is RORORO done, or is this the start of a category bet?** Plugin backlog (`docs/plugins/PLUGIN_IDEAS.md`) suggests platform shape. Worth the writer naming this explicitly.

---

## Key file paths for citation

- Product page (all marketing copy): `C:\Users\estev\Projects\626labs-hub\rororo.html`
- Site card entry: `C:\Users\estev\Projects\626labs-hub\content\site.json:447-478`
- Media blitz launch copy: `C:\Users\estev\Projects\626labs-hub\docs\rororo-media-blitz-2026-05-06.md`
- Creator outreach strategy: `C:\Users\estev\Projects\626labs-hub\docs\rororo-creator-outreach-2026-05-14.md`
- Tier 1 outreach batch: `C:\Users\estev\Projects\626labs-hub\docs\rororo-tier1-outreach-batch-2026-05-14.md`
- Windows README (source of truth on what the app does): `C:\Users\estev\Projects\ROROROblox\README.md`
- Rename rationale (the 10.1.1.1 rejection + 8-phase fix): `C:\Users\estev\Projects\ROROROblox\docs\store\rename-plan.md`
- MultiBloxy provenance: `C:\Users\estev\Projects\ROROROblox\PROVENANCE.txt`
- Original v1 design spec: `C:\Users\estev\Projects\ROROROblox\docs\superpowers\specs\2026-05-03-rororoblox-design.md`
- Plugin-system v1.4 spec: `C:\Users\estev\Projects\ROROROblox\docs\superpowers\specs\2026-05-09-rororo-plugin-system-design.md`
- Plugin backlog: `C:\Users\estev\Projects\ROROROblox\docs\plugins\PLUGIN_IDEAS.md`
- Mac core (not local — via GitHub MCP): `estevanhernandez-stack-ed/rororo-mac`
- First plugin: `estevanhernandez-stack-ed/rororo-ur-task`
- Second plugin: `estevanhernandez-stack-ed/Ur-OCR`
