"""Voice-pipeline volume leveler — every VO clip to one loudness, no spikes.

Measure-then-correct over the voiceover directories of a video
project: pass one measures each clip (ffmpeg loudnorm, EBU R128), pass
two applies exact gain to the loudness target plus a speech-tuned
limiter that only shaves peaks past the true-peak ceiling — so every
clip matches and no spike survives.

Pipeline position: TTS/retakes -> LEVEL -> render. Run it after any new
clip lands; it is idempotent — clips already within tolerance are left
byte-identical, so re-runs produce zero git churn.

Usage:
  python level_vo.py <project-src-dir>        # sweeps voiceover*/ subdirs
  python level_vo.py <dir> <dir> ...          # explicit clip dirs
  python level_vo.py <dir> --check            # measure + report only
  python level_vo.py <dir> --target -16 --tp -1.5

Targets default to -17 LUFS integrated / -1.5 dBTP. (-16 is the
online convention, but TTS speech under this peak ceiling gives ~1 LU
back to the limiter on hot clips — -17 is the loudest every clip can
actually reach without audible squash, measured across 56 clips on
2026-09-09. What matters for the pipeline is that they all match.)

Durations barely move under gain+limiting, but each dir's
durations.json is re-probed and patched anyway so it can never lie.

Example (the RoRoRo launch project, all seven languages):
  python assets/video/tools/level_vo.py assets/video/rororo/src
"""
import argparse
import json
import os
import re
import subprocess
import sys

TOLERANCE_LU = 0.75  # pause-heavy clips oscillate ~0.6 LU under re-limiting;
                     # 0.75 stops the ping-pong and is inaudible for VO


def measure(path):
    """Pass one: measured loudness stats as a dict."""
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af",
         "loudnorm=print_format=json", "-f", "null", "-"],
        capture_output=True, text=True)
    m = re.search(r"\{[^{}]+\}", proc.stderr[-3000:], re.DOTALL)
    if not m:
        raise RuntimeError(f"loudnorm measure failed for {path}:\n{proc.stderr[-500:]}")
    return json.loads(m.group(0))


def apply_level(path, stats, target_i, target_tp):
    """Pass two: exact gain to the loudness target, then a speech-tuned
    limiter that shaves only the peaks past the ceiling.

    Straight linear loudnorm was tried first and could not converge:
    it respects the TP ceiling by capping the gain, so quiet-but-peaky
    TTS clips land short of the target (title stalled at -18.7 heading
    for -16). Gain+limiter reaches the target exactly; limiting touches
    only the few samples above the ceiling, which barely moves
    integrated loudness on speech. The limiter sits 0.5 dB under the
    stated TP ceiling because it acts on sample peaks and the mp3
    re-encode can push true peak slightly past them.
    """
    gain = target_i - float(stats["input_i"])
    limit_lin = 10 ** ((target_tp - 0.5) / 20)
    af = (
        f"volume={gain:.2f}dB,"
        f"alimiter=limit={limit_lin:.4f}:attack=5:release=50:level=false"
    )
    tmp = path + ".leveled.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", path, "-af", af,
         "-ar", "44100", "-c:a", "libmp3lame", "-b:a", "128k", tmp],
        check=True)
    os.replace(tmp, path)


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True).stdout.strip()
    return round(float(out), 3)


def level_dir(d, target_i, target_tp, check_only):
    clips = sorted(f for f in os.listdir(d) if f.endswith(".mp3"))
    if not clips:
        return 0
    changed = 0
    rows = []
    for clip in clips:
        path = os.path.join(d, clip)
        stats = measure(path)
        loud, peak = float(stats["input_i"]), float(stats["input_tp"])
        off_target = abs(loud - target_i) > TOLERANCE_LU or peak > target_tp
        mark = "LEVEL" if off_target else "ok"
        rows.append(f"  {clip:<14} {loud:>7.1f} LUFS  peak {peak:>6.1f} dBTP  {mark}")
        if off_target:
            changed += 1
            if not check_only:
                apply_level(path, stats, target_i, target_tp)
    print(f"{d}")
    print("\n".join(rows))
    if changed and not check_only:
        dj = os.path.join(d, "durations.json")
        if os.path.exists(dj):
            durs = json.load(open(dj))
            for clip in clips:
                key = clip[:-4]
                if key in durs:
                    durs[key] = probe_duration(os.path.join(d, clip))
            json.dump(durs, open(dj, "w"), indent=2)
        print(f"  -> {changed} clip(s) leveled, durations.json refreshed")
    return changed


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dirs", nargs="+", help="project src dir (sweeps voiceover*/) or explicit clip dirs")
    ap.add_argument("--target", type=float, default=-17.0, help="integrated loudness, LUFS (default -17)")
    ap.add_argument("--tp", type=float, default=-1.5, help="true-peak ceiling, dBTP (default -1.5)")
    ap.add_argument("--check", action="store_true", help="measure and report only, write nothing")
    args = ap.parse_args()

    targets = []
    for d in args.dirs:
        subs = sorted(
            os.path.join(d, s) for s in os.listdir(d)
            if s.startswith("voiceover") and os.path.isdir(os.path.join(d, s)))
        targets.extend(subs if subs else [d])

    total = 0
    for d in targets:
        total += level_dir(d, args.target, args.tp, args.check)
    verb = "would level" if args.check else "leveled"
    print(f"\n{verb if args.check else 'leveled'}: {total} clip(s) across {len(targets)} dir(s), "
          f"target {args.target} LUFS / {args.tp} dBTP")
    return 0


if __name__ == "__main__":
    sys.exit(main())
