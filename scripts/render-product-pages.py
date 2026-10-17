"""Render the app and product pages from content/site.json.

The plugin pages have been generated since A5 (render-plugin-pages.py); the
app and product pages were hand-authored, one file each, with their own CSS,
chrome and footer, so every site-wide change had to be made once per page and
every page needed its own registrations. This renderer is the second half of
issue #200: a product in site.json that carries a `pageSpec` block gets its
page generated from that block, at the path its `productPage` URL names.

    python scripts/render-product-pages.py                 # write every page
    python scripts/render-product-pages.py --check         # drift gate, exit 1 if stale
    python scripts/render-product-pages.py --list-outputs  # one repo-relative path per line
    python scripts/render-product-pages.py --theme <slug> --out <dir>   # preview

Why a renderer beside render-plugin-pages.py rather than inside it: the two
read different sources (content/plugin-pages.json there, content/site.json
here), wear different dresses (the theme's archetypes/product.css there, the
token half plus scripts/product-page.css here, because product pages recolor
monthly and do not re-layout), and have nothing in common past the head
boilerplate. One file holding both would be two renderers sharing a name.

THE SCHEMA. `productPage` stays the URL string the home row and the page-pane
mod read; its type never changes. The page lives in a sibling block:

    "productPage": "etsy-mcp.html",
    "pageSpec": {
      "meta":     {title, description, ogTitle, ogDescription, ogImage},
      "releaseReviewed": ["owner/repo@tag", ...],      optional
      "nav":      [{label, href, cta?, hideSm?}],
      "sections": [ {type: "hero", ...}, {type: "section", ...}, ... ],
      "footer":   {label, disclaimer?}
    }

Sections render in order. A `hero` section is the page header (eyebrow,
title + titleAccent, dek, fine, a key/value `strip`, a `get` strip of Store
and source links; `"align": "center"` for a game's splash); a `section`
section is `<section>` + its heading (optional: a section without one renders
its blocks alone) + an ordered list of `blocks`. Each block type is one
partial below (BLOCKS): widget (games only), lead, cards (optional per-card
tag), callout, trust (optional code list), status, contact, stats, shots,
reachMap. `shots` reads the product's own
uploader-managed `screenshots` list and renders nothing while it is empty. Field convention, same as
plugin-pages.json: labels, headings, keys and titles are ESCAPED; body copy
(dek, paragraphs, card and row bodies, captions) is RAW HTML, so inline
<b>, <code> and <a> work. Copy keeps living in site.json.

GAMES. An entry in `play.widgets` that carries a `pageSpec` (and a
`productPage` URL) is rendered the same way: games are pages too, not
products, so they keep living where the home Play row reads them. A game's
`widget` block mounts the game from the entry's own `script`, `stylesheet`,
`initFn` and `config` (the block's `config` overrides keys), so the page and
the home row can never disagree about which build plays. `pageSpec.aliases`
lists extra local paths that render the same page with the canonical
pointing at `productPage` (play/bacon/ is the legacy duplicate of
/bacon-trail/).

Every generated page carries, without per-page wiring: the theme's token
link, GoatCounter, the footer signature, the release-reviewed markers its
spec names, and the repo meter whenever the product has a `repo`.
"""
from __future__ import annotations

import json
import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import site_facts  # noqa: E402  sibling module
import theme_registry  # noqa: E402  sibling module

SITE_JSON = ROOT / "content" / "site.json"
STYLE_PATH = SCRIPTS / "product-page.css"
SITE_ORIGIN = "https://626labs.dev"

# The one theme stylesheet a generated page links: the TOKEN half of the
# product archetype. theme-doctor's resolution groups and render-hub.py's
# preview read this constant rather than repeating the path.
THEME_CSS_HREF = "archetypes/product-tokens.css"

GOATCOUNTER = (
    "<!-- GoatCounter — privacy-friendly, cookieless analytics. See goatcounter.com. -->\n"
    '<script data-goatcounter="https://626labs.goatcounter.com/count"\n'
    '        async src="//gc.zgo.at/count.js"></script>\n'
)


def e(s) -> str:
    return escape(str(s), quote=True)


# ─── which products get a page, and where ─────────────────────────────────

def _products(content: dict) -> list[dict]:
    products = content.get("products") or []
    if isinstance(products, dict):
        products = products.get("items") or list(products.values())
    return [p for p in products if isinstance(p, dict)]


