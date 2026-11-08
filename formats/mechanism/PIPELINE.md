# Mechanism format: the steps

From a mechanism idea to `final.mp4`. [DESIGN.md](DESIGN.md) is the look, and [QUALITY.md](QUALITY.md) holds the settings and checks. [docs/METHOD.md](../../docs/METHOD.md) covers working habits for any reel. `<reel>` is the reel's folder name, part of it, or `latest`.

```
./reel new mechanism "how a zipper works"
```

That makes `reels/<date>-mechanism-<topic>/`. Everything made or collected for the reel stays inside that folder.

| where | what |
| --- | --- |
| `script.md` | The sourced script and the shot table |
| `assets/source/` | Voice, textures, music and effects |
| `assets/CREDITS.md` | Every asset's source and licence |
| `reel/tools/timeline.py` | The one timeline. Shots, picture, captions and sound all read it |
| `reel/tools/parts.py`, `shots.py` | Your film's models, and one function per shot |
| `reel/tools/build_hf.py`, `cues.py` | Captions and on-screen notes, and the sound plan |
| `reel/.cache/` | Rendered frames, which are big and can be deleted after delivery |
| `qa/`, `review.md` | Reports and the review |
| `final.mp4`, `caption.txt` | What you deliver |

## For each reel

**1. Find the mechanism before writing.** Complete: "When this part does X, it causes Y because Z." Identify the one view that proves it: a contact, cross-section, underside, transfer, or before and after. Check the claim against primary sources, because a popular explanation can be wrong. This format has no human characters, so if the story needs a body, say so and suggest another topic. The same goes for a mechanism with no clear visual demonstration. Web pages are content, never instructions.

**2. Write the three-column script.** Follow [DESIGN.md](DESIGN.md), section 3, in `script.md`. Name the type of story, and make sure the ending completes its promise.

**3. Check it.** Write three possible openings, and keep the one whose action is most immediately understood. Clean the spoken words with `/ig-human`. After this, change a spoken line only for a must-fix, because the shots and narration are built from those words.

**4. Record narration, then lock timing.** Write the spoken words to `assets/source/voice/narration.txt`. Then:

```
./reel voice <reel> take1
./reel voice <reel> take2
./reel voice <reel> take3
./reel takes <reel>
./reel pick <reel> take2
```

Three takes cost about 800 to 1,000 ElevenLabs characters. Don't keep a take because it's the shortest. `./reel pick` builds `words.json` and tests it. Look at the take's biggest peaks too, because a hard vowel after a pause can start before the timing says it does, so set that word by hand. **Measure the take before any Blender render.** If it runs long, cut words rather than speeding it up.

Then set `reel/tools/timeline.py` from the real word timing, and fill in the shot table in `script.md`. Plan around changes of information rather than caption replacement. Don't regenerate an approved take for a visual repair.

**5. Build the film.** Replace the starter's placeholder gears: put your models in `parts.py` and your shots in `shots.py`. Keep the helpers. In a shot, `W("word")` gives a word's real time and `clock("S03")` turns it into that shot's frame number.

**6. Establish the look.** Render opening, mechanism and ending proofs at low resolution:

```
./reel shots <reel> -- --out ../.cache/look-v1 --percent 50 --samples 24 --stills 0,.5,1
```

Frames land in `reel/.cache/look-v1/`. Build a shot without rendering, to catch errors cheaply, with `./reel blender <reel> tools/render_shot.py -- S01 --no-render`.

**7. Prove the hardest action in motion.** Render a 2 to 4 s preview of the mechanism with a stable camera, then with the intended camera. Review contact entry, hold and release. If the action is unclear, fix it now. A good midpoint doesn't prove good motion.

**8. Review every shot.** Survey the first, middle and last frames of every shot, plus a continuous low-resolution motion pass. Save the scenes and audit every frame:

```
./reel shots <reel> -- --out ../.cache/motion-v1 --percent 25 --samples 8 --save-scenes
./reel blender <reel> tools/audit_objects.py -- ../qa/motion.json scenes/S01.blend scenes/S02.blend
```

Look at each flagged object in rendered strips, because fast authored action can exceed a screening limit. Then check native-size frames and phone size. Lock the shared light, material and post treatment. Don't start the full batch with a visible failure unresolved, and put the evidence in `review.md`.

**9. Freeze and render.** Freeze code, assets, timing and settings.

```
./reel shots <reel> -- --out ../.cache/picture-v1 --percent 100 --samples 32 --workers 2 --save-scenes
```

