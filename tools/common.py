"""Paths and small helpers shared by the ./reel commands."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REELS = ROOT / "reels"
FORMATS = ROOT / "formats"
QA = ROOT / "tools/qa"
VERSIONS = json.loads((ROOT / "tools/versions.json").read_text())
HYPERFRAMES = f"hyperframes@{VERSIONS['hyperframes']}"
FORMAT_NAMES = sorted(p.parent.name for p in FORMATS.glob("*/format.json"))


def die(message: str, code: int = 1):
    print(message, file=sys.stderr)
    raise SystemExit(code)


def format_meta(name: str) -> dict:
    name = name.lower()
    path = FORMATS / name / "format.json"
    if not path.exists():
        die(f"Unknown format {name!r}. Choose one of: {', '.join(FORMAT_NAMES)}")
    return json.loads(path.read_text())


def env_value(name: str) -> str | None:
    """Read one value from the project's .env. Values are never printed."""
    path = ROOT / ".env"
    if not path.exists():
        return None
    for line in path.read_text().splitlines():
        if line.startswith(f"{name}="):
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            return value or None
    return None


def resolve_post(arg: str | None) -> Path:
    """A post is named by its path, its folder name, part of its folder name, or 'latest' (also the default)."""
    posts = [p for p in REELS.iterdir() if (p / "post.json").exists()] if REELS.exists() else []
    if not posts:
        die("No reels yet. Start one with:  ./reel new roundup \"your topic\"")
    if arg in (None, "latest"):
        return max(posts, key=lambda p: (p / "post.json").stat().st_mtime)
    direct = Path(arg).expanduser()
    if (direct / "post.json").exists():
        return direct.resolve()
    hits = [p for p in posts if arg in p.name]
    if len(hits) == 1:
        return hits[0]
    if hits:
        die(f"{arg!r} matches several reels: {', '.join(p.name for p in hits)}")
    die(f"No reel matches {arg!r}. Reels: {', '.join(sorted(p.name for p in posts))}")


def post_meta(post: Path) -> dict:
    return json.loads((post / "post.json").read_text())


def voice_dir(post: Path) -> Path:
    return post / "assets/source/voice"


def load_words(post: Path) -> list[dict]:
    path = voice_dir(post) / "words.json"
    if not path.exists():
        die(f"{path} doesn't exist yet. Choose a take first:  ./reel pick {post.name} <label>")
    return json.loads(path.read_text())


def timeline(post: Path) -> dict:
    path = post / "reel/timeline.json"
    if not path.exists():
        die(f"{path} doesn't exist yet. The reel's generator writes it, so build the composition first.")
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(cmd: list, **kw) -> subprocess.CompletedProcess:
    return subprocess.run([str(c) for c in cmd], **kw)


def duration_of(path: Path) -> float:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def slugify(text: str, limit: int = 48) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:limit].rstrip("-") or "reel"


def find_blender() -> str | None:
    import os
    candidates = [os.environ.get("BLENDER"), "/Applications/Blender.app/Contents/MacOS/Blender", shutil.which("blender")]
    return next((c for c in candidates if c and Path(c).exists()), None)
