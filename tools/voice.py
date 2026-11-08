"""Narration takes, word timing, and generated sound, all from ElevenLabs.

The voice is the clock for the whole reel, so nothing downstream ever speeds it up or processes it.
"""
from __future__ import annotations

import base64
import json
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path

import common as c
from common import die

API = "https://api.elevenlabs.io/v1"
WHISPER_MODEL = Path.home() / ".cache/hyperframes/whisper/models/ggml-small.en.bin"


def api_key() -> str:
    key = c.env_value("ELEVENLABS_API_KEY")
    if not key:
        die("ELEVENLABS_API_KEY isn't set. It's required: get one at https://elevenlabs.io/app/settings/api-keys and put it in .env.")
    return key


def _request(url: str, *, body: dict | None = None, timeout: int = 180) -> bytes:
    headers = {"xi-api-key": api_key(), "User-Agent": "algoreel/1.0"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers), timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        detail = error.read()[:400].decode("utf-8", "replace")
        if error.code in (401, 403):
            die(f"ElevenLabs refused the key (HTTP {error.code}). Check ELEVENLABS_API_KEY in .env.\n{detail}")
        die(f"ElevenLabs returned HTTP {error.code}.\n{detail}")
    except urllib.error.URLError as error:
        die(f"Couldn't reach ElevenLabs: {error.reason}")


def voice_available(voice_id: str) -> dict | None:
    """Free check. Returns the voice's record, or None if this account can't use it."""
    try:
        request = urllib.request.Request(f"{API}/voices/{voice_id}", headers={"xi-api-key": api_key(), "User-Agent": "algoreel/1.0"})
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError:
        return None


def narration_text(post: Path) -> str:
    path = c.voice_dir(post) / "narration.txt"
    if not path.exists() or not path.read_text().strip():
        die(f"{path.relative_to(c.ROOT)} is empty. Put the spoken script in it, with names respelled for the voice if needed.")
    return path.read_text().strip()


def take(post: Path, label: str, seed: int | None = None) -> None:
    meta = c.format_meta(c.post_meta(post)["format"])
    text = narration_text(post)
    takes = c.voice_dir(post) / "takes"
    takes.mkdir(parents=True, exist_ok=True)
    voice = meta["voice"]
    body: dict = {"text": text, "model_id": voice["model"]}
    if seed is not None:
        body["seed"] = seed
    url = f"{API}/text-to-speech/{voice['id']}/with-timestamps?output_format=mp3_44100_128"
    data = json.loads(_request(url, body=body))
    (takes / f"{label}.mp3").write_bytes(base64.b64decode(data["audio_base64"]))
    (takes / f"{label}.json").write_text(json.dumps(data["alignment"]))
    end = data["alignment"]["character_end_times_seconds"][-1]
    print(f"{label}: {voice['name']} on {voice['model']}, {end:.2f} s, {len(text.split())} words, {len(text)} characters used")
    _report_length(meta, end)


def _report_length(meta: dict, seconds: float) -> None:
    low, high = meta["duration"]["min"], meta["duration"]["max"]
    if seconds > high - 1:
        print(f"Too long for this format's {low} to {high} s, with room for the ending. Cut words and generate again. Never speed the voice up.")
    elif seconds < low - 3:
        print(f"Short for this format's {low} to {high} s. Add a beat, or accept it and say why in review.md.")


def split_words(characters: list[str], starts: list[float], ends: list[float]) -> list[tuple[str, float, float]]:
    words, current, begun, last = [], "", 0.0, 0.0
    for char, start, end in zip(characters, starts, ends):
        if char.isspace():
            if current:
                words.append((current, begun, last))
            current = ""
            continue
        if not current:
            begun = start
        current += char
        last = end
    if current:
        words.append((current, begun, last))
    return words


