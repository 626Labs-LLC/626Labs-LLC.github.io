# Discord draft — vibe-walk

**vibe-walk v0.1.0 is live** 👣

New Claude Code plugin: point it at your app and it builds the onboarding tour that walks new users straight to the moment your product clicks.

- 🔍 reads your surfaces and names the aha moment — the first time it actually lands
- 🛠️ drops in a Driver.js spotlight tour you own outright (shadcn-style — the generated code is yours, no runtime SDK)
- 📊 anchor-injection codemod + 6 analytics events that track downstream **activation**, not a meaningless "tour completed"
- 🧭 honest about fit: if a tour won't help your app, it tells you *before* you build one
- ✅ 197 tests, dogfooded against the Celestia3 webapp

Install (stable, via the Vibe Plugins marketplace):
```
/plugin marketplace add estevanhernandez-stack-ed/vibe-plugins
/plugin install vibe-walk@vibe-plugins
```

Full rundown → https://626labs.dev/vibe-walk/
