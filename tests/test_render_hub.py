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
