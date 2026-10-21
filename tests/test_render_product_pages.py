"""scripts/render-product-pages.py: product pages generated from site.json.

Issue #200. A product with a `pageSpec` block gets its page rendered at the
path its `productPage` URL names. These pin the contract the hand-authored
pages kept by hand: the theme link, analytics, the signature, the repo meter,
the release markers, and the rule that a page never ships an empty strip.
"""
import copy
import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location(
    "render_product_pages", ROOT / "scripts" / "render-product-pages.py"
)
rpp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rpp)

SITE = json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))


def _product(pid):
    return next(p for p in SITE["products"] if p["id"] == pid)


def _minimal(**over):
    p = {
        "id": "demo",
        "title": "Demo",
        "productPage": "demo.html",
        "repo": None,
        "pageSpec": {
            "meta": {"title": "Demo", "description": "d", "ogTitle": "Demo",
                     "ogDescription": "d", "ogImage": "/assets/brand/banner-1200x630.png"},
            "nav": [{"label": "Home", "href": "/"}],
            "sections": [{"type": "hero", "title": "Demo", "dek": "A demo."}],
            "footer": {"label": "626 Labs · Demo"},
        },
    }
    p.update(over)
    return p


def test_every_generated_page_is_up_to_date():
    for rel, html in rpp.build().items():
        on_disk = (ROOT / rel).read_text(encoding="utf-8")
        assert on_disk == html, f"{rel} is stale; run scripts/render-product-pages.py"


def test_etsy_mcp_is_generated():
    assert "etsy-mcp.html" in rpp.generated_pages()


def test_product_page_stays_a_url_string():
    # The home row and the page-pane mod read productPage as a URL. The page
    # lives in the sibling pageSpec block; productPage's type never changes.
    for p in SITE["products"]:
        if p.get("pageSpec"):
            assert isinstance(p["productPage"], str), p["id"]


@pytest.mark.parametrize("url,rel", [
    ("etsy-mcp.html", "etsy-mcp.html"),
    ("/rbx15.html", "rbx15.html"),
    ("/demo/", "demo/index.html"),
])
def test_output_rel(url, rel):
    assert rpp.output_rel({"id": "x", "productPage": url}) == rel


@pytest.mark.parametrize("url", [
    None, "", "https://example.com/x.html", "//x.html", "../x.html", "x.htm", "x.html#top",
])
def test_output_rel_refuses_what_cannot_be_served(url):
    with pytest.raises(ValueError):
        rpp.output_rel({"id": "x", "productPage": url})


@pytest.mark.parametrize("rel", rpp.generated_pages())
def test_generated_page_carries_the_site_wide_furniture(rel):
    html = (ROOT / rel).read_text(encoding="utf-8")
    active = json.loads((ROOT / "content" / "themes.json").read_text(encoding="utf-8"))["active"]
    assert f'href="/themes/{active}/{rpp.THEME_CSS_HREF}"' in html
    assert 'data-goatcounter="https://626labs.goatcounter.com/count"' in html
    footer = html[html.rindex("<footer"):html.rindex("</footer>")]
    assert 'class="site-signature"' in footer
    assert "/assets/logos/signature.css" in html
    # An alias (pageSpec.aliases) canonicalizes to its entry's productPage,
    # so search engines fold the duplicate URL into the real one.
    canonical = {}
    for _, entry in rpp._page_sources(rpp.load_content()):
        primary = rpp.output_rel(entry)
        canonical[primary] = primary
        canonical.update({a: primary for a in rpp.alias_rels(entry)})
    assert f'<link rel="canonical" href="{rpp.page_url(canonical[rel])}" />' in html


def test_style_keeps_the_font_import_first():
    # @import after any rule is dropped silently, and the whole brand type
    # stack goes with it (render-plugin-pages.py measured that the hard way).
    css = rpp.STYLE_PATH.read_text(encoding="utf-8")
    first = re.sub(r"/\*.*?\*/", "", css, flags=re.S).strip().splitlines()[0]
    assert first == "@import url('/fonts/fonts.css');"


