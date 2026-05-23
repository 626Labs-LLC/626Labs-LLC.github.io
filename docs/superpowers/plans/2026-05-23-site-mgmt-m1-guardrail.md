# Site Management Plane — M1 (Health & Reactivity Guardrail) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the read/validate organ + shared contract for 626labs.dev so facts derive from existing sources, data-like prose fills itself from those facts, voice prose fails loud when it contradicts them, and a CI gate catches drift on PRs — fixing the live "Eleven slash commands" staleness as the first run.

**Architecture:** A pure `site_facts.py` module derives a flat facts dict from `content/site.json` + `content/plugin-pages.json` + a tiny `content/facts-supplement.json` (external truths only). A `resolve_tokens()` pass lets the renderers substitute `{{fact:KEY}}` tokens in data-like prose at render time. A `site-doctor.py` tool validates voice-prose-vs-facts (curated check registry), asset existence, and render drift, with `--report` (human) and `--check` (CI exit code) modes. A new `content-health.yml` runs the doctor on PRs.

**Tech Stack:** Python 3.11 (stdlib only — `json`, `pathlib`, `re`, `argparse`, `subprocess`), pytest 8.3.

**Spec:** `docs/superpowers/specs/2026-05-23-site-management-plane-design.md`

---

## File structure

| File | Responsibility |
|---|---|
| `scripts/site_facts.py` | **Create.** Pure facts derivation + number words + `resolve_tokens()`. The one place that encodes product classification and the number-word table. |
| `content/facts-supplement.json` | **Create.** External truths only (`ms_store_releases`, `cmd_vibe-cartographer`). |
| `scripts/site-doctor.py` | **Create.** Checkup + CI gate: prose-vs-facts registry, asset existence, render drift. `--report`/`--check`. |
| `scripts/render-hub.py` | **Modify.** Call `resolve_tokens(data, facts())` after load. |
| `scripts/render-plugin-pages.py` | **Modify.** Same; import `number_word` from `site_facts` (drop local `NUM_WORDS`). |
| `content/site.json` | **Modify.** Tokenize hero meta + cartographer "Eleven slash commands"; derive About plugin list. |
| `content/plugin-pages.json` | **Modify.** Tokenize cartographer command-count prose. |
| `.github/workflows/content-health.yml` | **Create.** PR + scheduled + dispatch doctor gate. |
| `.github/workflows/rebuild-hub.yml` | **Modify.** Add `plugin-pages.json` + `facts-supplement.json` to triggers. |
| `tests/test_site_facts.py` | **Create.** Derivation + token tests (fixtures + real-data smoke). |
| `tests/test_site_doctor.py` | **Create.** Check-registry + asset-existence tests (fixtures). |
| `tests/fixtures/*.json` | **Create.** Minimal deterministic source fixtures. |
| `pytest.ini` | **Create.** `testpaths = tests`. |

---

## Task 1: Test scaffold

**Files:**
- Create: `pytest.ini`
- Create: `tests/fixtures/site_min.json`, `tests/fixtures/plugin_pages_min.json`, `tests/fixtures/supplement_min.json`

- [ ] **Step 1: Create pytest config**

`pytest.ini`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
```

- [ ] **Step 2: Create fixtures**

`tests/fixtures/site_min.json` (two live plugins, one wip plugin, one web app, one Windows-native):
```json
{
  "hero": { "meta": [{ "label": "Deployed", "value": "{{fact:claude_plugins}} plugins" }] },
  "about": { "paragraphs": ["Names: <strong>{{fact:live_plugin_names}}</strong>."] },
  "products": [
    { "id": "vibe-alpha", "title": "vibe-alpha", "status": "live", "claudeCode": true, "tags": [] },
    { "id": "thesis-beta", "title": "thesis-beta", "status": "live", "claudeCode": true, "tags": [] },
    { "id": "vibe-wip", "title": "vibe-wip", "status": "wip", "claudeCode": true, "tags": [] },
    { "id": "webby", "title": "webby", "status": "live", "claudeCode": false, "tags": [] },
    { "id": "nativey", "title": "nativey", "status": "live", "tags": [{ "label": "Windows" }] }
  ]
}
```

`tests/fixtures/plugin_pages_min.json`:
```json
{ "family": [{ "id": "a" }, { "id": "b" }, { "id": "c" }], "plugins": {} }
```

`tests/fixtures/supplement_min.json`:
```json
{ "ms_store_releases": 3, "cmd_vibe-cartographer": 12, "_note": "external only" }
```

- [ ] **Step 3: Commit**
```bash
git add pytest.ini tests/fixtures
git commit -m "test: scaffold pytest config + minimal source fixtures"
```

---

## Task 2: `site_facts.py` — number words + derivation

**Files:**
- Create: `scripts/site_facts.py`
- Test: `tests/test_site_facts.py`

- [ ] **Step 1: Write the failing test**

`tests/test_site_facts.py`:
```python
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import site_facts  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


