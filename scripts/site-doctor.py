"""site-doctor.py — health checkup + CI gate for 626labs.dev content.

Modes:
  --report   human-readable report (default)
  --check    exit nonzero on any failure (for CI)

Validation rules live HERE and nowhere else — this is the shared contract's
enforcer. Every write path (human admin, agent CLI, agent MCP) funnels through
the CI gate that runs this, so no other surface re-implements the rules.

Checks:
  1. prose-vs-facts  — a curated registry; literal counts in voice prose that
                       contradict the derived/supplemented facts.
  2. asset existence — local /assets/... references that don't exist on disk.
  3. render drift    — render-hub.py --check and render-plugin-pages.py --check.
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

NUM_WORD_RE = (
    "(One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve|"
    "Thirteen|Fourteen|Fifteen)"
)

# Curated check registry: (regex with one number-word group, fact key it must
# equal, human label). Only VOICE prose mentioning a count but NOT tokenized
# needs a check here. Each rule is scoped to a specific phrasing to avoid
# false-positives against other plugins' own counts.
PROSE_CHECKS = [
    (
        re.compile(rf"\b{NUM_WORD_RE}\s+slash\s+commands\b"),
        "cmd_vibe-cartographer_word",
        "cartographer slash commands",
    ),
]

ASSET_RE = re.compile(r"^/?assets/[\w./\-]+\.(png|jpg|jpeg|svg|webp|gif|ico)$", re.I)


def check_prose(text: str, fcts: dict, source: str) -> list[str]:
    failures = []
    for rx, fact_key, label in PROSE_CHECKS:
        for m in rx.finditer(text):
            found = m.group(1)
            expected = fcts.get(fact_key)
            if expected is not None and found != expected:
                failures.append(
                    f"[{source}] {label}: prose says '{found}' but facts say '{expected}'"
                )
    return failures


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


def check_render_drift() -> list[str]:
    failures = []
    for script in ("render-hub.py", "render-plugin-pages.py"):
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script), "--check"],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            failures.append(
                f"render drift: {script} --check failed\n{r.stdout}{r.stderr}".rstrip()
            )
    return failures


def run() -> list[str]:
    fcts = site_facts.facts()
    site = json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))
    pages = json.loads(
        (ROOT / "content" / "plugin-pages.json").read_text(encoding="utf-8")
    )
    failures: list[str] = []
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
        print(
            f"derived: {fcts['claude_plugins']} plugins, "
            f"{fcts['family_count']} family, {fcts['widget_count']} widget, "
            f"{fcts['windows_native_count']} windows-native"
        )
        print(
            "supplement (re-confirm periodically): "
            f"ms_store_releases={fcts.get('ms_store_releases')}, "
            f"cmd_vibe-cartographer={fcts.get('cmd_vibe-cartographer')}"
        )
        print(f"checks: {'PASS' if not failures else str(len(failures)) + ' FAILURE(S)'}")
        for f in failures:
            print(f"  - {f}")

    if args.check:
        return 1 if failures else 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
