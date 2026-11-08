"""Every check that runs on the delivered file. Rerun after any picture or sound change: numbers in review.md come from here.

Measuring is not watching. These reports feed the review; they don't replace looking at the frames this writes to qa/frames/.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import common as c
from common import die

PY = sys.executable


def save(post: Path, name: str, cmd: list) -> str:
    result = c.run(cmd, capture_output=True, text=True)
    text = (result.stdout or "") + (result.stderr or "")
    (post / "qa" / name).write_text(text)
    lines = text.strip().splitlines()
    return lines[-1] if lines else ""


def frame_at(video: Path, seconds: float, out: Path) -> None:
    c.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{seconds:.3f}", "-i", video, "-frames:v", "1", "-q:v", "2", out], check=True)


def run_all(post: Path) -> None:
    final = post / "final.mp4"
    if not final.exists():
        die(f"{final.relative_to(c.ROOT)} doesn't exist yet. Run ./reel finish first.")
    voice = c.voice_dir(post)
    narration, words = voice / "narration.mp3", voice / "words.json"
    info = c.timeline(post)
    duration = float(info["duration"])
    fps = int(info.get("fps", 30))
    frames = post / "qa/frames"
    frames.mkdir(parents=True, exist_ok=True)

    print("voice levels:     ", save(post, "voice-levels.txt", [PY, c.QA / "voice_levels.py", narration, words]) or "see qa/voice-levels.txt")
    trim = json.loads((post / "qa/sound-finish.json").read_text()).get("effects_trim_db", 0) if (post / "qa/sound-finish.json").exists() else 0
    print("effects on words: ", save(post, "effects-on-words.txt", [PY, c.QA / "effects_on_words.py", narration, post / "reel/assets/audio/effects_stem.wav", words, "--trim", trim]))
    print("voice integrity:  ", save(post, "voice-integrity.txt", [PY, c.QA / "voice_integrity.py", final, narration, words, post / "qa/voice-integrity.json"]))
    delivery = c.run([PY, c.ROOT / "tools/verify_video.py", final, "--width", "1080", "--height", "1920", "--fps", fps, "--duration", duration,
                      "--frames", round(duration * fps), "--out", post / "qa/delivery.json"], capture_output=True, text=True)
    print("delivery:         ", (delivery.stdout or delivery.stderr).strip().splitlines()[0][:220])

    frame_at(final, 0, frames / "first_frame.jpg")
    frame_at(final, max(0, duration - 0.05), frames / "last_frame.jpg")
    c.run(["ffmpeg", "-v", "error", "-y", "-i", final, "-vf", "fps=2,scale=216:-2,tile=14x8:padding=3:color=0x222222", "-frames:v", "1", "-update", "1", frames / "whole_reel_2fps.jpg"], check=True)
    cuts = info.get("cuts", [])
    for cut in cuts:
        c.run(["bash", c.QA / "strip.sh", final, max(0, cut - 0.2), 0.4, frames / f"cut_{cut:06.2f}.jpg", "30", "12", "160"], check=True, capture_output=True)
    moments = [str(round(duration * f, 2)) for f in (0.02, 0.33, 0.66, 0.95)]
    c.run([PY, c.QA / "ig_mock.py", final, frames / "instagram_mock.jpg", *moments], check=True, capture_output=True)

    model = Path.home() / ".cache/hyperframes/whisper/models/ggml-small.en.bin"
    if shutil.which("whisper-cli") and model.exists():
        wav = post / "qa/.final_16k.wav"
        c.run(["ffmpeg", "-v", "error", "-y", "-i", final, "-ar", "16000", "-ac", "1", wav], check=True)
        heard = c.run(["whisper-cli", "-ng", "-m", model, "-f", wav, "-nt", "-np"], capture_output=True, text=True).stdout
        (post / "qa/final-speech-to-text.txt").write_text(" ".join(heard.split()) + "\n")
        wav.unlink(missing_ok=True)
        print("speech to text:    qa/final-speech-to-text.txt. Read it against the script, especially the last line.")
    (post / "qa/final-sha256.txt").write_text(c.sha256(final) + "\n")
    print(f"Frames for review are in {frames.relative_to(c.ROOT)}. Now look at them, at phone size and at full size.")
