"""prproj-parser: Efficient parser for Adobe Premiere Pro .prproj project files.

Quick start::

    from prproj_parser import load

    project = load("my_project.prproj")
    for seq in project.sequences:
        print(seq.name, seq.frame_rate)
        for clip in seq.clips:
            print(f"  {clip.name}  {clip.start_timecode}--{clip.end_timecode}")

For ultra-lightweight sequence listing (minimal memory)::

    from prproj_parser import list_sequences
    names = list_sequences("my_project.prproj")
"""

try:
    from ._version import version as __version__
except ImportError:
    # Editable/source install without a build step (e.g. running tests
    # directly from a git checkout with no `pip install -e .` yet).
    __version__ = "0.0.0.dev0"

from ._compat import BACKEND
from .clip_typing import classify_extension, detect_clip_type, find_extension
from .exceptions import (
    PrprojError,
    PrprojParseError,
    PrprojVersionError,
    ReferenceNotFoundError,
    SequenceNotFoundError,
)
from .index import ProjectIndex, list_sequences_fast
from .models import Clip, MediaInfo, Project, Sequence, Track
from .resolver import Resolver, resolve
from .timecode import detect_fps, seconds_to_timecode, ticks_to_seconds


def load(file_path: str) -> Project:
    """Parse a ``.prproj`` file and return a fully-resolved :class:`Project`.

    This is the primary high-level entry point.  It:

    1. Decompresses the gzip file (or reads plain-XML files)
    2. Builds a :class:`ProjectIndex` via a single ``iterparse`` pass that
       also extracts the deterministic MasterClip -> Media chain maps
    3. Resolves all reference chains into :class:`Sequence` / :class:`Clip`
       objects using those maps

    Args:
        file_path: Path to the ``.prproj`` file.

    Returns:
        A :class:`Project` containing all sequences, tracks, and clips.

    Raises:
        PrprojParseError: If the file cannot be parsed (corrupt, invalid gzip).
        PrprojVersionError: If the PremiereData version is unsupported.
    """
    index = ProjectIndex.from_file(file_path)
    return resolve(index, file_path=file_path)


def list_sequences(file_path: str) -> list:
    """List all sequence names in a ``.prproj`` file.

    This is an ultra-lightweight fast path that only scans for
    ``<Sequence>`` elements and their ``<Name>`` children.  It does
    **not** build a full :class:`ProjectIndex` — memory usage stays
    near-zero regardless of project size.

    Args:
        file_path: Path to the ``.prproj`` file.

    Returns:
        A list of sequence name strings.

    Raises:
        PrprojParseError: If the file cannot be parsed.
    """
    return list_sequences_fast(file_path)


__all__ = [
    # High-level API
    "load",
    "list_sequences",
    # Models
    "Project",
    "Sequence",
    "Clip",
    "Track",
    "MediaInfo",
    # Low-level
    "ProjectIndex",
    "Resolver",
    "resolve",
    # Utilities
    "detect_fps",
    "ticks_to_seconds",
    "seconds_to_timecode",
    "detect_clip_type",
    "classify_extension",
    "find_extension",
    # Exceptions
    "PrprojError",
    "PrprojParseError",
    "PrprojVersionError",
    "ReferenceNotFoundError",
    "SequenceNotFoundError",
    # Meta
    "BACKEND",
    "__version__",
]
