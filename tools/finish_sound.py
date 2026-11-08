#!/usr/bin/env python3
"""Build a reel's delivered sound. The voice goes from the ElevenLabs file to the final sum, with one fixed gain.

Nothing rides, compresses or equalizes the voice. Music and effects arrive as finished stems that have already moved around it.
The one thing that can touch the voice is a peak limiter on the finished sum, and this reports exactly how much it did. The video
stream is copied. It refuses a reel of one minute or longer.

Run it with ./reel finish <reel>, which fills in every path.

--explore  Lists what each loudness would make the limiter do to the voice, then stops. Use it to choose --target.
--effects-under  Sets the effects this many LU under voice and music. Leave it out to use the effects at the level they arrive.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import minimum_filter1d
from scipy.signal import fftconvolve, resample_poly

LIMIT_SECONDS = 60.0
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--video", required=True)
ap.add_argument("--voice", required=True)
ap.add_argument("--words", required=True)
ap.add_argument("--music", required=True)
ap.add_argument("--effects")
ap.add_argument("--effects-under", type=float)
ap.add_argument("--out")
ap.add_argument("--report")
ap.add_argument("--target", type=float, default=-16.0)
ap.add_argument("--ceiling", type=float, default=-2.3, help="leaves room for the AAC encode to stay at or below -2 dBTP")
ap.add_argument("--explore", action="store_true")
args = ap.parse_args()
if not args.explore and not args.out:
    sys.exit("--out is required unless --explore is set")


def probe(path, entry, stream=None):
    cmd = ["ffprobe", "-v", "error"] + (["-select_streams", stream] if stream else []) + ["-show_entries", entry, "-of", "csv=p=0", str(path)]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip().split(",")[0]


SR = int(probe(args.voice, "stream=sample_rate", "a:0"))  # the voice file's own rate, so its samples are never resampled
dur = float(probe(args.video, "format=duration"))
if dur >= LIMIT_SECONDS:
    sys.exit(f"{args.video} runs {dur:.2f} s. A reel must stay under one minute, so cut words from the script.")
n = int(round(dur * SR))
TMP = Path(args.out or args.video).with_name(".finish_sound_tmp.wav")


def decode(path, channels):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", str(channels), "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, dtype=np.float32).astype(np.float64).reshape(-1, channels)
    return np.pad(a, ((0, max(0, n - len(a))), (0, 0)))[:n]


def write_wav(path, x):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "f64le", "-ar", str(SR), "-ac", str(x.shape[1]), "-i", "-", "-c:a", "pcm_s24le", str(path)],
                         stdin=subprocess.PIPE)
    p.stdin.write(x.astype(np.float64).tobytes())
    p.stdin.close()
    p.wait()


def meter(path):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return (float(re.findall(r"I:\s+(-?[\d.]+) LUFS", err)[-1]), float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", err)[-1]),
            float(re.findall(r"LRA:\s+(-?[\d.]+) LU", err)[-1]))


def true_peak(x):
    """Largest absolute value around each sample, at 4x oversampling."""
    up = np.max(np.abs(resample_poly(x, 4, 1, axis=0)), axis=1)
    return np.maximum(np.abs(x).max(axis=1), up[:len(x) * 4].reshape(len(x), 4).max(axis=1))


def limit(x, ceiling_db, look_ms=2.0, release_ms=25.0):
    """Lookahead peak limiter. The gain moves only around peaks that would pass the ceiling, and it is 1.0 everywhere else."""
    need = np.minimum(1.0, 10 ** (ceiling_db / 20) / np.maximum(true_peak(x), 1e-9))
    look = int(SR * look_ms / 1000)
    held = minimum_filter1d(need, size=2 * look + 1, mode="nearest")
    release = np.exp(-1 / (SR * release_ms / 1000))
    g = held.copy()
    for i in np.nonzero(held < 1.0)[0][:1]:
        cur = 1.0
        for k in range(i, len(g)):
            cur = min(held[k], 1 - (1 - cur) * release)
            g[k] = cur
    win = np.hanning(2 * look + 1)
    # Padded with 1.0, so the smoothing can't read the file's edges as a gain drop.
    g = fftconvolve(np.pad(g, look, constant_values=1.0), win / win.sum(), mode="same")[look:-look]
    g = np.minimum(g, 1.0)
    return x * g[:, None], g


voice, music = decode(args.voice, 1), decode(args.music, 2)
stereo_voice = np.repeat(voice, 2, axis=1)
pre = stereo_voice + music
effects_trim = 0.0
write_wav(TMP, pre)
base_lufs = meter(TMP)[0]
if args.effects:
    effects = decode(args.effects, 2)
    if args.effects_under is not None:
        write_wav(TMP, effects)
        effects_trim = base_lufs - args.effects_under - meter(TMP)[0]
    pre = pre + effects * 10 ** (effects_trim / 20)
write_wav(TMP, pre)
pre_lufs = meter(TMP)[0]
print(f"voice and music {base_lufs:.1f} LUFS, effects trim {effects_trim:+.1f} dB, unity sum {pre_lufs:.1f} LUFS")

speech = np.zeros(n, dtype=bool)
sentences, began = [], None
for w in json.loads(Path(args.words).read_text()):
    text, a, b = w["w"], w["s"], w["e"]
    speech[int(a * SR):int(b * SR)] = True
    began = a if began is None else began
    if re.search(r"[.?!]$", text):
        sentences.append((began, b))
        began = None
v = voice[:, 0]


def rms_db(x):
    return 10 * np.log10(np.mean(x ** 2) + 1e-12)


music_gaps = [round(float(rms_db(v[int(a * SR):int(b * SR)]) - rms_db(music[int(a * SR):int(b * SR)].mean(axis=1))), 1) for a, b in sentences]
print("music under the voice, by sentence, dB:", music_gaps)


def effect_on_voice(g):
    db = -20 * np.log10(g)
    change = 10 * np.log10(np.sum((v * (1 - g))[speech] ** 2) / np.sum(v[speech] ** 2) + 1e-12)
    return {"speech_over_1_db_percent": round(100 * float((db[speech] > 1).mean()), 2), "speech_over_3_db_percent": round(100 * float((db[speech] > 3).mean()), 2),
            "deepest_on_speech_db": round(float(db[speech].max()), 2), "change_to_voice_db": round(float(change), 1)}


if args.explore:
    print("gain needed for each loudness, and what the limiter would then do to the voice:")
    for t in (-14.0, -15.0, -16.0, -17.0, -18.0, -19.0):
        print(f"{t:6.1f} LUFS: gain {t - pre_lufs:+5.2f} dB | {effect_on_voice(limit(pre * 10 ** ((t - pre_lufs) / 20), args.ceiling)[1])}")
    TMP.unlink(missing_ok=True)
    sys.exit()

# The limiter takes a little loudness back, so measure and correct until the sum lands on the target.
gain = args.target - pre_lufs
for _ in range(3):
    out, g = limit(pre * 10 ** (gain / 20), args.ceiling)
    write_wav(TMP, out)
    miss = args.target - meter(TMP)[0]
    if abs(miss) < 0.05:
        break
    gain += miss

# Every moment the limiter pulls down by more than 1.5 dB, so a hot effect gets turned down instead of dipping the voice.
db = -20 * np.log10(g)
hot = np.nonzero(db > 1.5)[0]
events = []
if len(hot):
    events = [{"time": round(int(h[np.argmax(db[h])]) / SR, 2), "db": round(float(db[h].max()), 1), "ms": round(len(h) / SR * 1000)}
              for h in np.split(hot, np.nonzero(np.diff(hot) > SR // 20)[0] + 1)]
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(args.video), "-i", str(TMP), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
                "-b:a", "256k", "-ar", str(SR), "-movflags", "+faststart", str(args.out)], check=True)
TMP.unlink(missing_ok=True)
lufs, peak, lra = meter(args.out)
report = {"output": str(args.out), "duration_seconds": round(dur, 3), "lufs": lufs, "true_peak_dbtp": peak, "lra_lu": lra, "fixed_voice_gain_db": round(float(gain), 2),
          "effects_trim_db": round(effects_trim, 2), "music_under_voice_db_by_sentence": music_gaps, "limiter_on_voice": effect_on_voice(g), "limiter_events_over_1_5_db": events,
          "voice_after_limiter_correlation": round(float(np.corrcoef(v * g, v)[0, 1]), 5)}
print(json.dumps(report, indent=1))
if args.report:
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(report, indent=1) + "\n")
