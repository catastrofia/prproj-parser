# The Object Model

*Doc version 1.1 — 2026-09-18*

This is the single most important thing to understand about `.prproj`
before trying to parse one.

## It's not a document tree — it's a flat, cross-referenced graph

In most XML formats, nesting means ownership: a `<track>` inside a
`<sequence>` belongs to that sequence. **`.prproj` doesn't work that way.**
Almost every meaningful piece of data — a sequence, a track, a clip, a media
file reference — is a **direct child of the root `<PremiereData>` element**,
sitting as a sibling next to thousands of other unrelated-looking elements:

```xml
<PremiereData Version="3">
    <Sequence ObjectUID="946f1366-99f8-4cd6-8d22-f858a7967568">...</Sequence>
    <VideoTrackGroup ObjectID="791">...</VideoTrackGroup>
    <VideoClipTrack ObjectUID="4f497cd6-df1c-4b4b-adb5-2071fe66ec84">...</VideoClipTrack>
    <VideoClipTrackItem ObjectID="1057">...</VideoClipTrackItem>
    <MasterClip ObjectUID="742c7adb-93b1-4931-a2b6-cd82e0995c39">...</MasterClip>
    <Media ObjectUID="90aedb11-761b-462b-8b6c-e9382c1b43c9">...</Media>
    <!-- ...thousands more elements, all at this same depth... -->
</PremiereData>
```

None of the elements above is nested inside another — they're all siblings.
A single sequence's worth of tracks, clips, media references, and effects
can add up to thousands of these top-level elements, all sitting flat, side
by side.

So how does a `Sequence` know which tracks it has, or which clip is at
position 3? Through **references** — attributes that point at another
element elsewhere in the file, the same way a foreign key in a database
points at a row in another table.

## The four attributes that hold the graph together

| Attribute | Appears on | Meaning |
|---|---|---|
| `ObjectID` | An element's definition | A numeric ID for this element, e.g. `ObjectID="1057"` |
| `ObjectUID` | An element's definition | A UUID for this element, e.g. `ObjectUID="742c7adb-93b1-4931-a2b6-cd82e0995c39"` |
| `ObjectRef` | A reference inside another element | Points at some other element's `ObjectID` |
| `ObjectURef` | A reference inside another element | Points at some other element's `ObjectUID` |

Some element types use numeric IDs, some use UUIDs, and it's consistent per
type — every `VideoClipTrack`, for instance, uses `ObjectUID`, never
`ObjectID`, while every `VideoTrackGroup` uses `ObjectID`. A reference always
uses the matching kind: an `ObjectRef` never resolves to something identified
only by `ObjectUID`, and vice versa.

Example — a track pointing at one of its clips:

```xml
<VideoClipTrack ObjectUID="4f497cd6-df1c-4b4b-adb5-2071fe66ec84">
    <ClipTrack Version="2">
        <ClipItems Version="3">
            <TrackItems Version="1">
                <TrackItem Index="0" ObjectRef="1057"/>   <!-- points at ObjectID="1057" -->
            </TrackItems>
        </ClipItems>
    </ClipTrack>
</VideoClipTrack>

<!-- Elsewhere in the file, not nested inside the track above -->
<VideoClipTrackItem ObjectID="1057" ClassID="368b0406-29e3-4923-9fcd-094fbf9a1089" Version="6">
    ...
</VideoClipTrackItem>
```

## What this means for parsing

You can't just walk the XML tree from top to bottom and expect to find a
sequence's clips nested inside it — because they aren't. To read a project,
you need to:

1. Do one pass over the file, recording every element's `ObjectID` and/or
   `ObjectUID` in a lookup table (a dictionary keyed by ID, essentially a
   primary-key index).
2. Then follow `ObjectRef`/`ObjectURef` attributes through that lookup table
   to hop from one element to the next — the same way you'd follow a foreign
   key in SQL.

## The one gotcha that will bite you: IDs are not globally unique

Here's the trap. `ObjectID` numbers are **only guaranteed unique among the
"real" top-level objects** — the ones sitting as direct children of
`<PremiereData>`. The *same number* can also turn up, completely
coincidentally, as the ID of some unrelated, deeply-nested element buried
inside UI preference data.

