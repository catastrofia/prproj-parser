"""Constants: FPS map, file extension sets, indexed tag names, defaults."""

from typing import Dict, FrozenSet

# Premiere Pro stores frame rate as ticks-per-frame.
# Some versions store the value ×1000.
FPS_MAP: Dict[int, float] = {
    # Standard values
    10594584: 23.976,
    10160640: 25.0,
    8475667: 29.97,
    8408400: 30.0,
    5297292: 47.952,
    5080320: 50.0,
    4237833: 59.94,
    4204200: 60.0,
    # ×1000 variants (seen in some Premiere versions)
    10594584000: 23.976,
    10160640000: 25.0,
    8475667000: 29.97,
    8475667200: 29.97,
    8408400000: 30.0,
    5297292000: 47.952,
    5080320000: 50.0,
    4237833000: 59.94,
    4237833600: 59.94,
    4204200000: 60.0,
}

# File extension sets for clip type detection
VIDEO_EXTENSIONS: FrozenSet[str] = frozenset({
    ".mp4", ".mov", ".avi", ".mxf", ".mkv", ".wmv", ".flv",
    ".m4v", ".mpg", ".mpeg", ".m2v", ".m2t", ".m2ts", ".mts",
    ".ts", ".vob", ".3gp", ".webm", ".r3d", ".braw", ".ari",
    ".arx", ".dpx", ".exr", ".dng", ".crm", ".cine",
})

AUDIO_EXTENSIONS: FrozenSet[str] = frozenset({
    ".wav", ".mp3", ".aac", ".aif", ".aiff", ".flac", ".ogg",
    ".wma", ".m4a", ".opus", ".ac3", ".eac3",
})

IMAGE_EXTENSIONS: FrozenSet[str] = frozenset({
    ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif",
    ".psd", ".psb", ".ai", ".svg", ".webp", ".ico", ".heic",
    ".heif", ".raw", ".cr2", ".nef", ".orf",
})

GRAPHIC_EXTENSIONS: FrozenSet[str] = frozenset({
    ".mogrt", ".prtl", ".prsl",
})

# Element tag names that the indexer should keep in memory.
# All other elements are cleared during iterparse to save memory.
INDEXED_TAGS: FrozenSet[str] = frozenset({
    "Sequence",
    "VideoTrackGroup",
    "AudioTrackGroup",
    "VideoClipTrack",
    "AudioClipTrack",
    "VideoClipTrackItem",
    "AudioClipTrackItem",
    "SubClip",
    "MasterClip",
    "ClipProjectItem",
    "Media",
    "BinProjectItem",
})

# Ticks per second in Premiere Pro (254016000000)
TICKS_PER_SECOND: int = 254016000000

#: Default FPS used when detection fails (NTSC standard).
DEFAULT_FPS: float = 29.97
