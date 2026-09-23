"""Tests for prproj_parser.models module."""

import pytest

from prproj_parser.models import (
    Clip,
    MediaInfo,
    Project,
    Sequence,
    Track,
    _UnresolvedAccessError,
)

# ---------------------------------------------------------------------------
# MediaInfo
# ---------------------------------------------------------------------------


class TestMediaInfo:
    """Tests for MediaInfo dataclass."""

    def test_best_path_prefers_actual(self):
        info = MediaInfo(
            file_path="/file.mp4",
            actual_path="/actual.mp4",
            relative_path="rel.mp4",
        )
        assert info.best_path == "/actual.mp4"

    def test_best_path_falls_back_to_file(self):
        info = MediaInfo(file_path="/file.mp4")
        assert info.best_path == "/file.mp4"

    def test_best_path_falls_back_to_relative(self):
        info = MediaInfo(relative_path="rel.mp4")
        assert info.best_path == "rel.mp4"

    def test_best_path_none_when_all_empty(self):
        info = MediaInfo()
        assert info.best_path is None

    def test_frozen(self):
        info = MediaInfo(file_path="/test.mp4")
        with pytest.raises(AttributeError):
            info.file_path = "/other.mp4"


# ---------------------------------------------------------------------------
# Clip
# ---------------------------------------------------------------------------


class TestClip:
    """Tests for Clip dataclass."""

    def _make_clip(self, **kwargs):
        defaults = dict(
            name="test_clip",
            start_ticks=0,
            end_ticks=254016000000,
            start_seconds=0.0,
            end_seconds=1.0,
            start_timecode="00:00:00",
            end_timecode="00:00:01",
            duration_seconds=1.0,
            track_index=0,
            track_type="video",
            clip_type="Video",
        )
        defaults.update(kwargs)
        return Clip(**defaults)

    def test_basic_creation(self):
        clip = self._make_clip()
        assert clip.name == "test_clip"
        assert clip.duration_seconds == 1.0

    def test_frozen(self):
        clip = self._make_clip()
        with pytest.raises(AttributeError):
            clip.name = "changed"

    def test_media_default_none(self):
        clip = self._make_clip()
        assert clip.media is None

    def test_nested_sequence_default_false(self):
        clip = self._make_clip()
        assert clip.is_nested_sequence is False

    def test_with_media(self):
        media = MediaInfo(file_path="/test.mp4")
        clip = self._make_clip(media=media)
        assert clip.media.file_path == "/test.mp4"


# ---------------------------------------------------------------------------
# Track
# ---------------------------------------------------------------------------


class TestTrack:
    """Tests for Track dataclass."""

    def test_empty_track(self):
        track = Track(index=0, track_type="video")
        assert track.clip_count == 0
        assert track.clips == ()

    def test_track_with_clips(self):
        clip = Clip(
            name="c",
            start_ticks=0,
            end_ticks=1,
            start_seconds=0.0,
            end_seconds=1.0,
            start_timecode="00:00:00",
            end_timecode="00:00:01",
            duration_seconds=1.0,
            track_index=0,
            track_type="video",
            clip_type="Video",
        )
        track = Track(index=0, track_type="video", clips=(clip,))
        assert track.clip_count == 1

    def test_frozen(self):
        track = Track(index=0, track_type="video")
        with pytest.raises(AttributeError):
            track.index = 1

    def test_clips_is_tuple(self):
        """Track.clips must be a tuple (m1 fix)."""
        track = Track(index=0, track_type="audio", clips=())
        assert isinstance(track.clips, tuple)


# ---------------------------------------------------------------------------
# Sequence
# ---------------------------------------------------------------------------


