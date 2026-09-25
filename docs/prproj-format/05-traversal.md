# Traversing a Timeline

*Doc version 1.0 — 2026-09-18*

This walks through reading a representative clip end to end — from "which sequence is
this" down to "what file is on disk" — using the reference chain described
in [Object Model](02-object-model.md) and [Element Reference](04-elements.md).

The example sequence is named "Example Sequence", and the clip we'll follow is the first
one on video track 1.

## Step 1 — Find the sequence

Sequences are top-level elements identified by `<Name>`:

```xml
<Sequence ObjectUID="946f1366-99f8-4cd6-8d22-f858a7967568" ... Version="11">
    <Name>Example Sequence</Name>
    ...
</Sequence>
```

## Step 2 — Get its video track group

The sequence's `TrackGroups` list points at the video track group via
`ObjectRef` at `Index="0"` (always video — see
[Element Reference](04-elements.md)):

```xml
<TrackGroup Version="1" Index="0">
    <Second ObjectRef="791"/>
</TrackGroup>
```

```xml
<VideoTrackGroup ObjectID="791" ... Version="13">
    <Tracks Version="1">
        <Track Index="0" ObjectURef="4f497cd6-df1c-4b4b-adb5-2071fe66ec84"/>
        ...
    </Tracks>
</VideoTrackGroup>
```

## Step 3 — Get the first track

`Index="0"` is the first video track (V1):

```xml
<VideoClipTrack ObjectUID="4f497cd6-df1c-4b4b-adb5-2071fe66ec84" ... Version="1">
    <ClipTrack Version="2">
        <ClipItems Version="3">
            <TrackItems Version="1">
                <TrackItem Index="0" ObjectRef="1057"/>
            </TrackItems>
        </ClipItems>
    </ClipTrack>
</VideoClipTrack>
```

## Step 4 — Get the clip's timeline position

```xml
<VideoClipTrackItem ObjectID="1057" ... Version="6">
    <ClipTrackItem Version="8">
        <TrackItem Version="3">
            <Start>0</Start>
            <End>1127831040000</End>
        </TrackItem>
        <SubClip ObjectRef="1104"/>
    </ClipTrackItem>
</VideoClipTrackItem>
```

The clip sits from tick `0` to tick `1127831040000` on the timeline. See
[Timing & Ticks](06-timing.md) to convert that to seconds/frames.

## Step 5 — Get its display name

```xml
<SubClip ObjectID="1104" ... Version="5">
    <Clip ObjectRef="1358"/>
    <MasterClip ObjectURef="742c7adb-93b1-4931-a2b6-cd82e0995c39"/>
    <Name>clip.mov</Name>
</SubClip>
```

`clip.mov` is the name shown for this clip.

## Step 6 — Follow it down to the actual file

```xml
<VideoClip ObjectID="1358" ... Version="11">
    <Clip Version="18">
        <Source ObjectRef="614"/>
        <InPoint>914457600000000</InPoint>
        <OutPoint>915585431040000</OutPoint>
    </Clip>
</VideoClip>
```

```xml
<VideoMediaSource ObjectID="614" ... Version="2">
    <MediaSource Version="4">
        <Media ObjectURef="90aedb11-761b-462b-8b6c-e9382c1b43c9"/>
    </MediaSource>
</VideoMediaSource>
```

```xml
<!-- Synthetic sanitized path example -->
<Media ObjectUID="90aedb11-761b-462b-8b6c-e9382c1b43c9" ... Version="28">
    <FilePath>C:\Media\Project\IN\clip.mov</FilePath>
</Media>
```

## Full chain, summarized

```
Sequence "Example Sequence"
  -> VideoTrackGroup (Index 0)
    -> VideoClipTrack (V1)
      -> VideoClipTrackItem  (Start=0, End=1127831040000)
        -> SubClip           (Name = "clip.mov")
          -> MasterClip
          -> VideoClip       (InPoint / OutPoint into the source file)
            -> VideoMediaSource
              -> Media       (FilePath = C:\Media\...\clip.mov)
```

Every hop in this chain is a lookup by `ObjectRef` → `ObjectID` or
`ObjectURef` → `ObjectUID` against the depth-2 index described in
[Object Model](02-object-model.md). There is no shortcut that skips a step
— e.g. a `SubClip` never points directly at a `Media` element, it always
goes through `MasterClip`/`VideoClip`/`VideoMediaSource` first.

## Doing the same for audio, transitions, and captions

- Audio clips follow the identical chain, just with `AudioClipTrackItem` /
  `AudioClip` / `AudioMediaSource` / `AudioStream` in place of the video
  equivalents.
- A clip with a transition on one end also has a `HeadTransition` (and/or
  `TailTransition`) reference from its `ClipTrackItem`, pointing at a
  `VideoTransitionTrackItem` / `AudioTransitionTrackItem` — see
  [Element Reference](04-elements.md).
- Captions follow the same pattern via `CaptionDataClipTrack` and
  `CaptionDataClipTrackItem`, but the actual caption text requires an extra
  decoding step — see [Element Reference](04-elements.md).
