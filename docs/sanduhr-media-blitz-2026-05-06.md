# Sanduhr für Claude — media blitz

Major update push: Microsoft Store launch (Win11 native), three-platform parity (Mac/Win/Python), five hand-tuned glass themes, AI-agent theme prompt, hardened no-telemetry stance.

**Links to use:**
- Product page: https://626labs.dev/sanduhr/
- Microsoft Store: https://apps.microsoft.com/detail/9NH3NK2RGCF5
- GitHub: https://github.com/estevanhernandez-stack-ed/Sanduhr_f-r_Claude
- Releases (Mac DMG): https://github.com/estevanhernandez-stack-ed/Sanduhr_f-r_Claude/releases

**Suggested asset pairings:**
- Hero shot for any single-image post → `sanduhr/screenshot-full-view.png`
- Themes triptych for "5 themes" beats → `screenshot-obsidian.png` + `screenshot-aurora.png` + `screenshot-matrix.png`
- New icon for avatar / OG → `sanduhr/icon.png`

---

## Reddit

Reddit hates promo. Lead with the problem, not the product. Link in comments where the sub allows it.

### r/ClaudeAI — primary

**Title:** I built a desktop widget that pages you before you run out of Claude usage, not after

**Body:**
The "you've used 95% of your weekly limit" email always lands too late for me. So I built Sanduhr — a tiny native widget that sits on your desktop and does the pacing math the dashboard doesn't:

- **Burn-rate projection** — "at this pace, you hit 100% in 4h 22m"
- **Pace markers** on every bar, so you can read it without doing the math
- **2-hour sparkline** per tier so you can see whether you're heating up or cooling off
- **Five glass themes** (Obsidian, Aurora, Ember, Mint, Matrix), plus drop-in JSON for custom themes
- **No telemetry.** No server. No analytics. Your session cookie lives in Keychain / Credential Manager. The only outbound call is HTTPS to claude.ai with *your own* cookie.

Three builds — Mac (SwiftUI, signed + notarized, Sparkle auto-updates), Windows 11 (native PySide6 with real Mica glass, free on the Microsoft Store), or Python single-file if you want to audit the source and `python sanduhr.py` it.

Built it after one too many "wait, I'm out?" moments at 11pm. Sharing in case anyone else has been hitting the same wall.

(Links in a comment because reddit is reddit.)

**Top comment:**
- Microsoft Store (Win11): https://apps.microsoft.com/detail/9NH3NK2RGCF5
- Mac DMG (notarized): https://github.com/estevanhernandez-stack-ed/Sanduhr_f-r_Claude/releases
- Source: https://github.com/estevanhernandez-stack-ed/Sanduhr_f-r_Claude
- Full pitch + screenshots: https://626labs.dev/sanduhr/

---

### r/macapps

**Title:** Sanduhr für Claude — native macOS widget for pacing your claude.ai subscription usage [Free, notarized DMG]

**Body:**
Native SwiftUI app, Developer ID signed and Apple-notarized so no Gatekeeper warnings. NSVisualEffectView vibrancy, Keychain-backed credentials, Sparkle auto-updates. Requires macOS 11+.

Reads your own claude.ai usage with your own session cookie and projects burn rate so you can pace yourself across the 5-hour session window and the weekly windows. Pace markers on every bar, sparkline trends, five hand-tuned glass themes, plus drop-in JSON for custom ones.

No telemetry, no analytics, no crash reporter — there's literally no server on our end to receive data.

DMG (notarized): https://github.com/estevanhernandez-stack-ed/Sanduhr_f-r_Claude/releases
Full landing page: https://626labs.dev/sanduhr/

---

### r/SideProject

**Title:** Shipped a native usage-pacing widget for Claude.ai across three platforms — Mac (notarized), Win11 (MS Store), Python source

**Body:**
The shape of the project: Anthropic exposes weekly + 5-hour session windows for claude.ai usage but their dashboard makes you do the math yourself. Sanduhr does the math.

What's interesting from a builder angle:

- Three native builds, one product. SwiftUI on Mac, PySide6 + real Win11 Mica glass on Windows, single-file tkinter for "I want to read every line before I run it" people.
- Free on the Microsoft Store, which dodges every SmartScreen / Defender false-positive issue you'd otherwise hit with PyInstaller'd Python on Windows.
- AI-agent theme prompt — hand any LLM a reference image, get back a drop-in JSON theme file. Lets users author themes without me shipping a theme editor.
- Privacy by construction: no server exists on our side. Cookie in OS-native credential store, wiped on uninstall, the only network call is HTTPS to claude.ai with the user's own cookie.

Site: https://626labs.dev/sanduhr/
GitHub: https://github.com/estevanhernandez-stack-ed/Sanduhr_f-r_Claude

