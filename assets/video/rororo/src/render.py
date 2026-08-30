"""Render manifest.json at one canvas size via the tiktok-video-maker renderer.

Usage: python render.py 9x16 | 16x9 | 1x1
The still frames are full-canvas at each size (built by make_frames.py); screenshots
get the renderer's blurred fill. Output lands at ../rororo-launch-<size>.mp4.
"""
import importlib.util, json, os, sys

SIZES = {"9x16": (1080, 1920), "16x9": (1920, 1080), "1x1": (1080, 1080)}
SKILL = os.path.expanduser("~/.claude-personal/skills/tiktok-video-maker/scripts/build_video.py")

size = sys.argv[1] if len(sys.argv) > 1 else "9x16"
W, H = SIZES[size]
here = os.path.dirname(os.path.abspath(__file__))
src = json.load(open(os.path.join(here, "manifest.json")))
text = json.dumps(src).replace("{size}", size)
tmp = os.path.join(here, f"manifest-{size}.json")
open(tmp, "w").write(text)

spec = importlib.util.spec_from_file_location("build_video", SKILL)
bv = importlib.util.module_from_spec(spec); spec.loader.exec_module(bv)
bv.W, bv.H = W, H
# single-image slides: let full-canvas stills fill the frame edge to edge
_orig = bv.image_target
def image_target(iw, ih, n, layout, idx):
    if n == 1 and abs(iw / ih - W / H) < 0.01:
        return W, H, 0, 0
    return _orig(iw, ih, n, layout, idx)
bv.image_target = image_target
sys.argv = ["build_video.py", tmp]
bv.main()
