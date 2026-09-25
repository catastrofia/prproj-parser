# Parser Gotchas

*Doc version 1.1 — 2026-09-18*

A collection of pitfalls that will silently produce wrong output rather than
crash — the dangerous kind.

## 1. `ObjectID` is not globally unique — only unique among top-level elements

Covered in full in [Object Model](02-object-model.md). If you index every
`ObjectID` in the file regardless of nesting depth, you will get collisions
between real objects and unrelated, deeply-nested UI-preference elements
that happen to reuse the same ID number. **Only index elements that are
direct children of `<PremiereData>`.**

## 2. `ClipItems` contains a *different* element also named `TrackItems`

Both a track's `ClipItems` and `TransitionItems` wrap their contents in a
child called `<TrackItems>`, and that in turn contains `<TrackItem>`
elements:

```xml
<ClipItems Version="3">
    <TrackItems Version="1">
        <TrackItem Index="0" ObjectRef="1057"/>
    </TrackItems>
</ClipItems>
```

If a track has no clips at all, `ClipItems` is present but empty (no
`<TrackItems>` child):

```xml
<ClipItems Version="3">
    <MediaType>228cda18-3625-4d2d-951e-348879e4ed93</MediaType>
    <Index>0</Index>
</ClipItems>
```

Don't assume `<TrackItems>` is always present just because `<ClipItems>` is.
Check for it explicitly, and treat its absence as "zero clips on this
track," not as an error.

## 3. `<Track>` never contains clip references

Despite the similar naming, the `<Track>` element inside a `ClipTrack` only
holds track-level metadata (locked/muted/sync-locked/index/ID) — never
`TrackItem` references. Clip and transition references only ever live in
the sibling `<ClipItems>` / `<TransitionItems>` elements. Don't look for
clips inside `<Track>`.

## 4. `<Start>` can be entirely absent, meaning zero — but only from Premiere Pro 2026 onward

Covered in [Version Differences](03-versions.md). From Project Version 45
onward, a `TrackItem` with a timeline start of `0` omits `<Start>` entirely,
rather than writing `<Start>0</Start>`. Always default a missing `<Start>`
to `0`; never assume `<End>` will also be missing (it wasn't observed to be
omitted at any position or version).

## 5. `Start`/`End` and `InPoint`/`OutPoint` are not interchangeable

Covered in full in [Timing & Ticks](06-timing.md). `Start`/`End` is
timeline position; `InPoint`/`OutPoint` is source-media trim range, and
lives on a completely different element (`VideoClip`/`AudioClip`, not
`TrackItem`). Mixing them up will give you a plausible-looking but wrong
number.

## 6. A clip's source range doesn't equal its timeline duration if its speed has changed

Covered in full in [Timing & Ticks](06-timing.md). If a `VideoClip`/
`AudioClip` carries `<PlaybackSpeed>` (or `<TimeRemapping>` for an animated
speed ramp), `OutPoint - InPoint` (source duration consumed) will be scaled
by that speed relative to `End - Start` (timeline duration) — a 2× speed
clip consumes twice as much source material as timeline space; a 0.5×
clip consumes half. Computing "what part of the source does this clip show"
without accounting for `PlaybackSpeed` gives a wrong answer that's silently
off by exactly the speed factor, which is easy to miss because it still
looks like a plausible timecode.

## 7. `<FrameRate>` means different things in different places

Covered in full in [Timing & Ticks](06-timing.md). Inside a
`VideoTrackGroup`, it's ticks-per-frame for the sequence. Inside an
`AudioTrackGroup`, it's ticks-per-sample, not a frame rate at all. Inside a
`VideoStream` on an individual clip, it's that source file's own native
frame rate, which can differ freely from the sequence it's placed into.
Reading the wrong one will give you a number that looks like a frame rate
but is actually a sample rate, or vice versa.

## 8. `<FilePath>` is not always a filesystem path

Generated media — Color Matte, Black Video, Bars and Tone, and
title/graphic clips — are represented as ordinary `Media` elements, but
their `<FilePath>` is a bare internal integer ID, not a real path:

```xml
<FilePath>1112293707</FilePath>
```

Check whether the value parses as a path (contains a drive letter or slash)
before treating it as one.

## 9. Element version numbers are not stable across Premiere Pro releases — don't hard-code them

Covered in full in [Version Differences](03-versions.md). Many element
types bump their internal `Version` attribute between Premiere Pro
releases while keeping the exact same structure and meaning. If your parser
rejects or mishandles an element because its `Version` doesn't match a
number you saw in one test file, it will break on projects from a different
Premiere Pro release. Match elements by tag name and `ClassID`, which are
stable; treat `Version` as informational only.

## 10. A nested sequence isn't a special element type — don't special-case it and miss it

Covered in full in [Clip Names & Nested Sequences](07-names-and-nested-sequences.md).
A sequence used as a clip inside another sequence looks, at the
`TrackItem`/`SubClip`/`MasterClip` level, exactly like any other clip. The
only difference is one hop further down: its `VideoClip`/`AudioClip`
resolves through a `VideoSequenceSource`/`AudioSequenceSource` rather than a
`VideoMediaSource`/`AudioMediaSource`. If your tool assumes every clip
eventually resolves to a file on disk, it will crash or silently skip
nested sequences — check for the `SequenceSource` case explicitly, and
recurse into that sequence's own tracks rather than treating it as a leaf.
This applies at any nesting depth — a nested sequence can itself contain
another nested sequence, arbitrarily deep — so resolve `SequenceSource`
recursively, not just once.

## 11. Large files need streaming, not a full DOM load

`.prproj` files can decompress to hundreds of megabytes of XML. Loading the
whole thing into a DOM (e.g. `xml.dom.minidom.parse` or a naive
`ElementTree.parse`) can use several times that much memory, and most of it
— UI panel state, per-column preferences, effect parameter defaults — is
irrelevant to timeline/media extraction. Use an incremental parser
(`ElementTree.iterparse` in Python, or the equivalent streaming parser in
your language) and call `.clear()` on elements you don't need to keep
referenced, once you've read what you need from them.
