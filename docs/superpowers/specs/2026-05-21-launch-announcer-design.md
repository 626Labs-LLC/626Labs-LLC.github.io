# Launch Announcer — design spec

- **Date:** 2026-05-21
- **Status:** Approved (design); pending implementation plan
- **Repo:** 626Labs-LLC/626Labs-LLC.github.io (626labs-hub)
- **Author:** The Architect + Este

## Purpose

Turn a shipped product into go-to-market copy in one move. Given a product,
`/announce <product>` reads `content/site.json` plus the product's latest
GitHub release and drafts launch announcements for three targets — the
626labs.dev site (as a Field Note), X/Twitter, and Discord — in Este's voice.

This fills the gap in the existing toolkit: `626labs:design` makes assets,
`626labs:publishing` / `thesis-engine:blog` write long-form, the repo's
`copy-reviewer` / `visual-asset-reviewer` agents do quality control — but
nothing converts a release into launch copy. Announcer is the first of an
eventual set of marketing skills (ship-to-site pipeline, release→Field Note,
SEO/meta audit are queued for later).

## Form factor

- **Repo-local skill** at `.claude/skills/announce/SKILL.md` in 626labs-hub.
- **No scripts** — the skill drives the agent to read `site.json`, run `gh`,
  and write files. (A helper script can come later if the flow proves it
  needs one. YAGNI for v1.)
