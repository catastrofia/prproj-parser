"""Tests for prproj_parser.resolver module."""

import gzip

from prproj_parser.index import ProjectIndex
from prproj_parser.models import Project
from prproj_parser.resolver import (
    Resolver,
    _build_chain_maps,
    _build_chain_maps_from_bytes,
    _build_masterclip_to_media_map,
    _extract_media_info,
    resolve,
)

# ---------------------------------------------------------------------------
# XML fixture with deterministic chain elements
# ---------------------------------------------------------------------------

CHAIN_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<PremiereData Version="3">

  <Sequence ObjectUID="seq-uid-001"
            ClassID="6a15d903-8739-11d5-af2d-9b7855ad8974" Version="11">
    <TrackGroups Version="1">
      <TrackGroup Version="1" Index="0">
        <First>228cda18-3625-4d2d-951e-348879e4ed93</First>
        <Second ObjectRef="100"/>
      </TrackGroup>
      <TrackGroup Version="1" Index="1">
        <First>80b8e3d5-6dca-4195-aefb-cb5f407ab009</First>
        <Second ObjectRef="200"/>
      </TrackGroup>
    </TrackGroups>
    <Name>Chain Test</Name>
    <ID>1</ID>
  </Sequence>

  <VideoTrackGroup ObjectID="100"
                   ClassID="9e9abf7a-0918-49c2-91ae-991b5dde77bb" Version="13">
    <TrackGroup Version="1">
      <Tracks Version="1">
        <Track Index="0" ObjectURef="vtrack-uid-001"/>
      </Tracks>
      <FrameRate>10160640000</FrameRate>
      <NextTrackID>2</NextTrackID>
    </TrackGroup>
    <FrameRect>0,0,1080,1920</FrameRect>
  </VideoTrackGroup>

  <AudioTrackGroup ObjectID="200"
                   ClassID="9b9238b9-53a8-4cc3-b03f-b36246d052e6" Version="6">
    <TrackGroup Version="1">
      <Tracks Version="1">
        <Track Index="0" ObjectURef="atrack-uid-001"/>
      </Tracks>
      <FrameRate>5292000</FrameRate>
      <NextTrackID>2</NextTrackID>
    </TrackGroup>
  </AudioTrackGroup>

  <VideoClipTrack ObjectUID="vtrack-uid-001"
                  ClassID="f68dcd81-8805-11d5-af2d-9bfa89d4ddd4" Version="11">
    <ClipTrack Version="2">
      <Track Version="3"><Index>0</Index></Track>
      <ClipItems Version="3">
        <TrackItems Version="1">
          <TrackItem Index="0" ObjectRef="400"/>
        </TrackItems>
      </ClipItems>
    </ClipTrack>
  </VideoClipTrack>

  <AudioClipTrack ObjectUID="atrack-uid-001"
                  ClassID="f68dcd81-8805-11d5-af2d-9bfa89d4ddd5" Version="11">
    <ClipTrack Version="2">
      <Track Version="3"><Index>0</Index></Track>
      <ClipItems Version="3">
        <TrackItems Version="1">
          <TrackItem Index="0" ObjectRef="500"/>
        </TrackItems>
      </ClipItems>
    </ClipTrack>
  </AudioClipTrack>

  <VideoClipTrackItem ObjectID="400"
                      ClassID="368b0406-29e3-4923-9fcd-094fbf9a1089" Version="6">
    <ClipTrackItem Version="8">
      <TrackItem Version="3">
        <Start>0</Start>
        <End>254016000000</End>
      </TrackItem>
      <SubClip ObjectRef="600"/>
    </ClipTrackItem>
  </VideoClipTrackItem>

  <AudioClipTrackItem ObjectID="500"
                      ClassID="064ec682-9ba6-11d5-af2d-9ca32c7d6164" Version="11">
    <ClipTrackItem Version="8">
      <TrackItem Version="3">
        <Start>0</Start>
        <End>254016000000</End>
      </TrackItem>
      <SubClip ObjectRef="601"/>
    </ClipTrackItem>
  </AudioClipTrackItem>

  <SubClip ObjectID="600"
           ClassID="e0c58dc9-dbdd-4166-aef7-5db7e3f22e84" Version="5">
    <Clip ObjectRef="700"/>
    <MasterClip ObjectURef="mc-uid-001"/>
    <Name>intro_clip.mp4</Name>
  </SubClip>

  <SubClip ObjectID="601"
           ClassID="e0c58dc9-dbdd-4166-aef7-5db7e3f22e84" Version="5">
    <Clip ObjectRef="800"/>
    <MasterClip ObjectURef="mc-uid-002"/>
    <Name>narration.wav</Name>
  </SubClip>

  <MasterClip ObjectUID="mc-uid-001"
              ClassID="fb11c33a-b0a9-4465-aa94-b6d5db2628cf" Version="11">
    <Name>intro_clip.mp4</Name>
    <Clips Version="1">
      <Clip ObjectRef="700"/>
    </Clips>
  </MasterClip>

  <MasterClip ObjectUID="mc-uid-002"
              ClassID="fb11c33a-b0a9-4465-aa94-b6d5db2628cf" Version="11">
    <Name>narration.wav</Name>
    <Clips Version="1">
      <Clip ObjectRef="800"/>
    </Clips>
  </MasterClip>

  <!-- Chain elements (not in INDEXED_TAGS, used by second iterparse pass) -->
  <VideoClip ObjectID="700"
             ClassID="test-vc" Version="1">
    <Clip Version="1">
      <Source ObjectRef="900"/>
      <PlaybackSpeed>2.5</PlaybackSpeed>
    </Clip>
  </VideoClip>

  <AudioClip ObjectID="800"
             ClassID="test-ac" Version="1">
    <Clip Version="1">
      <Source ObjectRef="901"/>
    </Clip>
  </AudioClip>

  <VideoMediaSource ObjectID="900"
                    ClassID="test-vms" Version="1">
    <MediaSource Version="1">
      <Media ObjectURef="media-uid-001"/>
    </MediaSource>
  </VideoMediaSource>

  <AudioMediaSource ObjectID="901"
                    ClassID="test-ams" Version="1">
    <MediaSource Version="1">
      <Media ObjectURef="media-uid-002"/>
    </MediaSource>
  </AudioMediaSource>

  <Media ObjectUID="media-uid-001"
         ClassID="7a5c103e-f3ac-4391-b6b4-7cc3d2f9a7ff" Version="28">
    <FilePath>C:\\Projects\\Media\\intro_clip.mp4</FilePath>
    <Title>intro_clip.mp4</Title>
    <ActualMediaFilePath>C:\\Projects\\Media\\intro_clip.mp4</ActualMediaFilePath>
  </Media>

  <Media ObjectUID="media-uid-002"
         ClassID="7a5c103e-f3ac-4391-b6b4-7cc3d2f9a7ff" Version="28">
    <FilePath>C:\\Projects\\Media\\narration.wav</FilePath>
    <Title>narration.wav</Title>
    <ActualMediaFilePath>C:\\Projects\\Media\\narration.wav</ActualMediaFilePath>
  </Media>

  <ClipProjectItem ObjectUID="cpi-uid-001"
                   ClassID="cb4e0ed7-aca1-4171-8525-e3658dec06dd" Version="1">
    <ProjectItem Version="1"><Name>intro_clip.mp4</Name></ProjectItem>
    <MasterClip ObjectURef="mc-uid-001"/>
  </ClipProjectItem>

  <BinProjectItem ObjectUID="bin-uid-001"
                  ClassID="dbfd6653-24da-480e-a35e-ba45e9504e4b" Version="11">
    <ProjectItem Version="1"><Name>Media Bin</Name></ProjectItem>
  </BinProjectItem>

