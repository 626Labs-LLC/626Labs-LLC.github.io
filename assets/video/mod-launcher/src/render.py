"""Render manifest.json at one canvas size via the tiktok-video-maker renderer.

Usage: python render.py 9x16 | 4x5 | 1x1 | 16x9
The still frames are full-canvas at each size (built by make_frames.py); screenshots
get the renderer's blurred fill. Output lands at ../rororo-launch-<size>.mp4.
"""
import importlib.util, json, os, sys

SIZES = {"9x16": (1080, 1920), "4x5": (1080, 1350), "1x1": (1080, 1080), "16x9": (1920, 1080)}
SKILL = os.path.expanduser("~/.claude-personal/skills/tiktok-video-maker/scripts/build_video.py")

size = sys.argv[1] if len(sys.argv) > 1 else "9x16"
W, H = SIZES[size]
here = os.path.dirname(os.path.abspath(__file__))
src = json.load(open(os.path.join(here, "manifest.json")))

# Hub-facing cuts open with the brand title card + a short ident; the 9x16
# TikTok cut keeps the cold open (ad plan: the product demo IS the hook).
if size != "9x16":
    import shutil, tempfile
    src["slides"].insert(0, {"images": [{"path": "frames/{size}/01-title.png", "effect": "fade"}]})
    vo_src = os.path.join(here, src["audio"]["dir"])
    vo_dir = os.path.join(here, f"vo-{size}")
    if os.path.isdir(vo_dir):
        shutil.rmtree(vo_dir)
    os.makedirs(vo_dir)
    durs_path = os.path.join(vo_src, "durations.json")
    durs = json.load(open(durs_path)) if os.path.exists(durs_path) else {}
    remap = {"slide_01": ("title.mp3", durs.get("title"))}
    for i in range(1, len(src["slides"])):
        remap[f"slide_{i + 1:02d}"] = (f"slide_{i:02d}.mp3", durs.get(f"slide_{i:02d}"))
    new_durs = {}
    for key, (fname, dur) in remap.items():
        p = os.path.join(vo_src, fname)
        if os.path.exists(p):
            shutil.copy(p, os.path.join(vo_dir, key + ".mp3"))
            if dur:
                new_durs[key] = dur
    json.dump(new_durs, open(os.path.join(vo_dir, "durations.json"), "w"))
    src["audio"]["dir"] = f"vo-{size}"

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

# --- kenburns: true push-in for single-image slides flagged {"kenburns": {...}} ---
# The skill's zoom_in is fade+drift; this pre-composes the slide (blurred cover
# field + fitted image, matching build_slide's look) and runs ffmpeg zoompan from
# full frame into (cx, cy) of the composed canvas. Zoom strength scales with how
# much of the canvas the image already fills.
KB_ZOOM = {"9x16": 1.85, "4x5": 1.85, "1x1": 1.5, "16x9": 1.35}
_orig_build = bv.build_slide

def build_slide(idx, slide, m, dur, audio_path, tmpdir):
    kb = slide.get("kenburns")
    imgs = slide.get("images") or []
    if not kb or len(imgs) != 1:
        return _orig_build(idx, slide, m, dur, audio_path, tmpdir)
    from PIL import Image, ImageFilter, ImageEnhance
    path = imgs[0]["path"]
    im = Image.open(path).convert("RGB")
    cover = max(W / im.width, H / im.height)
    bg = im.resize((int(im.width * cover) + 1, int(im.height * cover) + 1))
    bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2,
                  (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
    bg = ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(28))).enhance(0.92)
    fit = min(W * 0.92 / im.width, H * 0.86 / im.height)
    fw, fh = int(im.width * fit), int(im.height * fit)
    fx, fy = (W - fw) // 2, (H - fh) // 2
    bg.paste(im.resize((fw, fh), Image.LANCZOS), (fx, fy))
    composed = os.path.join(tmpdir, f"kb_{idx:03d}.png")
    bg.save(composed)
    # zoom target in composed-canvas fractions: image-space (cx, cy) mapped through the fit
    tx = (fx + float(kb.get("cx", 0.5)) * fw) / W
    ty = (fy + float(kb.get("cy", 0.5)) * fh) / H
    fps = m.get("fps", 30)
    n = max(int(dur * fps), 2)
    ze = float(kb.get("zoom", KB_ZOOM.get(size, 1.5)))
    z = f"1+({ze}-1)*on/{n - 1}"
    x = f"min(max({tx}*iw-(iw/zoom)/2,0),iw-iw/zoom)"
    y = f"min(max({ty}*ih-(ih/zoom)/2,0),ih-ih/zoom)"
    filters = [f"[0:v]scale={W * 2}:{H * 2},zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={fps},format=yuv420p[v]"]
    seg = os.path.join(tmpdir, f"seg_{idx:03d}.mp4")
    cmd = ["ffmpeg", "-y", "-i", composed]
    if audio_path:
        cmd += ["-i", audio_path]
        filters.append("[1:a]apad[a]")
        cmd += ["-filter_complex", ";".join(filters), "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}"]
    else:
        cmd += ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=44100:cl=stereo"]
        cmd += ["-filter_complex", ";".join(filters), "-map", "[v]", "-map", "1:a", "-t", f"{dur:.3f}"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-r", str(fps),
            "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2",
            "-movflags", "+faststart", seg]
    bv.run(cmd)
    return seg

bv.build_slide = build_slide
sys.argv = ["build_video.py", tmp]
bv.main()
