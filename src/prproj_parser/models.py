"""Data models for parsed Premiere Pro project data.

Public-facing types that users interact with after parsing a ``.prproj`` file.

Immutability policy
-------------------
* :class:`MediaInfo` and :class:`Clip` are **frozen** dataclasses — once
  created they are immutable and therefore thread-safe.
* :class:`Track` is frozen; its :attr:`clips` field is a ``Tuple[Clip, ...]``
  to preserve immutability.
* :class:`Sequence` is **not** frozen but is constructed fully-resolved via
  :meth:`Sequence._from_resolved`.  Once created, all data should be treated
  as read-only.  Accessor properties guard against premature access.
* :class:`Project` is a simple container of sequences.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, List, Optional, Tuple

# ---------------------------------------------------------------------------
# MediaInfo
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MediaInfo:
    """Media file information resolved from a MasterClip → Media chain.

    Premiere stores media references across several elements.  This model
    collects the resolved paths into a single object.
    """

    file_path: Optional[str] = None
    """The ``<FilePath>`` value from the ``<Media>`` element."""

    relative_path: Optional[str] = None
    """A relative path derived from the project location."""

    actual_path: Optional[str] = None
    """The ``<ActualMediaFilePath>`` value, if present."""

    title: Optional[str] = None
    """Human-readable title (often the filename without extension)."""

    @property
    def best_path(self) -> Optional[str]:
        """Return the most useful path: *actual* > *file* > *relative*.

        Returns:
            The first non-``None`` path in priority order, or ``None`` if
            all paths are unset.
        """
        return self.actual_path or self.file_path or self.relative_path


# ---------------------------------------------------------------------------
# Clip
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Clip:
    """A single clip instance on a timeline track.

    All time values are pre-computed during parsing so consumers never need
    to perform tick arithmetic themselves.
    """

    name: str
    """Display name of the clip."""

    start_ticks: int
    """Raw start position in Premiere ticks."""

    end_ticks: int
    """Raw end position in Premiere ticks."""

    start_seconds: float
    """Start position in seconds (frame-aligned)."""

    end_seconds: float
    """End position in seconds (frame-aligned)."""

    start_timecode: str
    """Start position formatted as timecode (``HH:MM:SS`` or ``HH:MM:SS:FF``)."""

    end_timecode: str
    """End position formatted as timecode."""

    duration_seconds: float
    """Clip duration in seconds (``end_seconds - start_seconds``)."""

    track_index: int
    """0-based index of the track this clip lives on."""

    track_type: str
    """``"video"`` or ``"audio"``."""

    clip_type: str
    """Detected content type: ``"Video"``, ``"Audio"``, ``"Image"``,
    ``"Graphic"``, ``"Premiere element"`` (adjustment layer, color matte,
    black video, bars & tone — has no real underlying media file), or
    ``"Unknown"``."""

    media: Optional[MediaInfo] = None
    """Resolved media information, if available."""

    is_nested_sequence: bool = False
    """``True`` if this clip is a nested sequence reference."""

    speed_percent: float = 100.0
    """Playback speed as a percentage (``100.0`` = normal speed,
    ``200.0`` = 2x, ``50.0`` = half speed). Read from Premiere's
    ``PlaybackSpeed`` element, which is stored as a multiplier
    (e.g. ``2.0``) and converted to percent here."""


# ---------------------------------------------------------------------------
# Track
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Track:
    """A single video or audio track in a sequence.

    Clips are stored as a ``tuple`` (not a ``list``) to preserve the frozen
    contract.
    """

    index: int
    """0-based track index within its type (video or audio)."""

    track_type: str
    """``"video"`` or ``"audio"``."""

    clips: Tuple[Clip, ...] = field(default_factory=tuple)
    """Immutable sequence of :class:`Clip` objects on this track."""

    @property
    def clip_count(self) -> int:
        """Number of clips on this track."""
        return len(self.clips)


# ---------------------------------------------------------------------------
# Sequence
# ---------------------------------------------------------------------------


class _UnresolvedAccessError(RuntimeError):
    """Raised when accessing clip/track data on an unresolved Sequence."""


@dataclass
class Sequence:
    """A timeline sequence in the project.

    Constructed via :meth:`_from_resolved` by the resolver.  Accessor
    properties guard against premature access — calling :attr:`clips`,
    :attr:`tracks`, etc. before resolution raises
    :class:`_UnresolvedAccessError`.
    """

    name: str
    """Sequence display name."""

    uid: str
    """Unique identifier for this sequence within the project."""

    frame_rate: float
    """Detected frames-per-second for this sequence."""

    ticks_per_frame: int
    """Raw ticks-per-frame value from the ``<FrameRate>`` element."""

    duration_ticks: int = 0
    """Total sequence duration in ticks."""

    duration_seconds: float = 0.0
    """Total sequence duration in seconds."""

    video_track_count: int = 0
    """Number of video tracks."""

    audio_track_count: int = 0
    """Number of audio tracks."""

    _video_clips: Tuple[Clip, ...] = field(default_factory=tuple, repr=False)
    _audio_clips: Tuple[Clip, ...] = field(default_factory=tuple, repr=False)
    _tracks: Tuple[Track, ...] = field(default_factory=tuple, repr=False)
    _resolved: bool = field(default=False, repr=False)

    # -- Factory classmethod (M2 fix) --------------------------------------

    @classmethod
    def _from_resolved(
        cls,
        *,
        name: str,
        uid: str,
        frame_rate: float,
        ticks_per_frame: int,
        duration_ticks: int,
        duration_seconds: float,
        video_track_count: int,
        audio_track_count: int,
        video_clips: List[Clip],
        audio_clips: List[Clip],
        tracks: List[Track],
    ) -> "Sequence":
        """Construct a fully-resolved Sequence.

        This is the **only** sanctioned way to create a Sequence with clip
        and track data.  All internal fields are set atomically, and the
        ``_resolved`` flag is set to ``True``.

        Args:
            name: Sequence display name.
            uid: Unique identifier.
            frame_rate: Detected FPS.
            ticks_per_frame: Raw ticks-per-frame.
            duration_ticks: Total duration in ticks.
            duration_seconds: Total duration in seconds.
            video_track_count: Number of video tracks.
            audio_track_count: Number of audio tracks.
            video_clips: Resolved video clips.
            audio_clips: Resolved audio clips.
            tracks: Resolved tracks (video + audio).

        Returns:
            A fully-resolved :class:`Sequence`.
        """
        return cls(
            name=name,
            uid=uid,
            frame_rate=frame_rate,
            ticks_per_frame=ticks_per_frame,
            duration_ticks=duration_ticks,
            duration_seconds=duration_seconds,
            video_track_count=video_track_count,
            audio_track_count=audio_track_count,
            _video_clips=tuple(video_clips),
            _audio_clips=tuple(audio_clips),
            _tracks=tuple(tracks),
            _resolved=True,
        )

    # -- Guard helper -------------------------------------------------------

    def _check_resolved(self) -> None:
        """Raise if the sequence has not been resolved yet."""
        if not self._resolved:
            raise _UnresolvedAccessError(
                f"Sequence {self.name!r} has not been resolved yet. "
                "Clip and track data is only available after resolution."
            )

    # -- Property accessors (m2 fix: methods → properties) ------------------

    @property
    def clips(self) -> List[Clip]:
        """All clips in the sequence (video + audio).

        Returns:
            A **new** list combining video and audio clips.

        Raises:
            _UnresolvedAccessError: If the sequence has not been resolved.
        """
        self._check_resolved()
        return list(self._video_clips) + list(self._audio_clips)

    @property
    def video_clips(self) -> List[Clip]:
        """Return a copy of the video clip list.

        Raises:
            _UnresolvedAccessError: If the sequence has not been resolved.
        """
        self._check_resolved()
        return list(self._video_clips)

    @property
    def audio_clips(self) -> List[Clip]:
        """Return a copy of the audio clip list.

        Raises:
            _UnresolvedAccessError: If the sequence has not been resolved.
        """
        self._check_resolved()
        return list(self._audio_clips)

    @property
    def tracks(self) -> List[Track]:
        """Return a copy of the track list.

        Raises:
            _UnresolvedAccessError: If the sequence has not been resolved.
        """
        self._check_resolved()
        return list(self._tracks)

    # -- Filtered clip access -----------------------------------------------

    def get_clips(self, include_audio: bool = True) -> List[Clip]:
        """Return clips with optional audio filtering.

        Args:
            include_audio: If ``False``, only video clips are returned.

        Returns:
            A **new** list combining video (and optionally audio) clips.

        Raises:
            _UnresolvedAccessError: If the sequence has not been resolved.
        """
        self._check_resolved()
        if include_audio:
            return list(self._video_clips) + list(self._audio_clips)
        return list(self._video_clips)

    # -- Generator-based lazy iteration ------------------------------------

    def iter_clips(self, include_audio: bool = True) -> Iterator[Clip]:
        """Lazily iterate over clips without copying.

        Args:
            include_audio: If ``False``, only video clips are yielded.

        Yields:
            :class:`Clip` instances — video first, then audio.

        Raises:
            _UnresolvedAccessError: If the sequence has not been resolved.
        """
        self._check_resolved()
        yield from self._video_clips
        if include_audio:
            yield from self._audio_clips

    def iter_video_clips(self) -> Iterator[Clip]:
        """Lazily iterate over video clips.

        Raises:
            _UnresolvedAccessError: If the sequence has not been resolved.
        """
        self._check_resolved()
        yield from self._video_clips

    def iter_audio_clips(self) -> Iterator[Clip]:
        """Lazily iterate over audio clips.

        Raises:
            _UnresolvedAccessError: If the sequence has not been resolved.
        """
        self._check_resolved()
        yield from self._audio_clips


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------


@dataclass
class Project:
    """A parsed Premiere Pro project.

    Top-level container returned by the parser.  Holds one or more
    :class:`Sequence` objects.
    """

    file_path: str
    """Path to the ``.prproj`` file that was parsed."""

    sequences: List[Sequence] = field(default_factory=list)
    """All sequences discovered in the project."""

    @property
    def sequence_names(self) -> List[str]:
        """Return the names of all sequences."""
        return [s.name for s in self.sequences]

    def get_sequence(self, name: str) -> Optional[Sequence]:
        """Look up a sequence by its display name.

        Args:
            name: Exact sequence name to search for.

        Returns:
            The matching :class:`Sequence`, or ``None`` if not found.
        """
        for s in self.sequences:
            if s.name == name:
                return s
        return None
