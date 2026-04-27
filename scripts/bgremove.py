#!/usr/bin/env python3
"""bgremove — classical-CV background removal for logos and graphics.

Six modes, five classical + one AI fallback:

  color-key   Distance-from-bg matte + alpha unmix. Best on solid bgs.
  contour     Canny edge detect + largest outer contour. Best on
              high-contrast subjects against busy bgs.
  grabcut     cv2.grabCut iterative segmentation. Takes a bbox
              (auto: 5% inset). Best on photos / mixed bgs.
  matting     Closed-form alpha matting via pymatting. Refines a
              coarse mask from another mode for sub-pixel-accurate
              edges (good for hair, fur, anti-aliasing). Slower.
              Requires `pip install pymatting`.
  ai          rembg + U2Net (lazy import). Best on portraits and
              anything classical CV struggles with. Requires
              `pip install rembg[cpu]`.
  auto        Picks color-key when corners agree (uniform bg),
              grabcut when they're close-ish (subtle gradient),
              contour otherwise. Never picks `matting` or `ai`
              automatically — heavy deps, explicit opt-in only.

Batch mode: pass a directory as input. Outputs land in <input>-cut/.

Examples:
  bgremove logo.png                          # auto, write logo-cut.png
  bgremove banner.jpg -o out.png --mode color-key --bg-color "#192e44"
  bgremove photo.jpg --mode contour --feather 3 -v
  bgremove photo.jpg --mode grabcut --rect 50,80,400,500 --iters 5
  bgremove portrait.jpg --mode matting
  bgremove portrait.jpg --mode ai
  bgremove ./photos/                         # batch, writes ./photos-cut/
  bgremove ./photos/ -o ./out/ --mode auto -v
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


def parse_rect(s: str, w: int, h: int) -> tuple[int, int, int, int] | None:
    """Parse 'auto' / 'x,y,w,h' into a cv2 grabCut rect, clamped to image bounds.

    Returns None when caller wants 'auto' so mode_grabcut can compute its
    own default (5% inset on each edge).
    """
    if s == "auto":
        return None
    parts = [int(p.strip()) for p in s.split(",")]
    if len(parts) != 4:
        raise ValueError(f"--rect expects 4 ints (x,y,w,h), got {s!r}")
    x, y, rw, rh = parts
    x = max(0, min(x, w - 2))
    y = max(0, min(y, h - 2))
    rw = max(2, min(rw, w - x))
    rh = max(2, min(rh, h - y))
    return (x, y, rw, rh)


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


def corner_disagreement(rgb: np.ndarray, patch: int = 12) -> float:
    """Max RGB distance between any pair of the 4 corner medians.

    0 = solid uniform bg. ~30+ = subtle gradient/vignette. 60+ = photo-like.
    """
    h, w = rgb.shape[:2]
    p = max(2, min(patch, h // 8, w // 8))
    corner_medians = np.array([
        np.median(rgb[:p, :p].reshape(-1, 3), axis=0),
        np.median(rgb[:p, -p:].reshape(-1, 3), axis=0),
        np.median(rgb[-p:, :p].reshape(-1, 3), axis=0),
        np.median(rgb[-p:, -p:].reshape(-1, 3), axis=0),
    ])
    dists = []
    for i in range(4):
        for j in range(i + 1, 4):
            dists.append(float(np.linalg.norm(corner_medians[i] - corner_medians[j])))
    return max(dists)


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


# ─── grabcut mode ───────────────────────────────────────────────────
def mode_grabcut(
    rgb: np.ndarray,
    rect: tuple[int, int, int, int] | None = None,
    iters: int = 5,
    feather: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """cv2.grabCut iterative segmentation, initialized from a bbox.

    grabCut models fg/bg as Gaussian mixtures and runs graph-cut
    iterations to refine the assignment. No training data, no neural
    net — just the algorithm.

    `rect` is (x, y, width, height). When None, uses a 5% inset on
    each edge — works when the subject is roughly centered.
    """
    import cv2  # lazy

    img_bgr = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2BGR)
    h, w = img_bgr.shape[:2]
    if rect is None:
        m_x = max(2, int(w * 0.05))
        m_y = max(2, int(h * 0.05))
        rect = (m_x, m_y, w - 2 * m_x, h - 2 * m_y)

    mask = np.zeros((h, w), dtype=np.uint8)
    bgd = np.zeros((1, 65), dtype=np.float64)
    fgd = np.zeros((1, 65), dtype=np.float64)
    cv2.grabCut(img_bgr, mask, rect, bgd, fgd, iters, cv2.GC_INIT_WITH_RECT)

    # 4-class mask: 0=sure_bg, 1=sure_fg, 2=prob_bg, 3=prob_fg.
    alpha_mask = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)

    if feather > 0:
        k = max(3, feather * 2 + 1)
        alpha_mask = cv2.GaussianBlur(alpha_mask, (k, k), 0)

    return rgb, alpha_mask.astype(np.float64)


# ─── matting mode (refine an existing alpha mask via pymatting) ────
MATTING_MAX_DIM = 1000  # downsample so the long edge is ≤ this before solving


def mode_matting(
    rgb: np.ndarray,
    seed_mode: str = "grabcut",
    seed_kwargs: dict | None = None,
    input_alpha: np.ndarray | None = None,
    erode_radius: int | None = None,
    dilate_radius: int | None = None,
    max_dim: int = MATTING_MAX_DIM,
    verbose: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """Closed-form alpha matting via pymatting, with downsample+fallback armor.

    Matting needs a *trimap* — a 3-class mask of definitely-fg / definitely-bg /
    unknown. We generate it from another mode's coarse binary output: erode
    → sure_fg, dilate-complement → sure_bg, the band in between → unknown.
    Then `estimate_alpha_cf` solves a closed-form Laplacian over the unknown
    band to recover sub-pixel-accurate alpha.

    Two armor layers around the solve:
      1. **Downsample.** pymatting's preconditioned conjugate gradient solver
         scales poorly with image size and frequently fails Cholesky on >1500px
         inputs ('insufficient positive-definiteness'). We downsample to
         max_dim on the long edge before solving, then bicubic-upsample the
         alpha back. Alpha is a smooth signal, so the upsample loss is small.
         4-10× faster, dodges most numerical failures.
      2. **Catch + fallback.** If the solver still blows up, we fall back to
         the seed alpha with a warning instead of crashing the whole batch.

    Use this when contour or grabcut gives you the right *region* but the
    edges look chunky and you want soft, hair-friendly cutouts.
    """
    try:
        from pymatting import estimate_alpha_cf
    except ImportError as ex:
        raise RuntimeError(
            "--mode matting requires pymatting. Install: pip install pymatting "
            f"(import error: {ex})"
        )
    import cv2

    if input_alpha is not None:
        # Refining an existing cut (typically the previous attempt's output).
        # Skip the seed mode entirely — the provided alpha IS the seed.
        if input_alpha.shape[:2] != rgb.shape[:2]:
            import cv2 as _cv
            input_alpha = _cv.resize(
                input_alpha.astype(np.uint8),
                (rgb.shape[1], rgb.shape[0]),
                interpolation=_cv.INTER_NEAREST,
            ).astype(np.float64)
        alpha_seed = input_alpha
        if verbose:
            print("matting: seeding from provided alpha mask", file=sys.stderr)
    else:
        seed_kwargs = seed_kwargs or {}
        if seed_mode == "grabcut":
            _, alpha_seed = mode_grabcut(rgb, **seed_kwargs)
        elif seed_mode == "contour":
            _, alpha_seed = mode_contour(rgb, **seed_kwargs)
        elif seed_mode == "color-key":
            # Color-key already produces soft alpha — matting on top is rarely
            # useful, but allow it. The threshold below cleans up the trimap.
            _, alpha_seed = mode_color_key(rgb, **seed_kwargs)
        else:
            raise ValueError(f"matting seed_mode must be grabcut/contour/color-key, got {seed_mode!r}")

    # Scale erode/dilate radii to image size so small icons don't erode away.
    h, w = rgb.shape[:2]
    auto_radius = max(2, min(h, w) // 80)
    er = erode_radius if erode_radius is not None else auto_radius
    dr = dilate_radius if dilate_radius is not None else auto_radius

    # Convert seed to a binary mask, then erode/dilate to build the trimap.
    binary = (alpha_seed > 127).astype(np.uint8) * 255
    k_erode = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (er * 2 + 1, er * 2 + 1))
    k_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dr * 2 + 1, dr * 2 + 1))
    sure_fg = cv2.erode(binary, k_erode)
    dilated = cv2.dilate(binary, k_dilate)

    # If erosion wiped out all fg (subject too thin for the radius), fall back
    # to the binary itself as sure_fg — better than a meaningless trimap.
    if (sure_fg == 255).sum() == 0:
        sure_fg = binary

    # Trimap encoding for pymatting: 0.0 = bg, 0.5 = unknown, 1.0 = fg
    trimap = np.full(binary.shape, 0.5, dtype=np.float64)
    trimap[sure_fg == 255] = 1.0
    trimap[dilated == 0] = 0.0

    # ── Armor layer 1: downsample for the solve ──────────────────────
    long_edge = max(h, w)
    if long_edge > max_dim:
        scale = max_dim / long_edge
        new_w = int(round(w * scale))
        new_h = int(round(h * scale))
        rgb_small = cv2.resize(rgb.astype(np.uint8), (new_w, new_h), interpolation=cv2.INTER_AREA)
        # Trimap downsample: nearest preserves the 3-class structure (0/0.5/1).
        trimap_small = cv2.resize(trimap, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
        if verbose:
            print(f"matting: downsampled {w}x{h} -> {new_w}x{new_h} for solve", file=sys.stderr)
    else:
        rgb_small = rgb.astype(np.uint8)
        trimap_small = trimap

    # ── Armor layer 2: catch solver blowups, fall back to seed ───────
    rgb_norm = (rgb_small / 255.0).astype(np.float64)
    try:
        alpha_small = estimate_alpha_cf(rgb_norm, trimap_small)
    except Exception as ex:
        # Cholesky / preconditioner failures end up here. Fall back to the
        # seed mask — same image region, just chunkier edges than matting
        # would have given us. Better than crashing.
        msg = str(ex).splitlines()[0] if str(ex) else type(ex).__name__
        print(
            f"matting: solver failed ({msg}); falling back to {seed_mode} seed",
            file=sys.stderr,
        )
        return rgb, alpha_seed

    # Upsample alpha back to original resolution. Bicubic preserves smooth
    # alpha gradients without ringing on the way up.
    if (alpha_small.shape[1], alpha_small.shape[0]) != (w, h):
        alpha_full = cv2.resize(alpha_small, (w, h), interpolation=cv2.INTER_CUBIC)
        alpha_full = np.clip(alpha_full, 0.0, 1.0)
    else:
        alpha_full = alpha_small

    alpha_out = np.clip(alpha_full * 255.0, 0, 255)

    # Unmix the inferred bg out of the foreground (using ORIGINAL-resolution
    # rgb + upsampled alpha — recovers neon edges without resampling artifacts).
    bg_pixels = rgb[dilated == 0]
    if bg_pixels.size > 0:
        bg_color = np.median(bg_pixels.reshape(-1, 3), axis=0)
        a01 = (alpha_out / 255.0)[..., None]
        safe_a = np.where(a01 > 1e-3, a01, 1.0)
        rgb_out = np.clip((rgb - (1 - a01) * bg_color) / safe_a, 0, 255)
    else:
        rgb_out = rgb

    return rgb_out, alpha_out


# ─── ai (rembg) mode ────────────────────────────────────────────────
def mode_ai(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """rembg + U2Net. Lazy import — graceful error if not installed.

    First call will download the U2Net weights (~170 MB) into the
    user's cache. Subsequent calls reuse the cached model.
    """
    try:
        from rembg import remove
    except ImportError as ex:
        raise RuntimeError(
            "--mode ai requires rembg. Install: pip install rembg "
            f"(import error: {ex})"
        )
    from io import BytesIO

    src = Image.fromarray(rgb.astype(np.uint8), "RGB")
    buf = BytesIO()
    src.save(buf, format="PNG")
    cut_bytes = remove(buf.getvalue())
    cut = Image.open(BytesIO(cut_bytes)).convert("RGBA")
    arr = np.array(cut).astype(np.float64)
    return arr[..., :3], arr[..., 3]


# ─── orchestration ──────────────────────────────────────────────────
def pick_mode(rgb: np.ndarray, verbose: bool = False) -> str:
    """Auto-pick. Stays in classical-CV land — never returns 'ai'.

    Tier picked by corner_disagreement:
      < 18  -> color-key  (bg is a single color)
      18-35 -> grabcut    (bg has gradient / vignette / subtle drift)
      > 35  -> contour    (bg is busy or photo-like)
    """
    d = corner_disagreement(rgb)
    if d < 18:
        if verbose:
            print(f"auto: corner-disagreement={d:.1f} -> color-key", file=sys.stderr)
        return "color-key"
    if d < 35:
        if verbose:
            print(f"auto: corner-disagreement={d:.1f} -> grabcut", file=sys.stderr)
        return "grabcut"
    if verbose:
        print(f"auto: corner-disagreement={d:.1f} -> contour", file=sys.stderr)
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
    rect: str = "auto",
    iters: int = 5,
    input_alpha_path: Path | None = None,
    verbose: bool = False,
) -> None:
    img = Image.open(input_path).convert("RGBA")
    arr = np.array(img).astype(np.float64)
    rgb = arr[..., :3]
    src_alpha = arr[..., 3]
    h, w = rgb.shape[:2]

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
    elif mode == "grabcut":
        gc_rect = parse_rect(rect, w, h)
        if verbose:
            shown = gc_rect or f"auto (5% inset)"
            print(f"grabcut: rect={shown} iters={iters}", file=sys.stderr)
        rgb_out, alpha = mode_grabcut(rgb, rect=gc_rect, iters=iters, feather=feather)
    elif mode == "ai":
        if verbose:
            print("ai: handing off to rembg + U2Net", file=sys.stderr)
        rgb_out, alpha = mode_ai(rgb)
    elif mode == "matting":
        # If the caller passed --input-alpha, refine that. Otherwise re-seed
        # from grabcut. The agent uses --input-alpha to refine a previous
        # attempt's output without re-running grabcut from scratch.
        input_alpha_arr = None
        if input_alpha_path is not None:
            with Image.open(input_alpha_path) as ai:
                input_alpha_arr = np.array(ai.convert("RGBA"))[..., 3].astype(np.float64)
            if verbose:
                print(f"matting: loaded seed alpha from {input_alpha_path}", file=sys.stderr)
        seed_kwargs = {"rect": parse_rect(rect, w, h), "iters": iters} if input_alpha_arr is None else {}
        if verbose and input_alpha_arr is None:
            print("matting: seed_mode=grabcut (refining edges with pymatting)", file=sys.stderr)
        rgb_out, alpha = mode_matting(
            rgb,
            seed_mode="grabcut",
            seed_kwargs=seed_kwargs,
            input_alpha=input_alpha_arr,
            verbose=verbose,
        )
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


def iter_images(d: Path, exts: tuple[str, ...]) -> list[Path]:
    """Find images in a directory matching the given extensions (non-recursive)."""
    out = []
    for child in sorted(d.iterdir()):
        if child.is_file() and child.suffix.lower() in exts:
            out.append(child)
    return out


def run_batch(
    input_dir: Path,
    output_dir: Path,
    exts: tuple[str, ...],
    **kwargs,
) -> tuple[int, int]:
    """Run `run` on every image in `input_dir`, writing into `output_dir`.

    Returns (succeeded, failed). Errors are printed to stderr but don't abort
    the batch — one bad file shouldn't stop the rest.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    images = iter_images(input_dir, exts)
    if not images:
        print(f"no images in {input_dir} matching {exts}", file=sys.stderr)
        return 0, 0
    ok = fail = 0
    for img in images:
        out_path = output_dir / f"{img.stem}-cut.png"
        try:
            run(input_path=img, output_path=out_path, **kwargs)
            ok += 1
        except Exception as ex:
            print(f"  {img.name}: FAILED ({ex})", file=sys.stderr)
            fail += 1
    print(f"batch done: {ok} ok, {fail} failed", file=sys.stderr)
    return ok, fail


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="bgremove",
        description="Classical-CV background remover. No neural net.",
    )
    ap.add_argument("input", type=Path, help="Input image OR directory (PNG / JPG / etc.)")
    ap.add_argument("-o", "--output", type=Path, help="Output PNG (default: <input>-cut.png) or output dir for batch")
    ap.add_argument("--ext", default=".png,.jpg,.jpeg,.webp,.bmp", help="Batch only: comma-separated extensions to include")
    ap.add_argument(
        "--mode",
        choices=["auto", "color-key", "contour", "grabcut", "matting", "ai"],
        default="auto",
        help="Which algorithm to run (default: auto). 'matting' requires `pip install pymatting`. 'ai' requires `pip install rembg[cpu]`.",
    )
    ap.add_argument(
        "--bg-color",
        default="auto",
        help="For color-key: '#RRGGBB' / 'r,g,b' / 'auto' (sample corners)",
    )
    ap.add_argument("--no-unmix", dest="unmix", action="store_false", help="Disable RGB unmixing in color-key mode")
    ap.add_argument("--lo", type=float, default=6.0, help="color-key: bg distance below this -> fully transparent")
    ap.add_argument("--hi", type=float, default=150.0, help="color-key: bg distance above this -> fully opaque")
    ap.add_argument("--feather", type=int, default=0, help="contour/grabcut: Gaussian blur radius for the alpha edge")
    ap.add_argument("--rect", default="auto", help="grabcut: 'auto' (5%% inset) or 'x,y,w,h' bbox")
    ap.add_argument("--iters", type=int, default=5, help="grabcut: number of refinement iterations (default 5)")
    ap.add_argument("--input-alpha", type=Path, dest="input_alpha", help="matting: path to PNG whose alpha channel becomes the seed mask (refine an existing cut)")
    ap.add_argument("-v", "--verbose", action="store_true", help="Print picked mode + alpha summary to stderr")
    args = ap.parse_args(argv)

    if not args.input.exists():
        print(f"input not found: {args.input}", file=sys.stderr)
        return 2

    bg = parse_color(args.bg_color)
    common_kwargs = dict(
        mode=args.mode,
        bg_color=bg,
        unmix=args.unmix,
        lo=args.lo,
        hi=args.hi,
        feather=args.feather,
        rect=args.rect,
        iters=args.iters,
        input_alpha_path=args.input_alpha,
        verbose=args.verbose,
    )

    if args.input.is_dir():
        out_dir = args.output or args.input.with_name(f"{args.input.name}-cut")
        if out_dir.exists() and not out_dir.is_dir():
            print(f"--output must be a directory when input is a directory: {out_dir}", file=sys.stderr)
            return 2
        exts = tuple(e.strip().lower() for e in args.ext.split(",") if e.strip())
        ok, fail = run_batch(args.input, out_dir, exts, **common_kwargs)
        return 0 if fail == 0 else 1

    output = args.output or args.input.with_name(f"{args.input.stem}-cut.png")
    try:
        run(input_path=args.input, output_path=output, **common_kwargs)
    except Exception as ex:
        print(f"bgremove: {ex}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
