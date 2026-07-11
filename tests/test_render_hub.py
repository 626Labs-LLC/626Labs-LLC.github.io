import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

# render-hub.py has a hyphen (matches site-doctor.py convention) — load by path.
_spec = importlib.util.spec_from_file_location(
    "render_hub", ROOT / "scripts" / "render-hub.py"
)
render_hub = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(render_hub)


def _make_site(tmp_path):
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
    for name in ("vibe-walk", "editorial", "bacon-trail"):
        d = tmp_path / name
        d.mkdir()
        (d / "index.html").write_text("<html></html>", encoding="utf-8")


def test_sitemap_includes_home_and_subpages(tmp_path):
    _make_site(tmp_path)
    xml = render_hub.render_sitemap(root=tmp_path)
    assert xml.startswith('<?xml version="1.0" encoding="utf-8"?>')
    assert "<urlset" in xml and "</urlset>" in xml
    assert "<loc>https://626labs.dev/</loc>" in xml
    assert "<loc>https://626labs.dev/vibe-walk/</loc>" in xml
    assert "<loc>https://626labs.dev/editorial/</loc>" in xml
    assert "<loc>https://626labs.dev/bacon-trail/</loc>" in xml


def test_sitemap_is_deterministic(tmp_path):
    _make_site(tmp_path)
    assert render_hub.render_sitemap(root=tmp_path) == render_hub.render_sitemap(root=tmp_path)


def test_sitemap_home_listed_first_with_top_priority(tmp_path):
    _make_site(tmp_path)
    xml = render_hub.render_sitemap(root=tmp_path)
    assert xml.index("<loc>https://626labs.dev/</loc>") < xml.index(
        "<loc>https://626labs.dev/bacon-trail/</loc>"
    )
    assert "<priority>1.0</priority>" in xml
    assert "<priority>0.8</priority>" in xml


def test_sitemap_subpages_sorted_alphabetically(tmp_path):
    _make_site(tmp_path)
    xml = render_hub.render_sitemap(root=tmp_path)
    order = [
        xml.index(f"<loc>https://626labs.dev/{name}/</loc>")
        for name in ("bacon-trail", "editorial", "vibe-walk")
    ]
    assert order == sorted(order)


def test_sitemap_honors_exclude(tmp_path, monkeypatch):
    _make_site(tmp_path)
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    (drafts / "index.html").write_text("<html></html>", encoding="utf-8")
    monkeypatch.setattr(render_hub, "SITEMAP_EXCLUDE", frozenset({"drafts"}))
    xml = render_hub.render_sitemap(root=tmp_path)
    assert "drafts" not in xml


# ─── conundrum shop page zones ──────────────────────────────────────

def _conundrum(**over):
    base = {
        "etsyUrl": "https://www.etsy.com/shop/ConundrumByEste",
        "repoUrl": None,
        "products": [
            {
                "title": "Fire & Ice Spider Monster Joggers",
                "price": "$46.99",
                "image": "assets/screenshots/conundrum/fire-ice-spider-monster-joggers.jpg",
                "etsyListing": "https://www.etsy.com/listing/111",
                "chip": "recently sold",
            },
            {
                "title": "Not My Problem Penguin Crew Socks",
                "price": "$21.99",
                "image": "assets/screenshots/conundrum/not-my-problem-penguin-crew-socks.jpg",
                "etsyListing": "https://www.etsy.com/listing/222",
            },
        ],
    }
    base.update(over)
    return base


def test_conundrum_products_renders_cards_in_array_order():
    html = render_hub.render_conundrum_products(_conundrum())
    assert html.count('class="merch-card"') == 2
    assert html.index("Fire &amp; Ice") < html.index("Penguin")
    assert 'href="https://www.etsy.com/listing/111"' in html
    assert 'src="assets/screenshots/conundrum/fire-ice-spider-monster-joggers.jpg"' in html
    assert "$46.99" in html


def test_conundrum_products_chip_is_optional():
    html = render_hub.render_conundrum_products(_conundrum())
    assert html.count('class="merch-chip"') == 1
    assert "recently sold" in html


def test_conundrum_products_slugs_data_etsy():
    html = render_hub.render_conundrum_products(_conundrum())
    assert 'data-etsy="fire-ice-spider-monster-joggers"' in html


def test_conundrum_products_empty_list_renders_nothing():
    assert render_hub.render_conundrum_products(_conundrum(products=[])) == ""


def test_conundrum_repo_collapses_when_null():
    assert render_hub.render_conundrum_repo(_conundrum()) == ""
    assert render_hub.render_conundrum_repo(_conundrum(repoUrl="")) == ""


def test_conundrum_repo_renders_when_set():
    html = render_hub.render_conundrum_repo(
        _conundrum(repoUrl="https://github.com/626Labs-LLC/pod-pipeline")
    )
    assert 'href="https://github.com/626Labs-LLC/pod-pipeline"' in html
    assert 'class="repo-cta"' in html
    assert "Read the code" in html
