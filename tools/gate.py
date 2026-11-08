"""Does a finished reel pass? Mechanical checks on the file, and proof that a real review happened.

It checks the review's record, not the film's quality. The scores are the reviewer's judgment, and each one needs a reason and saved
evidence. A broken model, a false claim or a clipped word blocks a reel whatever its scores say, so list those under blocking_issues.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import common as c

CATEGORIES = ("story", "source_accuracy", "design_fidelity", "visual_quality", "motion", "captions", "audio")
COMMON_CHECKS = ("sources", "asset_rights", "frame_review", "transitions", "caption_review", "audio_review", "mix_levels", "voice_integrity")
MINIMUM_SCORE = 8
VOICE_GAIN_SWING_MAX_DB = 2.0
HARD_LIMIT_SECONDS = 60.0


def template(format_name: str) -> dict:
    meta = c.format_meta(format_name)
    checks = (*COMMON_CHECKS, *meta["checks"])
    return {
        "format": format_name, "sha256": "", "reviewer": "", "reviewed_at": "",
        "scores": {name: {"score": None, "rationale": "", "evidence": []} for name in CATEGORIES},
        "checks": {name: {"status": "pending", "evidence": [], "notes": ""} for name in checks},
        "blocking_issues": [], "human_listening": "not performed", "human_playback": "not performed",
    }


def probe(final: Path) -> dict:
    out = c.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", final], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def validate(post: Path) -> list[str]:
    problems: list[str] = []
    meta = c.format_meta(c.post_meta(post)["format"])
    final = post / "final.mp4"
    if not final.exists():
        return ["final.mp4 doesn't exist yet. Run ./reel finish."]

    # The file itself.
    info = probe(final)
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    seconds = float(info["format"]["duration"])
    low, high = meta["duration"]["min"], meta["duration"]["max"]
    if seconds >= HARD_LIMIT_SECONDS:
        problems.append(f"It runs {seconds:.2f} s. Every reel stays under one minute. Cut words and generate the voice again.")
    elif not low <= seconds <= high:
        problems.append(f"It runs {seconds:.2f} s, and {meta['name']} runs {low} to {high} s.")
    if not video or (video["width"], video["height"]) != (1080, 1920):
        problems.append("The picture must be 1080 x 1920.")
    if video and (video.get("codec_name") != "h264" or video.get("pix_fmt") != "yuv420p"):
        problems.append("The picture must be H.264 yuv420p.")
    if video and video.get("avg_frame_rate") != "30/1":
        problems.append(f"The picture must be 30 fps, and it's {video.get('avg_frame_rate')}.")
    if not audio or audio.get("codec_name") != "aac":
        problems.append("The sound must be AAC.")
    digest = c.sha256(final)

    # The delivery report and the voice.
    def report(name: str) -> dict | None:
        try:
            return json.loads((post / "qa" / name).read_text())
        except (OSError, ValueError):
            problems.append(f"qa/{name} is missing. Run ./reel checks.")
            return None

    delivery = report("delivery.json")
    if delivery:
        if delivery.get("sha256") != digest:
            problems.append("qa/delivery.json describes a different file. Run ./reel checks on the final file.")
        if not delivery.get("technical_passed"):
            problems.append(f"The delivery check failed: {delivery.get('errors')}")
    integrity = report("voice-integrity.json")
    if integrity:
        if integrity.get("sha256") != digest:
            problems.append("qa/voice-integrity.json describes a different file. Run ./reel checks on the final file.")
        swing = integrity.get("gain_swing_db")
        if not isinstance(swing, (int, float)) or swing > VOICE_GAIN_SWING_MAX_DB:
            problems.append(f"The voice's gain varies {swing} dB between sentences. Change the take or the mix, and never ride the voice.")

    # The caption and the credits.
    caption = post / "caption.txt"
    if not caption.exists() or not caption.read_text().strip():
        problems.append("caption.txt is missing. Write it with /ig-caption.")
    credits = post / "assets/CREDITS.md"
    if not credits.exists() or credits.stat().st_size < 120:
        problems.append("assets/CREDITS.md looks empty. Credit every asset, with its licence as read on its own page.")

    # The review record.
    try:
        review = json.loads((post / "qa/quality.json").read_text())
    except (OSError, ValueError):
        problems.append("qa/quality.json is missing or unreadable.")
        return problems
    if review.get("format") != meta["name"]:
        problems.append("qa/quality.json names a different format.")
    if review.get("sha256") != digest:
        problems.append(f"qa/quality.json must name the final file's exact hash, {digest}. Review the file you're shipping.")
    if not review.get("reviewer") or not review.get("reviewed_at"):
        problems.append("qa/quality.json needs a reviewer and a timezone-qualified reviewed_at.")
    if review.get("blocking_issues") != []:
        problems.append(f"Unresolved blocking issues: {review.get('blocking_issues')}")

    def evidence(paths, owner: str) -> None:
        if not isinstance(paths, list) or not paths:
            problems.append(f"{owner} needs saved evidence.")
            return
        for path in paths:
            target = (post / path).resolve()
            if not target.is_relative_to(post.resolve()) or not target.is_file() or not target.stat().st_size:
                problems.append(f"{owner}: evidence {path} is missing, empty or outside this reel's folder.")

    for category in CATEGORIES:
        item = review.get("scores", {}).get(category, {})
        score = item.get("score")
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or not MINIMUM_SCORE <= score <= 10:
            problems.append(f"{category} is {score}, and every category needs at least {MINIMUM_SCORE}/10. Fix the film, not the number.")
        if not str(item.get("rationale", "")).strip():
            problems.append(f"{category} needs a rationale.")
        evidence(item.get("evidence"), category)

    for check in (*COMMON_CHECKS, *meta["checks"]):
        item = review.get("checks", {}).get(check, {})
        status = item.get("status")
        if status != "pass":
            problems.append(f"The {check} check is {status or 'missing'}.")
            continue
        evidence(item.get("evidence"), check)
    for check, needs in (("closing_ask", "the exact last line, why the keyword fits, and its timestamps in the final file"),
                         ("opening_order", "the opening sentences as spoken, showing where the first project is named and where it's called one of five")):
        if check in meta["checks"] and not str(review.get("checks", {}).get(check, {}).get("notes", "")).strip():
            problems.append(f"{check} needs notes: {needs}.")
    return problems
