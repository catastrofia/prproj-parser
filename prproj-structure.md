# Premiere Pro `.prproj` XML Structure Reference

> **Purpose:** Complete technical reference for parsing `.prproj` files. Covers file format, XML layout, element types, reference chains, timing, and edge cases — verified across 25 real-world test projects.

---

## 1. File Format

| Property | Value |
|----------|-------|
| Extension | `.prproj` |
| Compression | **gzip** (standard). Some files may be raw XML (starts with `<?xml`) |
| Encoding | UTF-8 |
| Root element | `<PremiereData Version="3">` |
| All test projects | Version `"3"` (as of Premiere Pro 2023–2026) |

### Opening a `.prproj` file

```python
import gzip

with open(path, "rb") as f:
    data = f.read()
try:
    xml_bytes = gzip.decompress(data)
except gzip.BadGzipFile:
    xml_bytes = data  # Already raw XML
```

---

## 2. Flat Object Graph Architecture

**This is the most important concept.** Premiere does NOT use a hierarchical XML tree where sequences contain tracks which contain clips. Instead:

- **All major elements are siblings** — direct children of `<PremiereData>` at depth 1.
- Elements reference each other via **ID/UID attributes**.
- The XML is essentially a **serialized object graph**, not a document tree.

### 2.1 Reference Attributes

| Attribute | On Element | Points To | Type |
|-----------|-----------|-----------|------|
| `ObjectID` | Definition | — | Integer (e.g., `ObjectID="530"`) |
| `ObjectUID` | Definition | — | UUID string (e.g., `ObjectUID="5dd3f44f-..."`) |
| `ObjectRef` | Reference child | Another element's `ObjectID` | Integer |
| `ObjectURef` | Reference child | Another element's `ObjectUID` | UUID string |

**Key rule:** `ObjectRef` always points to an `ObjectID`. `ObjectURef` always points to an `ObjectUID`. Some elements have both `ObjectID` and `ObjectUID`.

### 2.2 Depth Structure

```
<PremiereData Version="3">          ← depth 1 (root)
  <Sequence ObjectUID="..." ...>    ← depth 2 (all major elements live here)
    <Name>My Sequence</Name>        ← depth 3 (children of major elements)
    <TrackGroups>                   ← depth 3
      <TrackGroup Index="0">        ← depth 4
        ...
  <VideoTrackGroup ObjectID="177">  ← depth 2 (sibling, NOT nested in Sequence)
  <VideoClipTrack ObjectUID="...">  ← depth 2
  <VideoClipTrackItem ObjectID="208"> ← depth 2
  <SubClip ObjectID="310">          ← depth 2
  <MasterClip ObjectUID="...">      ← depth 2
  <Media ObjectUID="...">           ← depth 2
  ...thousands more elements...
```

**All parseable elements are at depth 2.** Their internal children (depth 3+) contain the actual data (names, timing, references to other depth-2 elements).

---

## 3. Element Types & Their Structure

### 3.1 Element Census (from 25 test projects)

| Tag Name | Role | Typical Count (small/large project) |
|----------|------|-------------------------------------|
| `Sequence` | Timeline sequence | 2 / 40 |
| `VideoTrackGroup` | Video track container | = sequence count |
| `AudioTrackGroup` | Audio track container | = sequence count |
| `DataTrackGroup` | Data/caption track container | = sequence count |
| `VideoClipTrack` | Single video track | 11 / 119 |
| `AudioClipTrack` | Single audio track | 5 / 32 |
| `VideoClipTrackItem` | Video clip on timeline | 66 / 291 |
| `AudioClipTrackItem` | Audio clip on timeline | 18 / 118 |
| `SubClip` | Clip reference (name + master ref) | 84 / 9108 |
| `MasterClip` | Master clip definition | 18 / 46 |
| `ClipProjectItem` | Project bin item for a clip | 21 / 46 |
| `Media` | Media file reference | 16 / 42 |
| `BinProjectItem` | Bin/folder in project panel | varies |
| `Markers` | Marker container | 15 / 551 |
| `VideoComponentParam` | Video effect parameter | 1651 / 6628 (MOST COMMON) |
| `VideoFilterComponent` | Video effect | 187 / 744 |
| `VideoComponentChain` | Effect chain | 67 / 293 |
| `AudioComponentParam` | Audio effect parameter | 19 / 370 |
| `AudioComponentChain` | Audio effect chain | 32 / 195 |

