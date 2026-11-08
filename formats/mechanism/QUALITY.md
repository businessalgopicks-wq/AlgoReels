# Mechanism format: quality checks

Use with [DESIGN.md](DESIGN.md) and [PIPELINE.md](PIPELINE.md). This is the practical method learned from building these films, including the repairs. A renderer setting or a passing number can't establish visual quality by itself, so someone still has to look.

The tested stack was Blender 5.2 LTS, Cycles on Metal, and HyperFrames 0.9.16. Those are tested versions, not a claim that others behave identically.

## 1. Establish the inputs before animation

`reel/tools/timeline.py` is the only timeline, so derive shots, captions, sound and export timing from it. Record the versions you used, the final voice and any overlaps in `review.md`.

Before a batch, test GPU startup, one frame, scene loading, fonts, narration and the CLI. Keep API keys in `.env` and out of reports and commands. Don't run paid voice or sound generation again just to recreate an approved file.

`render_refined.py` hashes the generator files and word timing, not external assets. When a film depends on those, extend its hash list, or freeze them and say so before trusting a resume.

## 2. Prove motion and contact before the full render

Start with a 2 to 4 s preview of the hardest mechanism or contact, with a fixed camera and then the intended one. Survey every shot at low resolution. Inspect first, middle and last frames, contact entry, hold and release, and occlusions. Add a continuous low-resolution motion pass, because midpoints alone can miss a part snapping for one frame.

Save the scenes and audit every frame, not just keyed poses:

```sh
./reel blender <reel> tools/audit_objects.py -- ../qa/motion.json scenes/S01.blend scenes/S02.blend
```

Legitimate fast action can exceed a screening limit, so inspect and record it. Never raise a limit just to hide a bad move. The audit doesn't check collisions or geometry.

Render native-resolution stress frames for contact points, thin parts, contact shadows and any water. Recheck in motion after any change to geometry or timing.

## 3. Lock the look with native proofs

These settings describe the tested baseline. Use them as a starting profile, then prove noise, temporal stability, detail and readability on your film's hardest frames. Keep exposure, material response and post the same across shots.

| area | baseline | what to inspect |
| --- | --- | --- |
| Colour | AgX, Medium High Contrast, exposure +0.05 | Highlights keep detail, and don't wash out materials or water |
| Cycles | GPU, adaptive sampling, OIDN with RGB, albedo and normal. Seed 17, animated seed off | Denoising must not erase thin parts or shimmer between frames |
| Sampling | Look: 50% at 24 samples. Final: 1080 × 1920 at 32 samples, adaptive threshold 0.025, minimum 8 | Raise samples where proofs or moving reflections need it |
| Light paths | 8 total bounces, diffuse 3, glossy 4, transmission 8, volume 0, transparent 12. Indirect clamp 6, caustics off | Judge glass, water and dark interiors, which may need more |
| Motion blur | Shutter 0.28, only on shots that deliberately enable it | Blur must not hide a causal action |
| Metal | Roughness about 0.3, with subtle wear and neutral reflections | Steel reads as steel, not teal or a perfect mirror |
| Water | Roughness 0.045, two moving wave scales about 0.009 and 0.004 m, local ripples, projected caustic patterns | Surface motion, a coherent waterline, depth, wet contact and believable absorption |
| Post | `post.py`: luminance threshold 0.88, 9 px blur at 1080 width, 0.045 glow, light vignette | Keeps AgX detail |

A glossy plane alone doesn't read as water. Changing level should wet the steps, underwater absorption should keep visible depth, and a jet needs taper and movement. These are procedural approximations, so a hero splash may need another technique. Choose it by the visible action you need.

Check the chosen treatment on the same representative frames, at native and phone size. Don't tune every shot in isolation until the film loses its common look.

## 4. Freeze, render and resume

Use `./reel shots`, with one or two workers and explicit samples and resolution. Don't edit scene code or dependencies while a batch runs. Save scenes under a revision-specific folder if you'll compare them later, because `--save-scenes` overwrites `reel/scenes/`. A frame folder is immutable once accepted.

If a run stops, check the live process before launching another worker, then rerun the same frozen command. The runner validates every expected frame's dimensions and integrity, and renders only what's missing or invalid, with at most four attempts. A mismatch of source or settings means a new output folder, not deleting the old manifest.

For a correction, render only the affected shots into a new revision, such as `.cache/picture-v2`. `reel/tools/merge_revisions.py` combines revisions, later ones winning, and writes `qa/render-origins.json`. Don't turn a failed launch into an unbounded retry loop.

## 5. Assemble and check the actual delivery

Rerunning `build_hf.py` rewrites captions and the composition from its source, so change the source on purpose, then confirm the composition points to the right picture. HyperFrames checks don't examine what's inside the picture track. Keep the original word timing, caption band and mix during a picture-only repair.

`./reel checks` runs the delivery verifier against `timeline.json`, and writes frames to `qa/frames/`. Inspect frames from that exact output, not Blender proofs. Cover the opening, every shot, contact extremes, caption changes, dark transitions and the ending. Use every-frame strips around risky transitions, with `./reel strip <reel> <start> <seconds>`. The luminance scan flags possible black flashes, and an intentional dark transition needs a timestamped explanation, not automatic removal.

Watch playback and have a person listen before publishing. If either wasn't done, write `pending` rather than implying a tool completed it.

## 6. Record the decision

Use `review.md`. Each check is **pass**, **fail** or **pending**, with a timestamp or file and a stated scope. Don't average away a failure or a missed test. A corrupt file, an unsupported factual claim or an unresolved asset permission is a blocker. So is a floating required contact, an unreadable mechanism or a missed caption.

For feedback such as "everything is good except this shot", lock the approved story, voice, captions, timing and look, then repair the problem and its transitions. Avoid unrelated restyling. Acceptance of one file doesn't carry over to a later export.

## What broke, and what fixed it

| failure | cause | what held | rule for next time |
| --- | --- | --- | --- |
| Washed-out picture | Broad bloom and strong specular and fill | AgX, softer light, tiny high-luminance halation | Compare your brightest and darkest materials together before committing to a look |
| Water read as a reflective sheet | Shading without visible displacement or depth | Low waves, local ripples, wet surfaces and absorption | Prove the waterline and interaction, not just the sparkle |
| A part snapped for one frame | A procedural move stopped just as an authored key took over | A smooth transition across 12 frames | Audit every delivered frame and every handoff |
| A long render was interrupted | A long batch, with reusable frames on disk | Validate, then render only what's missing | A stopped run is no reason to rerender everything, or to trust a file count |
