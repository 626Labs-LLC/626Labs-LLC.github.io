import json, sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import theme_registry as tr


def _reg():
    return {"active": "a", "queue": ["b", "c"], "archive": []}


def test_rotate_promotes_and_archives():
    out = tr.rotate(_reg(), "2026-09")
    assert out["active"] == "b"
    assert out["queue"] == ["c"]
    assert out["archive"] == [
        {"slug": "a", "month": "2026-09", "url": "/themes/archive/2026-09/"}
    ]


def test_rotate_is_pure():
    reg = _reg()
    tr.rotate(reg, "2026-09")
    assert reg == _reg()


def test_rotate_empty_queue_raises():
    with pytest.raises(ValueError, match="queue is empty"):
        tr.rotate({"active": "a", "queue": [], "archive": []}, "2026-09")


def test_validate_flags_missing_theme_dir(tmp_path):
    (tmp_path / "themes").mkdir()
    errs = tr.validate({"active": "ghost", "queue": [], "archive": []}, root=tmp_path)
    assert any("ghost" in e for e in errs)


def _make_complete_theme(tmp_path, slug):
    d = tmp_path / "themes" / slug
    (d / "archetypes").mkdir(parents=True)
    for f in ("tokens.css", "theme.json"):
        (d / f).write_text("x", encoding="utf-8")
    for a in tr.REQUIRED_ARCHETYPES:
        (d / "archetypes" / f"{a}.html").write_text("x", encoding="utf-8")


def test_validate_flags_duplicate_queue(tmp_path):
    for slug in ("a", "b"):
        _make_complete_theme(tmp_path, slug)
    errs = tr.validate({"active": "a", "queue": ["b", "b"], "archive": []}, root=tmp_path)
    assert any("duplicate" in e.lower() for e in errs)


def test_theme_complete_requires_all_four_archetypes(tmp_path):
    # Every archetype file present but one -> a named, specific failure.
    _make_complete_theme(tmp_path, "partial")
    (tmp_path / "themes" / "partial" / "archetypes" / "product.html").unlink()
    errs = tr._theme_complete("partial", tmp_path)
    assert any("archetypes/product.html" in e for e in errs)


def test_theme_complete_shell_html_alone_no_longer_satisfies(tmp_path):
    # The legacy fallback is gone: a theme with only shell.html (no
    # archetypes/ dir at all) must fail completeness, not be waved through.
    d = tmp_path / "themes" / "legacy-only"
    d.mkdir(parents=True)
    for f in ("tokens.css", "theme.json", "shell.html"):
        (d / f).write_text("x", encoding="utf-8")
    errs = tr._theme_complete("legacy-only", tmp_path)
    assert len(errs) == len(tr.REQUIRED_ARCHETYPES)
    assert all("archetypes/" in e for e in errs)


def test_real_registry_is_valid():
    assert tr.validate(tr.load()) == []
