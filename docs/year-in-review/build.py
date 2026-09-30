"""Rebuild the year-in-review page from its parts.

    python docs/year-in-review/build.py out.html                     # standalone
    python docs/year-in-review/build.py out.html --theme <slug>      # hosted on the hub

page.tpl.html holds the layout, styles and script. The three data files fill its
placeholders: page-data.json (events), map.json (Store installs by market with
country geometry), activity.json (commits per day).

Standalone keeps the page's own light and dark palette and loads Google Fonts.
It is what the private artifact used.

Hosted (--theme) binds every color and font to the hub's theme contract
(scripts/archetypes.py REQUIRED_TOKENS: --bg-0/1, --fg-1/3, --border-2, --cyan,
--magenta, --ok, --warn, --font-*) and links /themes/<slug>/tokens.css and
/fonts/fonts.css instead. The page keeps only namespaced --y-* tokens, so a
rotation changes the page by swapping the slug in that one <link> and nothing
else. Colors follow the theme, so the page never carries its own light/dark switch
when hosted.
"""
import re
import sys
from pathlib import Path

here = Path(__file__).parent
args = sys.argv[1:]
theme = args[args.index("--theme") + 1] if "--theme" in args else None
if theme:
    del args[args.index("--theme"):args.index("--theme") + 2]
out = args[0] if args else "year-one.html"

tpl = (here / "page.tpl.html").read_text(encoding="utf-8")
for key, name in (("__DATA__", "page-data.json"), ("__MAP__", "map.json"), ("__ACT__", "activity.json")):
    tpl = tpl.replace(key, (here / name).read_text(encoding="utf-8"))

if theme:
    tpl = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>\n?', "", tpl)
    tpl = tpl.replace(
        "<!--__THEME_LINK__-->",
        f'<link rel="stylesheet" href="/fonts/fonts.css">\n'
        f'<link rel="stylesheet" href="/themes/{theme}/tokens.css">',
    )
    tpl = tpl.replace(
        "/*__THEME_MAP__*/",
        ":root:root:root{--y-bg:var(--bg-0);--y-panel:var(--bg-1);--y-fg:var(--fg-1);"
        "--y-dim:var(--fg-3);--y-line:var(--border-2);--y-cyan:var(--cyan);"
        "--y-mag:var(--magenta);--y-ok:var(--ok);--y-warn:var(--warn);"
        "--y-f-display:var(--font-display);--y-f-body:var(--font-body);"
        "--y-f-mono:var(--font-mono)}",
    )
    # The artifact viewer supplies the document shell, title and meta; a hosted
    # page needs its own, matching what the other hand-authored pages carry
    # (conundrum.html is the reference).
    tpl = tpl.replace(
        "<title>626 Labs Year One</title>",
        '<title>The Year in Review · From a Roblox game to 165 markets · 626 Labs</title>\n'
        '<meta name="description" content="Where 626 Labs actually came from: a dated timeline '
        'from the first Roblox game through Store reach in 165 markets, with a commit heatmap and '
        'an install map.">\n'
        '<meta property="og:title" content="626 Labs, the Year in Review">\n'
        '<meta property="og:description" content="From a Roblox game to 165 markets '
        '— the dated timeline.">\n'
        '<meta property="og:type" content="website">\n'
        '<meta property="og:url" content="https://626labs.dev/year-in-review.html">\n'
        '<meta property="og:image" content="https://626labs.dev/assets/brand/medium-header-1500x600.png">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        '<link rel="icon" type="image/png" href="favicon-626.png">\n'
        '<link rel="canonical" href="https://626labs.dev/year-in-review.html">',
    )
    head, rest = tpl.split("</style>", 1)
    shell_open = (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    )
    tpl = shell_open + head + "</style>\n</head>\n<body>" + rest + "\n</body>\n</html>\n"
else:
    tpl = tpl.replace("<!--__THEME_LINK__-->", "").replace("/*__THEME_MAP__*/", "")

Path(out).write_text(tpl, encoding="utf-8", newline="\n")