Happy to talk about the Mica integration, the cross-platform theming model, or the MS Store submission process if anyone's about to do similar.

---

### r/Anthropic / r/ChatGPTPro / r/LocalLLaMA (variations)

Trim the body. Lead with: "Built a desktop widget that does pacing math for claude.ai subscription windows so you don't run out at 11pm." Link the product page. Keep it short.

---

## X / Twitter

### Launch tweet (single shot)

> The "95% used" email always lands too late.
>
> So I built Sanduhr — a native desktop widget that paces your claude.ai usage *before* you run dry.
>
> Burn-rate projection. Pace markers. 5 glass themes. Mac + Win native, free on the Microsoft Store.
>
> No telemetry.
>
> 626labs.dev/sanduhr

[attach screenshot-full-view.png]

---

### Launch thread

**1/**
> Sanduhr für Claude is now native on Mac *and* Windows.
>
> It's a desktop widget that does the pacing math claude.ai's dashboard doesn't — so you can see "hits 100% in 4h 22m at current pace" instead of finding out at 11pm that you're out.
>
> 626labs.dev/sanduhr

[attach screenshot-full-view.png]

**2/**
> Three builds, one product:
>
> → Mac: native SwiftUI, Apple-notarized, Sparkle auto-updates, NSVisualEffectView vibrancy
> → Win11: native PySide6 with real Mica glass, free on the Microsoft Store
> → Python: single-file tkinter, audit every line, runs on anything
>
> Pick your platform.

**3/**
> The pacing math is the whole point.
>
> Pace markers on every bar = "you should be here right now."
> 2-hour sparkline = are you accelerating or cooling off.
> Burn-rate projection = "if you keep this up, you're out at 11:42pm."
>
> Read it by eye. Don't do mental arithmetic.

[attach screenshot-aurora.png]

**4/**
> Five hand-tuned glass themes ship in the box: Obsidian, Aurora, Ember, Mint, Matrix.
>
> Plus a JSON theme format and an AI-agent prompt — hand Claude or any chat agent a reference image, paste the prompt, drop the resulting JSON in. Done.

[attach screenshot-obsidian.png + screenshot-matrix.png as 2-up]

**5/**
> Privacy is structural, not a checkbox.
>
> No telemetry. No analytics. No crash reporter. We have no server to receive data from Sanduhr — even in principle.
>
> The only outbound call is HTTPS to claude.ai with your own session cookie, stored in Keychain / Credential Manager. Wiped on uninstall.

**6/**
> Free.
>
> → Microsoft Store (Win): apps.microsoft.com/detail/9NH3NK2RGCF5
> → Mac DMG (notarized): github.com/estevanhernandez-stack-ed/Sanduhr_f-r_Claude/releases
> → Source: github.com/estevanhernandez-stack-ed/Sanduhr_f-r_Claude
>
> Full pitch + all screenshots: 626labs.dev/sanduhr

---

### Quote-tweet variants (for re-poking the launch over the next few days)

**Day +1 — features angle**

> Forgot to mention the AI-agent theme prompt.
>
> Hand Claude (or any chat agent) a reference image and the prompt that ships with Sanduhr. Get back a drop-in JSON theme file. Paste, done.
>
> A theme editor I didn't have to write.

[attach a custom-theme example screenshot if available]

**Day +2 — privacy angle**

> The reason Sanduhr has no telemetry isn't policy. It's that there's no server on our end to receive it.
>
> Your cookie goes in Keychain / Credential Manager. The only network call is HTTPS to claude.ai with that cookie, to read your own numbers.
>
> Privacy by construction.

**Day +3 — Win11 Mica angle**

> The Win11 build is real PySide6 with real Mica backdrop. Not Electron pretending. Not WebView dressed up.
>
> If you're on Win11 and you want to see what native Python desktop UI can actually look like in 2026, free on the Microsoft Store:
>
> apps.microsoft.com/detail/9NH3NK2RGCF5

[attach a Mica-on screenshot]

---

## Notes for posting

- **Sequence:** X launch tweet first → reddit r/ClaudeAI within an hour → r/macapps + r/SideProject the next day → X thread same day or +1 → quote-tweet daypole over week 1.
- **Don't** cross-post the same body to two reddits — re-write each.
- **Don't** put "I built this" in the title for r/ClaudeAI; it triggers their promo flag. The body owns the disclosure.
- **Watch for:** "is this affiliated with Anthropic?" — answer "no, independent third-party tool, claude.ai is used nominatively, see the footer of the product page." Pin this answer in any thread it surfaces in.
- **Comments to anticipate:** "why German name?" → it's hourglass in German, fits the pacing metaphor. "Linux?" → Python build runs on Linux, native build is on the roadmap if there's pull.