def _load(name):
    return json.loads((FIX / name).read_text())


def test_number_word():
    assert site_facts.number_word(12) == "Twelve"
    assert site_facts.number_word(8) == "Eight"
    assert site_facts.number_word(99) == "99"  # past the table -> str


def test_derive_counts():
    f = site_facts.derive(
        _load("site_min.json"), _load("plugin_pages_min.json"), _load("supplement_min.json")
    )
    assert f["claude_plugins"] == 2          # vibe-alpha, thesis-beta (live + claudeCode)
    assert f["claude_plugins_word"] == "Two"
    assert f["claude_plugins_wip"] == 1      # vibe-wip
    assert f["family_count"] == 3
    assert f["windows_native_count"] == 1    # nativey (Windows tag, no claudeCode)


def test_live_plugin_names():
    f = site_facts.derive(
        _load("site_min.json"), _load("plugin_pages_min.json"), _load("supplement_min.json")
    )
    # prefixes stripped, capitalized, comma-joined, in source order
    assert f["live_plugin_names"] == "Alpha, Beta"


def test_supplement_merges_with_word_variants():
    f = site_facts.derive(
        _load("site_min.json"), _load("plugin_pages_min.json"), _load("supplement_min.json")
    )
    assert f["ms_store_releases"] == 3
    assert f["ms_store_releases_word"] == "Three"
    assert f["cmd_vibe-cartographer"] == 12
    assert f["cmd_vibe-cartographer_word"] == "Twelve"
    assert "_note" not in f  # underscore keys skipped
