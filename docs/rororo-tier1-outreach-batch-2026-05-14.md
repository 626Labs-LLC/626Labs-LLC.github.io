# RORORO — Tier 1 creator outreach batch (2026-05-14)

Execution artifact for [`rororo-creator-outreach-2026-05-14.md`](rororo-creator-outreach-2026-05-14.md).
That doc is the strategy + templates. This is the first batch of personalized,
paste-ready sends — all five Tier 1 names — plus a fresh research snapshot and a
new angle the strategy doc doesn't have yet: **plugin co-creation**.

Trust rails carry forward unchanged: independent third-party tool, low-but-nonzero
ban risk stated plainly, provenance credited to Zgoly's MultiBloxy, never "alt
accounts," never pitched for cheating.

---

## Research snapshot — what's actually shipped (verified 2026-05-14)

Pulled from the RORORO repo, release notes, and `content/site.json`. This corrects
a stale premise in the strategy doc — see the flag at the bottom.

- **RORORO v1.4.1.0** is the latest published Windows release (2026-05-12).
  v1.4.0.0 (2026-05-11) shipped the **plugin system**: a per-user named-pipe gRPC
  host, a consent sheet that itemizes every capability a plugin requests, and
  SHA-256-pinned installs from a GitHub release URL. Plugins are separate signed
  EXEs in their own process — a plugin crash can't take RORORO down.
- **RoRoRo Ur Task is live.** First-party plugin, published as `rororo-ur-task`
  v0.2.0 (2026-05-13). Per-window-aware macro recorder — records bind to a Roblox
  user-id, and playback *refuses to fire keys or clicks into any other alt's
  window*. Alt-tab away mid-playback and it stops cold. This is the AFK-farming
  story the strategy doc was holding for "Wave 2" — **it already shipped.**
- **RORORO Mac is live** — Swift/SwiftUI sibling, brew-installable, Apple-signed
  and notarized, with a built-in auto-keys AFK cycler.
- **v1.4.2.0 is sitting as two unpublished draft releases** (captcha-during-
  multi-launch fix). Not a blocker for outreach, but it should ship before the
  batch goes out so "latest" is honest. Ops flag, not a copy flag.

**Plugin capability model** (matters for the co-creation pitch): plugins declare
`host.*` capabilities — subscribe to account-launched / account-exited /
mutex-state events, request a launch, contribute UI — and `system.*` capabilities
that *honestly disclose* what the plugin does locally (synthesize keyboard/mouse,
watch global input, prevent sleep, focus foreign windows). Backlog plugins already
scoped: Session Stats, Discord Rich Presence, Auto-Relaunch on Exit.

---

## The new angle — plugin co-creation

The strategy doc treats the plugin system as a Wave 2 tease. It's stronger than
that. The plugin system turns every outreach email into a **two-way** ask: not
just "use this," but "you're the power user — tell us what to build, or watch us
build the thing you've been describing in your own comments."

### The content-recording plugin (working name: *RoRoRo Ur Stream*)

The wedge plugin for the creator segment specifically. The core feature is small,
concrete, and instantly legible to anyone who has ever tried to film six Roblox
windows at once:

- **It renames each Roblox window to the saved account's name.** Your capture
  software stops showing six identical "Roblox" windows and starts showing
  "Window: BaconFarm_01," "Window: BaconFarm_02" — you build your OBS scene once
  and never re-guess which capture is which.
- Stretch scope, creator-driven: auto-arrange windows into a capture grid, a
  hotkey to cycle recording focus across alts, an OBS WebSocket hook that spins
  up a scene per launched alt.

**Feasibility:** buildable on today's v1.4 contract. The plugin already receives
`pid + displayName + RobloxUserId` from `account-launched` events; renaming the
window title is a Win32 `SetWindowText` call against that pid's window. The
nearest declared capability is `system.focus-foreign-windows`; modifying a foreign
window's *title* may warrant one new `system.*` disclosure string — small, honest,
worth doing. **Decision needed from you:** ship this as the next first-party
plugin, or float it to creators first and let their replies write the spec.

### How it changes the ask

Every Tier 1 send below now carries a short co-creation line: *"the plugin system
is open — what would make multi-account recording less painful for you?"* It costs
the creator nothing to answer, it makes them a stakeholder instead of a billboard,
and their reply is free product research from exactly the segment we're building
for.

---

## The batch — five Tier 1 sends

Sequencing per the strategy doc: **Aussie → AlphaGG → ZOMG** smallest-first on the
install funnel; **DeeterPlays + SharkBlox** run in parallel on the coverage funnel.
Send 3-5 a session — this is the whole session. Swap any bracketed bit if you know
the recipient better than the research does.

