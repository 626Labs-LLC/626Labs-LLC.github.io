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


def _pages(content: dict) -> list[dict]:
    return [p for p in content.get("pages") or [] if isinstance(p, dict)]


def _page_sources(content: dict) -> list[tuple[str, dict]]:
    """(source label, entry) for every entry that renders a page: products
    first, then games, then standalone `pages` (a product's second page, such
    as its trailer or plugin marketplace, which the home row never reads).
    The label names where the copy lives, for the generated-file banner."""
    return ([("products", p) for p in _products(content) if p.get("pageSpec")]
            + [("play.widgets", w) for w in _games(content) if w.get("pageSpec")]
            + [("pages", p) for p in _pages(content) if p.get("pageSpec")])


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
    video = ""
    if meta.get("video"):
        # A watch page: og:video lets a shared link play inline.
        v = meta["video"]
        src = v["url"] if "://" in v["url"] else SITE_ORIGIN + "/" + v["url"].lstrip("/")
        video = (
            f'<meta property="og:video" content="{e(src)}" />\n'
            f'<meta property="og:video:type" content="{e(v.get("type", "video/mp4"))}" />\n'
            f'<meta property="og:video:width" content="{int(v["width"])}" />\n'
            f'<meta property="og:video:height" content="{int(v["height"])}" />\n'
        )
    ld = ""
    if spec.get("jsonLd"):
        # Structured data as written in the spec (a watch page's VideoObject).
        body = json.dumps(spec["jsonLd"], ensure_ascii=False, indent=1).replace("</", "<\\/")
        ld = f'<script type="application/ld+json">\n{body}\n</script>\n'
    meter = ""
    if product.get("repo") or _uses(spec, "meter"):
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
        f'<meta property="og:type" content="{e(meta.get("ogType", "website"))}" />\n'
        f'<meta property="og:url" content="{e(url)}" />\n'
        f'<meta property="og:image" content="{e(og_image)}" />\n'
        f"{video}"
        '<meta name="twitter:card" content="summary_large_image" />\n'
        '<link rel="icon" type="image/png" href="/favicon-626.png" />\n'
        f"{ld}"
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


def resolve(product: dict, value):
    """`"@a.b"` reads site.json's a.b (the content the page was built from),
    so a fact like the Etsy shop URL lives in one place; anything else is
    returned as written. A reference that leads nowhere resolves to ""."""
    if not (isinstance(value, str) and value.startswith("@")):
        return value
    node = product.get("_content") or {}
    for key in value[1:].split("."):
        node = node.get(key) if isinstance(node, dict) else None
    return node if node is not None else ""


def link_attrs(product: dict, link: dict) -> str:
    """href (resolved), and for an outbound link `target`/`rel`; `track`
    becomes data-track, which the page's clickTrack script counts."""
    href = resolve(product, link["href"])
    if not href:
        # A nav or get-strip link that resolves to nothing would ship a blank
        # href silently (the Etsy shop link is the Conundrum page's whole
        # point). The cta block collapses instead and never gets here empty.
        raise ValueError(f"{product.get('id', '?')}: link {link.get('label')!r} has no href ({link['href']!r} is empty)")
    out = f' href="{e(href)}"'
    if link.get("id"):
        # A page script updates this link from live data (the Store link).
        out = f' id="{e(link["id"])}"' + out
    if link.get("external"):
        out += ' target="_blank" rel="noopener"'
    if link.get("track"):
        out += f' data-track="{e(link["track"])}"'
    return out


