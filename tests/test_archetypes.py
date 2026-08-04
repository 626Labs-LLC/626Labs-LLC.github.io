import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import archetypes as az


def test_four_archetypes():
    assert az.ARCHETYPES == ("home", "product", "reading", "utility")


def test_every_archetype_has_a_vocabulary():
    for a in az.ARCHETYPES:
        assert az.VOCABULARY[a], f"{a} has no required classes"


def test_archetype_for_known_page():
    mapping = {"index.html": "home", "about.html": "reading"}
    assert az.archetype_for("about.html", mapping) == "reading"


def test_archetype_for_unmapped_page_raises_naming_it():
    with pytest.raises(KeyError, match="ghost.html"):
        az.archetype_for("ghost.html", {"index.html": "home"})


def test_validate_flags_unknown_archetype(tmp_path):
    (tmp_path / "index.html").write_text("x", encoding="utf-8")
    errs = az.validate({"index.html": "spaceship"}, root=tmp_path)
    assert any("spaceship" in e for e in errs)


def test_validate_flags_missing_file(tmp_path):
    errs = az.validate({"ghost.html": "home"}, root=tmp_path)
    assert any("ghost.html" in e for e in errs)


def test_real_mapping_is_valid():
    assert az.validate(az.load()) == []
