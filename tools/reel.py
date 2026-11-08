#!/usr/bin/env python3
"""The ./reel command. Every step of making a reel goes through here, so nobody has to remember a path."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as c  # noqa: E402
from common import die, resolve_post, run  # noqa: E402

PY = sys.executable


# ---------------------------------------------------------------- starting a reel
def fetch_font(name: str) -> Path:
    cache = c.ROOT / ".cache/fonts"
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / name
    if not path.exists():
        request = urllib.request.Request(c.VERSIONS["fonts"][name], headers={"User-Agent": "algoreel/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            path.write_bytes(response.read())
    return path


def cmd_new(args):
    meta = c.format_meta(args.format)
    name = meta["name"]
    date = dt.date.today().isoformat()
    post = c.REELS / f"{date}-{name}-{c.slugify(args.topic)}"
    if post.exists():
        die(f"{post.relative_to(c.ROOT)} already exists. Continue it, or change the topic.")
    fmt = c.FORMATS / name
    for folder in ("assets/source/voice/takes", "assets/source/clips", "assets/source/sfx", "assets/source/music", "qa", "storyboard"):
        (post / folder).mkdir(parents=True, exist_ok=True)
    shutil.copytree(fmt / "starter", post / "reel", dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    for template in (fmt / "templates").glob("*.md"):
        shutil.copyfile(template, post / template.name)
    (post / "assets/CREDITS.md").write_text("# Credits\n\nEvery picture, clip, sound and font that isn't made here, with its source link and licence as read on the source page.\n\n")
    (post / "post.json").write_text(json.dumps({"format": name, "topic": args.topic, "created": date}, indent=2) + "\n")

    reel = post / "reel"
    (reel / "assets/fonts").mkdir(parents=True, exist_ok=True)
    (reel / "assets/audio").mkdir(parents=True, exist_ok=True)
    font_note = []
    if name == "roundup":
        for font in ("Inter-600.woff2", "InstrumentSerif-Italic.woff2", "Anton-400.woff2", "JetBrainsMono-500.woff2"):
            shutil.copyfile(fetch_font(font), reel / "assets/fonts" / font)
        font_note = ["Inter, Instrument Serif, Anton and JetBrains Mono, SIL Open Font License, from Fontsource"]
    else:
        shutil.copyfile("/System/Library/Fonts/Supplemental/Tahoma Bold.ttf", reel / "assets/fonts/caption-bold.ttf")
        font_note = ["Tahoma Bold, from this Mac's system fonts"]
    with (post / "assets/CREDITS.md").open("a") as credits:
        credits.write("## Fonts\n\n" + "\n".join(f"- {line}" for line in font_note) + "\n")

    pin = c.HYPERFRAMES
    (reel / "package.json").write_text(json.dumps({"name": post.name, "private": True, "type": "module", "scripts": {
        "check": f"npx --yes {pin} check", "render": f"npx --yes {pin} render"}}, indent=2) + "\n")
    (reel / "meta.json").write_text(json.dumps({"id": post.name, "name": post.name, "createdAt": dt.datetime.now(dt.timezone.utc).isoformat()}, indent=2) + "\n")
    (reel / "hyperframes.json").write_text(json.dumps({
        "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
        "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
        "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
        "media": {"autoProxy": False}, "authoringSkill": "hyperframes"}, indent=2) + "\n")

    import gate
    (post / "qa/quality.json").write_text(json.dumps(gate.template(name), indent=2) + "\n")
    print(post.relative_to(c.ROOT))


# ---------------------------------------------------------------- the voice
def cmd_voice(args):
    import voice
    post = resolve_post(args.post)
    voice.take(post, args.label, seed=args.seed)


def cmd_takes(args):
    post = resolve_post(args.post)
    takes = sorted((c.voice_dir(post) / "takes").glob("*.mp3"))
    if not takes:
        die(f"No takes yet. Make one:  ./reel voice {post.name} take1")
    spoken = (c.voice_dir(post) / "narration.txt").read_text().split()
    run([PY, c.QA / "compare_takes.py", *takes, "--words", len(spoken)], check=True)


def cmd_pick(args):
    import voice
    voice.pick(resolve_post(args.post), args.label, test=not args.no_test)


def cmd_sound(args):
    import voice
    voice.sound_effect(resolve_post(args.post), args.name, args.prompt, args.seconds)


def cmd_music(args):
    import voice
    voice.music(resolve_post(args.post), args.prompt, args.seconds)


# ---------------------------------------------------------------- the picture
def in_reel(post: Path, *cmd):
    run(cmd, cwd=post / "reel", check=True)


def cmd_build(args):
    post = resolve_post(args.post)
    script = "build_compositions.py" if c.post_meta(post)["format"] == "roundup" else "build_hf.py"
    in_reel(post, PY, f"tools/{script}")


def cmd_check(args):
    post = resolve_post(args.post)
    raise SystemExit(run([PY, c.QA / "check.py"], cwd=post / "reel").returncode)


def cmd_sheet(args):
    post = resolve_post(args.post)
    out = Path(args.out) if args.out else post / "storyboard" / "sheet.jpg"
    in_reel(post, "bash", c.QA / "sheet.sh", out.resolve(), args.times, args.columns, args.width)


def cmd_strip(args):
    post = resolve_post(args.post)
    video = post / "final.mp4" if (post / "final.mp4").exists() else post / "reel/base.mp4"
    out = (post / "qa/frames" / f"strip_{args.start}.jpg").resolve()
    run(["bash", c.QA / "strip.sh", video, args.start, args.seconds, out, args.fps, args.columns, args.width], check=True)


def cmd_render(args):
    post = resolve_post(args.post)
    quality, output = ("draft", "draft.mp4") if args.draft else ("delivery", "base.mp4")
    in_reel(post, "npx", "--yes", c.HYPERFRAMES, "render", "-q", quality, "--skill", "hyperframes", "-o", output)
    print(post.relative_to(c.ROOT) / "reel" / output)


def cmd_shots(args):
    """Mechanism: render shots with the frozen, validated Blender batch runner."""
    post = resolve_post(args.post)
    in_reel(post, PY, "tools/render_refined.py", *args.rest)


def cmd_blender(args):
    """Mechanism: run a Blender script against this reel, with its environment set. Paths are relative to reel/, or to the repo for tools/."""
    import os
    post = resolve_post(args.post)
    blender = c.find_blender()
    if not blender:
        die("Blender isn't installed. On a Mac: brew install --cask blender")
    script = post / "reel" / args.script if (post / "reel" / args.script).exists() else c.ROOT / args.script
    if not script.exists():
        die(f"No script at {args.script}, in the reel or in the repo.")
    profile = c.ROOT / ".cache/blender-profile"
    profile.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "REEL_ROOT": str(post), "BLENDER_USER_RESOURCES": str(profile)}
    raise SystemExit(run([blender, "-b", "--python-exit-code", "1", "--python", script, "--", *args.rest], cwd=post / "reel", env=env).returncode)


def cmd_assemble(args):
    """Mechanism: frames to picture track, then the HyperFrames project on top of it."""
    post = resolve_post(args.post)
    in_reel(post, PY, "tools/post.py", args.frames, "assets/picture.mp4")
    in_reel(post, PY, "tools/build_hf.py")


# ---------------------------------------------------------------- the sound and the finish
def cmd_mix(args):
    import mix
    mix.build(resolve_post(args.post))


def cmd_finish(args):
    post = resolve_post(args.post)
    audio = post / "reel/assets/audio"
    base = post / "reel/base.mp4"
    for path in (base, audio / "music_stem.wav", audio / "effects_stem.wav"):
        if not path.exists():
            die(f"{path.relative_to(c.ROOT)} is missing. Run ./reel render and ./reel mix first.")
    voice_dir = c.voice_dir(post)
    cmd = [PY, c.ROOT / "tools/finish_sound.py", "--video", base, "--voice", voice_dir / "narration.mp3", "--words", voice_dir / "words.json",
           "--music", audio / "music_stem.wav", "--effects", audio / "effects_stem.wav", "--target", args.target]
    if args.explore:
        run(cmd + ["--explore"], check=True)
        return
    run(cmd + ["--out", post / "final.mp4", "--report", post / "qa/sound-finish.json"], check=True)
    import checks
    checks.run_all(post)


def cmd_checks(args):
    import checks
    checks.run_all(resolve_post(args.post))


def cmd_gate(args):
    import gate
    post = resolve_post(args.post)
    problems = gate.validate(post)
    if problems:
        print("GATE FAILED")
        for problem in problems:
            print(" -", problem)
        raise SystemExit(1)
    print(f"GATE OK  {(post / 'final.mp4').relative_to(c.ROOT)}")


def cmd_status(args):
    post = resolve_post(args.post)
    meta = c.post_meta(post)
    voice_dir = c.voice_dir(post)
    steps = [
        ("script", (voice_dir / "narration.txt").exists(), "write script.md, then its spoken words to assets/source/voice/narration.txt"),
        ("takes", any((voice_dir / "takes").glob("*")), f"./reel voice {post.name} take1"),
        ("word timing", (voice_dir / "words.json").exists(), f"./reel pick {post.name} take1"),
        ("composition", (post / "reel/timeline.json").exists(), f"./reel build {post.name}" if meta["format"] == "roundup" else f"./reel shots {post.name} -- --out ../.cache/picture-v1, then ./reel assemble {post.name} .cache/picture-v1"),
        ("base render", (post / "reel/base.mp4").exists(), f"./reel render {post.name}"),
        ("stems", (post / "reel/assets/audio/music_stem.wav").exists(), f"./reel mix {post.name}"),
        ("final", (post / "final.mp4").exists(), f"./reel finish {post.name}"),
        ("caption", (post / "caption.txt").exists(), "write caption.txt with /ig-caption"),
    ]
    print(f"{post.relative_to(c.ROOT)}  ({meta['format']}: {meta['topic']})")
    pending = None
    for label, done, how in steps:
        print(f"  [{'x' if done else ' '}] {label}")
        pending = pending or (None if done else how)
    print(f"next: {pending}" if pending else f"next: complete qa/quality.json, then ./reel gate {post.name}")


def cmd_doctor(args):
    import doctor
    raise SystemExit(doctor.main())


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="./reel", description="Make a mechanism or roundup reel. Say it to Claude Code, or run the steps yourself.")
    sub = p.add_subparsers(dest="command", required=True, metavar="command")

    def add(name, fn, help_text, post=True):
        cmd = sub.add_parser(name, help=help_text)
        cmd.set_defaults(fn=fn)
        if post:
            cmd.add_argument("post", nargs="?" if name in OPTIONAL_POST else None, help="reel folder, part of its name, or 'latest'")
        return cmd

    OPTIONAL_POST = {"status", "build", "check", "render", "mix", "finish", "checks", "gate", "takes"}

    add("doctor", cmd_doctor, "check everything is installed, and the ElevenLabs key and voices (free calls)", post=False)

    n = add("new", cmd_new, "start a reel: ./reel new roundup \"five robotics projects\"", post=False)
    n.add_argument("format", help=f"one of: {', '.join(c.FORMAT_NAMES)}")
    n.add_argument("topic")

    add("status", cmd_status, "what's done, and the next step")

    v = add("voice", cmd_voice, "one narration take from assets/source/voice/narration.txt")
    v.add_argument("label")
    v.add_argument("--seed", type=int)

    add("takes", cmd_takes, "compare the takes, to shortlist before listening")

    k = add("pick", cmd_pick, "choose a take and build its word timing")
    k.add_argument("label")
    k.add_argument("--no-test", action="store_true", help="skip the speech-to-text timing test")

    s = add("sound", cmd_sound, "generate one sound effect with ElevenLabs (uses credits)")
    s.add_argument("name")
    s.add_argument("prompt")
    s.add_argument("seconds", type=float)

    m = add("music", cmd_music, "generate a music bed with ElevenLabs (uses credits)")
    m.add_argument("prompt")
    m.add_argument("seconds", type=float)

    add("build", cmd_build, "run this reel's generator")
    add("check", cmd_check, "hyperframes check, printing only what needs a decision")
    sh = add("sheet", cmd_sheet, "contact sheet of the composition at chosen seconds")
    sh.add_argument("times", help="comma separated seconds")
    sh.add_argument("--out")
    sh.add_argument("--columns", default="6")
    sh.add_argument("--width", default="330")
    st = add("strip", cmd_strip, "every frame of a stretch of the rendered file")
    st.add_argument("start")
    st.add_argument("seconds")
    st.add_argument("--fps", default="30")
    st.add_argument("--columns", default="8")
    st.add_argument("--width", default="200")
    r = add("render", cmd_render, "render the composition to reel/base.mp4")
    r.add_argument("--draft", action="store_true", help="fast and rough, to reel/draft.mp4")

    sh2 = add("shots", cmd_shots, "Mechanism: render Blender shots, e.g. ./reel shots latest -- --out ../.cache/look --percent 50 --stills .5")
    sh2.add_argument("rest", nargs=argparse.REMAINDER)
    b = add("blender", cmd_blender, "Mechanism: run a Blender script against this reel")
    b.add_argument("script")
    b.add_argument("rest", nargs=argparse.REMAINDER)
    a = add("assemble", cmd_assemble, "Mechanism: frames to reel/assets/picture.mp4, then the HyperFrames project")
    a.add_argument("frames", help="frames folder, relative to reel/")

    add("mix", cmd_mix, "build the music and effects stems from reel/tools/cues.py")
    f = add("finish", cmd_finish, "the final MP4, with the voice untouched, then every delivery check")
    f.add_argument("--target", default="-16", help="loudness in LUFS")
    f.add_argument("--explore", action="store_true", help="show what each loudness would do to the voice, then stop")
    add("checks", cmd_checks, "rerun every delivery check on final.mp4")
    add("gate", cmd_gate, "does the finished reel pass? evidence, hashes, scores and limits")
    return p


def main():
    argv = sys.argv[1:]
    args = parser().parse_args(argv or ["--help"])
    if getattr(args, "rest", None) and args.rest[0] == "--":
        args.rest = args.rest[1:]
    args.fn(args)


if __name__ == "__main__":
    main()