def test_repo_meter_and_release_markers_follow_the_data():
    p = _minimal(repo="owner/demo")
    p["pageSpec"]["releaseReviewed"] = ["owner/demo@v1.2.3"]
    html = rpp.render_page(p, "slate-broadsheet")
    assert '<meta name="release-reviewed" content="owner/demo@v1.2.3" />' in html
    assert 'class="repo-meter" data-repo="owner/demo"' in html
    assert "/repo-meter/meter.js" in html

    bare = rpp.render_page(_minimal(), "slate-broadsheet")
    assert "repo-meter" not in bare
    assert "release-reviewed" not in bare


def test_a_section_with_nothing_to_show_is_dropped_whole():
    p = _minimal()
    p["pageSpec"]["sections"].append(
        {"type": "section", "heading": "Zz empty section", "blocks": []}
    )
    html = rpp.render_page(p, "slate-broadsheet")
    assert "Zz empty section" not in html


def test_unknown_types_fail_loudly():
    p = _minimal()
    p["pageSpec"]["sections"].append({"type": "carousel"})
    with pytest.raises(ValueError, match="carousel"):
        rpp.render_page(p, "slate-broadsheet")
    p = _minimal()
    p["pageSpec"]["sections"].append(
        {"type": "section", "heading": "x", "blocks": [{"type": "marquee"}]})
    with pytest.raises(ValueError, match="marquee"):
        rpp.render_page(p, "slate-broadsheet")


def test_labels_are_escaped_and_body_copy_is_not():
    p = _minimal()
    p["pageSpec"]["sections"].append({
        "type": "section", "heading": "<script>",
        "blocks": [{"type": "lead", "paragraphs": ["<b>bold</b>"]}],
    })
    html = rpp.render_page(p, "slate-broadsheet")
    assert "<h2>&lt;script&gt;</h2>" in html
    assert '<p class="lead"><b>bold</b></p>' in html


def test_preview_renders_the_theme_it_is_asked_for():
    out = rpp.build("cyan-fade")
    for html in out.values():
        assert "/themes/cyan-fade/archetypes/product-tokens.css" in html


def test_the_workflows_render_and_commit_the_generated_pages():
    for wf in ("rotate-theme.yml", "rebuild-hub.yml"):
        yml = (ROOT / ".github" / "workflows" / wf).read_text(encoding="utf-8")
        assert "python scripts/render-product-pages.py" in yml or \
            "python3 scripts/render-product-pages.py" in yml, wf
        assert "render-product-pages.py --list-outputs" in yml, wf
        # Before render-hub: the sitemap is drawn from the page tree.
        run_product = re.search(r"(?m)python3? scripts/render-product-pages\.py\s*$", yml)
        run_hub = re.search(r"(?m)python3? scripts/render-hub\.py\s*$", yml)
        assert run_product and run_hub and run_product.start() < run_hub.start(), wf
    rotate = (ROOT / ".github" / "workflows" / "rotate-theme.yml").read_text(encoding="utf-8")
    assert "render-product-pages.py --check" in rotate


def test_site_doctor_runs_the_drift_check():
    doctor = (ROOT / "scripts" / "site-doctor.py").read_text(encoding="utf-8")
    assert '"render-product-pages.py"' in doctor


def _with_shots_section(shots):
    p = _minimal(screenshots=shots)
    p["pageSpec"]["sections"].append({
        "type": "section", "eyebrow": "See it work", "heading": "Zz shots heading",
        "blocks": [{"type": "shots", "captions": ["<b>One.</b> planned", "two"],
                    "alts": ["planned alt one"]}],
    })
    return rpp.render_page(p, "slate-broadsheet")


def test_no_screenshots_means_no_strip_and_no_heading():
    # Este's captures arrive later. Until then the section is absent, not a
    # row of empty frames.
    html = _with_shots_section([])
    assert "Zz shots heading" not in html
    assert 'class="shots"' not in html