```

- [ ] **Step 2: Run, verify it fails**

Run: `python -m pytest tests/test_site_facts.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'site_facts'` (or AttributeError).

- [ ] **Step 3: Implement `site_facts.py`**

`scripts/site_facts.py`:
```python
"""site_facts.py — canonical facts derived from the content sources.

One job: compute the facts dict that both the renderers and the doctor read.
Pure functions. This is the ONLY place that encodes how a product is classified
(claudeCode + status + tags), the number-word table, and {{fact:...}} tokens.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE_JSON = ROOT / "content" / "site.json"
PLUGIN_PAGES_JSON = ROOT / "content" / "plugin-pages.json"
SUPPLEMENT_JSON = ROOT / "content" / "facts-supplement.json"
APPS_DIR = ROOT / "apps"

NUM_WORDS = {
    0: "Zero", 1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five",
    6: "Six", 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten", 11: "Eleven",
    12: "Twelve", 13: "Thirteen", 14: "Fourteen", 15: "Fifteen",
    16: "Sixteen", 17: "Seventeen", 18: "Eighteen", 19: "Nineteen", 20: "Twenty",
}

TOKEN_RE = re.compile(r"\{\{fact:([A-Za-z0-9_\-]+)\}\}")


def number_word(n: int) -> str:
    """Capitalized cardinal word for n; falls back to str(n) past the table."""
    return NUM_WORDS.get(n, str(n))


def is_claude_plugin(product: dict) -> bool:
    return product.get("claudeCode") is True


def _has_tag(product: dict, label: str) -> bool:
    return any(
        (t.get("label", "").lower() == label.lower()) for t in product.get("tags", [])
    )


def display_name(product: dict) -> str:
    """Short display name: id with a vibe-/thesis- prefix stripped, capitalized.
    e.g. 'vibe-cartographer' -> 'Cartographer', 'thesis-engine' -> 'Engine'."""
    name = product.get("id", "")
    for prefix in ("vibe-", "thesis-"):
        if name.lower().startswith(prefix):
            name = name[len(prefix):]
            break
    return name[:1].upper() + name[1:] if name else product.get("id", "")


def _widget_count() -> int:
    if not APPS_DIR.exists():
        return 0
    return sum(1 for p in APPS_DIR.iterdir() if p.is_dir() and p.name.startswith("widget-"))


def derive(site: dict, pages: dict, supplement: dict) -> dict:
    products = site.get("products", [])
    live = [p for p in products if is_claude_plugin(p) and p.get("status") == "live"]
    wip = [p for p in products if is_claude_plugin(p) and p.get("status") == "wip"]
    win_native = [
        p for p in products if not is_claude_plugin(p) and _has_tag(p, "Windows")
    ]
    family = pages.get("family", [])

    f: dict = {
        "claude_plugins": len(live),
        "claude_plugins_word": number_word(len(live)),
        "claude_plugins_wip": len(wip),
        "claude_plugins_wip_word": number_word(len(wip)),
        "family_count": len(family),
        "family_count_word": number_word(len(family)),
        "windows_native_count": len(win_native),
        "windows_native_count_word": number_word(len(win_native)),
        "widget_count": _widget_count(),
        "widget_count_word": number_word(_widget_count()),
        "live_plugin_names": ", ".join(display_name(p) for p in live),
    }

    for key, val in supplement.items():
        if key.startswith("_"):
            continue
        f[key] = val
        if isinstance(val, int):
            f[f"{key}_word"] = number_word(val)

    return f


def facts() -> dict:
    """Derive facts from the real content sources."""
    site = json.loads(SITE_JSON.read_text(encoding="utf-8"))
    pages = json.loads(PLUGIN_PAGES_JSON.read_text(encoding="utf-8"))
    supplement = (
        json.loads(SUPPLEMENT_JSON.read_text(encoding="utf-8"))
        if SUPPLEMENT_JSON.exists()
        else {}
    )
    return derive(site, pages, supplement)


def resolve_tokens(obj, fct: dict):
    """Recursively replace {{fact:KEY}} tokens in all strings of a JSON-like
    structure. Unknown token -> KeyError (fail-loud, so a typo never ships)."""
    if isinstance(obj, str):
        def sub(m):
            key = m.group(1)
            if key not in fct:
                raise KeyError(f"unknown fact token: {{{{fact:{key}}}}}")
            return str(fct[key])
        return TOKEN_RE.sub(sub, obj)
    if isinstance(obj, list):
        return [resolve_tokens(v, fct) for v in obj]
    if isinstance(obj, dict):
        return {k: resolve_tokens(v, fct) for k, v in obj.items()}
    return obj
```

- [ ] **Step 4: Run, verify it passes**

Run: `python -m pytest tests/test_site_facts.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**
```bash
git add scripts/site_facts.py tests/test_site_facts.py
git commit -m "feat(facts): site_facts derivation module + number words"
```

---

## Task 3: `resolve_tokens` tests + `facts-supplement.json`

**Files:**
- Create: `content/facts-supplement.json`
- Modify: `tests/test_site_facts.py` (append)

- [ ] **Step 1: Write failing tests** (append to `tests/test_site_facts.py`)
```python
def test_resolve_tokens_replaces():
    out = site_facts.resolve_tokens(
        {"v": "{{fact:claude_plugins_word}} plugins", "n": ["{{fact:claude_plugins}}"]},
        {"claude_plugins_word": "Two", "claude_plugins": 2},
    )
    assert out["v"] == "Two plugins"
    assert out["n"] == ["2"]


def test_resolve_tokens_unknown_raises():
    import pytest
    with pytest.raises(KeyError):
        site_facts.resolve_tokens("{{fact:nope}}", {"claude_plugins": 2})


def test_real_facts_smoke():
    f = site_facts.facts()
    assert f["claude_plugins"] == 8        # live + claudeCode today
    assert f["family_count"] == 10
    assert f["widget_count"] == 1
    assert f["cmd_vibe-cartographer"] == 12  # from supplement
```

- [ ] **Step 2: Run, verify the smoke test fails**

Run: `python -m pytest tests/test_site_facts.py -v`
Expected: `test_real_facts_smoke` FAILS (no `facts-supplement.json` yet → `cmd_vibe-cartographer` missing). Token tests PASS.

- [ ] **Step 3: Create `content/facts-supplement.json`**
```json
{
  "ms_store_releases": 5,
  "cmd_vibe-cartographer": 12,
  "_note": "External truths only — facts that cannot be derived from repo sources. ms_store_releases: confirm against the Microsoft Store dashboard. cmd_vibe-cartographer: lives in the vibe-cartographer plugin repo; bump when its commands change."
}
```

- [ ] **Step 4: Run, verify all pass**

Run: `python -m pytest tests/test_site_facts.py -v`
Expected: PASS (all).

- [ ] **Step 5: Commit**
```bash
git add content/facts-supplement.json tests/test_site_facts.py
git commit -m "feat(facts): external-truth supplement + token resolution tests"
```

---

## Task 4: Wire token resolution into `render-hub.py`

**Files:**
- Modify: `scripts/render-hub.py` (the load step in `main`, ~line 1186-1219)

- [ ] **Step 1: Read the load + render flow**

Run: `python -m pytest -q` then open `scripts/render-hub.py` around `def main` (1186) and the `json.load`/`SITE_JSON` read (~40, ~1190). Identify where `data` (parsed site.json) is loaded before rendering.

- [ ] **Step 2: Add the import + resolution**

Near the top imports of `render-hub.py` add:
```python
import site_facts  # same dir (scripts/)
```
(If `scripts/` isn't on path when run directly, it is — the script lives there. Confirm `from pathlib import Path` already present.)

Immediately after the site.json is parsed into the working dict (the variable passed to the render functions), insert:
```python
    data = site_facts.resolve_tokens(data, site_facts.facts())
```
Use the actual variable name from Step 1 (likely `data` or `site`).

- [ ] **Step 3: Verify render is idempotent + token-free**

Run:
```bash
python scripts/render-hub.py
python scripts/render-hub.py --check
```
Expected: first writes index.html; `--check` exits 0 (no drift). Then:
```bash
grep -c "{{fact:" index.html
```
Expected: `0` (no unresolved tokens — there are none yet; this guards future edits).

- [ ] **Step 4: Commit**
```bash
git add scripts/render-hub.py
git commit -m "feat(render): resolve {{fact:...}} tokens in render-hub from site_facts"
```

---

## Task 5: Wire token resolution into `render-plugin-pages.py` + consolidate number words

**Files:**
- Modify: `scripts/render-plugin-pages.py` (`NUM_WORDS`/`num_word` at 268-276; `data` load before render ~654)

- [ ] **Step 1: Replace local number table with the shared one**

Delete the `NUM_WORDS` dict (268-272) and the `num_word` body; replace with:
```python
import site_facts

def num_word(n):
    return site_facts.number_word(n)
```
(Keep the `num_word` name so existing call sites at 578 work unchanged.)

- [ ] **Step 2: Resolve tokens after load**

After `plugin-pages.json` is parsed into the working dict (the one used by `render_index`/page render, ~654), insert:
```python
    data = site_facts.resolve_tokens(data, site_facts.facts())
```

- [ ] **Step 3: Verify**

Run:
```bash
python scripts/render-plugin-pages.py
python scripts/render-plugin-pages.py --check
```
Expected: `--check` exits 0.

- [ ] **Step 4: Commit**
```bash
git add scripts/render-plugin-pages.py
git commit -m "feat(render): token resolution in plugin pages + share number_word"
```

---

## Task 6: Phase-1 content edits — tokenize stale strings + derive About list

**Files:**
- Modify: `content/site.json` (hero.meta value; About paragraph; cartographer product "Eleven slash commands")
- Modify: `content/plugin-pages.json` (cartographer command-count prose)

- [ ] **Step 1: Tokenize the hero meta tuple**

In `content/site.json`, `hero.meta[0].value`:
`"8 plugins · 1 widget · 5 Microsoft Store Releases"`
→ `"{{fact:claude_plugins}} plugins · {{fact:widget_count}} widget · {{fact:ms_store_releases}} Microsoft Store Releases"`

- [ ] **Step 2: Derive the About plugin list**

In the About paragraph that reads `... <strong>Cartographer, Doc, Test, Sec</strong> ...`, replace the four hardcoded names with `{{fact:live_plugin_names}}` (keep the surrounding `<strong>` and prose). Render the list inline for now; structure is star-map-ready (see spec §1.7).

- [ ] **Step 3: Fix the live staleness**

Find the cartographer product description containing "Eleven slash commands" in `content/site.json` and replace `Eleven` with `{{fact:cmd_vibe-cartographer_word}}`. In `content/plugin-pages.json`, replace the "Twelve commands" / "Twelve slash commands" literals on the cartographer page with `{{fact:cmd_vibe-cartographer_word}}` for consistency.

- [ ] **Step 4: Re-render and verify the fix**

Run:
```bash
python scripts/render-hub.py && python scripts/render-plugin-pages.py
grep -rn "Eleven slash" index.html ; echo "exit:$?"
grep -c "Twelve" index.html
grep -c "{{fact:" index.html
```
Expected: no "Eleven slash" match (grep exit 1); "Twelve" present; zero unresolved tokens.

- [ ] **Step 5: Commit**
```bash
git add content/site.json content/plugin-pages.json index.html plugins/
git commit -m "fix(content): tokenize counts + derive About list (Eleven->Twelve)"
```

---

## Task 7: `site-doctor.py` — prose-vs-facts check registry

**Files:**
- Create: `scripts/site-doctor.py`
- Test: `tests/test_site_doctor.py`

- [ ] **Step 1: Write the failing test**

`tests/test_site_doctor.py`:
```python
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import importlib
doctor = importlib.import_module("site-doctor".replace("-", "_")) \
    if (ROOT / "scripts" / "site_doctor.py").exists() else None
# site-doctor.py has a hyphen; import via runpy-safe module name:
import importlib.util
spec = importlib.util.spec_from_file_location("site_doctor", ROOT / "scripts" / "site-doctor.py")
site_doctor = importlib.util.module_from_spec(spec); spec.loader.exec_module(site_doctor)


def test_prose_check_passes_when_consistent():
    fcts = {"cmd_vibe-cartographer": 12, "cmd_vibe-cartographer_word": "Twelve"}
    text = "Twelve slash commands walk you from idea to ship."
    failures = site_doctor.check_prose(text, fcts, source="x")
    assert failures == []


def test_prose_check_fails_on_stale_count():
    fcts = {"cmd_vibe-cartographer": 12, "cmd_vibe-cartographer_word": "Twelve"}
    text = "Eleven slash commands walk you from idea to ship."
    failures = site_doctor.check_prose(text, fcts, source="x")
    assert failures and "slash commands" in failures[0]
```

- [ ] **Step 2: Run, verify fail**

Run: `python -m pytest tests/test_site_doctor.py -v`
Expected: FAIL — file not found / `check_prose` undefined.

- [ ] **Step 3: Implement the registry + `check_prose`**

`scripts/site-doctor.py` (registry portion):
```python
"""site-doctor.py — health checkup + CI gate for 626labs.dev content.

