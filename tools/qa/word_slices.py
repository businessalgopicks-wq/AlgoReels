#!/usr/bin/env python3
"""Test word timing by cutting the narration at the computed boundaries and transcribing each slice.

./reel pick runs this at slice sizes 5, 4 and 3.
Usage:  word_slices.py <narration audio> <words.json> [words per slice] [--fix <out.json>]

--fix walks a slice's start back, up to 0.30 s and never into the previous word's start, until its first word is heard, then
saves the corrected timing in the input's form. A word that's never heard stays put, because it may be a homophone. Run it at a
few slice sizes, since each size only tests the first word of its slices.

If a slice loses its first word, or that word comes back wrong, the boundary is probably late. Speech-to-text also slips on
its own, so read the column rather than treating a mismatch as proof. Uses whisper-cli on the CPU, because its GPU path can crash.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

args = sys.argv[1:]
fix = None
if "--fix" in args:
    at = args.index("--fix")
    fix = args[at + 1]
    del args[at:at + 2]
audio, words = args[0], json.loads(Path(args[1]).read_text())
size = int(args[2]) if len(args) > 2 else 5
model = Path.home() / ".cache/hyperframes/whisper/models/ggml-small.en.bin"


def norm(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


late = 0
with tempfile.TemporaryDirectory() as tmp:
    wav = Path(tmp) / "slice.wav"

    def hear(a, b):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-to", str(b), "-i", audio,
                        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)], check=True)
        out = subprocess.run(["whisper-cli", "-ng", "-nt", "-np", "-m", str(model), "-f", str(wav)], capture_output=True, text=True).stdout
        return " ".join(out.split())

    for i in range(0, len(words), size):
        chunk = words[i:i + size]
        heard = hear(chunk[0]["s"], chunk[-1]["e"])
        want = " ".join(w["w"] for w in chunk)
        first = norm(chunk[0]["w"])
        ok = norm(heard).startswith(first)
        if not ok and fix:
            floor = words[i - 1]["s"] + 0.03 if i else 0.0
            for back in (0.03, 0.06, 0.09, 0.12, 0.15, 0.18, 0.21, 0.24, 0.27, 0.30):
                a = round(chunk[0]["s"] - back, 3)
                if a < floor:
                    break
                if norm(hear(a, chunk[-1]["e"])).startswith(first):
                    print(f"  moved {chunk[0]['w']} from {chunk[0]['s']:.2f} to {a:.2f}")
                    chunk[0]["s"] = a
                    if i:
                        words[i - 1]["e"] = min(words[i - 1]["e"], a)
                    ok = True
                    break
        late += not ok
        print(f"{'  ' if ok else '? '}{chunk[0]['s']:6.2f}  want: {want:44}  heard: {heard}")
print(f"{late} slice(s) of {len(range(0, len(words), size))} to look at")
if fix:
    Path(fix).write_text(json.dumps(words, indent=0))
