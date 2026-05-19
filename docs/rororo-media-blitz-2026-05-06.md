# RORORO — media blitz

Microsoft Store launch for RORORO, the Windows-native multi-launcher for Roblox: spawn multiple Roblox clients side by side, each signed in as a different saved account.

**Links to use:**
- Microsoft Store: https://apps.microsoft.com/detail/9NMJCS390KWB
- GitHub: https://github.com/estevanhernandez-stack-ed/ROROROblox
- Releases (sideload installer + MSIX): https://github.com/estevanhernandez-stack-ed/ROROROblox/releases

**Suggested asset pairings:**
- Hero icon (three voxel stack, cyan/magenta/cyan on navy) → `assets/thumb-rororo.png`
- For tray-state demos, screenshot the system tray with the cyan ring on (multi-instance ON)
- For account vault, screenshot the main window with 2-3 saved accounts and **Launch As** buttons visible

**Trust rails — never violate, even by accident:**
- "Roblox" is a trademark of Roblox Corporation. Always say "independent third-party tool, not affiliated with, endorsed by, or sponsored by Roblox Corporation."
- Don't oversell. The honest line is: "Risk of a ban appears low — we don't inject, we hold a Windows mutex name before launch — but it is non-zero. Don't run this on accounts you can't afford to lose."
- Provenance is owned, not hidden. The named-mutex defeat technique is from MultiBloxy by Zgoly. RORORO is a clean C# reimplementation with expanded scope, not a fork. PROVENANCE.txt in the repo.

---

## Reddit

### r/roblox

Read the rules first. Most Roblox subs disallow tools that touch the client. RORORO doesn't inject or modify the Roblox client (only holds a Windows mutex name before launch), but mods may still flag it. Lead with the honest, technical framing.

**Title:** RORORO — open-source multi-launcher for Roblox on Windows, now free on the Microsoft Store

**Body:**
Built a Windows-native multi-launcher so I could test my Roblox creations across two accounts without alt-tabbing into a second PC. Open-sourced it on GitHub a few weeks back; the Microsoft Store listing went live today.

What it does:
- Tray toggle holds the Roblox singleton mutex so multiple clients can run side by side. *Same trick the older MultiBloxy tool used* — RORORO is a clean C# reimplementation, not a fork (PROVENANCE.txt in the repo with the original credit).
- Save Roblox accounts via an embedded login window (your password never touches the app process — the login form is Roblox's own page in a WebView2).
- *Launch As* spawns each saved alt straight into a default game URL you set once.
- DPAPI-encrypted account vault — saved cookies are tied to your Windows user, the file won't decrypt on another PC.

**On bans:** I am not Roblox / Hyperion. They've stated multi-instancing "may be considered malicious behavior." We don't inject into or modify the Roblox client, so risk appears low — but it's non-zero. Don't run this on accounts you can't afford to lose. That language is in the README and the privacy policy on purpose.

Free on the Microsoft Store, MIT-licensed source on GitHub. Independent third-party tool — not affiliated with Roblox Corporation. Honest feedback welcome, including "you should not have shipped this" if that's where you land.

[links in comments because reddit]

---

### r/RobloxDevelopers / r/robloxgamedev

Devs are the cleanest audience here — they have legit "test on two accounts" use cases. Tone shifts to *creator tooling*.

**Title:** Released RORORO — Windows multi-launcher for Roblox creators who need to QA across multiple accounts

**Body:**
If you've ever needed to test a place across two accounts and didn't want to spin up a second machine or use Roblox Studio's Local Server (which doesn't reproduce client behavior 1:1), this is for you.

RORORO holds the singleton mutex on Windows so you can run multiple Roblox clients side by side, each signed in as a different saved account. Native .NET 10 + WPF — no Electron, no DevTools tricks, no registry edits.

For dev workflow specifically:
- Save your test alts once via the embedded WebView2 login. Password never touches the app process — login happens on Roblox's own page; we capture only the `.ROBLOSECURITY` cookie post-success.
- DPAPI-encrypted vault, tied to your Windows user. File can't decrypt on a different PC.
- Set a default game URL once → *Launch As* lands every alt in your test place.
- Tray UX with state-coloured ring (cyan = mutex held, slate = off, magenta = error).

Free on the Microsoft Store. MIT-licensed source on GitHub. Independent third-party tool, not affiliated with or endorsed by Roblox Corporation.

If you find places where it falls down for your dev loop, please file a GitHub issue — there's a roadmap item for distinguishing Roblox-side 2FA re-verify from "session expired" that I'd love eyes on.

---

### r/SideProject

Builders. Same shape as the Sanduhr post — lead with what's interesting from a builder angle.

**Title:** Shipped a native .NET 10 Roblox multi-launcher to the Microsoft Store — here's what was actually hard

**Body:**
Just got RORORO live on the Microsoft Store. WPF + WPF-UI + .NET 10 + WebView2 + DPAPI + Velopack. The interesting stuff:

- **The mutex defeat is documented and old** — Zgoly's MultiBloxy did it years ago. What was hard wasn't reimplementing the trick; it was wrapping it in something a non-developer can install, sign, and trust.
- **Login capture without seeing the password.** The embedded login is Roblox's own page in WebView2 — keystrokes go straight from browser to Roblox's servers, not through our process. We only ever touch the `.ROBLOSECURITY` cookie that gets set after a successful login. Then DPAPI before it goes to disk.
- **MS Store submission for a tool that touches a third-party trademark.** Spent more time on the trademark / nominative-use language than on the WPF chrome. Footer disclaimer, README disclaimer, privacy-policy disclaimer, store-listing disclaimer. The Store team approved the listing on the first pass with that language verbatim.
- **Velopack vs MSIX vs sideload-MSIX.** Three install paths in v1.1, each useful for a different trust posture. SmartScreen-bypassing Store install for "I just want it to work." Sideload MSIX with a pinned dev cert for "I want to inspect what's happening." Velopack-updated `.exe` from GitHub Releases for "the Store hasn't approved yet but I want it now."

