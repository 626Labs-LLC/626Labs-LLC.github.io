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


def _product_block_span(text: str, product_id: str) -> tuple[int, int]:
    """(start, end) char span of a product object, bounded by the next id."""
    m = re.search(r'"id":\s*"' + re.escape(product_id) + r'"', text)
    if not m:
        raise ValueError(f"product not found: {product_id}")
    start = m.end()
    nxt = re.search(r'"id":\s*"', text[start:])
    end = start + nxt.start() if nxt else len(text)
    return start, end


def set_field_in_text(text: str, product_id: str, field: str, new_value: str) -> str:
    """Replace a product's string field value in place, preserving formatting."""
    start, end = _product_block_span(text, product_id)
    block = text[start:end]
    pat = re.compile(r'("' + re.escape(field) + r'":\s*")([^"]*)(")')
    new_block, n = pat.subn(
        r"\g<1>" + new_value.replace("\\", "\\\\") + r"\g<3>", block, count=1
    )
    if n != 1:
        raise ValueError(f"string field '{field}' not found for {product_id}")
    return text[:start] + new_block + text[end:]


def array_append_in_text(text: str, array_key: str, element_text: str,
                         search_from: int = 0) -> str:
    """Append element_text to the named array, preserving formatting. Handles
    empty and non-empty arrays (inline or multi-line). Format-preserving, valid
    JSON. Indentation is derived from the array key's line, so it is correct
    even for an inline empty array like `"items": []`."""
    m = re.search(r'"' + re.escape(array_key) + r'":\s*\[', text[search_from:])
    if not m:
        raise ValueError(f"array not found: {array_key}")
    key_abs = search_from + m.start()
    open_idx = search_from + m.end()
    key_line_start = text.rfind("\n", 0, key_abs) + 1
    key_indent = text[key_line_start:key_abs]  # leading whitespace before the key
    elem_indent = key_indent + "  "
    depth, i = 1, open_idx
    while depth:
        c = text[i]
        depth += (c == "[") - (c == "]")
        i += 1
    close = i - 1
    inner = text[open_idx:close]
    if inner.strip() == "":  # empty array -> expand it
        return (
            text[:open_idx] + "\n" + elem_indent + element_text + "\n"
            + key_indent + text[close:]
        )
    before = text[:close].rstrip()  # non-empty: comma after prev last element
    return (
        before + ",\n" + elem_indent + element_text + "\n" + key_indent + text[close:]
    )


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


def _on_main() -> bool:
    r = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True
    )
    return r.stdout.strip() in ("main", "master")


def _maybe_commit(args, message, paths=("content/site.json", "index.html")) -> int:
    if getattr(args, "commit", False):
        if _on_main():
            print("refusing to commit on main — switch to a branch.", file=sys.stderr)
            return 1
        subprocess.run(["git", "add", *paths], check=True)
        subprocess.run(["git", "commit", "-m", message], check=True)
        print("committed.")
    return 0


def cmd_facts(_args) -> int:
    print(json.dumps(site_facts.facts(), indent=2, ensure_ascii=False))
    return 0


def cmd_get(args) -> int:
    data = json.loads(SITE_JSON.read_text(encoding="utf-8"))
    if args.section not in data:
        print(
            f"no such section: {args.section}. available: {', '.join(data)}",
            file=sys.stderr,
        )
        return 2
    print(json.dumps(data[args.section], indent=2, ensure_ascii=False))
    return 0


def cmd_doctor(args) -> int:
    argv = ["--check"] if args.check else ["--report"]
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "site-doctor.py"), *argv]
    ).returncode


def cmd_render(_args) -> int:
    render_all()
    print("rendered index.html + plugin pages.")
    return 0


def cmd_ops(_args) -> int:
    try:
        return subprocess.run(["gh", "run", "list", "--limit", "8"]).returncode
    except FileNotFoundError:
        print("gh CLI not found — install it to see CI run status.", file=sys.stderr)
        return 2


def cmd_set_status(args) -> int:
    data = json.loads(SITE_JSON.read_text(encoding="utf-8"))
    product = next(
        (p for p in data.get("products", []) if p.get("id") == args.id), None
    )
    if product is None:
        print(f"no product with id: {args.id}", file=sys.stderr)
        return 2
    if product.get("status") == args.status:
        print(f"{args.id} is already '{args.status}' — no change.")
        return 0
    text = SITE_JSON.read_text(encoding="utf-8")
    new_text = set_status_in_text(text, args.id, args.status)
    ok, detail = guarded_apply(SITE_JSON, new_text)
    if not ok:
        print(
            f"refused: setting {args.id} -> {args.status} fails the doctor:\n{detail}",
            file=sys.stderr,
        )
        return 1
    print(f"set {args.id} status -> {args.status} (validated).")
    return _maybe_commit(args, f"content: set {args.id} status to {args.status}")


