# Mechanism format: the look

An original reel that explains a mechanism through a moving 3D scene, with captions and no host. [PIPELINE.md](PIPELINE.md) is the working order, and [QUALITY.md](QUALITY.md) holds the settings and checks.

Exact colours, fonts, positions and render settings below are this repo's production defaults. They aren't recovered from anyone's project.

## 1. The goal

Make an invisible or misunderstood process obvious by showing a thing act on another thing. The viewer should be able to point to the contact, hidden part or transfer that caused the outcome. A moving camera supports that explanation, and can't replace the action.

Good subjects: an object's failure, a tool, a machine, a physical process, or an abstract system with a clear physical analogy. For a software topic, show what changes in a mechanism or an enacted analogy, because a floating screen in a 3D room isn't enough. If real footage or a real interface is the key evidence, use a different format.

Use original models, animation, narration and sound, and record the licence of every asset. This format has no human characters, so tell the story with objects. If it needs a body, choose another topic.

## 2. Numbers to aim for

| item | default |
| --- | --- |
| Length | 25 to 45 s. Never a minute or more |
| Script | About 70 to 125 spoken words, at about 3 words a second |
| Views | A useful new view every 1 to 3 s, longer when continuous action reads well |
| Captions | 2 to 5 words a chunk, occasionally 6, timed to the voice |
| First picture | The action itself, before any title or setup |
| Format | 1080 × 1920, 30 fps |
| Ending | Outcome, gag, question or consequence. No forced call to action, and no required loop |

A caption change isn't a camera change. The two timelines do different jobs, so the same view can stay on screen while three phrases replace each other.

## 3. Script and beat map

**Write in this voice.** Present tense, second person, plain words and no jargon, one causal step at a time, with an everyday object for every mechanism: scissors, a saw, an airplane wing. Next, Then, Now, Instead and So carry the story. It asks for nothing and ends on the cost or a twist.

Start with the key visual and write one causal chain. Complete this sentence first: "When this part does X, it causes Y because Z."

Write three columns in `script.md`:

| ears | eyes | sources |
| --- | --- | --- |
| A complete spoken sentence | Object, action, contact point, camera view and reveal word | Evidence for the claim. Label analogy or hypothetical scenes |

- Start mid-action or with a concrete situation. A general introduction spends the best second.
- Spoken lines are full sentences. Each causal step needs a visible action, though a sentence can span several views.
- Reveal only the part needed at that moment. A macro or section is earned by a question the viewer already has.
- End after the mechanism works, the cost becomes clear or the question lands.
- Keep scientific, historical and technical claims independently sourced. Animation is illustration, not verification, and an analogy or fictional scenario must stay identifiable as one.
- A real accident isn't an ordinary topic. Stop short of the deaths on screen, name no crew or victims, state no cause as settled before the final report, attribute hearing evidence on screen, and put the question of whether to post it first in `review.md`.

A default 30 to 35 s map:

| beat | time | job on screen |
| --- | --- | --- |
| Action and question | 0 to 3 s | The object already acting, with the contact or failure established |
| Causal steps | 3 to 12 s | Two or three actions, with context, close-up and changed framing |
| Hidden mechanism | 12 to 24 s | Go inside, below, behind or closer, and reveal what actually changes |
| Consequence | 24 to 35 s | Back to enough context to understand the result, then end |

Other shapes work too:

- **Practice challenged:** show the act, explain why people do it, then expose its cost.
- **Problem and alternative:** demonstrate one method, explain its limit, then offer the other.
- **Delayed reveal:** establish the sensation, delay the explanation, then show the cause.
- **Physical analogy:** enact the familiar example before naming the real thing it stands for.
- **Logic or fiction:** frame it as hypothetical, rather than pretending an animated scene proves a real event.

## 4. World, material and light

The target, rendered in Blender Cycles, is clean, stylized realism: solid models, controlled materials and lighting, convincing contact and clear silhouettes. A real 3D scene is the default, rather than a run of generated stills with zooms.

| token | default | use |
| --- | --- | --- |
| `studio` | `#28B0C8` | An isolated background for a mechanism |
| `floor` | `#2FBCD3` | The studio ground, with a contact shadow |
| `alert` | `#E3262B` | An error, danger or a directional cue |
| `highlight` | `#E9F54A` | A contact point or moving part |
| `positive` | `#72D869` | The correct branch or a successful result |
| `caption` | `#FFFFFF` | Narration chunks |

Don't force a studio opening on every story. A set needs only what the explanation uses: a table and an object often suffice. Context scenes keep believable local colours.

