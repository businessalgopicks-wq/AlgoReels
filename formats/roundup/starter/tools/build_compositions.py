"""Write index.html and compositions/*.html for this reel. Run with ./reel build. Edit this file, never its output.

Everything that belongs to this reel is in THIS REEL, just below. The placeholder content shows the shape, so replace all of it, and
PHRASES must match the narration word for word. The generic project scene is a floor: give each project one moment of its own, built
from what its footage actually shows.

Every time is absolute seconds from the voice: W("word") is when that word starts.
"""
import json
import math
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMP = ROOT / "compositions"
COMP.mkdir(exist_ok=True)
WORDS = json.loads((ROOT.parent / "assets/source/voice/words.json").read_text())
if not (ROOT / "assets/stills/paper.jpg").exists():
    subprocess.run([sys.executable, "tools/make_textures.py"], cwd=ROOT, check=True)


def W(word, occ=0):
    """When a spoken word starts. occ picks a later occurrence, counting from 0."""
    hits = [w["s"] for w in WORDS if w["w"].strip(",.!?:;").lower() == word.lower()]
    if occ >= len(hits):
        raise SystemExit(f'"{word}" (occurrence {occ}) is not in words.json. It has it {len(hits)} time(s).')
    return hits[occ]


# ================================================================ THIS REEL ================================================================
# The headlines. Together they must be the on-screen script, word for word. *word* is the red serif and | is a line break.
PHRASES = [
    "A *small lab* just|shipped a *robot hand*",
    "that picks up *eggs*|without breaking them.",
    "That's *Project One,*|one of *five* new",
    "projects this week,|and *three* run at home.",
    "*Project Two* turns|one photo into a *room*",
    "you can walk through|in under a *minute.*",
    "*Project Three* writes|its own tests, and",
    "fixes the code when|one of them *fails.*",
    "*Project Four* reads|a page of *handwriting*",
    "and hands it back|as a *clean table.*",
    "*Project Five* looks|the most *impressive,*",
    "but the code|*isn't out yet.*",
    "Comment *HANDS,* and|see *all five* for yourself.",
]
# Each project, in order. first: the word its name starts on. One may set stamp=("TEXT", word), chip=("text", word), typed=("prompt text", word).
PROJECTS = [
    dict(id="p1", name="Project One", first="Project", occ=0, source="example.com", who="A small lab", when="Nov 2026", fact="runs at home", mark="tick"),
    dict(id="p2", name="Project Two", first="Project", occ=1, source="example.org", who="A university", when="Nov 2026", fact="runs at home", mark="tick", typed=("one photo of a kitchen", "photo")),
    dict(id="p3", name="Project Three", first="Project", occ=2, source="example.net", who="A startup", when="Nov 2026", fact="open licence", mark="tick"),
    dict(id="p4", name="Project Four", first="Project", occ=3, source="example.com", who="A research team", when="Nov 2026", fact="cloud only", mark="none", chip=("demo shortened", "handwriting")),
    dict(id="p5", name="Project Five", first="Project", occ=4, source="example.org", who="A big lab", when="Nov 2026", fact="no code yet", mark="lock", stamp=("WAITLIST", "isn't")),
]
COUNTER = ("RUN IT AT HOME", 3)  # the claim the reel keeps score of, or None. The number must come from your sources.
ONE_OF_FIVE = ("five", 0)  # the word where it says it's one of five. The strip of five tiles arrives on it.
KEYWORD = "HANDS"  # interesting, easy to type and tied to this reel's subject. Not WORKFLOW, LINK or LINKS.
ASK_STARTS_ON = ("Comment", 0)  # the first word of the closing ask
HOLD_AFTER_LAST_WORD = 0.7  # seconds on the closing card after the voice ends
# =============================================================================================================================================

INK, RED, PALE, PAPER = "#111111", "#F84018", "#C9C6BE", "#F1EFEA"
TOTAL = math.ceil((WORDS[-1]["e"] + HOLD_AFTER_LAST_WORD) * 30) / 30
ASK = W(*ASK_STARTS_ON)
WIPE_AT = ASK - 0.28  # the dot wipe covers the change of scene
STARTS = [0.0 if i == 0 else W(p["first"], p.get("occ", 0)) for i, p in enumerate(PROJECTS)]
ENDS = STARTS[1:] + [WIPE_AT + 0.3]
TILE_W, TILE_H, TILE_GAP, TILE_X, TILE_Y = 94, 66, 8, 66, 1368

