# 626 Labs Hub — Vibe Ecosystem Content Briefing

**Generated:** 2026-04-17
**Purpose:** Single source of truth for everything an agent needs to update `index.html` with current Vibe plugins / framework / stats information. Start a fresh Claude Code session in `c:/Users/estev/Projects/626labs-hub/` and point the agent at this file to drive the edit.

---

## What the hub is

- **Repo:** `github.com/626Labs-LLC/626Labs-LLC.github.io`
- **Deploy:** auto via GitHub Pages → serves at **626labs.dev**
- **Files:** `index.html` (main hub), `sanduhr/` subpage, `logo.png`, `favicon.png`, `CNAME`, `.nojekyll`
- **Current state of `index.html`:** already has a `<section class="products">` with 5 cards — Sanduhr (flagship), Vibe Cartographer, Vibe Doc, Vibe Test (coming soon), Vibe Sec (coming soon). Structure is good. Needs fresh info + a few additions.

---

## Design system (already in index.html — honor it)

**CSS variables at the top of index.html. Reuse these — don't introduce new colors.**

```
--navy-deep: #0f182b
--navy-mid:  #162033
--navy-hi:   #1a2540
--navy-line: #2a3a5c
--cyan:      #3bb4d9    ← primary accent, badges, CTAs
--cyan-pale: #7ae0f5    ← link hover
--magenta:   #e13aa0    ← flagship/attention
--text:      #e8f2ff
--text-sec:  #a8c2d9
--text-dim:  #6a849e
--text-mute: #4a5f7a
--ok:        #4ade80    ← success/shipping indicator
--warn:      #fb923c
```

**Font:** system stack (`-apple-system, BlinkMacSystemFont, "Segoe UI Variable", "Segoe UI", Roboto, ...`).
**Background:** `radial-gradient(ellipse at top, var(--navy-hi), var(--navy-deep) 70%)`.
**Header:** glass morphism — `backdrop-filter: blur(18px) saturate(140%)`, `rgba(15,24,43,0.72)` bg.
**Style philosophy:** clean, high-contrast, dark-themed, muted palette, clear information hierarchy. Builder voice. Never corporate.

---

## The Vibe Ecosystem — current state (2026-04-17)

### Shipped plugins

