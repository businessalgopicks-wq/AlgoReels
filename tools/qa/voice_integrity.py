#!/usr/bin/env python3
"""Check whether a finished video still carries the voice as recorded, or whether editing has changed it.

./reel checks runs this. Usage:  voice_integrity.py <video> <narration audio> <words.json> [report.json]

For each sentence it fits how much of the original voice is in the mix. Music and effects don't correlate with the voice, so
this reads the voice's real gain. An untouched voice shows one fixed gain and high correlation in every sentence. Gain rides
show up as sentences at different gains, and compression or limiting as lower correlation in the loud moments.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.signal import fftconvolve

SR = 44100
video, narration, words_path = sys.argv[1:4]
report_path = sys.argv[4] if len(sys.argv) > 4 else None


def load(path):
    # Decode each file with its real channels and average them here. ffmpeg's float up and down mixes change the level by 3 dB.
    channels = int(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels", "-of", "csv=p=0", path],
                                  capture_output=True, text=True, check=True).stdout.strip().split(",")[0])
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64).reshape(-1, channels).mean(axis=1)


mix, voice = load(video), load(narration)
n = min(len(mix), len(voice))
# Find any time offset between them, within half a second.
span = SR // 2
head = min(n, SR * 12)
corr = fftconvolve(mix[:head], voice[:head][::-1], mode="full")
centre = head - 1
window = corr[centre - span:centre + span + 1]
offset = int(np.argmax(window)) - span
print(f"time offset of the voice in the mix: {1000 * offset / SR:+.2f} ms")
if offset > 0:
    mix = mix[offset:]
elif offset < 0:
    mix = np.pad(mix, (-offset, 0))
n = min(len(mix), len(voice))
mix, voice = mix[:n], voice[:n]

words = json.loads(Path(words_path).read_text())
spans, start = [], None
for w in words:
    start = w["s"] if start is None else start
    if re.search(r"[.?!]$", w["w"]):
        spans.append((start, w["e"], w["w"]))
        start = None
gains, matches = [], []
print(f"{'sentence':>16} {'voice gain':>11} {'match':>7}")
for a, b, last in spans:
    i, j = int(a * SR), min(int(b * SR), n)
    v, m = voice[i:j], mix[i:j]
    g = float(np.dot(m, v) / (np.dot(v, v) + 1e-12))
    r = float(np.corrcoef(m, v)[0, 1])
    gains.append(20 * np.log10(abs(g) + 1e-9))
    matches.append(r)
    print(f"{a:7.2f}-{b:7.2f} {gains[-1]:+10.2f} dB {r:7.3f}")
print(f"voice gain varies by {max(gains) - min(gains):.2f} dB across the sentences")
if report_path:
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).write_text(json.dumps({"video": video, "sha256": hashlib.sha256(Path(video).read_bytes()).hexdigest(), "narration": narration,
                                             "sentences": len(gains), "offset_ms": round(1000 * offset / SR, 2),
                                             "gain_swing_db": round(max(gains) - min(gains), 2), "lowest_match": round(min(matches), 3)}, indent=1) + "\n")
