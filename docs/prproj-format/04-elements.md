# Element Reference

*Doc version 1.1 — 2026-09-18*

`.prproj` files use dozens of element types. Most of the effort in
understanding this format goes into the handful that carry your actual
timeline, media, and clip data — everything else is UI state (panel layout,
column widths, "was this bin expanded") that you can safely ignore for most
purposes.

This reference covers the elements you actually need, with sanitized examples taken from test projects. Elements are grouped by role.

## Project-level

### `Project`

The root object. Appears once. Its `Version` attribute is how you identify
which Premiere Pro release wrote the file (see [Version Differences](03-versions.md)).

```xml
<Project ObjectID="1" ClassID="62ad66dd-0dcd-42da-a660-6d8fbde94876" Version="42">
    <RootProjectItem ObjectURef="9ed1d31b-8ed0-4145-8c21-0fad5ce72cf8"/>
    <ProjectSettings ObjectRef="3"/>
    ...
    <NextSequenceID>15</NextSequenceID>
    <NextID>1000020</NextID>
</Project>
```

`NextID` is Premiere's own bookkeeping — the next `ObjectID` it will assign
when you add something. Not needed for reading a project, but useful if
you're ever generating one.

### `RootProjectItem`, `BinProjectItem`, `ClipProjectItem`