FONT_CSS = """
@font-face{font-family:'ReelSans';src:url('assets/fonts/Inter-600.woff2') format('woff2');font-weight:600}
@font-face{font-family:'ReelSerif';src:url('assets/fonts/InstrumentSerif-Italic.woff2') format('woff2');font-style:italic}
@font-face{font-family:'ReelDisplay';src:url('assets/fonts/Anton-400.woff2') format('woff2')}
@font-face{font-family:'ReelMono';src:url('assets/fonts/JetBrainsMono-500.woff2') format('woff2');font-weight:500}
"""

SHARED_CSS = FONT_CSS + """
.obj{position:absolute}
.ht{position:absolute;inset:16px -16px -16px 16px;border-radius:24px;background-image:radial-gradient(#111 34%,transparent 36%);background-size:9px 9px}
.card{position:absolute;inset:0;background:#fff;border:4px solid #111;border-radius:24px;overflow:hidden}
.badge{position:absolute;width:88px;height:88px;background:#111;color:#fff;border-radius:18px;font-family:'ReelDisplay';font-size:60px;line-height:88px;text-align:center}
.anton{font-family:'ReelDisplay';color:#111;line-height:1;white-space:nowrap}
.mono{font-family:'ReelMono';font-weight:500;color:#111;white-space:nowrap}
.chip{position:absolute;background:#fff;border:3px solid #111;border-radius:14px;padding:12px 20px;font-family:'ReelMono';font-weight:500;font-size:30px;color:#111;white-space:nowrap}
.chip.dark{background:#111;color:#fff}
.stamp{position:absolute;color:#F84018;border:9px solid #F84018;border-radius:12px;padding:10px 26px 6px;font-family:'ReelDisplay';white-space:nowrap;line-height:1.06;
 -webkit-mask-image:url('assets/stills/grunge.png');mask-image:url('assets/stills/grunge.png');-webkit-mask-size:100% 100%;mask-size:100% 100%;outline:4px solid #F84018;outline-offset:6px}
.roll{display:inline-block;overflow:hidden;vertical-align:top}
.roll>.col{display:block}
.roll>.col>span{display:block;text-align:center}
.tick{position:absolute;width:92px;height:92px}
video{position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover}
"""

TICK = ('<svg viewBox="0 0 92 92" width="100%" height="100%"><circle cx="46" cy="46" r="42" fill="#F84018" stroke="#111" stroke-width="4"/>'
        '<path d="M26 47l14 14 27-30" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/></svg>')
LOCK = ('<svg viewBox="0 0 92 92" width="100%" height="100%"><circle cx="46" cy="46" r="42" fill="#8d8a83" stroke="#111" stroke-width="4"/>'
        '<rect x="28" y="42" width="36" height="26" rx="5" fill="#fff"/><path d="M34 42V33a12 12 0 0 1 24 0v9" fill="none" stroke="#fff" stroke-width="7"/></svg>')
MARKS = {"tick": TICK, "lock": LOCK, "none": ""}

STAMP_JS = """
function stamp(sel,at,rot,big){
  tl.fromTo(sel,{opacity:0,scale:big||2.2,rotation:rot},{opacity:.45,scale:(big||2.2)*.82,rotation:rot,duration:.04,ease:'none'},at);
  tl.to(sel,{opacity:1,scale:1,duration:.07,ease:'power4.in'},at+.04);
}
function pop(sel,at,dur,from){
  tl.fromTo(sel,{opacity:0,scale:from||.6},{opacity:1,scale:1,duration:dur||.28,ease:'back.out(2.2)'},at);
}
"""


def scene(cid, css, body, script):
    """A sub-composition file. Everything sits inside <template>."""
    return f"""<template>
<style>
#root{{position:absolute;inset:0;overflow:hidden}}
{SHARED_CSS}
{css}
</style>
<div id="root" data-composition-id="{cid}" data-width="1080" data-height="1920">
{body}
</div>
<script>
(function(){{
var tl=gsap.timeline({{paused:true}});
{script}
window.__timelines["{cid}"]=tl;
}})();
</script>
</template>
"""


