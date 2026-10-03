"""assets/roundup/index.json, the site-doctor roundup check, and
scripts/refresh-roundup.py's CI-safe half (--index-only)."""
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


site_doctor = _load("site_doctor_roundup", "site-doctor.py")
refresh = _load("refresh_roundup", "refresh-roundup.py")

INDEX = ROOT / "assets" / "roundup" / "index.json"
KEYS = ["id", "name", "siteId", "repo", "sourceDir", "harvested",
        "icon", "logo", "hero", "screenshots", "other"]
PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082"
)


# --- the manifest ----------------------------------------------------------
def test_manifest_shape():
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    assert set(data) == {"generated", "note", "products", "gaps"}
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", data["generated"])
    ids = [p["id"] for p in data["products"]]
    assert ids == sorted(ids) and len(ids) == len(set(ids))
    folders = sorted(p.name for p in (ROOT / "assets" / "roundup").iterdir() if p.is_dir())
    assert ids == folders, "one entry per assets/roundup folder"
    for p in data["products"]:
        assert list(p) == KEYS, p["id"]
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", p["harvested"])
        assert p["repo"] is None or re.fullmatch(r"[\w.-]+/[\w.-]+", p["repo"])
        prefix = f"assets/roundup/{p['id']}/"
        for k in ("icon", "logo", "hero"):
            assert p[k] is None or p[k].startswith(prefix)
        for k in ("screenshots", "other"):
            assert p[k] == sorted(p[k])
            assert all(x.startswith(prefix) for x in p[k])
    assert set(data["gaps"]) == {"siteProductsWithoutRoundup", "roundupWithoutIcon"}


def test_manifest_site_ids_are_real():
    site = json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))
    titles = {p["id"]: p["title"] for p in site["products"]}
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    for p in data["products"]:
        if p["siteId"]:
            assert p["siteId"] in titles, p["id"]
            assert p["name"] == titles[p["siteId"]]


def test_manifest_is_lf():
    assert b"\r\n" not in INDEX.read_bytes()


# --- refresh-roundup.py ----------------------------------------------------
def test_index_only_reproduces_committed_index_byte_for_byte():
    regenerated = refresh.render_index(refresh.build_index(ROOT)).encode("utf-8")
    assert regenerated == INDEX.read_bytes(), (
        "index.json is stale: python scripts/refresh-roundup.py --index-only"
    )


def test_index_only_check_mode_passes_on_committed_tree():
    assert refresh.main(["--index-only", "--check"]) == 0


def test_mapping_covers_every_folder_and_never_reads_walled_repos():
    folders = {p.name for p in (ROOT / "assets" / "roundup").iterdir() if p.is_dir()}
    assert folders <= set(refresh.PRODUCTS)
    for pid, meta in refresh.PRODUCTS.items():
        assert not refresh.is_forbidden(meta.get("local")), pid
    assert refresh.is_forbidden("Marcus")
    assert refresh.is_forbidden("PriceScoutENTReact")
    assert refresh.is_forbidden("theatre-operations-platform")


def test_harvest_refuses_in_ci(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert refresh.main([], root=tmp_path, projects=tmp_path) == 2
    assert refresh.main(["--apply"], root=tmp_path, projects=tmp_path) == 2


def test_classify_picks_marks_by_name_and_dims():
    c = refresh.classify([
        ("icon-1024.png", (1024, 1024)),
        ("splash-icon.png", (2048, 2048)),
        ("logo-portrait-720x1080.png", (720, 1080)),
        ("hero.png", (1280, 640)),
        ("screenshots/a.png", (1440, 900)),
        ("favicon.svg", (100, 100)),
    ])
    assert c["icon"] == "icon-1024.png"
    assert c["logo"] == "logo-portrait-720x1080.png"
    assert c["hero"] == "hero.png"
    assert c["screenshots"] == ["screenshots/a.png"]
    assert c["other"] == ["favicon.svg", "splash-icon.png"]


def test_variant_collapse_keeps_largest(tmp_path):
    from PIL import Image

    src = tmp_path / "proj" / "Repo" / "store"
    src.mkdir(parents=True)
    for n in (71, 150, 300):
        Image.new("RGB", (n, n)).save(src / f"app-tile-{n}x{n}.png")
    (src / "README.md").write_text("listing copy", encoding="utf-8")
    Image.new("RGB", (44, 44)).save(src / "Logo.scale-400.png")
    meta = {"local": "Repo", "rules": [("dir", "store", "", {"variants": True})]}
    assert list(refresh.expected_files(meta, tmp_path / "proj")) == ["app-tile-300x300.png"]


# --- the site-doctor check -------------------------------------------------
def _tree(tmp_path):
    ru = tmp_path / "assets" / "roundup" / "app"
    ru.mkdir(parents=True)
    (ru / "icon.png").write_bytes(PNG_1PX)
    (tmp_path / "assets" / "roundup" / "README.md").write_text("x", encoding="utf-8")
    index = {"products": [{"id": "app", "icon": "assets/roundup/app/icon.png",
                           "logo": None, "hero": None, "screenshots": [], "other": []}]}
    (tmp_path / "assets" / "roundup" / "index.json").write_text(json.dumps(index), encoding="utf-8")
    return ru, index


def test_roundup_check_clean_tree_passes(tmp_path):
    _tree(tmp_path)
    assert site_doctor.check_roundup(tmp_path) == []


def test_roundup_check_catches_missing_path(tmp_path):
    ru, index = _tree(tmp_path)
    index["products"][0]["hero"] = "assets/roundup/app/hero.png"
    (tmp_path / "assets" / "roundup" / "index.json").write_text(json.dumps(index), encoding="utf-8")
    failures = site_doctor.check_roundup(tmp_path)
    assert len(failures) == 1 and "missing file" in failures[0] and "hero.png" in failures[0]


def test_roundup_check_catches_unindexed_image(tmp_path):
    ru, _ = _tree(tmp_path)
    (ru / "screenshots").mkdir()
    (ru / "screenshots" / "new.png").write_bytes(PNG_1PX)
    failures = site_doctor.check_roundup(tmp_path)
    assert len(failures) == 1 and "not in index.json" in failures[0]


def test_roundup_check_catches_stray_non_image(tmp_path):
    ru, _ = _tree(tmp_path)
    (ru / "store-listing.md").write_text("internal release notes", encoding="utf-8")
    (ru / ".gitkeep").write_bytes(b"")
    failures = site_doctor.check_roundup(tmp_path)
    assert len(failures) == 2
    assert all("non-image" in f for f in failures)


def test_roundup_check_catches_missing_index(tmp_path):
    ru, _ = _tree(tmp_path)
    (tmp_path / "assets" / "roundup" / "index.json").unlink()
    assert any("index.json is missing" in f for f in site_doctor.check_roundup(tmp_path))


def test_roundup_check_passes_on_the_real_tree():
    assert site_doctor.check_roundup(ROOT) == []
