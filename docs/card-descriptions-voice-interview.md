# Card descriptions — voice interview (mid-tier pass)

Status: ready to riff. Separate co-authored pass — not the capability-chips PR (#48).

## The job

Bring the thin mid-tier CC plugin cards up to the depth the PR #42 cards landed at
(**355–435 chars**), written in your voice. You riff, I shape + lint (copy-reviewer
agent) + ship as **one PR**.

Targets (current desc length → target ~355–435):

| card | now | tagline? | why it's thin |
|---|---:|---|---|
| vibe-test | 262 | **none** | shortest card; strong hook buried, no tagline |
| vibe-taker | 263 | yes | concept's there, the *pain* isn't |
| vibe-thesis | 290 | yes | the novel bit (self-review guard) undersold |
| thesis-engine | 292 | yes | "opposing positions" angle not pulled |
| vibe-insights | 348 | yes | **stretch** — already near-depth, maybe just a tighten |

## How we run it

- **Async, riff-style.** Answer any or all in one pass — bullets, fragments,
  half-thoughts, all fine. You talk; I turn it into card copy; you approve.
- I never publish your raw riff verbatim unless it's already card-shaped. I shape
  it to the card grammar: tagline + a 355–435-char description.
- **Fact-safe:** I won't touch `{{fact}}` tokens, and `site-doctor --check` must pass
  before it ships. Tags stay as-is unless you say otherwise.

## The bar (voice anchors)

House rules: builder-to-builder, **second person**, sentence case. No
"empower / leverage / seamlessly / unlock / unleash." Em-dashes welcome. No emoji.

The shape that worked in PR #42 — three beats:
1. **What it does** (one tight clause).
2. **The specific thing it nails that other tools fumble** (the differentiator — concrete, not adjectives).
3. **Land it** — the feeling, the who-it's-for, or the dry kicker.

Model to match (vibe-sec, 424 chars, already deep): leads with the action, names the
exact gap it closes, lands on the posture. Don't copy it — match its *density*.

## The interview

For each card: the current floor, what's missing, and the riff prompts. Answer in
whatever order. One or two real sentences per prompt is plenty — I'll do the shaping.

---

### vibe-test  (262 → ~400)

> *Now:* "Reads your vibe-coded app, classifies maturity tier and deployment risk,
> generates the tests that actually matter. Catches the broken harnesses every other
> test tool assumes away — vitest configs silently reporting 0%, coverage tools
> cherry-picking denominators."

The broken-harness catch is the best hook on the card. Pull it forward, give it room.
Also: **no tagline** — every other card has one.

**Riff:**
1. The broken-harness catch — give me the real horror story. The "it said 0% and was
   lying to my face" moment.
2. "Tests that actually matter" — in your head, what's the line between a test worth
   writing and noise?
3. Testing *vibe-coded* code specifically: what's different about testing what an
   agent wrote vs. what you wrote?
4. Tagline candidates? (one line, the feeling — e.g. the dry "your coverage number
   was lying" energy)

---

### vibe-taker  (263 → ~400)

> *Now (tagline "Take it with you."):* "Move a feature between repos without
> copy-paste archaeology. Capture a feature out of one codebase as a portable bundle
> — architecture, contract, the prompts that built it, and the gotchas — then plant
> it into another repo with stack-aware adaptation. Local-only."

Concept's sharp. The *pain* it kills isn't on the card yet.

**Riff:**
1. "Copy-paste archaeology" — paint it. What does moving a feature the dumb way
   actually cost you, step by step?
2. Why ship "the prompts that built it" inside the bundle — what does that unlock
   that raw code alone doesn't?
3. Picture the person mid-task who reaches for this. What repo are they staring at,
   and what did they just give up trying to do by hand?

---

### vibe-thesis  (290 → ~400)

> *Now (tagline "Long-form research, drafted with discipline."):* "Scaffolds
> thesis-shaped projects — academic dissertation, master's thesis, long-form research
> article, position essay. Bootstraps the structure, runs a voice synthesis pass,
> guards against self-review tone, then renders to PDF, HTML, and a plain-language lay
> version. Built on ThesisStudio."

The self-review-tone guard is genuinely novel and it's listed like a footnote. Surface it.

**Riff:**
1. The self-review-tone guard — why does it exist? What does AI-drafted long-form get
   embarrassingly wrong without it?
2. "Drafted with discipline" — what discipline, exactly? What's the failure mode of
   just asking an LLM to write your thesis?
3. The plain-language lay version — who's that for, and why did you bother building it?

---

### thesis-engine  (292 → ~400)

> *Now (tagline "Surface topics. Gather sources. Seed the thesis."):* "Research feeder
> for Vibe Thesis. Surfaces cutting-edge topics in any domain, gathers primary sources,
> opposing positions, and methodological precedents — then emits a run folder that drops
> straight into ThesisStudio. Optional stage three adapts a seeded topic into a Smart
> Brevity blog draft."

The "opposing positions" auto-gather is an intellectual-honesty move worth naming out loud.

**Riff:**
1. Why gather *opposing* positions automatically — what does that protect the writer from?
2. The feeder → thesis handoff: what blank-page problem does this kill? What's the moment
   it saves?
3. Stage 3 (topic → blog draft) — is that the side door for ideas that aren't
   thesis-sized? How do you actually use it?

---

### vibe-insights  (348 → tighten, optional)

> *Now (tagline "The /insights you wish you had."):* "Cross-machine, work-walled Claude
> Code session analytics — the verbose /insights over every machine and your whole
> history. Coverage, where-was-I recall, token/cost with the cache reveal, trends,
> decisions, languages, per-session friction, and a synthesized read of how you actually
> work. Standalone engine; employer sessions stay walled and local."

Already near-depth. Only touch it if you want to.

**Riff (optional):**
1. The work-walling (employer sessions stay local) — is that the trust line that makes
   it shippable? Worth leading with, or keep it as the closer?

## Output per card

`tagline` (short — the feeling) + `description` (355–435 chars, the three-beat shape).
I draft → copy-reviewer lints → you approve → one PR, doctor-green.

## When you're ready

Drop your riffs (any subset, any format) and I'll draft the set. Or say "just vibe-test
first" and we'll do one as a calibration round before the rest.
