#!/usr/bin/env bash
# Cut source footage to the beats and pull a thumbnail from each. Run from reel/. Replace the example lines with this reel's.
# Footage has no sound here, and a short keyframe interval keeps seeking exact. Crop away a demo's bars and on-screen keys,
# and tighten the crop until the subject reads at phone size.
set -euo pipefail
S=../assets/source/clips
enc=(-an -c:v libx264 -crf 15 -preset medium -pix_fmt yuv420p -r 30 -movflags +faststart -g 15)
mkdir -p assets/clips assets/stills

clip() { # source file, start seconds, length seconds, output name, optional ffmpeg filter
  local vf="${5:-scale=1128:846:force_original_aspect_ratio=increase,crop=1128:846}"
  ffmpeg -v error -y -ss "$2" -t "$3" -i "$S/$1" -vf "$vf" "${enc[@]}" "assets/clips/$4.mp4"
  ffmpeg -v error -y -ss 0.5 -i "assets/clips/$4.mp4" -frames:v 1 -q:v 2 "assets/stills/thumb_$4.jpg"
}

# clip project-one-demo.mp4 2.0 6.0 p1
# clip project-two-demo.webm 0.5 5.5 p2 "crop=1432:1074:244:3,scale=1128:846:flags=lanczos"