**Key insight:** `VideoComponentParam` is by far the most common element (often 50%+ of all depth-2 elements). These are video effect parameters and are **irrelevant for timeline extraction**. Clearing them during iterparse saves massive memory.

### 3.2 Sequence

```xml
<Sequence ObjectUID="e8794ff6-19a4-4302-8412-e57772c56576"
          ClassID="6a15d903-8739-11d5-af2d-9b7855ad8974" Version="11">
  <Node Version="1">
    <Properties Version="1">
      <!-- Many UI/export settings as child elements with long property names -->
      <MZ.Sequence.PreviewFrameSizeWidth>608</MZ.Sequence.PreviewFrameSizeWidth>
      <MZ.Sequence.PreviewFrameSizeHeight>1080</MZ.Sequence.PreviewFrameSizeHeight>
      <!-- ... dozens more properties ... -->
    </Properties>
  </Node>
  <TrackGroups Version="1">
    <TrackGroup Version="1" Index="0">
      <First>228cda18-3625-4d2d-951e-348879e4ed93</First>   <!-- MediaType GUID -->
      <Second ObjectRef="177"/>                               <!-- → VideoTrackGroup -->
    </TrackGroup>
    <TrackGroup Version="1" Index="1">
      <First>80b8e3d5-6dca-4195-aefb-cb5f407ab009</First>   <!-- MediaType GUID -->
      <Second ObjectRef="178"/>                               <!-- → AudioTrackGroup -->
    </TrackGroup>
    <TrackGroup Version="1" Index="2">
      <First>d8143ffe-eec4-4d2a-a909-d5f7bf094dc5</First>   <!-- MediaType GUID -->
      <Second ObjectRef="179"/>                               <!-- → DataTrackGroup -->
    </TrackGroup>
  </TrackGroups>
  <Name>SteelV1</Name>
  <ID>1</ID>
</Sequence>
```

**Verified across all 25 projects:** Every Sequence has exactly **3 TrackGroups**:
- Index 0 → `VideoTrackGroup` (via `ObjectRef`)
- Index 1 → `AudioTrackGroup` (via `ObjectRef`)
- Index 2 → `DataTrackGroup` (via `ObjectRef`)

The `<First>` element contains a MediaType GUID (not useful for parsing). The `<Second ObjectRef="...">` points to the actual TrackGroup element.

### 3.3 VideoTrackGroup / AudioTrackGroup

```xml
<VideoTrackGroup ObjectID="177"
                 ClassID="9e9abf7a-0918-49c2-91ae-991b5dde77bb" Version="13">
  <TrackGroup Version="1">
    <Tracks Version="1">
      <Track Index="0" ObjectURef="eb5f6af9-b5bb-4321-9491-3419340e1dce"/>
      <Track Index="1" ObjectURef="14868296-1b3c-473b-861f-dddb93d41020"/>
      <Track Index="2" ObjectURef="9e4c0fac-efa4-4e3b-81e0-c9d255271935"/>
      <Track Index="3" ObjectURef="d8383f0a-ddfc-4d6b-95d4-63017b2b816c"/>
    </Tracks>
    <FrameRate>10594584000</FrameRate>    <!-- ticks per frame for VIDEO -->
    <NextTrackID>5</NextTrackID>
  </TrackGroup>
  <FrameRect>0,0,1080,1920</FrameRect>   <!-- Video-only: frame dimensions -->
  <!-- ... other video settings ... -->
</VideoTrackGroup>
```

```xml
<AudioTrackGroup ObjectID="178"
                 ClassID="9b9238b9-53a8-4cc3-b03f-b36246d052e6" Version="6">
  <TrackGroup Version="1">
    <Tracks Version="1">
      <Track Index="0" ObjectURef="cb5ff3b0-3fa7-4cdc-bc94-74293a1a36a5"/>
      <!-- ... more tracks ... -->
    </Tracks>
    <FrameRate>5292000</FrameRate>        <!-- ticks per SAMPLE for AUDIO -->
    <NextTrackID>6</NextTrackID>
  </TrackGroup>
  <MasterTrack ObjectRef="205"/>
  <!-- ... other audio settings ... -->
</AudioTrackGroup>
```

