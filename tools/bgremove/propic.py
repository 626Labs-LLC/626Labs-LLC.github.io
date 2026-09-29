#!/usr/bin/env python3
"""propic — composite a cut subject onto a backdrop that reads as *behind* them.

bgremove.py gets the subject out of its original background. This gets it
*into* a new one. Those are different problems: a clean cutout pasted on a
backdrop still looks pasted, because the eye reads four things that a naive
paste gets wrong —

  edge color    Semi-transparent edge pixels still carry the OLD background's
                color. That's the halo. Fixed by solving the compositing
                equation backwards against a locally-estimated background —
                which works because `ai` and `grabcut` cuts leave the
                original pixels in RGB and only write a new alpha. Measured
                on a two-tone fixture: edge error 42.1 -> 3.7, with every
                hair strand kept.
  focus         A real backdrop behind a person is shot at the same aperture,
                so it's softer than they are. Fixed by depth-of-field blur,
                optionally graduated (more toward the top, which is further).
  white balance A subject lit at 5600K on a backdrop shot at 3200K never
                resolves. Fixed by nudging the backdrop's LAB chroma bias
                toward the subject's — *chroma only*, never the L mean, or
                the backdrop turns into skin.
  contact       Nothing anchors a floating subject. Fixed by a soft contact
                shadow and a light wrap: the backdrop's own color bleeding
                onto the subject's rim, which is what a real lens does.

Backdrops fall into four classes, and each wants a different recipe. propic
measures the backdrop and picks one, the same way bgremove's `auto` measures
corner disagreement and picks a mode:

  solid     One flat color. Std dev of color is near zero.
            -> no blur, radial vignette, light wrap, contact shadow, grain.
  gradient  Luminance is essentially a linear ramp (plane fit residual low).
            -> as solid, plus a touch of dim so the subject separates.
  texture   One material: chroma spread is low and luminance is unimodal.
            Fabric, paper, a pattern, a wash.
            -> mild blur, slight desaturate so it stops competing.
  photo     A scene: many hues, or many distinct brightnesses. A room, a
            street, a bookshelf — including one already shot wide open, which
            edge detection alone would mistake for fabric.
            -> real DoF blur, harmonize, strong light wrap, grain.

Six studio presets cover the standard corporate headshot without a second
image: teal, slate, white, charcoal, warm-gray, navy, sage. Each is generated
as a radial studio falloff, hot spot placed slightly above center where a
real backdrop light would land.

Not sure which treatment you want? `--contact-sheet` renders six labeled
variants as one grid PNG in a single pass. Pick the one that looks right and
re-run with `--variant <name>` for the full-resolution render.

Examples:
  propic me.jpg --preset teal                        # one-liner headshot
  propic me.jpg --backdrop office.jpg -v             # classify + auto recipe
  propic me.jpg --backdrop office.jpg --contact-sheet
  propic me.jpg --backdrop office.jpg --variant deep-blur -o final.png
  propic me.jpg --preset slate --aspect 1:1 --framing bust
  propic cut.png --cut cut.png --preset white        # already have a cutout
  propic ./team/ --preset slate --aspect 4:5         # batch a whole folder
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
BGREMOVE = HERE / "bgremove.py"

# All blur radii, band widths and offsets below are expressed against a
# 1000px reference long-edge, then scaled to the real output. Without this a
# recipe tuned on a 900px preview falls apart at 3000px.
REFERENCE_LONG_EDGE = 1000.0


# ─── studio presets ─────────────────────────────────────────────────
# (base RGB hex, falloff style). Hot spot sits at 38% height — where a real
# backdrop light lands, above the head rather than behind it.
PRESETS: dict[str, tuple[str, str]] = {
    "teal": ("#1F5F6B", "radial"),
    "slate": ("#3A4A5A", "radial"),
    "white": ("#F2F3F5", "radial"),
    "charcoal": ("#2B2E33", "radial"),
    "warm-gray": ("#6B6259", "radial"),
    "navy": ("#1E2D45", "radial"),
    "sage": ("#5A6B5D", "radial"),
}


# ─── recipe ─────────────────────────────────────────────────────────
@dataclass
class Recipe:
    """One complete set of compositing treatments.

    Every field is either a 0..1 strength or a @1000px-reference radius.
    `None` is never used — a treatment that shouldn't run is 0.0, so recipes
    stay comparable field-by-field and a contact-sheet label can print the
    diff against `auto` without special-casing.
    """

    name: str = "auto"
    # backdrop
    blur: float = 0.0             # DoF radius, px @1000 ref
    blur_gradient: float = 0.0    # 0 = uniform; 1 = top blurred ~2.5x the bottom
    desaturate: float = 0.0       # 0..1
    dim: float = 0.0              # 0..1, darken so the subject separates
    harmonize: float = 0.0        # 0..1, chroma bias toward the subject's light
    vignette: float = 0.0         # 0..1 radial falloff
    # subject edge
    defringe: float = 1.0         # px @1000 ref of edge color repair + alpha shrink
    light_wrap: float = 0.0       # 0..1 strength
    wrap_width: float = 6.0       # px @1000 ref of the rim band
    # grounding
    shadow: float = 0.0           # 0..1 opacity
    shadow_blur: float = 70.0     # px @1000 ref
    shadow_dx: float = 18.0       # px @1000 ref
    shadow_dy: float = 24.0       # px @1000 ref
    # match
    grain: float = 0.0            # multiplier on the subject's measured grain
    rationale: str = ""

    def summary(self) -> str:
        """Short human-readable param line for contact-sheet labels."""
        bits = []
        if self.blur:
            g = f"/{self.blur_gradient:.1f}" if self.blur_gradient else ""
            bits.append(f"blur {self.blur:.0f}{g}")
        if self.harmonize:
            bits.append(f"harm {self.harmonize:.2f}")
        if self.light_wrap:
            bits.append(f"wrap {self.light_wrap:.2f}")
        if self.shadow:
            bits.append(f"shadow {self.shadow:.2f}")
        if self.vignette:
            bits.append(f"vig {self.vignette:.2f}")
        if self.desaturate:
            bits.append(f"desat {self.desaturate:.2f}")
        if self.dim:
            bits.append(f"dim {self.dim:.2f}")
        if self.grain:
            bits.append(f"grain {self.grain:.1f}")
        return "  ".join(bits) or "no treatment"


# Base recipe per backdrop class. These are the numbers the whole tool turns
# on, so they carry their reasoning inline.
CLASS_RECIPES: dict[str, Recipe] = {
    "solid": Recipe(
        name="auto",
        blur=0.0,              # nothing to defocus
        vignette=0.35,         # a flat fill reads as paper without falloff
        defringe=1.2,
        light_wrap=0.18,       # subtle — a solid bg still throws color on the rim
        wrap_width=5.0,
        shadow=0.18,
        shadow_blur=70.0,
        grain=1.0,             # smooth fill next to a noisy subject reads as CGI
        rationale="Flat fill: no defocus needed, so the work is falloff, rim color and grain.",
    ),
    "gradient": Recipe(
        name="auto",
        blur=2.0,              # kills banding in an 8-bit ramp as a side effect
        vignette=0.22,         # the ramp is already doing some of this
        dim=0.05,
        defringe=1.2,
        light_wrap=0.20,
        wrap_width=5.0,
        shadow=0.18,
        shadow_blur=72.0,
        grain=1.0,
        rationale="Luminance ramp: light blur also kills 8-bit banding; ramp supplies some falloff already.",
    ),
    "texture": Recipe(
        name="auto",
        blur=6.0,              # enough to sit back, not enough to lose the material
        blur_gradient=0.3,
        desaturate=0.18,       # a busy texture competes with a face
        dim=0.10,
        harmonize=0.35,
        vignette=0.28,
        defringe=1.3,
        light_wrap=0.28,
        wrap_width=7.0,
        shadow=0.17,
        shadow_blur=75.0,
        grain=0.6,             # texture carries its own high-frequency detail
        rationale="Homogeneous texture: sit it back and desaturate so it stops competing with the face.",
    ),
    "photo": Recipe(
        name="auto",
        blur=16.0,             # a real 85mm at f/2 behind a subject is *very* soft
        blur_gradient=0.6,     # the top of a room is further away than the bottom
        desaturate=0.08,
        dim=0.12,
        harmonize=0.6,         # different shoot, different white balance
        vignette=0.30,
        defringe=1.5,
        light_wrap=0.40,       # biggest single realism win on a photo backdrop
        wrap_width=9.0,
        shadow=0.15,
        shadow_blur=80.0,
        grain=1.0,
        rationale="Real scene: heavy DoF, harmonize the white balance, wrap the rim. The full kit.",
    ),
    "flat": Recipe(
        name="flat",
        defringe=1.0,
        rationale="Straight composite — scale, defringe, paste. No treatment.",
    ),
}


# ─── backdrop classification ────────────────────────────────────────
def classify_backdrop(rgb: np.ndarray, verbose: bool = False) -> tuple[str, dict]:
    """Measure a backdrop and name its class: solid / gradient / texture / photo.

    Five measurements, taken on a downsample so cost is independent of input
    size:

      color_std     Mean per-channel std dev. Near zero = one flat color.
      plane_resid   Fit luminance to a plane (a*x + b*y + c) and take the
                    residual std. Low = the image IS a linear ramp.
      edge_density  Canny pixel fraction. How much hard detail there is.
      chroma_std    Mean std dev of LAB a/b. This is the real texture-vs-photo
                    discriminator. Edge density looks like the obvious choice
                    and it isn't: an ALREADY-BLURRED photo backdrop — which is
                    common, people hand you a shot taken at f/1.8 — measures
                    0.000 edge density, identical to fabric. Chroma survives
                    blur, because blurring mixes hues without collapsing their
                    spread. On the fixtures: fabric 1.6, blurred room 5.4.
      lum_peaks     Peaks in a smoothed luminance histogram. Covers the case
                    chroma misses: a grayscale or near-monochrome scene has no
                    chroma spread but is still multimodal (distinct objects at
                    distinct brightnesses), where a mottled material is not.

    A scene trips EITHER chroma spread or multimodality, so a backdrop only
    lands in `texture` when both say single-material.

    Returns (class_name, measurements).
    """
    h, w = rgb.shape[:2]
    scale = min(1.0, 512.0 / max(h, w))
    if scale < 1.0:
        small = cv2.resize(rgb.astype(np.uint8), (max(1, int(w * scale)), max(1, int(h * scale))),
                           interpolation=cv2.INTER_AREA).astype(np.float32)
    else:
        small = rgb.astype(np.float32)
    sh, sw = small.shape[:2]

    color_std = float(np.mean(small.reshape(-1, 3).std(axis=0)))

    lum = small @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    ys, xs = np.mgrid[0:sh, 0:sw].astype(np.float32)
    A = np.stack([xs.ravel(), ys.ravel(), np.ones(sh * sw, dtype=np.float32)], axis=1)
    coef, *_ = np.linalg.lstsq(A, lum.ravel(), rcond=None)
    plane_resid = float(np.std(lum.ravel() - A @ coef))

    gray = cv2.cvtColor(small.astype(np.uint8), cv2.COLOR_RGB2GRAY)
    v = float(np.median(gray))
    edges = cv2.Canny(gray, int(max(0, 0.67 * v)), int(min(255, 1.33 * v)), L2gradient=True)
    edge_density = float((edges > 0).mean())

    lab = cv2.cvtColor((small / 255.0).astype(np.float32), cv2.COLOR_RGB2LAB)
    chroma_std = float((lab[..., 1].std() + lab[..., 2].std()) / 2.0)

    hist, _ = np.histogram(lab[..., 0], bins=64, range=(0.0, 100.0))
    hist = cv2.GaussianBlur(hist.astype(np.float32).reshape(-1, 1), (1, 7), 0).ravel()
    floor = 0.08 * float(hist.max()) if hist.max() > 0 else 0.0
    lum_peaks = int(sum(
        1 for i in range(1, 63)
        if hist[i] > hist[i - 1] and hist[i] >= hist[i + 1] and hist[i] > floor
    ))

    m = {
        "color_std": color_std,
        "plane_resid": plane_resid,
        "edge_density": edge_density,
        "chroma_std": chroma_std,
        "lum_peaks": lum_peaks,
    }

    single_material = chroma_std < 3.5 and lum_peaks < 3

    if color_std < 7.0:
        cls = "solid"
    elif plane_resid < 5.0 and chroma_std < 3.5:
        cls = "gradient"
    elif single_material and edge_density < 0.10:
        cls = "texture"
    else:
        cls = "photo"

    if verbose:
        print(
            f"classify: color_std={color_std:.1f} plane_resid={plane_resid:.1f} "
            f"edge_density={edge_density:.3f} chroma_std={chroma_std:.2f} "
            f"lum_peaks={lum_peaks} -> {cls}",
            file=sys.stderr,
        )
    return cls, m


# ─── preset backdrop generation ─────────────────────────────────────
def _hex_to_rgb(s: str) -> np.ndarray:
    s = s.strip().lstrip("#")
    if "," in s:
        parts = [float(x) for x in s.split(",")]
        if len(parts) != 3:
            raise ValueError(f"color expects 3 components, got {s!r}")
        return np.array(parts, dtype=np.float32)
    if len(s) != 6:
        raise ValueError(f"don't know how to parse color {s!r}")
    return np.array([int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)], dtype=np.float32)


def make_preset_backdrop(name_or_color: str, w: int, h: int, style: str | None = None) -> np.ndarray:
    """Generate a studio backdrop: base color with a radial hot spot above center.

    A real seamless-paper or muslin backdrop is never flat — there's a light
    on it, and the falloff is what makes the subject sit in front of rather
    than on top of it. Hot spot at 38% height, gain 1.22 at the center down
    to 0.60 at the far corner, on a gamma-correct curve so the falloff reads
    smooth rather than plasticky.
    """
    if name_or_color in PRESETS:
        base_hex, preset_style = PRESETS[name_or_color]
        base = _hex_to_rgb(base_hex)
        style = style or preset_style
    else:
        base = _hex_to_rgb(name_or_color)
        style = style or "radial"

    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = (xs / max(1, w - 1) - 0.5) * 2.0
    ny = (ys / max(1, h - 1) - 0.38) * 2.0

    if style == "flat":
        gain = np.ones((h, w), dtype=np.float32)
    elif style == "linear":
        gain = 1.18 - 0.42 * (ys / max(1, h - 1))
    else:  # radial
        # Slight horizontal squash: backdrop lights spread wider than tall.
        d = np.sqrt((nx * 0.82) ** 2 + ny ** 2)
        gain = 1.22 - 0.62 * np.clip(d / 1.45, 0.0, 1.0) ** 1.35

    # Gamma-correct the multiply: scale linear light, not sRGB values.
    lin = (base / 255.0) ** 2.2
    out_lin = lin[None, None, :] * gain[..., None]
    out = np.clip(out_lin, 0.0, 4.0) ** (1 / 2.2) * 255.0
    return np.clip(out, 0, 255).astype(np.float32)


# ─── edge repair (defringe) ─────────────────────────────────────────
def _push_out(rgb: np.ndarray, core: np.ndarray, iters: int) -> np.ndarray:
    """Flood interior color outward into the soft alpha band.

    A masked box-dilate: at each step, every not-yet-filled pixel adjacent to
    filled pixels takes their mean. This is what removes the halo — the edge
    band gets the subject's OWN color instead of whatever the old background
    left mixed into it.
    """
    filled = rgb.astype(np.float32).copy()
    m = core.astype(np.float32).copy()
    k = np.ones((3, 3), dtype=np.float32)
    for _ in range(max(0, iters)):
        num = cv2.filter2D(filled * m[..., None], -1, k, borderType=cv2.BORDER_REPLICATE)
        den = cv2.filter2D(m, -1, k, borderType=cv2.BORDER_REPLICATE)
        reachable = den > 0.0
        mean = num / np.maximum(den, 1e-6)[..., None]
        unfilled = m <= 0.0
        take = unfilled & reachable
        filled = np.where(take[..., None], mean, filled)
        m = np.where(take, 1.0, m)
    return filled


def _unmix(rgb: np.ndarray, alpha: np.ndarray, sigma: float,
           verbose: bool = False) -> np.ndarray | None:
    """Solve the compositing equation backwards to recover true edge color.

    Every soft edge pixel is a mixture: C_obs = a*C_fg + (1-a)*C_bg. Knowing
    C_bg makes C_fg exact: C_fg = (C_obs - (1-a)*C_bg) / a.

    The trick is knowing C_bg after the background has supposedly been
    removed — and the answer is that it usually hasn't been. rembg and
    grabcut write an alpha channel and LEAVE the original pixels in RGB, so
    everything under alpha=0 is still the original background, sitting there
    to be sampled. We estimate C_bg per-pixel rather than globally, by
    blurring the background-masked image and normalizing by the blurred mask
    — a local average of "what was behind this, nearby". Local matters: a
    subject shot against a window and a wall has two background colors, and a
    single global sample splits the difference and is wrong for both.

    Returns None when the transparent region carries no usable signal — some
    tools zero out RGB where alpha is 0, and unmixing against a black field
    that was never really there would blow the edges out. The caller falls
    back to color flooding in that case.

    On `sigma`: it sets how local "local" is, and it has a real optimum
    rather than a more-is-better curve. Measured against ground truth on a
    two-tone background fixture (green one side, orange the other), mean
    absolute edge error was 42.1 untreated, bottomed at 3.7 around sigma 9,
    and rose again to 8.2 by sigma 30. Too small and the estimate cannot
    reach strands surrounded by open air; too large and it averages across
    the boundary between two backgrounds and corrects both sides toward mud.
    The caller passes px * 6, which sits near the bottom of that curve at
    ordinary defringe settings. Don't "simplify" this to a global sample.
    """
    bg_mask = (alpha < 0.05).astype(np.float32)
    if bg_mask.sum() < 256:
        return None

    bg_px = rgb[bg_mask > 0]
    # A zeroed-out background is near-black AND near-constant. A real one that
    # happens to be dark still has texture, so require both to bail.
    if float(bg_px.mean()) < 6.0 and float(bg_px.std()) < 4.0:
        if verbose:
            print("defringe: transparent region is zeroed — unmix unavailable", file=sys.stderr)
        return None

    num = cv2.GaussianBlur(rgb * bg_mask[..., None], (0, 0), sigma)
    den = cv2.GaussianBlur(bg_mask, (0, 0), sigma)
    support = den > 0.001
    local_bg = np.where(support[..., None], num / np.maximum(den, 1e-6)[..., None], rgb)

    a = np.clip(alpha, 0.0, 1.0)[..., None]
    safe_a = np.where(a > 0.04, a, 1.0)
    fg = (rgb - (1.0 - a) * local_bg) / safe_a

    # Only trust the solve in the soft band with local background support.
    # Deep inside (a>0.95) the observed color IS the true color, and at very
    # low alpha the division amplifies noise faster than it removes spill.
    trust = (support & (alpha > 0.04) & (alpha < 0.99))[..., None]
    return np.where(trust, np.clip(fg, 0, 255), rgb)


def defringe(rgb: np.ndarray, alpha: np.ndarray, px: float,
             verbose: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """Remove the halo, then crush only the faintest alpha.

    The halo is a COLOR problem, not an extent problem, and that distinction
    drives this whole function.

    Two repair strategies, because one alone does not cover the cases:

      unmix     Solves C_fg exactly from the local background color. Reaches
                ANY semi-transparent pixel, however far from the subject's
                body — which is what thin flyaway hair needs. Preferred
                whenever the cut left the original background in RGB, which
                the `ai` and `grabcut` paths both do.
      push-out  Floods opaque interior color outward. Needs no knowledge of
                the old background, but only reaches a few pixels past the
                core, so it cannot fix a strand 80px out into open air. The
                fallback for cuts that zeroed their background.

    The first version of this shipped push-out alone and measured a green
    cast of +56 on wisp pixels against +63 for a naive paste — almost no
    improvement, because the strands were simply out of reach. It LOOKED
    fixed only because a too-aggressive alpha shrink was deleting the
    contaminated strands rather than repairing them.

    Which brings us to alpha. The obvious shrink is a global remap,
    `(alpha - k) / (1 - k)`. Do not. It subtracts from EVERY semi-transparent
    pixel, so at k=0.45 a hair strand sitting at alpha 0.4 vanishes outright.
    For a headshot tool, flyaway hair is precisely what you are trying to
    keep. Instead this applies a `toe`: quadratic falloff BELOW a low
    threshold only. Alpha 0.40 stays 0.40; alpha 0.05 drops to ~0.02. The
    faint outer wash — no detail, just a veil over the backdrop — clears, and
    every real strand survives.

    `px` is already scaled to the output size by the caller.
    """
    if px <= 0:
        return rgb, alpha

    rgb_out = _unmix(rgb, alpha, sigma=max(4.0, px * 6.0), verbose=verbose)
    if rgb_out is None:
        core = (alpha > 0.88).astype(np.float32)
        if core.sum() == 0:
            rgb_out = rgb
        else:
            repaired = _push_out(rgb, core, int(max(1, round(px * 2))))
            band = np.clip((0.95 - alpha) / 0.95, 0.0, 1.0)[..., None]
            rgb_out = rgb * (1.0 - band) + repaired * band

    toe = float(np.clip(px * 0.08, 0.0, 0.20))
    if toe > 1e-3:
        alpha_out = np.where(alpha < toe, alpha * (alpha / toe), alpha)
    else:
        alpha_out = alpha
    return rgb_out, np.clip(alpha_out, 0.0, 1.0)


# ─── backdrop treatments ────────────────────────────────────────────
def dof_blur(bd: np.ndarray, radius: float, gradient: float) -> np.ndarray:
    """Gaussian defocus, optionally stronger toward the top of the frame.

    `gradient` blends a weak and a strong blur along a vertical ramp. The top
    of a room is further from the lens than the bottom, so uniform blur on a
    scene backdrop reads slightly wrong even when the amount is right.
    """
    if radius <= 0.3:
        return bd
    near = cv2.GaussianBlur(bd, (0, 0), radius)
    if gradient <= 0.01:
        return near
    far = cv2.GaussianBlur(bd, (0, 0), radius * (1.0 + 1.5 * gradient))
    h = bd.shape[0]
    ramp = np.linspace(1.0, 0.0, h, dtype=np.float32)[:, None, None]  # 1 at top
    return far * ramp + near * (1.0 - ramp)


def harmonize(bd: np.ndarray, subj_rgb: np.ndarray, alpha: np.ndarray, strength: float) -> np.ndarray:
    """Nudge the backdrop's color cast toward the subject's lighting.

    CHROMA ONLY, and clamped. The naive version of this is a full LAB
    mean/std transfer, which is wrong here: matching the L mean makes the
    backdrop as bright as a face, and matching the a/b means fully turns a
    teal backdrop skin-colored. What actually needs to agree between a
    subject and a backdrop is the *white balance* — the a/b bias — and
    roughly the contrast. So: shift a/b partway, capped at 6 LAB units, and
    pull L std (not L mean) toward the subject's.
    """
    if strength <= 0.01:
        return bd
    mask = alpha > 0.8
    if mask.sum() < 64:
        return bd

    bd_lab = cv2.cvtColor((bd / 255.0).astype(np.float32), cv2.COLOR_RGB2LAB)
    sj_lab = cv2.cvtColor((subj_rgb / 255.0).astype(np.float32), cv2.COLOR_RGB2LAB)

    sj_px = sj_lab[mask]
    sj_a, sj_b = float(sj_px[:, 1].mean()), float(sj_px[:, 2].mean())
    sj_lstd = float(sj_px[:, 0].std())

    bd_a, bd_b = float(bd_lab[..., 1].mean()), float(bd_lab[..., 2].mean())
    bd_lstd = float(bd_lab[..., 0].std())

    cap = 6.0
    da = np.clip((sj_a - bd_a) * strength * 0.5, -cap, cap)
    db = np.clip((sj_b - bd_b) * strength * 0.5, -cap, cap)

    out = bd_lab.copy()
    out[..., 1] += da
    out[..., 2] += db
    if bd_lstd > 1.0:
        # Contrast toward the subject's, but only a third of the way and never
        # more than ±25% — a backdrop is allowed to be flatter than a face.
        ratio = np.clip(1.0 + (sj_lstd / bd_lstd - 1.0) * strength * 0.33, 0.75, 1.25)
        lmean = float(out[..., 0].mean())
        out[..., 0] = np.clip((out[..., 0] - lmean) * ratio + lmean, 0.0, 100.0)

    rgb = cv2.cvtColor(out, cv2.COLOR_LAB2RGB) * 255.0
    return np.clip(rgb, 0, 255)


def desaturate(bd: np.ndarray, amount: float) -> np.ndarray:
    if amount <= 0.01:
        return bd
    lum = (bd @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32))[..., None]
    return bd * (1.0 - amount) + lum * amount


def dim(bd: np.ndarray, amount: float) -> np.ndarray:
    if amount <= 0.01:
        return bd
    # Dim in linear light so shadows don't crush.
    lin = (bd / 255.0) ** 2.2 * (1.0 - amount)
    return np.clip(lin ** (1 / 2.2) * 255.0, 0, 255)


def vignette(bd: np.ndarray, strength: float, cx: float = 0.5, cy: float = 0.42) -> np.ndarray:
    """Radial falloff centered a little above middle, behind where a head sits."""
    if strength <= 0.01:
        return bd
    h, w = bd.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = (xs / max(1, w - 1) - cx) * 2.0
    ny = (ys / max(1, h - 1) - cy) * 2.0
    d = np.sqrt((nx * 0.85) ** 2 + ny ** 2) / 1.45
    gain = 1.0 - strength * np.clip(d, 0.0, 1.0) ** 1.6
    lin = (bd / 255.0) ** 2.2 * gain[..., None]
    return np.clip(lin ** (1 / 2.2) * 255.0, 0, 255)


def contact_shadow(bd: np.ndarray, alpha: np.ndarray, opacity: float,
                   blur: float, dx: float, dy: float) -> np.ndarray:
    """Soft shadow cast by the subject onto the backdrop.

    Offset down and to one side, blurred HARD. The point isn't a realistic
    cast shadow — it's grounding. Without it the subject floats and the viewer
    can't say why the image looks wrong.

    The defaults are deliberately soft and far (blur 70-80 @1000 ref, offset
    18-20 across and 24-28 down, opacity 0.15-0.18). A tight, dark shadow
    hugging the silhouette is the obvious first guess and it looks like a
    sticker drop-shadow — the eye reads a second copy of the subject rather
    than a shadow. Directional offset matters too: a symmetric shadow peeking
    out both sides has no light source.
    """
    if opacity <= 0.01:
        return bd
    h, w = bd.shape[:2]
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    shifted = cv2.warpAffine(alpha, M, (w, h), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    if blur > 0.3:
        shifted = cv2.GaussianBlur(shifted, (0, 0), blur)
    shade = np.clip(shifted * opacity, 0.0, 1.0)[..., None]
    lin = (bd / 255.0) ** 2.2 * (1.0 - shade)
    return np.clip(lin ** (1 / 2.2) * 255.0, 0, 255)


def light_wrap(subj_rgb: np.ndarray, alpha: np.ndarray, bd: np.ndarray,
               strength: float, width: float) -> np.ndarray:
    """Bleed backdrop light onto the subject's rim.

    The single most convincing treatment in the set. A real lens photographing
    a person against a backdrop lets that backdrop's light spill around their
    edge — hair especially. Without it, even a perfect cutout on a perfect
    backdrop reads as two layers.

    The mask: `alpha * (1 - blur(alpha))`. Deep inside the subject, blurred
    alpha is 1 so the mask is 0. Just inside the edge, alpha is 1 but blurred
    alpha is ~0.5, so the mask peaks. Outside, alpha is 0. A band that hugs
    the inside of the silhouette, exactly where spill lands.
    """
    if strength <= 0.01 or width <= 0.3:
        return subj_rgb
    soft = cv2.GaussianBlur(alpha, (0, 0), width)
    band = np.clip(alpha * (1.0 - soft), 0.0, 1.0)
    peak = float(band.max())
    if peak < 1e-4:
        return subj_rgb
    band = (band / peak) * strength

    spill = cv2.GaussianBlur(bd, (0, 0), max(1.0, width * 2.0)) / 255.0
    base = np.clip(subj_rgb / 255.0, 0.0, 1.0)
    # Screen, so a bright backdrop lifts the rim without clipping it.
    screened = 1.0 - (1.0 - base) * (1.0 - spill)
    out = base + (screened - base) * band[..., None]
    return np.clip(out * 255.0, 0, 255)


def measure_grain(subj_rgb: np.ndarray, alpha: np.ndarray) -> float:
    """Robust high-frequency noise sigma of the subject, in 0..255 units.

    Median-absolute-deviation of (image - blur(image)) over opaque pixels.
    MAD rather than std because real edges — an eyelash, a shirt seam — are
    high-frequency too and would inflate a plain std into visible noise.
    """
    mask = alpha > 0.9
    if mask.sum() < 256:
        return 0.0
    gray = cv2.cvtColor(subj_rgb.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
    hp = gray - cv2.GaussianBlur(gray, (0, 0), 1.6)
    vals = np.abs(hp[mask])
    return float(np.median(vals) * 1.4826)


def add_grain(img: np.ndarray, sigma: float, where: np.ndarray, seed: int = 626) -> np.ndarray:
    """Add matched luminance noise, only where `where` says to.

    A generated or heavily-blurred backdrop is perfectly smooth. Next to a
    camera-noise subject that smoothness is the tell — it reads as CGI. Match
    the subject's measured sigma and the two surfaces belong to one photo.
    """
    if sigma <= 0.15:
        return img
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, sigma, img.shape[:2]).astype(np.float32)
    return np.clip(img + (noise * where)[..., None], 0, 255)


# ─── framing ────────────────────────────────────────────────────────
FRAMING = {
    # (headroom fraction, subject height as fraction of frame)
    "headshot": (0.07, 0.93),
    "bust": (0.10, 0.84),
    "full": (0.05, 0.95),
}


def alpha_bbox(alpha: np.ndarray, thresh: float = 0.08) -> tuple[int, int, int, int] | None:
    """Tight bbox of the subject as (x0, y0, x1, y1), exclusive on the far edge."""
    m = alpha > thresh
    rows = np.where(m.any(axis=1))[0]
    cols = np.where(m.any(axis=0))[0]
    if rows.size == 0 or cols.size == 0:
        return None
    return int(cols[0]), int(rows[0]), int(cols[-1]) + 1, int(rows[-1]) + 1


def frame_subject(rgb: np.ndarray, alpha: np.ndarray, out_w: int, out_h: int,
                  mode: str, headroom: float | None = None, fill: float | None = None,
                  verbose: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """Scale and place the subject on an out_w x out_h transparent canvas.

    Horizontal centering uses the centroid of the subject's TOP QUARTER, not
    the bbox center. For a headshot that's the head, and a head-centered crop
    survives an off-center pose or a shoulder turned toward camera — bbox
    centering visibly drifts the face off-axis on both.
    """
    if mode == "none":
        return rgb, alpha

    bb = alpha_bbox(alpha)
    if bb is None:
        return rgb, alpha
    x0, y0, x1, y1 = bb
    sub_h = max(1, y1 - y0)

    hr, fl = FRAMING.get(mode, FRAMING["headshot"])
    hr = hr if headroom is None else headroom
    fl = fl if fill is None else fill

    scale = (out_h * fl) / sub_h
    new_w = max(1, int(round(rgb.shape[1] * scale)))
    new_h = max(1, int(round(rgb.shape[0] * scale)))
    interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LANCZOS4
    rgb_s = cv2.resize(rgb.astype(np.float32), (new_w, new_h), interpolation=interp)
    alpha_s = cv2.resize(alpha.astype(np.float32), (new_w, new_h), interpolation=interp)
    alpha_s = np.clip(alpha_s, 0.0, 1.0)

    bb2 = alpha_bbox(alpha_s)
    if bb2 is None:
        return rgb_s, alpha_s
    sx0, sy0, sx1, sy1 = bb2

    # Head-level horizontal centroid.
    head_band = alpha_s[sy0:sy0 + max(1, (sy1 - sy0) // 4), :]
    col_w = head_band.sum(axis=0)
    if col_w.sum() > 1e-6:
        head_cx = float((np.arange(col_w.size) * col_w).sum() / col_w.sum())
    else:
        head_cx = (sx0 + sx1) / 2.0

    dst_top = out_h * hr
    off_y = int(round(dst_top - sy0))
    off_x = int(round(out_w / 2.0 - head_cx))

    canvas_rgb = np.zeros((out_h, out_w, 3), dtype=np.float32)
    canvas_a = np.zeros((out_h, out_w), dtype=np.float32)

    # Intersect source and destination rectangles once, rather than padding.
    sx_a, sx_b = max(0, -off_x), min(new_w, out_w - off_x)
    sy_a, sy_b = max(0, -off_y), min(new_h, out_h - off_y)
    if sx_b > sx_a and sy_b > sy_a:
        dx_a, dy_a = sx_a + off_x, sy_a + off_y
        canvas_rgb[dy_a:dy_a + (sy_b - sy_a), dx_a:dx_a + (sx_b - sx_a)] = rgb_s[sy_a:sy_b, sx_a:sx_b]
        canvas_a[dy_a:dy_a + (sy_b - sy_a), dx_a:dx_a + (sx_b - sx_a)] = alpha_s[sy_a:sy_b, sx_a:sx_b]

    if verbose:
        print(f"frame: mode={mode} scale={scale:.3f} headroom={hr:.2f} fill={fl:.2f} "
              f"offset=({off_x},{off_y})", file=sys.stderr)
    return canvas_rgb, canvas_a


def fit_backdrop(bd: np.ndarray, out_w: int, out_h: int,
                 focus: tuple[float, float] = (0.5, 0.5)) -> np.ndarray:
    """Cover-crop the backdrop to the canvas, biased toward a focal point.

    Crops the SOURCE to the target aspect first, then resizes once. The
    obvious order — scale up to cover, then slice — is a trap: a source with
    an extreme aspect ratio (a panorama, a 1px gradient strip) needs an
    enormous intermediate before the slice throws almost all of it away. A
    1x1600 source covering 900px wide materializes 900x1,440,000. Cropping
    first never allocates more than the source, and it's one resize instead
    of a resize plus a copy.
    """
    h, w = bd.shape[:2]
    target_ar = out_w / out_h

    # Largest rect inside the source that has the target aspect ratio.
    if w / h > target_ar:
        crop_h = h
        crop_w = max(1, int(round(h * target_ar)))
    else:
        crop_w = w
        crop_h = max(1, int(round(w / target_ar)))

    fx = int(round((w - crop_w) * float(np.clip(focus[0], 0.0, 1.0))))
    fy = int(round((h - crop_h) * float(np.clip(focus[1], 0.0, 1.0))))
    cropped = bd[fy:fy + crop_h, fx:fx + crop_w].astype(np.float32)

    interp = cv2.INTER_AREA if crop_w > out_w else cv2.INTER_LANCZOS4
    return cv2.resize(cropped, (out_w, out_h), interpolation=interp)


# ─── the composite ──────────────────────────────────────────────────
def composite(subj_rgb: np.ndarray, subj_alpha: np.ndarray, backdrop: np.ndarray,
              recipe: Recipe, verbose: bool = False) -> np.ndarray:
    """Apply a recipe and return an RGB uint8 image.

    Order matters and is not arbitrary:
      1. defringe      before anything reads the subject's edge color
      2. backdrop      blur -> desaturate -> dim -> harmonize -> vignette
                       (harmonize AFTER blur: measuring chroma on a blurred
                       backdrop is what the viewer will actually compare)
      3. shadow        onto the treated backdrop, before the subject lands
      4. light wrap    needs the final backdrop to spill the right color
      5. alpha blend   in linear light, or edges darken
      6. grain         last, so blur can't smooth away what we just added
    """
    h, w = backdrop.shape[:2]
    s = max(h, w) / REFERENCE_LONG_EDGE

    rgb, alpha = defringe(subj_rgb, subj_alpha, recipe.defringe * s, verbose=verbose)

    bd = dof_blur(backdrop, recipe.blur * s, recipe.blur_gradient)
    bd = desaturate(bd, recipe.desaturate)
    bd = dim(bd, recipe.dim)
    bd = harmonize(bd, rgb, alpha, recipe.harmonize)
    bd = vignette(bd, recipe.vignette)
    bd = contact_shadow(bd, alpha, recipe.shadow, recipe.shadow_blur * s,
                        recipe.shadow_dx * s, recipe.shadow_dy * s)

    fg = light_wrap(rgb, alpha, bd, recipe.light_wrap, recipe.wrap_width * s)

    # Blend in linear light. Compositing in sRGB darkens every soft edge —
    # the classic grey halo around hair that no amount of defringing fixes.
    a = alpha[..., None]
    fg_lin = np.clip(fg / 255.0, 0, 1) ** 2.2
    bd_lin = np.clip(bd / 255.0, 0, 1) ** 2.2
    out = np.clip(fg_lin * a + bd_lin * (1.0 - a), 0, 1) ** (1 / 2.2) * 255.0

    if recipe.grain > 0.01:
        sigma = measure_grain(rgb, alpha) * recipe.grain
        # Only where the backdrop shows — the subject brought its own noise.
        out = add_grain(out, sigma, 1.0 - alpha)
        if verbose:
            print(f"grain: subject sigma={sigma / max(recipe.grain, 1e-6):.2f} "
                  f"applied={sigma:.2f}", file=sys.stderr)

    return np.clip(out, 0, 255).astype(np.uint8)


# ─── variants ───────────────────────────────────────────────────────
def variant_set(base: Recipe, cls: str) -> list[Recipe]:
    """Six labeled recipes to eyeball: the auto pick plus five real alternatives.

    Each variant changes ONE axis that a person actually has an opinion about,
    so the contact sheet is a set of decisions rather than a random walk.
    """
    common = [replace(base, name="auto")]

    if cls in ("solid", "gradient"):
        return common + [
            replace(base, name="flat", vignette=0.0, shadow=0.0,
                    rationale="No falloff, no shadow. Clean and graphic — good for a grid of consistent staff photos."),
            replace(base, name="studio", vignette=0.55, shadow=0.26, shadow_blur=62.0,
                    rationale="Strong backdrop light and a deeper shadow. The classic lit-backdrop portrait."),
            replace(base, name="floating", shadow=0.0, vignette=0.42, light_wrap=base.light_wrap * 1.6,
                    rationale="No shadow, more rim spill. Reads cut-out-on-color rather than person-in-room."),
            replace(base, name="deep", dim=0.20, vignette=0.48, light_wrap=base.light_wrap * 1.4,
                    rationale="Darker backdrop, brighter rim. Most separation — good when hair and backdrop tone are close."),
            replace(base, name="clean", grain=0.0, vignette=0.25, shadow=0.14,
                    rationale="No grain. Sharper and more digital — right for slide decks, wrong next to a noisy photo."),
        ]

    return common + [
        replace(base, name="deep-blur", blur=base.blur * 2.0, blur_gradient=0.7, dim=base.dim + 0.06,
                rationale="Twice the defocus. Wider aperture look — backdrop becomes pure color and shape."),
        replace(base, name="crisp", blur=max(2.0, base.blur * 0.3), blur_gradient=0.15, desaturate=0.0,
                rationale="Backdrop stays readable. Use when the location IS the point — office, set, bookshelf."),
        replace(base, name="no-grade", harmonize=0.0, desaturate=0.0,
                rationale="No white-balance match. Honest if both were shot in the same light; jarring if not."),
        replace(base, name="soft-wrap", light_wrap=min(1.0, base.light_wrap * 1.8),
                wrap_width=base.wrap_width * 1.5,
                rationale="Heavy rim spill. Best on flyaway hair; can go milky on a hard-edged silhouette."),
        replace(base, name="pop", dim=base.dim + 0.14, vignette=min(1.0, base.vignette + 0.18),
                blur=base.blur * 1.4, desaturate=base.desaturate + 0.10,
                rationale="Backdrop pushed back hard on every axis. Maximum subject separation."),
    ]


def _label_strip(w: int, name: str, summary: str, note: str) -> np.ndarray:
    """Render a three-line caption strip under a thumbnail."""
    from PIL import ImageDraw, ImageFont

    pad, lh = 10, 15
    try:
        bold = ImageFont.truetype("DejaVuSans-Bold.ttf", 15)
        reg = ImageFont.truetype("DejaVuSans.ttf", 11)
        mono = ImageFont.truetype("DejaVuSansMono.ttf", 11)
    except OSError:
        bold = reg = mono = ImageFont.load_default()

    avail = w - 2 * pad

    def wrap(text: str, font, limit: int) -> list[str]:
        """Greedy wrap measured against the ACTUAL font, not a per-char guess.

        An estimated character width silently clips the parameter line —
        which is the one piece of a contact sheet you have to be able to read,
        since it's what you'd type to reproduce the variant.
        """
        lines, cur = [], ""
        for word in text.split():
            cand = f"{cur} {word}".strip()
            if font.getlength(cand) <= avail or not cur:
                cur = cand
            else:
                lines.append(cur)
                cur = word
            if len(lines) == limit:
                return lines
        if cur:
            lines.append(cur)
        return lines[:limit]

    sum_lines = wrap(summary, mono, 2)
    note_lines = wrap(note, reg, 3)

    h = pad + lh + 1 + lh * len(sum_lines) + lh * len(note_lines) + pad
    strip = Image.new("RGB", (w, h), (24, 26, 30))
    d = ImageDraw.Draw(strip)

    y = pad
    d.text((pad, y), name, font=bold, fill=(235, 238, 242))
    y += lh + 1
    for line in sum_lines:
        d.text((pad, y), line, font=mono, fill=(120, 190, 200))
        y += lh
    for line in note_lines:
        d.text((pad, y), line, font=reg, fill=(150, 156, 166))
        y += lh
    return np.array(strip)


def contact_sheet(subj_rgb: np.ndarray, subj_alpha: np.ndarray, backdrop: np.ndarray,
                  recipes: list[Recipe], out_path: Path, cls: str,
                  thumb_w: int = 440, cols: int = 3, verbose: bool = False) -> None:
    """Render every variant as a labeled grid so the choice is visual.

    Each thumbnail is composited at thumbnail resolution, not downscaled from
    full res. Because every radius in a Recipe is scaled against the
    reference long edge, the thumbnail shows the same *look* the full render
    will produce — which is the only thing that makes a contact sheet
    trustworthy enough to pick from.
    """
    from PIL import ImageDraw, ImageFont

    h, w = backdrop.shape[:2]
    tw = thumb_w
    th = max(1, int(round(h * tw / w)))
    bd_small = cv2.resize(backdrop, (tw, th), interpolation=cv2.INTER_AREA)
    rgb_small = cv2.resize(subj_rgb, (tw, th), interpolation=cv2.INTER_AREA)
    a_small = np.clip(cv2.resize(subj_alpha, (tw, th), interpolation=cv2.INTER_AREA), 0, 1)

    tiles = []
    for r in recipes:
        img = composite(rgb_small, a_small, bd_small, r)
        strip = _label_strip(tw, r.name, r.summary(), r.rationale)
        tiles.append(np.vstack([img, strip]))
        if verbose:
            print(f"sheet: rendered {r.name}", file=sys.stderr)

    tile_h = max(t.shape[0] for t in tiles)
    tiles = [
        np.vstack([t, np.full((tile_h - t.shape[0], tw, 3), 24, dtype=np.uint8)])
        if t.shape[0] < tile_h else t
        for t in tiles
    ]

    rows = (len(tiles) + cols - 1) // cols
    gap, margin, header = 14, 22, 62
    sheet_w = margin * 2 + cols * tw + (cols - 1) * gap
    sheet_h = header + margin + rows * tile_h + (rows - 1) * gap + margin
    sheet = np.full((sheet_h, sheet_w, 3), 16, dtype=np.uint8)

    for i, t in enumerate(tiles):
        r, c = divmod(i, cols)
        y = header + margin + r * (tile_h + gap)
        x = margin + c * (tw + gap)
        sheet[y:y + tile_h, x:x + tw] = t

    img = Image.fromarray(sheet)
    d = ImageDraw.Draw(img)
    try:
        bold = ImageFont.truetype("DejaVuSans-Bold.ttf", 19)
        reg = ImageFont.truetype("DejaVuSans.ttf", 12)
    except OSError:
        bold = reg = ImageFont.load_default()
    d.text((margin, 18), f"propic variants  ·  backdrop classified: {cls}",
           font=bold, fill=(235, 238, 242))
    d.text((margin, 42), "Pick one and re-run with  --variant <name>  for the full-resolution render.",
           font=reg, fill=(130, 136, 146))
    img.save(out_path, optimize=True)
    print(f"contact sheet: {out_path} ({len(recipes)} variants)", file=sys.stderr)


# ─── subject acquisition ────────────────────────────────────────────
def cut_subject(src: Path, mode: str, refine: bool, workdir: Path,
                verbose: bool = False) -> Path:
    """Hand off to bgremove.py for the cutout, then optionally refine edges.

    Two passes by default. `ai` (rembg/U2Net) finds the person reliably but
    leaves chunky hair; `matting --input-alpha` then refines THAT alpha with
    closed-form matting instead of re-seeding from grabcut. The second pass is
    where flyaway hair comes from, and it's the difference between a headshot
    that survives a 2x zoom and one that doesn't.
    """
    if not BGREMOVE.exists():
        raise RuntimeError(f"bgremove.py not found next to propic.py (looked in {HERE})")

    cut = workdir / f"{src.stem}-cut.png"
    cmd = [sys.executable, str(BGREMOVE), str(src), "-o", str(cut), "--mode", mode]
    if verbose:
        cmd.append("-v")
        print(f"cut: $ {' '.join(cmd)}", file=sys.stderr)
    rc = subprocess.run(cmd).returncode
    if rc != 0:
        raise RuntimeError(f"bgremove failed (exit {rc}) on {src.name}")

    if not refine:
        return cut

    refined = workdir / f"{src.stem}-refined.png"
    cmd = [sys.executable, str(BGREMOVE), str(src), "-o", str(refined),
           "--mode", "matting", "--input-alpha", str(cut)]
    if verbose:
        cmd.append("-v")
        print(f"refine: $ {' '.join(cmd)}", file=sys.stderr)
    rc = subprocess.run(cmd).returncode
    if rc != 0:
        # pymatting missing, or the solver gave up. The ai cut is still good.
        print("refine: matting pass failed; keeping the unrefined cut", file=sys.stderr)
        return cut
    return refined


def load_rgba(path: Path) -> tuple[np.ndarray, np.ndarray]:
    with Image.open(path) as im:
        arr = np.array(im.convert("RGBA")).astype(np.float32)
    return arr[..., :3], arr[..., 3] / 255.0


def parse_aspect(s: str) -> float:
    """'4:5' / '4/5' / '0.8' -> width/height."""
    s = s.strip().replace("/", ":")
    if ":" in s:
        a, b = s.split(":", 1)
        return float(a) / float(b)
    return float(s)


def parse_focus(s: str) -> tuple[float, float]:
    parts = [float(p) for p in s.replace(":", ",").split(",")]
    if len(parts) != 2:
        raise ValueError(f"--backdrop-focus expects x,y fractions, got {s!r}")
    return parts[0], parts[1]


# ─── orchestration ──────────────────────────────────────────────────
def build(
    subject: Path,
    output: Path,
    backdrop_path: Path | None = None,
    preset: str | None = None,
    cut_path: Path | None = None,
    cut_mode: str = "ai",
    refine: bool = True,
    keep_cut: Path | None = None,
    recipe_name: str = "auto",
    variant: str | None = None,
    sheet_path: Path | None = None,
    aspect: str = "4:5",
    width: int = 1600,
    framing: str = "headshot",
    headroom: float | None = None,
    fill: float | None = None,
    focus: tuple[float, float] = (0.5, 0.5),
    overrides: dict | None = None,
    verbose: bool = False,
) -> None:
    ar = parse_aspect(aspect)
    out_w = int(width)
    out_h = max(1, int(round(out_w / ar)))

    # 1. Subject.
    with tempfile.TemporaryDirectory(prefix="propic-") as tmp:
        tmpdir = Path(tmp)
        if cut_path is not None:
            src_cut = cut_path
            if verbose:
                print(f"cut: using provided {src_cut}", file=sys.stderr)
        else:
            src_cut = cut_subject(subject, cut_mode, refine, tmpdir, verbose=verbose)
            if keep_cut is not None:
                keep_cut.parent.mkdir(parents=True, exist_ok=True)
                keep_cut.write_bytes(src_cut.read_bytes())
                if verbose:
                    print(f"cut: saved to {keep_cut}", file=sys.stderr)
        subj_rgb, subj_alpha = load_rgba(src_cut)

    if subj_alpha.max() <= 0.02:
        raise RuntimeError(
            f"{src_cut.name} has no opaque pixels — the cut removed everything. "
            "Try --cut-mode grabcut, or pass a known-good cutout with --cut."
        )

    # 2. Frame the subject onto the output canvas.
    subj_rgb, subj_alpha = frame_subject(
        subj_rgb, subj_alpha, out_w, out_h, framing, headroom, fill, verbose=verbose
    )
    if subj_rgb.shape[:2] != (out_h, out_w):
        # framing="none": the canvas is whatever the cut was.
        out_h, out_w = subj_rgb.shape[:2]

    # 3. Backdrop.
    if backdrop_path is not None:
        with Image.open(backdrop_path) as im:
            bd_full = np.array(im.convert("RGB")).astype(np.float32)
        cls, _ = classify_backdrop(bd_full, verbose=verbose)
        backdrop = fit_backdrop(bd_full, out_w, out_h, focus)
    elif preset is not None:
        backdrop = make_preset_backdrop(preset, out_w, out_h)
        cls = "gradient" if preset in PRESETS else "solid"
        if verbose:
            print(f"backdrop: preset {preset} -> class {cls}", file=sys.stderr)
    else:
        raise ValueError("need either --backdrop or --preset")

    # 4. Recipe.
    base = CLASS_RECIPES[cls if recipe_name == "auto" else recipe_name]
    variants = variant_set(base, cls)

    if sheet_path is not None:
        contact_sheet(subj_rgb, subj_alpha, backdrop, variants, sheet_path, cls, verbose=verbose)
        return

    if variant is not None:
        match = next((r for r in variants if r.name == variant), None)
        if match is None:
            names = ", ".join(r.name for r in variants)
            raise ValueError(f"no variant {variant!r} for a {cls} backdrop. Available: {names}")
        recipe = match
    else:
        recipe = base

    if overrides:
        recipe = replace(recipe, **overrides, name=f"{recipe.name}+custom")

    if verbose:
        print(f"recipe: {recipe.name} [{recipe.summary()}]", file=sys.stderr)
        print(f"        {recipe.rationale}", file=sys.stderr)

    # 5. Composite and save.
    out = composite(subj_rgb, subj_alpha, backdrop, recipe, verbose=verbose)
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out, "RGB").save(output, optimize=True, quality=95)
    print(f"propic: {output} ({out_w}x{out_h}, {cls}/{recipe.name})", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="propic",
        description="Composite a cut subject onto a backdrop that reads as behind them.",
    )
    ap.add_argument("input", type=Path, nargs="?", help="Subject photo, or a directory for batch")
    ap.add_argument("-o", "--output", type=Path, help="Output image (default: <input>-propic.png)")
    ap.add_argument("--list-presets", action="store_true", help="Print the studio presets and exit")

    g = ap.add_argument_group("backdrop")
    g.add_argument("--backdrop", type=Path, help="Backdrop image — the second photo")
    g.add_argument("--preset", help=f"Studio preset or a #RRGGBB color. Presets: {', '.join(PRESETS)}")
    g.add_argument("--backdrop-focus", default="0.5,0.5",
                   help="Focal point for the cover-crop, as x,y fractions (default 0.5,0.5)")

    g = ap.add_argument_group("cutout")
    g.add_argument("--cut", type=Path, help="Use this already-cut RGBA PNG; skip bgremove entirely")
    g.add_argument("--cut-mode", default="ai",
                   choices=["auto", "color-key", "contour", "grabcut", "matting", "ai"],
                   help="bgremove mode for the first pass (default: ai — best on people)")
    g.add_argument("--no-refine", dest="refine", action="store_false",
                   help="Skip the matting pass that refines hair edges")
    g.add_argument("--keep-cut", type=Path, help="Also save the intermediate cutout here")

    g = ap.add_argument_group("treatment")
    g.add_argument("--recipe", default="auto",
                   choices=["auto", "solid", "gradient", "texture", "photo", "flat"],
                   help="Force a recipe class instead of classifying the backdrop")
    g.add_argument("--variant", help="Render a named variant from the contact sheet")
    g.add_argument("--contact-sheet", nargs="?", const="", dest="sheet", metavar="PATH",
                   help="Render all variants as one labeled grid instead of a final image")

    g = ap.add_argument_group("framing")
    g.add_argument("--aspect", default="4:5", help="Output aspect ratio (default 4:5)")
    g.add_argument("--width", type=int, default=1600, help="Output width in px (default 1600)")
    g.add_argument("--framing", default="headshot", choices=["headshot", "bust", "full", "none"],
                   help="How to crop around the subject (default headshot)")
    g.add_argument("--headroom", type=float, help="Override: space above the head, as a frame fraction")
    g.add_argument("--fill", type=float, help="Override: subject height as a frame fraction")

    g = ap.add_argument_group("treatment overrides (any float overrides the recipe)")
    for flag, dest in [
        ("--blur", "blur"), ("--blur-gradient", "blur_gradient"), ("--desaturate", "desaturate"),
        ("--dim", "dim"), ("--harmonize", "harmonize"), ("--vignette", "vignette"),
        ("--defringe", "defringe"), ("--light-wrap", "light_wrap"), ("--wrap-width", "wrap_width"),
        ("--shadow", "shadow"), ("--shadow-blur", "shadow_blur"), ("--grain", "grain"),
    ]:
        g.add_argument(flag, type=float, dest=f"ov_{dest}", default=None)

    ap.add_argument("--ext", default=".png,.jpg,.jpeg,.webp,.bmp", help="Batch only: extensions to include")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    if args.list_presets:
        print("propic studio presets:")
        for name, (hexcode, style) in PRESETS.items():
            print(f"  {name:<11} {hexcode}  {style}")
        print("\nAny #RRGGBB also works: --preset '#1F5F6B'")
        return 0

    if args.input is None:
        ap.error("input is required (or use --list-presets)")
    if not args.input.exists():
        print(f"input not found: {args.input}", file=sys.stderr)
        return 2
    if args.backdrop is None and args.preset is None:
        ap.error("need either --backdrop <image> or --preset <name>")
    if args.backdrop is not None and not args.backdrop.exists():
        print(f"backdrop not found: {args.backdrop}", file=sys.stderr)
        return 2

    overrides = {k[3:]: v for k, v in vars(args).items() if k.startswith("ov_") and v is not None}

    common = dict(
        backdrop_path=args.backdrop,
        preset=args.preset,
        cut_mode=args.cut_mode,
        refine=args.refine,
        recipe_name=args.recipe,
        variant=args.variant,
        aspect=args.aspect,
        width=args.width,
        framing=args.framing,
        headroom=args.headroom,
        fill=args.fill,
        focus=parse_focus(args.backdrop_focus),
        overrides=overrides,
        verbose=args.verbose,
    )

    if args.input.is_dir():
        exts = tuple(e.strip().lower() for e in args.ext.split(",") if e.strip())
        images = sorted(p for p in args.input.iterdir() if p.is_file() and p.suffix.lower() in exts)
        if not images:
            print(f"no images in {args.input} matching {exts}", file=sys.stderr)
            return 0
        out_dir = args.output or args.input.with_name(f"{args.input.name}-propic")
        out_dir.mkdir(parents=True, exist_ok=True)
        ok = fail = 0
        for img in images:
            try:
                build(
                    subject=img,
                    output=out_dir / f"{img.stem}-propic.png",
                    cut_path=None,
                    keep_cut=None,
                    sheet_path=(out_dir / f"{img.stem}-variants.png") if args.sheet is not None else None,
                    **common,
                )
                ok += 1
            except Exception as ex:
                print(f"  {img.name}: FAILED ({ex})", file=sys.stderr)
                fail += 1
        print(f"propic batch done: {ok} ok, {fail} failed", file=sys.stderr)
        return 0 if fail == 0 else 1

    output = args.output or args.input.with_name(f"{args.input.stem}-propic.png")
    sheet_path = None
    if args.sheet is not None:
        sheet_path = Path(args.sheet) if args.sheet else args.input.with_name(
            f"{args.input.stem}-variants.png")

    try:
        build(
            subject=args.input,
            output=output,
            cut_path=args.cut,
            keep_cut=args.keep_cut,
            sheet_path=sheet_path,
            **common,
        )
    except Exception as ex:
        print(f"propic: {ex}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