| Plugin | npm package | Current version | Weekly downloads | Repo |
|--------|------------|-----------------|------------------|------|
| **Vibe Cartographer** | `@esthernandez/vibe-cartographer` | **1.5.0** (shipped 2026-04-17) | **631** (up from 201 yesterday — 3.1× jump after 1.5.0) | [`vibe-cartographer`](https://github.com/estevanhernandez-stack-ed/vibe-cartographer) |
| **Vibe Doc** | `@esthernandez/vibe-doc` | **0.5.0** (shipped 2026-04-16) | **1,130** (up from 801 yesterday — added 329 in a day, crossed four digits) | [`Vibe-Doc`](https://github.com/estevanhernandez-stack-ed/Vibe-Doc) |

**Deprecated but still receiving downloads:** `@esthernandez/app-project-readiness` (former Cart name) — 577/week, 5/day. Migration is working. Numbers will fade out over coming weeks.

**Combined ecosystem weekly downloads: ~2,338** (631 + 1,130 + 577).

### Coming-soon plugins (live in monorepo, not yet shipped)

| Plugin | Framework draft | npm (reserved) | Repo path |
|--------|-----------------|----------------|-----------|
| **Vibe Test** | [framework.md (complete)](https://github.com/estevanhernandez-stack-ed/vibe-plugins/blob/main/packages/vibe-test/framework.md) | `@esthernandez/vibe-test` (not published) | `vibe-plugins/packages/vibe-test/` |
| **Vibe Sec** | [framework.md (complete)](https://github.com/estevanhernandez-stack-ed/vibe-plugins/blob/main/packages/vibe-sec/framework.md) | `@esthernandez/vibe-sec` (not published) | `vibe-plugins/packages/vibe-sec/` |

**Vibe Test status as of 2026-04-17:** `/scope` completed, `/prd` in progress. First plugin slated to ship from the monorepo (forcing the marketplace-from-monorepo flow to work before Cart/Vibe Doc migrate in).

### Shared library (internal only)

| Package | Status | Home |
|---------|--------|------|
| `@626labs/plugin-core` | Interface scaffold committed; implementations extract from Vibe Doc in Phase 2 | `vibe-plugins/packages/core/` |

### Ecosystem monorepo

- **Repo:** [`vibe-plugins`](https://github.com/estevanhernandez-stack-ed/vibe-plugins)
- **Role:** Home for Vibe Sec, Vibe Test, and the shared `@626labs/plugin-core`. Cart and Vibe Doc will migrate in once the core is proven.
- **Live stats data:** `data/stats/history.jsonl` auto-updated daily by GitHub Actions cron. Public raw URL:
  ```
  https://raw.githubusercontent.com/estevanhernandez-stack-ed/vibe-plugins/main/data/stats/history.jsonl
  ```
  Daily snapshots at `data/stats/YYYY-MM-DD.json`. The hub's stats strip (see below) should fetch from this — no auth, no API quota, 1-hour caching is fine.

---

## Self-Evolving Plugin Framework (the thesis)

**This is the architectural backbone behind every Vibe plugin.** Currently lives at `github.com/estevanhernandez-stack-ed/vibe-cartographer/blob/main/docs/self-evolving-plugins-framework.md`. 16 patterns, 5-level maturity ladder, 3 pillars (self-repair, self-teach, self-evolve). Vibe Cartographer is currently at **Level 3.5**.

**The thesis in one sentence:**
> A plugin should be more useful on its tenth run than on its first — not because the user learned it, but because it learned the user.

**The hub should link to this prominently** — it's the intellectual scaffolding that makes the ecosystem coherent. Probably deserves its own `<section>` titled "The thinking behind it" or similar, between Products and About.

---

## What to update in `index.html`

### 1. Vibe Cartographer card — minor refresh

Current card is mostly accurate. Suggested updates:

- **Description** currently says *"11 slash commands"* — correct for 1.5.0 (`/onboard`, `/scope`, `/prd`, `/spec`, `/checklist`, `/build`, `/iterate`, `/reflect`, `/evolve`, `/vitals`, `/friction`). No change needed.
- **Tagline** — consider sharpening to: *"Vibe coding with course correction."* Matches the 1.5.0 language reframe.
- **Add** a small version/freshness indicator (optional): *"v1.5.0 · shipped 2026-04-17"* in a muted color.

### 2. Vibe Doc card — minor refresh

Current card says *"AI-powered documentation gap analyzer. Scans your codebase, classifies what you've built, and generates the ADRs, runbooks, threat models, and specs you're missing."* That's accurate but understates Vibe Doc's reach. Consider:

- **Description upgrade (optional):** *"AI-powered documentation gap analyzer. Scans your codebase, classifies project type, generates the 11 doc types you're actually missing — ADRs, runbooks, threat models, API specs, test plans, deployment procedures, install guides, and more."*
- **Add** stat context in a muted footnote: *"1,130 weekly downloads · crossed four digits 2026-04-17."*

### 3. Vibe Test card — promote from "coming soon" to "in active development"

Vibe Test has moved from "framework drafted" to "scope complete, PRD in progress" as of today. The card should reflect that. Suggested copy:

- **Status badge:** change `coming-soon` → something like `in development` or `scoping` — use the same class style but swap the word.
- **Description (optional enhancement):** *"Reads a vibe-coded app, classifies its maturity tier, and generates the tests it genuinely needs — smoke, behavioral, edge, integration, performance — proportional to deployment risk. First plugin slated to ship from the 626Labs monorepo."*
- **Add** a link to the scope doc: [`docs/scope.md`](https://github.com/estevanhernandez-stack-ed/vibe-plugins/tree/main/packages/vibe-test) — reviewers can see the scoping in public.

### 4. Vibe Sec card — keep as-is

No change yet. Framework is drafted; no active scoping. Keep `coming-soon` status.

### 5. NEW section — "The thinking behind it" (between Products and About)

Propose a short section that links to the Self-Evolving Plugin Framework. Suggested structure:

```html
<section class="framework" id="framework">
  <div class="container">
    <h2>The thinking behind it</h2>
    <p class="lead">Every Vibe plugin follows the same architectural playbook.</p>
    <blockquote>
      A plugin should be more useful on its tenth run than on its first —
      not because the user learned it, but because it learned the user.
    </blockquote>
    <p>The <strong>Self-Evolving Plugin Framework</strong> is 626 Labs' open-source thesis on how AI plugins should get sharper over time. Three pillars — self-repair, self-teach, self-evolve. A five-level maturity ladder from static tools to autonomous adaptation. Sixteen named patterns with concrete implementation playbooks.</p>
    <p>Vibe Cartographer is currently at <strong>Level 3.5</strong> — it reads its own usage, surfaces friction patterns, proposes changes to its own behavior, and runs self-diagnostic health checks. The framework doc drives every plugin's roadmap.</p>
    <div class="links">
      <a href="https://github.com/estevanhernandez-stack-ed/vibe-cartographer/blob/main/docs/self-evolving-plugins-framework.md"><strong>Read the framework doc &rarr;</strong></a>
    </div>
  </div>
</section>
```

Styling should match the `.about` section (same container, same `.lead`, same `.tag`-style chips if useful). Use the blockquote for the thesis line — render it in `--cyan` or `--cyan-pale` italic for emphasis.

### 6. NEW section or inline strip — "Ecosystem in numbers"

Live-data strip showing current download counts. Fetches from the public raw URL above on page load; caches in `sessionStorage` for 1 hour. If the fetch fails, fall back to hard-coded numbers (updated manually when releases ship).

Suggested JS pattern:

```js
async function loadEcosystemStats() {
  const CACHE_KEY = 'vibe-stats-v1';
  const CACHE_TTL = 60 * 60 * 1000; // 1 hour
  const cached = sessionStorage.getItem(CACHE_KEY);
  if (cached) {
    const { ts, data } = JSON.parse(cached);
    if (Date.now() - ts < CACHE_TTL) return data;
  }
  try {
    const res = await fetch('https://raw.githubusercontent.com/estevanhernandez-stack-ed/vibe-plugins/main/data/stats/history.jsonl');
    const text = await res.text();
    const lines = text.trim().split('\n').filter(Boolean).map(JSON.parse);
    const latest = lines[lines.length - 1];
    sessionStorage.setItem(CACHE_KEY, JSON.stringify({ ts: Date.now(), data: latest }));
    return latest;
  } catch {
    // fallback baseline — updated when releases ship
    return {
      packages: {
        '@esthernandez/vibe-cartographer': { last_week: 631 },
        '@esthernandez/vibe-doc': { last_week: 1130 },
        '@esthernandez/app-project-readiness': { last_week: 577 }
      }
    };
  }
}
```

Display as a small card or strip: *"2,338 weekly downloads across the ecosystem · updated daily."* Total is the sum of `last_week` for all packages in the latest entry.

Nice-to-have: a tiny sparkline beside each plugin card showing its last-14-day trend from `history.jsonl`. Low priority — add after the main content ships.

### 7. Install instructions — add depth

Current cards show marketplace-add only. Vibe Cartographer and Vibe Doc both support three install paths. Consider adding a collapsible `<details>` or tabbed group under each shipped plugin card:

**Vibe Cartographer:**
- Claude Desktop (recommended): `Personal plugins → + → Add marketplace` → `estevanhernandez-stack-ed/vibe-cartographer` → Sync
- Claude Code CLI: `/plugin marketplace add estevanhernandez-stack-ed/vibe-cartographer` then `/plugin install vibe-cartographer@vibe-cartographer`
- npm (for CLI tooling alongside the plugin): `npm install -g @esthernandez/vibe-cartographer`

**Vibe Doc:**
- Same three paths, substituting the Vibe-Doc repo and package names.
- Vibe Doc is also a **standalone CLI** (`vibe-doc scan`, `vibe-doc generate`, etc.) — worth highlighting. Cart is plugin-only.

---

## Content principles (voice + tone)

Match the existing hub voice. Sample lines from the current site:

- *"Ship what you vibe‑code."*
- *"Built for builders who want AI-assisted workflows that actually land in production."*
- *"Builder mentality — ship then polish. Native over Electron, Python over JavaScript, and talking it through over spec'ing it out."*

**This is the register:** confident, practical, slightly opinionated, no hype. Outsider / underdog energy ("scrappy builder in Fort Worth"). Avoid: "revolutionary," "powered by AI," "next-gen," generic marketing-speak.

---

## Things NOT to put on the hub (yet)

- Download numbers below 100 (feels thin, hide until they're impressive)
- "Coming soon" on anything without a framework doc committed
- Beta / alpha disclaimers on shipping plugins — Cart 1.5.0 and Vibe Doc 0.5.0 are in production despite the pre-1.0 Vibe Doc version number
- Any testimonials / user quotes (none to use yet — capture when real users post)
- Individual commit links or version histories (let GitHub handle that)

---

## Things to verify before pushing

1. **Links tested** — all plugin repo links, npm links, framework doc link, and the stats raw-URL work from a fresh browser (no auth required).
2. **Shields.io URLs resolve** — the existing `npm/v/`, `npm/dw/`, `npm/l/` shields return correct badges. No change needed unless they broke.
3. **Mobile layout** — the existing CSS uses a grid with `auto-fit, minmax(300px, 1fr)`. New sections should inherit the same container + responsive patterns.
4. **Deploy preview** — push to `main`, GitHub Pages auto-deploys at 626labs.dev within 1-2 minutes. Verify.

---

## Out of scope for this update (future work)

- Per-plugin subpages like the existing `sanduhr/` — would be nice for Cart and Vibe Doc eventually
- Blog / posts section — deferred until there's a real first post to anchor it
- Contact / demo form — not needed at current scale
- Analytics beyond the stats strip — GitHub Pages has no built-in analytics; if desired, add a privacy-respecting option like Plausible or GoatCounter
- Newsletter signup — premature

---

## Suggested commit message for whoever executes this

```
hub: refresh Vibe ecosystem content — v1.5.0 Cart, Vibe Doc 0.5.0, framework link, live stats strip

- Cart card: tagline refresh to match 1.5.0 course-correction language
- Vibe Doc card: highlight 1,130/week + four-digit milestone
- Vibe Test card: promote from "coming soon" to "in development"
- New section: "The thinking behind it" → links to Self-Evolving Plugin Framework doc
- New live-data strip: ecosystem weekly downloads, fetched from vibe-plugins/data/stats/history.jsonl
- Install instructions: expand to show all 3 install paths per plugin
```

---

## Starting the agent

Open a fresh Claude Code session at `c:/Users/estev/Projects/626labs-hub/` and hand it this file:

> "Read `VIBE-ECOSYSTEM-BRIEFING.md` and update `index.html` per the 'What to update' section. Preserve the existing design system (CSS variables, layout grid, voice). Test locally in a browser before pushing. Use the suggested commit message. Don't touch `sanduhr/` or the image assets."

Everything the agent needs is in this file.
