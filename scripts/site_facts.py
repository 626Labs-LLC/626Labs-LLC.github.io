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
PLUGIN_STATS_JSON = ROOT / "data" / "plugin-stats.json"
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
    return sum(
        1 for p in APPS_DIR.iterdir() if p.is_dir() and p.name.startswith("widget-")
    )


def derive(site: dict, pages: dict, supplement: dict, stats: dict | None = None) -> dict:
    stats = stats or {}
    products = site.get("products", [])
    live = [p for p in products if is_claude_plugin(p) and p.get("status") == "live"]
    wip = [p for p in products if is_claude_plugin(p) and p.get("status") == "wip"]
    win_native = [
        p for p in products if not is_claude_plugin(p) and _has_tag(p, "Windows")
    ]
    family = pages.get("family", [])
    widgets = _widget_count()

    f: dict = {
        "claude_plugins": len(live),
        "claude_plugins_word": number_word(len(live)),
        "claude_plugins_wip": len(wip),
        "claude_plugins_wip_word": number_word(len(wip)),
        "family_count": len(family),
        "family_count_word": number_word(len(family)),
        "windows_native_count": len(win_native),
        "windows_native_count_word": number_word(len(win_native)),
        "widget_count": widgets,
        "widget_count_word": number_word(widgets),
        "live_plugin_names": ", ".join(display_name(p) for p in live),
    }

    # Live per-plugin command counts, derived from data/plugin-stats.json (the same
    # repo-tree source as the capability chips). Exposes cmd_<id> + cmd_<id>_word for
    # every plugin so card copy can reference a count that can't drift. "commands" is
    # the raw command-file count — command-as-skill plugins read 0, matching the chip.
    # The supplement loop below runs last, so a manual override is still possible.
    for pid, s in stats.items():
        if not isinstance(s, dict):
            continue
        n = int(s.get("commands", 0) or 0)
        f[f"cmd_{pid}"] = n
        f[f"cmd_{pid}_word"] = number_word(n)

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
    stats = (
        json.loads(PLUGIN_STATS_JSON.read_text(encoding="utf-8"))
        if PLUGIN_STATS_JSON.exists()
        else {}
    )
    return derive(site, pages, supplement, stats)


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
