#!/usr/bin/env bash
# Snapshot a composition at chosen times and tile them into one image, to review many frames at once.
# Run it with ./reel sheet <reel> <comma separated seconds>.
# Times close together (0.08 s apart) show a transition. Reads the pinned HyperFrames version from package.json.
set -euo pipefail
out=$1; times=$2; cols=${3:-6}; w=${4:-330}
mkdir -p "$(dirname "$out")"
pin=$(grep -o 'hyperframes@[0-9.]*' package.json | head -1)
tmp=$(mktemp -d)
npx --yes "$pin" snapshot --at "$times" --no-end -o "$tmp" --json >/dev/null 2>&1 || true
rm -f "$tmp"/contact-sheet*
n=$(ls "$tmp"/frame-*.png | wc -l | tr -d ' ')
ffmpeg -v error -y -pattern_type glob -i "$tmp/frame-*.png" -vf "scale=$w:-2,tile=${cols}x$(( (n + cols - 1) / cols )):padding=5:color=0x222222" -frames:v 1 -update 1 "$out"
rm -rf "$tmp"
echo "$out ($n frames)"
