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

from typing import Any

# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------

try:
    # Secure backend: defusedxml wraps stdlib ET with entity-expansion guards
    from defusedxml.ElementTree import iterparse as _iterparse  # type: ignore[import-untyped]
    from xml.etree.ElementTree import Element as Element  # noqa: F401
    BACKEND: str = "defusedxml"
except ImportError:
    try:
        from lxml.etree import iterparse as _iterparse  # type: ignore[assignment]
        from lxml.etree import _Element as Element  # type: ignore[assignment] # noqa: F401
        BACKEND = "lxml"
    except ImportError:
        from xml.etree.ElementTree import iterparse as _iterparse  # type: ignore[assignment]
        from xml.etree.ElementTree import Element as Element  # noqa: F401
        BACKEND = "stdlib"

iterparse = _iterparse