def _games(content: dict) -> list[dict]:
    widgets = (content.get("play") or {}).get("widgets") or []
    return [w for w in widgets if isinstance(w, dict)]


def _page_sources(content: dict) -> list[tuple[str, dict]]:
    """(source label, entry) for every entry that renders a page: products
    first, then games. The label names where the copy lives, for the
    generated-file banner."""
    return ([("products", p) for p in _products(content) if p.get("pageSpec")]
            + [("play.widgets", w) for w in _games(content) if w.get("pageSpec")])


def _local_rel(url: str, pid: str, what: str) -> str:
    if "://" in url or url.startswith("//") or ".." in url or "?" in url or "#" in url:
        raise ValueError(f"{pid}: {what} {url!r} is not a local page path")
    rel = url.lstrip("/")
    if rel.endswith("/"):
        rel += "index.html"
    if not rel.endswith(".html"):
        raise ValueError(f"{pid}: {what} {url!r} must end in .html or /")
    return rel


def alias_rels(product: dict) -> list[str]:
    """Extra paths the same page renders to; the canonical stays productPage."""
    pid = product.get("id", "?")
    aliases = (product.get("pageSpec") or {}).get("aliases") or []
    return [_local_rel(a, pid, "pageSpec.aliases entry") for a in aliases]


def output_rel(product: dict) -> str:
    """The repo-relative file a product's page renders to, from its
    `productPage` URL. Same-origin and local only: `x.html` or `/x.html`
    renders to x.html, `/x/` to x/index.html. Anything else is an error,
    because a pageSpec that cannot be served at the URL the home row links is
    a page nobody reaches."""
    url = product.get("productPage")
    pid = product.get("id", "?")
    if not isinstance(url, str) or not url:
        raise ValueError(f"{pid}: pageSpec needs a productPage URL to render to")
    return _local_rel(url, pid, "productPage")


def page_url(rel: str) -> str:
    return f"{SITE_ORIGIN}/{rel[:-len('index.html')] if rel.endswith('index.html') else rel}"


def load_content(root: Path = ROOT) -> dict:
    content = json.loads((root / "content" / "site.json").read_text(encoding="utf-8"))
    return site_facts.resolve_tokens(content, site_facts.facts())


def generated_pages(root: Path = ROOT) -> list[str]:
    """Repo-relative paths of every page this renderer owns, sorted. Read
    straight from site.json with no token resolution, so theme-doctor,
    render-hub.py and the tests can ask cheaply. This is the "every generated
    product page" list the per-page registrations were replaced with."""
    content = json.loads((root / "content" / "site.json").read_text(encoding="utf-8"))
    rels = []
    for _, p in _page_sources(content):
        rels.append(output_rel(p))
        rels.extend(alias_rels(p))
    return sorted(rels)


# ─── head, chrome, footer ─────────────────────────────────────────────────

def _style() -> str:
    return STYLE_PATH.read_text(encoding="utf-8")


def _uses(spec: dict, block_type: str) -> bool:
    for s in spec.get("sections", []):
        if s.get("type") == block_type:
            return True
        if any(b.get("type") == block_type for b in s.get("blocks", [])):
            return True
    return False


def render_head(product: dict, spec: dict, rel: str, slug: str, source: str = "products") -> str:
    meta = spec["meta"]
    url = page_url(rel)
    og_image = meta["ogImage"]
    if og_image.startswith("/"):
        og_image = SITE_ORIGIN + og_image
    markers = "".join(
        f'<meta name="release-reviewed" content="{e(m)}" />\n'
        for m in spec.get("releaseReviewed") or []
    )
    meter = ""
    if product.get("repo"):
        meter = ('<link rel="stylesheet" href="/repo-meter/meter.css" />\n'
                 '<script src="/repo-meter/meter.js" defer></script>\n')
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8" />\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1" />\n'
        f"{markers}"
        f"<title>{e(meta['title'])}</title>\n"
        f'<meta name="description" content="{e(meta["description"])}" />\n'
        f'<link rel="canonical" href="{e(url)}" />\n'
        f'<meta property="og:title" content="{e(meta["ogTitle"])}" />\n'
        f'<meta property="og:description" content="{e(meta["ogDescription"])}" />\n'
        '<meta property="og:type" content="website" />\n'
        f'<meta property="og:url" content="{e(url)}" />\n'
        f'<meta property="og:image" content="{e(og_image)}" />\n'
        '<meta name="twitter:card" content="summary_large_image" />\n'
        '<link rel="icon" type="image/png" href="/favicon-626.png" />\n'
        "\n"
        "<!-- Generated by scripts/render-product-pages.py from content/site.json "
        f"({e(source)}[id={e(product['id'])}].pageSpec). Do not hand-edit. -->\n"
        f'<link rel="stylesheet" href="/themes/{e(slug)}/{THEME_CSS_HREF}">\n'
        f"{meter}"
        "\n"
        f"<style>\n{_style()}</style>\n"
        '<link rel="stylesheet" href="/assets/logos/signature.css">\n'
        "</head>\n"
    )