**Critical:** The `<FrameRate>` element has different meanings:
- In `VideoTrackGroup`: **ticks per video frame** (used for time conversion)
- In `AudioTrackGroup`: **ticks per audio sample** (NOT used for time conversion)

**Track references:** Each `<Track>` child uses `ObjectURef` to point to a `VideoClipTrack` or `AudioClipTrack`. The `Index` attribute gives the 0-based track number (V1=0, V2=1, etc.).

### 3.4 DataTrackGroup

```xml
<DataTrackGroup ObjectID="425"
                ClassID="b714b71d-6838-48dd-9b77-db19088ced7e" Version="1">
  <TrackGroup Version="1">
    <FrameRate>10594584000</FrameRate>
    <NextTrackID>1</NextTrackID>
  </TrackGroup>
</DataTrackGroup>
```

DataTrackGroups contain caption/subtitle tracks. They typically have no `<Tracks>` children and can be **skipped** for timeline clip extraction.

### 3.5 VideoClipTrack / AudioClipTrack

```xml
<VideoClipTrack ObjectUID="eb5f6af9-b5bb-4321-9491-3419340e1dce"
                ClassID="f68dcd81-8805-11d5-af2d-9bfa89d4ddd4" Version="11">
  <ClipTrack Version="2">
    <Track Version="3">
      <Node Version="1">
        <Properties Version="1">
          <TL.SQTrackShy>0</TL.SQTrackShy>
          <MZ.TrackTargeted>1</MZ.TrackTargeted>
          <!-- ... UI properties ... -->
        </Properties>
      </Node>
      <IsLocked>false</IsLocked>
      <MediaType>228cda18-3625-4d2d-951e-348879e4ed93</MediaType>
      <Index>0</Index>
      <IsMuted>false</IsMuted>
      <IsSyncLocked>true</IsSyncLocked>
      <ID>1</ID>
    </Track>
    <ClipItems Version="3">
      <TrackItems Version="1">
        <TrackItem Index="0" ObjectRef="208"/>   <!-- → VideoClipTrackItem -->
        <TrackItem Index="1" ObjectRef="209"/>
        <TrackItem Index="2" ObjectRef="210"/>
        <!-- ... more items ... -->
      </TrackItems>
      <MediaType>228cda18-3625-4d2d-951e-348879e4ed93</MediaType>
      <Index>0</Index>
    </ClipItems>
    <TransitionItems Version="3">
      <TrackItems Version="1">
        <TrackItem Index="0" ObjectRef="227"/>   <!-- → Transition items -->
      </TrackItems>
    </TransitionItems>
  </ClipTrack>
</VideoClipTrack>
```

**Key path to clip items:** `ClipTrack > ClipItems > TrackItems > TrackItem[ObjectRef]`

Each `<TrackItem>` uses `ObjectRef` to point to a `VideoClipTrackItem` or `AudioClipTrackItem`.

### 3.6 VideoClipTrackItem / AudioClipTrackItem

```xml
<VideoClipTrackItem ObjectID="208"
                    ClassID="368b0406-29e3-4923-9fcd-094fbf9a1089" Version="6">
  <ClipTrackItem Version="8">
    <ComponentOwner Version="1">
      <Components ObjectRef="309"/>    <!-- → VideoComponentChain (effects) -->
    </ComponentOwner>
    <TrackItem Version="3">
      <Start>0</Start>                 <!-- Timeline position in TICKS -->
      <End>275459184000</End>           <!-- Timeline position in TICKS -->
    </TrackItem>
    <SubClip ObjectRef="310"/>          <!-- → SubClip (clip identity) -->
  </ClipTrackItem>
  <FrameRect>0,0,1080,1920</FrameRect>
  <PixelAspectRatio>1,1</PixelAspectRatio>
</VideoClipTrackItem>
```