</PremiereData>
"""


# ---------------------------------------------------------------------------
# _build_chain_maps_from_bytes
# ---------------------------------------------------------------------------


class TestBuildChainMaps:
    """Tests for _build_chain_maps_from_bytes()."""

    def test_extracts_vc_to_source(self):
        xml_bytes = CHAIN_XML.encode("utf-8")
        vc_to_source, ms_to_media, vc_to_speed = _build_chain_maps_from_bytes(xml_bytes)
        # VideoClip 700 -> Source 900
        assert vc_to_source.get(700) == 900

    def test_extracts_ac_to_source(self):
        xml_bytes = CHAIN_XML.encode("utf-8")
        vc_to_source, ms_to_media, vc_to_speed = _build_chain_maps_from_bytes(xml_bytes)
        # AudioClip 800 -> Source 901
        assert vc_to_source.get(800) == 901

    def test_extracts_ms_to_media(self):
        xml_bytes = CHAIN_XML.encode("utf-8")
        vc_to_source, ms_to_media, vc_to_speed = _build_chain_maps_from_bytes(xml_bytes)
        # VideoMediaSource 900 -> media-uid-001
        assert ms_to_media.get(900) == "media-uid-001"
        # AudioMediaSource 901 -> media-uid-002
        assert ms_to_media.get(901) == "media-uid-002"

    def test_extracts_vc_to_speed(self):
        """VideoClip 700 has PlaybackSpeed=2.5 -> vc_to_speed[700] == 2.5."""
        xml_bytes = CHAIN_XML.encode("utf-8")
        vc_to_source, ms_to_media, vc_to_speed = _build_chain_maps_from_bytes(xml_bytes)
        assert vc_to_speed.get(700) == 2.5

    def test_no_playback_speed_absent_from_map(self):
        """AudioClip 800 has no PlaybackSpeed -> absent, not defaulted here
        (the 100.0 default is applied later, at Clip construction)."""
        xml_bytes = CHAIN_XML.encode("utf-8")
        vc_to_source, ms_to_media, vc_to_speed = _build_chain_maps_from_bytes(xml_bytes)
        assert 800 not in vc_to_speed

    def test_empty_xml_returns_empty_maps(self):
        xml = b'<?xml version="1.0"?><PremiereData Version="3"></PremiereData>'
        vc, ms, speed = _build_chain_maps_from_bytes(xml)
        assert vc == {}
        assert ms == {}
        assert speed == {}

    def test_invalid_xml_returns_empty_maps(self):
        """Gracefully handles invalid XML."""
        vc, ms, speed = _build_chain_maps_from_bytes(b"not xml at all")
        assert vc == {}
        assert ms == {}
        assert speed == {}


class TestBuildChainMapsFromFile:
    """Tests for _build_chain_maps() reading from a real file path.

    Real-world .prproj files are sometimes gzip-compressed and sometimes
    plain XML. _build_chain_maps must handle both, matching the same
    fallback behavior as _open_prproj_stream in index.py.
    """

    def test_extracts_chain_from_gzip_file(self, tmp_path):
        fpath = tmp_path / "chain.prproj"
        with gzip.open(str(fpath), "wb") as f:
            f.write(CHAIN_XML.encode("utf-8"))
        vc_to_source, ms_to_media, vc_to_speed = _build_chain_maps(str(fpath))
        assert vc_to_source.get(700) == 900
        assert ms_to_media.get(900) == "media-uid-001"

    def test_extracts_chain_from_raw_xml_file(self, tmp_path):
        """Raw (non-gzip) .prproj files must not silently fall back to
        an empty chain map — this was a real bug: the deterministic
        chain pass caught the gzip.BadGzipFile exception and returned
        empty dicts, forcing every real project to rely on heuristic
        title/filename matching instead of the accurate reference chain.
        """
        fpath = tmp_path / "chain_raw.prproj"
        fpath.write_text(CHAIN_XML, encoding="utf-8")
        vc_to_source, ms_to_media, vc_to_speed = _build_chain_maps(str(fpath))
        assert vc_to_source.get(700) == 900
        assert ms_to_media.get(900) == "media-uid-001"


# ---------------------------------------------------------------------------
# _build_masterclip_to_media_map
# ---------------------------------------------------------------------------


class TestBuildMasterclipToMediaMap:
    """Tests for _build_masterclip_to_media_map()."""

    def test_deterministic_chain_resolves(self):
        xml_bytes = CHAIN_XML.encode("utf-8")
        index = ProjectIndex.from_xml_string(xml_bytes)
        vc_to_source, ms_to_media, vc_to_speed = _build_chain_maps_from_bytes(xml_bytes)
        mc_map = _build_masterclip_to_media_map(index, vc_to_source, ms_to_media)

        # mc-uid-001 should resolve to media with intro_clip.mp4
        info = mc_map.get("mc-uid-001")
        assert info is not None
        assert "intro_clip.mp4" in (info.best_path or "")

    def test_heuristic_fallback(self):
        """When chain maps are empty, heuristic title match should work."""
        xml_bytes = CHAIN_XML.encode("utf-8")
        index = ProjectIndex.from_xml_string(xml_bytes)
        # Pass empty chain maps to force heuristic
        mc_map = _build_masterclip_to_media_map(index, {}, {})

        # Should still resolve via title match
        info = mc_map.get("mc-uid-001")
        assert info is not None


# ---------------------------------------------------------------------------
# _extract_media_info
# ---------------------------------------------------------------------------


class TestExtractMediaInfo:
    """Tests for _extract_media_info()."""

    def test_extracts_all_fields(self):
        from xml.etree.ElementTree import Element, SubElement

        media = Element("Media")
        SubElement(media, "FilePath").text = "/path/file.mp4"
        SubElement(media, "Title").text = "file.mp4"
        SubElement(media, "ActualMediaFilePath").text = "/actual/file.mp4"
        SubElement(media, "RelativePath").text = "rel/file.mp4"

        info = _extract_media_info(media)
        assert info.file_path == "/path/file.mp4"
        assert info.title == "file.mp4"
        assert info.actual_path == "/actual/file.mp4"
        assert info.relative_path == "rel/file.mp4"

    def test_missing_fields_are_none(self):
        from xml.etree.ElementTree import Element

        media = Element("Media")
        info = _extract_media_info(media)
        assert info.file_path is None
        assert info.title is None


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------


class TestResolver:
    """Tests for Resolver class."""

    def test_resolve_with_xml_bytes(self):
        xml_bytes = CHAIN_XML.encode("utf-8")
        index = ProjectIndex.from_xml_string(xml_bytes)
        resolver = Resolver(index, xml_bytes=xml_bytes)
        project = resolver.resolve_project("test.prproj")

        assert isinstance(project, Project)
        assert len(project.sequences) == 1

    def test_resolved_sequence_has_clips(self):
        xml_bytes = CHAIN_XML.encode("utf-8")
        index = ProjectIndex.from_xml_string(xml_bytes)
        resolver = Resolver(index, xml_bytes=xml_bytes)
        project = resolver.resolve_project()

        seq = project.sequences[0]
        assert seq.name == "Chain Test"
        assert seq._resolved is True
        # Should have at least 1 video clip and 1 audio clip
        assert len(seq.video_clips) >= 1
        assert len(seq.audio_clips) >= 1

    def test_resolved_clips_have_media(self):
        xml_bytes = CHAIN_XML.encode("utf-8")
        index = ProjectIndex.from_xml_string(xml_bytes)
        resolver = Resolver(index, xml_bytes=xml_bytes)
        project = resolver.resolve_project()

        seq = project.sequences[0]
        video_clips = seq.video_clips
        # At least one clip should have resolved media
        clips_with_media = [c for c in video_clips if c.media is not None]
        assert len(clips_with_media) >= 1

    def test_clip_speed_percent_from_playback_speed(self):
        """Real-world .prproj files commonly speed-ramp clips (verified:
        1032 PlaybackSpeed occurrences across 51 real DW project files).
        The video SubClip in CHAIN_XML has PlaybackSpeed=2.5 on its
        VideoClip element -> should surface as speed_percent=250.0.
        """
        xml_bytes = CHAIN_XML.encode("utf-8")
        index = ProjectIndex.from_xml_string(xml_bytes)
        resolver = Resolver(index, xml_bytes=xml_bytes)
        project = resolver.resolve_project()

        seq = project.sequences[0]
        video_clip = seq.video_clips[0]
        assert video_clip.speed_percent == 250.0

    def test_clip_speed_percent_defaults_to_100(self):
        """A clip with no PlaybackSpeed element (normal speed) defaults
        to 100.0, not None — callers shouldn't need a None-check for the
        overwhelmingly common case."""
        xml_bytes = CHAIN_XML.encode("utf-8")
        index = ProjectIndex.from_xml_string(xml_bytes)
        resolver = Resolver(index, xml_bytes=xml_bytes)
        project = resolver.resolve_project()

        seq = project.sequences[0]
        audio_clip = seq.audio_clips[0]
        assert audio_clip.speed_percent == 100.0

    def test_sequence_frame_rate(self):
        xml_bytes = CHAIN_XML.encode("utf-8")
        index = ProjectIndex.from_xml_string(xml_bytes)
        resolver = Resolver(index, xml_bytes=xml_bytes)
        project = resolver.resolve_project()

        seq = project.sequences[0]
        assert seq.frame_rate == 25.0

    def test_resolver_without_chain_data(self):
        """Resolver works even without file_path or xml_bytes (heuristic only)."""
        xml_bytes = CHAIN_XML.encode("utf-8")
        index = ProjectIndex.from_xml_string(xml_bytes)
        resolver = Resolver(index)  # no file_path, no xml_bytes
        project = resolver.resolve_project()

        assert len(project.sequences) == 1


# ---------------------------------------------------------------------------
# resolve() convenience function
# ---------------------------------------------------------------------------


class TestResolveFunction:
    """Tests for the resolve() convenience function."""

    def test_resolve_returns_project(self):
        xml_bytes = CHAIN_XML.encode("utf-8")
        index = ProjectIndex.from_xml_string(xml_bytes)
        project = resolve(index, xml_bytes=xml_bytes)

        assert isinstance(project, Project)
        assert len(project.sequences) == 1

    def test_resolve_stores_file_path(self):
        xml_bytes = CHAIN_XML.encode("utf-8")
        index = ProjectIndex.from_xml_string(xml_bytes)
        project = resolve(index, file_path="my_project.prproj", xml_bytes=xml_bytes)

        assert project.file_path == "my_project.prproj"
