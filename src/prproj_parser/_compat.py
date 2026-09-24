"""Parser backend auto-detection with optional secure XML parsing.

Priority order:
1. ``defusedxml`` (if installed via ``pip install prproj-parser[secure]``)
2. ``lxml`` (fast C-based parser)
3. ``xml.etree.ElementTree`` (stdlib fallback)

Exports:
    iterparse   — streaming XML parser
    Element     — element type alias (for type annotations)
    BACKEND     — string identifying which backend is active
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element as Element
    from xml.etree.ElementTree import iterparse as iterparse

    BACKEND: str
else:
    # ---------------------------------------------------------------------------
    # Backend selection
    # ---------------------------------------------------------------------------

    try:
        import xml.etree.ElementTree as _stdlib_et

        from defusedxml.ElementTree import iterparse as _iterparse

        Element = _stdlib_et.Element
        BACKEND: str = "defusedxml"
    except ImportError:
        try:
            import lxml.etree as _lxml_et

            Element = _lxml_et._Element
            _iterparse = _lxml_et.iterparse
            BACKEND = "lxml"
        except ImportError:
            import xml.etree.ElementTree as _stdlib_et

            Element = _stdlib_et.Element
            _iterparse = _stdlib_et.iterparse
            BACKEND = "stdlib"

    iterparse = _iterparse
