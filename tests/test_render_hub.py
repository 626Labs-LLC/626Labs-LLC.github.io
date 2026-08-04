import importlib.util
import json
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


# ─── plugin-family grouping ─────────────────────────────────────────

def _products():
    mk = lambda i: {"id": i, "title": i, "description": "d", "tags": [], "status": "live"}
    return [mk("celestia-3"), mk("vibe-cartographer"), mk("vibe-doc"),
            mk("rororo"), mk("vibe-test"), mk("conundrum")]


def _family():
    return {
        "memberIds": ["vibe-cartographer", "vibe-doc", "vibe-test"],
        "card": {"id": "vibe-family", "title": "The Vibe Plugin Family",
                 "description": "One playbook.", "tags": [], "status": "live",
                 "flagship": True, "repo": "estevanhernandez-stack-ed/vibe-plugins",
                 "productPage": "plugins/", "productPageLabel": "Meet the family"},
    }


def test_family_grouping_collapses_members_in_place():
    html = render_hub.render_products(_products(), _family())
    assert html.count('<article class="product') == 4  # 3 non-members + 1 family card
    assert "The Vibe Plugin Family" in html
    assert html.index("celestia-3") < html.index("The Vibe Plugin Family") < html.index("rororo")
    for member in ("vibe-doc", "vibe-test"):
        assert f"<h3>{member}</h3>" not in html


def test_family_grouping_absent_config_is_identity():
    prods = _products()
    assert render_hub.render_products(prods) == render_hub.render_products(prods, None)
    assert render_hub.render_products(prods).count('<article class="product') == 6


def test_family_flagship_head_links_product_page():
    html = render_hub.render_products(_products(), _family())
    assert 'href="plugins/"' in html
    assert "Meet the family" in html


# ─── founding (section 02) ───────────────────────────────────────────

def _founding():
    return {"eyebrow": "02 · The founding", "headline": "It started with a Nintendo",
            "quote": "I build tools, because care doesn't always scale",
            "paragraphs": ["<strong>First</strong> para.", "Second para."],
            "door": {"label": "Read the whole story", "href": "about.html"}}


def test_founding_renders_section_with_door():
    html = render_hub.render_founding(_founding())
    assert 'id="founding"' in html and 'href="about.html"' in html
    assert "Read the whole story" in html and "care doesn" in html


def test_founding_paragraphs_render_raw_html():
    assert "<strong>First</strong>" in render_hub.render_founding(_founding())


# ─── themes gallery (themes.html zone) ───────────────────────────────

def _make_theme(tmp_path, slug, **meta):
    d = tmp_path / "themes" / slug
    d.mkdir(parents=True)
    for name in ("shell.html", "tokens.css"):
        (d / name).write_text("x", encoding="utf-8")
    base = {"name": slug.title(), "slug": slug, "thesis": f"{slug} thesis.", "month": "2026-08"}
    base.update(meta)
    (d / "theme.json").write_text(json.dumps(base), encoding="utf-8")


def test_themes_gallery_active_only_renders_one_live_card_linking_root(tmp_path):
    _make_theme(tmp_path, "phosphor-blueprint", name="Phosphor Blueprint",
                thesis="CRT phosphor kit.", month="2026-08")
    reg = {"active": "phosphor-blueprint", "queue": [], "archive": []}
    html = render_hub.render_themes_gallery(reg, root=tmp_path)
    assert html.count('class="theme-card ') == 1
    assert '<a class="theme-card live" href="/">' in html
    assert '<span class="theme-status live">Live</span>' in html
    assert "Phosphor Blueprint" in html and "CRT phosphor kit." in html
    assert "August 2026" in html


def test_themes_gallery_queued_theme_has_no_link_and_queued_chip(tmp_path):
    _make_theme(tmp_path, "phosphor-blueprint")
    _make_theme(tmp_path, "next-up", name="Next Up", thesis="Coming soon.")
    reg = {"active": "phosphor-blueprint", "queue": ["next-up"], "archive": []}
    html = render_hub.render_themes_gallery(reg, root=tmp_path)
    assert '<div class="theme-card queued">' in html
    assert '<span class="theme-status queued">Queued</span>' in html
    assert "Next Up" in html
    # No href anywhere pointing at a queued theme — it isn't live yet.
    assert 'href="/next-up' not in html


