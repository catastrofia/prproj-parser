"""Shared test fixtures for prproj_parser tests.

Provides minimal XML fixtures that mirror the Premiere Pro .prproj structure
without requiring actual project files.
"""

import gzip
import os
import sys

import pytest

# Ensure the library is importable from the source tree
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


# ---------------------------------------------------------------------------
# Minimal XML fixture representing a small Premiere Pro project
# ---------------------------------------------------------------------------

MINIMAL_PROJECT_XML = """\
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
      <TrackGroup Version="1" Index="2">
        <First>d8143ffe-eec4-4d2a-a909-d5f7bf094dc5</First>
        <Second ObjectRef="300"/>
      </TrackGroup>
    </TrackGroups>
    <Name>Test Sequence</Name>
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

  <DataTrackGroup ObjectID="300"
                  ClassID="b714b71d-6838-48dd-9b77-db19088ced7e" Version="1">
    <TrackGroup Version="1">
      <FrameRate>10160640000</FrameRate>
      <NextTrackID>1</NextTrackID>
    </TrackGroup>
  </DataTrackGroup>

  <VideoClipTrack ObjectUID="vtrack-uid-001"
                  ClassID="f68dcd81-8805-11d5-af2d-9bfa89d4ddd4" Version="11">
    <ClipTrack Version="2">
      <Track Version="3">
        <Index>0</Index>
      </Track>
      <ClipItems Version="3">
        <TrackItems Version="1">
          <TrackItem Index="0" ObjectRef="400"/>
          <TrackItem Index="1" ObjectRef="401"/>
        </TrackItems>
      </ClipItems>
    </ClipTrack>
  </VideoClipTrack>

  <AudioClipTrack ObjectUID="atrack-uid-001"
                  ClassID="f68dcd81-8805-11d5-af2d-9bfa89d4ddd5" Version="11">
    <ClipTrack Version="2">
      <Track Version="3">
        <Index>0</Index>
      </Track>
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

  <VideoClipTrackItem ObjectID="401"
                      ClassID="368b0406-29e3-4923-9fcd-094fbf9a1089" Version="6">
    <ClipTrackItem Version="8">
      <TrackItem Version="3">
        <Start>254016000000</Start>
        <End>508032000000</End>
      </TrackItem>
      <SubClip ObjectRef="601"/>
    </ClipTrackItem>
  </VideoClipTrackItem>

  <AudioClipTrackItem ObjectID="500"
                      ClassID="064ec682-9ba6-11d5-af2d-9ca32c7d6164" Version="11">
    <ClipTrackItem Version="8">
      <TrackItem Version="3">
        <Start>0</Start>
        <End>508032000000</End>
      </TrackItem>
      <SubClip ObjectRef="602"/>
    </ClipTrackItem>
  </AudioClipTrackItem>

  <SubClip ObjectID="600"
           ClassID="e0c58dc9-dbdd-4166-aef7-5db7e3f22e84" Version="5">
    <MasterClip ObjectURef="mc-uid-001"/>
    <Name>intro_clip.mp4</Name>
  </SubClip>

  <SubClip ObjectID="601"
           ClassID="e0c58dc9-dbdd-4166-aef7-5db7e3f22e84" Version="5">
    <MasterClip ObjectURef="mc-uid-002"/>
    <Name>background.png</Name>
  </SubClip>

  <SubClip ObjectID="602"
           ClassID="e0c58dc9-dbdd-4166-aef7-5db7e3f22e84" Version="5">
    <MasterClip ObjectURef="mc-uid-003"/>
    <Name>narration.wav</Name>
  </SubClip>

  <MasterClip ObjectUID="mc-uid-001"
              ClassID="fb11c33a-b0a9-4465-aa94-b6d5db2628cf" Version="11">
    <Name>intro_clip.mp4</Name>
  </MasterClip>

  <MasterClip ObjectUID="mc-uid-002"
              ClassID="fb11c33a-b0a9-4465-aa94-b6d5db2628cf" Version="11">
    <Name>background.png</Name>
  </MasterClip>

  <MasterClip ObjectUID="mc-uid-003"
              ClassID="fb11c33a-b0a9-4465-aa94-b6d5db2628cf" Version="11">
    <Name>narration.wav</Name>
  </MasterClip>

  <ClipProjectItem ObjectUID="cpi-uid-001"
                   ClassID="cb4e0ed7-aca1-4171-8525-e3658dec06dd" Version="1">
    <ProjectItem Version="1">
      <Name>intro_clip.mp4</Name>
    </ProjectItem>
    <MasterClip ObjectURef="mc-uid-001"/>
  </ClipProjectItem>

  <ClipProjectItem ObjectUID="cpi-uid-002"
                   ClassID="cb4e0ed7-aca1-4171-8525-e3658dec06dd" Version="1">
    <ProjectItem Version="1">
      <Name>background.png</Name>
    </ProjectItem>
    <MasterClip ObjectURef="mc-uid-002"/>
  </ClipProjectItem>

  <Media ObjectUID="media-uid-001"
         ClassID="7a5c103e-f3ac-4391-b6b4-7cc3d2f9a7ff" Version="28">
    <FilePath>C:\\Projects\\Media\\intro_clip.mp4</FilePath>
    <Title>intro_clip.mp4</Title>
    <ActualMediaFilePath>C:\\Projects\\Media\\intro_clip.mp4</ActualMediaFilePath>
  </Media>

  <Media ObjectUID="media-uid-002"
         ClassID="7a5c103e-f3ac-4391-b6b4-7cc3d2f9a7ff" Version="28">
    <FilePath>C:\\Projects\\Media\\background.png</FilePath>
    <Title>background.png</Title>
    <ActualMediaFilePath>C:\\Projects\\Media\\background.png</ActualMediaFilePath>
  </Media>

  <Media ObjectUID="media-uid-003"
         ClassID="7a5c103e-f3ac-4391-b6b4-7cc3d2f9a7ff" Version="28">
    <FilePath>C:\\Projects\\Media\\narration.wav</FilePath>
    <Title>narration.wav</Title>
    <ActualMediaFilePath>C:\\Projects\\Media\\narration.wav</ActualMediaFilePath>
  </Media>

  <BinProjectItem ObjectUID="bin-uid-001"
                  ClassID="dbfd6653-24da-480e-a35e-ba45e9504e4b" Version="11">
    <ProjectItem Version="1">
      <Name>Media Bin</Name>
    </ProjectItem>
  </BinProjectItem>

  <!-- Non-indexed elements (should be cleared during parse) -->
  <VideoComponentParam ObjectID="9001" ClassID="test" Version="1">
    <Name>Opacity</Name>
  </VideoComponentParam>
  <VideoFilterComponent ObjectID="9002" ClassID="test" Version="1">
    <Name>Motion</Name>
  </VideoFilterComponent>

</PremiereData>
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def minimal_xml():
    """Return the minimal project XML as a string."""
    return MINIMAL_PROJECT_XML


@pytest.fixture
def minimal_xml_bytes():
    """Return the minimal project XML as UTF-8 bytes."""
    return MINIMAL_PROJECT_XML.encode("utf-8")


@pytest.fixture
def minimal_gzip_file(tmp_path):
    """Create a temporary gzip-compressed .prproj file and return its path."""
    fpath = tmp_path / "test_project.prproj"
    with gzip.open(str(fpath), "wb") as f:
        f.write(MINIMAL_PROJECT_XML.encode("utf-8"))
    return str(fpath)


@pytest.fixture
def minimal_index(minimal_xml):
    """Build a ProjectIndex from the minimal XML fixture."""
    from prproj_parser.index import ProjectIndex

    return ProjectIndex.from_xml_string(minimal_xml)


@pytest.fixture
def minimal_project(minimal_gzip_file):
    """Load a fully-resolved Project from the minimal fixture."""
    from prproj_parser import load

    return load(minimal_gzip_file)


# ---------------------------------------------------------------------------
# Real project file fixtures (skip if not available)
# ---------------------------------------------------------------------------
#
# Real .prproj files are not committed by default (they can be large and
# may contain personal file-system paths). Drop sanitized sample projects
# into tests/fixtures/real/ locally to exercise these tests; CI runs
# whatever is committed there, and the tests skip gracefully if empty.

REAL_FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "real")


def _real_fixture_paths():
    """Return all .prproj files in tests/fixtures/real/, or []."""
    if not os.path.isdir(REAL_FIXTURES_DIR):
        return []
    return sorted(
        os.path.join(REAL_FIXTURES_DIR, f)
        for f in os.listdir(REAL_FIXTURES_DIR)
        if f.endswith(".prproj")
    )


@pytest.fixture(params=_real_fixture_paths())
def real_project_path(request):
    """Parametrized fixture: one test run per file in fixtures/real/.

    Skips (rather than errors) when no real fixtures are present.
    """
    return request.param
