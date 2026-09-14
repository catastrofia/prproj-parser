"""Tests for prproj_parser.clip_typing module."""

import pytest

from prproj_parser.clip_typing import find_extension, classify_extension, detect_clip_type


# ---------------------------------------------------------------------------
# find_extension
# ---------------------------------------------------------------------------

class TestFindExtension:
    """Tests for find_extension()."""

    def test_simple_filename(self):
        assert find_extension("video.mp4") == ".mp4"

    def test_path_with_backslashes(self):
        assert find_extension(r"C:\Media\clip.mov") == ".mov"

    def test_path_with_forward_slashes(self):
        assert find_extension("/media/clip.wav") == ".wav"

    def test_none_returns_none(self):
        assert find_extension(None) is None

    def test_empty_string_returns_none(self):
        assert find_extension("") is None

    def test_no_extension(self):
        assert find_extension("no_extension_here") is None

    def test_uppercase_normalized(self):
        assert find_extension("VIDEO.MP4") == ".mp4"

    def test_multiple_dots(self):
        """Should find the first valid extension."""
        result = find_extension("file.backup.mp4")
        # Should find .backup or .mp4 depending on regex
        assert result is not None

    def test_whitespace_normalized(self):
        assert find_extension("my  video.mp4") == ".mp4"

    def test_email_in_filename_finds_real_extension(self):
        """Real bug: a filename containing an email address (common in
        royalty-free sound library credits, e.g. freesound.org contributor
        naming) must not match the dotted TLD as the file extension.
        The true extension is the LAST dot-group, not the first.
        """
        name = "qubodup aka Iwan Gabovitch _ qubodup@gmail.com - whoosh-sound.mp3"
        assert find_extension(name) == ".mp3"

    def test_path_with_dotted_folder_names(self):
        """A dotted folder name earlier in the path must not be picked
        over the real trailing extension."""
        path = r"C:\Users\me\unknown album v1.2\track.wav"
        assert find_extension(path) == ".wav"


# ---------------------------------------------------------------------------
# classify_extension
# ---------------------------------------------------------------------------

class TestClassifyExtension:
    """Tests for classify_extension()."""

    def test_video_extensions(self):
        assert classify_extension(".mp4") == "Video"
        assert classify_extension(".mov") == "Video"
        assert classify_extension(".avi") == "Video"
        assert classify_extension(".mxf") == "Video"

    def test_audio_extensions(self):
        assert classify_extension(".wav") == "Audio"
        assert classify_extension(".mp3") == "Audio"
        assert classify_extension(".aac") == "Audio"

    def test_image_extensions(self):
        assert classify_extension(".jpg") == "Image"
        assert classify_extension(".png") == "Image"
        assert classify_extension(".tiff") == "Image"

    def test_graphic_extensions(self):
        assert classify_extension(".mogrt") == "Graphic"

    def test_unknown_extension(self):
        assert classify_extension(".xyz") == "Unknown"

    def test_case_insensitive(self):
        assert classify_extension(".MP4") == "Video"
        assert classify_extension(".Wav") == "Audio"


# ---------------------------------------------------------------------------
# detect_clip_type
# ---------------------------------------------------------------------------

class TestDetectClipType:
    """Tests for detect_clip_type()."""

    def test_from_media_path(self):
        clip_type, hint = detect_clip_type(media_path=r"C:\Media\clip.mp4")
        assert clip_type == "Video"
        assert hint == "ext:media_path"

    def test_from_media_title(self):
        clip_type, hint = detect_clip_type(media_title="narration.wav")
        assert clip_type == "Audio"
        assert hint == "ext:media_title"

    def test_from_name(self):
        clip_type, hint = detect_clip_type(name="background.png")
        assert clip_type == "Image"
        assert hint == "ext:name"

    def test_priority_order(self):
        """media_path takes priority over name."""
        clip_type, hint = detect_clip_type(
            name="audio.wav",
            media_path=r"C:\Media\video.mp4",
        )
        assert clip_type == "Video"
        assert hint == "ext:media_path"

    def test_graphic_keyword_heuristic(self):
        clip_type, hint = detect_clip_type(name="Lower Third Title")
        assert clip_type == "Graphic"
        assert hint == "heuristic:name"

    def test_graphic_folder_heuristic(self):
        clip_type, hint = detect_clip_type(
            name="element",
            media_path=r"C:\Projects\Graphics\element",
        )
        assert clip_type == "Graphic"
        assert hint == "heuristic:path"

    def test_unknown_fallback(self):
        clip_type, hint = detect_clip_type(name="random_clip_name")
        assert clip_type == "Unknown"
        assert hint is None

    def test_all_none(self):
        clip_type, hint = detect_clip_type()
        assert clip_type == "Unknown"
        assert hint is None

    def test_adjustment_layer_synthetic_media_path(self):
        """Adjustment layers, color mattes, bars & tone, black video, and
        other Premiere-native generators have no real media file — Premiere
        writes a purely numeric synthetic ID as the media path
        (e.g. FilePath=1112293707) instead of a real file path. These must
        be classified distinctly from real, unrecognized media.
        """
        clip_type, hint = detect_clip_type(
            name="Adjustment Layer",
            media_path="1112293707",
            media_title="Black Video",
        )
        assert clip_type == "Premiere element"
        assert hint == "synthetic_media_path"

    def test_synthetic_media_path_without_extension_anywhere(self):
        """Even with no other extension hints, a purely-numeric media path
        should resolve to Premiere element, not Unknown."""
        clip_type, hint = detect_clip_type(media_path="9876543210")
        assert clip_type == "Premiere element"

    def test_real_numeric_looking_filename_not_misclassified(self):
        """A real filename that happens to be digits-then-extension must
        still classify by extension, not as a Premiere element."""
        clip_type, hint = detect_clip_type(media_path="1112293707.mp4")
        assert clip_type == "Video"