These three make up the Project panel (the bin/folder tree you see in
Premiere's UI). `RootProjectItem` is the top of the tree; `BinProjectItem`
is a folder; `ClipProjectItem` is a clip sitting in a bin.

```xml
<BinProjectItem ObjectUID="f29370ce-0a2a-4015-8087-58c919afe13e" ...>
    <ProjectItem Version="1">
        <Name>01 Master</Name>
    </ProjectItem>
    <ProjectItemContainer Version="1">
        <Items Version="1">
            <Item Index="0" ObjectURef="ac73c854-844b-4983-a1ac-89f1913571a7"/>
        </Items>
    </ProjectItemContainer>
</BinProjectItem>
```

`Items` lists the bin's contents by reference — could be more bins, or
clips. `ClipProjectItem` looks similar but points at a `MasterClip` instead
of holding an item list:

```xml
<ClipProjectItem ObjectUID="84f91df0-9c74-4825-994f-5eee630642e8" ...>
    <ProjectItem Version="1">
        <Name>clip.mov</Name>
    </ProjectItem>
    <MasterClip ObjectURef="e382832f-f598-4c22-b0a2-5413836d2bc8"/>
</ClipProjectItem>
```

## Sequences and tracks

### `Sequence`

A timeline. Its `<Name>` is what you see in the Timeline panel tab. It
doesn't contain its tracks directly — it points at exactly three
`TrackGroup` entries (video, audio, data), each referencing the actual
track-group element by `ObjectRef`.

```xml
<Sequence ObjectUID="946f1366-99f8-4cd6-8d22-f858a7967568" ... Version="11">
    <TrackGroups Version="1">
        <TrackGroup Version="1" Index="0">
            <First>228cda18-3625-4d2d-951e-348879e4ed93</First>  <!-- media-type marker, not useful -->
            <Second ObjectRef="791"/>                             <!-- -> VideoTrackGroup -->
        </TrackGroup>
        <TrackGroup Version="1" Index="1">
            <First>80b8e3d5-6dca-4195-aefb-cb5f407ab009</First>
            <Second ObjectRef="792"/>                             <!-- -> AudioTrackGroup -->
        </TrackGroup>
        <TrackGroup Version="1" Index="2">
            <First>d8143ffe-eec4-4d2a-a909-d5f7bf094dc5</First>
            <Second ObjectRef="793"/>                             <!-- -> DataTrackGroup (captions) -->
        </TrackGroup>
    </TrackGroups>
    <Name>Example Sequence</Name>
    <ID>13</ID>
</Sequence>
```

Index 0 is always video, index 1 is always audio, index 2 is always data.
The `<First>` value is a fixed GUID identifying the media type; it's always
the same three GUIDs in the same order and isn't otherwise useful.

### `VideoTrackGroup` / `AudioTrackGroup` / `DataTrackGroup`

Holds the list of tracks for one media type, plus the sequence's frame rate
(video group) or sample-timing base (audio group) — see
[Timing & Ticks](06-timing.md) for what `<FrameRate>` actually means here.

```xml
<VideoTrackGroup ObjectID="791" ... Version="13">
    <TrackGroup Version="1">
        <Tracks Version="1">
            <Track Index="0" ObjectURef="4f497cd6-df1c-4b4b-adb5-2071fe66ec84"/>
            <Track Index="1" ObjectURef="ff0731e5-2460-4f03-b92f-b7eb7dbf2861"/>
            <!-- one per video track, V1, V2, V3... in Index order -->
        </Tracks>
        <FrameRate>10160640000</FrameRate>   <!-- ticks per video frame -->
        <NextTrackID>10</NextTrackID>
    </TrackGroup>
    <FrameRect>0,0,1080,1920</FrameRect>     <!-- sequence frame size, video only -->
    <PixelAspectRatio>1,1</PixelAspectRatio>
</VideoTrackGroup>
```

`AudioTrackGroup` looks the same but its `<FrameRate>` means ticks per audio
sample, not per frame — see [Timing & Ticks](06-timing.md) for the
conversion math, which is different for the two.

An `AudioTrackGroup` also has a `<MasterTrack>` reference, which is not one
of the ordinary tracks in its `<Tracks>` list — it points at an
`AudioMixTrack`, covered below.

`DataTrackGroup` (captions/subtitles) is much sparser and, in projects with
no captions, has no `<Tracks>` at all:

```xml
<DataTrackGroup ObjectID="793" ... Version="1">
    <TrackGroup Version="1">
        <FrameRate>10160640000</FrameRate>
        <NextTrackID>1</NextTrackID>
    </TrackGroup>
</DataTrackGroup>
```

### `VideoClipTrack` / `AudioClipTrack` / `CaptionDataClipTrack`

One of these per track (V1, V2, A1, etc). Contains track-level flags
(locked, muted, sync-locked) and, importantly, the **list of clips and
transitions on that track** — via two separate lists, `ClipItems` and
`TransitionItems`, each wrapping a `TrackItems` list of `TrackItem`
references:

```xml
<VideoClipTrack ObjectUID="4f59e6d9-bb6d-4568-906a-61b4a402726d" ... Version="1">
    <ClipTrack Version="2">
        <Track Version="3">
            <IsLocked>false</IsLocked>
            <Index>3</Index>
            <IsMuted>false</IsMuted>
            <IsSyncLocked>true</IsSyncLocked>
            <ID>4</ID>
        </Track>
        <ClipItems Version="3">
            <TrackItems Version="1">
                <TrackItem Index="0" ObjectRef="1057"/>   <!-- -> VideoClipTrackItem -->
            </TrackItems>
        </ClipItems>
        <TransitionItems Version="3">
            <TrackItems Version="1">
                <TrackItem Index="0" ObjectRef="1058"/>   <!-- -> VideoTransitionTrackItem -->
            </TrackItems>
        </TransitionItems>
    </ClipTrack>
</VideoClipTrack>
```

**Important:** the `<Track>` element itself never holds clip references —
only track metadata (locked/muted/index/id). Clip references only ever live
inside `ClipItems` / `TransitionItems`, both of which wrap their contents in
a nested `<TrackItems>` element (not to be confused with the parent
`ClipItems` itself, despite the near-identical name — see
[Parser Gotchas](08-gotchas.md)).

### `AudioMixTrack` — the sequence's master audio track

Every sequence has exactly one `AudioMixTrack`, referenced by
`AudioTrackGroup.MasterTrack`. It's a different element type from the
ordinary `AudioClipTrack`s that hold your A1/A2/etc. clips — it represents
the mix bus that all of the sequence's audio tracks feed into (equivalent
to the "Master" strip in the Audio Track Mixer panel), and it's where the
overall track panning and channel routing live:

