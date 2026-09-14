"""Single-pass iterparse indexer for Premiere Pro project files."""

from __future__ import annotations

import gzip
from contextlib import contextmanager
from io import BytesIO
from dataclasses import dataclass, field
from typing import BinaryIO, Dict, Iterator, List, Optional, Union

from ._compat import Element, iterparse
from ._xml_helpers import local_name, safe_int
from .constants import INDEXED_TAGS
from .exceptions import PrprojParseError, PrprojVersionError


# ---------------------------------------------------------------------------
# Shared stream opener (M4 fix)
# ---------------------------------------------------------------------------

_GZIP_MAGIC = b"\x1f\x8b"


@contextmanager
def _open_prproj_stream(file_path: str) -> Iterator[BinaryIO]:
    """Open a ``.prproj`` file as a decompressed binary stream.

    Most ``.prproj`` files are gzip-compressed, but Premiere Pro will
    sometimes write them as plain UTF-8 XML (observed in roughly half of
    real-world exported project files). This sniffs the first two bytes
    for the gzip magic number and picks the right path — it does not
    attempt gzip first and fall back on exception, since a truncated or
    corrupt gzip file would otherwise be silently misread as XML.

    Yields:
        A readable binary stream of the decompressed (or raw) XML.

    Raises:
        PrprojParseError: If the file cannot be read, or is gzip-flagged
            but not valid gzip.
    """
    try:
        with open(file_path, "rb") as probe:
            magic = probe.read(2)
    except Exception as e:
        raise PrprojParseError(f"Failed to open {file_path}: {e}") from e

    is_gzip = magic == _GZIP_MAGIC

    try:
        if is_gzip:
            f = gzip.open(file_path, "rb")
        else:
            f = open(file_path, "rb")
        try:
            yield f
        finally:
            f.close()
    except gzip.BadGzipFile:
        raise PrprojParseError(f"Not a valid gzip file: {file_path}")
    except PrprojParseError:
        raise
    except Exception as e:
        raise PrprojParseError(f"Failed to open {file_path}: {e}") from e


