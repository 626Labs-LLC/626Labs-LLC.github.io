# RORORO — creator outreach

Strategy + paste-ready copy + a tiered target list for getting RORORO in front of
Roblox YouTubers and the sites/communities they live in.

Companion to [`rororo-media-blitz-2026-05-06.md`](rororo-media-blitz-2026-05-06.md) —
that doc covers the Reddit + X launch posts. This one covers creator/influencer
outreach, which the media-blitz doc doesn't touch. Use them together.

> **Status note (2026-05-14):** Creator names and subscriber counts below were
> sourced from public web data in May 2026. Counts drift — treat them as tier
> bands, not exact figures. Contact paths are listed where verifiable; where a
> business email wasn't public, the doc says so rather than guessing. Verify the
> contact path before you send.

---

## The play in one paragraph

RORORO is an unusually good fit for Roblox-creator outreach because content
creators *are* the power-user segment for multi-account tooling — they need alts
running constantly to film multiplayer, trading, giveaways, and AFK-grind
content. The wedge is not "please promote our app." The wedge is "your viewers
already ask you how you run six accounts at once — here's a clean, free, signed
answer you can point them at without the 'is this a virus' comments." We lead
with the safety story, we ask for nothing binding, and we sequence small-to-large
so the messaging is pressure-tested before it reaches the big names.

---

## Links to use

- **Microsoft Store:** https://apps.microsoft.com/detail/9NMJCS390KWB
- **GitHub:** https://github.com/estevanhernandez-stack-ed/ROROROblox
- **Releases (sideload installer + MSIX):** https://github.com/estevanhernandez-stack-ed/ROROROblox/releases
- **Product page (when live):** https://626labs.dev/ — RORORO product section

## Asset pairings

- **Hero / avatar / OG:** three-voxel-stack icon (cyan/magenta/cyan on navy)
- **"Run six at once" proof shot:** main window with 4-6 saved accounts and
  **Launch As** buttons visible — this is the screenshot that sells it to a
  creator audience
- **Tray-state demo:** system tray with the cyan ring on (multi-instance ON)
- **30-second walkthrough:** the video linked from each Release page — send this,
  not a wall of text, when a creator asks "what does it actually do"

## Trust rails — never violate, even by accident

Carried forward from the media-blitz doc. These are load-bearing for creator
outreach specifically, because a creator's whole business is audience trust —
they will not touch anything that reads as ban-bait.

- **Trademark:** "Roblox" is a trademark of Roblox Corporation. Always say
  "independent third-party tool, not affiliated with, endorsed by, or sponsored
  by Roblox Corporation."
- **Don't oversell the safety.** The honest line is the only line: "Risk of a ban
  appears low — we don't inject, we hold a Windows mutex name before launch — but
  it is non-zero. Don't run this on accounts you can't afford to lose." A creator
  who repeats that line is protected. A creator who repeats an overclaim is
  exposed — and they know it, so an overclaim gets you ignored.
- **Provenance is owned, not hidden.** The named-mutex technique is Zgoly's
  MultiBloxy. RORORO is a clean C# reimplementation with expanded scope, not a
  fork. PROVENANCE.txt is in the repo.
- **Never say "alt accounts" in a subject line or title.** The product language
  is "saved accounts." "Alt" reads as ban-evasion to a moderator skimming fast.
- **Never pitch it for cheating.** The use cases are real: trading across
  accounts, AFK-grind content, multiplayer filming, dev QA, giveaways. If someone
  reframes it as exploiting, that's their reframe — don't carry it.

---

## Why creators, and which creators

### The wedge

Three things make RORORO land with a creator audience that a generic "check out
my app" pitch never would:

1. **The pain is already in their comments.** Every PS99 grinder, trader, and
   giveaway creator gets asked "how do you run that many accounts?" RORORO is a
   one-link answer.
2. **It's free and signed.** No affiliate ask, no paywall to explain, and the
   Microsoft Store listing means no SmartScreen warning to talk their viewers
   through. That removes the single biggest reason a creator declines a tool
   shout-out — the "my viewers will think I'm shilling malware" risk.
3. **It's the un-sketchy one.** The incumbents (Roblox Account Manager,
   MultiRoblox, the various `*strap` forks) are GitHub binaries or bootstrapper
   mods. RORORO is on the Store, open-source, with a DPAPI-encrypted vault and a
   privacy policy. That contrast *is* the creator pitch — they can recommend it
   on-camera without the comment-section blowback.