def roller(cid, digits, h, size, width):
    """A rolling digit column. digits is the sequence from first to last."""
    spans = "".join(f"<span style='height:{h}px;line-height:{h}px'>{d}</span>" for d in digits)
    return (f"<span class='roll' data-layout-ignore style='height:{h}px;width:{width}px;font-size:{size}px'>"
            f"<span class='col' id='{cid}'>{spans}</span></span>")


def card_shell(obj_id, x, y, w, h, inner, extra=""):
    return (f"<div class='obj' id='{obj_id}' style='left:{x}px;top:{y}px;width:{w}px;height:{h}px;{extra}'>"
            f"<div class='ht'></div><div class='card'>{inner}</div></div>")


def picture(p, w, h):
    """The project's footage. With no clip yet, a labelled stand-in, so the layout still reads."""
    clip = ROOT / f"assets/clips/{p['id']}.mp4"
    if clip.exists():
        return None
    return (f"<div style='position:absolute;inset:0;background:repeating-linear-gradient(135deg,#ECE9E1 0 34px,#E2DED4 34px 68px)'>"
            f"<div class='anton' style='position:absolute;left:0;right:0;top:{h / 2 - 48:.0f}px;text-align:center;font-size:88px;color:#8d8a83'>{p['name']}</div></div>")


def thumb(p, w, h):
    still = ROOT / f"assets/stills/thumb_{p['id']}.jpg"
    if still.exists():
        return f"<img src='assets/stills/thumb_{p['id']}.jpg' alt='' style='position:absolute;inset:0;width:100%;height:100%;object-fit:cover'/>"
    return f"<div style='position:absolute;inset:0;background:repeating-linear-gradient(135deg,#ECE9E1 0 10px,#E2DED4 10px 20px)'></div>"


# ---------------------------------------------------------------- the headline, word by word
def build_captions():
    labels = [(STARTS[i], ENDS[i], f"// {i + 1:02d} · {p['name'].lower()}", p["source"]) for i, p in enumerate(PROJECTS)]
    labels.append((WIPE_AT + 0.3, TOTAL, f"// comment {KEYWORD}", ""))
    body, script, i, starts = [], [], 0, []
    for phrase in PHRASES:
        n = len(re.findall(r"\S+", phrase.replace("|", " ")))
        if i >= len(WORDS):
            raise SystemExit(f"PHRASES has more words than words.json, at: {phrase}")
        starts.append(WORDS[i]["s"])
        i += n
    if i != len(WORDS):
        raise SystemExit(f"PHRASES has {i} words and words.json has {len(WORDS)}. They must be the same script.")
    i = 0
    for pi, phrase in enumerate(PHRASES):
        start = max(0.0, starts[pi] - 0.02)
        end = (starts[pi + 1] - 0.02) if pi + 1 < len(starts) else TOTAL
        lines, in_em = [], False
        for line in phrase.split("|"):
            tokens = []
            for token in line.split():
                opens, closes = token.startswith("*"), token.endswith("*")
                text = token.strip("*")
                in_em = in_em or opens
                wid = f"w{i}"
                tokens.append(f"<span class='{'w em' if in_em else 'w'}' id='{wid}'>{text}</span>")
                t = WORDS[i]["s"]
                at = 0.0 if i == 0 else max(0.0, t - 0.02)  # the first word of the film is on screen at frame 0
                color = RED if in_em else INK
                first_color = (INK if i == 0 else PALE) if not in_em else ("#F84018" if i == 0 else "#F7A898")
                script.append(f"tl.fromTo('#{wid}',{{opacity:0,color:'{first_color}'}},{{opacity:1,duration:{0.001 if i == 0 else 0.05},ease:'none'}},{at:.3f});"
                              f"tl.to('#{wid}',{{color:'{color}',duration:.05,ease:'none'}},{at + 0.09:.3f});")
                in_em = in_em and not closes
                i += 1
            lines.append("<div class='ln'>" + " ".join(tokens) + "</div>")
        body.append(f"<div class='clip head' id='p{pi}' data-start='{start:.3f}' data-duration='{end - start:.3f}' data-track-index='20' data-layout-allow-overflow>{''.join(lines)}</div>")
    for li, (a, b, lab, src) in enumerate(labels):
        body.append(f"<div class='clip phase' id='lab{li}' data-start='{a:.3f}' data-duration='{b - a:.3f}' data-track-index='21'>{lab}</div>")
        if src:
            body.append(f"<div class='clip src' id='src{li}' data-start='{a:.3f}' data-duration='{b - a:.3f}' data-track-index='22'>{src}</div>")
    css = """
.head{position:absolute;left:132px;top:252px;width:880px;font-family:'ReelSans';font-weight:600;font-size:82px;line-height:91px;color:#111;letter-spacing:-.018em}
.ln{white-space:nowrap}
.w{display:inline-block}
.em{font-family:'ReelSerif';font-style:italic;font-weight:400;font-size:94px;line-height:80px;letter-spacing:-.01em;color:#F84018}
.phase{position:absolute;left:132px;top:128px;font-family:'ReelMono';font-weight:500;font-size:24px;color:#6f6c66}
.src{position:absolute;right:132px;top:128px;font-family:'ReelMono';font-weight:500;font-size:24px;color:#6f6c66;text-align:right}
"""
    return scene("captions", css, "\n".join(body), "\n".join(script))


