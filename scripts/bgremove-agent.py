#!/usr/bin/env python3
"""bgremove-agent — Claude vision picks + evaluates bgremove cuts.

The closed-loop agentic layer over scripts/bgremove.py. Default workflow:

  1. Read image, encode as base64, send to Claude with a system prompt
     explaining the 5 bgremove modes.
  2. Claude returns a structured strategy: { mode, rect?, bg_color?,
     rationale, confidence }.
  3. Run bgremove.py with those args.
  4. Send Claude the original + the cut and ask: "did this work?" Claude
     returns { quality: clean|rough|broken, issue?, next_strategy? }.
  5. If quality != "clean" and we have attempts left, run the suggested
     next_strategy. Cap at --max-attempts (default 2: initial + 1 retry).

The evaluation step is what makes this different from a naive LLM-routes-
to-classical-CV wrapper — none of the existing open-source tools close
the loop on output quality.

Disable the loop with --no-evaluate (single-shot, v3 behavior, lower cost).

Requires `pip install anthropic` and ANTHROPIC_API_KEY in env.

Examples:
  bgremove-agent logo.png                       # eval on, max 2 attempts
  bgremove-agent photo.jpg --max-attempts 3 -v
  bgremove-agent ./batch/ --no-evaluate         # single-shot for cost savings
"""
from __future__ import annotations

import argparse
import base64
import os
import subprocess
import sys
from pathlib import Path
from typing import Literal, Optional

import anthropic
from PIL import Image
from pydantic import BaseModel, Field

# System prompt is static across all calls — cache it via prompt caching
# (top-level cache_control auto-places on the last cacheable block, so the
# prompt itself caches and we get ~90% read discount on every call after the
# first within a 5-minute window).
SYSTEM_PROMPT = """\
You are picking a background-removal strategy for a single image. Your job: \
pick exactly one mode and any required parameters so the image gets a clean \
cutout. Be honest about confidence — a low score with a soft mode is better \
than a high score with the wrong mode.

Modes available:

1. **color-key** — Distance-from-bg matte + alpha unmix. Use when the bg is a \
single uniform color (logos on flat fields, generated assets, screenshots \
with solid backdrops). **Leave `bg_color` null** — the tool auto-samples \
corner pixels, which is more accurate than your visual estimate. Vision \
can't read pixel-perfect hex from a JPEG-or-PNG view, and color-key is \
unforgiving about the difference (off by 15 RGB units = ghost-bg in the \
output instead of clean transparency). Only specify `bg_color` if the bg is \
NOT in the image corners (rare — e.g., border baked into the file). \
This is the cleanest cut available when applicable. Picks up interior \
negative space (e.g. holes inside hexagons get cut too).

2. **contour** — Canny edge detect → largest outer contour, fills the \
silhouette. Use when the subject is a single high-contrast solid shape \
against a busy bg, AND interior holes don't need to be transparent. \
Doesn't preserve interior negative space. Decent fallback when bg color is \
varied but the subject's outline is sharp.

3. **grabcut** — Iterative graph-cut segmentation. Takes a bounding box \
`[x, y, w, h]` (in original pixel coords) where the subject sits. Use for \
photos with mixed bgs when you can identify roughly where the subject is. \
Without an explicit rect it uses a 5% inset which often works for centered \
subjects. Set `rect` if the subject is off-center.

4. **matting** — Closed-form alpha matting (pymatting). Refines a \
grabcut/color-key seed mask for sub-pixel edge accuracy. Use ONLY when the \
subject has hair, fur, semi-transparent edges, or fine detail that grabcut \
will leave chunky. 3-10× slower than other modes — don't pick it unless \
edge quality matters.

5. **ai** — rembg + U2Net neural net. Use ONLY for portraits, people, \
animals, or images where classical CV will obviously fail (mottled \
camouflage subject, near-monochrome scenes). Pulls a 176MB model on first \
run. Don't pick this for logos, screenshots, or simple shapes — \
classical modes are faster and just as good there.

Output a strict JSON object matching the schema. Keep `rationale` to one \
sentence — what you saw and why this mode fits. Confidence: 0.9+ for \
slam-dunks (logo on solid bg → color-key), 0.6-0.8 for reasonable picks, \
0.4-0.5 if you're unsure. Never above 0.5 if you picked `ai` for a non-photo \
image — it's overkill there.
"""