def screen_words(post: Path, spoken: list[tuple[str, float, float]]) -> list[dict]:
    """Map spoken words to on-screen words.

    The voice can read a respelling ("Quick V two") while the screen shows the real name ("QuickV2"). screen.txt holds the
    on-screen script, and a token like QuickV2:3 says that word covers three spoken words. With no screen.txt the two are the same.
    """
    path = c.voice_dir(post) / "screen.txt"
    if not path.exists():
        return [{"w": w, "s": round(a, 3), "e": round(b, 3)} for w, a, b in spoken]
    out, i = [], 0
    for token in path.read_text().split():
        count = 1
        if ":" in token and token.rsplit(":", 1)[1].isdigit():
            token, n = token.rsplit(":", 1)
            count = int(n)
        chunk = spoken[i:i + count]
        if not chunk:
            die(f"screen.txt has more words than the take, at {token!r}.")
        out.append({"w": token, "s": round(chunk[0][1], 3), "e": round(chunk[-1][2], 3)})
        i += count
    if i != len(spoken):
        die(f"screen.txt covers {i} spoken words, and the take has {len(spoken)}. Fix the :counts.")
    return out


def pick(post: Path, label: str, test: bool = True) -> None:
    """Make one take the narration: copy it into place, build the word timing, correct it against the audio, test it."""
    voice = c.voice_dir(post)
    source, chars = voice / "takes" / f"{label}.mp3", voice / "takes" / f"{label}.json"
    if not source.exists() or not chars.exists():
        die(f"No take named {label!r} in {(voice / 'takes').relative_to(c.ROOT)}. Make one with ./reel voice.")
    narration = voice / "narration.mp3"
    shutil.copyfile(source, narration)
    a = json.loads(chars.read_text())
    spoken = split_words(a["characters"], a["character_start_times_seconds"], a["character_end_times_seconds"])
    words = screen_words(post, spoken)
    (voice / "words_raw.json").write_text(json.dumps(words, indent=0))
    target = voice / "words.json"
    refine = c.run([sys.executable, c.QA / "refine_words.py", narration, voice / "words_raw.json", target])
    if refine.returncode:
        die("Word refinement failed. Is the environment installed? Run ./setup.sh")
    if test and shutil.which("whisper-cli") and WHISPER_MODEL.exists():
        for size in (5, 4, 3):
            c.run([sys.executable, c.QA / "word_slices.py", narration, target, size, "--fix", target], check=True)
    elif test:
        print("Skipped the speech-to-text timing test: whisper-cli or its model isn't installed. Run ./setup.sh to add them.")
    audio = post / "reel/assets/audio"
    audio.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(narration, audio / "narration.mp3")
    meta = c.format_meta(c.post_meta(post)["format"])
    seconds = c.duration_of(narration)
    print(f"Chose {label}: {seconds:.2f} s, {len(words)} on-screen words. Timing is in {target.relative_to(c.ROOT)}.")
    _report_length(meta, seconds)
    print("Look at the take's biggest peaks too: a hard vowel after a pause can start before the timing says it does.")


def sound_effect(post: Path, name: str, prompt: str, seconds: float) -> None:
    out = post / "assets/source/sfx" / f"{name}.mp3"
    if out.exists():
        print(f"{out.relative_to(c.ROOT)} exists, so it was kept. Delete it to generate again.")
        return
    body = {"text": prompt, "duration_seconds": seconds, "prompt_influence": 0.5}
    out.write_bytes(_request(f"{API}/sound-generation?output_format=mp3_44100_128", body=body))
    print(out.relative_to(c.ROOT))
    with (post / "assets/CREDITS.md").open("a") as credits:
        credits.write(f"- Sound effect `{name}`: generated with ElevenLabs. Prompt: {prompt}\n")


def music(post: Path, prompt: str, seconds: float) -> None:
    out = post / "assets/source/music/bed.mp3"
    if out.exists():
        print(f"{out.relative_to(c.ROOT)} exists, so it was kept. Delete it to generate again.")
        return
    body = {"prompt": prompt, "music_length_ms": int(seconds * 1000), "model_id": "music_v1"}
    out.write_bytes(_request(f"{API}/music?output_format=mp3_44100_128", body=body, timeout=400))
    print(out.relative_to(c.ROOT))
    with (post / "assets/CREDITS.md").open("a") as credits:
        credits.write(f"- Music: generated with ElevenLabs. Prompt: {prompt}\n")