### The constraint — safety-first or nothing

This lives in Roblox-ToS gray territory; Roblox's own wording is that
multi-instancing "may be considered malicious behavior." Creators are allergic to
recommending anything that could get their audience banned. So every piece of
outreach **opens** with the safety frame — no injection, holds a Windows mutex,
launches the official client unmodified, on the Microsoft Store — and only then
gets to features. If the safety story isn't the first thing they read, the pitch
is dead.

### The offer — what we give, and what we don't

RORORO is free, so there is no affiliate cut to dangle. That's a feature, not a
gap — it makes the outreach honest. What we actually offer:

- **A genuinely useful free tool their audience wants.** That's the whole offer
  for most Tier 1 contacts. No contract, no "must post," no tracking link.
- **No-strings framing.** "Try it. If it's useful, a mention helps us. If it's
  not, tell us why — that's useful too." A creator can say yes to that in one
  reply.
- **Early access to the plugin ecosystem.** v1.4 shipped the plugin system; the
  first plugin — `auto-keys`, an AFK-defeat cycler — lands in a sibling repo
  soon. For PS99 creators specifically, *that* is the killer hook (see below).
  Offer named creators a heads-up + early build when it ships.
- **Build-what-they-need, within reason.** For a high-fit creator with a specific
  workflow gap, "what would make this perfect for your setup?" is a real offer.
  The roadmap already has creator-shaped items.
- **What we don't offer:** paid placement, inflated claims, or anything that
  compromises the trust rails. If a creator only does paid promo and the rate
  doesn't fit a free product's budget, that's a Tier 3 "later, maybe" — not a
  reason to bend the pitch.

### The two waves

- **Wave 1 (now) — the launcher.** RORORO as it ships today: multi-instance,
  saved-account vault, Launch As, Squad Launch. Target: traders, multi-account
  creators, Roblox-news/tool creators, the trading communities.
- **Wave 2 (when `auto-keys` ships) — the AFK story.** PS99 is a grind. AFK-
  farming across a stack of accounts is exactly what a chunk of the PS99 audience
  does. An AFK-defeat cycler plugin on top of a clean multi-launcher is a much
  bigger creator hook than the launcher alone — and it's the angle that gets the
  Tier 2 PS99 names interested. Don't burn the big names on Wave 1; tease the
  plugin to them and come back loud when it's real.

---

## Target list

Tiered by fit × reachability, not by raw subscriber count. **Tier 1 is where you
start** — mid-size, reachable, audience has the exact pain. Tier 2 is the bigger
lift kept warm for Wave 2. Tier 3 is broad reach and later-wave mentions.

Confidence is labeled per row. Verify the contact path before sending — do not
treat "About tab" as confirmed until you've looked.

### Tier 1 — start here

| Creator | Platform / handle | Reach (band) | Why they fit | Contact path | Confidence |
|---|---|---|---|---|---|
| **AlphaGG** | YouTube `@AlphaGG`, X `@YouTubeAlphaGG` | ~440K | Pet Sim X / Pet Sim 2 / Bubble Gum / value-list content. Runs a Star Code — already does brand deals, so an outreach DM isn't cold-cold. Audience grinds and trades. | X DM `@YouTubeAlphaGG`; Discord `discord.com/invite/alphagg`; check YouTube About tab for business email | Med-high |
| **ZOMG** | YouTube `@ZOMGYT` | ~0.9-1M | Active PS99 creator. Mid-size enough to answer a DM, big enough to move installs. | YouTube About tab; channel-linked socials | Medium |
| **Aussie** | YouTube | ~100K | Pet Sim X + Pls Donate + giveaways. Giveaway-driven audiences run multiple accounts constantly — tight fit. Small enough to be very reachable. | YouTube About tab | Medium |
| **DeeterPlays** | YouTube | ~545K | Roblox news + events coverage. Different angle from the PS99 grinders — pitch as a *tool spotlight / "new on the Store"* news beat, not a sponsorship. | YouTube About tab | Medium |
| **SharkBlox** | YouTube, ~1.5M | ~1.5M | Roblox news, free-item videos, community/tool commentary. He *covers Roblox tools as content*. Pitch the tool-spotlight angle — "here's a new Store-listed multi-launcher, here's the honest safety story." | YouTube About tab; X | Med-high |

### Tier 2 — bigger lift, keep warm for Wave 2

