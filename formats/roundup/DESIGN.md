# Roundup format: the look

A roundup of five current projects, built from one repeating unit: **a sentence plus a diagram that changes.** The headline develops word by word, a physical diagram or real software demo develops with it, and visible proof comes before a concrete closing ask. There's no host and no avatar. The space a presenter would use goes to bigger pictures and a lower band that does useful work.

[PIPELINE.md](PIPELINE.md) is the working order. The numbers below are defaults to adjust against what you see, not recovered settings from anyone's project.

## Rules every reel keeps

**Open straight on the first project, then say it's one of five.** The first sentence is that project's result. No intro, no "five AI projects…" and no roadmap comes before it. Say it's one of five right after naming the project, within the first few sentences. Only the order is fixed, so write each reel's own lines. The shape looks like: *[what the first project just did, with a number]. That's [name], one of five new [things], and [a claim the viewer can test].*

**End on a spoken "Comment [keyword]" and the resource it gets them.** Make the keyword interesting, easy to type and tied to the video's central object, idea or result: ROBOT for a robot reel, WORLD for AI world models. Don't default to WORKFLOW, LINK or LINKS. The keyword and the resource are separate, so "Comment PLANE and I'll send you my workflow" works on a plane video.

- The whole line is in the narration, with the keyword shown large on screen as it's said. A caption, silent end card or "follow for more" doesn't count.
- Reserve the last 3 to 5 seconds, and more if the take needs it. Trim earlier material rather than rushing. Never speed the voice up.
- Music and effects must not mask the words, and no transition may clip the last syllable.
- Only promise what can happen. "Comment PLANE if you want my workflow" is an ask. "I'll DM it to you" needs a real delivery path behind it. If the user doesn't want a comment ask at all, end on a useful recap instead, and note that in `review.md`.

**Under one minute, always.** A roundup runs 45 to 59 seconds. At about 3 words a second on Eleven v4, write 150 to 160 spoken words, which lands near 52 to 55 seconds. Measure the real take before building on it. If it runs long, cut words and generate again.

## What the picture is

Three layers, always:

1. **The sentence.** One to three left-aligned lines in sentence case. A black sans carries it, and a narrow red italic serif marks the words that matter. Several words can be emphasized together. Incoming words appear pale for a moment, then settle.
2. **The explanation.** A large object or relationship in the middle: a project's real footage in an outlined card, a phone, a graph, a calendar, a terminal. Small stamps, arrows and chips give it a sequence.
3. **The lower band.** A strip of five project tiles with a counter on the left, and a small fact card on the right: who made the project on screen, when, and one key fact. It's never empty and never decoration.

The canvas is textured warm paper with generous space above the main diagram. Objects are layered, rotated, outlined and shadowed. Browser and terminal mockups sit comfortably next to illustrated physical objects.

## Defaults

| system | starting value |
| --- | --- |
| Canvas | 1080 × 1920 at 30 fps. Paper #F1EFEA with subtle grain and a dot grid |
| Ink and accent | Ink #111111, red #F84018 |
| Headline | Inter 600 at 82 px, line height 91 px. Instrument Serif Italic at 94 px for emphasis. Fit by line breaks before shrinking |
| Headline position | Left 132 px, top 252 px, maximum width about 816 px |
| Phase label | JetBrains Mono 500, 24 px at x132, y128. A concise name for the phase, with the source on the right |
| Display type | Anton, typically 100 to 130 px, for a diagram heading or verdict, not the narration |
| Explanatory area | y552 to y1340. White cards, 2 to 4 px outlines, offset or halftone shadow |
| Lower band | y1358 to y1540 |
| Sound | True peak at or below −2 dBTP, and as loud as the limiter allows while barely touching the voice. Start at −16 LUFS |

## Layout

- Give the headline its own space. Don't lay a second caption over it.
- Build one relationship at a time: folder to contents, prompt to example, step to completed state, claim to proof. A diagram can stay across several headline phrases.
- Keep useful context while changing the important part. Highlight a task without replacing the whole terminal, and roll a number inside a stable card.
- Use physical metaphors when they explain the claim: a calendar for time, a crowd for competition, a maze for a path, a balance for a comparison.
- Use red for emphasis, a selected state and a verdict.
- Draw circles, arrows, brackets and stamps to direct attention. Avoid marks that compete with the noun being explained.
- The first frame is the thumbnail, so check it on its own. It should already show a real picture and the first word.
- Check everything against Instagram's interface with `./reel checks`, which writes `qa/frames/instagram_mock.jpg`.