class TestSequence:
    """Tests for Sequence dataclass."""

    def _make_resolved_sequence(self, **kwargs):
        """Create a resolved Sequence via the factory classmethod."""
        defaults = dict(
            name="Test Seq",
            uid="uid-001",
            frame_rate=25.0,
            ticks_per_frame=10160640000,
            duration_ticks=0,
            duration_seconds=0.0,
            video_track_count=1,
            audio_track_count=1,
            video_clips=[],
            audio_clips=[],
            tracks=[],
        )
        defaults.update(kwargs)
        return Sequence._from_resolved(**defaults)

    def test_from_resolved_sets_flag(self):
        seq = self._make_resolved_sequence()
        assert seq._resolved is True

    def test_unresolved_clips_raises(self):
        """Accessing clips on unresolved Sequence raises _UnresolvedAccessError."""
        seq = Sequence(
            name="test", uid="uid", frame_rate=25.0, ticks_per_frame=10160640000
        )
        with pytest.raises(_UnresolvedAccessError):
            _ = seq.clips

    def test_unresolved_tracks_raises(self):
        seq = Sequence(
            name="test", uid="uid", frame_rate=25.0, ticks_per_frame=10160640000
        )
        with pytest.raises(_UnresolvedAccessError):
            _ = seq.tracks

    def test_unresolved_video_clips_raises(self):
        seq = Sequence(
            name="test", uid="uid", frame_rate=25.0, ticks_per_frame=10160640000
        )
        with pytest.raises(_UnresolvedAccessError):
            _ = seq.video_clips

    def test_unresolved_audio_clips_raises(self):
        seq = Sequence(
            name="test", uid="uid", frame_rate=25.0, ticks_per_frame=10160640000
        )
        with pytest.raises(_UnresolvedAccessError):
            _ = seq.audio_clips

    def test_clips_property_returns_list(self):
        """clips is a property, not a method (m2 fix)."""
        seq = self._make_resolved_sequence()
        result = seq.clips
        assert isinstance(result, list)

    def test_clips_combines_video_and_audio(self):
        vc = Clip(
            name="v",
            start_ticks=0,
            end_ticks=1,
            start_seconds=0.0,
            end_seconds=1.0,
            start_timecode="00:00:00",
            end_timecode="00:00:01",
            duration_seconds=1.0,
            track_index=0,
            track_type="video",
            clip_type="Video",
        )
        ac = Clip(
            name="a",
            start_ticks=0,
            end_ticks=1,
            start_seconds=0.0,
            end_seconds=1.0,
            start_timecode="00:00:00",
            end_timecode="00:00:01",
            duration_seconds=1.0,
            track_index=0,
            track_type="audio",
            clip_type="Audio",
        )
        seq = self._make_resolved_sequence(video_clips=[vc], audio_clips=[ac])
        assert len(seq.clips) == 2
        assert seq.clips[0].name == "v"
        assert seq.clips[1].name == "a"

    def test_video_clips_property(self):
        vc = Clip(
            name="v",
            start_ticks=0,
            end_ticks=1,
            start_seconds=0.0,
            end_seconds=1.0,
            start_timecode="00:00:00",
            end_timecode="00:00:01",
            duration_seconds=1.0,
            track_index=0,
            track_type="video",
            clip_type="Video",
        )
        seq = self._make_resolved_sequence(video_clips=[vc])
        assert len(seq.video_clips) == 1

    def test_audio_clips_property(self):
        ac = Clip(
            name="a",
            start_ticks=0,
            end_ticks=1,
            start_seconds=0.0,
            end_seconds=1.0,
            start_timecode="00:00:00",
            end_timecode="00:00:01",
            duration_seconds=1.0,
            track_index=0,
            track_type="audio",
            clip_type="Audio",
        )
        seq = self._make_resolved_sequence(audio_clips=[ac])
        assert len(seq.audio_clips) == 1

    def test_tracks_property(self):
        t = Track(index=0, track_type="video")
        seq = self._make_resolved_sequence(tracks=[t])
        assert len(seq.tracks) == 1

    def test_get_clips_with_audio(self):
        vc = Clip(
            name="v",
            start_ticks=0,
            end_ticks=1,
            start_seconds=0.0,
            end_seconds=1.0,
            start_timecode="00:00:00",
            end_timecode="00:00:01",
            duration_seconds=1.0,
            track_index=0,
            track_type="video",
            clip_type="Video",
        )
        ac = Clip(
            name="a",
            start_ticks=0,
            end_ticks=1,
            start_seconds=0.0,
            end_seconds=1.0,
            start_timecode="00:00:00",
            end_timecode="00:00:01",
            duration_seconds=1.0,
            track_index=0,
            track_type="audio",
            clip_type="Audio",
        )
        seq = self._make_resolved_sequence(video_clips=[vc], audio_clips=[ac])
        assert len(seq.get_clips(include_audio=True)) == 2
        assert len(seq.get_clips(include_audio=False)) == 1

    def test_iter_clips(self):
        vc = Clip(
            name="v",
            start_ticks=0,
            end_ticks=1,
            start_seconds=0.0,
            end_seconds=1.0,
            start_timecode="00:00:00",
            end_timecode="00:00:01",
            duration_seconds=1.0,
            track_index=0,
            track_type="video",
            clip_type="Video",
        )
        seq = self._make_resolved_sequence(video_clips=[vc])
        clips = list(seq.iter_clips())
        assert len(clips) == 1

    def test_clips_returns_copy(self):
        """Each call to .clips returns a new list (not the internal tuple)."""
        seq = self._make_resolved_sequence()
        a = seq.clips
        b = seq.clips
        assert a is not b


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------


class TestProject:
    """Tests for Project dataclass."""

    def test_empty_project(self):
        proj = Project(file_path="test.prproj")
        assert proj.sequence_names == []
        assert proj.get_sequence("missing") is None

    def test_sequence_names_property(self):
        """sequence_names is a property (not a method)."""
        seq = Sequence._from_resolved(
            name="Seq1",
            uid="uid-1",
            frame_rate=25.0,
            ticks_per_frame=10160640000,
            duration_ticks=0,
            duration_seconds=0.0,
            video_track_count=0,
            audio_track_count=0,
            video_clips=[],
            audio_clips=[],
            tracks=[],
        )
        proj = Project(file_path="test.prproj", sequences=[seq])
        assert proj.sequence_names == ["Seq1"]

    def test_get_sequence_found(self):
        seq = Sequence._from_resolved(
            name="MySeq",
            uid="uid-1",
            frame_rate=25.0,
            ticks_per_frame=10160640000,
            duration_ticks=0,
            duration_seconds=0.0,
            video_track_count=0,
            audio_track_count=0,
            video_clips=[],
            audio_clips=[],
            tracks=[],
        )
        proj = Project(file_path="test.prproj", sequences=[seq])
        found = proj.get_sequence("MySeq")
        assert found is not None
        assert found.name == "MySeq"

    def test_get_sequence_not_found(self):
        proj = Project(file_path="test.prproj")
        assert proj.get_sequence("nonexistent") is None
