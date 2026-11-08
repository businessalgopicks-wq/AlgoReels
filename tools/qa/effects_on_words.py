#!/usr/bin/env python3
"""Find the words an effect sits on top of. A mix can pass every overall check and still lose the end of a word under a hose.

./reel checks runs this. Usage:  effects_on_words.py <voice> <effects stem> <words.json> [--trim dB] [--under dB]

It compares the voice with the effects over the voiced part of each word, and lists every word with less than --under dB between
them (6 by default). --trim is any gain applied to the effects at the finish, as with finish_sound.py's effects trim. Turn down the
cue that's named by its time, not the voice. Speech-to-text on the finished mix is a good second check.
"""
import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

SR = 44100
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("voice")
ap.add_argument("effects")
ap.add_argument("words")
ap.add_argument("--trim", type=float, default=0.0)
ap.add_argument("--under", type=float, default=6.0)
args = ap.parse_args()


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def level(x):
    return 10 * np.log10(np.mean(x ** 2) + 1e-12)


voice, effects = load(args.voice), load(args.effects) * 10 ** (args.trim / 20)
n = min(len(voice), len(effects))
envelope = np.convolve(np.abs(voice[:n]), np.ones(441) / 441, mode="same")
gaps = []
for w in json.loads(Path(args.words).read_text()):
    text, a, b = w["w"], w["s"], w["e"]
    i, j = int(a * SR), min(int(b * SR), n)
    voiced = np.nonzero(envelope[i:j] > 0.01)[0] + i  # above -40 dB
    if len(voiced) < 200:
        continue
    gap = level(voice[voiced]) - level(effects[voiced])
    gaps.append(gap)
    if gap < args.under:
        print(f"{text:14} {a:6.2f}-{b:6.2f}  effects {gap:5.1f} dB under the voice")
print(f"{len(gaps)} words, median {np.median(gaps):.1f} dB, {sum(g < args.under for g in gaps)} under {args.under:g} dB")
