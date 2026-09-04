"""The `raster` block and the generators that read it.

What is pinned here, and why each pin exists:

- The block parses and validates for every REGISTERED theme (active and
  queued), and a malformed one fails naming its key: the four generators
  run unattended on the rotation morning, so the doctor has to catch a
  bad block while the theme is still queued.
- RASTER_DEFAULTS IS phosphor-blueprint's block: a theme with no block
  regresses nothing.
- The field primitives branch on texture / glow / colorBar.
- The Phosphor Blueprint path is BYTE-IDENTICAL to the committed assets:
  the refactor moved the drawing into raster_theme and nothing off-site
  may move until the 1st.
- The grain is deterministic: rebuild-hub.yml's OG-card --check
  byte-compares, and a noisy grain would fail it on every run.
- The field-free outputs (transparent icons, lockup, portrait) are the
  same bytes under every theme: they carry no field, so they carry no
  theme.
- The rotation regenerates the rasters after the render and before the
  first gate, and commits all three output locations.
"""
import importlib.util
import io
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import raster_theme as rt  # noqa: E402
import theme_registry  # noqa: E402


def _load(name: str, module: str):
    spec = importlib.util.spec_from_file_location(module, SCRIPTS / name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _registered_slugs():
    reg = theme_registry.load()
    return [reg["active"], *reg.get("queue", [])]


SLATE = {
    "field": "#3A4350", "ink": "#F7F5F0", "dim": "#C3C1BA",
    "texture": "grain", "glow": False, "colorBar": True, "bodyFace": "serif",
}


# ─── the block ───────────────────────────────────────────────────────────
@pytest.mark.parametrize("slug", _registered_slugs())
def test_every_registered_theme_declares_a_block_that_parses(slug):
    block = rt.read_block(slug)
    assert block is not None, f"{slug} has no raster block"
    assert rt.validate_block(block) == []
    r = rt.load(slug)
    assert r.slug == slug
    assert r.texture in rt.TEXTURES


def test_defaults_are_phosphor_blueprints_block_exactly():
    """A theme with no block draws PB. If PB's own block ever drifts from
    RASTER_DEFAULTS, a block-less theme and the live theme disagree about
    what 'the default' is."""
    assert rt.read_block("phosphor-blueprint") == rt.RASTER_DEFAULTS
    assert rt.load("phosphor-blueprint").is_default


def test_slate_block_is_the_spec_treatment():
    assert rt.read_block("slate-broadsheet") == SLATE


def test_a_theme_with_no_block_gets_the_defaults(tmp_path):
    (tmp_path / "content").mkdir()
    (tmp_path / "content" / "themes.json").write_text(
        json.dumps({"active": "bare", "queue": [], "archive": []}), encoding="utf-8")
    (tmp_path / "themes" / "bare").mkdir(parents=True)
    (tmp_path / "themes" / "bare" / "theme.json").write_text('{"name": "Bare"}', encoding="utf-8")
    r = rt.load(root=tmp_path)  # slug None -> the active theme of THAT root
    assert r.slug == "bare"
    assert r.is_default
    assert (r.field, r.ink, r.dim) == ((0, 0, 0), (231, 237, 245), (138, 153, 174))


@pytest.mark.parametrize("mutation, key", [
    ({"field": "not-a-color"}, "field"),
    ({"ink": 12}, "ink"),
    ({"dim": "#GGGGGG"}, "dim"),
    ({"texture": "scanlines"}, "texture"),
    ({"glow": "false"}, "glow"),
    ({"colorBar": 1}, "colorBar"),
    ({"bodyFace": "mono"}, "bodyFace"),
    ({"colourBar": True}, "colourBar"),
])
def test_a_malformed_block_fails_naming_the_key(mutation, key):
    block = {**SLATE, **mutation}
    errs = rt.validate_block(block)
    assert errs, f"{mutation} was accepted"
    assert any(f"raster.{key}" in e for e in errs), errs
    with pytest.raises(ValueError, match=f"raster.{key}"):
        rt.from_block("x", block)


@pytest.mark.parametrize("key", rt.REQUIRED_KEYS)
def test_a_missing_required_key_fails_naming_it(key):
    block = {k: v for k, v in SLATE.items() if k != key}
    errs = rt.validate_block(block)
    assert errs == [f"raster.{key}: missing"]


def test_body_face_is_optional_and_defaults_to_sans():
    block = {k: v for k, v in SLATE.items() if k != "bodyFace"}
    assert rt.validate_block(block) == []
    assert rt.from_block("x", block).body_face == "sans"


def test_block_accepts_any_css_color_syntax():
    block = {**SLATE, "field": "rgb(58 67 80)", "ink": "oklch(96% 0.01 90)", "dim": "hsl(50 7% 75%)"}
    assert rt.validate_block(block) == []
    r = rt.from_block("x", block)
    assert r.field == (58, 67, 80)


def test_not_an_object_is_one_error():
    assert rt.validate_block("grain") == ["raster: must be an object, got str"]


def test_theme_doctor_grades_the_block():
    """theme-doctor.main reads theme.json; check_raster_block is the hook.
    A malformed block fails the doctor with the key named; no block passes."""
    td = _load("theme-doctor.py", "theme_doctor_for_raster")
    assert td.check_raster_block({"name": "x"}) == []
    errs = td.check_raster_block({"raster": {**SLATE, "texture": "bloom"}})
    assert len(errs) == 1 and "raster.texture" in errs[0] and "bloom" in errs[0]


def test_theme_doctor_main_fails_a_registered_theme_with_a_malformed_block(monkeypatch, tmp_path, capsys):
    """End to end through main(): copy the queued theme, break its block,
    point the doctor at the copy. Static path only (no --browser)."""
    import shutil
    td = _load("theme-doctor.py", "theme_doctor_for_raster_main")
    slug = "slate-broadsheet"
    src = theme_registry.theme_dir(slug)
    dst = tmp_path / "themes" / slug
    shutil.copytree(src, dst)
    meta = json.loads((dst / "theme.json").read_text(encoding="utf-8"))
    meta["raster"]["glow"] = "no"
    (dst / "theme.json").write_text(json.dumps(meta), encoding="utf-8")
    monkeypatch.setattr(td.theme_registry, "theme_dir", lambda s, root=None: dst if s == slug else src)
    rc = td.main([slug])
    out = capsys.readouterr().out
    assert rc == 1
    assert "raster.glow" in out, out


# ─── contrast ────────────────────────────────────────────────────────────
def test_contrast_math_matches_theme_doctors():
    td = _load("theme-doctor.py", "theme_doctor_for_contrast")
    for a, b in (((247, 245, 240), (58, 67, 80)), ((195, 193, 186), (58, 67, 80)), ((23, 212, 250), (58, 67, 80))):
        assert rt.contrast_ratio(a, b) == pytest.approx(td._contrast_ratio(a, b))


@pytest.mark.parametrize("slug", _registered_slugs())
def test_every_text_ink_clears_aa_on_the_field_under_the_grain(slug):
    """Social cards get read on phones in sunlight: title (ink), dek and
    dateline (dim) and the cyan wordmark, each against the field as the
    grain leaves it, all at or above 4.5:1."""
    r = rt.load(slug)
    ground = rt.grained_field(r)
    for name, fg in (("ink", r.ink), ("dim", r.dim), ("cyan", rt.CYAN)):
        assert rt.contrast_ratio(fg, ground) >= 4.5, (slug, name, rt.contrast_ratio(fg, ground))


def test_slate_contrast_numbers_are_the_theme_sheets():
    """The numbers the tokens.css header records, so the raster and the
    page agree about the same inks on the same ground."""
    r = rt.load("slate-broadsheet")
    assert rt.contrast_ratio(r.ink, r.field) == pytest.approx(9.18, abs=0.01)
    assert rt.contrast_ratio(r.dim, r.field) == pytest.approx(5.55, abs=0.01)
    assert rt.contrast_ratio(rt.CYAN, r.field) == pytest.approx(5.64, abs=0.01)
    assert rt.grained_field(r) == (65, 73, 86)


# ─── the primitives branch on the block ──────────────────────────────────
def _raster(**over):
    return rt.from_block("t", {**SLATE, **over})


def _px(img, x, y):
    return img.convert("RGB").getpixel((x, y))


def test_texture_grid_draws_the_drafting_grid_and_grain_does_not():
    grid = rt.paint_field(200, 200, _raster(texture="grid"))
    # Row 0 and column 0 carry the 120px line (alpha 28 cyan over the field).
    assert _px(grid, 0, 5) != _px(grid, 3, 5)
    assert _px(grid, 5, 0) != _px(grid, 5, 3)
    flat = rt.paint_field(200, 200, _raster(texture="none"))
    arr = np.asarray(flat.convert("RGB"))
    assert (arr == arr[0, 0]).all(), "texture none must be a flat field"
    grain = rt.paint_field(200, 200, _raster(texture="grain"))
    arr = np.asarray(grain.convert("RGB")).astype(int)
    assert not (arr == arr[0, 0]).all(), "grain must vary"
    # Mean coverage ~3.5 percent of the ink over the field, never below it.
    field = np.array(_raster().field)
    assert (arr >= field - 1).all()
    mean = arr.reshape(-1, 3).mean(axis=0)
    expected = field + rt.GRAIN_OPACITY / 2 * (np.array(_raster().ink) - field)
    assert np.abs(mean - expected).max() < 1.5, (mean, expected)


def test_grain_is_deterministic_and_size_keyed():
    a = np.asarray(rt.paper_grain(300, 120, (247, 245, 240)))
    b = np.asarray(rt.paper_grain(300, 120, (247, 245, 240)))
    assert (a == b).all()
    c = np.asarray(rt.paper_grain(300, 120, (247, 245, 240), seed=rt.GRAIN_SEED + 1))
    assert not (a == c).all()


def test_glow_false_draws_no_glow_and_glow_true_does():
    glows = ((0.5, 0.5, rt.MAGENTA, 200, 0.5),)
    lit = rt.paint_field(100, 100, _raster(texture="none", glow=True), glows=glows)
    matte = rt.paint_field(100, 100, _raster(texture="none", glow=False), glows=glows)
    assert _px(lit, 50, 50) != _px(lit, 0, 0)
    assert _px(matte, 50, 50) == _px(matte, 0, 0)


def test_texture_can_be_suppressed_at_icon_scale():
    """The animated icon keeps PB's rule: no grid at icon scale."""
    f = rt.paint_field(200, 200, _raster(texture="grid"), texture=False)
    arr = np.asarray(f.convert("RGB"))
    assert (arr == arr[0, 0]).all()


def test_color_bar_is_cyan_magenta_paper_and_only_when_declared():
    r = _raster(texture="none")
    bar = rt.color_bar(r, 10, gap=4)
    assert bar.size == (38, 10)
    assert bar.getpixel((5, 5))[:3] == rt.CYAN
    assert bar.getpixel((19, 5))[:3] == rt.MAGENTA
    assert bar.getpixel((33, 5))[:3] == r.ink
    assert bar.getpixel((12, 5))[3] == 0  # the gap is transparent
    canvas = rt.paint_field(120, 60, r)
    rt.place_color_bar(canvas, r, right=110, bottom=50)
    assert any(canvas.getpixel((x, 45))[:3] == rt.MAGENTA for x in range(60, 110))
    off = rt.paint_field(120, 60, r)
    rt.place_color_bar(off, _raster(texture="none", colorBar=False), right=110, bottom=50)
    assert np.asarray(off.convert("RGB")).reshape(-1, 3).tolist().count(list(rt.MAGENTA)) == 0


# ─── the generators ──────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def eb():
    return _load("export-brand.py", "export_brand_for_tests")


@pytest.fixture(scope="module")
def icon(eb, tmp_path_factory):
    return eb.build_transparent_icon(tmp_path_factory.mktemp("icon"))


def test_phosphor_blueprint_banner_and_favicon_are_byte_identical_to_the_committed_ones(eb, icon, tmp_path):
    """The no-regression proof: the default path reproduces today's assets
    exactly. Only the 1200x630 banner, the favicon and the animated icon
    here (the full set is ~5s); export-brand.py with no flag is the whole
    proof and is run before every commit of this branch.

    Only while Phosphor Blueprint is live: the committed assets are the
    ACTIVE theme's build, so once the rotation regenerates them in slate
    a PB build cannot match them, and this gate runs inside
    rotate-theme.yml after the registry flips. (A post-rotation "active
    build == committed" pin is deliberately not here either: assets/brand
    is ubuntu-built from the 1st on, and FreeType rasterizes text a few
    bytes differently on Windows, the same reason CLAUDE.md gives for not
    committing OG cards from this box.)"""
    if theme_registry.active_slug(theme_registry.load()) != "phosphor-blueprint":
        pytest.skip("the PB no-regression proof only applies while phosphor-blueprint is live")
    pb = rt.load("phosphor-blueprint")
    eb.build_banner((1200, 630), icon, tmp_path / "b.png", pb)
    assert (tmp_path / "b.png").read_bytes() == (ROOT / "assets" / "brand" / "banner-1200x630.png").read_bytes()
    eb.build_site_favicon(icon, pb, tmp_path / "f.png")
    assert (tmp_path / "f.png").read_bytes() == (ROOT / "favicon-626.png").read_bytes()
    eb.build_animated_icon(icon, pb, tmp_path)
    assert (tmp_path / "icon-animated-512.gif").read_bytes() == (ROOT / "assets" / "brand" / "icon-animated-512.gif").read_bytes()


def test_field_free_outputs_are_the_same_bytes_under_every_theme(eb, tmp_path):
    """Transparent icons, the lockup and the portrait carry no field, so
    they are identical to the committed files whatever theme is active."""
    eb.build_transparent_icon(tmp_path)
    eb.build_transparent_lockup(tmp_path)
    eb.build_press_portrait(tmp_path)
    for name in ("icon-transparent-256.png", "icon-transparent-512.png", "icon-transparent-1024.png",
                 "logo-lockup-transparent-1080.png", "logo-portrait-256.png"):
        assert (tmp_path / name).read_bytes() == (ROOT / "assets" / "brand" / name).read_bytes(), name


def test_slate_banner_is_grained_slate_with_a_color_bar_and_no_glow(eb, icon, tmp_path):
    slate = rt.load("slate-broadsheet")
    eb.build_banner((600, 315), icon, tmp_path / "s.png", slate)
    img = Image.open(tmp_path / "s.png").convert("RGB")
    arr = np.asarray(img).astype(int)
    field, ink = np.array(slate.field), np.array(slate.ink)
    # Top-left patch sits inside the grain envelope: field .. field + 7% ink.
    patch = arr[:8, :8].reshape(-1, 3)
    assert (patch >= field - 1).all() and (patch <= field + rt.GRAIN_OPACITY * (ink - field) + 1).all()
    assert not (patch == patch[0]).all()
    # The color bar's magenta swatch is on the canvas; PB's has no magenta pixel.
    assert (arr.reshape(-1, 3) == np.array(rt.MAGENTA)).all(axis=1).any()


def test_slate_animated_icon_is_a_single_frame_gif(eb, icon, tmp_path):
    eb.build_animated_icon(icon, rt.load("slate-broadsheet"), tmp_path)
    g = Image.open(tmp_path / "icon-animated-512.gif")
    assert g.format == "GIF"
    assert getattr(g, "n_frames", 1) == 1
    # Pillow merges identical consecutive frames on save, so 40 flat frames
    # would ALSO read as one frame, carrying the whole 2000ms loop as its
    # duration. A frame drawn once carries one frame's 50ms.
    assert g.info.get("duration") == 50
    eb.build_animated_icon(icon, rt.load("phosphor-blueprint"), tmp_path)
    assert getattr(Image.open(tmp_path / "icon-animated-512.gif"), "n_frames", 1) > 1


def test_slate_favicon_is_flat_slate_with_no_bloom(eb, icon, tmp_path):
    eb.build_site_favicon(icon, rt.load("slate-broadsheet"), tmp_path / "f.png")
    img = Image.open(tmp_path / "f.png").convert("RGB")
    assert img.getpixel((0, 0)) == (58, 67, 80)
    # Halfway in from the corner toward the mark, PB's bloom lifts the field;
    # slate's stays the ground.
    assert img.getpixel((40, 256)) == (58, 67, 80)


def test_og_card_branches_on_the_block():
    og = _load("build-og-cards.py", "build_og_cards_for_tests")
    rh = og._load_render_hub()
    story = next(s for s in rh.discover_stories() if not s.get("external_url"))
    pb = og.build_card(story, rh, rt.load("phosphor-blueprint"))
    slate = og.build_card(story, rh, rt.load("slate-broadsheet"))
    # (0,0) on PB is a grid line under the cyan glow; sample off-grid,
    # bottom-middle, where the field is near-black.
    assert max(pb.getpixel((601, 629))) < 40
    assert pb.getpixel((0, 0)) != slate.getpixel((0, 0))
    arr = np.asarray(slate).astype(int)[:8, :8].reshape(-1, 3)
    assert (arr >= np.array([58, 67, 80]) - 1).all() and (arr <= np.array([72, 80, 92])).all()
    # PB's card is unchanged by the refactor: same bytes as the committed
    # card when this box rasterizes like the runner (one card does), and
    # in any case the same bytes as a second in-memory build.
    buf = io.BytesIO(); pb.save(buf, "PNG", optimize=True)
    buf2 = io.BytesIO(); og.build_card(story, rh, rt.load("phosphor-blueprint")).save(buf2, "PNG", optimize=True)
    assert buf.getvalue() == buf2.getvalue()


def test_og_card_dek_face_follows_body_face():
    og = _load("build-og-cards.py", "build_og_cards_for_dek")
    serif = og._dek_font(_raster(bodyFace="serif"), 27)
    sans = og._dek_font(_raster(bodyFace="sans"), 27)
    assert Path(serif.path).name == "SourceSerif4-Variable.ttf"
    assert Path(sans.path).name == "Inter-Italic-Variable.ttf"


def test_generator_args_parse_theme_and_out():
    slug, out, rest = rt.parse_args(["--check", "--theme", "slate-broadsheet", "--out", "x/y"])
    assert (slug, out, rest) == ("slate-broadsheet", Path("x/y"), ["--check"])
    assert rt.parse_args([]) == (None, None, [])


# ─── the rotation ────────────────────────────────────────────────────────
def test_rotation_regenerates_the_rasters_after_the_render_and_before_the_gates():
    wf = yaml.safe_load((ROOT / ".github" / "workflows" / "rotate-theme.yml").read_text(encoding="utf-8"))
    steps = wf["jobs"]["rotate"]["steps"]
    names = [s.get("name", "") for s in steps]
    render = next(i for i, n in enumerate(names) if n.startswith("Render the new active theme"))
    regen = next(i for i, n in enumerate(names) if "Regenerate the brand rasters" in n)
    first_gate = next(i for i, n in enumerate(names) if n.startswith("Gate:"))
    assert render < regen < first_gate, names
    run = steps[regen]["run"]
    for script in ("export-brand.py", "export-medium-header.py", "export-vibe-plugins-logo.py", "build-og-cards.py"):
        assert f"scripts/{script}" in run, script
    assert run.index("export-brand.py") < run.index("export-medium-header.py")
    assert "set -euo pipefail" in run
    assert steps[regen]["if"] == steps[render]["if"]
    commit = next(s for s in steps if s.get("name", "").startswith("Commit + push rotation"))
    add_line = next(l for l in commit["run"].splitlines() if l.strip().startswith("git add"))
    add_block = commit["run"][commit["run"].index("git add"):commit["run"].index("git commit")]
    assert add_line
    for path in ("assets/brand", "assets/og", "favicon-626.png"):
        assert path in add_block, path


def test_rebuild_hub_retriggers_on_the_raster_module():
    wf = yaml.safe_load((ROOT / ".github" / "workflows" / "rebuild-hub.yml").read_text(encoding="utf-8"))
    paths = wf[True]["push"]["paths"] if True in wf else wf["on"]["push"]["paths"]
    assert "scripts/raster_theme.py" in paths
    assert "scripts/build-og-cards.py" in paths