| Creator | Platform / handle | Reach (band) | Why they fit | Contact path | Confidence |
|---|---|---|---|---|---|
| **Digito** | YouTube | ~2.75M | Dominant PS99 creator, English, was among the first to end-game zones. Perfect audience fit; large enough that this is a real ask. Save for the `auto-keys` wave. | Business inquiry via YouTube About tab; agency/management likely | Medium |
| **RussoPlays** | YouTube `@russoplaysgames` | ~2M+ | Pet Sim + heavy *trading* content. Trading is a multi-account workflow — strong thematic fit. | YouTube About tab; X `@RussoTalkss` (verify) | Medium |
| **Gravycatman** | YouTube | ~4.3M | Huge Pet Sim creator. Great audience fit, but at this size expect management and a rate card. Wave 2, and only if a smaller PS99 push has already proven the messaging. | Management via YouTube About tab | Medium |
| **Conor3D** | YouTube | ~800K | Roblox walkthroughs + tutorials. Fits a "how-to: run multiple accounts the safe way" video natively. | YouTube About tab | Low-med |
| **Reckless - Roblox** | YouTube | ~1.7M | Roblox tutorials / how-to. Same native fit as Conor3D — the tutorial format is the product demo. | YouTube About tab | Low-med |

### Tier 3 — broad reach, later wave, or mention-only

| Target | Why it's Tier 3 | Use |
|---|---|---|
| **KreekCraft** (~16M) and the general top-tier Roblox names | Massive reach, weak direct fit, expensive. | Not an outreach target. If RORORO gets organic traction, they may cover it — don't chase. |
| **"How to run multiple Roblox accounts" tutorial channels** | High keyword fit — their videos *are* the use case — but many are SEO-style channels with low trust transfer. | Wave-2 "here's a cleaner method" outreach. Low effort, low priority. Worth a templated DM, not a custom pitch. |
| **RTC / `@Roblox_RTC`** | Roblox news outlet (X-first, small YouTube channel with KreekCraft / Jackeryz / WaffleTrades). | Pitch as a *news mention* — "new Store-listed multi-launcher" — not a sponsorship. Good for credibility, not installs. |

### Sites & communities — the "youtubers' sites" angle

This is where the audience already gathers. Often higher-yield than a single
creator because the post stays up.

| Target | What it is | Approach |
|---|---|---|
| **Rolimon's** | Largest Roblox trading site (`rolimons.com`) + ~270K-member Discord. | Traders run multiple accounts. Find the right channel/role in their Discord and post under their self-promo rules — read the rules first. Don't spam the trade channels. |
| **Traderie** (`traderie.com/petsimulator99`) | Moderated PS99 trading marketplace + community. | Community/Discord post where their rules allow. Same self-promo discipline. |
| **PS99 trading Discords** | Multiple large PS99/SAB/trading servers. | Templated community post (below). Read each server's promo rules; skip the ones that ban tool posts rather than argue. |
| **r/RobloxDevelopers / r/robloxgamedev** | Already in the media-blitz doc — dev QA angle. | Covered by the media-blitz doc; cross-referenced here for completeness. |
| **GitHub "awesome-roblox" / tool lists & directories** | Curated lists where Roblox tools get discovered. | Low-effort PRs / submissions. RORORO being open-source + MIT helps here. |

### Competitive context — what creators will compare us to

Know these so the pitch positions cleanly. Do not bash them — the provenance
posture is "reuse without erasure." Position on *trust and polish*, not on
trashing the incumbents.

- **Roblox Account Manager (RAM)** by ic3w0lf22 — the incumbent account manager.
  GitHub binary. RORORO's edge: Store-signed, encrypted vault, privacy policy.
- **MultiBloxy** by Zgoly — the provenance ancestor. Credit it; don't compete
  with it.
- **MultiRoblox / Multiple Games / Bloxstrap (2.9.0+) / Hellstrap / Voidstrap** —
  bootstrapper-class tools; multi-instance is a toggle, not an account workflow.
  RORORO's edge: it's an account *manager*, not just an instance unlocker.
- **Process Explorer manual method** — the "free but fiddly" baseline. RORORO's
  edge: one click, no handle-killing.

The one-line positioning: **"the multi-launcher you can recommend on camera."**

---

## The copy

All copy is paste-ready and on the 626 voice: builder-to-builder, second person,
sentence case, em-dashes welcome, no emoji, no "empower / leverage / seamlessly /
unlock." Lead with the verdict. Swap the bracketed bits per recipient.

### A. Cold email — Tier 1 / Tier 2 creators

