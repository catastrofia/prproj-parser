# Timing & Ticks

*Doc version 1.1 — 2026-09-18*

Premiere Pro doesn't store time as seconds or frame numbers directly. Every
timing value in a `.prproj` file — clip positions, in/out points, marker
times, durations — is stored in **ticks**, a fixed-size integer unit.

## The tick constant

```
254,016,000,000 ticks = 1 second
```

This single constant is used everywhere in the file, for both video and
audio, and for every frame rate. To convert ticks to seconds:

```python
seconds = ticks / 254_016_000_000
```

To go the other way — ticks per frame, for a given frame rate:

```python
ticks_per_frame = 254_016_000_000 / fps
```

This matches real values found directly in the files. For example, at 25
fps: `254_016_000_000 / 25 = 10_160_640_000` — exactly the `<FrameRate>`
value stored inside a `VideoTrackGroup` for a 25fps sequence. At 23.976 fps
(`24000/1001`): `10_594_584_000`. At 29.97 fps: `8_475_667_200`.

The constant also divides cleanly into standard audio sample rates: at
48,000 Hz, `254_016_000_000 / 48000 = 5,292,000` — exactly the
`<FrameRate>` value found inside an `AudioTrackGroup` for a 48kHz project.
At 44,100 Hz: `5,760,000`. At 96,000 Hz: `2,646,000`.

The constant is fixed regardless of the sequence's actual frame rate or
sample rate — it's simply a large common denominator (in fact, a multiple
of frame counts for every common broadcast frame rate) chosen so that every
common fps and sample rate divides it into a whole number.

## `<FrameRate>` means something different depending on where it appears

This is a common point of confusion, because the same element name,
`<FrameRate>`, is used for two different things depending on context:

| Location | What it actually means |
|---|---|
| Inside a `VideoTrackGroup` | Ticks **per video frame**, for this sequence |
| Inside an `AudioTrackGroup` | Ticks **per audio sample**, for this sequence |
| Inside a `VideoStream` (a source media file) | The *source file's own* native frame rate — can differ from the sequence's |

A `VideoStream`'s frame rate describes the camera/file's native capture
rate, which has nothing to do with the sequence it's placed into — a 30fps
clip can sit in a 25fps sequence without any special marker; Premiere just
resamples it during playback/export. If you need "what's the sequence's
frame rate," read it from the `VideoTrackGroup`, not from any individual
clip's `VideoStream`.

Frame rates aren't always round numbers, either — one project in the wild
used a `VideoTrackGroup` frame rate corresponding to roughly 30.01 fps
(`254_016_000_000 / 8_464_321_152 ≈ 30.0102`), most likely from footage shot
on a device with a slightly non-standard capture rate. Don't assume the
value will always match one of the "clean" broadcast frame rates.

## `Start`/`End` vs `InPoint`/`OutPoint`

These two pairs of values look similar but mean completely different things,
and live on different elements:

- **`<Start>` / `<End>`** — on a `TrackItem` (inside a `VideoClipTrackItem`,
  `AudioClipTrackItem`, or transition item). This is the clip's position
  **on the timeline** — where it starts and ends relative to the start of
  the sequence.
- **`<InPoint>` / `<OutPoint>`** — on a `VideoClip`/`AudioClip` element
  (the source-binding layer, one step further down the reference chain —
  see [Traversing a Timeline](05-traversal.md)). This is where **within the
  source media file** the clip's content begins and ends — the same in/out
  points you'd set by trimming a clip in the Source Monitor.

Trimming a clip's head in the timeline changes `Start`; trimming what part
of the source file is used changes `InPoint`. They're independent, and
`InPoint`/`OutPoint` values are frequently astronomically large numbers
(sometimes into the tens of trillions of ticks) because they're measured
from an arbitrary zero point in the source file's own timeline, not from
"0 seconds into this specific clip."

One version-specific detail worth knowing: starting with Premiere Pro 2026,
`<Start>` is omitted from the XML entirely (rather than written as
`<Start>0</Start>`) whenever a clip starts exactly at position 0. See
[Version Differences](03-versions.md) for the full explanation and the code
fix needed.

## Clip speed changes affect the `InPoint`/`OutPoint` math

If a clip's playback speed has been changed (right-click a clip → Speed/
Duration in Premiere), its `VideoClip`/`AudioClip` element carries a
`<PlaybackSpeed>` multiplier, and the amount of source media consumed
(`OutPoint - InPoint`) will **not** equal the amount of timeline space it
occupies (`End - Start`) — it's scaled by that multiplier instead:

```xml
<VideoClip ObjectID="1031" ...>
    <Clip Version="18">
        <Source ObjectRef="1032"/>
        <PlaybackSpeed>2</PlaybackSpeed>
        <InPoint>33713003520000</InPoint>
        <OutPoint>36761195520000</OutPoint>
    </Clip>
</VideoClip>
```

This clip's `OutPoint - InPoint` is `3,048,192,000,000` ticks of source
material, but on the timeline its corresponding `VideoClipTrackItem`'s
`End - Start` is `1,524,096,000,000` ticks — exactly half, matching the
`PlaybackSpeed` of `2` (2× speed plays twice as much source per unit of
timeline time). A `PlaybackSpeed` between 0 and 1 is a slow-motion clip; the
same relationship holds — a 0.5× clip's source range is half its timeline
duration.

If you're computing "what part of the source file does this timeline clip
actually show," you need `PlaybackSpeed` in the calculation, not just
`InPoint`/`OutPoint` and `Start`/`End` — mismatch here is a common source of
subtly-wrong duration math when speed-changed clips are in the mix. `1`
(the default, unchanged speed) was not seen written explicitly on every
clip — some clips at normal speed simply omit `<PlaybackSpeed>` entirely, so
treat a missing value as `1`, not as an error.

A clip whose speed is **animated over time** (a speed ramp, rather than one
constant multiplier) additionally carries a `<TimeRemapping>` reference
instead of, or alongside, `PlaybackSpeed`:

```xml
<VideoClip ObjectID="1031" ...>
    <Clip Version="18">
        <Source ObjectRef="1032"/>
        <TimeRemapping ObjectRef="1033"/>
        <PlaybackSpeed>2</PlaybackSpeed>
        <InPoint>33713003520000</InPoint>
        <OutPoint>36761195520000</OutPoint>
    </Clip>
</VideoClip>

<TimeRemapping ObjectID="1033" ...>
    <Keyframes ObjectRef="1034"/>   <!-- -> TimeComponentParam -->
</TimeRemapping>
```

The referenced `TimeComponentParam` holds the actual speed-over-time curve
in its `<Keyframes>` string — see [Element Reference](04-elements.md) for
what's confirmed (and not confirmed) about that format. `TimeRemapping` was
rare in the test corpus (found in only one of 51 files) compared to plain
constant-speed `PlaybackSpeed`, which appeared in the large majority of
files across every Premiere Pro version checked — so constant-speed changes
are the common case to design for; ramped speed is the exception.

## Marker timing

A `Marker` element's time isn't a plain XML value — it's embedded inside a
JSON string:

```xml
<Marker ObjectID="1024" ... Version="3">
    <DVAMarker>{"DVAMarker":{"mMarkerID":"...","mStartTime":{"ticks":914528724480000},"mType":"Comment"}}</DVAMarker>
</Marker>
```

The `"ticks"` value inside that JSON blob uses the exact same tick constant
as everything else — divide by `254_016_000_000` to get seconds.
