---
name: reel
description: Make a finished short vertical reel in the mechanism format (a Blender 3D film explaining how something works) or the roundup format (five current projects on warm paper, with no host). Use when someone says "create me a mechanism reel", "make a roundup reel", "a 3D reel about X", "a reel about X", or asks for a video in either format.
argument-hint: "<mechanism|roundup> [topic]"
---

# Make a reel

Build the whole reel. Make routine creative choices yourself and write them down in `review.md`, rather than stopping to ask.

## 1. Understand the request

- **Format.** "3D" or "explainer" means mechanism. If no format is named, choose from the request: how something works is a mechanism reel, and new projects or tools are a roundup. If it could be either, ask once.
- **Topic.** Use what they gave you. With none, a roundup reel finds five current AI or tech projects on the web, and a mechanism reel picks something physical people are talking about this week.

## 2. Check the setup

```
./reel doctor
```

Fix what it flags, or tell the person exactly what to do. If the ElevenLabs key is missing, ask them to add it to `.env`, because a reel can't be made without it. If nothing is installed, tell them to run `./setup.sh`.

Say what to expect before starting: a roundup takes a few hours of agent work and about 1,500 ElevenLabs characters. A mechanism film also needs a long Blender render, often hours, and the machine needs to stay awake.

## 3. Start it and read the method

```
./reel new <format> "<topic>"
```

Then read, in full: `docs/METHOD.md`, `formats/<format>/DESIGN.md` and `formats/<format>/PIPELINE.md`. For mechanism, also read `formats/mechanism/QUALITY.md`. Read `.claude/skills/hyperframes/SKILL.md` before writing composition code.

## 4. Follow the pipeline to the end

Work through `PIPELINE.md` in order. `./reel status <reel>` says what's done and what's next. The starter in `reel/tools/` is a working skeleton with placeholder content, so replace all of it with this reel's own story, and don't ship a generic version of it.

A roundup reel has **no host and no avatar.** The narration carries it, and the picture is the sentence, the diagrams and the real footage.

## 5. It's done when the gate passes

```
./reel gate <reel>
```

Complete `qa/quality.json` by looking at the final file, following `docs/REVIEW.md`. Never fabricate a score or evidence, and never claim that a person listened or watched. If quality or a missing resource stops you after a bounded number of repairs, leave a `resume.md` with the commands, timings and open faults, and say what's blocking.

## 6. Hand it over

Give the path to `final.mp4`, `caption.txt` and `review.md`. Say plainly what you measured, what you only looked at, and that nobody has heard it yet, and name the moments to check. List any footage with no stated reuse licence. Remind them to turn on Instagram's AI label when posting. Don't post anything.
