"""Performance-architecture tests for the parsing pipeline.

Pins two architectural guarantees:

1. **Single-pass indexing** — ``ProjectIndex`` must extract the
   MasterClip→Media chain maps during its own iterparse pass. ``load()``
   must never run a second full parse pass over the file.
2. **Linear-time index cleanup** — building the index over N depth-2
   elements must scale ~linearly, not quadratically (the historical
   implementation removed non-indexed children from the root one-by-one,
   which is O(n²) and dominated wall-clock time on real projects).
"""

import gzip
import time

import pytest

import prproj_parser._compat as _compat
from prproj_parser import load
from prproj_parser.index import ProjectIndex
from tests.test_resolver import CHAIN_XML


def _junk_xml(n_junk: int, n_kept: int = 40) -> bytes:
    """Build XML with many non-indexed depth-2 elements plus indexed ones."""
    parts = ['<?xml version="1.0"?><PremiereData Version="3">']
    for i in range(n_kept):
        parts.append(
            f'<MasterClip ObjectUID="mc-{i}"><Name>clip{i}.mp4</Name></MasterClip>'
        )
    for i in range(n_junk):
        parts.append(
            f'<VideoComponentParam ObjectID="{i}"><Name>x</Name></VideoComponentParam>'
        )
    parts.append("</PremiereData>")
    return "".join(parts).encode("utf-8")


