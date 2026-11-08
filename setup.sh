#!/usr/bin/env bash
# One command install for macOS. Safe to run again: it skips what's already there.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

say() { printf '\n==> %s\n' "$1"; }

if [ "$(uname -s)" != "Darwin" ]; then
  echo "AlgoReel is built for macOS."
  exit 1
fi
if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is needed. Install it from https://brew.sh, then run ./setup.sh again."
  exit 1
fi

# ---------------------------------------------------------------- system tools
say "System tools"
brew_need() { brew list --formula "$1" >/dev/null 2>&1 || brew install "$1"; }
brew_need python@3.13
brew_need ffmpeg-full
command -v node >/dev/null 2>&1 || brew_need node
command -v whisper-cli >/dev/null 2>&1 || brew_need whisper-cpp
if [ ! -x /Applications/Blender.app/Contents/MacOS/Blender ] && ! command -v blender >/dev/null 2>&1; then
  brew install --cask blender
fi
PYTHON="$(brew --prefix python@3.13)/bin/python3.13"

# ---------------------------------------------------------------- python
say "Python environment"
[ -x .venv/bin/python ] || "$PYTHON" -m venv .venv
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install --quiet -r requirements.txt

# ---------------------------------------------------------------- skills
say "Agent skills, pinned, into .claude/skills"
SRC=.cache/skills-src
mkdir -p "$SRC" .claude/skills
checkout() { # repo ref -> folder
  local repo="$1" ref="$2" name dir
  name="$(basename "$repo" .git)"
  dir="$SRC/$name-$(printf '%s' "$ref" | cut -c1-12)"
  if [ ! -d "$dir/.git" ]; then
    git init --quiet "$dir"
    git -C "$dir" remote add origin "$repo"
    git -C "$dir" config core.sparseCheckout true
    git -C "$dir" sparse-checkout set skills >/dev/null 2>&1 || true
    git -C "$dir" -c advice.detachedHead=false fetch --quiet --depth 1 --filter=blob:none origin "$ref"
    git -C "$dir" -c advice.detachedHead=false checkout --quiet FETCH_HEAD
  fi
  printf '%s' "$dir"
}
while IFS=$'\t' read -r name repo ref path licence; do
  case "$name" in ''|\#*) continue ;; esac
  [ -f ".claude/skills/$name/SKILL.md" ] && continue
  dir="$(checkout "$repo" "$ref")"
  mkdir -p ".claude/skills/$name"
  cp -R "$dir/$path/." ".claude/skills/$name/"
  echo "  $name ($licence)"
done < tools/skills.lock.tsv

# ---------------------------------------------------------------- earshot
say "Earshot, so the agent can measure what it can't hear"
if [ ! -x .venvs/earshot/bin/earshot ]; then
  PIN="$(awk -F'\t' '$1=="earshot"{print $3}' tools/skills.lock.tsv)"
  if [ ! -d vendor/earshot/.git ]; then
    git init --quiet vendor/earshot
    git -C vendor/earshot remote add origin https://github.com/Leonxlnx/earshot.git
    git -C vendor/earshot fetch --quiet --depth 1 origin "$PIN"
    git -C vendor/earshot -c advice.detachedHead=false checkout --quiet FETCH_HEAD
  fi
  mkdir -p .venvs
  "$PYTHON" -m venv .venvs/earshot
  .venvs/earshot/bin/python -m pip install --quiet --upgrade pip
  # Never install "earshot" from PyPI: that name belongs to an unrelated project.
  .venvs/earshot/bin/python -m pip install --quiet -e vendor/earshot
else
  echo "  already installed"
fi

# ---------------------------------------------------------------- speech to text
say "Speech-to-text model, used to test word timing"
MODEL="$HOME/.cache/hyperframes/whisper/models/ggml-small.en.bin"
if [ ! -s "$MODEL" ]; then
  mkdir -p "$(dirname "$MODEL")"
  curl -fL --progress-bar -o "$MODEL.part" https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin
  mv "$MODEL.part" "$MODEL"
else
  echo "  already there"
fi

# ---------------------------------------------------------------- HyperFrames
say "HyperFrames, the renderer"
HF="hyperframes@$(.venv/bin/python -c "import json; print(json.load(open('tools/versions.json'))['hyperframes'])")"
npx --yes "$HF" --version >/dev/null
npx --yes "$HF" browser ensure >/dev/null 2>&1 || echo "  The render browser will download on the first render."

# ---------------------------------------------------------------- key
[ -f .env ] || cp .env.example .env
if ! grep -q '^ELEVENLABS_API_KEY=.' .env && [ -t 0 ]; then
  printf '\nPaste your ElevenLabs API key (required, from https://elevenlabs.io/app/settings/api-keys): '
  read -r KEY || KEY=""
  if [ -n "$KEY" ]; then
    TMP="$(mktemp)"; grep -v '^ELEVENLABS_API_KEY=' .env > "$TMP" || true
    printf 'ELEVENLABS_API_KEY=%s\n' "$KEY" >> "$TMP"
    mv "$TMP" .env; chmod 600 .env
  fi
fi

say "Checking everything"
./reel doctor || true