def test_screenshots_render_from_the_uploader_entries():
    html = _with_shots_section([
        {"id": "shot-1", "path": "assets/screenshots/demo/1791000000000-menu.png", "name": "menu.png"},
        {"id": "shot-2", "path": "assets/screenshots/demo/1791000000001-toast.png", "name": "toast.png",
         "caption": "own caption", "alt": "own alt"},
        {"id": "shot-3", "path": "assets/screenshots/demo/1791000000002-x.png", "name": "x.png"},
    ])
    assert "Zz shots heading" in html
    assert html.count('<figure class="shot') == 3
    assert '<figure class="shot lead">' in html
    assert 'src="/assets/screenshots/demo/1791000000000-menu.png" alt="planned alt one"' in html
    assert "<b>One.</b> planned" in html  # planned caption fills shot 1
    assert "own caption" in html and 'alt="own alt"' in html  # the entry wins
    assert "Demo screenshot 3" in html  # no planned alt: a generic one, never empty


@pytest.mark.parametrize("pid", ["rtclickpng", "rbx15-shirt-pants"])
def test_the_new_app_pages_hold_their_shots_section_until_shots_exist(pid):
    p = _product(pid)
    html = (ROOT / rpp.output_rel(p)).read_text(encoding="utf-8")
    if p.get("screenshots"):
        assert 'class="shots"' in html
    else:
        assert 'class="shots"' not in html and "See it work" not in html


def test_reach_map_takes_its_id_from_the_store_url_in_upper_case():
    html = rpp.render_page(_product("rbx15-shirt-pants"), "slate-broadsheet")
    assert 'data-app="9MV9G4XFJ8S0"' in html
    assert '<script src="/assets/reach-map.js" defer></script>' in html
    p = _minimal()
    p["pageSpec"]["sections"].append(
        {"type": "section", "heading": "x", "blocks": [{"type": "reachMap"}]})
    with pytest.raises(ValueError, match="storeUrl"):
        rpp.render_page(p, "slate-broadsheet")


@pytest.mark.parametrize("pid", ["rtclickpng", "rbx15-shirt-pants"])
def test_every_live_store_app_page_has_its_furniture(pid):
    p = _product(pid)
    html = (ROOT / rpp.output_rel(p)).read_text(encoding="utf-8")
    assert f'data-repo="{p["repo"]}"' in html
    assert 'class="reach-map"' in html
    assert '<meta name="release-reviewed"' in html
    assert 'id="get-it"' in html


def test_rbx15_is_never_called_native():
    # RBX15 is Electron. The page says "Windows desktop app".
    html = (ROOT / "rbx15.html").read_text(encoding="utf-8").lower()
    assert not re.search(r"\bnative\b", html)  # "nominatively" is fine
    assert "windows desktop app" in html


# ─── games: play.widgets entries with a pageSpec (2026-10-17) ─────────────

def _bacon():
    return next(w for w in rpp.load_content()["play"]["widgets"] if w["id"] == "bacon-widget")


def test_bacon_trail_and_its_legacy_alias_are_generated():
    pages = rpp.generated_pages()
    assert "bacon-trail/index.html" in pages and "play/bacon/index.html" in pages
    a = (ROOT / "bacon-trail/index.html").read_text(encoding="utf-8")
    b = (ROOT / "play/bacon/index.html").read_text(encoding="utf-8")
    assert a == b  # one page, two addresses; the canonical names the first
    assert '<link rel="canonical" href="https://626labs.dev/bacon-trail/" />' in a
    assert "(play.widgets[id=bacon-widget].pageSpec)" in a


def test_the_game_mounts_from_the_entrys_own_fields():
    w = _bacon()
    html = (ROOT / "bacon-trail/index.html").read_text(encoding="utf-8")
    assert f'<div id="{w["id"]}" class="play-widget" style="max-width:440px"></div>' in html
    assert f'<link rel="stylesheet" href="{w["stylesheet"]}" />' in html
    assert f'<script src="{w["script"]}" defer></script>' in html
    # The page's config overrides the home row's: on its own page the CTA
    # has to leave for /#work, not scroll to a #work that isn't there.
    assert '"ctaUrl": "/#work"' in html and '"ctaLabel": "See the full suite' in html
    assert f'{w["initFn"]}(Object.assign({{ container: document.getElementById("{w["id"]}") }}' in html