def test_themes_gallery_archived_theme_links_registry_url_and_month(tmp_path):
    _make_theme(tmp_path, "phosphor-blueprint")
    _make_theme(tmp_path, "old-look", name="Old Look", thesis="Retired now.", month="2026-07")
    reg = {
        "active": "phosphor-blueprint",
        "queue": [],
        "archive": [{"slug": "old-look", "month": "2026-08", "url": "/themes/archive/2026-08/"}],
    }
    html = render_hub.render_themes_gallery(reg, root=tmp_path)
    assert '<a class="theme-card archived" href="/themes/archive/2026-08/">' in html
    assert '<span class="theme-status archived">Archived</span>' in html
    # Registry month (when it was actually retired) wins over theme.json's
    # original month — the registry is the authoritative record.
    assert "August 2026" in html


def test_themes_gallery_archive_renders_newest_first(tmp_path):
    _make_theme(tmp_path, "phosphor-blueprint")
    _make_theme(tmp_path, "first-out", name="First Out")
    _make_theme(tmp_path, "second-out", name="Second Out")
    reg = {
        "active": "phosphor-blueprint",
        "queue": [],
        "archive": [
            {"slug": "first-out", "month": "2026-06", "url": "/themes/archive/2026-06/"},
            {"slug": "second-out", "month": "2026-07", "url": "/themes/archive/2026-07/"},
        ],
    }
    html = render_hub.render_themes_gallery(reg, root=tmp_path)
    assert html.index("Second Out") < html.index("First Out")


def test_themes_gallery_missing_theme_json_falls_back_to_slug_name(tmp_path):
    # Active theme dir exists (with theme.json) so the registry stays valid,
    # but an archived slug's source dir is gone entirely.
    _make_theme(tmp_path, "phosphor-blueprint")
    reg = {
        "active": "phosphor-blueprint",
        "queue": [],
        "archive": [{"slug": "long-gone", "month": "2026-05", "url": "/themes/archive/2026-05/"}],
    }
    html = render_hub.render_themes_gallery(reg, root=tmp_path)
    assert "Long Gone" in html


def test_themes_gallery_always_has_at_least_the_active_card(tmp_path):
    _make_theme(tmp_path, "phosphor-blueprint")
    reg = {"active": "phosphor-blueprint", "queue": [], "archive": []}
    html = render_hub.render_themes_gallery(reg, root=tmp_path)
    assert html.count('class="theme-card ') == 1


def test_real_themes_registry_renders_at_least_one_card():
    html = render_hub.render_themes_gallery(render_hub.theme_registry.load())
    assert html.count('class="theme-card ') >= 1
    assert '<span class="theme-status live">Live</span>' in html


# ─── main() guardrails (Fix 5) ─────────────────────────────────────────────
#
# Two failure-shaped bugs the whole-branch review caught: a missing theme
# shell used to fall back to reading the LIVE index.html as its own source
# (so `--check` would compare that file against itself and stay green
# forever, and a genuinely broken theme would render as a silent no-op
# instead of an error); and `--theme` without `--out` had no guard at all,
# so a typo'd invocation would render an arbitrary theme straight over the
# live site and every other surface it touches (feed, sitemap, story pages,
# themes.html).


def test_theme_without_out_is_a_usage_error(capsys):
    # This guard fires before anything touches the registry or the
    # filesystem, so it's safe to exercise against the real repo state.
    rc = render_hub.main(["--theme", "phosphor-blueprint"])
    assert rc != 0
    err = capsys.readouterr().err
    assert "--out" in err


def test_missing_shell_fails_loudly_instead_of_falling_back_to_live_index(tmp_path, capsys):
    # A slug with no themes/<slug>/ directory at all under the real ROOT.
    # theme+out are paired (clears the first guard above) so this isolates
    # the missing-shell guard; nothing is written since it errors first.
    rc = render_hub.main([
        "--theme", "definitely-not-a-real-theme-slug",
        "--out", str(tmp_path),
    ])
    assert rc != 0
    err = capsys.readouterr().err
    assert "shell" in err.lower()
    assert "definitely-not-a-real-theme-slug" in err
    assert not (tmp_path / "index.html").exists()
