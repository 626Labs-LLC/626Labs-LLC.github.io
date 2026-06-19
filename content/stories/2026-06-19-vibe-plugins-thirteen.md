---
title: "The Vibe family is thirteen, and they all read the code first"
subtitle: "Thirteen Claude Code plugins on one shared spine — an opinionated agent that reads your repo before it touches it. They cover the whole lifecycle around the code, where vibe-coded apps actually rot."
tagline: "AI ships code fast. The lifecycle around it is where things rot. Thirteen plugins, one spine, the whole arc from idea to maintained."
published: 2026-06-19
author: "Este Hernandez"
draft: false
---

<p>AI will write you a working app in an afternoon. It will not keep it alive. The code is the easy part now — the lifecycle <em>around</em> the code is where a vibe-coded afternoon turns into a thing nobody can ship to real users. Scoping it. Documenting it. Testing it. Securing it. Auditing the prompts it ships. Deciding what to build next. That is the surface that rots, quietly, while the demo still runs.</p>

<p>The Vibe family is the answer to that rot. <strong>Thirteen Claude Code plugins</strong> on one shared spine: an opinionated agent that reads the code before it touches it. No plugin guesses. Each one reads your repo first, then acts on what is actually there — not on a template, not on what a generic scaffolder assumes you wrote. That single rule is the whole thesis. Everything else is the arc.</p>

<h2>From idea to shipped</h2>

<p><strong>Vibe Cartographer</strong> takes an idea to a running app through a build chain you can actually follow — onboard, scope, PRD, spec, checklist, build, iterate, reflect. It sits at Level 3.5 of the maturity ladder: not a one-shot generator, not a fully autonomous fleet you can't steer, but a sequenced run with you holding the wheel at the seams. Before the agent writes a line, <strong>Vibe Keystone</strong> maps the repo and drafts the CLAUDE.md — the load-bearing file every later decision rests on. The agent that reads first needs something to read; Keystone writes it.</p>

<p>Then the documentation nobody volunteers to write. <strong>Vibe Doc</strong> finds the docs you are missing and writes them from what is already in the repo — not invented prose, the actual shape of your code described back to you. Idea became app. App is now legible.</p>

<h2>The part that keeps it alive</h2>

<p>Shipped is not done. <strong>Vibe Test</strong> classifies your project's maturity and deployment risk, generates the tests that matter for where you actually are, and catches the broken harness — the one cheerfully reporting 0% coverage while you think you're covered. <strong>Vibe Sec</strong> audits twelve security concerns, calibrated to your tier so a weekend prototype isn't held to a fintech bar. From there it writes the fix, builds a STRIDE threat model, and drops a CI gate so the hole stays closed. <strong>Vibe Prompt</strong> — the thirteenth, and the newest — turns the same lens on the prompts your app ships: structural smells plus a behavioral eval run against your actual production model, because a prompt that reads clean can still misbehave on the model you deploy.</p>

<p><strong>Vibe Walk</strong> builds the onboarding tour your users actually finish, and is honest when a tour won't help — it has a first-class don't-build verdict, and now ships an accessibility contract so the tour you generate isn't one keyboard users can't use. <strong>Vibe Iterate</strong> decides what to build next after ship, reading competitors and your own backlog, and now understands .NET and NuGet repos, not just JS and TS. <strong>Vibe Wrap</strong> closes the session — it writes the wrap-up from the breadcrumb trail the rest of the toolkit already left, so the handoff costs you nothing.</p>

<p>And the long tail of real work: <strong>Vibe Taker</strong> lifts a feature out of one repo as a portable bundle and plants it in another — all on your machine, no cloud round-trip. <strong>Vibe Thesis</strong> and its <strong>Thesis Engine</strong> carry long-form research, drafted with discipline instead of vibes. <strong>Vibe Insights</strong> is the retrospective that crosses machines — where you left off, what burned tokens, what you actually shipped, stitched across every place you work.</p>

<h2>Why now</h2>

<p>The family did not arrive thirteen-strong. It got there. On June 9, nearly every plugin cut a release in a single day — the kind of wave that only happens when a standard ratifies across the whole set at once. A model-tiering convention landed family-wide, so every plugin now picks the right model for the job instead of each one guessing. Vibe Sec climbed to twelve concerns. Vibe Walk shipped its accessibility contract. Vibe Iterate opened the .NET lane. And Vibe Prompt earned its place as the thirteenth, because the prompts your app ships are code too, and code gets audited.</p>

<p>That is the shape: one spine, the full arc from idea to maintained, and a release cadence that tightens the family instead of just adding to it. The agents read first. Everything good follows from that.</p>

<p>Install the whole family from the Vibe Plugins marketplace:</p>

<p><code>/plugin marketplace add estevanhernandez-stack-ed/vibe-plugins</code></p>

<p>Imagine Something Else.</p>
