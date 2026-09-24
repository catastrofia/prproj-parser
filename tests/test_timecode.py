"""Tests for prproj_parser.timecode module."""

import pytest

from prproj_parser.constants import DEFAULT_FPS, TICKS_PER_SECOND
from prproj_parser.timecode import detect_fps, seconds_to_timecode, ticks_to_seconds

# ---------------------------------------------------------------------------
# detect_fps
# ---------------------------------------------------------------------------


class TestDetectFps:
    """Tests for detect_fps()."""

    def test_known_25fps(self):
        fps, exact = detect_fps(10160640000)
        assert fps == 25.0
        assert exact is True

    def test_known_29_97fps(self):
        fps, exact = detect_fps(8475667000)
        assert fps == 29.97
        assert exact is True

    def test_known_23_976fps(self):
        fps, exact = detect_fps(10594584000)
        assert fps == 23.976
        assert exact is True

    def test_known_30fps(self):
        fps, exact = detect_fps(8408400000)
        assert fps == 30.0
        assert exact is True

    def test_known_60fps(self):
        fps, exact = detect_fps(4204200000)
        assert fps == 60.0
        assert exact is True

    def test_non_x1000_variant(self):
        """Direct lookup for non-×1000 values."""
        fps, exact = detect_fps(10160640)
        assert fps == 25.0
        assert exact is True

    def test_zero_returns_default(self):
        fps, exact = detect_fps(0)
        assert fps == DEFAULT_FPS
        assert exact is False

    def test_negative_returns_default(self):
        fps, exact = detect_fps(-1)
        assert fps == DEFAULT_FPS
        assert exact is False

    def test_arithmetic_fallback(self):
        """Unknown value that yields a reasonable FPS via arithmetic."""
        # TICKS_PER_SECOND / value should be in 1-240 range
        ticks_per_frame = TICKS_PER_SECOND // 24  # ~24 fps
        fps, exact = detect_fps(ticks_per_frame)
        assert exact is False
        assert 23.0 <= fps <= 25.0

    def test_unreasonable_value_returns_default(self):
        """Value that yields FPS outside 1-240 range."""
        fps, exact = detect_fps(1)  # Would give 254016000000 fps
        assert fps == DEFAULT_FPS
        assert exact is False


# ---------------------------------------------------------------------------
# ticks_to_seconds
# ---------------------------------------------------------------------------


class TestTicksToSeconds:
    """Tests for ticks_to_seconds()."""

    def test_zero_ticks(self):
        assert ticks_to_seconds(0, 10160640000, 25.0) == 0.0

    def test_one_second_at_25fps(self):
        """25 frames at 25fps = 1 second."""
        ticks = 25 * 10160640000  # 25 frames worth of ticks
        result = ticks_to_seconds(ticks, 10160640000, 25.0)
        assert result == pytest.approx(1.0)

    def test_ten_seconds_at_29_97fps(self):
        ticks = 300 * 8475667000  # ~300 frames at 29.97fps ≈ 10.01s
        result = ticks_to_seconds(ticks, 8475667000, 29.97)
        assert result == pytest.approx(300 / 29.97, rel=1e-3)

    def test_zero_ticks_per_frame_returns_zero(self):
        assert ticks_to_seconds(1000, 0, 25.0) == 0.0

    def test_negative_ticks_per_frame_returns_zero(self):
        assert ticks_to_seconds(1000, -1, 25.0) == 0.0

    def test_zero_fps_returns_zero(self):
        assert ticks_to_seconds(1000, 10160640000, 0.0) == 0.0

    def test_negative_fps_returns_zero(self):
        assert ticks_to_seconds(1000, 10160640000, -1.0) == 0.0


# ---------------------------------------------------------------------------
# seconds_to_timecode
# ---------------------------------------------------------------------------


class TestSecondsToTimecode:
    """Tests for seconds_to_timecode()."""

    def test_zero_seconds_no_fps(self):
        assert seconds_to_timecode(0.0) == "00:00:00"

    def test_one_minute_no_fps(self):
        assert seconds_to_timecode(60.0) == "00:01:00"

    def test_one_hour_no_fps(self):
        assert seconds_to_timecode(3600.0) == "01:00:00"

    def test_complex_time_no_fps(self):
        # 1h 23m 45s
        assert seconds_to_timecode(5025.0) == "01:23:45"

    def test_negative_seconds_no_fps(self):
        assert seconds_to_timecode(-60.0) == "-00:01:00"

    def test_zero_with_fps(self):
        assert seconds_to_timecode(0.0, fps=25.0) == "00:00:00:00"

    def test_one_frame_at_25fps(self):
        assert seconds_to_timecode(1 / 25.0, fps=25.0) == "00:00:00:01"

    def test_one_second_at_25fps(self):
        assert seconds_to_timecode(1.0, fps=25.0) == "00:00:01:00"

    def test_complex_with_fps(self):
        # 1h 2m 3s + 12 frames at 25fps
        seconds = 3723.0 + 12 / 25.0
        assert seconds_to_timecode(seconds, fps=25.0) == "01:02:03:12"

    def test_negative_with_fps(self):
        result = seconds_to_timecode(-1.0, fps=25.0)
        assert result.startswith("-")
        assert result == "-00:00:01:00"
