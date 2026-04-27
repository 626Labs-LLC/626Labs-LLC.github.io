#!/usr/bin/env python3
"""bgremove — classical-CV background removal for logos and graphics.

No neural net, no model download. Three modes:

  color-key   Distance-from-bg matte + alpha unmix. Best on solid bgs.
  contour     Canny edge detect + largest outer contour. Best on
              high-contrast subjects against busy bgs.
  auto        Picks color-key when corners agree (uniform bg),
              otherwise contour.

Examples:
  bgremove logo.png                          # auto, write logo-cut.png
  bgremove banner.jpg -o banner.png --mode color-key --bg-color "#192e44"
  bgremove photo.jpg --mode contour --feather 3 -v
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

# cv2 is imported lazily — only contour mode needs it, keeps cold start fast.


# ─── helpers ────────────────────────────────────────────────────────
def parse_color(s: str) -> np.ndarray:
    """Parse '#RRGGBB' / 'RRGGBB' / 'r,g,b' / 'auto' into [R,G,B]."""
    if s == "auto":
        return None
    s = s.strip().lstrip("#")
    if "," in s:
        parts = [int(x) for x in s.split(",")]
        if len(parts) != 3:
            raise ValueError(f"--bg-color expects 3 components, got {s}")
        return np.array(parts, dtype=np.float64)
    if len(s) == 6:
        return np.array([int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)], dtype=np.float64)
    raise ValueError(f"--bg-color: don't know how to parse {s!r}")


def sample_corner_bg(rgb: np.ndarray, patch: int = 12) -> np.ndarray:
    """Median RGB across the 4 corner patches."""
    h, w = rgb.shape[:2]
    p = max(2, min(patch, h // 8, w // 8))
    corners = np.concatenate([
        rgb[:p, :p].reshape(-1, 3),
        rgb[:p, -p:].reshape(-1, 3),
        rgb[-p:, :p].reshape(-1, 3),
        rgb[-p:, -p:].reshape(-1, 3),
    ], axis=0)
    return np.median(corners, axis=0).astype(np.float64)


def corners_agree(rgb: np.ndarray, patch: int = 12, threshold: float = 18.0) -> bool:
    """True if all 4 corner medians are within `threshold` of each other.

    Uniform bg -> trivially true. Mixed bg (gradient, vignette, photo) -> false.
    """
    h, w = rgb.shape[:2]
    p = max(2, min(patch, h // 8, w // 8))
    corner_medians = np.array([
        np.median(rgb[:p, :p].reshape(-1, 3), axis=0),
        np.median(rgb[:p, -p:].reshape(-1, 3), axis=0),
        np.median(rgb[-p:, :p].reshape(-1, 3), axis=0),
        np.median(rgb[-p:, -p:].reshape(-1, 3), axis=0),
    ])
    # Max distance between any pair.
    dists = []
    for i in range(4):
        for j in range(i + 1, 4):
            dists.append(np.linalg.norm(corner_medians[i] - corner_medians[j]))
    return max(dists) < threshold


# ─── color-key mode ─────────────────────────────────────────────────
def mode_color_key(
    rgb: np.ndarray,
    bg: np.ndarray,
    lo: float = 6.0,
    hi: float = 150.0,
    unmix: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    """Soft color-key with optional alpha unmix.

    Returns (rgb_out, alpha) — both float64 in 0..255 range so the caller
    can compose them into RGBA + downcast to uint8.
    """
    dist = np.sqrt(((rgb - bg) ** 2).sum(axis=-1))
    alpha = np.clip((dist - lo) / (hi - lo), 0, 1)
    if unmix:
        # C_obs = α·C_fg + (1-α)·C_bg ⇒ C_fg = (C_obs - (1-α)·C_bg) / α
        safe_alpha = np.where(alpha > 1e-3, alpha, 1.0)[..., None]
        fg = (rgb - (1 - alpha[..., None]) * bg) / safe_alpha
        rgb_out = np.clip(fg, 0, 255)
    else:
        rgb_out = rgb
    return rgb_out, alpha * 255.0


# ─── contour mode ───────────────────────────────────────────────────
def mode_contour(
    rgb: np.ndarray,
    feather: int = 0,
    min_area_frac: float = 0.005,
) -> tuple[np.ndarray, np.ndarray]:
    """Canny + largest outer contour -> filled alpha mask.

    Doesn't preserve interior holes (e.g., negative space inside a donut).
    Use this when the subject's silhouette is what you want.

    `feather` blurs the alpha edge for a softer cut. 0 = hard edge.
    """
    import cv2  # lazy

    gray = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2GRAY)
    # Auto Canny thresholds via median (a la Adrian Rosebrock's heuristic).
    v = float(np.median(gray))
    sigma = 0.33
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    edges = cv2.Canny(gray, lower, upper, L2gradient=True)

    # Close small gaps so contours are continuous.
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Outer contours only — interior holes are intentionally collapsed.
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        # Nothing detected; return fully-opaque (no-op cut).
        h, w = rgb.shape[:2]
        return rgb, np.full((h, w), 255.0)

    h, w = rgb.shape[:2]
    min_area = h * w * min_area_frac
    big = [c for c in contours if cv2.contourArea(c) >= min_area]
    if not big:
        # Fall back to single largest if nothing meets the floor.
        big = [max(contours, key=cv2.contourArea)]

    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.drawContours(mask, big, -1, 255, thickness=cv2.FILLED)

    if feather > 0:
        # Gaussian blur on the mask. Kernel must be odd.
        k = max(3, feather * 2 + 1)
        mask = cv2.GaussianBlur(mask, (k, k), 0)

    return rgb, mask.astype(np.float64)


# ─── orchestration ──────────────────────────────────────────────────
def pick_mode(rgb: np.ndarray, verbose: bool = False) -> str:
    if corners_agree(rgb, threshold=18.0):
        if verbose:
            print("auto: corners agree -> color-key", file=sys.stderr)
        return "color-key"
    if verbose:
        print("auto: corners disagree -> contour", file=sys.stderr)
    return "contour"


def run(
    input_path: Path,
    output_path: Path,
    mode: str = "auto",
    bg_color: np.ndarray | None = None,
    unmix: bool = True,
    lo: float = 6.0,
    hi: float = 150.0,
    feather: int = 0,
    verbose: bool = False,
) -> None:
    img = Image.open(input_path).convert("RGBA")
    arr = np.array(img).astype(np.float64)
    rgb = arr[..., :3]
    src_alpha = arr[..., 3]

    if mode == "auto":
        mode = pick_mode(rgb, verbose=verbose)

    if mode == "color-key":
        if bg_color is None:
            bg_color = sample_corner_bg(rgb)
            if verbose:
                print(f"color-key: bg auto-detected = {tuple(int(x) for x in bg_color)}", file=sys.stderr)
        rgb_out, alpha = mode_color_key(rgb, bg_color, lo=lo, hi=hi, unmix=unmix)
    elif mode == "contour":
        rgb_out, alpha = mode_contour(rgb, feather=feather)
    else:
        raise ValueError(f"unknown mode: {mode!r}")

    # Multiply with any pre-existing alpha so we don't bring back hidden bits.
    final_alpha = np.minimum(src_alpha, alpha).clip(0, 255)
    out = np.zeros_like(arr, dtype=np.uint8)
    out[..., :3] = rgb_out.clip(0, 255).astype(np.uint8)
    out[..., 3] = final_alpha.astype(np.uint8)

    Image.fromarray(out, "RGBA").save(output_path, optimize=True)
    if verbose:
        # Quick alpha distribution summary so the user can sanity-check.
        a = final_alpha.flatten()
        opaque = (a > 250).sum() / a.size
        transparent = (a < 5).sum() / a.size
        print(
            f"saved {output_path}  ({out.shape[1]}x{out.shape[0]}) "
            f"opaque={opaque:.1%} transparent={transparent:.1%}",
            file=sys.stderr,
        )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="bgremove",
        description="Classical-CV background remover. No neural net.",
    )
    ap.add_argument("input", type=Path, help="Input image (PNG / JPG / etc.)")
    ap.add_argument("-o", "--output", type=Path, help="Output PNG (default: <input>-cut.png)")
    ap.add_argument(
        "--mode",
        choices=["auto", "color-key", "contour"],
        default="auto",
        help="Which algorithm to run (default: auto)",
    )
    ap.add_argument(
        "--bg-color",
        default="auto",
        help="For color-key: '#RRGGBB' / 'r,g,b' / 'auto' (sample corners)",
    )
    ap.add_argument("--no-unmix", dest="unmix", action="store_false", help="Disable RGB unmixing in color-key mode")
    ap.add_argument("--lo", type=float, default=6.0, help="color-key: bg distance below this -> fully transparent")
    ap.add_argument("--hi", type=float, default=150.0, help="color-key: bg distance above this -> fully opaque")
    ap.add_argument("--feather", type=int, default=0, help="contour: Gaussian blur radius for the alpha edge")
    ap.add_argument("-v", "--verbose", action="store_true", help="Print picked mode + alpha summary to stderr")
    args = ap.parse_args(argv)

    if not args.input.exists():
        print(f"input not found: {args.input}", file=sys.stderr)
        return 2

    output = args.output or args.input.with_name(f"{args.input.stem}-cut.png")
    bg = parse_color(args.bg_color)

    try:
        run(
            input_path=args.input,
            output_path=output,
            mode=args.mode,
            bg_color=bg,
            unmix=args.unmix,
            lo=args.lo,
            hi=args.hi,
            feather=args.feather,
            verbose=args.verbose,
        )
    except Exception as ex:
        print(f"bgremove: {ex}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
