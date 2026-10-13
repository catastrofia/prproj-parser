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


class TestIndexingScalesLinearly:
    """Index build time must scale ~linearly with element count."""

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