# ---------------------------------------------------------------- one project
# Each project moves differently, so the reel doesn't read as one slide repeated. The first is on screen at frame 0: it's the thumbnail.
ENTRANCES = [None, ("x", 1250, 3), ("y", 1500, -3), ("x", -1250, -2), ("y", -1400, 2)]
EXITS = [("x", -1250, -9), ("y", 1500, 5), ("x", 1250, 8), ("y", -1500, -6), None]


def build_project(i, p):
    start, end = STARTS[i], ENDS[i]
    length = end - start
    x, y, w, h = 70, 552, 940, 705
    clip = ROOT / f"assets/clips/{p['id']}.mp4"
    inner = (f"<video id='{p['id']}-v' class='clip' data-start='0' data-duration='{length + 0.3:.3f}' data-track-index='1' muted playsinline src='assets/clips/{p['id']}.mp4'></video>"
             if clip.exists() else picture(p, w, h))
    if p.get("inner"):  # a project with no footage: its own drawing, as HTML
        inner = p["inner"]
    chip_html = ""
    if p.get("chip"):
        chip_html = f"<div class='chip dark' id='{p['id']}-chip' style='left:18px;bottom:18px;font-size:28px;padding:8px 16px;opacity:0'>{p['chip'][0]}</div>"
    body = [f"<div id='{p['id']}-group' style='position:absolute;inset:0'>", card_shell(f"{p['id']}-obj", x, y, w, h, inner + chip_html),
            f"<div class='badge' id='{p['id']}-badge' style='left:44px;top:524px'>{i + 1}</div>"]
    js = [STAMP_JS, f"tl.set('#{p['id']}-obj',{{rotation:{(-1, 1, -0.6, 0.8, -1)[i % 5]}}},0);"]
    enter = ENTRANCES[i % len(ENTRANCES)]
    if enter:
        axis, distance, rotation = enter
        js.append(f"tl.fromTo('#{p['id']}-group',{{{axis}:{distance},rotation:{rotation}}},{{{axis}:0,rotation:0,duration:.34,ease:'expo.out'}},0);")
    js.append(f"pop('#{p['id']}-badge',{0.06 if i == 0 else 0.22},.26,.3);")
    if p.get("chip"):
        at = W(p["chip"][1]) - start
        js.append(f"tl.fromTo('#{p['id']}-chip',{{opacity:0}},{{opacity:1,duration:.06,ease:'none'}},{at:.3f});")
    if p.get("typed"):
        text, word = p["typed"]
        chars = "".join(f"<span class='ch' id='{p['id']}c{k}'>{ch}</span>" for k, ch in enumerate(text))
        body.append(f"<div class='obj' id='{p['id']}-prompt' style='left:96px;top:1186px;width:888px;height:128px'><div class='ht' style='border-radius:22px'></div>"
                    f"<div class='card' style='border-radius:22px;padding:17px 104px 0 26px;font-family:ReelSans;font-weight:600;font-size:38px;line-height:92px;color:#111'>{chars}</div></div>")
        at = max(0.3, W(word) - start - 0.5)
        js.append(f"tl.fromTo('#{p['id']}-prompt',{{y:220,opacity:0}},{{y:0,opacity:1,duration:.22,ease:'expo.out'}},{at - .2:.3f});")
        for k in range(len(text)):
            js.append(f"tl.fromTo('#{p['id']}c{k}',{{opacity:0}},{{opacity:1,duration:.001}},{at + k * 0.022:.3f});")
        js.append(f"tl.to('#{p['id']}-prompt',{{y:240,opacity:0,duration:.2,ease:'power3.in'}},{min(length - .5, at + 1.8):.3f});")
    if p.get("stamp"):
        text, word = p["stamp"]
        at = W(word) - start
        body.append(f"<div class='stamp' id='{p['id']}-stamp' style='left:120px;top:640px;font-size:112px;opacity:0'>{text}</div>")
        js.append(f"stamp('#{p['id']}-stamp',{at:.3f},-8);")
        js.append(f"tl.to('#{p['id']}-obj',{{x:'+=7',y:'+=5',duration:.03}},{at + .11:.3f});tl.to('#{p['id']}-obj',{{x:'-=7',y:'-=5',duration:.08}},{at + .14:.3f});")
    leave = EXITS[i % len(EXITS)]
    if leave:
        axis, distance, rotation = leave
        js.append(f"tl.to('#{p['id']}-group',{{{axis}:{distance},rotation:{rotation},duration:.28,ease:'power3.in'}},{length - .26:.3f});")
    body.append("</div>")
    return scene(p["id"], ".ch{white-space:pre}", "\n".join(body), "\n".join(js))


