"""Reference chain resolution for Premiere Pro project elements.

Follows the flat object-graph references lazily to build high-level
:class:`~prproj_parser.models.Sequence`, :class:`~prproj_parser.models.Clip`,
and :class:`~prproj_parser.models.Track` objects from the raw
:class:`~prproj_parser.index.ProjectIndex`.

Reference chain (from ``prproj-structure.md``):

.. code-block:: text

    Sequence
      > TrackGroups > TrackGroup[Index=0] > Second[ObjectRef] -> VideoTrackGroup
      > TrackGroups > TrackGroup[Index=1] > Second[ObjectRef] -> AudioTrackGroup

    VideoTrackGroup / AudioTrackGroup
      > TrackGroup > Tracks > Track[ObjectURef] -> VideoClipTrack / AudioClipTrack
      > TrackGroup > FrameRate -> ticks per frame (video only)

    VideoClipTrack / AudioClipTrack
      > ClipTrack > ClipItems > TrackItems > TrackItem[ObjectRef] -> TrackItem

    VideoClipTrackItem / AudioClipTrackItem
      > ClipTrackItem > TrackItem > Start / End (ticks)
      > ClipTrackItem > SubClip[ObjectRef] -> SubClip

    SubClip
      > Name (display name)
      > MasterClip[ObjectURef] -> MasterClip

    MasterClip -> Media (deterministic chain):
      MasterClip > Clips > Clip[ObjectRef] -> VideoClip/AudioClip
      VideoClip/AudioClip > Clip > Source[ObjectRef]
        -> VideoMediaSource/AudioMediaSource
      VideoMediaSource/AudioMediaSource > ... > Media[ObjectURef] -> Media
"""

from __future__ import annotations

import logging
from typing import Dict, Iterator, List, Optional, Set, Tuple

