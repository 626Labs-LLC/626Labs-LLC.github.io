# 626 Labs Hub — Copy Brief for Voice Agent

Hand this file to your voice-agent. It returns HTML-ready prose for each section. I'll wire the results into `index.html`.

Brand-voice source of truth: `C:\Users\estev\Projects\626labs-hub\Design` (also installed as the `626labs-design` Claude Code skill). The agent should read that skill for full context. The essentials are repeated below.

---

## Brand voice guardrails (non-negotiable)

- **Second person, active voice.** "You ship. We build the tools that round out your codebase." Never "users will be able to."
- **Short sentences. Longer sentences when the point earns it.** Rhythm matters.
- **Technical specificity over abstraction.** "Claude Code plugin" beats "AI-powered assistant." Name the tool, name the verb.
- **A wink, not a wisecrack.** Dry humor. Confident, not cute.
- **No hedging.** Remove "help you to," "enables," "empowers," "leverages," "seamlessly."
- **Sentence case** for headings. Not Title Case.
- **No emoji** in prose or UI copy.
- **Em-dashes welcome.** Periods terminate even microcopy. Ellipses are for loading states only.
- **"We" for the company. "You" for the reader.** Never "our users," "our customers," "the team."
- **Product names preserve casing.** `626Labs` internally, `626 Labs` inline. `Sanduhr für Claude`. `Vibe Cartographer`.
- **Tagline to protect:** *Imagine Something Else.*

Examples from the brand:
- ✅ "Ship enterprise software with vibe-coded speed."
- ✅ "Your codebase, with the docs it always needed."
- ❌ "Unlock the power of AI-driven development"
- ❌ "Seamlessly integrates with your workflow"

---

## Sections to fill

Return each as HTML-ready markup so the agent can drop the output directly in. Use `<strong>` on product names for visual anchoring. Use `<p>` per paragraph.

### 1. About 626 Labs — **PRIORITY**

**Location:** replaces the body of `<section class="about" id="about">` — everything inside `<div class="container">` after the `<h2>About 626 Labs</h2>`.

**Length target:** 5–7 short paragraphs plus the opening `<p class="lead">...</p>` tagline. Around 250–400 words total.

**Themes to cover (Este's raw notes, to be distilled — not quoted verbatim):**

1. **Mission: "New ideas to old logic."** 626 Labs brings modern tools to practices and institutions that have been running on spreadsheets, paper, or inherited habits for decades (or centuries).

2. **Celestia 3 as the proof case.** AI combined with tarot, numerology, and astrology. We refused to ship with the second-precision default Swiss Ephemeris engine — we repaired it ourselves to reach NASA-grade accuracy. The bar moved up mid-build; we met the new bar. (The point isn't the specific tech — it's the *posture*: we don't settle.)

3. **Old empires track.** Vibe coding as the cheat code for legacy institutions and enterprise workflows that have never had digital tools that fit the actual need. Think: theater operations, safety inspections, hotel/hospitality, cinema exhibition. Off-the-shelf vendors miss the real needs; we build to the real needs.

4. **Plugins for vibe coders.** Vibe Cartographer, Vibe Doc, Vibe Test, Vibe Sec. The point is *legitimization* — helping vibe-coded apps hold up in production. (Omit the Thanos reference — it was context for the agent, not prose to keep.)

5. **Gaming, next on deck.** Trivia and head-to-head card battles inside We See You at the Movies are warm-ups. Bigger gaming ideas are queued.

6. **The tenacity line.** "I'll do it myself" — not a menacing grin, a quiet knowing smile. Won't stop until the thing turns out the way it was supposed to.

7. **Enterprise grade for an audience of one.** Even when the app may only ever be seen by one pair of eyes, it's built to the bar that would survive a thousand. *"I have deployed more apps to production than I ever imagined."*

**Constraints:**
- Open with `<p class="lead">New ideas to old logic.</p>` (or a voice-tuned variant — keep it one line, aphoristic).
- Bold product names with `<strong>` on first mention per paragraph.
- Don't name every product — the Products grid above already does. Celestia 3, Vibe plugins, and We See You at the Movies are the only ones worth specific mention here.
- Close with the "audience of one" / "enterprise grade" / "deployed more than I imagined" note. That's the kicker.
- Semi-professional + personal. Not corporate. The reader should feel like they're hearing from a builder, not a marketing team.

**Deliverable:** HTML paragraphs ready to paste. No surrounding `<section>` tag, just the inside.

---

### 2. Hero tagline — OPTIONAL

**Location:** `<p class="tag">` inside `<section class="hero">`.

**Current:** *"Open-source Claude Code plugins for turning a vibe-coded afternoon into an app that actually holds up in production — planning, docs, tests, security. Plus a native desktop widget for pacing your Claude.ai usage."*

**Target:** 1–2 sentences, under 45 words. Should plant the flag on (a) vibe coding for *serious* output, (b) the plugin ecosystem is the lead act, (c) Sanduhr is supporting. If the current line lands, leave it.

**Deliverable:** a single `<p class="tag">` element, or confirmation to keep current.

---

### 3. "The thinking behind it" — OPTIONAL

**Location:** `<section class="thinking" id="thinking">` — the blockquote + supporting paragraphs that introduce the Self-Evolving Plugin Framework.

**Current thesis quote (to preserve):**
> *A plugin should be more useful on its tenth run than on its first — not because the user learned it, but because it learned the user.*

**Current surrounding copy** talks about three pillars (self-repair, self-teach, self-evolve), five-level maturity ladder, sixteen named patterns, Vibe Cartographer at Level 3.5.

**Target:** keep the thesis blockquote verbatim. Rework the two surrounding paragraphs if the voice feels off — make them sound like a builder-to-builder explanation, not a framework marketing blurb. ~80–130 words total across both paragraphs.

**Deliverable:** two `<p>` blocks (the blockquote stays unchanged).

---

### 4. "How the lab runs" caption — OPTIONAL

**Location:** `<div class="caption">` inside `<section class="lab-runs">`.

**Current:** two paragraphs describing the 626 Labs Dashboard as a private agent OS, The Architect AI, etc., then a "not open source yet; plugins are the open-source distillation" line.

**Target:** keep the same two-beat structure. Make the first paragraph concrete about what the Dashboard *does* (Operation Center, Decisions log, Architect, Scanner/Voice/Whiteboard inputs). Make the second paragraph acknowledge the plugins are what the Dashboard taught us, now shared. ~100 words total.

**Deliverable:** two `<p>` blocks.

---

### 5. "Keep the lab running" — OPTIONAL

**Location:** `<div class="support-copy">` inside `<section class="support">`.

**Current h3:** *"Keep the lab running"*
**Current body:** *"Every 626 Labs plugin is MIT-licensed and maintained on nights and weekends. If the Vibe ecosystem is saving you time, GitHub Sponsors is the cleanest way to say thanks — and to keep the next plugin on track."*

**Target:** same tone. If the agent wants to sharpen the h3 or the body, welcome. Under 45 words total.

**Deliverable:** an `<h3>` + `<p>` inside `<div class="support-copy">`.

---

## Format for the agent's response

For each section, return:

```html
<!-- SECTION: About 626 Labs -->
<p class="lead">…</p>
<p>…</p>
<p>…</p>
<!-- …etc -->
```

Plus a one-line rationale per section explaining any voice choices that might look unusual.

---

## After the agent returns copy

Hand it back to me (this Claude session, or a new one pointed at this repo). I'll drop each block into its slot in `index.html`, verify nothing breaks the design-system tokens, commit, and push.