# ---------------------------------------------------------------- the lower band: five tiles and the counter, then a fact card
def build_strip():
    arrive = W(*ONE_OF_FIVE)
    tiles = []
    for i, p in enumerate(PROJECTS):
        x = TILE_X + i * (TILE_W + TILE_GAP)
        tiles.append(f"<div class='obj' id='tile{i}' style='left:{x}px;top:{TILE_Y}px;width:{TILE_W}px;height:{TILE_H}px;opacity:0'>"
                     f"<div class='card' id='tilec{i}' style='border-width:3px;border-radius:12px'>{thumb(p, TILE_W, TILE_H)}</div>"
                     f"<div class='badge' style='left:-8px;top:-12px;width:34px;height:34px;font-size:24px;line-height:34px;border-radius:8px'>{i + 1}</div>"
                     f"<div class='tick' id='tmark{i}' style='right:-10px;top:-14px;width:40px;height:40px;opacity:0'>{MARKS[p.get('mark', 'none')]}</div></div>")
    counter = ""
    if COUNTER:
        digits = list(range(COUNTER[1] + 1))
        counter = (f"<div id='counter' style='position:absolute;left:66px;top:1452px;display:flex;align-items:center;gap:18px;height:70px;opacity:0'>"
                   f"<span class='mono' style='font-size:30px'>{COUNTER[0]}</span><span class='anton' style='font-size:62px;color:#F84018'>{roller('cnt', digits, 70, 62, 34)}"
                   f"<span style='color:#111;display:inline-block;line-height:70px;vertical-align:top'>/{COUNTER[1]}</span></span></div>")
    js = [STAMP_JS]
    for i in range(len(PROJECTS)):
        js.append(f"pop('#tile{i}',{arrive + i * .05:.3f},.26,.3);")
    if COUNTER:
        js.append(f"tl.fromTo('#counter',{{opacity:0,y:30}},{{opacity:1,y:0,duration:.24,ease:'expo.out'}},{arrive + .3:.3f});")
    count = 0
    for i, p in enumerate(PROJECTS):
        active = max(STARTS[i], arrive + .4)
        settled = ENDS[i] - 0.45
        js.append(f"tl.to('#tile{i}',{{y:-12,duration:.16,ease:'back.out(3)'}},{active:.3f});")
        js.append(f"tl.to('#tilec{i}',{{borderColor:'{RED}',duration:.05}},{active:.3f});")
        js.append(f"tl.to('#tile{i}',{{y:0,duration:.14,ease:'power2.out'}},{settled:.3f});")
        js.append(f"tl.to('#tilec{i}',{{borderColor:'{INK}',duration:.05}},{settled:.3f});")
        if p.get("mark", "none") != "none":
            js.append(f"pop('#tmark{i}',{settled:.3f},.26,.2);")
        if COUNTER and p.get("mark") == "tick" and count < COUNTER[1]:
            count += 1
            js.append(f"tl.to('#cnt',{{y:{-70 * count},duration:.34,ease:'back.out(1.6)'}},{settled:.3f});")
    return scene("strip", "", "".join(tiles) + counter, "\n".join(js))