- Authored cleanly enough to lift into a portable `626-market` plugin later
  if cross-repo reuse is wanted. Not generalized now (premature — it is
  coupled to this repo's `site.json` schema + Field Notes pipeline).

## Invocation + product resolution

- `/announce <product>` where `<product>` is a product `id` from
  `content/site.json` (e.g. `vibe-taker`, `celestia-3`, `vibe-test`).
- Missing or ambiguous arg → the skill lists the available `site.json`
  product ids and asks the user to pick. No guessing.
- All editorial content (title, tagline, description, repo, install,
  productPage, tags, npm, anthropicApproved) is read from that one entry.
  `site.json` stays the single source of truth — the announcer never
  invents product facts.

## Release sourcing

- Fetch the latest **published GitHub Release** for the product via `gh`
  (already authenticated in this environment).
- **Monorepo handling:** release location is resolved with the **same
  mapping the badge system uses** (`SHIELDS_RELEASE` in
  `scripts/render-hub.py`), so the announcer and the release badges always
  point at the same source of truth. Resolution order:
  1. If the product is in the `SHIELDS_RELEASE` override (e.g. `vibe-test` →
     repo `estevanhernandez-stack-ed/vibe-plugins`, filter `vibe-test-v*`;
     `vibe-sec` → suppressed), use that repo + prefix. Note this is needed
     because a product's `site.json` `repo` can differ from where its
     Releases live — `vibe-test`'s `repo` is the standalone repo, but its
     published Releases are in the monorepo.
  2. Else if the product's `site.json` `repo` is `vibe-plugins`, filter the
     monorepo by `<id>-v*`.
  3. Else query the product's own `repo` for its latest release.

  The implementation should read this mapping from one place (shared with or
  copied from `SHIELDS_RELEASE`) so the two never drift.
- **Graceful degradation (the common case today):** many products have tags
  but no published Release, or no release anywhere (e.g. `celestia-3`,
  `vibe-sec`, `vibe-iterate`). When no release is found, the announcer drafts
  from `site.json` copy alone, omits the "what's new" section, and flags in
  its summary that there were no release notes. Degrade is expected, not an
  error.
- Private/missing repo → skip the release fetch, note it, continue from
  `site.json`.

## Outputs — three targets, three registers

### 1. Site (626labs.dev) — Field Note

- Written **directly into the repo** at
  `content/stories/<YYYY-MM-DD>-<product>-launch.md` (commit-ready).
- `draft: false` — nothing publishes until Este commits + pushes (the render
  pipeline only runs on push; the file is inert until then). The skill does
  **not** auto-commit.
- Frontmatter matches the existing Field Notes pipeline
  (`scripts/render-hub.py` → `parse_story_frontmatter`):
  ```yaml
  ---
  title: <launch headline>
  published: <YYYY-MM-DD>
  product: <product display name>
  subtitle: <one-line>
  tagline: <short kicker>
  draft: false
  ---
  ```
- Body: launch-flavored Field Note in essay/working register, on-brand,
  **no emoji** (the site is the brand surface). Punchline-first, specific,
  em-dashes welcome — per the CODER VOICE SYNTHESIS in `~/.claude/CLAUDE.md`.
- If a `content/stories/` file for this product+date already exists, warn
  before overwriting.

### 2. X / Twitter — draft only

- Written to `docs/announcements/<YYYY-MM-DD>-<product>/x.md` (staging; Este
  copies and posts manually).
- One primary post (≤ 280 chars) + an optional 2–4-post thread when release
  notes are rich enough to justify it.
- Includes the install command and a link (productPage or 626labs.dev).
- Marketing register, tight, builder-to-builder.
- **Emoji:** sparing emoji allowed (see Emoji policy below).

### 3. Discord — draft only

- Written to `docs/announcements/<YYYY-MM-DD>-<product>/discord.md` (staging;
  Este posts to the announce channel).
- Release-drop energy for the 626 Labs Discord (the planned release/update
  channel). What's-new (from release notes when present) + install + links.
- Conversational, formatted for a Discord announcement (bold, line breaks).
- **Emoji:** emoji welcome (see Emoji policy below).

The skill closes with file paths + a 2-line summary + the next action
(review, commit the Field Note, paste the social drafts) — never the full
copy pasted back into chat. Honors the output-token-discipline rule.

## Emoji policy (per-channel)

The 626 Labs brand rule is "no emoji in UI copy or marketing surfaces."
This skill carries a **documented launch caveat**:

| Channel | Emoji |
|---|---|
| Site Field Note | None — the site is the brand surface, rule holds. |
| X / Twitter | Sparing — a light emoji or two is allowed for launch posts. |
| Discord | Welcome — Discord chat is its own register. |

The caveat lives in the skill's voice rules. Optionally reflect the same
exception in the repo `CLAUDE.md` / `626labs-design` voice notes so the
brand rule and the skill agree (offer; not required for v1).

## Voice

Driven by the `CODER VOICE SYNTHESIS` block in `~/.claude/CLAUDE.md`:
punchline-first, specific over generic, em-dashes, zero corporate speak,
no hedging. Working/marketing register for X and the Field Note; the
casual/Discord register (wells welcome — Liz/Jack/Tracy beats) for Discord
when the moment fits.

## Error handling + edges

- Unknown / ambiguous product id → list `site.json` ids, ask.
- No published release → draft from `site.json`, omit "what's new", flag it.
- Private/missing repo → skip release fetch, note it.
- Re-run same day → overwrite the dated `docs/announcements/` folder; warn
  if the `content/stories/` Field Note already exists before overwriting.

## File / structure layout

```
.claude/skills/announce/
  SKILL.md            # the skill: flow, voice rules, emoji policy,
                      # monorepo release map, frontmatter + X/Discord templates

# produced per run:
content/stories/<date>-<product>-launch.md          # live site Field Note
docs/announcements/<date>-<product>/x.md            # X draft (manual post)
docs/announcements/<date>-<product>/discord.md      # Discord draft (manual post)
```

## Out of scope (v1)

- No auto-posting to X or Discord (no API keys, no webhooks, no stored secrets).
- No new on-site section — reuses the Field Notes pipeline.
- No helper scripts — skill-driven only.
- No portable plugin extraction — repo-local first.
- The other queued marketing skills (ship-to-site pipeline, release→Field
  Note, SEO/meta audit) are separate, later specs.

## Future (not now)

- Extract to a `626-market` plugin for cross-repo reuse once the pattern proves out.
- Optional auto-post to the Discord announce channel via webhook (its own spec,
  its own secret handling).
