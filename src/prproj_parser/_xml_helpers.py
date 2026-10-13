"""XML helper utilities: namespace handling, safe type parsing."""

import re
from typing import Dict, Optional, overload

_NS_PATTERN = re.compile(r"\{[^}]*\}")

# Memoized local names: element tags are highly repetitive in .prproj
# files (a few hundred distinct tags across hundreds of thousands of
# elements), so a dict lookup beats re-running the namespace regex.
# Bounded to keep pathological inputs (dynamic/adversarial tag names)
# from growing the process without limit.
_LOCAL_NAME_CACHE: Dict[str, str] = {}
_LOCAL_NAME_CACHE_MAX = 4096


def local_name(tag) -> str:
    """Strip XML namespace prefix from a tag name.

    '{http://example.com}Sequence' -> 'Sequence'
    'Sequence' -> 'Sequence'

    Returns empty string for non-string tags (e.g. lxml Comment/PI
    functions or cleared element stubs).

    Memoized with a bounded cache: real .prproj files contain a few
    hundred distinct tags, so the cap only engages on pathological input
    (dynamic/adversarial tag names), where it degrades to re-running the
    regex instead of growing without limit.
    """
    if not isinstance(tag, str):
        return ""
    cached = _LOCAL_NAME_CACHE.get(tag)
    if cached is None:
        cached = _NS_PATTERN.sub("", tag)
        if len(_LOCAL_NAME_CACHE) < _LOCAL_NAME_CACHE_MAX:
            _LOCAL_NAME_CACHE[tag] = cached
    return cached


@overload
def safe_int(value, default: int) -> int: ...


@overload
def safe_int(value, default: None = None) -> Optional[int]: ...


def safe_int(value, default: Optional[int] = None) -> Optional[int]:
    """Parse a string to int, returning default on failure."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def findtext_local(elem, local_tag: str) -> Optional[str]:
    """Find child element text by local name, ignoring namespaces.

    Iterates direct children and returns the text of the first child
    whose local tag name matches.
    """
    for child in elem:
        if local_name(child.tag) == local_tag:
            return child.text
    return None


def find_child_local(elem, local_tag: str):
    """Find first direct child element by local name, ignoring namespaces.

    Returns the Element or None.
    """
    for child in elem:
        if local_name(child.tag) == local_tag:
            return child
    return None


def find_all_children_local(elem, local_tag: str) -> list:
    """Find all direct children matching a local tag name."""
    return [child for child in elem if local_name(child.tag) == local_tag]