```xml
<AudioTrackGroup ObjectID="792" ... Version="6">
    <MasterTrack ObjectRef="978"/>   <!-- -> AudioMixTrack -->
    ...
</AudioTrackGroup>

<AudioMixTrack ObjectID="978" ... Version="4">
    <AudioTrack Version="11">
        <Panner ObjectRef="1072"/>          <!-- -> DefaultPanProcessor / StereoToStereoPanProcessor -->
        <ChannelType>1</ChannelType>
        <FrameRate>5292000</FrameRate>       <!-- ticks per audio sample, same as AudioTrackGroup -->
    </AudioTrack>
    <Inlet ObjectRef="1073"/>               <!-- -> AudioTrackInlet -->
</AudioMixTrack>
```

The `Inlet` reference resolves to an `AudioTrackInlet`, which is what
actually lists which of the sequence's ordinary audio tracks feed into this
mix track:

```xml
<AudioTrackInlet ObjectID="1073" ... Version="3">
    <Sources Version="1">
        <Source Index="0" ObjectURef="cc0f45b6-41a5-43ba-8c59-42ac681d941d"/>   <!-- -> AudioClipTrack -->
    </Sources>
</AudioTrackInlet>
```

For most timeline/media extraction purposes you can ignore `AudioMixTrack`
entirely — the actual clips live on the ordinary `AudioClipTrack`s described
above, regardless of how they're mixed down. It matters if you need to
reproduce panning, channel routing, or per-sequence audio output
configuration.

## Clips on the timeline

### `VideoClipTrackItem` / `AudioClipTrackItem`

A single clip instance sitting on a track. Holds its timeline position
(`Start`/`End`, in ticks — see [Timing & Ticks](06-timing.md)), a reference
to the `SubClip` that names its source, and — if it has a transition on
either end — a reference to that transition.

```xml
<VideoClipTrackItem ObjectID="1057" ClassID="368b0406-29e3-4923-9fcd-094fbf9a1089" Version="6">
    <ClipTrackItem Version="8">
        <ComponentOwner Version="1">
            <Components ObjectRef="1103"/>       <!-- -> VideoComponentChain (effects) -->
        </ComponentOwner>
        <TrackItem Version="3">
            <Start>0</Start>
            <End>1127831040000</End>
        </TrackItem>
        <SubClip ObjectRef="1104"/>              <!-- -> SubClip -->
        <HeadTransition ObjectRef="1058"/>       <!-- -> VideoTransitionTrackItem, if any -->
    </ClipTrackItem>
    <FrameRect>0,0,1080,1920</FrameRect>
    <PixelAspectRatio>1,1</PixelAspectRatio>
</VideoClipTrackItem>
```

`AudioClipTrackItem` mirrors this exactly, and can additionally carry a
`TailTransition` reference alongside `HeadTransition`.

### `VideoTransitionTrackItem` / `AudioTransitionTrackItem`

A transition (cross dissolve, wipe, etc). Also has its own `Start`/`End`
(the span of the transition, not the whole clip) plus the effect name:

```xml
<VideoTransitionTrackItem ObjectID="1058" ... Version="5">
    <TransitionTrackItem Version="3">
        <TrackItem Version="3">
            <Start>0</Start>
            <End>121927680000</End>
        </TrackItem>
        <DisplayName>Cross Dissolve</DisplayName>
        <MatchName>AE.ADBE Cross Dissolve New</MatchName>
        <HasOutgoingClip>false</HasOutgoingClip>
        <HasIncomingClip>true</HasIncomingClip>
    </TransitionTrackItem>
    <VideoFilterComponent ObjectRef="1105"/>
</VideoTransitionTrackItem>
```

### `SubClip`

The bridge between a timeline clip and its source media. Holds the display
`<Name>` you actually see on the clip, plus a reference to the owning
`MasterClip`:

