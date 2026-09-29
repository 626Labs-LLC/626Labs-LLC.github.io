"""Rebuild the year-in-review page from its parts.

    python docs/year-in-review/build.py out.html

page.tpl.html holds the layout, styles and script. The three data files fill its
placeholders: page-data.json (events), map.json (Store installs by market with
country geometry), activity.json (commits per day). Output is a single
self-contained HTML file.
"""
import sys
from pathlib import Path

here = Path(__file__).parent
tpl = (here / "page.tpl.html").read_text(encoding="utf-8")
for key, name in (("__DATA__", "page-data.json"), ("__MAP__", "map.json"), ("__ACT__", "activity.json")):
    tpl = tpl.replace(key, (here / name).read_text(encoding="utf-8"))
Path(sys.argv[1] if len(sys.argv) > 1 else "year-one.html").write_text(tpl, encoding="utf-8", newline="\n")
