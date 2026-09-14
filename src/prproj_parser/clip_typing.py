"""Clip type detection based on file extensions and heuristics.

Simplified from the original app's ``components/clip_detector.py``.
No full-tree-scan fallback needed — media path is resolved through the
reference chain in the resolver.
"""

import re
from typing import Optional, Tuple

from .constants import VIDEO_EXTENSIONS, AUDIO_EXTENSIONS, IMAGE_EXTENSIONS, GRAPHIC_EXTENSIONS

# Pre-compiled pattern for extracting file extensions
_EXT_PATTERN = re.compile(r"\.([a-z0-9]{2,20})(?:\b|$)")

# Premiere writes a purely numeric synthetic ID as the media path for
# native generators (adjustment layers, color mattes, black video, bars &
# tone) that have no real underlying media file.
_SYNTHETIC_PATH_PATTERN = re.compile(r"^\d+$")

# Keywords that suggest a graphic/title clip when no extension is found
_GRAPHIC_KEYWORDS = frozenset({
    "graphic", "title", "caption", "overlay", "lowerthird",
    "lower third", "grad", "template", "mogrt",
})

# Folder names that suggest graphic content
_GRAPHIC_FOLDERS = frozenset({
    "graphics", "templates", "motion graphics", "mogrt",
})


def find_extension(text: Optional[str]) -> Optional[str]:
    """Extract a file extension from a string.

    Isolates the filename component (splitting on ``/`` and ``\\``) and
    returns the extension from its **last** dot-group. This avoids false
    positives from dotted substrings earlier in the string — e.g. an email
    address embedded in a royalty-free audio credit filename
    (``qubodup@gmail.com - whoosh.mp3``) must resolve to ``.mp3``, not
    ``.com``.

    Args:
        text: Any string that might contain a filename or path.

    Returns:
        The extension **with** leading dot (e.g. ``".mp4"``), or ``None``.
    """
    if not text:
        return None
    normalised = re.sub(r"\s+", " ", text.lower())
    filename = normalised.replace("\\", "/").rsplit("/", 1)[-1]
    matches = _EXT_PATTERN.findall(filename)
    if matches:
        return "." + matches[-1]
    return None


def classify_extension(ext: str) -> str:
    """Classify a file extension into a clip type.

    Args:
        ext: Extension **with** leading dot, lowercased (e.g. ``".mp4"``).

    Returns:
        One of ``"Video"``, ``"Audio"``, ``"Image"``, ``"Graphic"``,
        or ``"Unknown"``.
    """
    ext_lower = ext.lower()
    if ext_lower in VIDEO_EXTENSIONS:
        return "Video"
    if ext_lower in AUDIO_EXTENSIONS:
        return "Audio"
    if ext_lower in IMAGE_EXTENSIONS:
        return "Image"
    if ext_lower in GRAPHIC_EXTENSIONS:
        return "Graphic"
    return "Unknown"


def detect_clip_type(
    name: Optional[str] = None,
    media_path: Optional[str] = None,
    media_title: Optional[str] = None,
) -> Tuple[str, Optional[str]]:
    """Determine clip type from available metadata.

    Resolution order:

    1. Synthetic media path (Premiere-native generator: adjustment layer,
       color matte, black video, bars & tone, etc — no real media file).
    2. Extract extension from *media_path* (most reliable).
    3. Extract extension from *media_title*.
    4. Extract extension from *name*.
    5. Heuristic: keyword match in *name*.
    6. Heuristic: graphic folder in *media_path*.
    7. Fallback: ``"Unknown"``.

    Args:
        name: Clip display name (from SubClip).
        media_path: Resolved media file path (from Media element).
        media_title: Media title (from Media element).

    Returns:
        ``(clip_type, source_hint)`` — *source_hint* is a short string
        indicating how the type was determined (useful for debugging),
        or ``None`` for ``"Unknown"``.
    """
    # 1: Premiere-native generator — synthetic numeric media path, no
    # extension anywhere in the path itself.
    if media_path and _SYNTHETIC_PATH_PATTERN.match(media_path):
        return "Premiere element", "synthetic_media_path"

    # 2–4: Try extension from each candidate
    candidates = [
        ("media_path", media_path),
        ("media_title", media_title),
        ("name", name),
    ]
    for source_label, text in candidates:
        ext = find_extension(text)
        if ext:
            clip_type = classify_extension(ext)
            if clip_type != "Unknown":
                return clip_type, f"ext:{source_label}"

    # 5: Heuristic — keyword match in name
    if name:
        name_lower = name.lower()
        for keyword in _GRAPHIC_KEYWORDS:
            if keyword in name_lower:
                return "Graphic", "heuristic:name"

    # 6: Heuristic — graphic folder in media path
    if media_path:
        path_lower = media_path.lower()
        for folder in _GRAPHIC_FOLDERS:
            if folder in path_lower:
                return "Graphic", "heuristic:path"

    # 7: Fallback
    return "Unknown", None
