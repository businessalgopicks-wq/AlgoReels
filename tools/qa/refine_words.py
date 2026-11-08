#!/usr/bin/env python3
"""Correct ElevenLabs' word timing against the take's own audio, so captions and pictures land on the real words.

ElevenLabs' alignment on v4 is close, and when it misses it runs late, by up to about 0.2 s in the take this was measured on. So
each start moves back to the nearest real onset just before it, a word after a real silence starts where the speech returns, and
a word edge at a silence ends where the silence begins. Starts only move earlier, because moving later clipped the front of
words. Check the result with word_slices.py, which catches a boundary this leaves late.

./reel pick runs this. Both JSON files are lists of {"w": on-screen word, "s": start, "e": end}.
"""
import json
import sys
from pathlib import Path

import librosa
import numpy as np

SR, HOP = 22050, 220  # about 10 ms a frame
WINDOW = 0.10  # how far back a start may move to reach an onset


def refine(audio, words, window=WINDOW):
    y, _ = librosa.load(audio, sr=SR, mono=True)
    db = 20 * np.log10(librosa.feature.rms(y=y, frame_length=512, hop_length=HOP)[0] + 1e-7)
    times = librosa.frames_to_time(np.arange(len(db)), sr=SR, hop_length=HOP)
    silent = db < np.percentile(db, 90) - 38
    onsets = librosa.onset.onset_detect(
        onset_envelope=librosa.onset.onset_strength(y=y, sr=SR, hop_length=110), sr=SR, hop_length=110, units="time", backtrack=True)

    silences, i = [], 0  # runs of real silence at least 90 ms long
    while i < len(silent):
        if silent[i]:
            j = i
            while j < len(silent) and silent[j]:
                j += 1
            if (j - i) * HOP / SR >= 0.09:
                silences.append((float(times[i]), float(times[min(j, len(times) - 1)])))
            i = j
        else:
            i += 1

    starts = []
    for w in words:
        s = w["s"]
        earlier = onsets[onsets <= s]
        starts.append(float(earlier[-1]) if len(earlier) and s - earlier[-1] < window else s)
    for _, end in silences:  # a word starting close to the end of a silence starts where the speech returns
        k = min(range(len(starts)), key=lambda n: abs(starts[n] - end))
        if abs(starts[k] - end) < 0.30:
            starts[k] = end
    starts[0] = 0.0 if starts[0] < 0.05 else starts[0]
    for k in range(1, len(starts)):
        starts[k] = max(starts[k], starts[k - 1] + 0.03)

    speech_end = float(times[np.where(~silent)[0][-1]])
    out = []
    for k, w in enumerate(words):
        nxt = starts[k + 1] if k + 1 < len(starts) else speech_end
        end = nxt
        for a, _ in silences:
            if starts[k] < a < nxt:
                end = a
                break
        out.append({"w": w["w"], "s": round(starts[k], 3), "e": round(end, 3)})
    return out, speech_end


if __name__ == "__main__":
    if len(sys.argv) not in (4, 5):
        sys.exit(__doc__)
    audio, source, target = sys.argv[1:4]
    words = json.loads(Path(source).read_text())
    result, speech_end = refine(audio, words, float(sys.argv[4]) if len(sys.argv) == 5 else WINDOW)
    Path(target).write_text(json.dumps(result, indent=0))
    moved = np.array([w["s"] - o["s"] for w, o in zip(result, words)])
    print(f"{len(result)} words. Speech ends {speech_end:.3f}, last word ends {result[-1]['e']:.3f}")
    print(f"moved from ElevenLabs' timing: median {np.median(np.abs(moved)):.3f} s, largest {np.abs(moved).max():.3f} s")
