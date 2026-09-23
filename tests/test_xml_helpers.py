"""Tests for prproj_parser._xml_helpers module."""

from xml.etree.ElementTree import Element, SubElement

from prproj_parser._xml_helpers import (
    find_all_children_local,
    find_child_local,
    findtext_local,
    local_name,
    safe_int,
)

# ---------------------------------------------------------------------------
# local_name
# ---------------------------------------------------------------------------


class TestLocalName:
    """Tests for local_name()."""

    def test_strips_namespace(self):
        assert local_name("{http://example.com}Sequence") == "Sequence"

    def test_no_namespace(self):
        assert local_name("Sequence") == "Sequence"

    def test_empty_namespace(self):
        assert local_name("{}Sequence") == "Sequence"

    def test_non_string_returns_empty(self):
        """Non-string tags (e.g. lxml Comment functions) return ''."""
        assert local_name(None) == ""
        assert local_name(42) == ""

    def test_empty_string(self):
        assert local_name("") == ""

    def test_complex_namespace(self):
        assert local_name("{urn:schemas-microsoft-com:office:word}Name") == "Name"


# ---------------------------------------------------------------------------
# safe_int
# ---------------------------------------------------------------------------


class TestSafeInt:
    """Tests for safe_int()."""

    def test_valid_int_string(self):
        assert safe_int("42") == 42

    def test_none_returns_default(self):
        assert safe_int(None) is None
        assert safe_int(None, 0) == 0

    def test_invalid_string_returns_default(self):
        assert safe_int("abc") is None
        assert safe_int("abc", -1) == -1

    def test_float_string_returns_default(self):
        assert safe_int("3.14") is None

    def test_negative_int(self):
        assert safe_int("-100") == -100

    def test_zero(self):
        assert safe_int("0") == 0

    def test_empty_string_returns_default(self):
        assert safe_int("") is None


# ---------------------------------------------------------------------------
# findtext_local
# ---------------------------------------------------------------------------


class TestFindtextLocal:
    """Tests for findtext_local()."""

    def test_finds_child_text(self):
        parent = Element("Parent")
        child = SubElement(parent, "Name")
        child.text = "hello"
        assert findtext_local(parent, "Name") == "hello"

    def test_returns_none_when_missing(self):
        parent = Element("Parent")
        assert findtext_local(parent, "Name") is None

    def test_ignores_namespace_on_child(self):
        parent = Element("Parent")
        child = SubElement(parent, "{http://ns.example.com}Name")
        child.text = "namespaced"
        assert findtext_local(parent, "Name") == "namespaced"

    def test_returns_first_match(self):
        parent = Element("Parent")
        c1 = SubElement(parent, "Name")
        c1.text = "first"
        c2 = SubElement(parent, "Name")
        c2.text = "second"
        assert findtext_local(parent, "Name") == "first"

    def test_returns_none_for_empty_text(self):
        parent = Element("Parent")
        SubElement(parent, "Name")  # no text set
        assert findtext_local(parent, "Name") is None


# ---------------------------------------------------------------------------
# find_child_local
# ---------------------------------------------------------------------------


class TestFindChildLocal:
    """Tests for find_child_local()."""

    def test_finds_child_element(self):
        parent = Element("Parent")
        child = SubElement(parent, "TrackGroup")
        result = find_child_local(parent, "TrackGroup")
        assert result is child

    def test_returns_none_when_missing(self):
        parent = Element("Parent")
        assert find_child_local(parent, "Missing") is None

    def test_ignores_namespace(self):
        parent = Element("Parent")
        child = SubElement(parent, "{http://ns}TrackGroup")
        result = find_child_local(parent, "TrackGroup")
        assert result is child


# ---------------------------------------------------------------------------
# find_all_children_local
# ---------------------------------------------------------------------------


class TestFindAllChildrenLocal:
    """Tests for find_all_children_local()."""

    def test_finds_all_matching(self):
        parent = Element("Parent")
        c1 = SubElement(parent, "Track")
        SubElement(parent, "Other")
        c3 = SubElement(parent, "Track")
        result = find_all_children_local(parent, "Track")
        assert result == [c1, c3]

    def test_returns_empty_when_none_match(self):
        parent = Element("Parent")
        SubElement(parent, "Other")
        assert find_all_children_local(parent, "Track") == []

    def test_empty_parent(self):
        parent = Element("Parent")
        assert find_all_children_local(parent, "Track") == []