def build_facts():
    """The corner card: who made the project on screen, when, and one fact. Every value comes from script.md's sources."""
    cards, js = [], [STAMP_JS]
    for i, p in enumerate(PROJECTS):
        a, b = STARTS[i] + .14, ENDS[i] - .3
        r = (-1.5, 1.2, -1, 1.5, -1.2)[i % 5]
        cards.append(f"<div class='obj' id='fc{i}' style='left:604px;top:1358px;width:348px;height:180px;opacity:0'><div class='ht' style='border-radius:18px'></div>"
                     f"<div class='card' style='border-radius:18px'>"
                     f"<div style='position:absolute;left:20px;top:16px;font-family:ReelSans;font-weight:600;font-size:36px;line-height:46px;color:#111;white-space:nowrap'>{p['who']}</div>"
                     f"<div style='position:absolute;left:20px;right:20px;top:70px;height:3px;background:#E3E0D8'></div>"
                     f"<div class='mono' style='position:absolute;left:20px;top:84px;font-size:29px;color:#6f6c66'>{p['when']}</div>"
                     f"<div class='mono' style='position:absolute;left:20px;top:124px;font-size:29px;color:#F84018'>{p['fact']}</div></div></div>")
        js.append(f"tl.fromTo('#fc{i}',{{opacity:0,scale:.6,rotation:{r * 4}}},{{opacity:1,scale:1,rotation:{r},duration:.28,ease:'back.out(2)'}},{a:.3f});")
        js.append(f"tl.to('#fc{i}',{{opacity:0,scale:.82,duration:.1,ease:'power2.in'}},{b:.3f});")
    return scene("facts", "", "".join(cards), "\n".join(js))