```xml
<AudioClipTrackItem ObjectID="505"
                    ClassID="064ec682-9ba6-11d5-af2d-9ca32c7d6164" Version="11">
  <ClipTrackItem Version="8">
    <ComponentOwner Version="1">
      <Components ObjectRef="544"/>
    </ComponentOwner>
    <TrackItem Version="3">
      <Start>8486261784000</Start>
      <End>9270261000000</End>
    </TrackItem>
    <SubClip ObjectRef="545"/>
  </ClipTrackItem>
  <ID>beee1b2a-4d59-49f1-8de4-5b702df7cc69</ID>
</AudioClipTrackItem>
```

**Key data:**
- `ClipTrackItem > TrackItem > Start` — timeline start position in ticks
- `ClipTrackItem > TrackItem > End` — timeline end position in ticks
- `ClipTrackItem > SubClip[ObjectRef]` — reference to SubClip for clip identity

### 3.7 SubClip

```xml
<SubClip ObjectID="310"
         ClassID="e0c58dc9-dbdd-4166-aef7-5db7e3f22e84" Version="5">
  <Clip ObjectRef="498"/>
  <MasterClip ObjectURef="f1b78c6e-2a6f-49b5-9deb-a128923823af"/>
  <OrigChGrp>0</OrigChGrp>
  <Name>6073148_Metalworker Steel Girders_By_Dmitrii_Borovikov__Artlist</Name>
</SubClip>
```

**Key data:**
- `<Name>` — the **display name** of the clip on the timeline (primary source for clip name)
- `<MasterClip ObjectURef>` — reference to the MasterClip (for media path resolution)
- `<Clip ObjectRef>` — reference to a VideoClip/AudioClip element (contains in/out points within the source media, not needed for timeline position)

### 3.8 MasterClip

```xml
<MasterClip ObjectUID="47600972-736e-4a7c-a34b-816d51331e0b"
            ClassID="fb11c33a-b0a9-4465-aa94-b6d5db2628cf" Version="11">
  <LoggingInfo ObjectRef="40"/>
  <AudioComponentChains Version="1">
    <AudioComponentChain Index="0" ObjectRef="41"/>
  </AudioComponentChains>
  <Clips Version="1">
    <Clip Index="0" ObjectRef="42"/>
    <Clip Index="1" ObjectRef="43"/>
  </Clips>
  <AudioClipChannelGroups ObjectRef="44"/>
  <Name>SteelV1</Name>
  <MasterClipChangeVersion>30603</MasterClipChangeVersion>
</MasterClip>
```

**Key data:**
- `<Name>` — master clip name (may differ from SubClip name)
- `ObjectUID` — used by SubClip's `<MasterClip ObjectURef>` to reference this element

**Note:** MasterClip does NOT directly reference Media. The connection goes through `ClipProjectItem`.

### 3.9 ClipProjectItem

```xml
<ClipProjectItem ObjectUID="566b9fa9-c049-437e-a408-8885d2dff273"
                 ClassID="cb4e0ed7-aca1-4171-8525-e3658dec06dd" Version="1">
  <ProjectItem Version="1">
    <Node Version="1">
      <Properties Version="1">
        <project.icon.view.grid.order>0</project.icon.view.grid.order>
        <Column.PropertyText.Label>BE.Prefs.LabelColors.3</Column.PropertyText.Label>
      </Properties>
    </Node>
    <Name>SteelV1</Name>
  </ProjectItem>
  <MasterClip ObjectURef="47600972-736e-4a7c-a34b-816d51331e0b"/>
</ClipProjectItem>
```

**Key data:**
- `<MasterClip ObjectURef>` — references the MasterClip this project item represents
- `<Name>` — display name in the project panel

**Important:** The ClipProjectItem → MasterClip link is a **reverse reference**. To find the Media for a MasterClip, you must search ClipProjectItems that reference that MasterClip's UID, then follow the ClipProjectItem to its Media. However, in practice the Media path is more directly accessible (see Section 4).

### 3.10 Media

