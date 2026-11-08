"""Build the music and effects stems around the narration. The voice never enters these files.

The voice is only the key that ducks the music and dips the effects. finish_sound.py then sums these stems with the untouched voice.
Each reel's sound plan is its reel/tools/cues.py.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import common as c
from common import die

FORMAT = "aformat=sample_rates=48000:channel_layouts=stereo"
EFFECTS_LIFT = 3.5  # makes up what the dip under speech takes from the effects overall, so hits away from words keep their level


def load_plan(post: Path):
    path = post / "reel/tools/cues.py"
    if not path.exists():
        die(f"{path.relative_to(c.ROOT)} is missing.")
    spec = importlib.util.spec_from_file_location("cues", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def word_lookup(words: list[dict]):
    def w(word: str, occ: int = 0) -> float:
        hits = [x["s"] for x in words if x["w"].strip(",.!?:;").lower() == word.lower()]
        if occ >= len(hits):
            die(f"cues.py asks for {word!r} (occurrence {occ}), and the narration has it {len(hits)} time(s).")
        return hits[occ]
    return w


def find_sound(folder: Path, name: str) -> Path:
    hits = sorted(p for p in folder.glob(f"{name}.*") if p.suffix.lower() in {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aiff"})
    if not hits:
        die(f"cues.py names {name!r}, and there's no such file in {folder.relative_to(c.ROOT)}.")
    return hits[0]


def build(post: Path) -> None:
    plan = load_plan(post)
    words = c.load_words(post)
    duration = float(c.timeline(post)["duration"])
    voice = c.voice_dir(post) / "narration.mp3"
    out = post / "reel/assets/audio"
    out.mkdir(parents=True, exist_ok=True)
    level = float(getattr(plan, "LEVEL", 0.0))
    music_db = float(getattr(plan, "MUSIC_DB", -18.0))
    threshold = 0.03 * 10 ** (level / 20)
    cues = list(plan.cues(word_lookup(words)))

    music_files = sorted((post / "assets/source/music").glob("bed.*"))
    if music_files:
        music = music_files[0]
        graph = (f"[0:a]{FORMAT},apad[key];"
                 f"[1:a]{FORMAT},atrim=0:{duration},asetpts=N/SR/TB,afade=t=in:d=0.3,afade=t=out:st={max(0, duration - 0.9)}:d=0.9,volume={music_db + level}dB[bed0];"
                 f"[bed0][key]sidechaincompress=threshold={threshold:.4f}:ratio=4:attack=25:release=350[bed]")
        c.run(["ffmpeg", "-v", "error", "-y", "-i", voice, "-i", music, "-filter_complex", graph, "-map", "[bed]", "-t", duration, out / "music_stem.wav"], check=True)
    else:
        print("No music: assets/source/music/bed.* doesn't exist yet, so the music stem is silent.")
        c.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-t", duration, "-i", "anullsrc=r=48000:cl=stereo", out / "music_stem.wav"], check=True)

    inputs: list = ["-f", "lavfi", "-t", duration, "-i", "anullsrc=r=48000:cl=stereo"]
    parts, labels = [], ["[0:a]"]
    sfx = post / "assets/source/sfx"
    for i, (name, start, gain, fade_in, fade_out, trim) in enumerate(cues):
        inputs += ["-i", find_sound(sfx, name)]
        ms = int(round(start * 1000))
        fade = f"afade=t=in:d={fade_in}," if fade_in else ""
        parts.append(f"[{i + 1}:a]{FORMAT},atrim=0:{trim},asetpts=N/SR/TB,{fade}afade=t=out:st={max(0.0, trim - fade_out)}:d={fade_out},"
                     f"volume={gain + level + EFFECTS_LIFT}dB,adelay={ms}|{ms}[c{i}]")
        labels.append(f"[c{i}]")
    inputs += ["-i", voice]
    parts.append(f"{''.join(labels)}amix=inputs={len(labels)}:duration=first:normalize=0[fx0]")
    parts.append(f"[{len(cues) + 1}:a]{FORMAT},apad[fxkey]")
    parts.append(f"[fx0][fxkey]sidechaincompress=threshold={threshold:.4f}:ratio=2:attack=10:release=200[fx]")
    c.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(parts), "-map", "[fx]", "-t", duration, out / "effects_stem.wav"], check=True)
    print(f"Stems written, {len(cues)} effect cue(s), {duration:.2f} s.")
