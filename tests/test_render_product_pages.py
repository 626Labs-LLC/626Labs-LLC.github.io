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
    assert f'<link rel="canonical" href="{rpp.page_url(rel)}" />' in html


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
