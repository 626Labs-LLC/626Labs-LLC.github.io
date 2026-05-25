---
title: vibe-walk builds the onboarding tour, and tells you when not to
published: 2026-05-24
product: vibe-walk
subtitle: A Claude Code plugin that reads your app, builds an instrumented spotlight tour you own, and is honest when a tour won't help.
tagline: Tours your users actually finish.
draft: false
---

The first five minutes decide whether a new user stays. vibe-walk builds the tour that walks them to the moment your product clicks. Just as important, it tells you when your app doesn't need one.

Point it at your app. It reads your user-facing surfaces, names the aha moment (the first time the product actually lands), and generates a spotlight tour you own outright: a Driver.js module, an anchor-injection codemod, and six analytics events. Same ownership model as shadcn. The generated code is yours from day one, with no runtime SDK and no vendor. And it measures the right thing: downstream activation, not a "tour completed" badge that means nothing.

The part most onboarding tools skip is the honest verdict. vibe-walk has a first-class don't-build output. If a guided tour genuinely won't help your app, it says so before you build one. Honesty about fit is a feature, not a disclaimer.

v0.1.0 ships walkthrough mode for the web, MIT licensed, with 197 tests behind it and a dogfooding run against the Celestia3 web app. Install it from the Vibe Plugins marketplace:

`/plugin marketplace add estevanhernandez-stack-ed/vibe-plugins`
`/plugin install vibe-walk@vibe-plugins`

See it at 626labs.dev/vibe-walk/.
