# How to work on any reel

These habits apply to both formats. `CLAUDE.md` has the hard rules, a format's `DESIGN.md` decides the look, and its `PIPELINE.md` gives the steps.

## Order of work

1. **Sources and real material, then the script.** Verify each claim at its source before writing around it. What the material shows and what the check finds can make a better line than the brief.
2. **The voice, then the picture.** Time the picture from the take's real word timing, not estimates. If a take runs long, cut words. Don't choose a take because it's the shortest. Eleven v4 reads about 3 words a second.
3. **Prove the riskiest part before a full batch.** Render one difficult motion or contact, inspect it, then review representative native-size frames. A good still doesn't prove good motion.
4. **The picture locked, then the sound.**
5. **The last edit, then the final measurements.** Every number in `review.md` comes from the delivered file, so rerun `./reel checks` after any change.

## While building

- **Spoken lines are full sentences,** with no dashes in narration or captions.
- **One generator, absolute times.** Write the composition from one script, and edit that script, never its output, because the next build overwrites hand edits.
- **Freeze code and settings while rendering.** Validate outputs by integrity and dimensions, not by count. Changes go into a new revision, and earlier accepted exports stay intact.
- **Write multi-step shell work as a bash script.** zsh doesn't split `$var` into words, so loops over pairs and ffmpeg flags in a variable fail there. Bash arrays work.
- **Run heavy jobs one at a time, in the background.** Don't poll them.

## Looking at it

Tools can't tell you a film is good. Use each for what it can actually see.

| command | what it's for |
| --- | --- |
| `./reel check <reel>` | Composition errors and reading-time warnings, after each build. Fix every error and decide every warning |
| `./reel sheet <reel> <seconds>` | Stills at moments taken from the word timing. These catch what no check does: a mark off its target, a stamp covering the subject, a cursor arriving early |
| `./reel strip <reel> <start> <seconds>` | Every frame of a stretch of the rendered file, before calling a move smooth |
| `./reel checks <reel>` | Delivery report, voice integrity, effects on words, frames for review, an Instagram interface mock, and speech-to-text of the final file |
| `.venvs/earshot/bin/earshot critique <file>` | A measured read of the sound. Read `/earshot` first |

## Being honest about it

- If footage has no stated licence, say so in your handoff. That decision belongs to the person posting.
- If your cut makes something look faster or easier than its source does, say so on screen.
- If a number depends on a condition, such as the hardware, the condition stays on screen.
- In the credits, separate what was measured from what was illustrated.
- Say what was measured, sampled visually, played back and listened to. A frame strip isn't a full-speed watch, and an audio meter isn't a human listen. Keep unperformed checks pending.

## Handing it over

Deliver `final.mp4`, `caption.txt` and `review.md`. Open `review.md` with what needs the person, then the calls made without asking, what checking the sources changed, what was measured, what was only looked at, the warnings kept on purpose, and the weakest moments. Stop anything heavy you started.

Instagram asks creators to label realistic AI-made video, so remind the person to turn on the AI label when posting.