def cmd_set_product(args) -> int:
    data = json.loads(SITE_JSON.read_text(encoding="utf-8"))
    product = next(
        (p for p in data.get("products", []) if p.get("id") == args.id), None
    )
    if product is None:
        print(f"no product with id: {args.id}", file=sys.stderr)
        return 2
    if str(product.get(args.field)) == args.value:
        print(f"{args.id}.{args.field} is already '{args.value}' — no change.")
        return 0
    text = SITE_JSON.read_text(encoding="utf-8")
    try:
        new_text = set_field_in_text(text, args.id, args.field, args.value)
    except ValueError as e:
        print(f"cannot set {args.id}.{args.field}: {e}", file=sys.stderr)
        return 2
    ok, detail = guarded_apply(SITE_JSON, new_text)
    if not ok:
        print(
            f"refused: {args.id}.{args.field} -> {args.value} fails the doctor:\n{detail}",
            file=sys.stderr,
        )
        return 1
    print(f"set {args.id}.{args.field} -> {args.value} (validated).")
    return _maybe_commit(args, f"content: set {args.id} {args.field}")


def product_skeleton(pid: str, title: str, tagline: str, claude_code: bool) -> str:
    obj = {
        "id": pid, "title": title, "tagline": tagline, "description": "",
        "tags": [], "status": "wip", "repo": "", "npm": "", "install": "",
        "claudeCode": claude_code, "screenshots": [],
    }
    return json.dumps(obj, ensure_ascii=False)


def cmd_add_plugin(args) -> int:
    data = json.loads(SITE_JSON.read_text(encoding="utf-8"))
    if any(p.get("id") == args.id for p in data.get("products", [])):
        print(f"product id already exists: {args.id}", file=sys.stderr)
        return 2
    text = SITE_JSON.read_text(encoding="utf-8")
    element = product_skeleton(args.id, args.title, args.tagline or "",
                              claude_code=args.claude_code)
    new_text = array_append_in_text(text, "products", element)
    ok, detail = guarded_apply(SITE_JSON, new_text)
    if not ok:
        print(f"refused: add-plugin {args.id} fails the doctor:\n{detail}", file=sys.stderr)
        return 1
    print(f"added product '{args.id}' (status: wip). Fill in description/tags/repo "
          f"next, and create its landing page in content/plugin-pages.json if it's "
          f"a Claude Code plugin.")
    return _maybe_commit(args, f"content: add product {args.id}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="site.py", description="626labs.dev management CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("facts", help="print derived facts").set_defaults(fn=cmd_facts)
    g = sub.add_parser("get", help="print a section of site.json")
    g.add_argument("section")
    g.set_defaults(fn=cmd_get)
    d = sub.add_parser("doctor", help="health checkup")
    d.add_argument("--check", action="store_true")
    d.set_defaults(fn=cmd_doctor)
    sub.add_parser("render", help="re-render site").set_defaults(fn=cmd_render)
    sub.add_parser("ops", help="recent CI runs (needs gh)").set_defaults(fn=cmd_ops)
    s = sub.add_parser("set-status", help="flip a product's status (guarded)")
    s.add_argument("id")
    s.add_argument("status", choices=["live", "wip"])
    s.add_argument("--commit", action="store_true", help="commit on current branch (not main)")
    s.set_defaults(fn=cmd_set_status)
    sp = sub.add_parser("set-product", help="set a product string field (guarded)")
    sp.add_argument("id")
    sp.add_argument("field")
    sp.add_argument("value")
    sp.add_argument("--commit", action="store_true")
    sp.set_defaults(fn=cmd_set_product)
    ap2 = sub.add_parser("add-plugin", help="append a skeleton product (guarded)")
    ap2.add_argument("id")
    ap2.add_argument("--title", required=True)
    ap2.add_argument("--tagline", default="")
    ap2.add_argument("--claude-code", dest="claude_code", action="store_true")
    ap2.add_argument("--commit", action="store_true")
    ap2.set_defaults(fn=cmd_add_plugin)
    return ap


def main(argv) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