def render_nav(spec: dict) -> str:
    links = []
    for link in spec.get("nav") or []:
        classes = []
        if link.get("cta"):
            classes.append("cta")
        if link.get("hideSm"):
            classes.append("hide-sm")
        cls = f' class="{" ".join(classes)}"' if classes else ""
        links.append(f'      <a{cls} href="{e(link["href"])}">{e(link["label"])}</a>')
    return (
        '<div class="grid-bg" aria-hidden="true"></div>\n\n'
        '<nav class="topnav">\n'
        '  <div class="topnav-inner">\n'
        '    <a class="brand" href="index.html"><span class="mark"></span>626 Labs</a>\n'
        '    <div class="links">\n'
        + "\n".join(links) + "\n"
        "    </div>\n"
        "  </div>\n"
        "</nav>\n"
    )


def render_footer(spec: dict) -> str:
    foot = spec.get("footer") or {}
    disclaimer = (
        f'  <span class="disclaimer">{e(foot["disclaimer"])}</span>\n'
        if foot.get("disclaimer") else ""
    )
    return (
        "<footer>\n"
        f"  <span>{e(foot.get('label', '626 Labs'))}</span>\n"
        f"{disclaimer}"
        '  <span><a href="index.html">626labs.dev</a> · Imagine Something Else.</span>\n'
        '  <a class="site-signature" href="/" aria-label="626Labs, home"></a>\n'
        "</footer>\n"
    )


# ─── section partials ─────────────────────────────────────────────────────

def render_repo_meter(product: dict) -> str:
    """The empty meter element; /repo-meter/meter.js fills it in the browser
    from data/repo-activity.json. Rendered for every product with a repo, so
    no page can forget it."""
    if not product.get("repo"):
        return ""
    return (
        f'    <div class="repo-meter" data-repo="{e(product["repo"])}" '
        f'aria-label="Commit activity for {e(product.get("title", product["id"]))}"></div>\n'
    )


STORE_ICON = (
    '<svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
    '<path d="M3 3h8.5v8.5H3zM12.5 3H21v8.5h-8.5zM3 12.5h8.5V21H3zM12.5 12.5H21V21h-8.5z"/></svg>'
)


def render_get_strip(g: dict) -> str:
    """The get-it strip under the hero: a label, then the ways to get the
    app. A link with `store: true` wears the Microsoft Store mark."""
    links = []
    for link in g["links"]:
        cls = "btn primary" if link.get("primary") else "btn"
        icon = STORE_ICON if link.get("store") else ""
        links.append(f'      <a class="{cls}" href="{e(link["href"])}">{icon}{e(link["label"])}</a>\n')
    return (
        '\n    <div class="get-strip" id="get-it">\n'
        f'      <span class="gs-key">{e(g["label"])}</span>\n'
        '      <span class="spacer"></span>\n'
        + "".join(links)
        + "    </div>\n"
    )


def render_hero(product: dict, s: dict) -> str:
    accent = f" <em>{e(s['titleAccent'])}</em>" if s.get("titleAccent") else ""
    cls = "hero hero-center" if s.get("align") == "center" else "hero"
    out = [f'  <section class="{cls}">\n']
    if s.get("eyebrow"):
        out.append(f'    <p class="eyebrow">{e(s["eyebrow"])}</p>\n')
    out.append(f"    <h1>{e(s['title'])}{accent}</h1>\n")
    out.append(f'    <p class="dek">{s["dek"]}</p>\n')
    if s.get("fine"):
        out.append(f'    <p class="fine">{s["fine"]}</p>\n')
    if s.get("strip"):
        cells = "".join(
            "      <div>\n"
            f'        <span class="k">{e(c["key"])}</span>\n'
            f'        <span class="v">{e(c["value"])}</span>\n'
            "      </div>\n"
            for c in s["strip"]
        )
        out.append(f'\n    <div class="strip">\n{cells}    </div>\n')
    if s.get("get"):
        out.append(render_get_strip(s["get"]))
    out.append(render_repo_meter(product))
    out.append("  </section>\n")
    return "".join(out)


