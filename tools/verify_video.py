#!/usr/bin/env python3
"""Read-only delivery checks. Requires ffmpeg and ffprobe; writes only --out.

This checks media integrity and declared delivery settings, not visual quality or truth.
Dark-frame findings require review; they do not automatically mean a broken render.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import subprocess


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('video', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--width', type=int, required=True)
    p.add_argument('--height', type=int, required=True)
    p.add_argument('--fps', type=Fraction, required=True)
    p.add_argument('--duration', type=float, required=True)
    p.add_argument('--frames', type=int, required=True)
    p.add_argument('--silent', action='store_true', help='Explicitly allow a delivery without audio')
    p.add_argument('--dark-threshold', type=float, default=17,
                   help='YAVG screening threshold on a 135px-wide scan, not a universal brightness target')
    a = p.parse_args()
    video = a.video.resolve(); destination = a.out.resolve()
    if video == destination:
        p.error('--out must not overwrite the input video')
    if min(a.width, a.height, a.frames, a.duration, float(a.fps)) <= 0:
        p.error('Expected delivery values must be positive')
    result = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-show_streams',
                             '-show_format', '-of', 'json', str(video)], capture_output=True, text=True)
    if result.returncode:
        p.exit(2, result.stderr)
    probe = json.loads(result.stdout)
    streams = [s for s in probe['streams'] if s['codec_type'] == 'video']
    if not streams:
        p.exit(2, 'No video stream\n')
    v = streams[0]; errors = []
    actual = dict(width=v['width'], height=v['height'], fps=v['avg_frame_rate'],
                  frames=int(v.get('nb_read_frames', 0)),
                  duration=float(v.get('duration', probe['format']['duration'])),
                  video_codec=v['codec_name'], pixel_format=v.get('pix_fmt'))
    for key in ('width', 'height', 'frames'):
        if actual[key] != getattr(a, key):
            errors.append(f'{key}: expected {getattr(a, key)}, found {actual[key]}')
    if Fraction(actual['fps']) != a.fps:
        errors.append(f'fps: expected {a.fps}, found {actual["fps"]}')
    tolerance = max(.001, .5 / float(a.fps))
    if abs(actual['duration'] - a.duration) > tolerance:
        errors.append(f'duration: expected {a.duration}, found {actual["duration"]}')
    audio = [s for s in probe['streams'] if s['codec_type'] == 'audio']
    if not audio and not a.silent:
        errors.append('Missing expected audio stream')
    for s in audio:
        if 'duration' in s and abs(float(s['duration']) - a.duration) > max(.05, 1 / float(a.fps)):
            errors.append(f'Audio duration differs: {s["duration"]}')
    decode = subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(video),
                              '-f', 'null', '-'], capture_output=True, text=True)
    if decode.returncode or decode.stderr.strip():
        errors.append('Full decode reported errors')
    scan = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'info', '-i', str(video),
                           '-map', '0:v:0', '-vf', 'scale=135:-2,signalstats,metadata=print',
                           '-an', '-f', 'null', '-'], capture_output=True, text=True)
    levels = [float(x) for x in re.findall(r'lavfi.signalstats.YAVG=([\d.]+)', scan.stderr)]
    if scan.returncode or len(levels) != actual['frames']:
        errors.append(f'Luminance scan incomplete: {len(levels)} of {actual["frames"]} decoded frames')
    dark = [i for i, value in enumerate(levels) if value < a.dark_threshold]
    with video.open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest()
    report = dict(video=str(video), sha256=digest, technical_passed=not errors, errors=errors,
                  actual=actual, audio=[{k: s.get(k) for k in ('codec_name', 'sample_rate', 'channels', 'duration')} for s in audio],
                  decode_returncode=decode.returncode, decode_diagnostics=decode.stderr.strip(),
                  luma=dict(frames=len(levels), minimum=min(levels) if levels else None,
                            minimum_frame=levels.index(min(levels)) if levels else None,
                            threshold=a.dark_threshold, frames_requiring_review=dark),
                  visual_review='pending', human_audio_listen='pending')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(report=str(destination), technical_passed=not errors,
                          errors=errors, dark_frames_requiring_review=len(dark))))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