def test_a_widget_block_refuses_a_bad_entry():
    w = copy.deepcopy(_bacon())
    w["initFn"] = "alert(1);x"
    with pytest.raises(ValueError, match="dotted name"):
        rpp.render_page(w, "slate-broadsheet", "play.widgets")
    del w["script"]
    with pytest.raises(ValueError, match="script"):
        rpp.render_page(w, "slate-broadsheet", "play.widgets")


def test_an_alias_must_be_a_local_page_path():
    w = copy.deepcopy(_bacon())
    w["pageSpec"]["aliases"] = ["https://example.com/x/"]
    with pytest.raises(ValueError, match="aliases"):
        rpp.alias_rels(w)


# ─── app-page blocks: showcase, platforms, gallery, panel, cta (2026-10-17) ─

def _sanduhr():
    return next(p for p in rpp.load_content()["products"] if p["id"] == "sanduhr")


def _declared_shots(product):
    """Every image src the pageSpec's gallery and showcase blocks declare."""
    srcs = []
    for section in product["pageSpec"]["sections"]:
        for b in section.get("blocks", []):
            if b["type"] == "gallery":
                srcs += [s["src"] for s in b["items"]]
                if b.get("wide"):
                    srcs.append(b["wide"]["src"])
            elif b["type"] == "showcase":
                srcs.append(b["src"])
    return srcs


def _assert_shots_match(html, srcs):
    frames = (html.count('class="gallery-shot"') + html.count('class="gallery-shot wide"')
              + html.count('class="showcase-frame"'))
    assert frames == len(srcs), f"{frames} frames rendered, {len(srcs)} declared"
    for src in srcs:
        n = len(re.findall(r'<img src="' + re.escape(src) + '"', html))
        assert n == 1, f"{src} rendered {n} times"


def test_sanduhr_is_generated_with_its_furniture():
    assert "sanduhr/index.html" in rpp.generated_pages()
    html = (ROOT / "sanduhr/index.html").read_text(encoding="utf-8")
    assert '<img class="app-icon" src="icon.png"' in html
    # The Mac page since 2026-10-18: Desk first, the Claude config carry
    # second; the platform picker and the Store reach map moved to
    # /sanduhr/windows/. The hand sets Este's own words only; no heading here
    # is one.
    assert 'class="hand"' not in html
    assert 'class="platform-card"' not in html and 'data-app=' not in html
    assert 'src="screenshot-desk-full.jpg"' in html and 'src="screenshot-desk-under-files.jpg"' in html
    assert "screenshot-whats-new" not in html
    assert 'class="stages"' in html  # how a pack travels
    assert "brew install --cask estevanhernandez-stack-ed/tap/sanduhr" in html
    assert 'href="/sanduhr/windows/"' in html
    _assert_shots_match(html, _declared_shots(_sanduhr()))
    assert 'class="panel ok"' in html
    assert '<meta name="release-reviewed" content="estevanhernandez-stack-ed/Sanduhr_f-r_Claude@v2.31.0-mac"' in html


def test_sanduhr_windows_is_generated_beside_the_mac_page():
    # /sanduhr/ is the Mac build's page since 2026-10-18; Windows lives at
    # /sanduhr/windows/ (a `pages[]` entry) until it catches up.
    assert "sanduhr/windows/index.html" in rpp.generated_pages()
    html = (ROOT / "sanduhr/windows/index.html").read_text(encoding="utf-8")
    assert '<img class="app-icon" src="icon.png"' in html and (ROOT / "sanduhr/windows/icon.png").is_file()
    assert 'href="/sanduhr/"' in html  # the Mac page, root-relative
    assert 'data-app="9NH3NK2RGCF5"' in html  # the reach map moved here
    assert '<meta name="release-reviewed" content="estevanhernandez-stack-ed/Sanduhr_f-r_Claude@v3.4.3"' in html
    assert 'class="hand"' not in html


def test_sanduhr_directory_holds_only_what_its_pages_use():
    # The spec's rule for the capture set: the directory says what the page
    # uses. A capture nothing references is a leftover, not an asset.
    mac = (ROOT / "sanduhr/index.html").read_text(encoding="utf-8")
    win = (ROOT / "sanduhr/windows/index.html").read_text(encoding="utf-8")
    for f in sorted((ROOT / "sanduhr").glob("screenshot-*")):
        assert f.name in mac or f.name in win, f"{f.name} is referenced by no page"
    assert 'src="screenshot-settings-notch-pill.png"' in mac  # the Notch pane, in the Settings strip