```xml
<SubClip ObjectID="1104" ClassID="e0c58dc9-dbdd-4166-aef7-5db7e3f22e84" Version="5">
    <Clip ObjectRef="1358"/>                                        <!-- -> VideoClip / AudioClip -->
    <MasterClip ObjectURef="742c7adb-93b1-4931-a2b6-cd82e0995c39"/>  <!-- -> MasterClip -->
    <OrigChGrp>0</OrigChGrp>
    <Name>clip.mov</Name>
</SubClip>
```

### `MasterClip`

The project-panel-level representation of an imported item — one per
imported file (or nested sequence). Its `<Name>` is what shows up in the
Project panel bin. It can own more than one `Clip` (a video track plus its
audio track, for example):

```xml
<MasterClip ObjectUID="742c7adb-93b1-4931-a2b6-cd82e0995c39" ... Version="11">
    <LoggingInfo ObjectRef="268"/>
    <Clips Version="1">
        <Clip Index="0" ObjectRef="269"/>
    </Clips>
    <Name>clip.mov</Name>
    <MasterClipChangeVersion>12</MasterClipChangeVersion>
</MasterClip>
```

### `VideoClip` / `AudioClip`

Binds a `MasterClip`'s `Clip` slot to an actual media source, and carries
the **source** in/out points (where in the source file the clip starts and
ends — different from the `Start`/`End` on the timeline `TrackItem`; see
[Timing & Ticks](06-timing.md)):

```xml
<VideoClip ObjectID="1358" ClassID="9308dbef-2440-4acb-9ab2-953b9a4e82ec" Version="11">
    <Clip Version="18">
        <Source ObjectRef="614"/>              <!-- -> VideoMediaSource -->
        <ClipID>5d03d563-ea87-4305-92d4-cba80188e35b</ClipID>
        <InPoint>914457600000000</InPoint>
        <OutPoint>915585431040000</OutPoint>
    </Clip>
</VideoClip>
```

If the clip's speed has been changed, this same element also carries
`<PlaybackSpeed>` (a constant multiplier) and/or `<TimeRemapping>` (an
animated speed curve) — see [Timing & Ticks](06-timing.md) for how those
affect the `InPoint`/`OutPoint` math, since they're easy to get wrong.

### `VideoMediaSource` / `AudioMediaSource`

The layer between a `Clip` and the actual `Media` file entry:

```xml
<VideoMediaSource ObjectID="614" ... Version="2">
    <MediaSource Version="4">
        <Media ObjectURef="90aedb11-761b-462b-8b6c-e9382c1b43c9"/>   <!-- -> Media -->
    </MediaSource>
    <OriginalDuration>10973491200000000</OriginalDuration>
</VideoMediaSource>
```

### `Media`

The actual file reference — the disk path, in Premiere's own bookkeeping
format:

```xml
<Media ObjectUID="90aedb11-761b-462b-8b6c-e9382c1b43c9" ... Version="28">
    <VideoStream ObjectRef="1004"/>
    <RelativePath>.\IN\clip.mov</RelativePath>
    <FilePath>C:\Media\Project\IN\clip.mov</FilePath>
    <Title>clip.mov</Title>
    <FileKey>cedb785d-850d-486a-9a22-07ecacbdf83b</FileKey>
</Media>
```

Not every `Media` element points at a real file on disk. Premiere's built-in
generators — Color Matte, Black Video, Bars and Tone, and title/graphic
clips — are also represented as `Media` elements, but with a plain numeric
`<FilePath>` (an internal ID, not a filesystem path) instead of a real path:

```xml
<Media ObjectUID="f231426a-0664-4585-aec7-50bb8551c6aa" ... Version="28">
    <VideoStream ObjectRef="1023"/>
    <FilePath>1112293707</FilePath>
    <Title>Black Video</Title>
    <Infinite>true</Infinite>
</Media>
```

Check whether `<FilePath>` parses as a path or as a bare integer before
treating it as a file reference.

### `VideoStream` / `AudioStream`