- Soft key and fill, contact shadows and restrained depth of field. Keep the working contact in focus, and blur the background to reduce clutter, not the part that proves the claim.
- Bare metal in the turquoise studio needs neutral reflections or it reads as teal. `P.studio()` already does this.
- For an interior, large soft fills hidden from the camera set the level, and a bright opening or lamp sets the contrast.
- Visible water needs real surface movement and interaction: small waves, local ripples, changing waterlines, wet contact surfaces and absorption. A hero splash may need another technique.
- Keep scale and spatial relations consistent across a change of view. A cutaway must not reverse or relocate the part.

## 5. Graphics

| device | use when | rule |
| --- | --- | --- |
| Macro or section | The working part is too small or hidden | Move into a readable detail, or open the surface while keeping orientation |
| Contact glow | A part or tool must touch one point | Anchor the glow to that point, and clear it when its job is done |
| Direction or flow | Direction or relative motion matters | Keep marks attached to the action, and animate the object too |
| Calendar or timer | Time must compress | Readable geometry or an anchored label, not an unrelated dashboard |
| Thought bubble or branch | Comparing possibilities | Keep the main scene as an anchor, and treat each branch the same way |
| Physical analogy | An abstract system is otherwise invisible | Enact the familiar example first, then connect it to the real system |

Prefer props and anchored graphics over detached paragraphs. Captions are the main editorial text, but not the only text allowed. Never copy real signage or logos.

## 6. Camera and animation

- Name what each camera cue reveals. Push for a detail, go wider for context, orbit to show a relation, or move through a section to expose the interior. Don't move the camera just to keep it moving.
- Every meaningful action must be animated: contact, deformation, separation, flow or transfer. Check it with the camera held still. If the mechanism disappears, the model action needs work.
- Hold a view across caption changes when the action continues, and cut or reframe for new information.
- Use hard cuts for a new step, and short dissolves for a useful relation or passage of time. A change of place can also hide inside a whip move or a pass behind a dark foreground object.
- Starting values: a 5 to 8% dolly or 10 to 20° orbit over a 2 to 3 s view, subtle easing, and a readable hold after a mechanism completes.
- Make scene state deterministic at any time. Transforms, particles, captions and cameras must render correctly after seeking straight to a timestamp.
- Check every handoff frame by frame. A part can look fine at both ends and still snap in one frame.

## 7. Captions

At 1080 × 1920, start with:

- **Tahoma Bold**, about 74 px, white, sentence case. `./reel new` copies it from the system, and never commits it.
- A 5 px dark outline under the fill, plus a small drop shadow. Check legibility against the brightest and busiest shot.
- Centred at x = 540, with the text band centred around y = 1498, about 78% down, about 57 px tall from the top of the tall letters to the baseline. Keep chunks under about 880 px wide, and shorten a chunk before shrinking the text.
- One line wherever possible, on the same baseline across cuts. Nothing else goes over the caption band.
- Timed from the voice's real word timing. Hold a chunk across a camera change if speech continues. No per-word bounce or colour flashing.

If captions hide the mechanism, reframe the subject rather than moving the caption baseline.

## 8. Narration and sound

The voice is ElevenLabs voice ID `TX3LPaxmHKxFdv7VOQHJ`, a stock voice, on Eleven v4 with no other settings sent. Never clone a creator's voice or reuse their recording.

Build a simple mix from the voice first, and leave the voice alone in the edit: no gain ride, compression, EQ or normalizing on it. The music and effects move around it. Add restrained ambience, music and action sounds only when they help the explanation. Align an impact or click to its visible contact, and don't assume a camera change needs a whoosh.

Delivery target: true peak at or below −2 dBTP, and as loud as the limiter allows while barely touching the voice. Start at −16 LUFS and assess the actual mix. A person must listen to the full render once.

## 9. Before you call it done

- The opening communicates the object and action without a title card.
- Each causal claim has a visible operation and a source in the script.
- Context, section, macro and outcome stay spatially consistent.
- A contact sheet shows useful changes of information, and a motion pass proves the parts actually move.
- Captions stay legible and in sync, and graphic labels never compete with the working part.
- Lighting and materials hold up at full size and phone size.
- The ending completes the explanation.
- Every asset is credited.
- There are no black flashes, broken seeking, stutter, bad crops, clipped text or audio faults.

## Rights

Everything published is your own: original story, models, narration, graphics and sound. Never render anyone's frames, video, audio, characters, face or branding into a reel, and never recreate one of their films shot for shot.
