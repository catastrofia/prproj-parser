"""Tests for prproj_parser.index module."""

import pytest

from prproj_parser.exceptions import PrprojParseError
from prproj_parser.index import ProjectIndex, _open_prproj_stream, list_sequences_fast

# ---------------------------------------------------------------------------
# _open_prproj_stream
# ---------------------------------------------------------------------------


class TestOpenPrprojStream:
    """Tests for _open_prproj_stream() context manager (M4 fix)."""

    def test_opens_valid_gzip(self, minimal_gzip_file):
        with _open_prproj_stream(minimal_gzip_file) as f:
            data = f.read()
        assert b"PremiereData" in data

    def test_opens_raw_xml_file(self, tmp_path, minimal_xml):
        """Some .prproj files are plain XML (not gzip-compressed).

        Real-world sample: roughly half of DW's exported .prproj files are
        raw UTF-8 XML starting with '<?xml ...>' rather than gzip. The
        stream opener must fall back to reading the file directly instead
        of raising PrprojParseError.
        """
        raw_file = tmp_path / "raw.prproj"
        raw_file.write_text(minimal_xml, encoding="utf-8")
        with _open_prproj_stream(str(raw_file)) as f:
            data = f.read()
        assert b"PremiereData" in data

    def test_raises_on_truncated_gzip(self, tmp_path):
        """Content that starts with the gzip magic but is corrupt should raise."""
        bad_file = tmp_path / "bad.prproj"
        bad_file.write_bytes(b"\x1f\x8b" + b"not really gzip")
        with pytest.raises(PrprojParseError, match="Not a valid gzip"):
            with _open_prproj_stream(str(bad_file)) as f:
                f.read()

    def test_non_gzip_non_xml_content_raises_downstream(self, tmp_path):
        """Content that is neither gzip nor XML opens as a raw stream, but
        fails later during actual XML parsing (see ProjectIndex.from_file)."""
        bad_file = tmp_path / "bad.prproj"
        bad_file.write_text("not gzip data and not xml either")
        with pytest.raises(PrprojParseError, match="Invalid XML|Failed to parse"):
            ProjectIndex.from_file(str(bad_file))

    def test_raises_on_missing_file(self):
        with pytest.raises(PrprojParseError, match="Failed to open"):
            with _open_prproj_stream("/nonexistent/file.prproj"):
                pass


# ---------------------------------------------------------------------------
# ProjectIndex
# ---------------------------------------------------------------------------


class TestProjectIndex:
    """Tests for ProjectIndex."""

    def test_from_xml_string_str(self, minimal_xml):
        idx = ProjectIndex.from_xml_string(minimal_xml)
        assert idx.version == "3"

    def test_from_xml_string_bytes(self, minimal_xml_bytes):
        """from_xml_string accepts bytes too (m5 fix)."""
        idx = ProjectIndex.from_xml_string(minimal_xml_bytes)
        assert idx.version == "3"

    def test_from_xml_bytes(self, minimal_xml_bytes):
        idx = ProjectIndex.from_xml_bytes(minimal_xml_bytes)
        assert idx.version == "3"

    def test_from_file(self, minimal_gzip_file):
        idx = ProjectIndex.from_file(minimal_gzip_file)
        assert idx.version == "3"

    def test_sequences_indexed(self, minimal_index):
        assert len(minimal_index.sequences) == 1

    def test_sequence_has_uid(self, minimal_index):
        assert "seq-uid-001" in minimal_index.sequences

    def test_by_id_populated(self, minimal_index):
        """ObjectID-indexed elements are accessible."""
        assert minimal_index.get_by_id(100) is not None  # VideoTrackGroup
        assert minimal_index.get_by_id(400) is not None  # VideoClipTrackItem

    def test_by_uid_populated(self, minimal_index):
        """ObjectUID-indexed elements are accessible."""
        assert minimal_index.get_by_uid("mc-uid-001") is not None  # MasterClip
        assert minimal_index.get_by_uid("media-uid-001") is not None  # Media

    def test_non_indexed_tags_cleared(self, minimal_index):
        """Elements not in INDEXED_TAGS should not be in the index."""
        # VideoComponentParam (ObjectID=9001) should not be indexed
        assert minimal_index.get_by_id(9001) is None

    def test_sequence_count(self, minimal_index):
        assert minimal_index.sequence_count == 1

    def test_sequence_names(self, minimal_index):
        names = minimal_index.sequence_names()
        assert "Test Sequence" in names

    def test_repr_compact(self, minimal_index):
        """Custom __repr__ doesn't dump XML elements (m6 fix)."""
        r = repr(minimal_index)
        assert "ProjectIndex(" in r
        assert "elems" in r
        assert "version='3'" in r
        # Should NOT contain raw XML
        assert "<" not in r

    def test_get_by_id_missing(self, minimal_index):
        assert minimal_index.get_by_id(99999) is None

    def test_get_by_uid_missing(self, minimal_index):
        assert minimal_index.get_by_uid("nonexistent") is None

    def test_invalid_xml_raises(self):
        with pytest.raises(PrprojParseError, match="Invalid XML"):
            ProjectIndex.from_xml_string("<broken xml><<<")


# ---------------------------------------------------------------------------
# list_sequences_fast
# ---------------------------------------------------------------------------


class TestListSequencesFast:
    """Tests for list_sequences_fast()."""

    def test_finds_sequence_names(self, minimal_gzip_file):
        names = list_sequences_fast(minimal_gzip_file)
        assert "Test Sequence" in names

    def test_returns_list(self, minimal_gzip_file):
        result = list_sequences_fast(minimal_gzip_file)
        assert isinstance(result, list)

    def test_raises_on_missing_file(self):
        with pytest.raises(PrprojParseError):
            list_sequences_fast("/nonexistent/file.prproj")