Technical metadata about the actual media file: its own native frame rate
(which can be a completely different number from the sequence's frame rate
— see [Timing & Ticks](06-timing.md)), duration, codec, frame size:

```xml
<VideoStream ObjectID="1004" ... Version="19">
    <FrameRate>10160640000</FrameRate>
    <Duration>10973491200000000</Duration>
    <FrameRect>0,0,1080,1920</FrameRect>
</VideoStream>
```

## Effects

### `VideoComponentChain` / `AudioComponentChain`, `VideoFilterComponent` / `AudioFilterComponent`

A clip's applied effects (Lumetri Color, Cross Dissolve, Gaussian Blur,
Motion, Opacity, etc.) hang off its `ClipTrackItem.ComponentOwner`, which
points at a `VideoComponentChain`/`AudioComponentChain` — an ordered list of
effects on that clip:

```xml
<VideoComponentChain ObjectID="1103" ... Version="3">
    <ComponentChain Version="3">
        <Components Version="1">
            <Component Index="0" ObjectRef="1360"/>   <!-- e.g. built-in "Motion" -->
            <Component Index="1" ObjectRef="1361"/>   <!-- e.g. built-in "Opacity" -->
        </Components>
    </ComponentChain>
</VideoComponentChain>
```

Each `Component` reference resolves to a `VideoFilterComponent` /
`AudioFilterComponent`. Its `<MatchName>` is the effect's internal
identifier and the most reliable way to know which effect it is — for
built-in effects it looks like `AE.ADBE Cross Dissolve New` or
`AE.ADBE Lumetri`, regardless of the current Premiere Pro UI language
(`<DisplayName>` is localized and shouldn't be used to identify an effect
programmatically):

```xml
<VideoFilterComponent ObjectID="1360" ... Version="9">
    <Component Version="6">
        <Params Version="1">
            <Param Index="0" ObjectRef="1773"/>
            <!-- ...one Param per effect parameter... -->
        </Params>
        <DisplayName>Motion</DisplayName>
        <Intrinsic>true</Intrinsic>
    </Component>
    <MatchName>AE.ADBE Motion</MatchName>
</VideoFilterComponent>
```