def test_nested_generated_pages_link_home_at_the_root():
    # A relative href="index.html" on /sanduhr/windows/ is the page itself.
    for rel in ("sanduhr/index.html", "sanduhr/windows/index.html"):
        html = (ROOT / rel).read_text(encoding="utf-8")
        assert '<a class="brand" href="/">' in html, rel
        assert '<a href="/">626labs.dev</a>' in html, rel


def test_a_badge_kind_must_be_known():
    # The platforms block is live on the rororo page, so every render exercises
    # it; this direct call pins the badge-kind ValueError, which no page triggers.
    block = {"type": "platforms", "items": [{"title": "macOS", "badges": [
        {"href": "/x", "kind": "itch", "top": "Get it from", "bottom": "itch.io"}]}]}
    with pytest.raises(ValueError, match="badge kind"):
        rpp.block_platforms(block, {"id": "x", "title": "X"})


def test_a_section_without_a_heading_renders_its_blocks_alone():
    html = rpp.render_section({"id": "x"}, {"type": "section", "blocks": [
        {"type": "cta", "text": "More?", "href": "/x", "label": "Go"}]})
    assert 'class="section-hd"' not in html and '<a class="btn" href="/x">Go</a>' in html


# ─── shop pages: merch, references, click tracking (conundrum, 2026-10-17) ─

def _shop(**over):
    content = {"conundrum": {
        "etsyUrl": "https://www.etsy.com/shop/ConundrumByEste", "repoUrl": None,
        "products": [
            {"title": "Fire & Ice Spider Monster Joggers", "price": "$46.99",
             "image": "assets/screenshots/conundrum/fire-ice.jpg",
             "etsyListing": "https://www.etsy.com/listing/111", "chip": "recently sold"},
            {"title": "Watercolor x Neon Spider Monster Joggers", "price": "$49.99",
             "image": "assets/screenshots/conundrum/watercolor.jpg",
             "etsyListing": "https://www.etsy.com/listing/222"},
        ]}}
    content["conundrum"].update(over)
    return {"id": "conundrum", "title": "Conundrum", "_content": content}


def test_merch_renders_cards_in_array_order_with_tracked_slugs():
    html = rpp.block_merch({"source": "@conundrum.products"}, _shop())
    assert html.count('class="merch-card"') == 2
    assert html.index("Fire &amp; Ice") < html.index("Watercolor")
    assert 'href="https://www.etsy.com/listing/111"' in html and "$46.99" in html
    assert 'data-track="fire-ice-spider-monster-joggers"' in html
    assert html.count('class="merch-chip"') == 1 and "recently sold" in html
    assert rpp.block_merch({"source": "@conundrum.products"}, _shop(products=[])) == ""


def test_repo_cta_collapses_when_unset_and_renders_when_set():
    b = {"style": "arrow", "href": "@conundrum.repoUrl", "label": "Read the code", "external": True, "track": "repo"}
    assert rpp.block_cta(b, _shop()) == ""
    html = rpp.block_cta(b, _shop(repoUrl="https://github.com/626Labs-LLC/pod-pipeline"))
    assert 'href="https://github.com/626Labs-LLC/pod-pipeline"' in html and 'data-track="repo"' in html
    assert 'class="arrow-link"' in html and "Read the code" in html


def test_a_shop_link_without_its_url_fails_by_name():
    with pytest.raises(ValueError, match="etsyUrl"):
        rpp.link_attrs(_shop(etsyUrl=""), {"label": "Shop on Etsy", "href": "@conundrum.etsyUrl"})