def block_lead(b: dict, product: dict) -> str:
    return "".join(f'    <p class="lead">{p}</p>\n' for p in b["paragraphs"])


def block_cards(b: dict, product: dict) -> str:
    cards = "".join(
        '      <div class="card">\n'
        + (f'        <span class="tag">{e(c["tag"])}</span>\n' if c.get("tag") else "")
        + f"        <h3>{e(c['title'])}</h3>\n"
        f"        <p>{c['body']}</p>\n"
        "      </div>\n"
        for c in b["items"]
    )
    return f'    <div class="cards">\n{cards}    </div>\n'


def block_callout(b: dict, product: dict) -> str:
    label = f'      <span class="k">{e(b["label"])}</span>\n' if b.get("label") else ""
    return (
        '    <div class="callout">\n'
        f"{label}"
        f"      <p>{b['text']}</p>\n"
        "    </div>\n"
    )


def block_stats(b: dict, product: dict) -> str:
    items = "".join(
        f'      <div class="stat"><div class="n">{e(s["value"])}</div>'
        f'<div class="l">{e(s["label"])}</div></div>\n'
        for s in b["items"]
    )
    return f'    <div class="stats">\n{items}    </div>\n'


def block_shots(b: dict, product: dict) -> str:
    """The screenshot strip, from the product's own `screenshots` list: the
    one the admin uploader writes (assets/screenshots/<product-id>/,
    `<epoch-ms>-<slug>.png`). No shots, no strip: this returns "" and the
    section around it drops whole, so a page never ships an empty frame or a
    placeholder. The first shot runs full width.

    Alt text and caption per shot: the screenshot entry's own `alt` /
    `caption` win; otherwise `captions[i]` / `alts[i]` from this block, in
    shot order, so the copy for a planned shot can be written before the
    capture exists and the upload is the only edit left."""
    shots = [s for s in (product.get("screenshots") or []) if s.get("path")]
    if not shots:
        return ""
    captions = b.get("captions") or []
    alts = b.get("alts") or []
    figures = []
    for i, shot in enumerate(shots):
        caption = shot.get("caption") or (captions[i] if i < len(captions) else "")
        alt = shot.get("alt") or (alts[i] if i < len(alts) else
                                  f"{product.get('title', product['id'])} screenshot {i + 1}")
        size = ""
        if shot.get("width") and shot.get("height"):
            size = f' width="{int(shot["width"])}" height="{int(shot["height"])}"'
        cap = f'\n        <figcaption class="shot-cap">{caption}</figcaption>' if caption else ""
        lead = " lead" if i == 0 else ""
        src = "/" + shot["path"].lstrip("/")
        figures.append(
            f'      <figure class="shot{lead}">\n'
            f'        <div class="shot-frame"><img src="{e(src)}" alt="{e(alt)}"{size} loading="lazy" /></div>'
            f"{cap}\n"
            "      </figure>\n"
        )
    return f'    <div class="shots">\n{"".join(figures)}    </div>\n'


_STORE_ID_RE = re.compile(r"/detail/([A-Za-z0-9]{12})")


def block_reach_map(b: dict, product: dict) -> str:
    """The per-country Store reach map. /assets/reach-map.js fills it from
    data/store-analytics.json and keeps it hidden until the geography pull
    has data. The Store id comes from the product's storeUrl unless the
    block names one; the data file keys ids in upper case."""
    app = b.get("app")
    if not app:
        m = _STORE_ID_RE.search(product.get("storeUrl") or "")
        if not m:
            raise ValueError(f"{product['id']}: reachMap needs an app id or a Store storeUrl")
        app = m.group(1)
    label = b.get("label") or product.get("title", product["id"])
    return f'    <div class="reach-map" data-app="{e(app.upper())}" data-label="{e(label)}"></div>\n'