@dataclass
class ProjectIndex:
    """Index of relevant elements from a Premiere Pro project file.

    Built via single-pass iterparse. Only elements with tags in INDEXED_TAGS
    are retained; all others are cleared to minimize memory usage.

    Attributes:
        by_id: Maps ObjectID (int) → Element for indexed elements.
        by_uid: Maps ObjectUID (str) → Element for indexed elements.
        sequences: Maps ObjectUID → Element for Sequence elements specifically.
        version: PremiereData version string (e.g., ``"3"``).
    """

    by_id: Dict[int, Element] = field(default_factory=dict, repr=False)
    by_uid: Dict[str, Element] = field(default_factory=dict, repr=False)
    sequences: Dict[str, Element] = field(default_factory=dict, repr=False)
    version: Optional[str] = None

    def __repr__(self) -> str:
        """Compact repr that doesn't dump thousands of XML elements."""
        return (
            f"ProjectIndex(by_id={len(self.by_id)} elems, "
            f"by_uid={len(self.by_uid)} elems, "
            f"sequences={len(self.sequences)}, "
            f"version={self.version!r})"
        )

    @classmethod
    def from_file(cls, file_path: str) -> "ProjectIndex":
        """Build index from a .prproj file (gzip-compressed XML).

        Opens the file, decompresses gzip, and runs single-pass iterparse.
        """
        with _open_prproj_stream(file_path) as f:
            return cls._build_from_stream(f)

    @classmethod
    def from_xml_string(cls, xml_content: Union[str, bytes]) -> "ProjectIndex":
        """Build index from raw XML content (already decompressed).

        Accepts both ``str`` and ``bytes``.  Useful for testing or when
        XML is already in memory.
        """
        if isinstance(xml_content, str):
            stream: BinaryIO = BytesIO(xml_content.encode("utf-8"))
        else:
            stream = BytesIO(xml_content)
        return cls._build_from_stream(stream)

    @classmethod
    def from_xml_bytes(cls, xml_bytes: bytes) -> "ProjectIndex":
        """Build index from raw XML bytes."""
        return cls._build_from_stream(BytesIO(xml_bytes))

    @classmethod
    def _build_from_stream(cls, stream: BinaryIO) -> "ProjectIndex":
        """Core indexing logic: single-pass iterparse with selective retention.

        CRITICAL IMPLEMENTATION DETAILS:

        1. Use iterparse with events=("start", "end") to track element depth
        2. Track depth so we know which elements are direct children of root
        3. On "end" of a depth-1 element: if its tag is in INDEXED_TAGS,
           extract ObjectID/ObjectUID and store in maps; otherwise clear it
        4. Children of indexed elements (depth 2+) are NEVER cleared
           independently — they are preserved as part of their parent
        5. Special handling for root <PremiereData> to capture version
        6. After iteration, remove non-indexed direct children from root

        The depth-aware clearing pattern:
        - Only depth-1 elements (direct children of <PremiereData>) are
          candidates for clearing. This prevents clearing <Name> or other
          sub-elements inside indexed parents like <Sequence>.
        - After iteration, a cleanup pass removes cleared stubs from root.
        """
        index = cls()

        try:
            context = iterparse(stream, events=("start", "end"))
            root = None
            depth = 0

            for event, elem in context:
                if event == "start":
                    depth += 1
                    # Capture root on first start event
                    if depth == 1:
                        tag = local_name(elem.tag)
                        if tag == "PremiereData":
                            index.version = elem.get("Version")
                            root = elem
                    continue

                # event == "end"
                tag = local_name(elem.tag)

                if depth == 2:
                    # Direct child of root — decide keep or clear
                    if tag in INDEXED_TAGS:
                        obj_id = safe_int(elem.get("ObjectID"))
                        obj_uid = elem.get("ObjectUID")

                        if obj_id is not None:
                            index.by_id[obj_id] = elem
                        if obj_uid is not None:
                            index.by_uid[obj_uid] = elem

                        # Also index sequences separately for quick access
                        if tag == "Sequence" and obj_uid:
                            index.sequences[obj_uid] = elem
                    else:
                        # Not an indexed tag — free memory
                        elem.clear()

                depth -= 1

            # Second cleanup pass: remove cleared children from root
            # to fully release parent references
            if root is not None:
                for child in list(root):
                    child_tag = local_name(child.tag)
                    if child_tag not in INDEXED_TAGS:
                        root.remove(child)

        except PrprojParseError:
            raise
        except Exception as e:
            if "xml" in str(type(e).__module__).lower() or "expat" in str(
                type(e)
            ).lower():
                raise PrprojParseError(f"Invalid XML: {e}") from e
            raise

        return index

    def get_by_id(self, obj_id: int) -> Optional[Element]:
        """Look up an element by ObjectID. Returns None if not found."""
        return self.by_id.get(obj_id)

    def get_by_uid(self, obj_uid: str) -> Optional[Element]:
        """Look up an element by ObjectUID. Returns None if not found."""
        return self.by_uid.get(obj_uid)

    @property
    def sequence_count(self) -> int:
        """Number of Sequence elements in the index."""
        return len(self.sequences)

    def sequence_names(self) -> List[str]:
        """Quick access to all sequence names without full resolution."""
        from ._xml_helpers import findtext_local

        names = []
        for uid, elem in self.sequences.items():
            name = findtext_local(elem, "Name")
            if name:
                names.append(name)
        return names


def list_sequences_fast(file_path: str) -> List[str]:
    """Ultra-lightweight sequence listing.

    Dedicated fast-path that ONLY scans for Sequence elements and their Name
    children. Does NOT build the full ProjectIndex. Clears every element
    immediately. Minimal memory footprint regardless of project size.

    Uses start/end events with depth tracking. At depth 2 (direct children
    of root), only Sequence elements are inspected for their Name child.
    All non-Sequence depth-2 elements are cleared immediately. Sequence
    elements are cleared after extracting the name.

    This is a separate, purpose-built iterparse loop — not the same as
    ``ProjectIndex.from_file().sequence_names()``.
    """
    names: List[str] = []

    with _open_prproj_stream(file_path) as f:
        try:
            context = iterparse(f, events=("start", "end"))
            depth = 0

            for event, elem in context:
                if event == "start":
                    depth += 1
                    continue

                # event == "end"
                if depth == 2:
                    tag = local_name(elem.tag)
                    if tag == "Sequence":
                        # Check for ObjectUID to distinguish definitions
                        # from references (ObjectURef)
                        if elem.get("ObjectUID") is not None:
                            # Look for Name child before clearing
                            for child in elem:
                                if local_name(child.tag) == "Name" and child.text:
                                    names.append(child.text)
                                    break
                    # Clear every depth-2 element to minimize memory
                    elem.clear()

                depth -= 1

        except PrprojParseError:
            raise
        except Exception as e:
            raise PrprojParseError(
                f"Failed to parse {file_path}: {e}"
            ) from e

    return names