# ---------------------------------------------------------------- the closing ask
def build_cta():
    """The voice says it, and the keyword gets typed, then lands as keycaps. The resource card shows what they'd get.

    Don't add a "sent" stamp or a delivery promise unless a real delivery path exists.
    """
    S = WIPE_AT + 0.28
    keys = "".join(f"<span class='key' id='ck{i}'>{ch}</span>" for i, ch in enumerate(KEYWORD))
    typed = "".join(f"<span id='ct{i}'>{ch}</span>" for i, ch in enumerate(KEYWORD))
    rows = "".join(f"<div class='row' id='cr{i}'><span class='n'>{i + 1}</span><span class='tx'><span class='nm'>{p['name']}</span><span class='ur'>{p['source']}</span></span></div>"
                   for i, p in enumerate(PROJECTS))
    key_w = min(110, int(760 / max(len(KEYWORD), 1)))
    body = f"""
<div id="c-field" style="position:absolute;left:96px;top:470px;width:888px;height:136px;background:#fff;border:4px solid #111;border-radius:75px;display:flex;align-items:center;padding-left:44px;font-family:'ReelSans';font-weight:600;font-size:66px;color:#111">
<span id="c-hint" style="position:absolute;left:44px;top:38px;color:#A8A49B;font-size:48px">Add a comment</span><span id="c-typed">{typed}</span></div>
<div class="obj" id="c-pill" style="left:80px;top:458px;width:920px;height:160px;opacity:0">
<div style="position:absolute;inset:12px -12px -12px 12px;background:#111;border-radius:83px"></div>
<div style="position:absolute;inset:0;background:#F84018;border:5px solid #111;border-radius:83px;display:flex;align-items:center;justify-content:center;gap:16px">{keys}</div>
<svg viewBox="0 0 90 70" width="90" height="70" style="position:absolute;left:100px;top:154px"><path d="M6 0h64L10 60z" fill="#F84018" stroke="#111" stroke-width="5" stroke-linejoin="round"/></svg>
</div>
<div class="obj" id="c-card" style="left:70px;top:660px;width:940px;height:570px"><div class="ht"></div>
<div class="card" style="background:#111;border-color:#111"><div class="mono" style="position:absolute;left:40px;top:20px;font-size:30px;color:#fff">all {len(PROJECTS)}, with their links</div>
<div style="position:absolute;left:40px;right:40px;top:68px;height:2px;background:#3a3a3a"></div>
<div style="position:absolute;left:40px;top:80px;right:30px">{rows}</div></div></div>
"""
    css = f"""
.key{{display:inline-block;width:{key_w}px;height:112px;background:#fff;color:#F84018;border-radius:20px;border:4px solid #111;box-shadow:0 10px 0 #111;font-family:'ReelDisplay';font-size:80px;line-height:106px;text-align:center}}
.row{{display:flex;align-items:center;gap:22px;height:96px}}
.n{{flex:0 0 58px;width:58px;height:58px;border-radius:12px;background:#F84018;color:#fff;font-family:'ReelDisplay';font-size:40px;line-height:58px;text-align:center}}
.tx{{display:flex;flex-direction:column;gap:2px}}
.nm{{font-family:'ReelSans';font-weight:600;font-size:38px;line-height:44px;color:#fff;white-space:nowrap}}
.ur{{font-family:'ReelMono';font-weight:500;font-size:28px;line-height:34px;color:#B9B6AE;white-space:nowrap}}
"""
    keyword_at = next(w["s"] for w in WORDS if w["w"].strip(",.!?:;").upper() == KEYWORD)
    land = keyword_at - S
    js = [STAMP_JS, f"tl.to('#c-hint',{{opacity:0,duration:.01}},{max(0.02, land - .3):.3f});"]
    for i in range(len(KEYWORD)):
        js.append(f"tl.fromTo('#ct{i}',{{opacity:0}},{{opacity:1,duration:.001}},{max(0.02, land - .3) + i * .05:.3f});")
    js.append(f"tl.to('#c-field',{{opacity:0,scale:1.04,duration:.05}},{land + .28:.3f});")
    js.append(f"tl.fromTo('#c-pill',{{opacity:0,scale:.8,rotation:-3}},{{opacity:1,scale:1,rotation:-2,duration:.26,ease:'back.out(2.4)'}},{land + .28:.3f});")
    for i in range(len(KEYWORD)):
        js.append(f"tl.fromTo('#ck{i}',{{y:-40,scale:.7}},{{y:0,scale:1,duration:.2,ease:'back.out(2.6)'}},{land + .31 + i * .035:.3f});")
    js.append(f"tl.fromTo('#c-card',{{y:1300,rotation:4}},{{y:0,rotation:0,duration:.42,ease:'expo.out'}},{land + .6:.3f});")
    for i in range(len(PROJECTS)):
        js.append(f"tl.fromTo('#cr{i}',{{opacity:0,x:-40}},{{opacity:1,x:0,duration:.14,ease:'expo.out'}},{land + .9 + i * .14:.3f});")
    return scene("cta", css, body, "\n".join(js))


def build_wipe():
    """A dot wipe, drawn as a pure function of progress, so it's exact at any seek. Dots grow to black, then holes open on the next scene."""
    body = """<canvas id="wp" width="540" height="960" style="position:absolute;inset:0;width:1080px;height:1920px"></canvas>"""
    js = """
var cv=document.getElementById('wp'),cx=cv.getContext('2d'),P=27,cols=21,rows=37,st={p:0};
function dist(c,r){var dx=(c-cols/2)/(cols/2),dy=(r-rows/2)/(rows/2);return Math.sqrt(dx*dx*.7+dy*dy*.7);}
function draw(){
  var p=st.p;cx.clearRect(0,0,540,960);
  if(p<=0||p>=1)return;
  if(p<.45){
    var q=p/.45;cx.fillStyle='#050505';
    for(var r=0;r<=rows;r++)for(var c=0;c<=cols;c++){
      var off=(r%2)*P/2,d=dist(c,r),k=Math.max(0,Math.min(1,q*1.9-(1-d)*.9));
      var rad=k*P*.86;if(rad<=.2)continue;
      cx.beginPath();cx.arc(c*P+off,r*P,rad,0,6.2832);cx.fill();
    }
  }else{
    var q2=(p-.45)/.55;cx.fillStyle='#050505';cx.fillRect(0,0,540,960);
    cx.globalCompositeOperation='destination-out';cx.fillStyle='#000';
    for(var r2=0;r2<=rows;r2++)for(var c2=0;c2<=cols;c2++){
      var off2=(r2%2)*P/2,d2=dist(c2,r2),k2=Math.max(0,Math.min(1,q2*1.9-d2*.9));
      var rad2=k2*P*.86;if(rad2<=.2)continue;
      cx.beginPath();cx.arc(c2*P+off2,r2*P,rad2,0,6.2832);cx.fill();
    }
    cx.globalCompositeOperation='source-over';
  }
}
tl.fromTo(st,{p:0},{p:1,duration:.56,ease:'none',onUpdate:draw},0);
draw();
"""
    return scene("wipe", "", body, js)


