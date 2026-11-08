# AlgoReel

**Say "create me a mechanism reel about how a zipper works" to Claude Code, and get back a finished vertical video.** It handles the research, script, voice, picture, sound and quality checks.

| | Mechanism | Roundup |
| --- | --- | --- |
| **What it is** | A 3D film that makes a mechanism obvious | A roundup of five current projects on warm paper |
| **How it looks** | Blender renders, moving camera, big captions | A sentence building word by word over real demos and diagrams |
| **On camera** | Objects only, no people | No host and no avatar |
| **Length** | 25 to 45 seconds | 45 to 59 seconds |
| **Say** | `create me a mechanism reel about how a lock works` | `create me a roundup reel about robotics` |

## What you need

- **An ElevenLabs API key.** It's required for the narration, and optionally makes sound effects and music. [Get a key](https://elevenlabs.io/app/settings/api-keys). A reel uses about 1,500 characters. The roundup voice is a Voice Library voice, so [add it to your account](https://elevenlabs.io/voices/HfRP3cIhYLmeNHeTvkWK) once.
- **[Claude Code](https://claude.com/claude-code)**, the agent that makes the reel.
- **A Mac with Apple Silicon and [Homebrew](https://brew.sh).**
- **Disk space:** about 5 GB, plus 1 to 3 GB per mechanism film while it renders.

## Install

```sh
git clone https://github.com/businessalgopicks-wq/AlgoReels.git
cd AlgoReels
./setup.sh
```

`setup.sh` installs the tools and pinned skills, asks for your ElevenLabs key, and finishes with a check that tells you exactly what's still missing. It's safe to run again.

## Make a reel

Run `claude` in the folder, then say what you want:

```
create me a mechanism reel about how a pin tumbler lock works
create me a roundup reel
create me a roundup reel about open source robotics
```

The agent works until the reel passes its quality gate, then gives you these in `reels/<date>-<format>-<topic>/`:

- `final.mp4`: 1080 × 1920, 30 fps, ready to post
- `caption.txt`: the post caption
- `review.md`: what was checked, what wasn't, and the moments you should look at yourself

**How long it takes:** a roundup reel takes hours of agent time. A mechanism film also needs a Blender render, which can take many hours on a laptop, so keep it plugged in and awake.

**Before you post, watch and listen once.** The agent measures sound and reads frames, and neither of those is hearing or watching. Nothing here posts for you.

## How it works

- **The voice is the clock.** Every caption, cut and sound is timed from the real take. The voice is never sped up or processed.
- **Sources before script.** Every claim is checked at its source, and every asset's licence is read on its own page.
- **Prove the hard part first.** The riskiest motion is rendered and inspected before the full batch.
- **The gate wants evidence.** Every check runs on the delivered MP4, and every category needs at least 8/10 with saved proof. A bad frame or false claim blocks the reel, whatever the scores say.

`./reel` runs every step, and `./reel status` tells you what's next on a reel.

## Your responsibility

You're responsible for what you publish. Use your own stories, narration and graphics, and never another creator's footage, voice, likeness or scripts. Check the facts yourself, make sure you have the right to use any footage or music that appears, and follow each platform's rules, including labelling AI-generated content. `review.md` lists any footage whose source states no reuse licence.

## Credits and licence

AlgoReel is [MIT licensed](LICENSE). Issues and pull requests are welcome.

`ig-human` and `ig-caption` are adapted from instagram-agent-skill (MIT), and keep their licence files. `setup.sh` downloads the rest from its own source at pinned versions, and none of it is committed here: [HyperFrames](https://github.com/heygen-com/hyperframes) (Apache-2.0, which can send anonymous usage events, so see its docs to turn them off), [Earshot](https://github.com/Leonxlnx/earshot) (MIT), [Blender](https://www.blender.org/) (GPL), FFmpeg and whisper.cpp. Voices come from [ElevenLabs](https://elevenlabs.io/) and free media search from [Openverse](https://openverse.org/).