## Motion

| behaviour | recipe |
| --- | --- |
| Headline | Reveal by word with a 1 to 2 frame fade, from the voice's real timing. The first word is on screen at frame 0 |
| Cards | Enter over about 8 to 14 frames with some rotation and a small overshoot. Hold supporting objects while a new detail arrives |
| Counter | Roll digits over about 0.8 to 1.2 s, then settle before the next beat. Use real, sourced numbers |
| Software demo | Type the input, move a visible cursor, highlight the control, then show the result. Sync the named object to the narration |
| Scene change | Prefer keeping context during a demonstration. A hard cut can establish a new world, and a dot wipe marks a bigger turn. Start dot wipes around 10 to 16 frames |
| Verdict | A circle, crossed-out object or stamped word, with room to land. A stamp: a faint ghost at about 2.2× for one frame, then a hit to full size over about two |
| The ask | The keyword typed into a comment field, landing as big keycaps as it's spoken, with a card showing what they'd get. Show delivery only when delivery is real |

Don't force constant movement on every layer. Alternate entry, reveal, attention shift and settle.

## Ideas that have worked

Weigh these against each topic. They aren't a checklist.

- **A claim the viewer can test.** Checking the sources might show that three of the five can be run today. A counter then carries that claim through the reel, so each project moves something.
- **Real material, chosen by watching it.** Each project's own footage in an outlined card, with the lines written around what it actually shows.
- **The picture changes on the word.** A divider wipes on "into this", digits roll to the number as it's said, a photo drops on "one photo".
- **Caveats as part of the design.** WAITLIST, CODE COMING LATER and "demo shortened" stamps make the honesty readable, and they give the verdict marks a real job.
- **Objects that carry over.** The first frame's picture becomes a tile in the strip, so one idea leads into the next.
- **Sound with a cause.** Each effect answers something on screen, such as a stamp landing or a counter's pops rising in pitch as it climbs.

## Story shapes

- **Roundup, five entries (the default).** Open on the first project's result, then say it's one of five. Each project gets its purpose, one demonstration and an updated number or check. Spend more time on the strongest. Finish with the ask.
- **Single-project deep dive, when the user names one project.** Show the result first, say what it does, type a concrete input, reveal the output step by step, explain a limit, then the ask. Cite the source and any performance evidence, plus the repo and licence if there is one.
- **Claim and proof.** A supported claim, why it matters now, visible proof, the mechanism made physical, one usable example, then the ask. Never assert a market deadline as fact without evidence.

## Write in this voice

Direct, talking to "you". The number and the stake go in the first sentence. In a roundup that's the first project's own number, not the count of five. A warning with a condition works (don't start this until you've done that), and "stop" only works with a stake. The picture proves each claim as it's said.

Vary the sentence shapes, and write lines someone would say out loud. Same-shaped sentences read flat even with a good voice, so treat `/ig-human`'s sentence-length flag as a warning to act on. Spoken lines stay full sentences, because clipped ones sound machine-made.

Tell it straight about what can and can't run. If a project needs four graphics cards, say so. If the code isn't out, say so.

## The voice

ElevenLabs voice ID `HfRP3cIhYLmeNHeTvkWK`, on Eleven v4, with no other settings sent. It's a Voice Library voice, so add it to your account once at <https://elevenlabs.io/voices/HfRP3cIhYLmeNHeTvkWK>. `./reel doctor` tells you if your account can't reach it, and how to switch.

- **Never speed it up,** and don't choose a take because it's the shortest. That picks the most rushed read.
- **Leave it alone in the edit.** No gain rides, compression, EQ or normalizing on the voice. `./reel finish` gives it one fixed gain, and a peak limiter on the finished sum is the only thing that can touch it. If a take fades or sounds wrong, change the take, not the audio.
- **Names:** if the voice gets one wrong, respell it in `narration.txt` and keep the real spelling on screen with `screen.txt`. See [PIPELINE.md](PIPELINE.md).

## Rights

Everything published is your own: original narration, cards, diagrams and sound. Never use another creator's frames, voice, likeness, scripts or personal numbers. A project's own footage can appear with its credit, and when its page states no licence for that media, say so in `assets/CREDITS.md` and in your handoff. That decision belongs to the person posting.