```xml
<Media ObjectUID="ed6b1924-bc5b-4202-983f-d48d491fbc36"
       ClassID="7a5c103e-f3ac-4391-b6b4-7cc3d2f9a7ff" Version="28">
  <AudioStream ObjectRef="180"/>
  <VideoStream ObjectRef="427"/>          <!-- Present for video media -->
  <FilePath>C:\Users\...\Steel.wav</FilePath>
  <Title>Steel.wav</Title>
  <FileKey>02c1e31b-61b3-4fa1-8b34-cf307e33a080</FileKey>
  <RelativePath>.\IN\Steel.wav</RelativePath>
  <ActualMediaFilePath>C:\Users\...\Steel.wav</ActualMediaFilePath>
  <ConformedAudioRate>5760000</ConformedAudioRate>
  <ImplementationID>1fa18bfa-255c-44b1-ad73-56bcd99fceaf</ImplementationID>
</Media>
```

**Key data:**
- `<FilePath>` — absolute path to the media file
- `<ActualMediaFilePath>` — actual path (may differ if file was moved)
- `<RelativePath>` — path relative to the project file
- `<Title>` — human-readable title (usually filename)
- `<VideoStream ObjectRef>` — present only for video/image media
- `<AudioStream ObjectRef>` — present for audio and video-with-audio media

**Priority for path resolution:** `ActualMediaFilePath` > `FilePath` > `RelativePath`

### 3.11 BinProjectItem

```xml
<BinProjectItem ObjectUID="bcac9d46-5dd1-4abc-93b4-31f18f6b2d41"
                ClassID="dbfd6653-24da-480e-a35e-ba45e9504e4b" Version="11">
  <ProjectItem Version="1">
    <Node Version="1">
      <Properties Version="1"/>
    </Node>
    <Name>Cutouts</Name>
  </ProjectItem>
  <ProjectItemContainer Version="1">
    <Items Version="1">
      <Item Index="0" ObjectURef="37c4a3b2-7365-4ea5-abab-00cf8535fd4b"/>
      <Item Index="1" ObjectURef="cab42bf0-4c2a-42b9-8bc1-6bbc690bab33"/>
      <!-- ... more items ... -->
    </Items>
  </ProjectItemContainer>
</BinProjectItem>
```

Represents a folder/bin in the project panel. Items can be `ClipProjectItem` or other `BinProjectItem` UIDs.

### 3.12 Markers

```xml
<Markers ObjectID="174"
         ClassID="bee50706-b524-416c-9f03-b596ce5f6866" Version="4">
  <ByGUID>byGUID</ByGUID>
  <LastMetadataState>8f7f8d03-c273-b6c9-9904-ebed00000024</LastMetadataState>
  <LastContentState>8f7f8d03-c273-b6c9-9904-ebed00000024</LastContentState>
</Markers>
```

Markers are referenced by other elements. The actual marker data (position, name, color) is typically stored as JSON-encoded strings within marker child elements or in `DVAMarker` elements.

---

## 4. Complete Reference Chain

### 4.1 From Sequence to Clip Timing

```
Sequence
  └─ TrackGroups > TrackGroup[Index=0] > Second[ObjectRef] ──→ VideoTrackGroup[ObjectID]
                                                                  └─ TrackGroup > Tracks > Track[ObjectURef] ──→ VideoClipTrack[ObjectUID]
                                                                  │   └─ (also) FrameRate (ticks per frame)
                                                                  └─ ...
VideoClipTrack
  └─ ClipTrack > ClipItems > TrackItems > TrackItem[ObjectRef] ──→ VideoClipTrackItem[ObjectID]

VideoClipTrackItem
  └─ ClipTrackItem > TrackItem > Start (ticks)
  └─ ClipTrackItem > TrackItem > End (ticks)
  └─ ClipTrackItem > SubClip[ObjectRef] ──→ SubClip[ObjectID]

SubClip
  └─ Name (display name on timeline)
  └─ MasterClip[ObjectURef] ──→ MasterClip[ObjectUID]
```

### 4.2 From MasterClip to Media File

```
MasterClip[ObjectUID]
  ← ClipProjectItem > MasterClip[ObjectURef] (reverse lookup)

ClipProjectItem
  ← (associated Media found by matching)

Media
  └─ FilePath
  └─ ActualMediaFilePath
  └─ RelativePath
  └─ Title
```

**Note:** The MasterClip → Media connection is indirect. In the current app, media paths are found by iterating through SubClip/MasterClip children looking for path-like text in various tags. The library plan uses a more structured approach through ClipProjectItem.