Note that an "Adjustment Layer" or a Lumetri-graded clip isn't a distinct
element type in this schema — an adjustment layer is an ordinary `Media`/
`MasterClip` with `<AdjustmentLayer>true</AdjustmentLayer>` set, and Lumetri
Color is an ordinary `VideoFilterComponent` with
`<MatchName>AE.ADBE Lumetri</MatchName>` — both fit the patterns already
described above and in [Media](#media) without any special-casing.

### `VideoComponentParam` / `AudioComponentParam` and keyframed values

Each `Param` reference inside a `VideoFilterComponent`/`AudioFilterComponent`
resolves to a `VideoComponentParam`/`AudioComponentParam` — one effect
parameter (e.g. "Scale Height", "Opacity", "Position"). A parameter that
isn't animated just has a single `<StartKeyframe>` tuple; a parameter with
`<IsTimeVarying>true</IsTimeVarying>` has an animation curve in its
`<Keyframes>` element instead:

```xml
<VideoComponentParam ObjectID="2838" ... Version="9">
    <IsTimeVarying>true</IsTimeVarying>
    <ParameterID>3</ParameterID>
    <Name>Scale Height</Name>
    <StartKeyframe>-91445760000000000,300.,0,0,0,0,0,0</StartKeyframe>
    <Keyframes>914457600000000,300.,5,0,0,0.16666666666666666,278.56756280828546,1;914518563840000,525.,0,0,937.50000000085265,0.16666666666666666,-8124.9999999150195,0.16666666666666666;...</Keyframes>
    <CurrentValue>300</CurrentValue>
</VideoComponentParam>
```

What's confirmed about the `<Keyframes>` format on `VideoComponentParam` /
`AudioComponentParam` / `TimeComponentParam`: it's a `;`-separated list
of keyframes, each a `,`-separated tuple of 8 fields (`PointComponentParam`
uses 14 fields, for its 2D value — see below). The **first field is always
a tick position** (on the same absolute tick timeline as everything else —
see [Timing & Ticks](06-timing.md)) and the **second field is always the
parameter's value** at that keyframe. The remaining fields are
almost certainly interpolation-related (ease-in/ease-out handle values and
an interpolation-mode flag are the most likely candidates, based on where
small integers like `0`, `4`, `5` show up alongside float-looking
handle values) but their exact per-field meaning was **not** conclusively
decoded — see [Open Questions](09-open-questions.md). If you only need
"does this parameter change over time, and what's its value at time T," you
can get the first two fields of the nearest keyframes and interpolate
linearly as an approximation; for exact-match round-tripping (rewriting a
project without altering its stored curves) you should preserve the
`<Keyframes>` string byte-for-byte rather than trying to reconstruct it.

`ArbVideoComponentParam` and `PointComponentParam` are variants of the same
idea for parameter types that don't fit a single scalar (respectively: an
arbitrary base64-encoded blob, e.g. for a LUT reference; and a 2D point,
e.g. for the Motion effect's Position parameter) — they follow the same
`StartKeyframe`/`Keyframes` pattern with a different value encoding per
keyframe entry. `TimeComponentParam` (the curve referenced by a clip's
`TimeRemapping` for an animated speed ramp — see
[Timing & Ticks](06-timing.md)) uses this same `StartKeyframe`/`Keyframes`
pattern too, with the value field representing speed rather than an effect
parameter.

## Markers

### `Markers` / `Marker`

A sequence or clip can own a `Markers` container, which lists individual
`Marker` references. Each `Marker`'s time and comment are stored as a JSON
blob under `<DVAMarker>`:

```xml
<Marker ObjectID="920" ... Version="3">
    <DVAMarker>{"DVAMarker":{"mMarkerID":"3cb08bcd-...","mStartTime":{"ticks":914528724480000},"mType":"Comment"}}</DVAMarker>
</Marker>
```

The `ticks` value inside that JSON uses the same tick system as everything
else — see [Timing & Ticks](06-timing.md).

## Linking video and audio

### `Link`

Groups a video `TrackItem` with its synced audio `TrackItem` (e.g. a video
clip and the audio that was captured with it), so that moving one moves the
other:

```xml
<Link ObjectID="601" ... Version="1">
    <TrackItemGroup Version="1">
        <TrackItems Version="1">
            <TrackItem Index="0" ObjectRef="743"/>   <!-- video clip -->
            <TrackItem Index="1" ObjectRef="744"/>   <!-- its linked audio clip -->
        </TrackItems>
    </TrackItemGroup>
</Link>
```

## Captions

### `CaptionDataClipTrack` / `CaptionDataClipTrackItem`

Captions live on the sequence's data track and follow the same
`ClipItems`/`TrackItems` pattern as video and audio clips. Each caption's
actual text is stored not as plain XML text but as a base64-encoded binary
blob under `<Block><FormattedTextData>`, alongside the font name used:

```xml
<CaptionDataClipTrackItem ObjectID="2647" ... Version="3">
    <DataClipTrackItem Version="1">
        <ClipTrackItem Version="8">
            <TrackItem Version="3">
                <Start>0</Start>
                <End>396264960000</End>
            </TrackItem>
            <SubClip ObjectRef="3661"/>
        </ClipTrackItem>
    </DataClipTrackItem>
    <BlockVector Version="1">
        <BlockVectorItem Index="0" ObjectRef="3662"/>   <!-- -> Block -->
    </BlockVector>
</CaptionDataClipTrackItem>
```

The referenced `Block` element's `<FormattedTextData>` decodes (base64) to a
binary structure that embeds caption text as UTF-8, plus the font family name.
Extracting caption text therefore requires decoding this blob rather than
reading an XML text node directly; the exact binary layout beyond "UTF-8 text
plus a font name string are present as sub-strings" was not fully
reverse-engineered — see [Open Questions](09-open-questions.md).