class BgRemoveStrategy(BaseModel):
    """The structured decision Claude returns."""

    mode: Literal["color-key", "contour", "grabcut", "matting", "ai"]
    rect: Optional[list[int]] = Field(
        None,
        description="grabcut only: [x, y, width, height] in original pixel coords",
    )
    bg_color: Optional[str] = Field(
        None,
        description=(
            "color-key only: '#RRGGBB' to override auto-detection. "
            "Almost always leave null — the tool's corner-sampler is more "
            "accurate than visual color estimation. Specify only when the "
            "bg is NOT in the image corners."
        ),
    )
    rationale: str = Field(..., description="One sentence describing what you saw and why this mode fits")
    confidence: float = Field(..., ge=0.0, le=1.0, description="0..1 estimate of how clean the cut will be")


class CutEvaluation(BaseModel):
    """Claude's verdict on a completed cut."""

    quality: Literal["clean", "rough", "broken"] = Field(
        ...,
        description=(
            "clean = subject preserved + bg fully removed; "
            "rough = mostly worked but has visible issues (halo, fringe, missed bg patches); "
            "broken = wrong subject or large failure"
        ),
    )
    issue: Optional[str] = Field(
        None,
        description="One sentence describing what's wrong, if anything. None when clean.",
    )
    next_strategy: Optional[BgRemoveStrategy] = Field(
        None,
        description=(
            "If quality != 'clean', suggest a different strategy to try next. "
            "Pick a different mode than the one that just ran — don't suggest "
            "the same mode that produced this rough/broken output. None when clean."
        ),
    )


# `from __future__ import annotations` makes Pydantic treat type hints as
# strings; rebuild now that both BgRemoveStrategy and CutEvaluation exist so
# the nested forward reference resolves.
BgRemoveStrategy.model_rebuild()
CutEvaluation.model_rebuild()


EVAL_SYSTEM_PROMPT = """\
You are evaluating a background-removal result. You see two images:

1. **Original** — the input image, with its original background intact.
2. **Cut** — the output PNG after bg removal. Transparent areas show as a \
checkerboard or empty regions in the rendered image; opaque areas are what \
was kept.

Decide:

- **clean** — Subject is fully preserved AND the background is fully removed. \
No halo, no fringe, no leftover bg patches, no missing detail.
- **rough** — Mostly works but has visible issues. Halos around hair/edges, \
soft fringe of bg color, small leftover bg patches, slight loss of subject \
detail. Usable for some purposes but not slam-dunk.
- **broken** — Significant failure. Wrong subject, subject removed, large bg \
patches retained, mode clearly didn't fit.

Be honest. If the cut is clean, say clean and stop — don't invent issues. \
If it's rough or broken, set `issue` to a one-sentence description and \
`next_strategy` to a *different* mode that addresses the specific problem:

- Halo / fringe / chunky edges → matting (refines a grabcut seed)
- Subject removed or wrong region → grabcut with a tighter `rect`
- Bg color bled into subject → color-key with explicit `bg_color`
- Classical modes obviously failing on a portrait → ai (rembg)
- Interior holes filled when they shouldn't be → color-key
- Interior negative space transparent when it shouldn't be → contour

Don't suggest the same mode that just ran with the same params — that won't \
help. Vary the mode, the rect, or the bg_color.
"""


def encode_image(path: Path) -> tuple[str, str, tuple[int, int]]:
    """Return (base64_data, media_type, (width, height))."""
    media_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(path.suffix.lower(), "image/png")

    with Image.open(path) as img:
        size = img.size

    data = path.read_bytes()
    return base64.b64encode(data).decode("ascii"), media_type, size