### 4.3 Simplified Chain Diagram

```
Sequence ──ObjectRef──→ VideoTrackGroup ──ObjectURef──→ VideoClipTrack
                              │                              │
                         FrameRate                    ClipItems/TrackItems
                                                           │
                                                    ObjectRef to each
                                                           │
                                                    VideoClipTrackItem
                                                      │         │
                                                   Start/End  SubClip[ObjectRef]
                                                                 │
                                                              SubClip
                                                              │     │
                                                           Name  MasterClip[ObjectURef]
                                                                    │
                                                               MasterClip
                                                                    │
                                                          (reverse: ClipProjectItem
                                                           refs this MasterClip)
                                                                    │
                                                                 Media
                                                              │    │    │
                                                        FilePath Title ActualMediaFilePath
```

---

## 5. Timing System

### 5.1 Ticks

Premiere Pro uses an internal tick system for all timing:

| Constant | Value |
|----------|-------|
| **Ticks per second** | `254,016,000,000` (254 billion) |

All `<Start>` and `<End>` values in `TrackItem` elements are in ticks.

### 5.2 FrameRate Values (Ticks per Frame)

The `<FrameRate>` element in `VideoTrackGroup` stores **ticks per frame**:

| FrameRate Value | FPS | Notes |
|----------------|-----|-------|
| `10594584` | 23.976 | Standard (non-×1000) |
| `10594584000` | 23.976 | ×1000 variant (most common in test projects) |
| `10160640` | 25.0 | Standard |
| `10160640000` | 25.0 | ×1000 variant (common in test projects) |
| `8475667` | 29.97 | Standard |
| `8475667000` | 29.97 | ×1000 variant |
| `8475667200` | 29.97 | Alternate ×1000 variant |
| `8408400` | 30.0 | Standard |
| `8408400000` | 30.0 | ×1000 variant |
| `5297292` | 47.952 | Standard |
| `5297292000` | 47.952 | ×1000 variant |
| `5080320` | 50.0 | Standard |
| `5080320000` | 50.0 | ×1000 variant |
| `4237833` | 59.94 | Standard |
| `4237833000` | 59.94 | ×1000 variant |
| `4237833600` | 59.94 | Alternate ×1000 variant |
| `4204200` | 60.0 | Standard |
| `4204200000` | 60.0 | ×1000 variant |

**Observed in test projects:** `10594584000` (23.976fps) and `10160640000` (25fps) are the most common. One project had `8464321152` which calculates to ~30.01fps.

### 5.3 Audio FrameRate Values (Ticks per Sample)

The `<FrameRate>` in `AudioTrackGroup` stores **ticks per audio sample** (NOT video frames):

| FrameRate Value | Sample Rate | Calculation |
|----------------|-------------|-------------|
| `5292000` | 48,000 Hz | 254016000000 / 48000 = 5292000 |
| `5760000` | 44,100 Hz | 254016000000 / 44100 ≈ 5760000 |

**These should NOT be used for video time conversion.** Always use the `VideoTrackGroup`'s FrameRate.

### 5.4 Time Conversion Formula

```python
# Convert ticks to seconds (frame-aligned)
frames = round(ticks / ticks_per_frame)
seconds = frames / fps

# Where:
#   ticks = Start or End value from TrackItem
#   ticks_per_frame = FrameRate value from VideoTrackGroup
#   fps = looked up from FPS_MAP or calculated as TICKS_PER_SECOND / ticks_per_frame
```

### 5.5 FPS Detection Strategy

1. **Direct lookup** in FPS_MAP (exact match)
2. **Scale-down search** — divide by 10 repeatedly until a match is found (handles unexpected ×10/×100 variants)
3. **Arithmetic fallback** — `254016000000 / raw_frame_rate` (sanity check: 1–240 fps range)
4. **Default** — 29.97 fps if all else fails

---

## 6. Nested Sequences

### 6.1 How Nested Sequences Work

When a sequence is placed inside another sequence on the timeline, it appears as a regular clip. The detection mechanism is:

1. The `VideoClipTrackItem` has a `SubClip` reference (same as any clip)
2. The `SubClip` has a `<Name>` that **matches a known Sequence name**
3. The `SubClip` has a `<MasterClip ObjectURef>` pointing to a MasterClip that represents the sequence