---

### 1. Aussie — cold email (start here)

*~100K, YouTube. Pet Sim X + Pls Donate + giveaways. Smallest and most reachable;
giveaway audiences run multiple accounts constantly. Contact: YouTube About tab.*

> **Subject:** a free, Store-signed multi-launcher for your giveaway viewers
>
> Hey Aussie,
>
> Quick one — I build small Windows tools under 626 Labs, and I just put one on
> the Microsoft Store that I think your audience actually needs.
>
> It's called RORORO. It runs multiple Roblox clients side by side, each signed
> into a different saved account, one click each. Honest safety story up front
> because it matters: it doesn't inject into or modify the Roblox client — it
> holds a Windows mutex name before launch and starts the official client
> unmodified. Roblox has said multi-instancing "may be considered malicious
> behavior," so the risk isn't zero and we say so plainly in the README — but
> there's no code injection, and the Store build is Microsoft-signed, so no
> SmartScreen warning for your viewers.
>
> Why you specifically: giveaway and Pls Donate content basically runs on having
> a stack of accounts ready, and "how do you run that many at once?" is probably
> a regular in your comments. RORORO is a one-link answer that won't get you "is
> this a virus" replies.
>
> It's free. No affiliate ask, no contract, no tracking link. If you try it and
> it's useful, a mention helps us a lot. If it's not, I'd genuinely want to know
> why.
>
> - Microsoft Store: https://apps.microsoft.com/detail/9NMJCS390KWB
> - Source (MIT, open): https://github.com/estevanhernandez-stack-ed/ROROROblox
>
> One more thing, and this is the part I'd actually love your take on: RORORO has
> an open plugin system now. The first plugin's already out — a per-window macro
> recorder that won't fire keys into the wrong alt's window. The next one I'm
> scoping is for creators: it renames each Roblox window to the account name so
> your capture software can tell six windows apart instead of showing six
> identical "Roblox" tiles. What would make multi-account recording less painful
> for *your* setup? Genuinely asking — that answer would shape what I build.
>
> Either way, thanks for reading.
>
> — Este, 626 Labs
> *RORORO is an independent third-party tool, not affiliated with, endorsed by, or
> sponsored by Roblox Corporation.*

---

### 2. AlphaGG — short DM (X `@YouTubeAlphaGG`)

*~440K. Pet Sim value-list content, runs a Star Code, already does brand deals —
a DM isn't cold-cold. Reachable on X.*

> Hey AlphaGG — I build small Windows tools (626 Labs). Just put RORORO on the
> Microsoft Store: runs multiple Roblox clients side by side, one click per saved
> account. No injection — holds a Windows mutex, launches the official client
> unmodified, Store build is MS-signed so no SmartScreen warning. Free, open
> source, no affiliate ask.
>
> Figured your value-list and Pet Sim viewers ask "how do you run that many
> accounts" a lot — this is a clean answer. It's also got an open plugin system;
> first plugin (a per-window macro recorder) already shipped, and I'm scoping a
> creator one that names each Roblox window after the account so capture software
> can tell them apart. If you film multi-account, I'd love to know what would
> make that less painful for you. Store link + 30-sec demo if you want a look —
> no pressure either way.

---

### 3. ZOMG — cold email (YouTube `@ZOMGYT`)

*~0.9-1M. Active PS99 creator — mid-size enough to answer a DM, big enough to move
installs. Contact: YouTube About tab.*

> **Subject:** tool your PS99 viewers keep asking you about
>
> Hey ZOMG,
>
> Quick one — I build small Windows tools under 626 Labs, and I just put one on
> the Microsoft Store that fits PS99 content almost too well.
>
> RORORO runs multiple Roblox clients side by side, each signed into a different
> saved account, one click each. Safety story up front because it matters: no
> injection, no client modification — it holds a Windows mutex name before launch
> and starts the official client. Roblox has called multi-instancing "potentially
> malicious," so the risk isn't zero and the README says so — but there's no code
> injection, and the Store build is Microsoft-signed, so no SmartScreen warning
> for your viewers.
>
> Why you specifically: PS99 is a grind across a stack of accounts, and "how do
> you run all those?" is a permanent comment-section question. RORORO is a
> one-link answer — and the per-window macro recorder plugin that just shipped
> alongside it means a farming sequence recorded on one alt won't fire keys into
> the wrong window.
>
> It's free. No affiliate ask, no contract, no tracking link. Try it; if it's
> useful, a mention helps. If it's not, tell me why — that's useful too.
>
> - Microsoft Store: https://apps.microsoft.com/detail/9NMJCS390KWB
> - Source (MIT, open): https://github.com/estevanhernandez-stack-ed/ROROROblox
> - The macro plugin: https://github.com/estevanhernandez-stack-ed/rororo-ur-task
>
> The plugin system is open, and the next one I'm scoping is creator-facing — it
> renames each Roblox window to the account name so capture software can tell six
> windows apart. If you film PS99 across alts, what would make that recording
> workflow less painful for you? That answer would shape what I build next.
>
> Thanks for reading either way.
>
> — Este, 626 Labs
> *RORORO is an independent third-party tool, not affiliated with, endorsed by, or
> sponsored by Roblox Corporation.*