> **Subject:** a free, Store-signed multi-launcher for your [PS99 / trading] viewers
>
> Hey [name],
>
> Quick one — I build small Windows tools under 626 Labs, and I just put one on
> the Microsoft Store that I think your audience actually needs.
>
> It's called RORORO. It runs multiple Roblox clients side by side, each signed
> into a different saved account, one click each. The honest version of the
> safety story up front, because it matters: it doesn't inject into or modify the
> Roblox client — it holds a Windows mutex name before launch and starts the
> official client unmodified. Roblox has said multi-instancing "may be considered
> malicious behavior," so the risk isn't zero and we say so plainly in the README
> — but there's no code injection, and the Store build is Microsoft-signed, so no
> SmartScreen warning for your viewers.
>
> Why I'm writing you specifically: your [trading / PS99 grind / giveaway]
> content basically requires running a stack of accounts, and "how do you do
> that?" is probably a regular in your comments. RORORO is a one-link answer that
> won't get you "is this a virus" replies.
>
> It's free. No affiliate ask, no contract, no tracking link. If you try it and
> it's useful, a mention helps us a lot. If it's not, I'd genuinely want to know
> why — that's useful too.
>
> - 30-second walkthrough: [release-page video link]
> - Microsoft Store: https://apps.microsoft.com/detail/9NMJCS390KWB
> - Source (MIT, open): https://github.com/estevanhernandez-stack-ed/ROROROblox
>
> One more thing worth a heads-up: v1.4 added a plugin system, and the first
> plugin — an AFK-defeat cycler — is landing soon. Happy to get you an early
> build when it ships if that's interesting.
>
> Either way, thanks for reading.
>
> — [your name], 626 Labs
> *RORORO is an independent third-party tool, not affiliated with, endorsed by,
> or sponsored by Roblox Corporation.*

### B. Short DM / X version — for creators reachable that way

> Hey [name] — I build small Windows tools (626 Labs). Just put RORORO on the
> Microsoft Store: runs multiple Roblox clients side by side, one click per saved
> account. No injection — holds a Windows mutex, launches the official client
> unmodified, Store build is MS-signed so no SmartScreen warning. Free, open
> source, no affiliate ask. Figured your [trading/PS99] viewers ask "how do you
> run that many accounts" a lot — this is a clean answer. 30-sec demo + Store
> link if you want a look. Either way, no pressure.

### C. Tool-spotlight pitch — for news / commentary creators (SharkBlox, DeeterPlays, RTC)

Different framing: this is a *story*, not a sponsorship. They cover Roblox tools
as content; give them the angle.

> **Subject:** new on the Store — a multi-launcher with the safety story written down
>
> Hey [name],
>
> Not a sponsorship pitch — a tip for the "new Roblox tools" beat.
>
> There's a multi-launcher called RORORO that just hit the Microsoft Store. The
> reason it might be worth a look on camera: it's the rare one in this category
> that's open-source, Store-signed, and ships its own honest risk language
> instead of hand-waving it. It holds a Windows mutex before launch — no
> injection, official client unmodified — and the README says outright that
> Roblox calls multi-instancing "potentially malicious" and the ban risk is
> low-but-nonzero.
>
> Whatever you'd conclude about it, it's a clean example of how this category
> *could* be done. Source is all public.
>
> - Store: https://apps.microsoft.com/detail/9NMJCS390KWB
> - Source: https://github.com/estevanhernandez-stack-ed/ROROROblox
> - 30-sec walkthrough: [release-page video link]
>
> — [your name], 626 Labs
> *Independent third-party tool, not affiliated with Roblox Corporation.*

### D. Community post — Discords / trading communities (where self-promo rules allow)

