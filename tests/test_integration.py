"""Integration tests for prproj_parser.

Tests the full load() pipeline and list_sequences() with both minimal
fixtures and real project files (when available).
"""

import pytest

from prproj_parser import load, list_sequences, BACKEND
from prproj_parser.models import Project, Sequence, Clip, Track


# ---------------------------------------------------------------------------
# Minimal fixture integration
# ---------------------------------------------------------------------------

class TestMinimalProjectIntegration:
    """End-to-end tests using the minimal XML fixture."""

    def test_load_returns_project(self, minimal_gzip_file):
        project = load(minimal_gzip_file)
        assert isinstance(project, Project)

    def test_load_finds_sequence(self, minimal_gzip_file):
        project = load(minimal_gzip_file)
        assert len(project.sequences) == 1
        assert project.sequences[0].name == "Test Sequence"

    def test_sequence_has_clips(self, minimal_gzip_file):
        project = load(minimal_gzip_file)
        seq = project.sequences[0]
        # The minimal fixture has 2 video clips and 1 audio clip
        assert len(seq.video_clips) == 2
        assert len(seq.audio_clips) == 1
        assert len(seq.clips) == 3

    def test_clips_have_names(self, minimal_gzip_file):
        project = load(minimal_gzip_file)
        seq = project.sequences[0]
        names = [c.name for c in seq.clips]
        assert "intro_clip.mp4" in names
        assert "background.png" in names
        assert "narration.wav" in names

    def test_sequence_frame_rate(self, minimal_gzip_file):
        project = load(minimal_gzip_file)
        seq = project.sequences[0]
        assert seq.frame_rate == 25.0

    def test_sequence_tracks(self, minimal_gzip_file):
        project = load(minimal_gzip_file)
        seq = project.sequences[0]
        assert len(seq.tracks) >= 2  # at least 1 video + 1 audio track

    def test_list_sequences(self, minimal_gzip_file):
        names = list_sequences(minimal_gzip_file)
        assert "Test Sequence" in names

    def test_sequence_names_property(self, minimal_gzip_file):
        project = load(minimal_gzip_file)
        assert "Test Sequence" in project.sequence_names

    def test_get_sequence_by_name(self, minimal_gzip_file):
        project = load(minimal_gzip_file)
        seq = project.get_sequence("Test Sequence")
        assert seq is not None
        assert seq.name == "Test Sequence"

    def test_clip_timecodes(self, minimal_gzip_file):
        project = load(minimal_gzip_file)
        seq = project.sequences[0]
        for clip in seq.clips:
            assert isinstance(clip.start_timecode, str)
            assert isinstance(clip.end_timecode, str)
            assert ":" in clip.start_timecode

    def test_clip_types_detected(self, minimal_gzip_file):
        project = load(minimal_gzip_file)
        seq = project.sequences[0]
        types = {c.name: c.clip_type for c in seq.clips}
        assert types["intro_clip.mp4"] == "Video"
        assert types["background.png"] == "Image"
        assert types["narration.wav"] == "Audio"

    def test_get_clips_filter(self, minimal_gzip_file):
        project = load(minimal_gzip_file)
        seq = project.sequences[0]
        video_only = seq.get_clips(include_audio=False)
        all_clips = seq.get_clips(include_audio=True)
        assert len(video_only) < len(all_clips)

    def test_iter_clips(self, minimal_gzip_file):
        project = load(minimal_gzip_file)
        seq = project.sequences[0]
        iterated = list(seq.iter_clips())
        assert len(iterated) == len(seq.clips)


# ---------------------------------------------------------------------------
# Real project integration (skipped if files not available)
# ---------------------------------------------------------------------------

class TestRealProjectIntegration:
    """Integration tests with real Premiere Pro project files.

    Runs once per file placed in tests/fixtures/real/ (see conftest.py).
    No fixtures committed -> zero test instances collected, not a failure.
    """

    def test_load(self, real_project_path):
        project = load(real_project_path)
        assert isinstance(project, Project)
        assert len(project.sequences) >= 1

    def test_list_sequences(self, real_project_path):
        names = list_sequences(real_project_path)
        assert len(names) >= 1

    def test_clips_resolved(self, real_project_path):
        project = load(real_project_path)
        for seq in project.sequences:
            clips = seq.clips
            if not clips:
                continue
            with_media = [c for c in clips if c.media is not None]
            assert len(with_media) > 0, f"No media resolved for {seq.name}"

    def test_all_clips_have_timecodes(self, real_project_path):
        project = load(real_project_path)
        for seq in project.sequences:
            for clip in seq.clips:
                assert clip.start_timecode, f"Missing start_timecode: {clip.name}"
                assert clip.end_timecode, f"Missing end_timecode: {clip.name}"
                assert clip.duration_seconds >= 0, f"Negative duration: {clip.name}"

    def test_track_types_correct(self, real_project_path):
        """Track types should be 'video' or 'audio'."""
        project = load(real_project_path)
        for seq in project.sequences:
            for track in seq.tracks:
                assert track.track_type in ("video", "audio")
                for clip in track.clips:
                    assert clip.track_type == track.track_type
