# Launch Announcer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repo-local `/announce <product>` Claude Code skill that turns a shipped 626 Labs product into launch copy for three targets — a site Field Note (written into `content/stories/`), an X/Twitter draft, and a Discord draft (both draft-only).

**Architecture:** A markdown-only skill (no scripts, no auto-posting). `SKILL.md` carries the flow; `references/templates.md` carries the three output shapes; `references/voice.md` carries per-channel register + emoji policy. The skill instructs the agent to read `content/site.json` for product facts, read `SHIELDS_RELEASE` from `scripts/render-hub.py` for release-repo resolution, run `gh` for release notes, then write the three outputs. Release sourcing reuses the monorepo mapping so it never drifts from the badge system.

**Tech Stack:** Claude Code skill (SKILL.md + references), `gh` CLI, the repo's existing Field Notes pipeline (`scripts/render-hub.py` → `discover_stories`).

**Note on testing:** This is a SKILL, not executable code — there are no unit tests. Each task's verification is a concrete inspection (file contents, frontmatter validity) or a `/announce` dry-run against a real product. Two products anchor the verification: `vibe-taker` (has a published GitHub Release → full path) and `celestia-3` (no Release → graceful-degrade path).

**Spec:** `docs/superpowers/specs/2026-05-21-launch-announcer-design.md`

---

## File structure

```
.claude/skills/announce/
  SKILL.md                  # frontmatter + when-to-use + the 5-step flow +
                            # error handling. References the two files below.
  references/
    templates.md            # the three output shapes (Field Note, X, Discord)
                            # with one worked example each
    voice.md                # per-channel register + the emoji policy table
```

Produced per run (not committed by the skill — the user reviews/commits):
```
content/stories/<YYYY-MM-DD>-<id>-launch.md     # live site Field Note (draft:false)
docs/announcements/<YYYY-MM-DD>-<id>/x.md       # X draft (manual post)
docs/announcements/<YYYY-MM-DD>-<id>/discord.md # Discord draft (manual post)
```

Responsibilities are split so `SKILL.md` stays scannable (behavior), `templates.md` holds the exact output skeletons (what to produce), and `voice.md` holds the tone rules (how to write). Files that change together live together.

---

## Task 1: Skill scaffold — frontmatter + when-to-use

**Files:**
- Create: `.claude/skills/announce/SKILL.md`

- [ ] **Step 1: Write the SKILL.md frontmatter + when-to-use block**

```markdown
---
name: announce
description: Draft launch announcements for a 626 Labs product across three targets — a site Field Note (written to content/stories/), an X/Twitter draft, and a Discord draft. Use when the user says "/announce", "announce <product>", "launch post for X", "write the launch copy", or wants go-to-market copy for a shipped product. Reads content/site.json + the product's latest GitHub release. Repo-local to 626labs-hub.
---

# Announce — launch copy for a 626 Labs product

Turn a shipped product into go-to-market copy in one move. Given a product,
draft a site Field Note (written into the repo), plus X and Discord drafts
(draft-only — the user posts them).

## When to use

- `/announce <product>` where `<product>` is a product `id` from
  `content/site.json` (e.g. `vibe-taker`, `celestia-3`, `vibe-test`).
- The user asks for "launch copy", "announcement", "launch post" for a
  shipped product.

## When NOT to use

- Long-form retrospectives — that's a hand-written Field Note, not a launch.
- Anything that posts to X/Discord automatically — this skill drafts only.
```

- [ ] **Step 2: Verify the skill is discoverable**

