# Version Differences

*Doc version 1.0 — 2026-09-18*

`.prproj` files don't carry an obvious "this was Premiere Pro 2025" label.
Here's where the real version signal is, what changes between versions, and
one breaking change you need to handle if you support Premiere Pro 2026
files.

## Where the version number actually is

Ignore the outer `<PremiereData Version="3">` — that number stays `"3"`
across every Premiere Pro release checked (2023 through 2026). The number
that actually tells you which Premiere Pro release wrote the file is on the
`Project` element itself, near the very top of the file:

```xml
<Project ObjectID="1" ClassID="62ad66dd-0dcd-42da-a660-6d8fbde94876" Version="42">
```

That `Version="42"` is what changes between releases. Its `ClassID` never
changes.

## Versions seen, and what they likely correspond to

| Project `Version` | Likely Premiere Pro release |
|---|---|
| 40 | 2023 |
| 42 | 2024 |
| 43 | 2025 |
| 45 | 2026 |

This mapping is inferred from filenames on resaved copies of the same
projects (e.g. a file suffixed `_PR2026` that carries `Version="45"`), not
from an official Adobe source — there isn't a public one. **Versions 41 and
44 have no known correspondence** in this documentation; they may be minor
point releases. Don't assume a clean one-to-one mapping between version
numbers and year-named releases beyond what's shown above.

## Same project, saved across four versions

The clearest way to see what actually changes between versions is to look
at one real-world project that was saved, then resaved after each Premiere
Pro upgrade, without any edits in between:

| File | Project Version |
|---|---|
| `same-project-v2024.prproj` | 42 |
| `same-project-v2025a.prproj` | 43 |
| `same-project-v2025b.prproj` | 43 |
| `same-project-v2026.prproj` | 45 |

Because the underlying edit never changed, any structural difference between
these four files is a genuine version-introduced change.

## What changes between versions (and what doesn't)

Most of the format is stable. Internally, every element carries its own
small `Version` number (separate from the Project version), and most of
these don't move between Premiere Pro releases. A handful do — mostly by
exactly one — coinciding with the release boundaries. None of this affects
how you'd read the data; it's just useful to know your parser shouldn't
assume a specific element-version number as a strict requirement.

Element types whose internal version number increases between Premiere Pro
releases: `Project`, `ProjectSettings`, `Sequence`, `AudioClipTrack`,
`VideoClipTrackItem`, `SubClip`, `MasterClip`, `Media`, `VideoStream`,
`AudioStream`, `VideoTransitionTrackItem`, `AudioTransitionTrackItem`,
`AudioComponentChain`, `VideoFilterComponent`, `AudioFilterComponent`, and
the various component-parameter elements (`VideoComponentParam`,
`AudioComponentParam`, `ArbVideoComponentParam`, `PointComponentParam`).

Element types whose internal version number stays identical across every
release from 2023 through 2026: `AudioTrackGroup`, `DataTrackGroup`,
`VideoClipTrack`, `VideoMediaSource`, `AudioMediaSource`,
`VideoSequenceSource`, `AudioSequenceSource`, `ClipProjectItem`,
`BinProjectItem`, `RootProjectItem`, `Markers`, `Marker`, `Link`,
`VideoComponentChain`, caption-related elements, `VideoClip`, and `AudioClip`.

**The takeaway for parser authors:** identify elements by tag name and
`ClassID`, not by their `Version` number. `ClassID` is a stable type
identifier that never changes across releases; the plain `Version` number is
just an internal revision counter and bumps independently of anything you'd
usually care about.

## The one change that will actually break your parser: Premiere Pro 2026

Every clip on a timeline has a `<TrackItem>` element recording where it sits
(`<Start>` and `<End>`, in ticks — explained in [Timing & Ticks](06-timing.md)).
Up through Project Version 43 (Premiere Pro 2025), this element **always**
includes `<Start>`, even when the clip starts at position zero:

```xml
<!-- Premiere Pro 2025 and earlier -->
<TrackItem Version="3">
    <Start>0</Start>
    <End>1127831040000</End>
</TrackItem>
```

Starting at Project Version 45 (Premiere Pro 2026), the element bumps to
`Version="4"`, and **`<Start>` is dropped entirely whenever its value would
be zero** — it isn't written as `<Start>0</Start>`, it simply isn't there:

```xml
<!-- Premiere Pro 2026, same clip, same edit -->
<TrackItem Version="4">
    <End>1127831040000</End>
</TrackItem>
```

Clips that don't start at zero are unaffected either way and still include
`<Start>` normally.

**If your parser assumes `<Start>` is always present, every clip at
position zero in a Premiere Pro 2026 project will silently vanish or get
the wrong timing.** The fix is one line:

```python
start_elem = track_item_elem.find("Start")
start_ticks = int(start_elem.text) if start_elem is not None else 0
```

`<End>` was never observed missing, at any version — only apply this
fallback to `<Start>`.