Modes: --report (human), --check (exit nonzero on any failure).
Validation rules live HERE and nowhere else (the shared contract's enforcer).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import site_facts  # noqa: E402

NUM_WORD_RE = "(One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve|Thirteen|Fourteen|Fifteen)"

# Curated check registry: (regex with one number-word group, fact key it must equal, human label).
# Only VOICE prose that mentions a count but is NOT tokenized needs a check here.
PROSE_CHECKS = [
    (re.compile(rf"\b{NUM_WORD_RE}\s+(?:slash\s+)?commands\b"), "cmd_vibe-cartographer_word", "slash commands"),
]


def check_prose(text: str, fcts: dict, source: str) -> list[str]:
    failures = []
    for rx, fact_key, label in PROSE_CHECKS:
        for m in rx.finditer(text):
            found = m.group(1)
            expected = fcts.get(fact_key)
            if expected is not None and found != expected:
                failures.append(
                    f"[{source}] '{label}': prose says '{found}' but facts say '{expected}'"
                )
    return failures
```

- [ ] **Step 4: Run, verify pass**

Run: `python -m pytest tests/test_site_doctor.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**
```bash
git add scripts/site-doctor.py tests/test_site_doctor.py
git commit -m "feat(doctor): prose-vs-facts curated check registry"
```

---

## Task 8: `site-doctor.py` — asset existence

**Files:**
- Modify: `scripts/site-doctor.py`
- Modify: `tests/test_site_doctor.py` (append)

- [ ] **Step 1: Write the failing test** (append)
```python
def test_asset_existence_flags_missing(tmp_path):
    obj = {"a": "/assets/exists.png", "b": "/assets/missing.png", "c": "https://x.com/y.png"}
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "exists.png").write_bytes(b"x")
    failures = site_doctor.check_assets(obj, root=tmp_path)
    assert any("missing.png" in f for f in failures)
    assert not any("exists.png" in f for f in failures)
    assert not any("x.com" in f for f in failures)  # remote URLs ignored
```

- [ ] **Step 2: Run, verify fail** — `check_assets` undefined.

- [ ] **Step 3: Implement** (append to `site-doctor.py`)
```python
ASSET_RE = re.compile(r"^/?assets/[\w./\-]+\.(png|jpg|jpeg|svg|webp|gif|ico)$", re.I)


def _walk_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_strings(v)
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_strings(v)


def check_assets(obj, root: Path = ROOT) -> list[str]:
    failures = []
    for s in _walk_strings(obj):
        if ASSET_RE.match(s.strip()):
            rel = s.strip().lstrip("/")
            if not (root / rel).exists():
                failures.append(f"dangling asset reference: {s}")
    return failures
```

- [ ] **Step 4: Run, verify pass.**

- [ ] **Step 5: Commit**
```bash
git add scripts/site-doctor.py tests/test_site_doctor.py
git commit -m "feat(doctor): dangling local-asset reference check"
```

---

## Task 9: `site-doctor.py` — render-drift wrap + CLI (`--report`/`--check`)

**Files:**
- Modify: `scripts/site-doctor.py`

- [ ] **Step 1: Implement the orchestrator + CLI** (append)
```python
def check_render_drift() -> list[str]:
    failures = []
    for script in ("render-hub.py", "render-plugin-pages.py"):
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script), "--check"],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            failures.append(f"render drift: {script} --check failed\n{r.stdout}{r.stderr}")
    return failures


def run() -> list[str]:
    fcts = site_facts.facts()
    site = json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))
    pages = json.loads((ROOT / "content" / "plugin-pages.json").read_text(encoding="utf-8"))
    failures = []
    for name, obj in (("site.json", site), ("plugin-pages.json", pages)):
        for s in _walk_strings(obj):
            failures += check_prose(s, fcts, source=name)
        failures += check_assets(obj)
    failures += check_render_drift()
    return failures


def main(argv) -> int:
    ap = argparse.ArgumentParser(description="626labs.dev content health doctor")
    ap.add_argument("--check", action="store_true", help="exit nonzero on any failure")
    ap.add_argument("--report", action="store_true", help="human-readable report")
    args = ap.parse_args(argv)
    failures = run()
    fcts = site_facts.facts()
    if args.report or not args.check:
        print("=== 626labs.dev health report ===")
        print(f"derived: {fcts['claude_plugins']} plugins, {fcts['family_count']} family, "
              f"{fcts['widget_count']} widget, {fcts['windows_native_count']} windows-native")
        print("supplement (re-confirm periodically): "
              f"ms_store_releases={fcts.get('ms_store_releases')}, "
              f"cmd_vibe-cartographer={fcts.get('cmd_vibe-cartographer')}")
        print(f"checks: {'PASS' if not failures else str(len(failures)) + ' FAILURE(S)'}")
        for f in failures:
            print(f"  - {f}")
    if args.check:
        return 1 if failures else 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 2: Run the checkup (this IS the Phase-1 checkup)**

Run: `python scripts/site-doctor.py --report`
Expected: prints derived facts + `checks: PASS` (after Task 6 fixes). If any failure prints, fix it inline and re-run.

- [ ] **Step 3: Verify the gate exit code**

Run: `python scripts/site-doctor.py --check ; echo "exit:$?"`
Expected: `exit:0`.

- [ ] **Step 4: Commit**
```bash
git add scripts/site-doctor.py
git commit -m "feat(doctor): render-drift wrap + --report/--check CLI"
```

---

## Task 10: CI — `content-health.yml` + `rebuild-hub.yml` trigger fix

**Files:**
- Create: `.github/workflows/content-health.yml`
- Modify: `.github/workflows/rebuild-hub.yml` (path triggers)

- [ ] **Step 1: Create the gate workflow**

`.github/workflows/content-health.yml`:
```yaml
name: content-health
on:
  pull_request:
    paths: ["content/**", "index.html", "plugins/**", "scripts/**", "assets/**", ".github/workflows/content-health.yml"]
  schedule:
    - cron: "0 13 * * 1"   # Mondays 13:00 UTC, alongside link-check
  workflow_dispatch:
permissions:
  contents: read
  issues: write
jobs:
  doctor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - name: Run site doctor
        id: doctor
        run: python scripts/site-doctor.py --check
      - name: Open issue on scheduled failure
        if: failure() && github.event_name == 'schedule'
        uses: actions/github-script@v7
        with:
          script: |
            await github.rest.issues.create({
              owner: context.repo.owner, repo: context.repo.repo,
              title: "Content health drift detected (scheduled run)",
              body: "`site-doctor.py --check` failed on the scheduled run. Run it locally with `--report` to see details."
            });
```

- [ ] **Step 2: Verify the doctor runs in a clean checkout locally**

Run: `python scripts/site-doctor.py --check ; echo "exit:$?"`
Expected: `exit:0`.

- [ ] **Step 3: Add the missing render triggers**

In `.github/workflows/rebuild-hub.yml`, add `content/plugin-pages.json` and `content/facts-supplement.json` to the `on.push.paths` list (hero tokens now derive from them).

- [ ] **Step 4: Commit**
```bash
git add .github/workflows/content-health.yml .github/workflows/rebuild-hub.yml
git commit -m "ci(content): doctor gate on PRs + schedule; widen rebuild-hub triggers"
```

---

## Task 11: Full run, README note, push, PR

**Files:**
- Modify: `CLAUDE.md` (add a one-liner under Scripts pointing at the doctor)

- [ ] **Step 1: Full test + checkup**
```bash
python -m pytest -q
python scripts/site-doctor.py --report
python scripts/render-hub.py --check && python scripts/render-plugin-pages.py --check
```
Expected: all tests pass; `checks: PASS`; both `--check` exit 0.

- [ ] **Step 2: Document the doctor in `CLAUDE.md`**

Under the Scripts section, add:
```markdown
### Content health — `scripts/site-doctor.py`
Facts-vs-prose drift check, dangling-asset check, render-drift wrap.
`--report` for an on-demand checkup; `--check` for CI (exits nonzero on drift).
Facts derive via `scripts/site_facts.py`; external truths live in
`content/facts-supplement.json`.
```

- [ ] **Step 3: Commit + push + PR**
```bash
git add CLAUDE.md
git commit -m "docs: document site-doctor content-health tooling"
git push -u origin feat/site-mgmt-m1
gh pr create --title "feat: site management plane M1 — health & reactivity guardrail" \
  --body "Implements M1 of the site management plane (spec: docs/superpowers/specs/2026-05-23-site-management-plane-design.md). Facts derive from existing sources; data-like prose self-fills via {{fact:...}} tokens; voice prose fails loud on drift; CI gate on PRs. First doctor run fixed the live 'Eleven slash commands' staleness (now Twelve).

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```

---

## Self-review

**Spec coverage (M1 sections):**
- §1.1 site_facts → Tasks 2, 3 ✓
- §1.2 facts-supplement → Task 3 ✓
- §1.3 doctor (prose/asset/render-drift, --report/--check) → Tasks 7, 8, 9 ✓
- §1.4 token-fill in renderers → Tasks 4, 5 ✓
- §1.5 CI (content-health + rebuild-hub triggers) → Task 10 ✓
- §1.6 Phase-1 fixes (Eleven→Twelve, hero tuple, asset paths) → Task 6 + doctor run Task 9 ✓
- §1.7 derive About list (star-map-ready) → Task 6 ✓

**Placeholder scan:** none — every code step has complete code; content edits name exact strings/files.

**Type/name consistency:** `derive(site, pages, supplement)`, `facts()`, `resolve_tokens(obj, fct)`, `number_word(n)`, `check_prose(text, fcts, source)`, `check_assets(obj, root)`, `check_render_drift()`, `run()`, `main(argv)` — consistent across tasks. `num_word` retained in render-plugin-pages as a thin wrapper over `site_facts.number_word`.

**Note on the doctor filename:** `site-doctor.py` has a hyphen (matches sibling `render-hub.py` convention) so tests import it via `importlib.util.spec_from_file_location` (Task 7 Step 1). `site_facts.py` uses an underscore because it is imported as a normal module.