Run: `python -c "import pathlib,re; t=pathlib.Path('.claude/skills/announce/SKILL.md').read_text(encoding='utf-8'); assert t.startswith('---'); assert 'name: announce' in t; assert 'description:' in t; print('frontmatter OK')"`
Expected: `frontmatter OK`

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/announce/SKILL.md
git commit -m "feat(announce): skill scaffold + frontmatter"
```

---

## Task 2: The flow — product resolution + release sourcing

**Files:**
- Modify: `.claude/skills/announce/SKILL.md` (append the flow section)

- [ ] **Step 1: Append the resolution + sourcing flow to SKILL.md**

````markdown
## Flow

### 1. Resolve the product

Read `content/site.json`. Find the entry in `products[]` whose `id` equals
`<product>`. Pull: `title`, `tagline`, `description`, `repo`, `install`,
`productPage`, `liveUrl`, `tags`, `npm`, `anthropicApproved`. This is the
canonical product copy — never invent product facts.

If `<product>` is missing or matches nothing, list the available ids from
`products[]` and ask the user to pick. Do not guess.

### 2. Source the release notes

shields.io / GitHub Releases are the source for "what's new". Resolve the
release repo with the **same mapping the badge system uses** so the two
never drift — read the `SHIELDS_RELEASE` dict from `scripts/render-hub.py`
and apply this order:

1. If the product `id` is a key in `SHIELDS_RELEASE`:
   - if that entry has `hide: true` (e.g. `vibe-sec`), there is no release —
     go straight to degrade (step 2c).
   - else use its `repo` + `filter` (e.g. `vibe-test` → repo
     `estevanhernandez-stack-ed/vibe-plugins`, filter `vibe-test-v*`).
2. Else if the product's `repo` is `estevanhernandez-stack-ed/vibe-plugins`,
   use that repo with filter `<id>-v*`.
3. Else use the product's own `repo`, latest release.

Fetch with `gh`:

- No filter:
  `gh release view --repo <repo> --json tagName,name,body,publishedAt,url`
- With a `<prefix>-v*` filter:
  `gh release list --repo <repo> --json tagName,name,publishedAt -L 30`,
  pick the newest tag starting with `<prefix>`, then
  `gh release view <tag> --repo <repo> --json tagName,name,body,publishedAt,url`

**2c. Graceful degrade (common today):** if no matching release exists
(e.g. `celestia-3`, `vibe-sec`, or any product with tags but no published
Release), draft from `site.json` copy alone, omit the "what's new" section,
and say so in the closing summary. A missing release is expected, not an error.
If the repo is private or missing, skip the fetch and note it.
````

- [ ] **Step 2: Verify the SHIELDS_RELEASE source still exists and is shaped as referenced**

Run: `python -c "import re,pathlib; s=pathlib.Path('scripts/render-hub.py').read_text(encoding='utf-8'); assert 'SHIELDS_RELEASE = {' in s; assert 'vibe-test' in s and 'vibe-sec' in s and 'hide' in s; print('SHIELDS_RELEASE present')"`
Expected: `SHIELDS_RELEASE present`

- [ ] **Step 3: Verify the gh commands run for both paths**

Run (monorepo path): `gh release list --repo estevanhernandez-stack-ed/vibe-plugins --json tagName -L 30`
Expected: JSON including a tag starting `vibe-test-v` (e.g. `vibe-test-v0.2.3`).

Run (standalone path): `gh release view --repo estevanhernandez-stack-ed/vibe-taker --json tagName,name`
Expected: JSON with `tagName` `v0.1.1` (or newer).

Run (degrade path): `gh release view --repo estevanhernandez-stack-ed/Celestia3 --json tagName`
Expected: non-zero exit / "release not found" — confirms the degrade branch is exercised by `celestia-3`.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/announce/SKILL.md
git commit -m "feat(announce): product resolution + release sourcing flow"
```

---

## Task 3: Output templates reference

**Files:**
- Create: `.claude/skills/announce/references/templates.md`

- [ ] **Step 1: Write the three output templates**

````markdown
# Announce — output templates

Three files per run. Site Field Note is written live into the repo; X and
Discord are draft-only.

## 1. Site Field Note → `content/stories/<YYYY-MM-DD>-<id>-launch.md`

Frontmatter must match the Field Notes pipeline
(`scripts/render-hub.py` → `parse_story_frontmatter`): simple key/value
pairs, no nested objects. `draft: false` so it publishes on the next
render+push (nothing goes live until the user commits + pushes).

```markdown
---
title: <Launch headline — punchy, specific>
published: <YYYY-MM-DD>
product: <Product display name>
subtitle: <one sentence: what it does for whom>
tagline: <short kicker, optional>
draft: false
---

<2–5 short paragraphs, essay/working register, NO emoji. Punchline first:
lead with what shipped and why it matters. If release notes exist, fold the
1–3 highlights in as prose, not a changelog dump. Close with the install or
"Start free" line and the link. On-brand: no "empower / leverage /
seamlessly / unlock". Em-dashes welcome.>
```

