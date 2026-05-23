#!/usr/bin/env python3
"""site.py — agent-facing management CLI for 626labs.dev.

The agent equivalent of the admin dashboard. Read verbs inspect; mutation verbs
edit content with FORMAT-PRESERVING surgical edits (never parse->dump, which
would explode the hand-formatted JSON), then validate via render + doctor and
auto-revert if the edit would introduce drift.

Verbs:
  facts                       print derived facts
  get <section>               print a section of content/site.json
  doctor [--check]            run the health checkup
  render                      re-render index.html + plugin pages
  ops                         recent CI run status (needs gh)
  set-status <id> <live|wip>  flip a product's status (guarded)

Mutation verbs validate before they stand. Default leaves the validated change
in the working tree; --commit commits on the current branch (refuses on main).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
SITE_JSON = ROOT / "content" / "site.json"
sys.path.insert(0, str(SCRIPTS))
import site_facts  # noqa: E402


def set_status_in_text(text: str, product_id: str, new_status: str) -> str:
    """Replace one product's status value in-place, preserving all formatting.
    Locate the product by id, bound the search by the next id so a sibling is
    never touched, and swap the single status value."""
    id_pat = re.compile(r'"id":\s*"' + re.escape(product_id) + r'"')
    m = id_pat.search(text)
    if not m:
        raise ValueError(f"product not found: {product_id}")
    start = m.end()
    nxt = re.search(r'"id":\s*"', text[start:])
    end = start + nxt.start() if nxt else len(text)
    block = text[start:end]
    new_block, n = re.subn(
        r'("status":\s*")(live|wip)(")',
        r"\g<1>" + new_status + r"\g<3>",
        block,
        count=1,
    )
    if n != 1:
        raise ValueError(f"status field not found for {product_id}")
    return text[:start] + new_block + text[end:]


def render_all() -> None:
    for script in ("render-hub.py", "render-plugin-pages.py"):
        subprocess.run(
            [sys.executable, str(SCRIPTS / script)],
            check=True, capture_output=True, text=True,
        )


def doctor_validate() -> tuple[bool, str]:
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "site-doctor.py"), "--check"],
        capture_output=True, text=True,
    )
    return r.returncode == 0, r.stdout + r.stderr


def guarded_apply(source_path: Path, new_text: str, *,
                  render_fn=render_all, validate_fn=doctor_validate) -> tuple[bool, str]:
    """Write new_text, render, validate. Revert source + re-render on failure."""
    original = source_path.read_text(encoding="utf-8")
    source_path.write_text(new_text, encoding="utf-8", newline="\n")
    render_fn()
    ok, detail = validate_fn()
    if not ok:
        source_path.write_text(original, encoding="utf-8", newline="\n")
        render_fn()
        return False, detail
    return True, detail