def minimal_chainless_xml() -> str:
    """A resolvable project with no VideoClip/VMS elements (empty chain maps)."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<PremiereData Version="3">\n'
        '  <Sequence ObjectUID="seq-1" Version="11">\n'
        '    <TrackGroups Version="1">\n'
        '      <TrackGroup Version="1" Index="0">'
        '<Second ObjectRef="100"/></TrackGroup>\n'
        "    </TrackGroups>\n"
        "    <Name>Chainless</Name>\n"
        "  </Sequence>\n"
        '  <VideoTrackGroup ObjectID="100" Version="13">\n'
        '    <TrackGroup Version="1">\n'
        '      <Tracks Version="1">\n'
        '        <Track Index="0" ObjectURef="vt-1"/>\n'
        "      </Tracks>\n"
        "      <FrameRate>10160640000</FrameRate>\n"
        "    </TrackGroup>\n"
        "  </VideoTrackGroup>\n"
        '  <VideoClipTrack ObjectUID="vt-1" Version="11">\n'
        '    <ClipTrack Version="2">\n'
        '      <ClipItems Version="3">\n'
        '        <TrackItems Version="1">\n'
        '          <TrackItem Index="0" ObjectRef="400"/>\n'
        "        </TrackItems>\n"
        "      </ClipItems>\n"
        "    </ClipTrack>\n"
        "  </VideoClipTrack>\n"
        '  <VideoClipTrackItem ObjectID="400" Version="6">\n'
        '    <ClipTrackItem Version="8">\n'
        '      <TrackItem Version="3">\n'
        "        <Start>0</Start>\n"
        "        <End>254016000000</End>\n"
        "      </TrackItem>\n"
        '      <SubClip ObjectRef="600"/>\n'
        "    </ClipTrackItem>\n"
        "  </VideoClipTrackItem>\n"
        '  <SubClip ObjectID="600" Version="5">\n'
        '    <MasterClip ObjectURef="mc-1"/>\n'
        "    <Name>only_clip.mp4</Name>\n"
        "  </SubClip>\n"
        '  <MasterClip ObjectUID="mc-1" Version="11">\n'
        "    <Name>only_clip.mp4</Name>\n"
        "  </MasterClip>\n"
        "</PremiereData>\n"
    )


def _timed_index_build(xml_bytes: bytes, repeat: int = 3) -> float:
    """Best-of-N wall-clock time for ProjectIndex.from_xml_bytes."""
    best: float | None = None
    for _ in range(repeat):
        t0 = time.perf_counter()
        ProjectIndex.from_xml_bytes(xml_bytes)
        dt = time.perf_counter() - t0
        best = dt if best is None else min(best, dt)
    assert best is not None
    return best


class TestSinglePassIndexing:
    """ProjectIndex carries the chain maps; load() is a single parse pass."""

    def test_index_carries_chain_maps(self):
        idx = ProjectIndex.from_xml_string(CHAIN_XML)
        vc_to_source, ms_to_media, vc_to_speed = idx.chain_maps()
        assert vc_to_source.get(700) == 900
        assert ms_to_media.get(900) == "media-uid-001"
        assert vc_to_speed.get(700) == 2.5

    def test_chain_maps_empty_without_chain_elements(self, minimal_xml):
        idx = ProjectIndex.from_xml_string(minimal_xml)
        assert idx.chain_maps() == ({}, {}, {})

    def test_chain_maps_present_after_file_load(self, tmp_path):
        fpath = tmp_path / "chain.prproj"
        with gzip.open(str(fpath), "wb") as f:
            f.write(CHAIN_XML.encode("utf-8"))
        idx = ProjectIndex.from_file(str(fpath))
        vc_to_source, ms_to_media, _ = idx.chain_maps()
        assert vc_to_source.get(700) == 900
        assert ms_to_media.get(900) == "media-uid-001"

    def test_load_does_not_run_second_parse_pass(self, tmp_path, monkeypatch):
        """load() must resolve media via the index's own chain maps.

        The legacy second-pass builders are booby-trapped: if load()
        still re-parses the file, these fail the test.
        """
        import prproj_parser.resolver as resolver_mod

        fpath = tmp_path / "chain.prproj"
        with gzip.open(str(fpath), "wb") as f:
            f.write(CHAIN_XML.encode("utf-8"))

        def _boom(*_args, **_kwargs):
            raise AssertionError("legacy second parse pass was called")

        monkeypatch.setattr(resolver_mod, "_build_chain_maps", _boom)
        monkeypatch.setattr(resolver_mod, "_build_chain_maps_from_bytes", _boom)

        project = load(str(fpath))
        clips = [c for s in project.sequences for c in s.clips]
        assert any(
            c.media and "intro_clip.mp4" in (c.media.best_path or "") for c in clips
        )
        video = [c for c in clips if c.track_type == "video"]
        assert video and video[0].speed_percent == 250.0

    def test_chainless_load_does_not_run_second_parse_pass(self, tmp_path, monkeypatch):
        """Chain-free projects must not trigger the legacy second pass.

        The index's chain maps are legitimately empty here; re-parsing the
        file cannot produce different (still-empty) maps, so the legacy
        builders must never run — even though ``any(chain_maps())`` is
        false. Regression guard for the fallback-bypass bug.
        """
        import prproj_parser.resolver as resolver_mod

        fpath = tmp_path / "chainless.prproj"
        with gzip.open(str(fpath), "wb") as f:
            f.write(minimal_chainless_xml().encode("utf-8"))

        def _boom(*_args, **_kwargs):
            raise AssertionError("legacy second parse pass ran on a chain-free project")

        monkeypatch.setattr(resolver_mod, "_build_chain_maps", _boom)
        monkeypatch.setattr(resolver_mod, "_build_chain_maps_from_bytes", _boom)

        project = load(str(fpath))
        assert project.sequences  # resolved without any re-parse


class TestIndexingScalesLinearly:
    """Index build time must scale ~linearly with element count.

    Note: the timing threshold reliably detects the historical quadratic
    cleanup on the pure-Python backends (stdlib, defusedxml) but NOT under
    the lxml extra, whose C-level ``Element.remove`` makes the old code
    fast enough to pass. The mechanism-level guarantee is pinned separately
    by ``test_cleanup_uses_root_clear`` below, which is backend-independent.
    """

    def test_cleanup_scales_linearly(self):
        t_small = _timed_index_build(_junk_xml(12000), repeat=2)
        t_large = _timed_index_build(_junk_xml(48000), repeat=2)
        if t_large < 0.001:
            pytest.skip("too fast to measure reliably")
        ratio = t_large / t_small
        # Linear code: ratio ~ 4. Quadratic code: ratio ~ 16 (parse time
        # dilutes it toward ~11). Threshold sits clear of both, tolerant
        # of timer noise.
        assert ratio < 6.5, (
            f"superlinear indexing: {t_small:.4f}s -> {t_large:.4f}s "
            f"(ratio {ratio:.1f}, quadratic cleanup suspected)"
        )

    def test_cleanup_uses_root_clear(self, monkeypatch):
        """Backend-independent guard: cleanup must not call root.remove().

        The historical implementation removed non-indexed children one by
        one (``root.remove(child)`` per child), which is O(n²) in the
        number of root children. The single-pass implementation drops the
        whole child list with ``root.clear()``. This asserts the mechanism
        directly, so the guarantee holds even on backends (lxml) whose C
        implementation hides the quadratic cost from the timing test.

        The stdlib ``Element`` class is immutable, so instead of patching
        the method we subclass it and inject the subclass via a custom
        ``TreeBuilder`` element factory: a monkeypatched ``iterparse`` runs
        the index over the spy-built tree, so a ``remove`` spy on the
        subclass sees every removal the cleanup makes.
        """
        from xml.etree import ElementTree as ET

        import prproj_parser.index as index_mod

        removed = []

        class _SpyElement(ET.Element):
            def remove(self, element):
                removed.append(element)
                return super().remove(element)

        # _compat.iterparse is backend-selected at import; the custom
        # element factory only applies to the stdlib parser (defusedxml
        # wraps stdlib Elements; lxml has its own C classes), so restrict
        # this mechanism test to the stdlib path.
        if _compat.BACKEND == "lxml":
            pytest.skip("mechanism assert applies to stdlib-backed Element trees")

        parser = ET.XMLParser(target=ET.TreeBuilder(element_factory=_SpyElement))

        def _factory_iterparse(src, events=("end",)):
            return ET.iterparse(src, events=events, parser=parser)

        # Patch the name *in the index module* — index.py binds iterparse
        # directly at import time (``from ._compat import iterparse``), so
        # patching _compat alone would not affect the call site.
        monkeypatch.setattr(index_mod, "iterparse", _factory_iterparse)

        ProjectIndex.from_xml_bytes(_junk_xml(2000))

        assert not removed, (
            f"index cleanup called Element.remove {len(removed)} times; "
            "expected a single root.clear() (quadratic cleanup suspected)"
        )