def pick_strategy(client: anthropic.Anthropic, path: Path, verbose: bool = False) -> BgRemoveStrategy:
    """Ask Claude to look at the image and pick a mode + params."""
    b64, media_type, (w, h) = encode_image(path)
    if verbose:
        print(f"agent: image {path.name} ({w}x{h}, {media_type})", file=sys.stderr)

    response = client.messages.parse(
        model="claude-opus-4-7",
        max_tokens=2000,
        thinking={"type": "adaptive"},
        output_config={"effort": "medium"},
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": b64},
                    },
                    {
                        "type": "text",
                        "text": (
                            f"Image dimensions: {w}x{h} pixels. "
                            f"Pick the best background-removal strategy. "
                            f"If choosing grabcut, give a `rect` in original pixel coords."
                        ),
                    },
                ],
            }
        ],
        output_format=BgRemoveStrategy,
    )

    if verbose and hasattr(response, "usage"):
        cache_read = getattr(response.usage, "cache_read_input_tokens", 0)
        cache_create = getattr(response.usage, "cache_creation_input_tokens", 0)
        print(
            f"agent: tokens in={response.usage.input_tokens} "
            f"out={response.usage.output_tokens} "
            f"cache_read={cache_read} cache_create={cache_create}",
            file=sys.stderr,
        )

    return response.parsed_output


def evaluate_cut(
    client: anthropic.Anthropic,
    original_path: Path,
    cut_path: Path,
    last_strategy: BgRemoveStrategy,
    verbose: bool = False,
) -> CutEvaluation:
    """Send original + cut to Claude, ask for a structured verdict + next move."""
    orig_b64, orig_mt, _ = encode_image(original_path)
    cut_b64, cut_mt, _ = encode_image(cut_path)

    response = client.messages.parse(
        model="claude-opus-4-7",
        max_tokens=2000,
        thinking={"type": "adaptive"},
        output_config={"effort": "medium"},
        system=[
            {
                "type": "text",
                "text": EVAL_SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Image 1 — Original input:"},
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": orig_mt, "data": orig_b64},
                    },
                    {"type": "text", "text": "Image 2 — Cut output (PNG with alpha):"},
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": cut_mt, "data": cut_b64},
                    },
                    {
                        "type": "text",
                        "text": (
                            f"The cut was produced by mode={last_strategy.mode}"
                            f"{f' with rect={last_strategy.rect}' if last_strategy.rect else ''}"
                            f"{f' with bg_color={last_strategy.bg_color}' if last_strategy.bg_color else ''}. "
                            f"Evaluate the result. If not clean, suggest a different strategy."
                        ),
                    },
                ],
            }
        ],
        output_format=CutEvaluation,
    )

    if verbose and hasattr(response, "usage"):
        cache_read = getattr(response.usage, "cache_read_input_tokens", 0)
        cache_create = getattr(response.usage, "cache_creation_input_tokens", 0)
        print(
            f"  eval: tokens in={response.usage.input_tokens} "
            f"out={response.usage.output_tokens} "
            f"cache_read={cache_read} cache_create={cache_create}",
            file=sys.stderr,
        )

    return response.parsed_output


def run_bgremove(
    input_path: Path,
    output_path: Path,
    strategy: BgRemoveStrategy,
    verbose: bool = False,
) -> int:
    """Invoke scripts/bgremove.py with the picked strategy."""
    here = Path(__file__).resolve().parent
    cmd = [
        sys.executable,
        str(here / "bgremove.py"),
        str(input_path),
        "-o",
        str(output_path),
        "--mode",
        strategy.mode,
    ]
    if strategy.mode == "grabcut" and strategy.rect:
        cmd += ["--rect", ",".join(str(int(x)) for x in strategy.rect)]
    if strategy.mode == "color-key" and strategy.bg_color:
        cmd += ["--bg-color", strategy.bg_color]
    if verbose:
        cmd.append("-v")
        print(f"agent: $ {' '.join(cmd)}", file=sys.stderr)
    return subprocess.run(cmd).returncode