## 2. X / Twitter → `docs/announcements/<YYYY-MM-DD>-<id>/x.md`

```markdown
# X / Twitter draft — <Product>

## Primary post (<=280 chars)
<hook + what it is + install/link. Sparing emoji allowed.>

## Thread (optional — only if release notes are rich)
1/ <hook>
2/ <what's new / the differentiator>
3/ <install command + link + CTA>
```

## 3. Discord → `docs/announcements/<YYYY-MM-DD>-<id>/discord.md`

```markdown
# Discord draft — <Product>

**<Product> <version> is live** <emoji ok>

<conversational what's-new, release-drop energy. Bold the headline,
bullet the highlights. Emoji welcome.>

Install: `<install command from site.json>`
<link to productPage / liveUrl / repo>
```
````

- [ ] **Step 2: Verify the Field Note frontmatter keys match the pipeline**

Run: `python -c "import re,pathlib; s=pathlib.Path('scripts/render-hub.py').read_text(encoding='utf-8'); [print('has',k) for k in ['title','published','product','subtitle','tagline','draft'] if k in s]"`
Expected: prints `has title`, `has published`, `has product`, `has subtitle`, `has tagline`, `has draft` — confirming every key the template uses is one the renderer reads.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/announce/references/templates.md
git commit -m "feat(announce): output templates for site/X/Discord"
```

---

## Task 4: Voice + emoji policy reference

**Files:**
- Create: `.claude/skills/announce/references/voice.md`

- [ ] **Step 1: Write the voice + emoji rules**

```markdown
# Announce — voice + emoji policy

Voice follows the CODER VOICE SYNTHESIS block in `~/.claude/CLAUDE.md`:
punchline-first, specific over generic, em-dashes, zero corporate speak,
no hedging.

## Per-channel register

- **Site Field Note** — essay/working register, on-brand, no emoji.
- **X / Twitter** — tight marketing register, hook + install + link.
- **Discord** — casual release-drop energy; the wells (30 Rock / Office)
  are fair game when a beat genuinely fits.

## Emoji policy (launch caveat to the brand rule)

The 626 Labs brand rule is "no emoji in UI copy or marketing surfaces."
Launch announcements carry a documented caveat:

| Channel | Emoji |
|---|---|
| Site Field Note | None — the site is the brand surface; rule holds. |
| X / Twitter | Sparing — a light emoji or two is allowed. |
| Discord | Welcome — Discord chat is its own register. |
```

- [ ] **Step 2: Wire the references into SKILL.md**

Append to `.claude/skills/announce/SKILL.md`:

```markdown
## References

- `references/templates.md` — the exact shape of each of the three outputs.
- `references/voice.md` — per-channel register + the emoji policy.

Read both before drafting.
```

- [ ] **Step 3: Verify the references resolve**

Run: `python -c "import pathlib; [print('ok',p) for p in ['.claude/skills/announce/references/templates.md','.claude/skills/announce/references/voice.md'] if pathlib.Path(p).exists()]; assert 'references/templates.md' in pathlib.Path('.claude/skills/announce/SKILL.md').read_text(encoding='utf-8')"`
Expected: prints `ok` for both reference files (and no assertion error).

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/announce/references/voice.md .claude/skills/announce/SKILL.md
git commit -m "feat(announce): voice + emoji policy reference"
```

---

## Task 5: Output-writing flow + closing summary

**Files:**
- Modify: `.claude/skills/announce/SKILL.md` (append the write + close section)

- [ ] **Step 1: Append the write/output section to SKILL.md**

````markdown
### 3. Draft all three

Read `references/templates.md` and `references/voice.md`. Draft the Field
Note, the X copy, and the Discord copy in their respective registers.

### 4. Write the files

- Site Field Note → `content/stories/<YYYY-MM-DD>-<id>-launch.md`.
  If that file already exists, warn before overwriting.
- X draft → `docs/announcements/<YYYY-MM-DD>-<id>/x.md`.
- Discord draft → `docs/announcements/<YYYY-MM-DD>-<id>/discord.md`.

Use today's date (`date +%F`) for `<YYYY-MM-DD>` and the product `id` for
`<id>`.

### 5. Close

