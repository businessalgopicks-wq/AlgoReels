# Reviewing a finished reel

`./reel gate <reel>` decides whether a reel is finished. It needs **8/10 in every category,** not an average, and every required check complete with saved evidence.

The gate checks the record, not the film. It can confirm that the file is right and that a review exists for that exact file, but it can't see a broken model or hear a clipped word. A bad claim, an unreadable caption, a corrupt file or an audible defect blocks a reel whatever its scores say, so put those under `blocking_issues`, then fix them and repeat the affected checks.

Don't just fill each score with 8. Explain why it earns that score, name its weakest moment, and link the evidence.

## Fill in `qa/quality.json`

`./reel new` writes the template. Complete it after inspecting the final file.

- `sha256`: the final MP4's exact hash, from `qa/final-sha256.txt`. A later edit invalidates the review, so the gate will send you back.
- `reviewer` and `reviewed_at`: who reviewed it, and when, with a timezone.
- `scores`: a score, a concrete rationale and evidence paths inside the reel's folder, for each category.
- `checks`: `status`, `evidence` and `notes` for each. Evidence files must exist and not be empty.
- `blocking_issues`: must be empty for the reel to pass.
- `human_listening` and `human_playback`: leave these as `not performed` unless a person really did it. Never claim them.

| category | what it covers |
| --- | --- |
| `story` | A strong opening, a coherent explanation and a useful ending. In roundup, five distinct entries, the opening order and the spoken ask. In mechanism, one clear mechanism |
| `source_accuracy` | Every factual line is supported by a primary source, with dates and limits verified |
| `design_fidelity` | Matches the format's `DESIGN.md`, using original story material |
| `visual_quality` | Legible at phone size, a clean composition, convincing contact, good materials |
| `motion` | Clear causality, smooth transitions, no hidden cuts, frame jumps or floating contact |
| `captions` | Exact words and spelling, accurate timing, readable dwell time, platform-safe placement |
| `audio` | Clear pronunciation, a conversational voice, well-balanced licensed sound, intentional sync |

| check | what to save |
| --- | --- |
| `sources` | Each claim checked at its source |
| `asset_rights` | `assets/CREDITS.md` |
| `frame_review` | Timestamps inspected, in `qa/visual-review.md`, plus `qa/frames/` |
| `transitions` | Strips around each cut, from `qa/frames/` |
| `caption_review` | Frames and `qa/final-speech-to-text.txt` read against the script |
| `audio_review` | `earshot critique` output, saved to `qa/` |
| `mix_levels` | `qa/sound-finish.json`, `qa/effects-on-words.txt` |
| `voice_integrity` | `qa/voice-integrity.json` |

**Roundup also needs:**

- `opening_order`: `notes` quote the opening sentences as spoken, showing where the first project is named and where it's called one of five.
- `closing_ask`: `notes` give the exact last line, why the keyword fits, and its start and end timestamps in the final file. Check that the words are clear and nothing is cut off.

**Mechanism also needs:**

- `mechanism`: the proof that the action explains the claim.
- `motion_continuity`: the every-frame audit, `qa/motion.json`.

## What the gate checks by itself

- `final.mp4` is 1080 × 1920, 30 fps, H.264 yuv420p with AAC.
- It runs under a minute, and inside the format's range: Roundup 45 to 59 s, mechanism 25 to 45 s.
- `qa/delivery.json` and `qa/voice-integrity.json` describe that exact file.
- The voice's gain varies by at most 2 dB between sentences. An untouched voice typically varies under 1 dB, and a heavily processed one can reach 8 or 9. Fix a failure by changing the take or the mix, never by riding the voice.
- `caption.txt` and `assets/CREDITS.md` aren't empty.

## Sound

Loudness and true peak are measurements. An embedding score isn't a listening pass or proof of natural pronunciation. When Earshot recommends a louder master or flatter dynamics, weigh that against the voice rule, and say in `review.md` what you declined.

A listening and full-speed playback pass by a person remains the last step before posting. This review doesn't replace it.