def process_one(
    client: anthropic.Anthropic,
    input_path: Path,
    output_path: Path,
    verbose: bool,
    evaluate: bool = True,
    max_attempts: int = 2,
) -> int:
    """Pick a strategy, run it, evaluate the result, retry on failure."""
    strategy = pick_strategy(client, input_path, verbose=verbose)
    print(
        f"{input_path.name}: attempt 1 mode={strategy.mode} "
        f"confidence={strategy.confidence:.2f} — {strategy.rationale}",
        file=sys.stderr,
    )
    rc = run_bgremove(input_path, output_path, strategy, verbose=verbose)
    if rc != 0:
        return rc

    if not evaluate:
        return 0

    for attempt in range(2, max_attempts + 1):
        try:
            evaluation = evaluate_cut(client, input_path, output_path, strategy, verbose=verbose)
        except Exception as ex:
            print(f"  eval failed ({ex}); keeping current cut", file=sys.stderr)
            return 0

        if evaluation.quality == "clean":
            print(f"  eval: clean ✓", file=sys.stderr)
            return 0

        if evaluation.next_strategy is None:
            # Eval said rough/broken but didn't propose a fix — bail.
            print(
                f"  eval: {evaluation.quality} (no retry suggested) — issue: {evaluation.issue}",
                file=sys.stderr,
            )
            return 0

        print(
            f"  eval: {evaluation.quality} — {evaluation.issue}",
            file=sys.stderr,
        )
        strategy = evaluation.next_strategy
        print(
            f"{input_path.name}: attempt {attempt} mode={strategy.mode} "
            f"confidence={strategy.confidence:.2f} — {strategy.rationale}",
            file=sys.stderr,
        )
        rc = run_bgremove(input_path, output_path, strategy, verbose=verbose)
        if rc != 0:
            return rc

    # Final eval after the last attempt — purely informational.
    try:
        final = evaluate_cut(client, input_path, output_path, strategy, verbose=verbose)
        if final.quality == "clean":
            print(f"  eval: clean ✓", file=sys.stderr)
        else:
            print(
                f"  eval: {final.quality} after {max_attempts} attempts — {final.issue}",
                file=sys.stderr,
            )
    except Exception as ex:
        print(f"  final eval failed ({ex})", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="bgremove-agent",
        description="Claude vision picks the bgremove mode. Wraps scripts/bgremove.py.",
    )
    ap.add_argument("input", type=Path, help="Input image OR directory")
    ap.add_argument("-o", "--output", type=Path, help="Output PNG (or output dir for batch)")
    ap.add_argument(
        "--ext",
        default=".png,.jpg,.jpeg,.webp,.bmp",
        help="Batch only: comma-separated extensions to include",
    )
    ap.add_argument(
        "--no-evaluate",
        dest="evaluate",
        action="store_false",
        help="Skip the post-cut evaluation loop (single-shot, lower cost)",
    )
    ap.add_argument(
        "--max-attempts",
        type=int,
        default=2,
        help="Max bgremove invocations per image when evaluating (default: 2 = initial + 1 retry)",
    )
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    if not args.input.exists():
        print(f"input not found: {args.input}", file=sys.stderr)
        return 2

    if "ANTHROPIC_API_KEY" not in os.environ:
        print("ANTHROPIC_API_KEY not set in environment", file=sys.stderr)
        return 2

    client = anthropic.Anthropic()

    if args.input.is_dir():
        out_dir = args.output or args.input.with_name(f"{args.input.name}-cut")
        out_dir.mkdir(parents=True, exist_ok=True)
        exts = tuple(e.strip().lower() for e in args.ext.split(",") if e.strip())
        images = sorted(p for p in args.input.iterdir() if p.is_file() and p.suffix.lower() in exts)
        if not images:
            print(f"no images in {args.input} matching {exts}", file=sys.stderr)
            return 0
        ok = fail = 0
        for img in images:
            try:
                rc = process_one(client, img, out_dir / f"{img.stem}-cut.png", args.verbose, evaluate=args.evaluate, max_attempts=args.max_attempts)
                if rc == 0:
                    ok += 1
                else:
                    fail += 1
            except Exception as ex:
                print(f"  {img.name}: FAILED ({ex})", file=sys.stderr)
                fail += 1
        print(f"agent batch done: {ok} ok, {fail} failed", file=sys.stderr)
        return 0 if fail == 0 else 1

    output = args.output or args.input.with_name(f"{args.input.stem}-cut.png")
    try:
        return process_one(client, args.input, output, args.verbose, evaluate=args.evaluate, max_attempts=args.max_attempts)
    except Exception as ex:
        print(f"bgremove-agent: {ex}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
