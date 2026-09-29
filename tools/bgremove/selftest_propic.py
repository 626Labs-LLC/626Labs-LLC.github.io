#!/usr/bin/env python3
"""Self-test for propic.py. Run directly: `python selftest_propic.py`

Deliberately NOT named test_*.py. The hub's CI installs `-r requirements.txt
pytest` and that requirements file has no opencv — a collected test module
importing cv2 would turn the site's pipeline red for a tool the site doesn't
build. Run this by hand, or wire it into a job that installs the extras.

Generates its own fixtures, so there is nothing to commit alongside it.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import propic  # noqa: E402

FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {name}{('  — ' + detail) if detail else ''}")
    if not cond:
        FAILURES.append(name)


# ─── fixtures ───────────────────────────────────────────────────────
def make_subject(h: int = 1400, w: int = 1100) -> tuple[np.ndarray, np.ndarray]:
    """Head-and-shoulders with wispy semi-transparent hair and camera grain."""
    rng = np.random.default_rng(7)
    alpha = np.zeros((h, w), np.float32)
    cy, cx = 480, w // 2
    cv2.ellipse(alpha, (cx, 1500), (520, 1000), 0, 0, 360, 1.0, -1)
    cv2.ellipse(alpha, (cx, 830), (110, 190), 0, 0, 360, 1.0, -1)
    cv2.ellipse(alpha, (cx, cy), (245, 320), 0, 0, 360, 1.0, -1)
    cv2.ellipse(alpha, (cx, cy - 90), (275, 275), 0, 180, 360, 1.0, -1)
    for _ in range(90):
        ang = rng.uniform(np.pi, 2 * np.pi)
        x0 = int(cx + 250 * np.cos(ang) * 1.05)
        y0 = int(cy - 90 + 250 * np.sin(ang))
        L = rng.integers(30, 120)
        x1 = int(x0 + L * np.cos(ang + rng.normal(0, .35)))
        y1 = int(y0 + L * np.sin(ang + rng.normal(0, .35)))
        cv2.line(alpha, (x0, y0), (x1, y1), float(rng.uniform(.35, .95)), int(rng.integers(1, 4)))
    alpha = np.clip(cv2.GaussianBlur(alpha, (0, 0), 2.2), 0, 1)

    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    key = np.clip(1.25 - 0.9 * np.sqrt(((xs - (cx - 190)) / 900) ** 2 + ((ys - 190) / 900) ** 2), .35, 1.3)
    hair_m = np.zeros((h, w), np.float32)
    cv2.ellipse(hair_m, (cx, cy - 110), (280, 280), 0, 180, 360, 1.0, -1)
    hair_m = cv2.GaussianBlur(hair_m, (0, 0), 9)
    shirt_m = cv2.GaussianBlur((ys > 880).astype(np.float32), (0, 0), 14)
    base = (np.array([214, 169, 138], np.float32) * (1 - hair_m)[..., None] * (1 - shirt_m)[..., None]
            + np.array([58, 42, 36], np.float32) * hair_m[..., None]
            + np.array([44, 58, 78], np.float32) * shirt_m[..., None] * (1 - hair_m)[..., None])
    rgb = np.clip(base * key[..., None] + rng.normal(0, 3.4, (h, w, 3)), 0, 255)
    return rgb.astype(np.float32), alpha


def make_backdrops() -> dict[str, np.ndarray]:
    rng = np.random.default_rng(11)
    bh, bw = 1600, 1400
    out = {}

    out["solid"] = np.clip(np.full((bh, bw, 3), 0, np.float32)
                           + np.array([31, 95, 107], np.float32)
                           + rng.normal(0, 0.6, (bh, bw, 3)), 0, 255).astype(np.float32)

    g = np.repeat(np.linspace(0.45, 1.25, bh, dtype=np.float32)[:, None], bw, axis=1)
    out["gradient"] = np.clip(np.array([70, 82, 96], np.float32) * g[..., None], 0, 255).astype(np.float32)

    t = np.zeros((bh, bw), np.float32)
    for octv, amp in [(2, 1.0), (6, .55), (18, .3), (48, .16)]:
        t += amp * cv2.resize(rng.normal(0, 1, (octv, octv)).astype(np.float32), (bw, bh),
                              interpolation=cv2.INTER_CUBIC)
    t = (t - t.mean()) / t.std()
    weave = .35 * np.sin(np.mgrid[0:bh, 0:bw][1] * .9) + .35 * np.sin(np.mgrid[0:bh, 0:bw][0] * 1.1)
    out["texture"] = np.clip(np.array([118, 106, 92], np.float32)
                             * (1 + .30 * t + .07 * weave)[..., None], 0, 255).astype(np.float32)

    ph = np.zeros((bh, bw, 3), np.float32)
    ph[:, :] = np.array([96, 92, 86])
    ph[int(bh * .72):, :] = np.array([74, 62, 50])
    cv2.rectangle(ph, (int(bw * .06), int(bh * .12)), (int(bw * .40), int(bh * .62)), (222, 231, 240), -1)
    for i in range(6):
        x = int(bw * .06 + i * (bw * .34 / 5))
        cv2.line(ph, (x, int(bh * .12)), (x, int(bh * .62)), (120, 118, 112), 7)
    cv2.rectangle(ph, (int(bw * .60), int(bh * .18)), (int(bw * .95), int(bh * .70)), (58, 44, 34), -1)
    for i in range(9):
        x = int(bw * .62 + i * (bw * .33 / 9))
        cv2.rectangle(ph, (x, int(bh * .22)), (x + int(bw * .026), int(bh * .44)),
                      tuple(int(v) for v in rng.integers(40, 190, 3)), -1)
    out["photo"] = np.clip(ph + rng.normal(0, 4.0, ph.shape), 0, 255).astype(np.float32)
    return out


# ─── tests ──────────────────────────────────────────────────────────
def test_classifier(bds: dict[str, np.ndarray]) -> None:
    print("\nclassifier")
    for name, bd in bds.items():
        cls, _ = propic.classify_backdrop(bd)
        check(f"{name} classifies as {name}", cls == name, f"got {cls}")

    # The two cases a naive edge-density classifier gets wrong.
    blurred = cv2.GaussianBlur(bds["photo"], (0, 0), 22)
    cls, m = propic.classify_backdrop(blurred)
    check("already-blurred photo is still photo", cls == "photo",
          f"got {cls}, edge_density={m['edge_density']:.3f}")

    gray = cv2.cvtColor(cv2.cvtColor(bds["photo"].astype(np.uint8), cv2.COLOR_RGB2GRAY),
                        cv2.COLOR_GRAY2RGB).astype(np.float32)
    cls, m = propic.classify_backdrop(cv2.GaussianBlur(gray, (0, 0), 20))
    check("blurred grayscale scene is still photo", cls == "photo",
          f"got {cls}, chroma_std={m['chroma_std']:.2f}")


def test_defringe(rgb: np.ndarray, alpha: np.ndarray) -> None:
    print("\ndefringe")
    h, w = alpha.shape

    for label, bg in [
        ("uniform background", np.broadcast_to(np.array([70, 180, 90], np.float32), (h, w, 3))),
        ("two-tone background", None),
    ]:
        if bg is None:
            bg = np.zeros((h, w, 3), np.float32)
            bg[:, :w // 2] = np.array([70, 180, 90])
            bg[:, w // 2:] = np.array([210, 120, 40])
        contam = np.where((alpha > 0.99)[..., None], rgb,
                          rgb * alpha[..., None] + bg * (1 - alpha[..., None]))
        wisp = (alpha > 0.15) & (alpha < 0.6)
        before = float(np.abs(contam[wisp] - rgb[wisp]).mean())
        fixed, a_out = propic.defringe(contam, alpha, 1.5)
        after = float(np.abs(fixed[wisp] - rgb[wisp]).mean())
        check(f"{label}: edge error drops >80%", after < before * 0.2,
              f"{before:.1f} -> {after:.1f}")
        kept = float(a_out[wisp].sum() / max(alpha[wisp].sum(), 1e-6))
        check(f"{label}: wisp alpha preserved >95%", kept > 0.95, f"kept {kept:.1%}")

    # A cut that zeroed its background must fall back, not blow the edges out.
    zeroed = np.where((alpha > 0.02)[..., None], rgb, 0.0)
    fixed, _ = propic.defringe(zeroed, alpha, 1.5)
    check("zeroed background falls back safely",
          np.isfinite(fixed).all() and fixed.max() <= 255.0 and fixed.min() >= 0.0)


def test_fit_backdrop(bds: dict[str, np.ndarray]) -> None:
    print("\nfit_backdrop")
    pan = cv2.resize(bds["photo"], (4000, 300), interpolation=cv2.INTER_AREA)
    strip = cv2.resize(bds["photo"], (1, 1600), interpolation=cv2.INTER_AREA)
    for label, src in [("panorama 4000x300", pan), ("degenerate 1x1600", strip)]:
        fitted = propic.fit_backdrop(src, 900, 1125)
        check(f"{label} fits without exploding", fitted.shape[:2] == (1125, 900),
              f"got {fitted.shape[:2]}")


def test_scale_invariance(rgb: np.ndarray, alpha: np.ndarray, bd: np.ndarray) -> None:
    """A recipe must produce the same LOOK at any output size.

    This is what the @1000px reference exists for. Render small and large,
    downsample the large one, and the two should agree closely — if a radius
    were in absolute pixels they would not.
    """
    print("\nscale invariance")
    small_w, big_w = 400, 1200
    outs = []
    for w in (small_w, big_w):
        h = int(w * 1.25)
        r, a = propic.frame_subject(rgb, alpha, w, h, "headshot")
        b = propic.fit_backdrop(bd, w, h)
        outs.append(propic.composite(r, a, b, propic.CLASS_RECIPES["photo"]))
    big_down = cv2.resize(outs[1], (small_w, int(small_w * 1.25)), interpolation=cv2.INTER_AREA)
    diff = float(np.abs(big_down.astype(np.float32) - outs[0].astype(np.float32)).mean())
    check("3x scale change keeps the same look", diff < 9.0, f"mean abs diff {diff:.2f}")


def test_framing(rgb: np.ndarray, alpha: np.ndarray) -> None:
    print("\nframing")
    for mode, (hr, fl) in propic.FRAMING.items():
        r, a = propic.frame_subject(rgb, alpha, 800, 1000, mode)
        bb = propic.alpha_bbox(a)
        check(f"{mode}: canvas is exact", r.shape[:2] == (1000, 800))
        if bb:
            top_frac = bb[1] / 1000
            check(f"{mode}: headroom within 2% of {hr}", abs(top_frac - hr) < 0.02,
                  f"got {top_frac:.3f}")

    # An off-center subject should still be centered on the HEAD, not the bbox.
    shifted = np.roll(alpha, 220, axis=1)
    rgb_s = np.roll(rgb, 220, axis=1)
    _, a = propic.frame_subject(rgb_s, shifted, 800, 1000, "headshot")
    bb = propic.alpha_bbox(a)
    if bb:
        band = a[bb[1]:bb[1] + (bb[3] - bb[1]) // 4, :]
        cw = band.sum(axis=0)
        head_cx = float((np.arange(cw.size) * cw).sum() / max(cw.sum(), 1e-6))
        check("off-center subject re-centers on the head", abs(head_cx - 400) < 12,
              f"head center at {head_cx:.0f}, want 400")


def test_presets() -> None:
    print("\npresets")
    for name in propic.PRESETS:
        bd = propic.make_preset_backdrop(name, 400, 500)
        check(f"{name} generates in range", bd.shape == (500, 400, 3)
              and bd.min() >= 0 and bd.max() <= 255)
    bd = propic.make_preset_backdrop("teal", 400, 500)
    # Hot spot above center must actually be brighter than the bottom corner.
    check("radial falloff has a hot spot above center",
          bd[190, 200].mean() > bd[490, 10].mean() * 1.15,
          f"center {bd[190, 200].mean():.0f} vs corner {bd[490, 10].mean():.0f}")
    check("arbitrary hex works", propic.make_preset_backdrop("#1F5F6B", 100, 100).shape == (100, 100, 3))


def test_cli(rgb: np.ndarray, alpha: np.ndarray, bd: np.ndarray) -> None:
    print("\ncli")
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        Image.fromarray(np.dstack([rgb, alpha * 255]).astype(np.uint8), "RGBA").save(d / "cut.png")
        Image.fromarray(bd.astype(np.uint8)).save(d / "bd.png")

        rc = propic.main([str(d / "cut.png"), "--cut", str(d / "cut.png"),
                          "--backdrop", str(d / "bd.png"), "-o", str(d / "o.png"), "--width", "500"])
        check("backdrop render exits 0", rc == 0)
        check("backdrop render writes output", (d / "o.png").exists())

        rc = propic.main([str(d / "cut.png"), "--cut", str(d / "cut.png"),
                          "--preset", "slate", "-o", str(d / "p.png"), "--width", "500"])
        check("preset render exits 0", rc == 0)

        rc = propic.main([str(d / "cut.png"), "--cut", str(d / "cut.png"),
                          "--backdrop", str(d / "bd.png"), "--contact-sheet", str(d / "s.png"),
                          "--width", "500"])
        check("contact sheet exits 0", rc == 0)
        check("contact sheet writes output", (d / "s.png").exists())

        rc = propic.main([str(d / "cut.png"), "--cut", str(d / "cut.png"),
                          "--backdrop", str(d / "bd.png"), "--variant", "deep-blur",
                          "-o", str(d / "v.png"), "--width", "500"])
        check("named variant exits 0", rc == 0)

        rc = propic.main([str(d / "cut.png"), "--cut", str(d / "cut.png"),
                          "--backdrop", str(d / "bd.png"), "--variant", "nope",
                          "-o", str(d / "x.png"), "--width", "500"])
        check("unknown variant exits nonzero", rc != 0)

        rc = propic.main([str(d / "cut.png"), "--cut", str(d / "cut.png"),
                          "--preset", "teal", "--blur", "9", "--shadow", "0",
                          "-o", str(d / "ov.png"), "--width", "500"])
        check("treatment overrides exit 0", rc == 0)


def main() -> int:
    print("propic self-test")
    rgb, alpha = make_subject()
    bds = make_backdrops()

    test_classifier(bds)
    test_defringe(rgb, alpha)
    test_fit_backdrop(bds)
    test_scale_invariance(rgb, alpha, bds["photo"])
    test_framing(rgb, alpha)
    test_presets()
    test_cli(rgb, alpha, bds["photo"])

    print(f"\n{'ALL PASS' if not FAILURES else str(len(FAILURES)) + ' FAILED: ' + ', '.join(FAILURES)}")
    return 0 if not FAILURES else 1


if __name__ == "__main__":
    sys.exit(main())