from ._compat import Element
from ._xml_helpers import (
    find_child_local,
    findtext_local,
    local_name,
    safe_int,
)
from .clip_typing import detect_clip_type
from .constants import DEFAULT_FPS
from .index import ProjectIndex
from .models import Clip, MediaInfo, Project, Sequence, Track
from .timecode import detect_fps, seconds_to_timecode, ticks_to_seconds

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Deterministic chain maps (extracted in the index's single iterparse pass;
# see ProjectIndex.chain_maps)
# ---------------------------------------------------------------------------


def _build_chain_maps(
    file_path: str,
) -> Tuple[Dict[int, int], Dict[int, str], Dict[int, float]]:
    """Build deterministic reference chain maps for a ``.prproj`` file.

    .. deprecated:: Single-pass architecture.
        Chain maps are now extracted by :class:`ProjectIndex` during its
        own iterparse pass (see :meth:`ProjectIndex.chain_maps`). This
        function remains for backward compatibility and simply builds a
        throwaway index. New code should use the index's chain maps
        directly — this re-parses the whole file and should not be called
        in hot paths.

    Returns:
        A tuple of ``(vc_to_source, ms_to_media, vc_to_speed)`` where:

        - ``vc_to_source``: VideoClip/AudioClip ObjectID -> Source ObjectRef
          (pointing to VideoMediaSource/AudioMediaSource)
        - ``ms_to_media``: VMS/AMS ObjectID -> Media ObjectURef
          (pointing to the Media element's ObjectUID)
        - ``vc_to_speed``: VideoClip/AudioClip ObjectID -> PlaybackSpeed
          multiplier (e.g. ``2.0`` for 2x speed). Absent = normal speed.
    """
    try:
        return ProjectIndex.from_file(file_path).chain_maps()
    except Exception:
        logger.debug(
            "Chain map pass failed for %s, falling back to heuristic", file_path
        )
    return {}, {}, {}


def _build_chain_maps_from_bytes(
    xml_bytes: bytes,
) -> Tuple[Dict[int, int], Dict[int, str], Dict[int, float]]:
    """Build chain maps from raw XML bytes (for testing / in-memory use).

    .. deprecated:: Single-pass architecture.
        See :func:`_build_chain_maps` — this is a thin wrapper over
        :meth:`ProjectIndex.from_xml_bytes` + :meth:`ProjectIndex.chain_maps`.
    """
    try:
        return ProjectIndex.from_xml_bytes(xml_bytes).chain_maps()
    except Exception:
        logger.debug("Chain map pass from bytes failed, falling back to heuristic")
    return {}, {}, {}


# ---------------------------------------------------------------------------
# MasterClip -> Media map builder (C1 rewrite)
# ---------------------------------------------------------------------------


def _build_masterclip_to_media_map(
    index: ProjectIndex,
    vc_to_source: Dict[int, int],
    ms_to_media: Dict[int, str],
) -> Dict[str, "MediaInfo"]:
    """Build a mapping from MasterClip ObjectUID -> MediaInfo.

    Uses a two-tier strategy:

    **Primary (deterministic chain):**
        MasterClip > Clips > Clip[ObjectRef] -> VideoClip/AudioClip
        -> vc_to_source -> VMS/AMS ObjectID
        -> ms_to_media -> Media ObjectURef
        -> index.by_uid -> Media element -> MediaInfo

    **Fallback (heuristic, for unmatched MasterClips):**
        1. Direct title match: MasterClip.Name == Media.Title
        2. Case-insensitive filename match

    The deterministic chain is built from the ``vc_to_source`` and
    ``ms_to_media`` maps produced by :func:`_build_chain_maps`.

    Args:
        index: The project index with all indexed elements.
        vc_to_source: VideoClip/AudioClip ObjectID -> Source ObjectRef.
        ms_to_media: VMS/AMS ObjectID -> Media ObjectURef.

    Returns:
        Dict mapping MasterClip ObjectUID -> MediaInfo.
    """
    mc_uid_to_media: Dict[str, MediaInfo] = {}

    # -- Collect all Media elements by UID ----------------------------------
    media_by_uid: Dict[str, Element] = {}
    for uid, elem in index.by_uid.items():
        if local_name(elem.tag) == "Media":
            media_by_uid[uid] = elem

    # -- Build heuristic lookup tables (for fallback) -----------------------
    media_title_to_info: Dict[str, MediaInfo] = {}
    all_media_fnames: List[Tuple[str, MediaInfo]] = []
    for uid, elem in media_by_uid.items():
        info = _extract_media_info(elem)
        title = info.title
        if title:
            media_title_to_info[title] = info
        best_path = info.best_path
        if best_path:
            fname = best_path.replace("\\", "/").rsplit("/", 1)[-1]
            if fname:
                all_media_fnames.append((fname.lower(), info))
                dot_pos = fname.rfind(".")
                if dot_pos > 0:
                    all_media_fnames.append((fname[:dot_pos].lower(), info))

    # -- Resolve each MasterClip --------------------------------------------
    for uid, elem in index.by_uid.items():
        if local_name(elem.tag) != "MasterClip":
            continue

        mc_uid = uid
        mc_name = findtext_local(elem, "Name")

        # --- Primary: Deterministic chain ---
        matched = False
        clips_container = find_child_local(elem, "Clips")
        if clips_container is not None:
            for clip_child in clips_container:
                if local_name(clip_child.tag) != "Clip":
                    continue
                clip_ref = safe_int(clip_child.get("ObjectRef"))
                if clip_ref is None:
                    continue
                # Step 1: VideoClip/AudioClip -> Source (VMS/AMS)
                source_id = vc_to_source.get(clip_ref)
                if source_id is None:
                    continue
                # Step 2: VMS/AMS -> Media UID
                media_uid = ms_to_media.get(source_id)
                if media_uid is None:
                    continue
                # Step 3: Media UID -> Media element
                media_elem = media_by_uid.get(media_uid)
                if media_elem is not None:
                    mc_uid_to_media[mc_uid] = _extract_media_info(media_elem)
                    matched = True
                    break

        if matched:
            continue

        # --- Fallback 1: Direct title match ---
        if mc_name and mc_name in media_title_to_info:
            mc_uid_to_media[mc_uid] = media_title_to_info[mc_name]
            continue

        # --- Fallback 2: Case-insensitive filename match ---
        if mc_name:
            mc_name_lower = mc_name.lower()
            for fname_lower, info in all_media_fnames:
                if mc_name_lower == fname_lower:
                    mc_uid_to_media[mc_uid] = info
                    break

    return mc_uid_to_media


def _extract_media_info(media_elem: Element) -> MediaInfo:
    """Extract a :class:`MediaInfo` from a ``<Media>`` element."""
    return MediaInfo(
        file_path=findtext_local(media_elem, "FilePath"),
        relative_path=findtext_local(media_elem, "RelativePath"),
        actual_path=findtext_local(media_elem, "ActualMediaFilePath"),
        title=findtext_local(media_elem, "Title"),
    )


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------


class Resolver:
    """Resolves the reference chain from Sequence -> Clips.

    Constructed with a :class:`ProjectIndex` and lazily resolves
    references on demand.  Caches intermediate results for efficiency.

    Usage::

        resolver = Resolver(index)
        project = resolver.resolve_project("my_project.prproj")

    Chain maps are normally already present on the index (extracted during
    its single iterparse pass). The ``file_path`` / ``xml_bytes`` arguments
    only matter for indexes built directly, which pre-date single-pass
    extraction::

        resolver = Resolver(index)
        project = resolver.resolve_project("my_project.prproj")
    """

    def __init__(
        self,
        index: ProjectIndex,
        *,
        file_path: Optional[str] = None,
        xml_bytes: Optional[bytes] = None,
    ) -> None:
        self._index = index
        self._file_path = file_path
        self._xml_bytes = xml_bytes
        self._mc_media_map: Optional[Dict[str, MediaInfo]] = None
        self._sequence_names: Optional[Set[str]] = None
        self._chain_maps_cache: Optional[
            Tuple[Dict[int, int], Dict[int, str], Dict[int, float]]
        ] = None

    @property
    def _chain_maps(
        self,
    ) -> Tuple[Dict[int, int], Dict[int, str], Dict[int, float]]:
        """Chain maps for deterministic MasterClip→Media + speed resolution.

        Preferred source: the maps the index already extracted during its
        own parse pass (no extra I/O, no second pass). Legacy fallbacks
        (a second iterparse over ``file_path`` / ``xml_bytes``) apply only
        when the index predates single-pass chain extraction — e.g. an
        index constructed directly rather than via ``from_*`` builders, or
        built by an older version.
        """
        if self._chain_maps_cache is None:
            if self._index.chain_extracted:
                # Index was built by a single-pass builder: the chain maps are
                # already extracted (possibly empty for chain-free projects).
                # Re-parsing the file cannot produce different maps, so the
                # legacy second pass is never needed here.
                self._chain_maps_cache = self._index.chain_maps()
            elif self._file_path:
                # Index built directly (pre-dates single-pass extraction):
                # run the legacy builders to populate the maps.
                self._chain_maps_cache = _build_chain_maps(self._file_path)
            elif self._xml_bytes:
                self._chain_maps_cache = _build_chain_maps_from_bytes(self._xml_bytes)
            else:
                self._chain_maps_cache = ({}, {}, {})
        return self._chain_maps_cache

    @property
    def _media_map(self) -> Dict[str, MediaInfo]:
        """Lazily build the MasterClip -> Media map.

        Uses the deterministic chain maps extracted during the index's
        single iterparse pass; falls back to pure heuristic matching when
        no chain data is available.
        """
        if self._mc_media_map is None:
            vc_to_source, ms_to_media, _vc_to_speed = self._chain_maps
            self._mc_media_map = _build_masterclip_to_media_map(
                self._index, vc_to_source, ms_to_media
            )
        return self._mc_media_map

    @property
    def _speed_map(self) -> Dict[int, float]:
        """VideoClip/AudioClip ObjectID -> PlaybackSpeed multiplier."""
        return self._chain_maps[2]

    @property
    def _seq_names(self) -> Set[str]:
        """Lazily build the set of all sequence names (for nested detection)."""
        if self._sequence_names is None:
            self._sequence_names = set()
            for uid, elem in self._index.sequences.items():
                name = findtext_local(elem, "Name")
                if name:
                    self._sequence_names.add(name)
        return self._sequence_names

    # -- Top-level resolution -----------------------------------------------

    def resolve_project(self, file_path: str = "") -> Project:
        """Resolve all sequences in the project into a :class:`Project`.

        Args:
            file_path: Path to the ``.prproj`` file (stored on the Project).

        Returns:
            A fully-resolved :class:`Project` with all sequences and clips.
        """
        sequences: List[Sequence] = []
        for uid, seq_elem in self._index.sequences.items():
            try:
                seq = self._resolve_sequence(uid, seq_elem)
                sequences.append(seq)
            except Exception as e:
                logger.warning("Failed to resolve sequence %s: %s", uid, e)
                continue

        return Project(file_path=file_path, sequences=sequences)

    # -- Sequence resolution ------------------------------------------------

    def _resolve_sequence(self, uid: str, seq_elem: Element) -> Sequence:
        """Resolve a single Sequence element into a :class:`Sequence`."""
        name = findtext_local(seq_elem, "Name") or f"Unnamed ({uid[:8]})"

        # Find TrackGroups -> VideoTrackGroup and AudioTrackGroup
        video_tg_elem, audio_tg_elem = self._resolve_track_groups(seq_elem)

        # Get frame rate from VideoTrackGroup
        ticks_per_frame = 0
        fps = DEFAULT_FPS
        if video_tg_elem is not None:
            ticks_per_frame, fps = self._extract_frame_rate(video_tg_elem)

        # Resolve video tracks
        video_tracks: List[Track] = []
        video_clips: List[Clip] = []
        if video_tg_elem is not None:
            video_tracks, video_clips = self._resolve_tracks_from_group(
                video_tg_elem, "video", ticks_per_frame, fps
            )

        # Resolve audio tracks
        audio_tracks: List[Track] = []
        audio_clips: List[Clip] = []
        if audio_tg_elem is not None:
            audio_tracks, audio_clips = self._resolve_tracks_from_group(
                audio_tg_elem, "audio", ticks_per_frame, fps
            )

        # Calculate duration from the latest clip end
        all_clips = video_clips + audio_clips
        duration_ticks = 0
        if all_clips:
            duration_ticks = max(c.end_ticks for c in all_clips)
        duration_seconds = ticks_to_seconds(duration_ticks, ticks_per_frame, fps)

        # M2 fix: use factory classmethod instead of direct mutation
        return Sequence._from_resolved(
            name=name,
            uid=uid,
            frame_rate=fps,
            ticks_per_frame=ticks_per_frame,
            duration_ticks=duration_ticks,
            duration_seconds=duration_seconds,
            video_track_count=len(video_tracks),
            audio_track_count=len(audio_tracks),
            video_clips=video_clips,
            audio_clips=audio_clips,
            tracks=video_tracks + audio_tracks,
        )

    # -- TrackGroup resolution ----------------------------------------------

    def _resolve_track_groups(
        self, seq_elem: Element
    ) -> Tuple[Optional[Element], Optional[Element]]:
        """Extract VideoTrackGroup and AudioTrackGroup from a Sequence.

        Returns:
            ``(video_track_group_elem, audio_track_group_elem)`` -- either
            may be ``None`` if not found.
        """
        video_tg: Optional[Element] = None
        audio_tg: Optional[Element] = None

        track_groups = find_child_local(seq_elem, "TrackGroups")
        if track_groups is None:
            return None, None

        for tg_child in track_groups:
            if local_name(tg_child.tag) != "TrackGroup":
                continue

            second = find_child_local(tg_child, "Second")
            if second is None:
                continue

            obj_ref = safe_int(second.get("ObjectRef"))
            if obj_ref is None:
                continue

            target = self._index.get_by_id(obj_ref)
            if target is None:
                logger.debug("TrackGroup Second ObjectRef=%d not found", obj_ref)
                continue

            target_tag = local_name(target.tag)
            if target_tag == "VideoTrackGroup":
                video_tg = target
            elif target_tag == "AudioTrackGroup":
                audio_tg = target
            # DataTrackGroup is skipped (Index=2)

        return video_tg, audio_tg

    # -- Frame rate extraction ----------------------------------------------

    def _extract_frame_rate(self, track_group_elem: Element) -> Tuple[int, float]:
        """Extract ticks-per-frame and FPS from a TrackGroup element.

        Looks for ``<TrackGroup> > <FrameRate>`` child.

        Returns:
            ``(ticks_per_frame, fps)``
        """
        tg_inner = find_child_local(track_group_elem, "TrackGroup")
        if tg_inner is None:
            return 0, DEFAULT_FPS

        raw_str = findtext_local(tg_inner, "FrameRate")
        if not raw_str:
            return 0, DEFAULT_FPS

        raw = safe_int(raw_str, 0)
        if raw <= 0:
            return 0, DEFAULT_FPS

        fps, _exact = detect_fps(raw)
        return raw, fps

    # -- Track resolution ---------------------------------------------------

    def _resolve_tracks_from_group(
        self,
        group_elem: Element,
        track_type: str,
        ticks_per_frame: int,
        fps: float,
    ) -> Tuple[List[Track], List[Clip]]:
        """Resolve all tracks from a VideoTrackGroup or AudioTrackGroup.

        Returns:
            ``(tracks, all_clips)`` -- tracks is a list of Track objects,
            all_clips is a flat list of all clips across all tracks.
        """
        tracks: List[Track] = []
        all_clips: List[Clip] = []

        # Navigate: group_elem > TrackGroup > Tracks > Track[ObjectURef]
        tg_inner = find_child_local(group_elem, "TrackGroup")
        if tg_inner is None:
            return tracks, all_clips

        tracks_container = find_child_local(tg_inner, "Tracks")
        if tracks_container is None:
            return tracks, all_clips

        for track_ref in tracks_container:
            if local_name(track_ref.tag) != "Track":
                continue

            track_index = safe_int(track_ref.get("Index"), 0)
            obj_uref = track_ref.get("ObjectURef")
            if not obj_uref:
                continue

            track_elem = self._index.get_by_uid(obj_uref)
            if track_elem is None:
                logger.debug("Track ObjectURef=%s not found", obj_uref)
                continue

            # Resolve clips on this track
            track_clips = list(
                self._resolve_track_clips(
                    track_elem,
                    track_index,
                    track_type,
                    ticks_per_frame,
                    fps,
                )
            )

            track_obj = Track(
                index=track_index,
                track_type=track_type,
                clips=tuple(track_clips),
            )
            tracks.append(track_obj)
            all_clips.extend(track_clips)

        return tracks, all_clips

    # -- Clip resolution ----------------------------------------------------

    def _resolve_track_clips(
        self,
        track_elem: Element,
        track_index: int,
        track_type: str,
        ticks_per_frame: int,
        fps: float,
    ) -> Iterator[Clip]:
        """Resolve all clips from a VideoClipTrack or AudioClipTrack.

        Path: ``ClipTrack > ClipItems > TrackItems > TrackItem[ObjectRef]``

        Yields:
            :class:`Clip` instances.
        """
        clip_track = find_child_local(track_elem, "ClipTrack")
        if clip_track is None:
            return

        clip_items = find_child_local(clip_track, "ClipItems")
        if clip_items is None:
            return

        track_items_container = find_child_local(clip_items, "TrackItems")
        if track_items_container is None:
            return

        for ti_ref in track_items_container:
            if local_name(ti_ref.tag) != "TrackItem":
                continue

            obj_ref = safe_int(ti_ref.get("ObjectRef"))
            if obj_ref is None:
                continue

            ti_elem = self._index.get_by_id(obj_ref)
            if ti_elem is None:
                logger.debug("TrackItem ObjectRef=%d not found", obj_ref)
                continue

            clip = self._resolve_single_clip(
                ti_elem, track_index, track_type, ticks_per_frame, fps
            )
            if clip is not None:
                yield clip

    def _resolve_single_clip(
        self,
        track_item_elem: Element,
        track_index: int,
        track_type: str,
        ticks_per_frame: int,
        fps: float,
    ) -> Optional[Clip]:
        """Resolve a single VideoClipTrackItem or AudioClipTrackItem.

        Extracts timing from ``ClipTrackItem > TrackItem > Start/End``
        and identity from ``ClipTrackItem > SubClip[ObjectRef]``.
        """
        clip_track_item = find_child_local(track_item_elem, "ClipTrackItem")
        if clip_track_item is None:
            return None

        # Extract timing
        ti_inner = find_child_local(clip_track_item, "TrackItem")
        if ti_inner is None:
            return None

        start_ticks = safe_int(findtext_local(ti_inner, "Start"), 0)
        end_ticks = safe_int(findtext_local(ti_inner, "End"), 0)

        # Skip zero-duration clips
        if end_ticks <= start_ticks:
            return None

        # Convert to seconds and timecode
        start_sec = ticks_to_seconds(start_ticks, ticks_per_frame, fps)
        end_sec = ticks_to_seconds(end_ticks, ticks_per_frame, fps)
        start_tc = seconds_to_timecode(start_sec, fps)
        end_tc = seconds_to_timecode(end_sec, fps)
        duration_sec = end_sec - start_sec

        # Resolve SubClip for name and media
        subclip_child = find_child_local(clip_track_item, "SubClip")
        clip_name = ""
        media_info: Optional[MediaInfo] = None
        is_nested = False
        speed_percent = 100.0

        if subclip_child is not None:
            sc_ref = safe_int(subclip_child.get("ObjectRef"))
            if sc_ref is not None:
                sc_elem = self._index.get_by_id(sc_ref)
                if sc_elem is not None:
                    clip_name, media_info, is_nested, speed_percent = (
                        self._resolve_subclip(sc_elem)
                    )

        # Fallback name
        if not clip_name:
            clip_name = "Unnamed Clip"

        # Detect clip type
        media_path = media_info.best_path if media_info else None
        media_title = media_info.title if media_info else None
        clip_type, _hint = detect_clip_type(
            name=clip_name,
            media_path=media_path,
            media_title=media_title,
        )

        return Clip(
            name=clip_name,
            start_ticks=start_ticks,
            end_ticks=end_ticks,
            start_seconds=start_sec,
            end_seconds=end_sec,
            start_timecode=start_tc,
            end_timecode=end_tc,
            duration_seconds=duration_sec,
            track_index=track_index,
            track_type=track_type,
            clip_type=clip_type,
            media=media_info,
            is_nested_sequence=is_nested,
            speed_percent=speed_percent,
        )

    # -- SubClip resolution -------------------------------------------------

    def _resolve_subclip(
        self, subclip_elem: Element
    ) -> Tuple[str, Optional[MediaInfo], bool, float]:
        """Resolve a SubClip element to (name, media_info, is_nested, speed_percent).

        Name priority:
        1. SubClip > Name
        2. MasterClip > Name (fallback)

        Nested sequence detection:
        - If SubClip name matches a known Sequence name -> nested.

        Speed resolution:
        - SubClip > Clip[ObjectRef] -> VideoClip/AudioClip -> PlaybackSpeed
          (per-timeline-instance; a repeated use of the same media can
          have a different speed each time, so this must key off the
          SubClip's own direct Clip reference, not the MasterClip).
        """
        # Get SubClip name
        name = findtext_local(subclip_elem, "Name") or ""

        # Check for nested sequence
        is_nested = name in self._seq_names if name else False

        # Resolve speed via SubClip's direct Clip[ObjectRef] -> VideoClip/AudioClip
        speed_percent = 100.0
        clip_ref_elem = find_child_local(subclip_elem, "Clip")
        if clip_ref_elem is not None:
            vc_ref = safe_int(clip_ref_elem.get("ObjectRef"))
            if vc_ref is not None:
                multiplier = self._speed_map.get(vc_ref)
                if multiplier is not None:
                    speed_percent = multiplier * 100.0

        # Resolve MasterClip for media
        media_info: Optional[MediaInfo] = None
        mc_child = find_child_local(subclip_elem, "MasterClip")
        mc_name = ""

        if mc_child is not None:
            mc_uref = mc_child.get("ObjectURef")
            if mc_uref:
                # Get media from the pre-built map
                media_info = self._media_map.get(mc_uref)

                # If no name from SubClip, try MasterClip name
                if not name:
                    mc_elem = self._index.get_by_uid(mc_uref)
                    if mc_elem is not None:
                        mc_name = findtext_local(mc_elem, "Name") or ""

        final_name = name or mc_name
        return final_name, media_info, is_nested, speed_percent


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


def resolve(
    index: ProjectIndex,
    file_path: str = "",
    *,
    xml_bytes: Optional[bytes] = None,
) -> Project:
    """Resolve a :class:`ProjectIndex` into a fully-populated :class:`Project`.

    This is the main entry point for turning raw indexed XML elements into
    the high-level data model.

    Deterministic MasterClip -> Media chain maps come from the index itself
    (extracted during its single iterparse pass). The ``file_path`` /
    ``xml_bytes`` arguments are only used to run legacy chain-map builders
    when the index was constructed directly and has no chain data.

    Args:
        index: A :class:`ProjectIndex` built from a ``.prproj`` file.
        file_path: Path to the original file (stored on the Project; used
            for legacy chain-map extraction on directly-built indexes).
        xml_bytes: Raw XML bytes (alternative to file_path for in-memory use).

    Returns:
        A :class:`Project` with all sequences, tracks, and clips resolved.
    """
    resolver = Resolver(index, file_path=file_path, xml_bytes=xml_bytes)
    return resolver.resolve_project(file_path)