Source: github.com/estevanhernandez-stack-ed/ROROROblox
Store: apps.microsoft.com/detail/9NMJCS390KWB

Happy to talk through any of those if you're about to do similar.

---

## X / Twitter

### Launch tweet (single shot)

> Shipped RORORO to the Microsoft Store today.
>
> Native Windows multi-launcher for Roblox — run multiple clients side by side, each signed in as a saved alt. .NET 10 / WPF, DPAPI-encrypted vault, login captured in Roblox's own page (your password never touches the app).
>
> Free. apps.microsoft.com/detail/9NMJCS390KWB

[attach hero icon + a screenshot of the main window with 2 saved accounts]

---

### Launch thread

**1/**
> RORORO just hit the Microsoft Store.
>
> It's a Windows-native multi-launcher for Roblox — spawn multiple clients side by side, each signed in as a different saved account. Native .NET 10 + WPF. No Electron, no DevTools, no registry edits.
>
> Free: apps.microsoft.com/detail/9NMJCS390KWB

[attach hero icon]

**2/**
> The technique that makes it work — holding the Roblox singleton mutex name before launch — was originated by MultiBloxy (Zgoly) years ago.
>
> RORORO is a clean C# reimplementation, not a fork. PROVENANCE.txt in the repo credits the source. Reuse without erasure.

**3/**
> What's new vs. older multi-launchers: a real account vault.
>
> Save your alts once via an embedded WebView2 login window. Click *Launch As* to spawn each one straight into your default game URL.
>
> Login is Roblox's own page — your password never touches the app's process.

[attach screenshot of main window with saved accounts]

**4/**
> Cookies are stored DPAPI-encrypted — Windows-issued encryption tied to your specific user on your specific machine.
>
> A copy of `accounts.dat` moved to another PC won't decrypt. We don't have the key. The OS does. That's the point.

**5/**
> Tray UX with a state-coloured ring:
>
> cyan = mutex held, multi-instance ON
> slate = off
> magenta = error
>
> Read it at a glance. No menu-diving to know whether you're set up to launch alts.

[attach a tray-state composite if available]

**6/**
> Caveat owned, not hidden: Roblox has stated multi-instancing "may be considered malicious behavior."
>
> We don't inject into or modify the client. We hold a Windows mutex name before launch. Risk of a ban appears low — but it's non-zero.
>
> Don't run this on accounts you can't afford to lose.

**7/**
> Free on the Microsoft Store. MIT-licensed source on GitHub.
>
> → Store: apps.microsoft.com/detail/9NMJCS390KWB
> → Source: github.com/estevanhernandez-stack-ed/ROROROblox
>
> Independent third-party tool. Not affiliated with, endorsed by, or sponsored by Roblox Corporation.

---

### Quote-tweet variants

**Day +1 — provenance angle**

> The thing I'm most proud of in RORORO isn't the WPF chrome or the Velopack update flow.
>
> It's the PROVENANCE.txt. The mutex trick is Zgoly's. We reused it cleanly, credited it loudly, and reimplemented it in C# with broader scope. That's how you ship on top of someone else's work without erasing them.

**Day +2 — privacy angle**

> Why RORORO has no telemetry: we have no server. There's no place for your data to go on our side, even in principle.
>
> Cookies live DPAPI-encrypted on your machine. The only network calls are to Roblox during launch — the same calls Roblox.com makes from your browser.

**Day +3 — install angle**

> Three ways to install RORORO. Pick the trust posture that fits you:
>
> 1. Microsoft Store — bypasses SmartScreen entirely. Easiest.
> 2. Sideload MSIX — pinned dev cert, you import once. For "show me the cert chain."
> 3. Velopack `.exe` — auto-updates from GitHub Releases. For "Store-pending, I want it now."

---

## Notes for posting

- **Sequence:** X launch tweet first → r/SideProject same day → r/RobloxDevelopers next day → r/roblox last (the highest-rule-density sub, post when the messaging has been pressure-tested elsewhere) → X thread 24-48h after launch tweet → daypoles over week 1.
- **Read the rules of every Roblox sub before posting.** Some explicitly prohibit "exploits / multi-instance / alt tools." If a sub bans it, don't argue — skip the sub. r/RobloxDevelopers is friendlier than r/roblox for tool announcements.
- **Don't** put "alt accounts" in any title. The wording "saved accounts" is what we use.
- **Watch for:** mods asking for clarification on whether this violates Roblox ToS. Answer: "We don't inject or modify the client — we hold a Windows mutex name before launch. Roblox has called multi-instancing 'potentially malicious'; we surface that warning verbatim in the README. Whether it violates ToS is Roblox's call, not mine. The README and privacy policy say so directly."
- **Watch for:** "is this a virus / why does SmartScreen warn me?" Answer: "Sideload installer is unsigned (cert costs > the app's funding). Microsoft Store install is signed and bypasses SmartScreen entirely. Source is on GitHub if you'd like to read every line first."
- **Don't** engage with anyone who frames it as "for cheating." The dev / QA / asset-testing use case is the real one. If someone wants to use it for something else, that's their call, not our pitch.
