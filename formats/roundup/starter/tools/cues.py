"""This reel's sound plan. ./reel mix reads it. Give every effect a cause on screen, timed from the voice with w().

Files come from ../assets/source/sfx/<name>.* and the music from ../assets/source/music/bed.*
Each cue is (file name, start seconds, gain dB, fade in, fade out, length to use).
"""
MUSIC_DB = -18.0  # the bed's level before it ducks under the voice
LEVEL = 0.0  # moves music and effects together, when a take reads louder or quieter


def cues(w):
    return [
        # ("whoosh", w("Next"), -14, 0.0, 0.2, 0.6),   # project two slides in
        # ("stamp", w("waitlist") + 0.1, -12, 0.0, 0.1, 0.5),   # the WAITLIST stamp lands
    ]