def _trust_row(r: dict) -> str:
    body = r["body"]
    if r.get("codes"):
        items = "".join(
            f'            <li><code>{e(c["code"])}</code> <span>{e(c["desc"])}</span></li>\n'
            for c in r["codes"]
        )
        note = f'          <p class="scopes-note">{r["codesNote"]}</p>\n' if r.get("codesNote") else ""
        body = (
            f"\n          {body}\n"
            f'          <ul class="scopes">\n{items}          </ul>\n{note}        '
        )
    return (
        '      <div class="trust-row">\n'
        f'        <span class="k">{e(r["label"])}</span>\n'
        f'        <div class="d">{body}</div>\n'
        "      </div>\n"
    )


def block_trust(b: dict, product: dict) -> str:
    rows = "\n".join(_trust_row(r) for r in b["rows"])
    return f'    <div class="trust">\n\n{rows}\n    </div>\n'


def block_status(b: dict, product: dict) -> str:
    paras = "".join(f"      <p>{p}</p>\n" for p in b["paragraphs"])
    gates = ""
    if b.get("gates"):
        items = "".join(f"        <li>{e(g)}</li>\n" for g in b["gates"])
        gates = f'      <ul class="gates">\n{items}      </ul>\n'
    return f'    <div class="status-panel">\n{paras}{gates}    </div>\n'


def block_contact(b: dict, product: dict) -> str:
    items = []
    for c in b["items"]:
        rel = ' rel="noopener"' if c.get("external") else ""
        items.append(
            "      <div>\n"
            f'        <span class="k">{e(c["label"])}</span>\n'
            f'        <a href="{e(c["href"])}"{rel}>{e(c["text"])}</a>\n'
            "      </div>\n"
        )
    return f'    <div class="contact">\n{"".join(items)}    </div>\n'


def block_widget(b: dict, product: dict) -> str:
    """The game's mount point. Its stylesheet, script and init are emitted
    once at the end of the page by widget_tail(), from the entry's fields."""
    for k in ("script", "stylesheet", "initFn"):
        if not product.get(k):
            raise ValueError(f"{product.get('id')}: a widget block needs the entry's {k!r}")
    width = f' style="max-width:{int(b["maxWidth"])}px"' if b.get("maxWidth") else ""
    return (
        '    <div class="widget-stage">\n'
        f'      <div id="{e(product["id"])}" class="play-widget"{width}></div>\n'
        "    </div>\n"
    )


def widget_tail(product: dict, spec: dict) -> str:
    """The game's stylesheet, script and init, when the page mounts one."""
    blocks = [b for s in spec.get("sections", []) for b in s.get("blocks", []) if b.get("type") == "widget"]
    if not blocks:
        return ""
    init_fn = product["initFn"]
    if not re.fullmatch(r"[A-Za-z_$][\w$]*(\.[A-Za-z_$][\w$]*)*", init_fn):
        raise ValueError(f"{product.get('id')}: initFn {init_fn!r} is not a dotted name")
    config = {**(product.get("config") or {}), **(blocks[0].get("config") or {})}
    args = json.dumps(config, ensure_ascii=False).replace("</", "<\\/")
    mount = json.dumps(product["id"])
    return (
        "<!-- the game (served from the repo root by GitHub Pages) -->\n"
        f'<link rel="stylesheet" href="{e(product["stylesheet"])}" />\n'
        f'<script src="{e(product["script"])}" defer></script>\n'
        "<script>\n"
        '  window.addEventListener("DOMContentLoaded", function () {\n'
        f"    if (window.{init_fn.split('.')[0]}) {{\n"
        f"      {init_fn}(Object.assign({{ container: document.getElementById({mount}) }}, {args}));\n"
        "    }\n"
        "  });\n"
        "</script>\n"
    )


BLOCKS = {
    "widget": block_widget,
    "lead": block_lead,
    "cards": block_cards,
    "callout": block_callout,
    "trust": block_trust,
    "status": block_status,
    "contact": block_contact,
    "stats": block_stats,
    "shots": block_shots,
    "reachMap": block_reach_map,
}