> **Read the server's self-promo rules before posting. If tool posts are banned,
> skip the server — don't argue.**
>
> Posting this here because a lot of you run multiple accounts for trading and it
> comes up constantly:
>
> RORORO is a free Windows multi-launcher for Roblox — run several clients side
> by side, each signed into a different saved account, one click each. Saved
> accounts live in a DPAPI-encrypted vault tied to your Windows user.
>
> Honest safety note, because you should have it: it doesn't inject into or
> modify the Roblox client — it holds a Windows mutex name before launch and
> starts the official client. Roblox has said multi-instancing "may be considered
> malicious behavior," so the risk isn't zero. Don't run it on accounts you can't
> afford to lose. That warning is in the README on purpose.
>
> Free on the Microsoft Store (MS-signed, no SmartScreen warning), open source on
> GitHub. Independent third-party tool, not affiliated with Roblox Corporation.
>
> [Store + GitHub links per server's link rules — comments if required]

### Subject-line bank

Avoid "alt," "cheat," "exploit," "bypass," "hack," "free Robux" — all of those
trip spam filters and moderator instincts. Tested-safe options:

- `a free, Store-signed multi-launcher for your [PS99/trading] viewers`
- `tool your multi-account viewers keep asking you about`
- `new on the Microsoft Store — multi-launcher, open source, free`
- `not a sponsorship — a tip for your "new Roblox tools" beat` (news creators)
- `built something your trading content basically requires`

### Follow-up (once, after ~5-7 days of no reply)

> Hey [name] — bumping this once in case it got buried. No worries if it's not a
> fit. If it helps, here's the 30-second walkthrough on its own: [link]. That's
> the whole pitch. Thanks either way. — [your name]

One follow-up. Not two. Silence is an answer.

---

## Notes for outreach

### Sequencing and cadence

- **Start Tier 1, smallest first.** Aussie → AlphaGG → ZOMG before you touch a
  Tier 2 name. The point is to pressure-test the pitch and rack up real
  installs/feedback so the Tier 2 email can say "creators X and Y's audiences are
  already using it."
- **News/commentary creators (SharkBlox, DeeterPlays, RTC) run in parallel** —
  they're a different funnel (coverage, not installs) and don't compete for the
  same calendar slot.
- **Hold Tier 2 for Wave 2.** When `auto-keys` ships, the PS99 pitch gets
  materially stronger. Email Digito/Gravycatman/RussoPlays *then*, with the
  plugin as the lead — not now with the launcher alone.
- **Batch size:** 3-5 personalized sends per session, not a blast. Each email's
  "why you specifically" line has to be real.
- **Pace:** one outreach session every 2-3 days through Wave 1. This is a slow
  burn, not a launch-day spike.

### What to watch for

- **"Is this against Roblox ToS?"** — Answer verbatim: "We don't inject or modify
  the client — we hold a Windows mutex name before launch. Roblox has called
  multi-instancing 'potentially malicious'; we surface that warning in the README
  and privacy policy. Whether it violates ToS is Roblox's call, not ours, and we
  say so directly." Never improvise past this answer.
- **"Why does SmartScreen warn me?"** — "The Microsoft Store build is signed and
  bypasses SmartScreen entirely. Only the sideload installer is unsigned — a code
  cert costs more than the app's funding. Source is on GitHub if you'd like to
  read every line." Point creators at the Store link, not the sideload one.
- **A creator wants paid promo.** Fine to decline cleanly: "We're a free product
  with no ad budget — this is a no-strings 'try it if it's useful' ask, not a
  paid placement. If that changes we'll come back." Don't bend the budget to
  chase one name.
- **A creator reframes it as a cheating tool.** Don't carry the reframe. Restate
  the real use cases (trading, AFK-grind content, multiplayer filming, dev QA,
  giveaways) once. If they keep pushing the cheating frame, disengage — that
  coverage would hurt more than help.

### What not to do

- **Don't say "alt accounts."** Product language is "saved accounts," every time.
- **Don't mass-DM identical copy.** The "why you specifically" line is the whole
  pitch. Without it, it's spam and it reads as spam.
- **Don't pitch the big names first.** Burning Digito or Gravycatman on an
  un-pressure-tested Wave 1 message wastes the best shots.
- **Don't argue with a server's mod team.** If a community bans tool posts, skip
  it. The trust posture is worth more than one post.
- **Don't overstate the safety.** Low-but-nonzero risk, stated plainly, is the
  pitch. An overclaim is how you lose a creator who would otherwise have said
  yes.
- **Don't promise the `auto-keys` plugin a ship date you don't control.** "Soon"
  and "I'll get you an early build" — not a calendar date.

### Tracking

Keep a simple sheet — creator, tier, channel, date sent, follow-up date,
response, outcome. The Tier 2 / Wave 2 emails depend on being able to name real
Wave 1 traction, so the record-keeping isn't optional. A creator who said "not
now" is a Wave 2 contact, not a dead lead — log them that way.

---

*Companion docs: [`rororo-media-blitz-2026-05-06.md`](rororo-media-blitz-2026-05-06.md)
(Reddit + X launch copy). RORORO repo: https://github.com/estevanhernandez-stack-ed/ROROROblox*
