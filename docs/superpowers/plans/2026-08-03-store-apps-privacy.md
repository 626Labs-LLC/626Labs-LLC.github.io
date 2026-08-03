# Store-Apps Privacy Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** privacy.html becomes the code-verified canonical privacy policy for the six Store apps, one anchored subsection each, shipped as a PR held for Este's line-by-line.

**Architecture:** Verification-first: an evidence sweep over the six app repos (owned endpoints, update checks, telemetry) produces a findings file; the policy section is written FROM findings; repo PRIVACY.mds become pointers. Spec: `docs/superpowers/specs/2026-08-03-store-apps-privacy-design.md` (the five-question template and known facts live there — every task consumes it).

**Tech Stack:** Static HTML edit (privacy.html), repo greps, markdown.

## Global Constraints

- Branch `feat/store-apps-privacy` from fresh origin/main. Trailer every commit: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`; conventional commits; no emoji; no em dashes in the policy prose (plain-language legal register: commas, periods, colons).
- **Policy text derives from verification findings only** — never from product/marketing copy. A claim without a finding row does not ship.
- Anchor ids exactly: `privacy-rororo`, `privacy-sanduhr`, `privacy-mod-launcher`, `privacy-rbx15`, `privacy-snapsnip`, `privacy-rtclickpng`.
- privacy.html is static (no SITE_JSON zones); match its existing section markup/classes (`<h2><span class="num">NN</span>Title</h2>` pattern, h3 subheads).
- Gates on any hub commit: `python scripts/render-hub.py --check` exit 0, `python -m pytest tests/ -q`, `python scripts/site-doctor.py --report` PASS.
- PR is HELD for Este. SnapSnip's subsection is drafted from its Store description and flagged `[ESTE CONFIRM]` in the PR body (no public repo).

---

### Task P1: Evidence sweep — six apps + the Worker

**Files:**
- Create: `.superpowers/sdd/privacy-findings-2026-08-03.md` (workspace, not committed)

**Interfaces:**
- Produces: per-app findings — every network endpoint (URL, trigger, setting-gate), storage mechanism (exact: DPAPI, Credential Manager service name, file paths), update mechanism, telemetry (payload + destination or "none found"), uninstall behavior — each with file:line evidence from the repo. Plus the Worker verdict.

- [ ] **Step 1:** Sweep each synced local repo READ-ONLY: `C:\Users\estev\Projects\ROROROblox`, `...\Sanduhr_f-r_Claude`, `...\626-mod-launcher`, `...\RBX15-Shirt-and-Pants`, `...\RTClickPng`. Hunt order per app: owned endpoints (`workers.dev`, `626labs`, api bases), all `http`/`Url` constants, update frameworks (Velopack/Squirrel/AppInstaller), crash/analytics SDKs (Sentry, AppCenter, telemetry), credential/storage APIs (DPAPI/ProtectedData, CredentialManager/keyring, localStorage paths), uninstall hooks. Record file:line per finding; record explicit "none found" per category per app.
- [ ] **Step 2:** The Worker: locate `626-mod-metadata-proxy` source (search `C:\Users\estev\Projects` dirs and `gh repo list` both owners). Read it: any logging/analytics/KV writes? Verdict: exactly what the endpoint sees and retains. If source is unfindable, record NEEDS-ESTE (do not guess).
- [ ] **Step 3:** SnapSnip: confirm no local/public repo exists; capture its Store-description privacy claims verbatim as the draft basis, marked unverified.
- [ ] **Step 4:** Write the findings file; report DONE with per-app one-liners.

### Task P2: Section 05 — the policy text

**Files:**
- Modify: `privacy.html`

**Interfaces:**
- Consumes: P1 findings + the spec's five-question template and known-facts list.
- Produces: the new section + renumbered 06-10 + updated effective-date line.

- [ ] **Step 1:** Insert section 05 "Desktop and Microsoft Store apps" after current 04, matching existing markup. Shared posture paragraph first, then six subsections (spec's anchor ids), each answering the five questions in order, each claim traceable to a findings row. Mod Launcher's three network paths get three distinct disclosures. SnapSnip's subsection drafted from Store claims with an HTML comment `<!-- ESTE CONFIRM: no repo source; drafted from Store description -->`.
- [ ] **Step 2:** Renumber current 05-09 to 06-10 (both the `<span class="num">` values and any internal anchors/links that reference them — grep first). Update the effective-date/changes line to 2026-08-03.
- [ ] **Step 3:** Gates (render --check, pytest, doctor --report) + `grep -c 'id="privacy-'` = 6 + serve once and click all six anchors from the URL bar.
- [ ] **Step 4:** Commit `feat(site): privacy policy covers the Store apps, code-verified` + trailer.

### Task P3: Repo pointer files

**Files:**
- Modify: `C:\Users\estev\Projects\RTClickPng\PRIVACY.md`, `C:\Users\estev\Projects\626-mod-launcher\PRIVACY.md`

- [ ] **Step 1:** Each becomes: one-paragraph summary (from the new subsection, condensed) + canonical link `https://626labs.dev/privacy.html#privacy-<app>` + "the site version governs" line. Keep any repo-specific technical detail that the site section links back to, if present.
- [ ] **Step 2:** Commit in each repo (`docs: privacy policy points at the canonical site policy` + trailer) and push. CAUTION (626-mod-launcher): the repo has Este's staged uncommitted WIP (.gitignore, RELEASE.md) — do NOT commit those files; stage only PRIVACY.md (`git add PRIVACY.md` then `git commit` — verify with `git status` that WIP stays staged-but-uncommitted or untouched).
- [ ] **Step 3:** Report both pushes' SHAs.

### Task P4: Verify + held PR

- [ ] **Step 1:** Serve repo root; Playwright (via ToolSearch) or curl+grep: all six anchors resolve, renumbering consistent (no duplicate section numbers, nav/footer links unaffected), zero console errors, mobile no h-scroll.
- [ ] **Step 2:** Push branch; `gh pr create` title `feat(site): privacy policy covers the Store apps` — body: per-app one-line summary of what its subsection discloses, the Worker verdict, `[ESTE CONFIRM]` items (SnapSnip; any NEEDS-ESTE from P1), and Este's post-merge checklist: six Partner Center privacy-URL updates to `https://626labs.dev/privacy.html#privacy-<app>`. Trailer `🤖 Generated with [Claude Code](https://claude.com/claude-code)`. `gh pr checks --watch`. DO NOT MERGE.

## Self-review notes

Spec coverage: verification-first (P1), five-question section + renumber + date (P2), pointers with WIP caution (P3), held PR + checklist (P4). No placeholders; SnapSnip path is a specified process. Anchor ids consistent across P2/P3/P4 and the spec.
