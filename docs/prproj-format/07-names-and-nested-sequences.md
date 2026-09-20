# Clip Names & Nested Sequences

*Doc version 1.1 — 2026-09-18*

## Where a clip's displayed name actually comes from

A timeline clip's name — the text you see printed on the clip in the
Timeline panel — comes from the `<Name>` element on its `SubClip`:

```xml
<VideoClipTrackItem ObjectID="1003" ...>
    <ClipTrackItem Version="8">
        <SubClip ObjectRef="1012"/>
        ...
    </ClipTrackItem>
</VideoClipTrackItem>

<SubClip ObjectID="1012" ...>
    <Name><Clip Name></Name>
    ...
</SubClip>
```

The `MasterClip` this `SubClip` points to also carries a `<Name>` — usually
the same text, since it's what shows up in the Project panel for the
imported file:

```xml
<MasterClip ObjectUID="00000000-0000-0000-0000-000000000004" ...>
    <Name><Clip Name></Name>
    ...
</MasterClip>
```

In practice you'll almost always want the `SubClip`'s name — Premiere lets a
user rename an individual clip instance on the timeline independently of its
source, in which case `SubClip.Name` and `MasterClip.Name` can diverge.

## Nested sequences (a sequence used as a clip inside another sequence)

Dropping one sequence onto another sequence's timeline — a common technique
for building modular, reusable sub-edits — doesn't need any special-case
element type. A nested sequence is represented using **exactly the same
clip-reference chain as any other clip**, just with the final "media source"
being another `Sequence` instead of a file on disk.

Concretely: instead of a `VideoClip` pointing at a `VideoMediaSource` (which
points at a `Media` file), a nested sequence's `VideoClip` points at a
`VideoSequenceSource`, which points directly at the nested `Sequence`:

```xml
<!-- A track item on the timeline, referencing a SubClip as usual -->
<VideoClipTrackItem ObjectID="1035" ...>
    <ClipTrackItem Version="8">
        <SubClip ObjectRef="1036"/>
    </ClipTrackItem>
</VideoClipTrackItem>

<!-- The SubClip's name is the nested sequence's name -->
<SubClip ObjectID="1036" ...>
    <MasterClip ObjectURef="00000000-0000-0000-0000-000000000025"/>
    <Name>Example Sequence</Name>
</SubClip>

<!-- Same MasterClip pattern as any other clip -->
<MasterClip ObjectUID="00000000-0000-0000-0000-000000000025" ...>
    <Clips Version="1">
        <Clip Index="0" ObjectRef="1037"/>   <!-- audio -->
        <Clip Index="1" ObjectRef="1038"/>   <!-- video -->
    </Clips>
    <Name>Example Sequence</Name>
</MasterClip>

<!-- The video Clip's Source points at a SequenceSource, not a MediaSource -->
<VideoClip ObjectID="1038" ...>
    <Clip Version="18">
        <Source ObjectRef="1039"/>
    </Clip>
</VideoClip>

<!-- ...which points directly at the nested Sequence -->
<VideoSequenceSource ObjectID="1039" ...>
    <SequenceSource Version="4">
        <Sequence ObjectURef="00000000-0000-0000-0000-000000000002"/>
    </SequenceSource>
</VideoSequenceSource>
```

In this sanitized example, the nested sequence being referenced is the very same
"Example Sequence" sequence used as the worked example in
[Traversing a Timeline](05-traversal.md) — which is why the `MasterClip`'s
name, the `SubClip`'s name, and the `Sequence`'s own `<Name>` all read
"Example Sequence".

`AudioSequenceSource` mirrors `VideoSequenceSource` for the nested
sequence's audio, the same way `AudioMediaSource` mirrors
`VideoMediaSource` for ordinary media.

**Practical implication:** if you're building a tool that resolves clip
names or flattens a project into a single timeline, check whether a
`VideoClip`/`AudioClip`'s `Source` reference resolves to a
`VideoMediaSource`/`AudioMediaSource` (a real file) or a
`VideoSequenceSource`/`AudioSequenceSource` (another sequence) — the latter
means you need to recurse into that sequence's own tracks to find the
underlying clips, rather than treating it as a leaf.

## Nesting a nested sequence (double, triple, and deeper nesting)

There's no separate mechanism for a "sequence nested inside a nested
sequence." The `Sequence` that a `VideoSequenceSource` points to is a
completely ordinary sequence — it has its own three `TrackGroup`s, its own
tracks, and its own clips, built from exactly the same elements described
above. If one of *those* clips also happens to resolve through a
`VideoSequenceSource`/`AudioSequenceSource`, you've found another level of
nesting, and the only way to know is to keep following the chain.

In other words: nesting depth isn't a property stored anywhere in the file
— it falls out naturally from how far you have to walk the same
`SubClip → MasterClip → VideoClip/AudioClip → VideoSequenceSource/AudioSequenceSource → Sequence`
chain before you finally land on a `Sequence` whose clips all resolve to
real `VideoMediaSource`/`AudioMediaSource` media instead of another
sequence.

A corpus project has a sequence nested four levels deep:

```
<Main Sequence Name>
  └─ <Nested Sequence Name A>
      └─ <Nested Sequence Name B>
          └─ <Nested Sequence Name C>   (and 13 sibling sequences at this same level)
```

The XML at each hop is identical in shape to the single-level example
above — a `VideoClipTrackItem` on `<Main Sequence Name>`'s own track resolves to
`SubClip → MasterClip → VideoSequenceSource → Sequence("<Nested Sequence Name A>")`;
that sequence's own (single) track has its own `VideoClipTrackItem`
resolving to `SubClip → MasterClip → VideoSequenceSource →
Sequence("<Nested Sequence Name B>")`; and that sequence's tracks have clips
resolving the same way again, one level deeper still, before finally
bottoming out.

**Practical implication for parsers:** resolve `VideoSequenceSource`/
`AudioSequenceSource` **recursively**, not just once. A single hard-coded
"un-nest one level" step will only handle the shallowest case and will
leave deeper nesting unresolved (or misinterpreted as a leaf clip with no
media). Guard against infinite recursion with a "sequences visited so far"
set — Premiere's own UI prevents you from nesting a sequence inside itself,
but a defensive parser shouldn't assume the file it's fed is always
well-formed.