For example, a `VideoTrackGroup` with `ObjectID="791"` can coexist with a
totally unrelated `TimecodeColumn` — an internal definition for a column in
Premiere's project-panel UI, buried many levels deep inside saved
"project panel layout" preferences — that happens to carry the exact same
`ObjectID="791"`, purely by coincidence of Premiere's internal ID
allocator:

```xml
<!-- Buried deep inside UI preference data — irrelevant, but shares the ID -->
<TimecodeColumn ObjectID="791" ClassID="9c9279d2-355c-487b-b644-0698b42e32f9" Version="1">
    <Column.Name>Subclip End</Column.Name>
    ...
</TimecodeColumn>

<!-- The actual object you want, sitting flat at the top level -->
<VideoTrackGroup ObjectID="791" ClassID="9e9abf7a-0918-49c2-91ae-991b5dde77bb" Version="13">
    ...
</VideoTrackGroup>
```

If your lookup table is built by scanning *every* element in the file for an
`ObjectID` attribute, you will get random, hard-to-debug collisions —
potentially thousands of them in a large project.

**The fix:** only record an element's `ObjectID`/`ObjectUID` in your lookup
table if the element is a **direct child of `<PremiereData>`** (i.e. at
depth 2, counting the root as depth 1). Restricting the index this way is
what makes `ObjectID`/`ObjectUID` reliably unique.

If you're using Python's `ElementTree.iterparse`, this means tracking depth
manually:

```python
import xml.etree.ElementTree as ET

by_id, by_uid = {}, {}
depth = 0

for event, elem in ET.iterparse(path, events=("start", "end")):
    if event == "start":
        depth += 1
        if depth == 2:                    # only the real top-level objects
            if "ObjectID" in elem.attrib:
                by_id[elem.attrib["ObjectID"]] = elem
            if "ObjectUID" in elem.attrib:
                by_uid[elem.attrib["ObjectUID"]] = elem
    else:
        depth -= 1
```

This depth check is the difference between a parser that works reliably and
one that occasionally resolves a clip's start time to a random UI setting.

## Parser cheat sheet

For timeline/media extraction, keep top-level objects with these tags and clear
other top-level objects after inspection when streaming large files:

```python
INDEXED_TAGS = {
    "Sequence",
    "VideoTrackGroup",
    "AudioTrackGroup",
    "DataTrackGroup",
    "VideoClipTrack",
    "AudioClipTrack",
    "VideoClipTrackItem",
    "AudioClipTrackItem",
    "SubClip",
    "MasterClip",
    "VideoClip",
    "AudioClip",
    "ClipProjectItem",
    "Media",
    "VideoMediaSource",
    "AudioMediaSource",
    "VideoSequenceSource",
    "AudioSequenceSource",
    "CaptionDataClipTrack",
    "CaptionDataClipTrackItem",
    "BinProjectItem",
}
```

Useful observed `ClassID` values for common core elements:

| Tag | ClassID |
|---|---|
| `Sequence` | `6a15d903-8739-11d5-af2d-9b7855ad8974` |
| `VideoTrackGroup` | `9e9abf7a-0918-49c2-91ae-991b5dde77bb` |
| `AudioTrackGroup` | `9b9238b9-53a8-4cc3-b03f-b36246d052e6` |
| `DataTrackGroup` | `b714b71d-6838-48dd-9b77-db19088ced7e` |
| `VideoClipTrack` | `f68dcd81-8805-11d5-af2d-9bfa89d4ddd4` |
| `VideoClipTrackItem` | `368b0406-29e3-4923-9fcd-094fbf9a1089` |
| `AudioClipTrackItem` | `064ec682-9ba6-11d5-af2d-9ca32c7d6164` |
| `SubClip` | `e0c58dc9-dbdd-4166-aef7-5db7e3f22e84` |
| `MasterClip` | `fb11c33a-b0a9-4465-aa94-b6d5db2628cf` |
| `ClipProjectItem` | `cb4e0ed7-aca1-4171-8525-e3658dec06dd` |
| `Media` | `7a5c103e-f3ac-4391-b6b4-7cc3d2f9a7ff` |
| `BinProjectItem` | `dbfd6653-24da-480e-a35e-ba45e9504e4b` |
| `Markers` | `bee50706-b524-416c-9f03-b596ce5f6866` |

Prefer tag names for parsing; use `ClassID` as a sanity check, not the primary
key, unless you have evidence from your target files that tag names are unstable.
