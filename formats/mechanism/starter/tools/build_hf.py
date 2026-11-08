"""Write the HyperFrames project: one picture track, the narration, the captions and any on-screen notes, timed from the voice.

Run by ./reel assemble, or on its own with ./reel build. It overwrites index.html and compositions/, so edit this file, never its output.
"""
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from timeline import DURATION, FPS, TIMES  # noqa: E402

post = HERE.parents[1]
reel = post / "reel"
(reel / "compositions").mkdir(exist_ok=True)
words = json.loads((post / "assets/source/voice/words.json").read_text())
DUR = DURATION

# Caption chunks, two to five words each, broken where a person would pause. None groups them automatically, and a hand-written list
# of strings wins when the automatic breaks read badly. Written lists must add up to the narration, word for word.
CHUNKS = None
# Sourcing notes and honest caveats on screen, as (text, start, end). Every value belongs in script.md's sources.
NOTES = [
    # ("Simplified animation of the published motion", 14.70, 18.70),
]


def auto_chunks(items, longest=5):
    chunks, current = [], []
    for w in items:
        current.append(w["w"])
        if len(current) >= longest or (len(current) >= 2 and re.search(r"[,.!?;:]$", w["w"])):
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    return chunks


groups, i = [], 0
for chunk in CHUNKS or auto_chunks(words):
    n = len(chunk.split())
    seg = words[i:i + n]
    if [w["w"] for w in seg] != chunk.split():
        raise SystemExit(f"Caption chunk doesn't match the narration here: {chunk!r} against {[w['w'] for w in seg]}")
    groups.append((chunk, seg[0]["s"], seg[-1]["e"]))
    i += n
if i != len(words):
    raise SystemExit(f"The captions cover {i} words, and the narration has {len(words)}.")

html = []
for k, (text, start, end) in enumerate(groups):
    following = groups[k + 1][1] if k + 1 < len(groups) else DUR
    lead = 0.03  # hold into a following gap, and never overlap the next chunk
    stop = min(following - lead, end + 0.45) if following - end > 0.2 else following - lead
    a = max(0.0, start - lead)
    html.append(f'<div class="cap clip" id="c{k}" data-start="{a:.3f}" data-duration="{stop - a:.3f}" data-track-index="2">{text.rstrip(",.")}</div>')
caps = f"""<template>
<style>
@font-face{{font-family:CaptionBold;font-weight:700;src:url('assets/fonts/caption-bold.ttf') format('truetype');}}
#root{{position:absolute;inset:0;font-family:CaptionBold,sans-serif;}}
.cap{{position:absolute;left:0;width:1080px;top:1451px;text-align:center;font-weight:700;font-size:74px;line-height:92px;color:#fff;
  letter-spacing:.002em;white-space:nowrap;-webkit-text-stroke:5px rgba(0,0,0,.92);paint-order:stroke fill;
  text-shadow:1px 3px 5px rgba(0,0,0,.75);}}
</style>
<div id="root" data-composition-id="captions" data-width="1080" data-height="1920" data-start="0" data-duration="{DUR}" data-layout-allow-caption-zone data-layout-allow-overlap>
{chr(10).join(html)}
</div>
<script>window.__timelines["captions"]=gsap.timeline({{paused:true}});</script>
</template>
"""
(reel / "compositions/captions.html").write_text(caps)

note_html = "\n".join(f'<div class="note clip" id="n{k}" data-start="{a}" data-duration="{b - a:.2f}" data-track-index="3"><span>{text}</span></div>' for k, (text, a, b) in enumerate(NOTES))
note_js = "\n".join(f"tl.fromTo('#n{k} span',{{opacity:0,y:10}},{{opacity:1,y:0,duration:.18,ease:'power2.out'}},{a});tl.to('#n{k} span',{{opacity:0,duration:.12}},{b - .12:.2f});" for k, (text, a, b) in enumerate(NOTES))
notes = f"""<template>
<style>
@font-face{{font-family:CaptionBold;font-weight:700;src:url('assets/fonts/caption-bold.ttf') format('truetype');}}
#root{{position:absolute;inset:0;font-family:CaptionBold,sans-serif;}}
.note{{position:absolute;left:0;width:1080px;top:168px;text-align:center}}
.note span{{display:inline-block;background:rgba(10,14,18,.78);color:#fff;font-weight:700;font-size:36px;line-height:50px;padding:6px 22px;border-radius:12px;white-space:nowrap}}
</style>
<div id="root" data-composition-id="notes" data-width="1080" data-height="1920" data-start="0" data-duration="{DUR}" data-layout-allow-overlap>
{note_html}
</div>
<script>(function(){{var tl=gsap.timeline({{paused:true}});{note_js}
window.__timelines["notes"]=tl;}})();</script>
</template>
"""
(reel / "compositions/notes.html").write_text(notes)

narration = reel / "assets/audio/narration.mp3"
audio_length = words[-1]["e"] + 0.3
if narration.exists():
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(narration)], capture_output=True, text=True)
    audio_length = float(probe.stdout.strip() or audio_length)
audio_length = min(audio_length, DUR)
index = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>*{{margin:0;padding:0;box-sizing:border-box;}}html,body{{margin:0;width:1080px;height:1920px;overflow:hidden;background:#000;}}#root{{width:100%;height:100%;}}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920" data-fps="{FPS}">
<video id="picture" class="clip" data-start="0" data-duration="{DUR}" data-track-index="1" muted playsinline src="assets/picture.mp4" style="position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover"></video>
<div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{DUR}" data-track-index="2" data-track-kind="captions" data-width="1080" data-height="1920"></div>
<div id="notes" data-composition-id="notes" data-composition-src="compositions/notes.html" data-start="0" data-duration="{DUR}" data-track-index="3" data-track-kind="graphics" data-width="1080" data-height="1920"></div>
<audio id="narration" class="clip" data-start="0" data-duration="{audio_length:.3f}" data-track-index="10" data-volume="1" src="assets/audio/narration.mp3"></audio>
</div>
<script>window.__timelines=window.__timelines||{{}};window.__timelines["main"]=gsap.timeline({{paused:true}});</script>
</body>
</html>
"""
(reel / "index.html").write_text(index)
starts = sorted(start for start, _ in TIMES.values())[1:]
(reel / "timeline.json").write_text(json.dumps({"duration": DUR, "fps": FPS, "cuts": [round(s, 2) for s in starts]}, indent=1) + "\n")
print("captions", len(groups), "duration", DUR)
