"""The one timeline, in absolute seconds, set from the narration's word timing. Shots, picture, captions and sound all read this.

A shot that starts before the previous one ends makes a dissolve across the overlap. Everything else is a hard cut.
"""
FPS = 30
TIMES = {
    "S01": (0.00, 3.20),
    "S02": (3.20, 6.60),
    "S03": (6.60, 10.00),
}
DURATION = max(end for _, end in TIMES.values())


def count(shot: str) -> int:
    """How many frames a shot renders."""
    start, end = TIMES[shot]
    return round(end * FPS) - round(start * FPS)
