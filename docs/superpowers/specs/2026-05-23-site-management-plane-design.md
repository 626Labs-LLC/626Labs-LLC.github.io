# 626 Labs Site Management Plane — Design

**Date:** 2026-05-23
**Repo:** 626labs-hub (626Labs-LLC/626Labs-LLC.github.io)
**Status:** Design — pending user review, then implementation plan
**Author:** The Architect (brainstormed with Este)

---

## The problem

The marketing site (626labs.dev) is hand-written HTML rendered from JSON
sources. The render pipeline derives *structural* things well (the plugins
family count already self-counts via `num_word(len(family))`, the lab pool is
array-driven). But **facts embedded in hand-written prose** are not derived by
anything, so they rot silently as tools are added.

This is not hypothetical. It is **live right now**:

- `content/site.json:140` says "Eleven slash commands walk you from first idea
  to shipped app." Cartographer ships **twelve** today. That stale string
  renders into `index.html` in two places.
- The hero tuple `8 plugins · 1 widget · 5 Microsoft Store Releases`
  (`site.json:20`) is hand-typed.
- The About paragraph hardcodes a plugin subset ("Cartographer, Doc, Test,
  Sec") that no script keeps current.
- Nothing validates that local asset paths (`/assets/...`) actually exist on
  disk — dangling references can ship.
- The render `--check` drift guard only runs **after** a push (`rebuild-hub.yml`),
  never on a PR. Plugin pages have **no** CI rebuild at all (committed by hand).

Two asks, captured from the brainstorm:

1. **Health & reactivity.** Make the site reactive to change so copy doesn't go
   stale as tools are added.
2. **Agent manageability.** Make the site as easy for an IDE agent to manage as
   it is for a human via the admin dashboard. The admin dashboard is the *human*
   face; build an equivalent *agent* face.

---

## Decisions captured (from brainstorm)

| Question | Decision |
|---|---|
| Scope | **Both** — run the checkup now AND build a durable guardrail |
| Reactivity model | **Hybrid** — auto-rewrite data-like surfaces from facts; fail-loud validate voice prose |
| Fact source | **Derive + tiny supplement** — compute from existing JSON; only genuinely-external facts are hand-maintained |
| Agent face | **Both** — CLI core + MCP wrapper |
| Sequencing | **Mega-spec all three milestones now**, then one plan, then build |

---

## The reframe: one management plane, two faces, one contract

This is not a health-check feature bolted onto a site. It is a **management
plane**. The admin dashboard is the human face. We are adding an agent face.
Both sit on the same operations.

```
                  THE CONTRACT (one rulebook)
        ┌──────────────────┴──────────────────┐
        │  facts derivation (site_facts.py)    │
        │  validation rules  (site-doctor)     │
        │  asset-naming conventions            │
        │  content schema (site.json shape)    │
        └──────────────────┬──────────────────┘
              ┌─────────────┴─────────────┐
         HUMAN FACE                   AGENT FACE
   admin dashboard (React,      ┌──────────┴──────────┐
   browser → GitHub API)    site.py CLI         MCP tool group
                            (local files → git)  (Firebase server →
                                                  GitHub API → PR)
```

**The execution contexts genuinely differ** and should not be fused:

- Human admin: browser React → GitHub Contents API (PAT-auth).
- Agent CLI: local Python → filesystem → git (runs inside the repo checkout).
- Agent MCP: TypeScript on Firebase → GitHub Contents API → branch + PR.

What they **must** share is the **contract**: the same facts, the same
validation rules, the same naming conventions, the same schema. Fusing
execution is wrong; sharing the rulebook is the whole point.

### The architectural crux (read this twice)

The contract is implemented in **Python** (in this repo). The MCP server is
**TypeScript** (on Firebase, in `Project-626Labs-1/mcp-server`). If the MCP
re-implements validation in TS, the two rulebooks drift — which is exactly the
disease we're curing.

**Resolution:** the validation rules live in **exactly one place** — the Python
doctor (`site-doctor.py`). Every write path funnels through the same CI choke
point that runs it:

- The **CLI** runs the doctor *in-process* before it commits (same code).
- The **human admin** commits → `content-health.yml` runs the doctor in CI.
- The **MCP** commits to a branch and opens a PR → `content-health.yml` runs
  the doctor in CI → MCP polls the GitHub checks API and reports the verdict.

No path re-implements the rules. The MCP never validates locally; it relies on
the one Python doctor via CI. This is the anti-drift guarantee for the entire
plane.

### One thing we are explicitly NOT doing

The site content's **source of truth is the repo** (`content/*.json`), because
GitHub Pages serves directly from it. The MCP must **not** mirror site content
into Firestore (a subagent suggested this; it is wrong for this use case — it
would create a second source of truth and reintroduce drift). Firestore remains
for the dashboard's project/task/decision data only. The MCP operates directly
on the repo via the GitHub Contents API, exactly as the human admin already does.

---

## Milestone 1 — Health & reactivity guardrail

Ships the live staleness fix and stands up the read/validate organ + the shared
contract. Independently shippable.

### 1.1 `scripts/site_facts.py` — the fact layer

A small, pure, importable module. One job: compute the canonical facts dict from
sources that already exist. No side effects, no I/O beyond reading the JSON
sources. This is the shared contract's data half.

Confirmed derivation logic (verified against current `site.json` /
`plugin-pages.json`):

| Fact | Derivation | Today |
|---|---|---|
| `claude_plugins_live` | products where `claudeCode == true and status == "live"` | 8 |
| `claude_plugins_wip` | products where `claudeCode == true and status == "wip"` | 1 (vibe-sec) |
| `live_plugin_names` | titles of the above live set (for the About list) | — |
| `family_count` | `len(family)` in `plugin-pages.json` (already used by render) | 10 |
| `cmd_count[<plugin>]` | `len(cards)` for each plugin page that has a command-card array | cartographer = 12 |
| `windows_native_count` | products with a "Windows" tag and `claudeCode` unset | 5 |
| `widget_count` | count of widget apps under `apps/` (or supplement) | 1 |
| `ms_store_releases` | **supplement** — the *published-to-Store* claim is external | 5 |

`number_word(n)` (cardinal) and a future `ordinal_word(n)` live here too, reused
by the renderers (today `render-plugin-pages.py` has its own `NUM_WORDS` —
consolidate into `site_facts` so there is one number-word table).

**Discriminator note:** `site.json` products have no clean `kind`/`type` field.
The discriminator is the `claudeCode` boolean (`true` = Claude Code plugin,
`false` = web app like celestia-3, unset = native app) combined with `status`
(`live`/`wip`) and `tags`. `site_facts.py` is the single place that encodes this
mapping; if the product schema ever changes, this is the only file to update.

### 1.2 `content/facts-supplement.json` — external truths

Tiny, hand-maintained, for facts that genuinely cannot be derived locally. Each
entry carries a comment explaining *why* it's manual.

```jsonc
{
  "ms_store_releases": 5,   // Store publication isn't visible in GitHub scans;
                            // confirm against the Microsoft Store dashboard.
  "_note": "Only facts that cannot be derived from repo sources belong here."
}
```

The doctor reminds you to re-confirm these on a schedule (they're the most
likely to silently lag reality).

### 1.3 `scripts/site-doctor.py` — the checkup + the CI gate

One tool, two modes:

- `--report` — human-readable health printout. Run anytime. This **is** the
  Phase-1 checkup; its first run produces the fix list.
- `--check` — same logic, exits nonzero on any failure. This is what CI runs.

What it checks:

1. **Prose-vs-facts (fail-loud).** A **curated check registry** — not magic
   full-text scanning (that false-positives, since "plugins" means 8 on the home
   page but 10 on the family page). Each check is explicit:
   `Check(matcher, expected_fact, where)`. ~8 checks at launch covering every
   known drift point. The registry is short, lives in the file, and the report
   names exactly which check failed and the offending file/field. Adding a tool
   means adding or adjusting a line.

2. **Asset existence.** Walk every string value in `site.json` and
   `plugin-pages.json`; for ones that look like local paths (`/assets/...`,
   `assets/...`), assert the file exists on disk. Closes the dangling-reference
   gap (e.g., the timestamped `lab-runs/...png` the audit couldn't verify).

3. **Render drift.** Wrap the existing `render-hub.py --check` and
   `render-plugin-pages.py --check`; aggregate pass/fail.

4. **Supplement staleness reminder.** In `--report`, print the supplement values
   and the date each should be re-confirmed.

### 1.4 Auto-rewrite the data surfaces (the hybrid line)

Data-like counts get tokenized so they fill themselves at render time. In the
content JSON prose:

- hero: `{{fact:claude_plugins}} plugins · {{fact:widget_count}} widget · {{fact:ms_store_releases}} Microsoft Store Releases`
- heading: `{{fact:cmd_cartographer_word}} commands. One shipped app.`

The render scripts import `site_facts`, substitute `{{fact:...}}` tokens during
render. Tokens never reach `index.html` (resolved at render time), so the output
stays clean and `--check` stays idempotent (facts derive deterministically from
the same sources).

**Voice prose is NOT tokenized.** "Eleven slash commands walk you from first idea
to shipped app" stays hand-written; the fail-loud check just won't let it lie.
That's the hybrid boundary: data fills itself, voice stays yours but guarded.

### 1.5 CI wiring

New `.github/workflows/content-health.yml`:

- **On PR** touching `content/**`, `index.html`, `scripts/**`, `assets/**` → run
  `python scripts/site-doctor.py --check`. Drift blocks the merge. **This is the
  PR-time gate that's missing today.**
- **On schedule** (weekly, alongside link-check) → run `--check`; on failure,
  open an issue (mirrors `link-check.yml`). Catches *external* drift (Store count
  changed, a plugin shipped) with no code change needed.
- Plus `workflow_dispatch` for on-demand.

One small fix to existing `rebuild-hub.yml`: add `content/plugin-pages.json` and
`content/facts-supplement.json` to its path triggers, since hero tokens now
derive from them.

### 1.6 Phase-1 checkup (the first run)

Build the tool, run `--report`, fix what it flags:

- "Eleven" → "Twelve" (via tokenizing the hero/heading counts, which fixes all
  renders at once).
- Confirm the hero tuple and the timestamped lab-runs asset path.
- **Derive the About plugin subset from `live_plugin_names`** (decided): the
  paragraph that today hardcodes "Cartographer, Doc, Test, Sec" becomes a
  rendered list of every live plugin. As the family grows the section fills out
  on its own — see *Vision* below.
- Land the first clean health report.

### 1.7 Vision — the About section as a star map

Deriving the plugin list from `live_plugin_names` isn't just anti-staleness;
it sets up a visual thread. As plugins ship, the About section fills with more
named points until it reads less like a sentence and more like a constellation —
a star map of the family that draws itself from the facts. Keep this in mind
when rendering the derived list (M1): structure it so a later visual treatment
(a constellation/star-map layout, brand cyan/magenta points on the navy field)
can sit on top of the same derived data without a re-plumb. No star-map UI in
M1 — just don't render the list in a shape that forecloses it.

---

## Milestone 2 — Agent write CLI (`scripts/site.py`)

The write organ. Makes the site agent-*manageable*, not just agent-*auditable*.
Mirrors the admin dashboard's capabilities as guarded verbs. Each mutating verb
validates before it commits, so an agent physically cannot ship drift.

### 2.1 Verbs (mirror the admin tabs)

| Verb | What it does | Guardrail |
|---|---|---|
| `site facts` | Print the derived facts dict | read-only |
| `site doctor [--report\|--check]` | Health checkup (folds M1 in) | read-only |
| `site get <section>` | Pretty-print a content section | read-only |
| `site set <section> <field> <value>` | Guarded edit of a `site.json` field | validates shape, re-renders |
| `site add-plugin <id> ...` | Add a plugin to products + family | derives count, re-renders |
| `site set-status <id> <live\|wip>` | Promote/demote a plugin | re-renders, updates derived facts |
| `site upload-shot <product-id> <image>` | Add a screenshot | enforces `assets/screenshots/<product-id>/<timestamp>-<slug>.<ext>`, builds thumbnail |
| `site story new\|edit <slug>` | Manage `content/stories/*.md` | template + frontmatter check |
| `site render` | Re-run both renderers | — |
| `site ops` | Bot run status (`gh run list`) | read-only |

### 2.2 Guarded mutation flow

Every mutating verb follows the same pipeline:

1. Apply the edit to the relevant JSON/MD source.
2. Re-render (`render-hub.py` / `render-plugin-pages.py`).
3. Run `site-doctor.py --check` **in-process**. On failure, refuse and report.
4. Stage the change. Default: commit on a **working branch** (never `main`,
   per repo convention). `--pr` opens a PR via `gh`. `--commit` commits without
   PR (for batched local work).

This is the CLI's edge over raw file editing: an agent that runs
`site set-status vibe-sec live` gets the products update, the family re-render,
the derived-count refresh, and a doctor pass — atomically — instead of
hand-editing JSON and forgetting a step.

### 2.3 Discoverability — `AGENTS.md`

A short `AGENTS.md` at repo root (and a pointer in `CLAUDE.md`) declares the CLI
the canonical management surface: "To manage the site, use
`python scripts/site.py <verb>`, not raw edits." This is how an agent *discovers*
the affordances the way a human discovers admin tabs.

---

## Milestone 3 — MCP wrapper (extend the existing server)

The MCP server already exists. **We extend it; we do not build a new one.**

### 3.1 Where it lives (verified)

`Project-626Labs-1/mcp-server/` — deployed to Firebase as a Cloud Function
(`mcp = onRequest()`), also runs stdio locally. Tool pattern: one tool per
domain (`manage_projects`, `manage_tasks`, ...), Zod input schema +
discriminated-union `action` enum + handler returning `{ content, isError }`.
Registered in `createMcpServer()` via `registerXxxTools(server, db, userId)`.
Auth: `USER_UID` env (user scope) + agent-based REST auth with an `allowedTools`
whitelist. Build: `npm run build` (tsc); deploy: `firebase deploy --only functions:mcp`.

### 3.2 New tool group

Create `mcp-server/src/tools/site-content.ts`, export
`registerSiteContentTools(server, db, userId)`, register it in `src/index.ts`.
Follow the existing action-dispatch pattern exactly.

- **`manage_site_content`** — actions: `getConfig | listSections | updateSection
  | addPlugin | setStatus`
- **`manage_site_assets`** — actions: `listAssets | uploadScreenshot`
- **`site_health`** — actions: `report | check`

### 3.3 Execution backend (the crux applied)

The Firebase-hosted server has **no local checkout** of 626labs-hub. So, exactly
like the human admin dashboard, the MCP tools operate via the **GitHub Contents
API**:

1. Read/modify `content/*.json` (or upload an asset) via the Contents API.
2. Commit to a **working branch** and open a **PR** (never push `main`).
3. `content-health.yml` runs the Python doctor on that PR.
4. The tool **polls the GitHub checks API** and returns the PR URL + the
   doctor's verdict to the agent.

No validation logic is re-implemented in TypeScript. The one Python doctor,
reached via CI, is the only judge. Asset naming conventions are the one thing the
TS side must mirror from the contract — keep them in a single small constant and
document that `site_facts`/CLI is the source of truth for the format.

### 3.4 Auth & secrets

- Add the new tool names to agents' `allowedTools` to gate access.
- The server needs a **fine-grained PAT** scoped to 626labs-hub
  (contents:write + pull-requests:write), stored as a Firebase secret — mirrors
  the admin dashboard's PAT model. **Security note:** scope it to the single repo;
  document rotation.

### 3.5 Build & deploy

```bash
cd Project-626Labs-1/mcp-server
npm run build
firebase deploy --only functions:mcp
```

---

## Out of scope (YAGNI)

- Full JSON-schema validation of `site.json` (it declares `$schema` but the file
  is a separate nice-to-have — not this).
- Fetch-from-live-repos for facts (network + PAT in CI; Store/native facts still
  aren't in GitHub).
- Tokenizing voice prose (fail-loud instead).
- Mirroring site content into Firestore (repo is the source of truth).
- A synchronous server-side doctor HTTP endpoint for instant MCP feedback
  (future optimization; v1 uses the CI gate + checks-API polling).
- Touching `link-check.yml` (works; content-health is complementary).

---

## Risks & open questions

1. **Cross-language contract drift** — mitigated by the single-Python-doctor +
   CI-choke-point design. The only TS duplication is the asset-naming format;
   keep it to one constant.
2. **MCP PAT storage** — a write-capable PAT lives in Firebase secrets. Scope to
   one repo, least privilege, documented rotation.
3. **MS Store count** — derivable as "Windows-native product count," but the
   *published* claim is external; the supplement confirms it.
4. **Token-fill triggers** — `rebuild-hub.yml` must trigger on
   `plugin-pages.json` + `facts-supplement.json` now that hero tokens derive from
   them.
5. **Plugin pages have no CI rebuild** — the doctor `--check` in CI covers this
   gap (fails if pages are stale), but consider adding a `rebuild-plugin-pages`
   job later.
6. **About-paragraph plugin subset** — RESOLVED: derive from `live_plugin_names`
   (renders all live plugins, not a curated four). Render the list in a shape that
   a later star-map visual treatment can build on (see §1.7).

---

## Testing strategy

- **M1:** unit tests for `site_facts` derivation (fixture JSON); doctor
  check-registry tests (pass/fail fixtures); asset-existence test; CI smoke run.
- **M2:** CLI verb tests against a temp-repo fixture; naming-convention test;
  validate-before-commit refusal test.
- **M3:** tool-handler unit tests with a mocked GitHub API; action-dispatch
  tests; `allowedTools` auth test. Reuse the existing `vitest` setup in
  `mcp-server`.

---

## Sequencing & shippable increments

`M1 → M2 → M3`, each independently shippable and strictly dependent on the prior:

1. **M1** ships the staleness fix + the read/validate organ + the shared
   contract. (First doctor run = Phase-1 checkup.)
2. **M2** ships the agent write CLI on top of M1's contract.
3. **M3** ships the MCP tool group wrapping M2's operations via GitHub API + CI.

Despite "both now" for the agent face, the build order is sequenced because M2
needs M1's contract and M3 wraps M2's core. All three are designed here; the
implementation plan covers all three; the work lands in this order.