def test_conundrum_page_takes_its_links_from_site_json():
    site = json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))
    html = (ROOT / "conundrum.html").read_text(encoding="utf-8")
    url = site["conundrum"]["etsyUrl"]
    assert html.count(f'href="{url}" target="_blank" rel="noopener" data-track="shop"') == 2  # nav + hero
    assert html.count('class="merch-card"') == len(site["conundrum"]["products"])
    # The click history continues: same event paths as the hand page.
    assert "path: \"etsy-click/\" + slug" in html
    assert 'data-repo="626Labs-LLC/626labs-pod-pipeline"' in html


# ─── the last six pages: live blocks, standalone pages, watch pages ──────
# (rororo, rororo-plugins, mod-launcher-games, the two trailers, snapsnip;
# 2026-10-17, which finished issue #200's list)

def _read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def test_the_last_six_pages_are_generated():
    pages = rpp.generated_pages()
    for rel in ("rororo.html", "rororo-plugins.html", "mod-launcher-games.html",
                "rororo-trailer.html", "mod-launcher-trailer.html", "snapsnip.html"):
        assert rel in pages, rel
        assert "Do not hand-edit" in _read(rel)
    # Standalone pages name their source as `pages`, not products.
    assert "(pages[id=rororo-trailer].pageSpec)" in _read("rororo-trailer.html")


def test_release_markers_carry_over():
    assert 'content="estevanhernandez-stack-ed/ROROROblox@' in _read("rororo.html")
    assert 'content="estevanhernandez-stack-ed/626-mod-launcher@' in _read("mod-launcher-games.html")


def test_watch_pages_keep_their_video_seo():
    for rel, dur in (("rororo-trailer.html", "PT63S"), ("mod-launcher-trailer.html", "PT53S")):
        html = _read(rel)
        assert '<meta property="og:type" content="video.other" />' in html
        assert '<meta property="og:video" content="https://626labs.dev/assets/video/' in html
        ld = json.loads(re.search(r'<script type="application/ld\+json">\n(.*?)\n</script>', html, re.S).group(1))
        assert ld["@type"] == "VideoObject" and ld["duration"] == dur
        # The video is the main content: it comes right after the h1.
        main = html[html.index("<main"):]
        assert main.index("<h1>") < main.index("<video") < main.index("<h2>")


def test_page_scripts_are_emitted_once_each_for_the_blocks_used():
    rororo = _read("rororo.html")
    assert rororo.count('src="/assets/rororo-plugins.js"') == 1
    assert rororo.count('src="/assets/video-langs.js"') == 1
    assert rororo.count('src="/assets/phone-nudge.js"') == 1
    # A video without language pills needs no script.
    assert "video-langs.js" not in _read("mod-launcher-trailer.html")
    assert 'src="/assets/game-feed.js"' in _read("mod-launcher-games.html")
    for script in ("video-langs.js", "phone-nudge.js", "rororo-plugins.js", "game-feed.js"):
        assert (ROOT / "assets" / script).exists()


def test_plugin_meters_stay_in_the_page_for_the_repo_activity_bot():
    # refresh-repo-activity.mjs finds the repos it tracks by scanning root
    # HTML for data-repo=, so the meters the marketplace script attaches to
    # its cards must be written into the page, not into the script.
    html = _read("rororo-plugins.html")
    tpl = html[html.index('<template class="plugin-meters">'):html.index("</template>")]
    for repo in ("rororo-ur-afk", "Ur-OCR", "Ur-Score", "rororo-ur-task"):
        assert f'data-repo="estevanhernandez-stack-ed/{repo}"' in tpl
    assert 'data-repo="estevanhernandez-stack-ed/626-game-manifest"' in _read("mod-launcher-games.html")


def test_the_game_feed_keeps_its_fallback_and_fixture_url():
    html = _read("mod-launcher-games.html")
    assert 'data-feed="https://raw.githubusercontent.com/estevanhernandez-stack-ed/626-game-manifest/main/supported-games.json"' in html
    assert '<div class="fallback" hidden>' in html and 'id="hero-fine"' in html
    assert 'id="curated-count"' in html and 'id="nexus-count"' in html


def test_language_pills_default_to_the_first_cut():
    html = _read("rororo-trailer.html")
    assert html.count('class="lang-pill') == 8
    assert '<button type="button" class="lang-pill is-active" data-lang="">English</button>' in html
    assert 'data-base="assets/video/rororo/rororo-launch" data-cut="The launch cut"' in html


