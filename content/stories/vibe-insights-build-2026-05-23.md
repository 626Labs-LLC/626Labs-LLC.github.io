---
id: vibe-insights-build-2026-05-23
product: vibe-insights
title: "I complained that /insights wasn't insightful. Seven hours later I had a plugin that beats it."
subtitle: "It grabs insights from every Claude Code building surface you use, walls work from personal, and can even tell you the story of how it got built."
published: 2026-05-23
tagline: "42 commits, 60 tests, 280 sessions analyzed. Twice, the win was verification catching what the tests couldn't."
draft: false
---

# I complained that `/insights` wasn't insightful. Seven hours later I had a plugin that beats it.

*A build story, drafted by vibe-insights from its own commit spine + decision log on 2026-05-23. Voice: mine.*

**The one-liner:** This tool grabs insights from all of your Claude Code building surfaces and can even tell you a story. Cross-machine, work-walled, installable. Two new private repos, 42 commits, 60 tests, one sleeping baby's worth of checking in between increments.

---

## It started as a complaint

I ran `/insights`. It read one config home, on one machine, over a recent window, and I run two accounts across two machines with history back to January. The report was fine. It just wasn't *mine*.

The actual question underneath: **how do I get my other PC's context here?** Two machines feet apart, both on the tailnet, and no shared brain. That's where it began.

## The reframe that unlocked it

The first instinct was "keep work and personal separate." Wrong frame. **Separation lives in the credentials, not the transcripts.** The logs are just JSONL. So you don't merge homes; you *read across* them and tag each session by account and machine. Billing stays clean; the brain gets the whole picture.

That reframe turned a config headache into a one-evening engine.

## The build (15:24 → 15:54, thirty minutes)

Spec → plan → subagent-driven TDD. One implementer subagent per task, two-stage review, fresh context each time. Phase 1 (the deterministic index engine, walled work, coverage + recall) landed in **thirty minutes of wall clock**. Reused Sanduhr's `cc_logs` token math via an extracted `cc-logs` package, so the two tools' burn numbers *can't* drift.

It's Wednesday, Lemon.

## Then the real-data smoke test earned its keep

The unit tests were green. The real run said 57 sessions when I knew there were ~179. The synthetic fixtures used the shallow on-disk layout; **real Claude Code nests subagent transcripts four levels deep**, and the one-level walk silently missed 70% of the files. Caught it, made discovery recursive across both repos, folded subagent burn into its parent session. The fixtures lied; the real data told the truth.

## The original goal, delivered

Syncthing over the tailnet, per-machine indexes, a structural wall (work never leaves its origin box). The merge lit up: **nebuchadnezzar's 75 sessions joined dunder's** in one report. The two machines finally shared a brain, the thing I'd wanted at hour zero.

## "Not as insightful as I expected"

Fair. So I went at the native report's actual depth: not more counting, but **per-session judgment**. An LLM tags each session for friction, satisfaction, outcome; deterministic charts roll it up. The standout finding: **env/tooling friction is ~44% of judged sessions**, the *exact* #1 the native `/insights` flagged, arrived at independently from my own data. Two analyses, one verdict.

The hidden number the flat report buried: **22.8 billion cache-read tokens** carrying 96% of input-side context. The headline burn is the small number.

## A wrong assumption, caught by instinct

The report showed dunder smaller than neb. That contradicted reality. Root cause: the wall was per-*home*, and `.claude` was a mixed pre-split history. Half my personal 626Labs work was buried in the "work" pile. Moved the wall to per-*repo*. dunder's personal jumped 58 → 119, exactly where it belonged. The wall was never about secrecy; it's about not burning work quota on personal, so everything's *viewable*, just labeled.

## The verge

Packaged it as an installable Claude Code plugin: manifest, skills layout, validator green. Then pointed my own iteration plugin at it and shipped four more features in a row: the native-grade charts, R4 polish, response-time, cross-project decisions.

## What it cost, what it is

- **42 commits** (15:24 → 22:53), **60 tests**, two private repos.
- **280 sessions** analyzed · **144M tokens** of burn · **22.8B** cache reads.
- A report with a synthesized read up top, then coverage, recall, token/cost, trends, pick-this-back-up, decisions, languages, and per-session how-it-went.

## The meta

The process is the product: spec → subagent-TDD → verify on real data → iterate. Twice, the win was *verification catching what the tests couldn't*: the recursive-discovery miss and the buried-personal split. And the tool now closes the loop: it holds every project's spine (sessions, decisions, friction, timeline) so it can draft the build story itself. This post is the proof.

Imagine something else.

Este · 626 Labs
