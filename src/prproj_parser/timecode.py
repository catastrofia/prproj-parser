"""Timecode conversion: ticks ↔ seconds, seconds ↔ timecode, FPS detection.

Ported and improved from the original app's ``components/time_converter.py``.
All functions are pure (no global state, no logging side-effects).
"""

from typing import Tuple, Optional

from .constants import DEFAULT_FPS, FPS_MAP, TICKS_PER_SECOND

# ---------------------------------------------------------------------------
# FPS detection
# ---------------------------------------------------------------------------


def detect_fps(raw_frame_rate: int) -> Tuple[float, bool]:
    """Detect FPS from Premiere's raw ticks-per-frame value.

    Premiere stores the frame rate of a sequence as the number of ticks per
    frame in the ``<FrameRate>`` element of a ``<TrackGroup>``.  This function
    resolves that integer to a human-readable FPS value.

    Resolution order:

    1. Direct lookup in :data:`~prproj_parser.constants.FPS_MAP`.
    2. Iterative scale-down (÷10) to handle ×1000 variants not already in the
       map.
    3. Arithmetic fallback: ``TICKS_PER_SECOND / raw_frame_rate``.

    Args:
        raw_frame_rate: The ``FrameRate`` value from a ``TrackGroup`` element.

    Returns:
        ``(fps, is_exact_match)`` — *is_exact_match* is ``True`` when the
        value was found in :data:`FPS_MAP`, ``False`` when it was calculated.
    """
    if raw_frame_rate <= 0:
        return DEFAULT_FPS, False

    # 1. Direct lookup
    fps = FPS_MAP.get(raw_frame_rate)
    if fps is not None:
        return fps, True

    # 2. Scale-down search (handles unexpected ×10/×100/… variants)
    scaled = raw_frame_rate
    while scaled > 1_000_000:
        scaled //= 10
        fps = FPS_MAP.get(scaled)
        if fps is not None:
            return fps, True

    # 3. Arithmetic fallback
    calculated = TICKS_PER_SECOND / raw_frame_rate
    # Sanity-check: FPS should be in a reasonable range (1–240)
    if 1.0 <= calculated <= 240.0:
        return round(calculated, 3), False

    return DEFAULT_FPS, False


# ---------------------------------------------------------------------------
# Tick → seconds conversion
# ---------------------------------------------------------------------------

def ticks_to_seconds(
    ticks: int,
    ticks_per_frame: int,
    fps: float,
) -> float:
    """Convert a Premiere tick value to seconds with frame alignment.

    Premiere stores ``TrackItem`` Start/End as integer ticks.  The conversion
    aligns to the nearest frame boundary to avoid floating-point drift::

        frames  = round(ticks / ticks_per_frame)
        seconds = frames / fps

    Args:
        ticks: Raw tick value (e.g. ``Start`` or ``End`` of a track item).
        ticks_per_frame: Ticks-per-frame value from the sequence's
            ``<FrameRate>`` element.
        fps: Frames per second (as returned by :func:`detect_fps`).

    Returns:
        Time in seconds (≥ 0.0).  Returns ``0.0`` if *ticks_per_frame* or
        *fps* are zero/negative.
    """
    if ticks_per_frame <= 0 or fps <= 0.0:
        return 0.0

    frames = round(ticks / ticks_per_frame)
    return frames / fps


# ---------------------------------------------------------------------------
# Seconds → timecode formatting
# ---------------------------------------------------------------------------

def seconds_to_timecode(
    seconds: float,
    fps: Optional[float] = None,
) -> str:
    """Format *seconds* as a timecode string.

    Two output formats are supported:

    * **Frame-accurate** (when *fps* is provided): ``HH:MM:SS:FF``
    * **Second-accurate** (when *fps* is ``None``): ``HH:MM:SS``

    Negative values produce a leading ``-`` sign.

    Args:
        seconds: Time in seconds.
        fps: Optional frames-per-second for frame-accurate output.

    Returns:
        Formatted timecode string.
    """
    negative = seconds < 0
    total = abs(seconds)
    sign = "-" if negative else ""

    if fps is not None and fps > 0:
        # Frame-accurate: HH:MM:SS:FF
        total_frames = round(total * fps)
        fps_int = round(fps)  # for modulo; works for integer & near-integer fps
        ff = total_frames % fps_int
        remaining_seconds = total_frames // fps_int
        ss = remaining_seconds % 60
        mm = (remaining_seconds // 60) % 60
        hh = remaining_seconds // 3600
        return f"{sign}{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"

    # Second-accurate: HH:MM:SS
    s_round = int(round(total))
    hh = s_round // 3600
    mm = (s_round % 3600) // 60
    ss = s_round % 60
    return f"{sign}{hh:02d}:{mm:02d}:{ss:02d}"