**There is NO `SequenceSource` child element** in SubClips (verified across all 25 test projects, including projects with nested sequences). The current app's `sequence_flattener.py` checks for `SequenceSource` but this path is never hit in practice.

### 6.2 Detection Strategy

```python
# Build a set of all sequence names
sequence_names = {seq.name for seq in all_sequences}

# For each SubClip, check if its name matches a sequence
if subclip.name in sequence_names:
    # This is a nested sequence reference
    nested_seq = sequence_name_map[subclip.name]
    # Recursively flatten the nested sequence
```

### 6.3 Example from Test Projects

In `Testproject_2023.prproj` (40 sequences, 9108 SubClips):
- 8 SubClips have names matching sequence names (e.g., "Verschachtelte Sequenz 03", "Verschachtelte Sequenz 05")
- These SubClips still have normal `<MasterClip ObjectURef>` references
- No SubClips have `<SequenceSource>` children

---

## 7. Element Tag Statistics

### 7.1 Root-Level Children (Depth 2)

Across all test projects, the following tags appear as direct children of `<PremiereData>`:

**High-frequency (irrelevant for timeline extraction — clear immediately):**
- `VideoComponentParam` — 50-60% of all depth-2 elements
- `PointComponentParam` — effect control points
- `VideoFilterComponent` — video effects
- `ArbVideoComponentParam` — arbitrary video params
- `AudioComponentParam` — audio effect params
- `VideoComponentChain` — effect chains
- `AudioComponentChain` — audio effect chains
- `SecondaryContent` — secondary content refs
- `VideoClip` / `AudioClip` — clip source definitions (in/out points within source media)

**Medium-frequency (needed for timeline extraction — keep in index):**
- `Sequence`, `VideoTrackGroup`, `AudioTrackGroup`, `DataTrackGroup`
- `VideoClipTrack`, `AudioClipTrack`
- `VideoClipTrackItem`, `AudioClipTrackItem`
- `SubClip`, `MasterClip`, `ClipProjectItem`, `Media`
- `BinProjectItem`, `Markers`

**Low-frequency (metadata — optional):**
- `VideoSettings`, `AudioSettings`
- `ClipLoggingInfo`, `ClipChannelGroupVectorSerializer`
- `VideoMediaSource`, `VideoStream`

### 7.2 Unique Tag Count

| Project Size | Unique Tags (all depths) | Unique Root Tags (depth 2) | Total Elements |
|-------------|-------------------------|---------------------------|----------------|
| Small (71KB gz) | 447 | 54 | 27,510 |
| Medium (313KB gz) | 504 | 58 | 114,355 |
| Large (12MB gz) | ~500 | ~60 | ~1,000,000+ |

---

## 8. Indexed Tags for Efficient Parsing

Based on the analysis, the following tags should be indexed (kept in memory during iterparse):

```python
INDEXED_TAGS = {
    # Core timeline structure
    "Sequence",
    "VideoTrackGroup",
    "AudioTrackGroup",
    
    # Track containers
    "VideoClipTrack",
    "AudioClipTrack",
    
    # Clip items (timing)
    "VideoClipTrackItem",
    "AudioClipTrackItem",
    
    # Clip identity and media
    "SubClip",
    "MasterClip",
    "ClipProjectItem",
    "Media",
    
    # Optional (project structure)
    "BinProjectItem",
}
```

All other depth-2 elements (especially `VideoComponentParam`, `PointComponentParam`, `VideoFilterComponent`) should be **cleared immediately** during iterparse to save memory. This typically discards 80-90% of elements.

---

## 9. Edge Cases & Gotchas

### 9.1 File Format
- Some `.prproj` files are **not gzipped** (start with `<?xml`). Always try gzip first, fall back to raw.
- All observed projects use `Version="3"`. Other versions may have different structures.

### 9.2 Namespace Handling
- Premiere XML occasionally uses namespaces (`{http://...}TagName`). Always strip namespaces when comparing tag names.
- Use regex: `re.sub(r"\{[^}]*\}", "", tag)` or `tag.split("}")[-1]`

