#!/usr/bin/env bash
# Tile frames of a real video file into one image. Stills from the composition can't prove a move works, so check the file.
# Usage:  strip.sh <video> <start s> <seconds> <out.jpg> [fps] [columns] [width]
# Every frame of a transition:  strip.sh reel.mp4 3.14 0.53 t1.jpg
# The whole reel at a glance:   strip.sh reel.mp4 0 30 all.jpg 2 10 216
set -euo pipefail
video=$1; start=$2; secs=$3; out=$4; fps=${5:-30}; cols=${6:-8}; w=${7:-180}
mkdir -p "$(dirname "$out")"
n=$(python3 -c "import math; print(math.ceil($secs * $fps))")
ffmpeg -v error -y -ss "$start" -t "$secs" -i "$video" -vf "fps=$fps,scale=$w:-2,tile=${cols}x$(( (n + cols - 1) / cols )):padding=3:color=0x222222" -frames:v 1 -update 1 "$out"
echo "$out ($n frames)"
