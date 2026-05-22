# Announce — output templates

Three files per run. The site Field Note is written live into the repo; X
and Discord are draft-only.

## 1. Site Field Note → `content/stories/<YYYY-MM-DD>-<id>-launch.md`

Frontmatter must match the Field Notes pipeline
(`scripts/render-hub.py` → `parse_story_frontmatter`): simple key/value
pairs, no nested objects. `draft: false` so it publishes on the next
render + push (nothing goes live until the user commits + pushes).

```markdown
---
title: <Launch headline — punchy, specific>
published: <YYYY-MM-DD>
product: <Product display name>
subtitle: <one sentence: what it does, for whom>
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

<conversational what's-new, release-drop energy. Bold the headline, bullet
the highlights. Emoji welcome.>

Install: `<install command from site.json>`
<link to productPage / liveUrl / repo>
```
