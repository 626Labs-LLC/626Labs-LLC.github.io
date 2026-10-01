#!/usr/bin/env python3
"""Token gate for the paper-and-ink sheets.

A sheet passes when every color literal it uses is either (a) a var() of an
--ed-* / --brand-* / --ink-* / --pi-<slug>-* token, or (b) a raw color that
appears ONLY as the value of an --pi-<slug>-* declaration inside the sheet's
own :root { } block. Raw hex/rgb/hsl anywhere else — including inside :root
but not bound to an --pi-* custom property (e.g. a literal `background:
#fff;` sitting in the root block) — fails. Usage: check-tokens.py sheet.html

Tightened from the task-C1-brief draft (documented, see task-C1-report.md):
the draft computed a `bad_decl` list — raw colors found inside :root — but
never consulted it in the pass/fail decision, and its skip condition
("not re.search(r'--ed-|--brand-|--ink-', declared)") tested the WHOLE
concatenated :root text rather than the color's own declaration, so a
single unrelated var(--ed-*) reference anywhere in a sheet's :root block
would silently exempt every raw color in that block, including ones never
bound to an --pi-* token. Replaced with a strip-then-scan pass: every
`--pi-<slug>-*: <color>;` declaration is removed from the declared text,
then any color literal still standing in what's left is a violation.
"""
import re, sys
from pathlib import Path

src = Path(sys.argv[1]).read_text(encoding="utf-8")
root_blocks = re.findall(r":root\s*\{[^}]*\}", src)
declared = "\n".join(root_blocks)
body = src
for b in root_blocks:
    body = body.replace(b, "")

COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)|hsla?\([^)]*\)")

# Fail condition 1: any raw color literal outside a :root block entirely.
loose = COLOR.findall(body)

# Fail condition 2: raw color literals inside :root that are not bound to
# an --pi-<slug>-* custom property. Strip every valid `--pi-*: <color>;`
# declaration out of the declared text first, then anything left that still
# matches COLOR is unbound.
AT_DECL = re.compile(
    r"--pi-[a-z0-9-]+\s*:\s*"
    r"(?:#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)|hsla?\([^)]*\))\s*;?"
)
declared_stripped = AT_DECL.sub("", declared)
bad_decl = COLOR.findall(declared_stripped)

problems = []
if loose:
    problems.append(f"{len(loose)} raw color(s) outside :root block(s):")
    problems += ["    " + m for m in sorted(set(loose))]
if bad_decl:
    problems.append(
        f"{len(bad_decl)} raw color(s) inside :root not bound to an --pi-* declaration:"
    )
    problems += ["    " + m for m in sorted(set(bad_decl))]

if problems:
    print(f"FAIL {sys.argv[1]}:")
    for line in problems:
        print(" ", line)
    sys.exit(1)

print(f"PASS {sys.argv[1]}: colors confined to declared --pi-* tokens.")