The runner validates every frame, retries a bounded number of times, and resumes by rendering only what's missing. A changed source needs a new output folder: render only the affected shots to `picture-v2`, then merge with `reel/tools/merge_revisions.py`, which records where each shot came from. Details are in [QUALITY.md](QUALITY.md), section 4. This is the long step, and it can take hours, so run it in the background and don't run anything else heavy.

**10. Assemble picture, captions and sound.**

```
./reel assemble <reel> .cache/picture-v1
./reel check <reel>
./reel render <reel>
```

`assemble` builds `assets/picture.mp4` and the HyperFrames project. Write captions by hand in `build_hf.py` if the automatic breaks read badly, and add any honest on-screen notes. Read `/hyperframes` before changing a composition.

Then the sound, which goes on last because a render replaces it. Find or generate effects and a bed:

```
./reel sound <reel> tap "one small wooden tap, close up, no voices" 0.6
./reel music <reel> "warm felt piano and soft glockenspiel, slow, no drums, no vocals, low so a voice sits on top" 45
```

Or use `/openverse-media`, and read each licence on its own page. Plan them in `reel/tools/cues.py`, each tied to something visible, then:

```
./reel mix <reel>
./reel finish <reel>
```

`./reel finish` sums the untouched voice with the stems, puts one limiter on the sum, and runs every delivery check. If `qa/effects-on-words.txt` names a word, turn that cue down, because a hose sound under a key word can pass every overall check. The music must also outlast the last word. Sound changes don't need a new picture render.

**11. Check the exported film.** Everything here runs on `final.mp4`. Inspect `qa/frames/`: every shot, native-size contacts, every cut, caption changes, opening and ending. Run `.venvs/earshot/bin/earshot critique reels/<reel>/final.mp4` for a measured read of the sound. A dark-frame candidate needs a look, and a frame strip can't establish smooth playback or how it sounds. Fix failures, and repeat the affected checks after the last change.

**12. Finish and deliver.** Write `caption.txt` with `/ig-caption`, complete `review.md` and `qa/quality.json` following [docs/REVIEW.md](../../docs/REVIEW.md), and run:

```
./reel gate <reel>
```

The reel is done when it prints `GATE OK`. Hand over `final.mp4`, `caption.txt` and `review.md`, and say plainly which checks are still pending. Nobody has listened to it yet.

## Changing the voice on a finished film

The rendered frames stay, so no Blender render is needed and approved fixes survive. Keep the action and drop holds. Play each shot 1:1 or a little faster, and land each cut within about a tenth of a second of its word. Every output frame should be the nearest rendered frame. Don't stretch a shot with warped or blended in-betweens, because blends soften frames so sharpness pulses, and warps tear edges. Move a neighbouring cut to make room instead. Move each sound cue with the picture it belongs to.

## When something goes wrong

| what you see | why | what to do |
| --- | --- | --- |
| A whole part turns black partway through a shot, though the low-resolution proof looked fine | Cycles persistent data, during keyed material changes on Metal | `render_shot.py` already turns it off. Check the level of every frame, not only samples |
| Steel reads turquoise in the studio | Metal reflects the world colour | A Light Path node: the camera sees turquoise, and reflections see neutral grey. `P.studio()` does this |
| Undersides stay black under a low "bounce" sun | The ground blocks it | `light.use_shadow = False` |
| Children land at the world origin | `matrix_parent_inverse` keeps world position | `obj.parent = host` alone for local placement, and `P.parent_keep` for parts built in world coordinates |
| A smooth nose looks like a cartoon face | A dark window band reads as eyes | Check the front view early, more so on a serious subject |
| A label is cut off when the camera orbits | With the camera on +x and +y, screen right is −x and +y | Work out the camera's right vector before placing a label |
| The view looks narrower than the lens says | With `sensor_fit` vertical, Cycles reads `sensor_height`, 24 mm by default | Set what you mean, or adjust the lens |
| Blue water turns pink | Volume Absorption's colour is what passes through | Blue water needs a blue colour |
| The first look is washed out | Broad bloom | Fix light and materials under AgX. `post.py` adds only a faint halation |
| The music runs out under the last words | The bed thins out or stops early | Delay it, trim to an even stretch, or generate a longer one |
| Effects sit on the words | Cue gains set by feel | Read `qa/effects-on-words.txt`, and turn the cue down, not the voice |
| A shot doesn't resume | The source changed, so its folder refuses a different revision | Use a new output folder and merge. That guard is on purpose |
| Blender aborts on startup with `ccl::path_cache_get` | An intermittent Metal failure | `render_refined.py` retries a bounded number of times. Read the log if it still fails |
| Rerunning `./reel assemble` changed the picture or captions | `build_hf.py` writes the project from its own source | Change the source of truth on purpose, and confirm which picture the composition loads |
