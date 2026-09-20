# The Object Model

*Doc version 1.0 — 2026-09-18*

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
    <Sequence ObjectUID="00000000-0000-0000-0000-000000000002">...</Sequence>
    <VideoTrackGroup ObjectID="1002">...</VideoTrackGroup>
    <VideoClipTrack ObjectUID="00000000-0000-0000-0000-000000000003">...</VideoClipTrack>
    <VideoClipTrackItem ObjectID="1003">...</VideoClipTrackItem>
    <MasterClip ObjectUID="00000000-0000-0000-0000-000000000004">...</MasterClip>
    <Media ObjectUID="00000000-0000-0000-0000-000000000005">...</Media>
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
| `ObjectID` | An element's definition | A numeric ID for this element, e.g. `ObjectID="1003"` |
| `ObjectUID` | An element's definition | A UUID for this element, e.g. `ObjectUID="00000000-0000-0000-0000-000000000004"` |
| `ObjectRef` | A reference inside another element | Points at some other element's `ObjectID` |
| `ObjectURef` | A reference inside another element | Points at some other element's `ObjectUID` |

Some element types use numeric IDs, some use UUIDs, and it's consistent per
type — every `VideoClipTrack`, for instance, uses `ObjectUID`, never
`ObjectID`, while every `VideoTrackGroup` uses `ObjectID`. A reference always
uses the matching kind: an `ObjectRef` never resolves to something identified
only by `ObjectUID`, and vice versa.

Example — a track pointing at one of its clips:

```xml
<VideoClipTrack ObjectUID="00000000-0000-0000-0000-000000000003">
    <ClipTrack Version="2">
        <ClipItems Version="3">
            <TrackItems Version="1">
                <TrackItem Index="0" ObjectRef="1003"/>   <!-- points at ObjectID="1003" -->
            </TrackItems>
        </ClipItems>
    </ClipTrack>
</VideoClipTrack>

<!-- Elsewhere in the file, not nested inside the track above -->
<VideoClipTrackItem ObjectID="1003" ClassID="00000000-0000-0000-0000-000000000006" Version="6">
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

For example, a `VideoTrackGroup` with `ObjectID="1002"` can coexist with a
totally unrelated `TimecodeColumn` — an internal definition for a column in
Premiere's project-panel UI, buried many levels deep inside saved
"project panel layout" preferences — that happens to carry the exact same
`ObjectID="1002"`, purely by coincidence of Premiere's internal ID
allocator:

```xml
<!-- Buried deep inside UI preference data — irrelevant, but shares the ID -->
<TimecodeColumn ObjectID="1002" ClassID="00000000-0000-0000-0000-000000000007" Version="1">
    <Column.Name><Column Name></Column.Name>
    ...
</TimecodeColumn>

<!-- The actual object you want, sitting flat at the top level -->
<VideoTrackGroup ObjectID="1002" ClassID="00000000-0000-0000-0000-000000000008" Version="13">
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