# ---------------------------------------------------------------- the root
def build_index():
    hosts = [(p["id"], STARTS[i], ENDS[i] - STARTS[i] + 0.04, 3 + i) for i, p in enumerate(PROJECTS)]
    hosts.append(("cta", WIPE_AT + 0.28, TOTAL - WIPE_AT - 0.28, 3 + len(PROJECTS)))
    tags = "\n".join(
        f'<div id="{cid}" data-composition-id="{cid}" data-composition-src="compositions/{cid}.html" data-start="{s:.3f}" data-duration="{d:.3f}" '
        f'data-track-index="{t}" data-track-kind="graphics" data-width="1080" data-height="1920" style="z-index:{t}"></div>'
        for cid, s, d, t in hosts)
    band_end = WIPE_AT + 0.3
    narration = ROOT / "assets/audio/narration.mp3"
    audio_length = WORDS[-1]["e"] + 0.3
    if narration.exists():
        probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(narration)], capture_output=True, text=True)
        audio_length = float(probe.stdout.strip() or audio_length)
    audio_length = min(audio_length, TOTAL)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{margin:0;width:1080px;height:1920px;overflow:hidden;background:{PAPER}}}
#root{{width:100%;height:100%;position:relative}}
#paper{{position:absolute;inset:0;width:1080px;height:1920px;z-index:0}}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:.3f}" data-width="1080" data-height="1920" data-fps="30">
<img id="paper" class="clip" data-start="0" data-duration="{TOTAL:.3f}" data-track-index="0" src="assets/stills/paper.jpg" alt=""/>
{tags}
<div id="strip" data-composition-id="strip" data-composition-src="compositions/strip.html" data-start="0" data-duration="{band_end:.3f}" data-track-index="9" data-track-kind="graphics" data-width="1080" data-height="1920" style="z-index:9"></div>
<div id="facts" data-composition-id="facts" data-composition-src="compositions/facts.html" data-start="0" data-duration="{band_end:.3f}" data-track-index="10" data-track-kind="graphics" data-width="1080" data-height="1920" style="z-index:10"></div>
<div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{TOTAL:.3f}" data-track-index="11" data-track-kind="captions" data-width="1080" data-height="1920" style="z-index:11"></div>
<div id="wipe" data-composition-id="wipe" data-composition-src="compositions/wipe.html" data-start="{WIPE_AT:.3f}" data-duration="0.58" data-track-index="12" data-track-kind="graphics" data-width="1080" data-height="1920" style="z-index:12"></div>
<audio id="narration" class="clip" data-start="0" data-duration="{audio_length:.3f}" data-track-index="20" data-volume="1" src="assets/audio/narration.mp3"></audio>
</div>
<script>window.__timelines=window.__timelines||{{}};window.__timelines["main"]=gsap.timeline({{paused:true}});</script>
</body>
</html>
"""


files = {"captions": build_captions, "strip": build_strip, "facts": build_facts, "cta": build_cta, "wipe": build_wipe}
for name, fn in files.items():
    (COMP / f"{name}.html").write_text(fn())
for i, p in enumerate(PROJECTS):
    (COMP / f"{p['id']}.html").write_text(build_project(i, p))
(ROOT / "index.html").write_text(build_index())
(ROOT / "timeline.json").write_text(json.dumps({"duration": round(TOTAL, 3), "fps": 30, "cuts": [round(s, 2) for s in STARTS[1:]] + [round(WIPE_AT, 2)]}, indent=1) + "\n")
print(f"wrote {len(files) + len(PROJECTS) + 1} files, {TOTAL:.2f} s")
