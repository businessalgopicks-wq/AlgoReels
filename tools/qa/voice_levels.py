#!/usr/bin/env python3
"""Measure a narration sentence by sentence. A take can fade badly while its overall number looks normal.

./reel checks runs this. Usage:  voice_levels.py <narration audio> <words.json>
Prints each sentence's loudness and how far it sits from the take's median. A large spread means change the take. Don't ride the voice in the edit.
"""
import json
import re
import statistics
import subprocess
import sys

audio, words = sys.argv[1], json.load(open(sys.argv[2]))
sentences, cur = [], []
for w in words:
    cur.append(w)
    if re.search(r"[.?!]$", w["w"]):
        sentences.append(cur)
        cur = []
if cur:
    sentences.append(cur)
rows = []
for s in sentences:
    a, b = s[0]["s"], s[-1]["e"]
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", audio,
                          "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    rows.append((a, b, float(re.findall(r"I:\s+(-?[\d.]+) LUFS", err)[-1]), " ".join(x["w"] for x in s[:4])))
mid = statistics.median(r[2] for r in rows)
print(f"median {mid:.1f} LUFS, spread {max(r[2] for r in rows) - min(r[2] for r in rows):.1f} LU")
for a, b, lufs, text in rows:
    print(f"{a:6.2f} {b:6.2f}  {lufs:6.1f} LUFS  {lufs - mid:+5.1f} dB from median  {text}...")