def render_section(product: dict, s: dict) -> str:
    """`<section>` + heading + its blocks. A block that renders to nothing
    (a screenshot strip with no shots yet) is dropped, and a section whose
    every block is empty is dropped whole, heading and all, so a page never
    ships an empty strip or a placeholder."""
    rendered = []
    for b in s.get("blocks", []):
        fn = BLOCKS.get(b.get("type"))
        if fn is None:
            raise ValueError(f"{product['id']}: unknown block type {b.get('type')!r}")
        html = fn(b, product)
        if html:
            rendered.append(html)
    if not rendered:
        return ""
    sid = f' id="{e(s["id"])}"' if s.get("id") else ""
    # A section with no heading (a game's stage, right under its hero)
    # renders its blocks alone, with no empty heading row.
    if not s.get("heading"):
        return f"  <section{sid}>\n" + "\n".join(rendered) + "  </section>\n"
    head = []
    if s.get("eyebrow"):
        head.append(f'      <p class="eyebrow">{e(s["eyebrow"])}</p>\n')
    head.append(f"      <h2>{e(s['heading'])}</h2>\n")
    return (
        f"  <section{sid}>\n"
        '    <div class="section-hd">\n'
        + "".join(head)
        + "    </div>\n\n"
        + "\n".join(rendered)
        + "  </section>\n"
    )


SECTIONS = {
    "hero": render_hero,
    "section": render_section,
}


def render_page(product: dict, slug: str, source: str = "products") -> str:
    spec = product["pageSpec"]
    rel = output_rel(product)
    parts = []
    for s in spec["sections"]:
        fn = SECTIONS.get(s.get("type"))
        if fn is None:
            raise ValueError(f"{product['id']}: unknown section type {s.get('type')!r}")
        html = fn(product, s)
        if html:
            parts.append(html)
    tail_scripts = widget_tail(product, spec)
    if _uses(spec, "reachMap"):
        tail_scripts += '<script src="/assets/reach-map.js" defer></script>\n'
    return (
        render_head(product, spec, rel, slug, source)
        + "<body>\n\n"
        + render_nav(spec)
        + '\n<main class="wrap">\n\n'
        + "\n".join(parts)
        + "\n</main>\n\n"
        + render_footer(spec)
        + "\n"
        + tail_scripts
        + GOATCOUNTER
        + "\n</body>\n</html>\n"
    )


def build(slug: str | None = None, root: Path = ROOT) -> dict[str, str]:
    """{repo-relative path: html} for every generated page, dressed in
    `slug` (default: the active theme)."""
    if slug is None:
        slug = theme_registry.active_slug(theme_registry.load(root))
    content = load_content(root)
    outputs: dict[str, str] = {}
    for source, product in _page_sources(content):
        html = render_page(product, slug, source)
        # Aliases share the page, canonical included, so search engines fold
        # them into productPage.
        for rel in [output_rel(product), *alias_rels(product)]:
            if rel in outputs:
                raise ValueError(f"two pages render to {rel}")
            outputs[rel] = html
    return dict(sorted(outputs.items()))


def main(argv: list[str]) -> int:
    if "--list-outputs" in argv:
        # LF explicitly: a CRLF path reaches git as a different pathspec.
        sys.stdout.reconfigure(newline="\n")
        sys.stdout.write("".join(f"{rel}\n" for rel in generated_pages()))
        return 0

    theme = argv[argv.index("--theme") + 1] if "--theme" in argv else None
    out_dir = Path(argv[argv.index("--out") + 1]) if "--out" in argv else None
    if theme and not out_dir:
        print("error: --theme requires --out; a bare --theme would render that "
              "theme over the live pages.", file=sys.stderr)
        return 2

    outputs = build(theme)
    if out_dir is not None:
        for rel, html in outputs.items():
            dest = out_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(html, encoding="utf-8", newline="\n")
            print(f"preview written: {dest}")
        return 0

    drift = []
    for rel, html in outputs.items():
        path = ROOT / rel
        existing = path.read_text(encoding="utf-8") if path.exists() else None
        if existing != html:
            drift.append(rel)
            if "--check" not in argv:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(html, encoding="utf-8", newline="\n")
    if "--check" in argv:
        if drift:
            print("DRIFT: these product pages are stale, run render-product-pages.py:")
            for rel in drift:
                print(f"  {rel}")
            return 1
        print(f"{len(outputs)} product page(s) up to date.")
        return 0
    for rel in drift:
        print(f"  wrote {rel}")
    print(f"{len(outputs)} product page(s) rendered, {len(drift)} changed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
