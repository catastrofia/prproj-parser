"""Tests for prproj_parser._compat module."""

import pytest

from prproj_parser._compat import iterparse, Element, BACKEND


class TestCompat:
    """Tests for backend auto-detection."""

    def test_backend_is_string(self):
        assert isinstance(BACKEND, str)

    def test_backend_is_known_value(self):
        assert BACKEND in ("defusedxml", "lxml", "stdlib")

    def test_iterparse_is_callable(self):
        assert callable(iterparse)

    def test_element_is_type(self):
        """Element should be a usable type (class)."""
        assert isinstance(Element, type)

    def test_iterparse_works(self):
        """iterparse can parse a minimal XML document."""
        from io import BytesIO
        xml = b"<root><child/></root>"
        events = list(iterparse(BytesIO(xml), events=("end",)))
        tags = [elem.tag for _, elem in events]
        assert "child" in tags
        assert "root" in tags