---

### 4. DeeterPlays — tool-spotlight pitch (YouTube About tab)

*~545K. Roblox news + events coverage. This is a story, not a sponsorship — pitch
the "new on the Store" beat.*

> **Subject:** not a sponsorship — a tip for your "new Roblox tools" beat
>
> Hey Deeter,
>
> Not a sponsorship pitch — a tip for the news beat.
>
> There's a multi-launcher called RORORO that just hit the Microsoft Store. Why
> it might be worth a look on camera: it's the rare one in this category that's
> open-source, Store-signed, and ships its own honest risk language instead of
> hand-waving it. It holds a Windows mutex before launch — no injection, official
> client unmodified — and the README says outright that Roblox calls
> multi-instancing "potentially malicious" and the ban risk is low-but-nonzero.
>
> The newer angle: it shipped an open plugin system, and a first plugin alongside
> it — a per-window macro recorder that won't fire into the wrong alt's window.
> There's a Mac-native sibling too. For a "what's new in Roblox tooling" segment,
> the whole release is a clean example of how this category *could* be done.
> Source is all public.
>
> - Store: https://apps.microsoft.com/detail/9NMJCS390KWB
> - Source: https://github.com/estevanhernandez-stack-ed/ROROROblox
>
> — Este, 626 Labs
> *Independent third-party tool, not affiliated with Roblox Corporation.*

---

### 5. SharkBlox — tool-spotlight pitch (YouTube About tab; X)

*~1.5M. Roblox news, free-item videos, covers Roblox tools as content. Highest-
reach Tier 1 name — lead with the story, not the ask.*

> **Subject:** new on the Store — a multi-launcher with the safety story written down
>
> Hey SharkBlox,
>
> Not a sponsorship pitch — a tip for the tool-coverage beat, since you actually
> cover Roblox tools as content.
>
> RORORO just hit the Microsoft Store: a Windows multi-launcher for Roblox — run
> multiple clients side by side, each signed into a saved account. What makes it
> worth a segment isn't the launcher, it's the posture. It's open-source,
> Store-signed, and ships its own honest risk language — the README states that
> Roblox calls multi-instancing "potentially malicious" and that ban risk is
> low-but-nonzero, instead of pretending the question doesn't exist. No
> injection; it holds a Windows mutex before launch and runs the official client
> unmodified. The provenance is owned, not hidden — the mutex technique is
> credited to Zgoly's MultiBloxy in a PROVENANCE.txt in the repo.
>
> It also just shipped an open plugin system with a first plugin — a per-window
> macro recorder — and there's a Mac-native sibling. Whatever you'd conclude about
> it, it's a clean case study in how this category could be done without the
> usual sketchiness.
>
> - Store: https://apps.microsoft.com/detail/9NMJCS390KWB
> - Source: https://github.com/estevanhernandez-stack-ed/ROROROblox
>
> — Este, 626 Labs
> *Independent third-party tool, not affiliated with Roblox Corporation.*

---

## Flags before this batch goes out

1. **Strategy-doc drift — fix before more outreach.** `rororo-creator-outreach-2026-05-14.md`
   still frames "auto-keys, an AFK-defeat cycler" as the first plugin "landing
   soon" and builds Wave 2 around it shipping. Reality: the first Windows plugin
   shipped is **RoRoRo Ur Task** (a general per-window macro recorder), published
   2026-05-13 — "auto-keys" was a placeholder name, superseded. RORORO's own
   README and `AUTHOR_GUIDE.md` carry the same stale reference. The Wave 1 / Wave 2
   split should be rethought: the AFK-farming capability is *already shippable
   today*, so Wave 2's distinct hook is now the **creator plugin** (RoRoRo Ur
   Stream), not auto-keys. Worth a focused edit pass on all three docs.
2. **v1.4.2.0 is unpublished** — two draft releases. Publish before the batch goes
   out so "latest release" in any creator's hands is honest.
3. **Decision needed:** build the content-recording plugin as the next first-party
   plugin, or float the concept in this batch and let creator replies write the
   spec. The sends above do the second by default — they ask the question.