def render_nav(spec: dict, product: dict | None = None) -> str:
    links = []
    for link in spec.get("nav") or []:
        classes = []
        if link.get("cta"):
            classes.append("cta")
        if link.get("hideSm"):
            classes.append("hide-sm")
        cls = f' class="{" ".join(classes)}"' if classes else ""
        links.append(f'      <a{cls}{link_attrs(product or {}, link)}>{e(link["label"])}</a>')
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
    axiom = f'  <span class="axiom">{foot["axiom"]}</span>\n' if foot.get("axiom") else ""
    links = "".join(f' · <a href="{e(l["href"])}">{e(l["label"])}</a>' for l in foot.get("links") or [])
    return (
        "<footer>\n"
        f"  <span>{e(foot.get('label', '626 Labs'))}</span>\n"
        f"{axiom}"
        f"{disclaimer}"
        f'  <span><a href="index.html">626labs.dev</a> · Imagine Something Else.{links}</span>\n'
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


def render_get_strip(g: dict, product: dict | None = None) -> str:
    """The get-it strip under the hero: a label, then the ways to get the
    app. A link with `store: true` wears the Microsoft Store mark."""
    links = []
    for link in g["links"]:
        cls = "btn primary" if link.get("primary") else "btn"
        icon = STORE_ICON if link.get("store") else ""
        links.append(f'      <a class="{cls}"{link_attrs(product or {}, link)}>{icon}{e(link["label"])}</a>\n')
    # `versionId` leaves a slot a page script fills with the live version.
    ver = f'      <span class="gs-ver" id="{e(g["versionId"])}"></span>\n' if g.get("versionId") else ""
    return (
        f'\n    <div class="get-strip" id="{e(g.get("id", "get-it"))}">\n'
        f'      <span class="gs-key">{e(g["label"])}</span>\n'
        f"{ver}"
        '      <span class="spacer"></span>\n'
        + "".join(links)
        + "    </div>\n"
    )


def _id(d: dict, key: str = "id") -> str:
    """An element id a page script writes live data into."""
    return f' id="{e(d[key])}"' if d.get(key) else ""


def render_hero(product: dict, s: dict) -> str:
    # `accentJoin: ""` sets the accent flush against the title (SnapSnip).
    accent = f"{s.get('accentJoin', ' ')}<em>{e(s['titleAccent'])}</em>" if s.get("titleAccent") else ""
    cls = {"center": "hero hero-center", "side": "hero hero-side"}.get(s.get("align"), "hero")
    out = [f'  <section class="{cls}">\n']
    if s.get("logo"):
        out.append(f'    <img class="logo" src="{e(s["logo"]["src"])}" alt="{e(s["logo"]["alt"])}" />\n')
    if s.get("align") == "side":
        out.append("    <div>\n")
    if s.get("icon"):
        out.append(f'    <img class="app-icon" src="{e(s["icon"]["src"])}" alt="{e(s["icon"]["alt"])}" />\n')
    if s.get("eyebrow"):
        out.append(f'    <p class="eyebrow">{e(s["eyebrow"])}</p>\n')
    out.append(f"    <h1>{e(s['title'])}{accent}</h1>\n")
    if s.get("dek"):
        out.append(f'    <p class="dek">{s["dek"]}</p>\n')
    if s.get("sub"):
        out.append(f'    <p class="sub">{s["sub"]}</p>\n')
    if s.get("fine"):
        out.append(f'    <p class="fine"{_id(s, "fineId")}>{s["fine"]}</p>\n')
    if s.get("strip"):
        cells = "".join(
            "      <div>\n"
            f'        <span class="k">{e(c["key"])}</span>\n'
            f'        <span class="v"{_id(c)}>{e(c["value"])}</span>\n'
            "      </div>\n"
            for c in s["strip"]
        )
        out.append(f'\n    <div class="strip">\n{cells}    </div>\n')
    if s.get("get"):
        out.append(render_get_strip(s["get"], product))
    out.append(render_repo_meter(product))
    if s.get("align") == "side":
        out.append("    </div>\n")
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
    title = f'<span class="t">{e(r["title"])}</span>' if r.get("title") else ""
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
        f'        <div class="d">{title}{body}</div>\n'
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


GITHUB_ICON = (
    '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .297c-6.63 0-12 5.373-12 12 '
    '0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61'
    'C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 '
    '2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-'
    '.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-'
    '1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 '
    '5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 '
    '12.297c0-6.627-5.373-12-12-12"/></svg>'
)
BADGE_ICONS = {
    "github": GITHUB_ICON,
    "store": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M3 3h8.5v8.5H3zm9.5 0H21v8.5h-8.5zM3 12.5h8.5V21H3zm9.5 0H21V21h-8.5z"/></svg>',
}


def block_showcase(b: dict, product: dict) -> str:
    """One framed hero image, centered. `wide` runs it the full column (an
    app's main window), not a phone-sized frame."""
    wide = " wide" if b.get("wide") else ""
    return (
        f'    <div class="showcase{wide}"><div class="showcase-frame">\n'
        f'      <img src="{e(b["src"])}" alt="{e(b["alt"])}" />\n'
        "    </div></div>\n"
    )


def _badge(bd: dict) -> str:
    icon = BADGE_ICONS.get(bd.get("kind", ""))
    if icon is None:
        raise ValueError(f"badge kind {bd.get('kind')!r} is not one of {sorted(BADGE_ICONS)}")
    return (
        f'          <a class="store-badge" href="{e(bd["href"])}" rel="noopener">\n'
        f"            {icon}\n"
        '            <div class="store-badge-text">\n'
        f'              <span class="store-badge-top">{e(bd["top"])}</span>\n'
        f'              <span class="store-badge-bottom">{e(bd["bottom"])}</span>\n'
        "            </div>\n"
        "          </a>\n"
    )


def block_platforms(b: dict, product: dict) -> str:
    """A card per platform: title, body, bullets, download badges."""
    cards = []
    for c in b["items"]:
        bullets = "".join(f"          <li>{li}</li>\n" for li in c.get("bullets") or [])
        badges = "".join(_badge(bd) for bd in c.get("badges") or [])
        # `tone: alt` is the second platform in the magenta accent; `key`
        # and `stack` are the mono lines above and under the title.
        tone = " alt" if c.get("tone") == "alt" else ""
        cards.append(
            f'      <article class="platform-card{tone}">\n'
            + (f'        <span class="key">{e(c["key"])}</span>\n' if c.get("key") else "")
            + f"        <h3>{e(c['title'])}</h3>\n"
            + (f'        <span class="stack">{e(c["stack"])}</span>\n' if c.get("stack") else "")
            + (f"        <p>{c['body']}</p>\n" if c.get("body") else "")
            + (f"        <ul>\n{bullets}        </ul>\n" if bullets else "")
            + (f'        <div class="badge-row">\n{badges}        </div>\n' if badges else "")
            + "      </article>\n"
        )
    return f'    <div class="platform-grid">\n{"".join(cards)}    </div>\n'


def _shot(s: dict, extra: str = "") -> str:
    return (
        f'      <div class="gallery-shot{extra}">\n'
        f'        <img src="{e(s["src"])}" alt="{e(s["alt"])}" loading="lazy" />\n'
        f'        <div class="caption">{s["caption"]}</div>\n'
        "      </div>\n"
    )


def block_gallery(b: dict, product: dict) -> str:
    """Captioned images from fixed paths (a product's own page assets, not the
    uploader's screenshots list: that is `shots`). `wide` adds one full-width
    image under the strip; `align: start` top-aligns shots of mixed heights."""
    cls = "gallery-strip align-start" if b.get("align") == "start" else "gallery-strip"
    out = f'    <div class="{cls}">\n' + "".join(_shot(s) for s in b["items"]) + "    </div>\n"
    if b.get("wide"):
        out += _shot(b["wide"], " wide")
    return out


def block_panel(b: dict, product: dict) -> str:
    """A bordered card with a heading and paragraphs. `tone: ok` is the green
    reassurance card (privacy); the default takes the page's panel fill."""
    tone = " ok" if b.get("tone") == "ok" else ""
    paras = "".join(f"      <p>{p}</p>\n" for p in b["paragraphs"])
    return (
        f'    <div class="panel{tone}">\n'
        + (f"      <h3>{e(b['title'])}</h3>\n" if b.get("title") else "")
        + f"{paras}"
        "    </div>\n"
    )


ARROW_ICON = '<svg class="ic arrow" viewBox="0 0 24 24"><path d="M5 12h14M13 5l7 7-7 7"/></svg>'


def block_cta(b: dict, product: dict) -> str:
    """A line and one button. The href may be a content reference; one that
    resolves empty drops the block (no placeholder link ships). `style:
    arrow` is the left-aligned outlined link with an arrow."""
    href = resolve(product, b["href"])
    if not href:
        return ""
    link = {**b, "href": href}
    if b.get("style") == "arrow":
        text = f"      <p>{b['text']}</p>\n" if b.get("text") else ""
        return (
            '    <div class="cta-arrow">\n'
            f"{text}"
            f'      <a class="arrow-link"{link_attrs(product, link)}>{e(b["label"])} {ARROW_ICON}</a>\n'
            "    </div>\n"
        )
    return (
        '    <div class="cta-row">\n'
        f"      <p>{b['text']}</p>\n"
        f'      <a class="btn"{link_attrs(product, link)}>{e(b["label"])}</a>\n'
        "    </div>\n"
    )


def _track_slug(title: str) -> str:
    """Stable slug for click-event paths (etsy-click/<slug> since July)."""
    return re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")


def block_merch(b: dict, product: dict) -> str:
    """Shop cards from a content list (`source`, e.g. "@conundrum.products").
    Array order IS display order (ranked upstream); a chip is an optional
    label, never a number. Each card links out and is click-tracked by its
    title's slug. No items, no grid."""
    items = resolve(product, b["source"]) or []
    if not items:
        return ""
    cards = []
    for it in items:
        chip = f'\n          <span class="merch-chip">{e(it["chip"])}</span>' if it.get("chip") else ""
        cards.append(
            f'      <a class="merch-card" href="{e(it["etsyListing"])}" target="_blank" rel="noopener" '
            f'data-track="{e(_track_slug(it.get("title")))}">\n'
            f'          <img class="merch-img" src="{e(it["image"])}" alt="" loading="lazy" />{chip}\n'
            '          <div class="merch-meta">\n'
            f'            <div class="merch-title">{e(it["title"])}</div>\n'
            f'            <div class="merch-price">{e(it["price"])}</div>\n'
            "          </div>\n"
            "      </a>\n"
        )
    return f'    <div class="merch-grid">\n{"".join(cards)}    </div>\n'


def block_steps(b: dict, product: dict) -> str:
    """A numbered row of stage pills."""
    items = "".join(f'      <li><b>{e(s["n"])}</b>{s["text"]}</li>\n' for s in b["items"])
    return f'    <ul class="stages">\n{items}    </ul>\n'


def block_pull(b: dict, product: dict) -> str:
    return f'    <p class="pull">{b["text"]}</p>\n'


def block_meter(b: dict, product: dict) -> str:
    """A repo meter for a repo the product entry doesn't carry (the home row
    reads `repo`, so setting it would change the home page)."""
    return render_repo_meter({"id": product["id"], "repo": b["repo"], "title": b.get("label") or product.get("title")})


def render_click_track(spec: dict) -> str:
    """Outbound clicks on [data-track] links as GoatCounter events, at
    <prefix><slug>. etsy-click/ is the path conundrum.html has always used,
    so the shop's click history continues."""
    ct = spec.get("clickTrack")
    if not ct:
        return ""
    prefix, title = json.dumps(ct["prefix"]), json.dumps(ct.get("titlePrefix", ""))
    return (
        "<script>\n"
        "(function () {\n"
        "  document.addEventListener('click', function (e) {\n"
        "    var a = e.target.closest ? e.target.closest('a[data-track]') : null;\n"
        "    if (!a || !window.goatcounter || !window.goatcounter.count) return;\n"
        "    var slug = a.getAttribute('data-track');\n"
        f"    window.goatcounter.count({{ path: {prefix} + slug, title: {title} + slug, event: true }});\n"
        "  });\n"
        "})();\n"
        "</script>\n"
    )


# ─── app-page blocks with live parts (RoRoRo, Mod Launcher, 2026-10-17) ───
#
# A block that needs a script names it in BLOCK_SCRIPTS; render_page emits
# each named script once, at the end of the page, the way reachMap always
# has. The scripts live in assets/ beside reach-map.js and read everything
# they need from the markup (data- attributes and ids), so the copy stays in
# site.json and one script serves every page that uses its block. Each one
# only ever upgrades the page: on a failed fetch the static content stands.

def block_features(b: dict, product: dict) -> str:
    """A grid of feature tiles: optional mono `key` ("01 · VAULT") or
    magenta `tag` ("New in 0.3"), a title, a body. `columns` is 2 or 3."""
    cols = f" cols-{int(b['columns'])}" if b.get("columns") else ""
    tiles = []
    for f in b["items"]:
        tiles.append(
            '      <div class="feature">\n'
            + (f'        <div class="key">{e(f["key"])}</div>\n' if f.get("key") else "")
            + (f'        <span class="tag">{e(f["tag"])}</span>\n' if f.get("tag") else "")
            + f"        <h3>{e(f['title'])}</h3>\n"
            f"        <p>{f['body']}</p>\n"
            "      </div>\n"
        )
    return f'    <div class="feature-grid{cols}">\n{"".join(tiles)}    </div>\n'


EXTERNAL_ARROW = (
    '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17L17 7M7 7h10v10"/></svg>'
)


def block_install(b: dict, product: dict) -> str:
    """Install paths, one card each: a platform line, a title, a body, an
    optional command block, and the link. `pill` marks the recommended one."""
    cards = []
    for c in b["items"]:
        rec = " recommended" if c.get("pill") else ""
        cards.append(
            f'      <div class="install-card{rec}">\n'
            + (f'        <span class="pill">{e(c["pill"])}</span>\n' if c.get("pill") else "")
            + f'        <span class="plat">{e(c["plat"])}</span>\n'
            f"        <h3>{e(c['title'])}</h3>\n"
            f"        <p>{c['body']}</p>\n"
            + (f"        <code>{e(c['code'])}</code>\n" if c.get("code") else "")
            + f'        <a class="go"{link_attrs(product, c)}>{e(c["label"])} {EXTERNAL_ARROW}</a>\n'
            "      </div>\n"
        )
    return f'    <div class="install-grid">\n{"".join(cards)}    </div>\n'


def block_video(b: dict, product: dict) -> str:
    """A player for `<base>-16x9.mp4` with `<base>-poster.jpg`. With `langs`,
    pills under it swap in `<base>-<code>-16x9.mp4` and its poster
    (assets/video-langs.js); the first pill is the default cut. The frame
    sits above the theme's CRT overlay, so the video stays clean."""
    base = b["base"]
    watch = (f'      <a class="video-cap" href="{e(b["watch"]["href"])}">{e(b["watch"]["label"])}</a>\n'
             if b.get("watch") else "")
    pills = ""
    attrs = ""
    if b.get("langs"):
        items = []
        for i, lang in enumerate(b["langs"]):
            active = " is-active" if i == 0 else ""
            secs = f' data-secs="{int(lang["secs"])}"' if lang.get("secs") else ""
            items.append(f'        <button type="button" class="lang-pill{active}" '
                         f'data-lang="{e(lang.get("code", ""))}"{secs}>{e(lang["label"])}</button>\n')
        pills = ('      <div class="video-langs" role="group" aria-label="Trailer language">\n'
                 + "".join(items) + "      </div>\n")
        attrs = f' data-base="{e(base)}" data-cut="{e(b["cut"])}"'
    return (
        f'    <div class="video-frame"{attrs}>\n'
        '      <video controls preload="metadata" playsinline\n'
        f'             poster="{e(base)}-poster.jpg">\n'
        f'        <source src="{e(base)}-16x9.mp4" type="video/mp4" />\n'
        "      </video>\n"
        '      <div class="video-foot">\n'
        f'      <p class="video-cap">{b["caption"]}</p>\n'
        f"{watch}{pills}"
        "      </div>\n"
        "    </div>\n"
    )


def block_nudge(b: dict, product: dict) -> str:
    """For a phone visitor on a desktop app's page: carry the page to the
    machine that can install it (assets/phone-nudge.js). Shown only on a
    touch screen under 720px; the link it copies is the canonical URL."""
    url = page_url(output_rel(product))
    return (
        f'    <div class="phone-nudge" data-url="{e(url)}" data-title="{e(b["title"])}" data-text="{e(b["shareText"])}">\n'
        f"      {b['text']}\n"
        '      <div class="acts">\n'
        '        <button type="button" class="nudge-copy">Copy link</button>\n'
        '        <button type="button" class="nudge-share">Share to myself</button>\n'
        '        <span class="done" aria-live="polite"></span>\n'
        "      </div>\n"
        "    </div>\n"
    )


def block_howto(b: dict, product: dict) -> str:
    """Side-by-side columns: numbered `steps`, `paragraphs`, and `links`
    with a note. `tone: alt` is the dashed magenta column."""
    cols = []
    for c in b["columns"]:
        tone = " alt" if c.get("tone") == "alt" else ""
        body = ""
        if c.get("steps"):
            body += '        <ol class="steps">\n' + "".join(f"          <li>{li}</li>\n" for li in c["steps"]) + "        </ol>\n"
        body += "".join(f"        <p>{p}</p>\n" for p in c.get("paragraphs") or [])
        if c.get("links"):
            body += ('        <div class="howto-links">\n'
                     + "".join(f'          <a href="{e(l["href"])}">{e(l["label"])} <span>{e(l["note"])}</span></a>\n'
                               for l in c["links"])
                     + "        </div>\n")
        cols.append(f'      <div class="howto-col{tone}">\n'
                    f'        <div class="howto-key">{e(c["key"])}</div>\n{body}      </div>\n')
    wide = " wide" if b.get("wide") else ""
    return f'    <div class="howto{wide}">\n{"".join(cols)}    </div>\n'


def _meter_template(meters: dict) -> str:
    """Repo meters for cards a script builds later, parked in a <template>
    so the data-repo attributes are in the page itself: the daily
    repo-activity bot finds the repos it tracks by scanning the root HTML."""
    if not meters:
        return ""
    items = "".join(
        f'      <div class="repo-meter" data-plugin="{e(pid)}" data-repo="{e(m["repo"])}" '
        f'aria-label="Commit activity for {e(m["label"])}"></div>\n'
        for pid, m in meters.items()
    )
    return f'    <template class="plugin-meters">\n{items}    </template>\n'


def block_plugin_catalog(b: dict, product: dict) -> str:
    """The RoRoRo plugin marketplace: cards built from data/rororo-plugins.json
    (assets/rororo-plugins.js), each with copy-install-URL, zip and source.
    On a failed fetch the fallback shows instead."""
    return (
        f'    <div class="plugin-cards" data-icons="{e(json.dumps(b.get("icons") or {}))}"></div>\n'
        f'    <div class="plugin-fallback" hidden>\n      {b["fallback"]}\n    </div>\n'
        + _meter_template(b.get("meters") or {})
        + '    <div class="toast" role="status"></div>\n'
    )


def block_plugin_list(b: dict, product: dict) -> str:
    """The product page's plugin rows: the live ones from the marketplace data
    (assets/rororo-plugins.js, which needs JavaScript; the noscript row stands
    in), then the `bench` ones, written here."""
    fb = b["fallback"]
    bench = "".join(
        '      <div class="plugin">\n'
        '        <div class="pl-l">\n'
        f'          <div class="pl-name"><h4>{e(p["title"])}</h4><span class="status bench">{e(p["status"])}</span></div>\n'
        f"          <p>{p['body']}</p>\n"
        "        </div>\n"
        f'        <span class="pl-link muted">{e(p["link"])}</span>\n'
        "      </div>\n"
        for p in b.get("bench") or []
    )
    return (
        '    <div class="plugin-list">\n'
        f'      <div class="live-plugins" data-href="{e(b["href"])}" data-icons="{e(json.dumps(b.get("icons") or {}))}" '
        f'data-label="{e(b["linkLabel"])}" style="display:contents">\n'
        "        <noscript>\n"
        '          <div class="plugin live">\n'
        '            <div class="pl-l">\n'
        f'              <div class="pl-name"><h4>{e(fb["title"])}</h4><span class="status live">{e(fb["status"])}</span></div>\n'
        f"              <p>{fb['body']}</p>\n"
        "            </div>\n"
        f'            <a class="pl-link" href="{e(b["href"])}">{e(fb["label"])}</a>\n'
        "          </div>\n"
        "        </noscript>\n"
        "      </div>\n"
        f"{bench}"
        "    </div>\n"
    )


def block_game_feed(b: dict, product: dict) -> str:
    """Every game the launcher knows, read live from the signed game feed
    (assets/game-feed.js): featured covers, then the engine-curated and
    Nexus-identified rows. Loading line first; the fallback on a failed
    fetch; the lists stay hidden until the feed parses."""
    def head(sec: dict, list_id: str) -> str:
        return section_head({**sec, "aside": sec.get("aside", ""), "asideId": f"{list_id}-count" if list_id != "featured" else None})
    sections = []
    for key, cls in (("featured", "covers"), ("curated", "rows"), ("nexus", "rows")):
        sec = b[key]
        dek = f'    <p class="section-dek">{sec["dek"]}</p>\n' if sec.get("dek") else ""
        sections.append(head(sec, key) + dek + f'    <div class="{cls}" data-list="{key}"></div>\n')
    req = b["request"]
    links = "".join(f'      <a class="btn{" primary" if l.get("primary") else ""}" href="{e(l["href"])}">{e(l["label"])}</a>\n'
                    for l in req["links"])
    meter = render_repo_meter({"id": product["id"], "repo": b["repo"], "title": b["meterLabel"]}) if b.get("repo") else ""
    return (
        f'    <div class="game-feed" data-feed="{e(b["feed"])}">\n'
        f'    <div class="loading">{e(b["loading"])}</div>\n'
        f'    <div class="fallback" hidden>\n      {b["fallback"]}\n    </div>\n'
        '    <div class="feed-content" hidden>\n'
        + "\n".join(sections)
        + '\n    <div class="request-strip">\n'
        f'      <div>\n        <div class="q">{e(req["q"])}</div>\n        <div class="d">{req["d"]}</div>\n      </div>\n'
        '      <span class="spacer"></span>\n'
        f"{links}"
        "    </div>\n"
        f"{meter}"
        "    </div>\n"
        "    </div>\n"
    )


def block_watch(b: dict, product: dict) -> str:
    """A watch page's body under the player: what the video shows (prose and
    beats) beside the ways to get the app."""
    paras = "".join(f"        <p>{p}</p>\n" for p in b["paragraphs"])
    beats = "".join(f"          <li>{li}</li>\n" for li in b["beats"])
    links = "".join(
        f'          <a class="btn{" primary" if l.get("primary") else ""}"{link_attrs(product, l)}>'
        f'{STORE_ICON if l.get("store") else ""}{e(l["label"])}</a>\n'
        for l in b["links"]
    )
    return (
        '    <div class="watch-body">\n'
        "      <div>\n"
        f"        <h2>{e(b['heading'])}</h2>\n"
        f"{paras}"
        f'        <ul class="beats">\n{beats}        </ul>\n'
        "      </div>\n"
        '      <aside class="watch-side">\n'
        f'        <div class="watch-links">\n{links}        </div>\n'
        f'        <p class="note">{b["note"]}</p>\n'
        "      </aside>\n"
        "    </div>\n"
    )


def _video_has_langs(b: dict) -> bool:
    return bool(b.get("langs"))


# block type -> (script, predicate on the block); None predicate = always.
BLOCK_SCRIPTS = {
    "reachMap": ("/assets/reach-map.js", None),
    "video": ("/assets/video-langs.js", _video_has_langs),
    "nudge": ("/assets/phone-nudge.js", None),
    "pluginCatalog": ("/assets/rororo-plugins.js", None),
    "pluginList": ("/assets/rororo-plugins.js", None),
    "gameFeed": ("/assets/game-feed.js", None),
}


def page_scripts(spec: dict) -> str:
    """Each script the page's blocks need, once, in first-use order."""
    seen: list[str] = []
    for s in spec.get("sections", []):
        for b in s.get("blocks", []):
            entry = BLOCK_SCRIPTS.get(b.get("type"))
            if entry and (entry[1] is None or entry[1](b)) and entry[0] not in seen:
                seen.append(entry[0])
    return "".join(f'<script src="{src}" defer></script>\n' for src in seen)


BLOCKS = {
    "features": block_features,
    "install": block_install,
    "video": block_video,
    "nudge": block_nudge,
    "howto": block_howto,
    "pluginCatalog": block_plugin_catalog,
    "pluginList": block_plugin_list,
    "gameFeed": block_game_feed,
    "watch": block_watch,
    "widget": block_widget,
    "merch": block_merch,
    "steps": block_steps,
    "pull": block_pull,
    "meter": block_meter,
    "showcase": block_showcase,
    "platforms": block_platforms,
    "gallery": block_gallery,
    "panel": block_panel,
    "cta": block_cta,
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
    return f"  <section{sid}>\n" + section_head(s) + "\n" + "\n".join(rendered) + "  </section>\n"


def section_head(s: dict) -> str:
    """A section's heading row. `sub` is a line under the heading (raw HTML);
    `aside` a short mono label at the right, which a page script can fill
    when it carries an `asideId` (a live count). Either one makes the row a
    split row; a heading without them renders exactly as before."""
    head = []
    if s.get("eyebrow"):
        head.append(f'      <p class="eyebrow">{e(s["eyebrow"])}</p>\n')
    hand = ' class="hand"' if s.get("hand") else ""
    head.append(f"      <h2{hand}>{e(s['heading'])}</h2>\n")
    if not (s.get("sub") or "aside" in s):
        return '    <div class="section-hd">\n' + "".join(head) + "    </div>\n"
    if s.get("sub"):
        head.append(f'      <p class="sub">{s["sub"]}</p>\n')
    return (
        '    <div class="section-hd split">\n'
        "      <div>\n" + "".join("  " + h for h in head) + "      </div>\n"
        f'      <div class="r"{_id(s, "asideId")}>{e(s.get("aside", ""))}</div>\n'
        "    </div>\n"
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
    tail_scripts += page_scripts(spec)
    tail_scripts += render_click_track(spec)
    return (
        render_head(product, spec, rel, slug, source)
        + "<body>\n\n"
        + render_nav(spec, product)
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
        # The page can reference other content ("@conundrum.etsyUrl").
        html = render_page({**product, "_content": content}, slug, source)
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
