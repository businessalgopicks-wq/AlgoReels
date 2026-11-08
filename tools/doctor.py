"""Check everything a reel needs, and say exactly how to fix what's missing."""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path

import common as c

OK, WARN, FAIL = "ok  ", "warn", "FAIL"


def has_filter(name: str) -> bool:
    result = c.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True)
    return any(f" {name} " in line for line in result.stdout.splitlines())


def main() -> int:
    rows: list[tuple[str, str, str]] = []

    def row(state: str, label: str, detail: str = "") -> None:
        rows.append((state, label, detail))

    for tool, install in (("npx", "brew install node"), ("ffmpeg", "brew install ffmpeg-full"), ("ffprobe", "brew install ffmpeg-full")):
        row(OK if shutil.which(tool) else FAIL, tool, "" if shutil.which(tool) else install)
    if shutil.which("ffmpeg"):
        for name in ("sidechaincompress", "ebur128", "signalstats"):
            row(OK if has_filter(name) else FAIL, f"ffmpeg filter {name}", "" if has_filter(name) else "brew install ffmpeg-full")

    in_venv = Path(sys.executable).parent.parent == c.ROOT / ".venv"
    row(OK if in_venv else FAIL, ".venv", "" if in_venv else "run ./setup.sh")
    for module in ("numpy", "scipy", "librosa", "PIL"):
        found = importlib.util.find_spec(module) is not None
        row(OK if found else FAIL, f"python module {module}", "" if found else "run ./setup.sh")

    skills = c.ROOT / ".claude/skills"
    for skill in ("reel", "ig-human", "ig-caption", "openverse-media", "hyperframes", "hyperframes-cli", "earshot"):
        present = (skills / skill / "SKILL.md").exists()
        row(OK if present else FAIL, f"skill {skill}", "" if present else "run ./setup.sh")
    earshot = (c.ROOT / ".venvs/earshot/bin/earshot").exists()
    row(OK if earshot else FAIL, "earshot", "" if earshot else "run ./setup.sh")

    whisper = shutil.which("whisper-cli")
    model = Path.home() / ".cache/hyperframes/whisper/models/ggml-small.en.bin"
    row(OK if whisper and model.exists() else WARN, "speech-to-text", "" if whisper and model.exists() else "word timing can't be tested. Run ./setup.sh")

    blender = c.find_blender()
    if blender:
        version = c.run([blender, "--version"], capture_output=True, text=True).stdout.splitlines()[0]
        tested = version.startswith("Blender 5.")
        row(OK if tested else WARN, "Blender", version if tested else f"{version}. The mechanism kit was tested on Blender 5.2")
    else:
        row(FAIL, "Blender", "brew install --cask blender")

    key = c.env_value("ELEVENLABS_API_KEY")
    if key:
        row(OK, "ElevenLabs key", "set in .env")
        import voice as v
        try:
            for name in c.FORMAT_NAMES:
                meta = c.format_meta(name)["voice"]
                found = v.voice_available(meta["id"])
                if found:
                    row(OK, f"{name} voice", f"{found.get('category', 'available')} on this account")
                else:
                    advice = f"this account can't use it yet. Add it from {meta['library_url']}"
                    if meta.get("fallback_id"):
                        advice += f", or set voice.id in formats/{name}/format.json to {meta['fallback_id']}, a stock voice"
                    row(FAIL, f"{name} voice", advice)
            request = urllib.request.Request(f"{v.API}/user/subscription", headers={"xi-api-key": key, "User-Agent": "algoreel/1.0"})
            with urllib.request.urlopen(request, timeout=20) as response:
                plan = json.load(response)
            left = plan.get("character_limit", 0) - plan.get("character_count", 0)
            row(OK if left > 3000 else WARN, "ElevenLabs characters left", f"{left}. A reel costs about 1,500 at three takes")
        except urllib.error.URLError as error:
            row(WARN, "ElevenLabs", f"couldn't check it: {getattr(error, 'reason', error)}")
    else:
        row(FAIL, "ElevenLabs key", "required. Get one at https://elevenlabs.io/app/settings/api-keys and put it in .env")

    width = max(len(label) for _, label, _ in rows)
    for state, label, detail in rows:
        print(f"{state}  {label:{width}}  {detail}")
    failed = [label for state, label, _ in rows if state == FAIL]
    print()
    if failed:
        print(f"{len(failed)} problem(s) to fix first. Most are solved by running ./setup.sh")
        return 1
    print("Ready. Open Claude Code here and say: create me a mechanism reel about how a zipper works")
    return 0