def test_a_heading_with_sub_or_aside_is_a_split_row_and_one_without_is_unchanged():
    plain = rpp.section_head({"heading": "A"})
    assert plain == '    <div class="section-hd">\n      <h2>A</h2>\n    </div>\n'
    split = rpp.section_head({"heading": "A", "sub": "<b>s</b>", "aside": "x", "asideId": "n"})
    assert 'class="section-hd split"' in split and '<p class="sub"><b>s</b></p>' in split
    assert '<div class="r" id="n">x</div>' in split


def test_the_nudge_copies_the_canonical_url():
    assert 'data-url="https://626labs.dev/rororo.html"' in _read("rororo.html")
    assert 'data-url="https://626labs.dev/mod-launcher-games.html"' in _read("mod-launcher-games.html")


# --- img width/height (issue #248) -------------------------------------------

def _png(path, size):
    from PIL import Image
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, (10, 20, 30)).save(path)


def test_img_size_attrs_resolves_relative_root_relative_missing_and_urls(tmp_path):
    _png(tmp_path / "assets" / "a.png", (40, 30))
    _png(tmp_path / "play" / "pic.png", (7, 9))
    out = tmp_path / "play" / "index.html"
    # root-relative: from the repo root
    assert rpp.img_size_attrs("/assets/a.png", out, tmp_path) == ' width="40" height="30"'
    # relative: from the page's own directory
    assert rpp.img_size_attrs("pic.png", out, tmp_path) == ' width="7" height="9"'
    # a query string or fragment does not hide the file
    assert rpp.img_size_attrs("/assets/a.png?v=2", out, tmp_path) == ' width="40" height="30"'
    # missing file: no attributes, never an error
    assert rpp.img_size_attrs("/assets/nope.png", out, tmp_path) == ""
    # never fetched, never opened
    for url in ("https://x.test/a.png", "http://x.test/a.png", "//x.test/a.png",
                "data:image/png;base64,AAAA"):
        assert rpp.img_size_attrs(url, out, tmp_path) == ""


def test_hero_and_blocks_emit_size_attributes_for_local_images(tmp_path):
    _png(tmp_path / "assets" / "logo.png", (120, 60))
    _png(tmp_path / "assets" / "shot.png", (300, 200))
    p = _minimal()
    p["_root"] = tmp_path
    hero = rpp.render_hero(p, {"type": "hero", "title": "T",
                               "logo": {"src": "/assets/logo.png", "alt": "L"},
                               "icon": {"src": "/assets/logo.png", "alt": "I"}})
    assert hero.count('width="120" height="60"') == 2
    assert 'alt="L" width="120" height="60" />' in hero
    show = rpp.block_showcase({"src": "/assets/shot.png", "alt": "S"}, p)
    assert 'alt="S" width="300" height="200" />' in show
    gal = rpp._shot({"src": "/assets/shot.png", "alt": "G", "caption": "c"}, p)
    assert 'alt="G" width="300" height="200" loading="lazy" />' in gal


def test_every_local_img_on_a_generated_page_carries_its_real_size():
    from PIL import Image
    img_re = re.compile(r"<img\b[^>]*>")
    checked = 0
    for rel in rpp.generated_pages(ROOT):
        html = _read(rel)
        for tag in img_re.findall(html):
            src = re.search(r'\bsrc="([^"]*)"', tag)
            if not src:
                continue
            src = src.group(1)
            if re.match(r"(?:[a-z][a-z0-9+.-]*:|//)", src, re.I):
                continue
            base = ROOT if src.startswith("/") else (ROOT / rel).parent
            f = base / src.lstrip("/").split("?")[0].split("#")[0]
            if not f.is_file():
                continue
            w = re.search(r'\bwidth="(\d+)"', tag)
            h = re.search(r'\bheight="(\d+)"', tag)
            assert w and h, f"{rel}: <img> for a local file has no width/height: {tag}"
            with Image.open(f) as im:
                assert (int(w.group(1)), int(h.group(1))) == im.size, f"{rel}: {tag}"
            checked += 1
    assert checked > 0