### 9.3 FrameRate Confusion
- `VideoTrackGroup.FrameRate` = ticks per video frame (use this for time conversion)
- `AudioTrackGroup.FrameRate` = ticks per audio sample (48kHz=5292000, 44.1kHz=5760000) — **do NOT use for time conversion**
- Some projects have ×1000 variants of frame rate values
- One test project had an unusual value `8464321152` (~30.01fps) — handle gracefully

### 9.4 Name Resolution Priority
1. `SubClip > Name` — primary display name
2. `MasterClip > Name` — fallback if SubClip has no name
3. `ClipProjectItem > ProjectItem > Name` — project panel name

### 9.5 Nested Sequence Detection
- Do NOT rely on `SequenceSource` child elements (never observed in practice)
- Match SubClip names against known Sequence names
- The SubClip's MasterClip reference still points to a valid MasterClip (which represents the sequence)

### 9.6 Track Indexing
- Track `Index` attribute is 0-based
- Human-readable labels: V1=Index 0, V2=Index 1, A1=Index 0, A2=Index 1
- Tracks may be empty (no ClipItems)

### 9.7 DataTrackGroup
- Always present (Index 2 in TrackGroups) but typically empty
- Contains caption/subtitle tracks — can be skipped for clip extraction

### 9.8 Duplicate Elements
- The same clip may appear as both `VideoClipTrackItem` and `AudioClipTrackItem` (video with audio)
- Deduplication by (name, start_time, end_time) is needed

### 9.9 Large Projects
- The largest test project (`DWVGENG251027_WeightLossDrugs.prproj`) is 57MB compressed, ~57MB+ XML
- `Testproject_2023.prproj` has 40 sequences and 9108 SubClips
- Memory-efficient parsing (iterparse + selective indexing) is essential

---

## 10. Test Project Summary

| Project | Size (gz) | Sequences | VTG | SubClips | MasterClips | Media | Video FPS |
|---------|-----------|-----------|-----|----------|-------------|-------|-----------|
| Steel_1 | 71KB | 2 | 2 | 84 | 18 | 16 | 23.976 |
| LightPollution_1 | 110KB | 2 | 2 | 70 | 44 | 42 | 23.976 |
| GEAnimals_1 | 313KB | 16 | 16 | 409 | 46 | 30 | 25.0 + 23.976 |
| Testproject_2023 | 12.4MB | 40 | 40 | 9108 | ~500 | ~400 | 25.0 |
| WeightLossDrugs | 57.3MB | 10 | 10 | ~5000 | ~200 | ~150 | 25.0 |

---

## 11. ClassID Reference

Each element type has a consistent ClassID across all projects:

| Tag | ClassID |
|-----|---------|
| `Sequence` | `6a15d903-8739-11d5-af2d-9b7855ad8974` |
| `VideoTrackGroup` | `9e9abf7a-0918-49c2-91ae-991b5dde77bb` |
| `AudioTrackGroup` | `9b9238b9-53a8-4cc3-b03f-b36246d052e6` |
| `DataTrackGroup` | `b714b71d-6838-48dd-9b77-db19088ced7e` |
| `VideoClipTrack` | `f68dcd81-8805-11d5-af2d-9bfa89d4ddd4` |
| `AudioClipTrack` | (varies by version) |
| `VideoClipTrackItem` | `368b0406-29e3-4923-9fcd-094fbf9a1089` |
| `AudioClipTrackItem` | `064ec682-9ba6-11d5-af2d-9ca32c7d6164` |
| `SubClip` | `e0c58dc9-dbdd-4166-aef7-5db7e3f22e84` |
| `MasterClip` | `fb11c33a-b0a9-4465-aa94-b6d5db2628cf` |
| `ClipProjectItem` | `cb4e0ed7-aca1-4171-8525-e3658dec06dd` |
| `Media` | `7a5c103e-f3ac-4391-b6b4-7cc3d2f9a7ff` |
| `BinProjectItem` | `dbfd6653-24da-480e-a35e-ba45e9504e4b` |
| `Markers` | `bee50706-b524-416c-9f03-b596ce5f6866` |

ClassIDs could be used as an alternative to tag names for element identification, but tag names are simpler and sufficient.
