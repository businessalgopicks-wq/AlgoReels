#!/usr/bin/env python3
"""Compare narration takes on the things that make a read sound flat or rushed. Use it to shortlist, then choose by ear.

Run it with ./reel takes <reel>.

pitch   Pitch range in semitones, 5th to 95th percentile, with octave errors folded back. Narrower reads flatter.
pauses  Pauses of 0.3 s or longer inside the take. None at all reads as one unbroken run.
gap     How far the quietest stretches fall below speech, in dB. Small means the pauses are filled in.
drift   Level change across the take, in dB per 10 s. A large negative number means the take fades.
w/s     Words per second of speech, with --words.

These are proxies. They can't say a take sounds human, and they don't hear pronunciation.
"""
import argparse
from pathlib import Path

import librosa
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("takes", nargs="+")
ap.add_argument("--words", type=int)
args = ap.parse_args()

HOP = 256
print(f"{'take':44} {'sec':>5} {'w/s':>5} {'pitch':>5} {'pauses':>6} {'gap':>5} {'drift':>6}")
for path in args.takes:
    y, sr = librosa.load(path, sr=22050, mono=True)
    f0, voiced, _ = librosa.pyin(y, fmin=70, fmax=280, sr=sr, frame_length=1024, hop_length=HOP)
    mask = voiced & ~np.isnan(f0)
    st = 12 * np.log2(f0[mask] / np.nanmedian(f0[mask]))
    st = np.where(st > 9, st - 12, st)
    st = np.where(st < -9, st + 12, st)
    pitch = np.percentile(st, 95) - np.percentile(st, 5)

    db = 20 * np.log10(librosa.feature.rms(y=y, frame_length=1024, hop_length=HOP)[0] + 1e-7)
    t = librosa.frames_to_time(np.arange(len(db)), sr=sr, hop_length=HOP)
    loud = np.percentile(db, 90)
    speech = db > loud - 25
    first, last = np.where(speech)[0][[0, -1]]
    inner = db[first:last + 1]
    runs, cur = [], 0
    for quiet in inner < loud - 25:
        if quiet:
            cur += 1
        elif cur:
            runs.append(cur * HOP / sr)
            cur = 0
    span = (last - first) * HOP / sr
    drift = np.polyfit(t[speech], db[speech], 1)[0] * 10
    wps = f"{args.words / span:.2f}" if args.words else "-"
    print(f"{Path(path).stem[:44]:44} {len(y) / sr:5.1f} {wps:>5} {pitch:5.1f} {sum(r >= 0.3 for r in runs):6d} {loud - np.percentile(inner, 3):5.1f} {drift:6.2f}")