Report, in chat: the three file paths, a 2-line summary, and the next
action (review the Field Note, commit + push to publish it, paste the X and
Discord drafts). Do NOT paste the full copy back into chat — the files are
the deliverable.
````

- [ ] **Step 2: Verify the full SKILL.md reads coherently end-to-end**

Run: `python -c "import pathlib; t=pathlib.Path('.claude/skills/announce/SKILL.md').read_text(encoding='utf-8'); [print('has section:',h) for h in ['## When to use','## Flow','### 1. Resolve','### 2. Source','### 3. Draft','### 4. Write','### 5. Close','## References'] if h in t]"`
Expected: prints all eight section markers.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/announce/SKILL.md
git commit -m "feat(announce): output-writing flow + closing summary"
```

---

## Task 6: End-to-end dry run (degrade path + full path)

**Files:**
- None created by this task (it exercises the skill and inspects outputs).

- [ ] **Step 1: Run the degrade path — `/announce celestia-3`**

Invoke the skill: `/announce celestia-3`.
Expected: it resolves `celestia-3` from `site.json`, finds no GitHub Release
(degrade), and writes three files. Verify:

Run: `ls docs/announcements/$(date +%F)-celestia-3/ && head -8 content/stories/$(date +%F)-celestia-3-launch.md`
Expected: `x.md` and `discord.md` exist; the Field Note opens with valid
frontmatter (`title`, `published`, `product`, `draft: false`) and no emoji.

- [ ] **Step 2: Verify the degrade Field Note renders through the pipeline**

Run: `python scripts/render-hub.py --check`
Expected: either "up to date" (if not yet rendered) or a drift notice naming
`index.html` — confirming `discover_stories` accepts the new Field Note's
frontmatter (no parse error/traceback). If it reports drift, that is fine —
it means the story was discovered; do NOT commit the render here.

- [ ] **Step 3: Run the full path — `/announce vibe-taker`**

Invoke: `/announce vibe-taker`.
Expected: resolves `vibe-taker`, fetches its latest Release (`v0.1.1`),
folds the release highlights into all three drafts. Verify:

Run: `grep -i "v0.1.1\|capture\|plant" docs/announcements/$(date +%F)-vibe-taker/discord.md`
Expected: the Discord draft references the version and/or the feature verbs.

- [ ] **Step 4: Verify the emoji policy held**

Run: `python -c "import pathlib,glob; f=glob.glob('content/stories/*-celestia-3-launch.md')[0]; t=pathlib.Path(f).read_text(encoding='utf-8'); import re; assert not re.search(r'[\U0001F300-\U0001FAFF☀-➿]', t), 'site Field Note must be emoji-free'; print('site emoji-free OK')"`
Expected: `site emoji-free OK`.

- [ ] **Step 5: Clean up the dry-run artifacts (they were just a test)**

```bash
rm -rf docs/announcements/$(date +%F)-celestia-3 docs/announcements/$(date +%F)-vibe-taker
rm -f content/stories/$(date +%F)-celestia-3-launch.md content/stories/$(date +%F)-vibe-taker-launch.md
git checkout -- index.html 2>/dev/null || true
```
Expected: working tree clean of dry-run files (the skill itself stays committed).

- [ ] **Step 6: Final commit (skill only — no run artifacts)**

```bash
git add .claude/skills/announce
git commit -m "feat(announce): verified end-to-end (degrade + full paths)" --allow-empty
```

---

## Self-review notes

- **Spec coverage:** product resolution (Task 2), release sourcing + monorepo
  mapping + degrade (Task 2), three outputs with exact paths (Tasks 3, 5),
  Field Notes reuse (Task 3), per-channel emoji policy + caveat (Task 4),
  voice (Task 4), error/edge handling — unknown id (Task 2), no release
  (Task 2/6), overwrite warning (Task 5), output-discipline closing summary
  (Task 5). Out-of-scope items (auto-post, new section, scripts, plugin
  extraction) are intentionally absent.
- **Naming consistency:** `SHIELDS_RELEASE` (matches `scripts/render-hub.py`),
  `<id>` for the product id throughout, `content/stories/<date>-<id>-launch.md`
  and `docs/announcements/<date>-<id>/{x,discord}.md` paths identical across
  Tasks 3, 5, 6.
- **No placeholders:** every SKILL.md / reference block is the actual content
  to write, not a description of it.
