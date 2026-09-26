# Methodology: How This Documentation Was Produced

*Doc version 1.1 — 2026-09-18*

This is a report on *how* the `.prproj` documentation in this folder was
derived, so readers can judge how much to trust each claim. Nothing in the
other documents is guesswork presented as fact; every non-trivial statement
traces back to one of the checks described below.

## Source material

A private corpus of `.prproj` files was inspected. These were real-world project files rather than synthetic samples, but private filenames, local paths, corpus size details, and subject matter have been removed from these public notes. The corpus still covered nested sequences, captions, transitions, multi-cam-style audio links, color mattes, still graphics, and accumulated UI preference data. Before migration, these public notes were checked for known private source paths, project prefixes, client/story titles, and caption/font strings from the source corpus.

Crucially, several files are **the same source project, re-saved multiple
times as the editor upgraded Premiere Pro**. For example:

```
same-project-v2024.prproj   (Project Version 42)
same-project-v2025a.prproj  (Project Version 43)
same-project-v2025b.prproj  (Project Version 43)
same-project-v2026.prproj   (Project Version 45)
```

All four contain the same sequence, timeline clips, and media references.
This is the single most valuable property of the corpus: it means any
structural difference found between these four
files is a genuine version-introduced change, not incidental variation
between unrelated projects. The same pattern exists for several other
redacted project families, and all of these were cross-checked against each
other so no single-project quirk would be mistaken for a version rule.

Two apparent "version pairs" turned out to be exact byte-for-byte duplicates and were excluded from version-diffing since they provide no signal.

## Tools used

- **Bash** (`xxd`, `grep`, `md5sum`, `sed`) for byte-level inspection: magic
  bytes, quick greps, line-range dumps of specific matches.
- **Python 3.12** with `gzip` (decompression) and
  `xml.etree.ElementTree.iterparse` (structural, depth-aware parsing —
  needed because the files are too large to load as a full DOM, and because
  depth matters: see the `ObjectID` scoping issue below).
- No third-party libraries, no decompiler, no access to Premiere Pro itself.
  Every claim comes from what's observable in the files on disk.

## What was actually done, step by step

1. **Decompressed the corpus** and recorded, for each file: on-disk compression
   (gzip vs plain XML, checked by magic bytes, not by file extension or
   assumption), decompressed size, and the `<Project ObjectID="1" ...
   Version="N">` value. This produced the version census in
   [03-versions.md](03-versions.md).

2. **Confirmed the "flat object graph" claim directly**, rather than taking
   it on faith from prior write-ups. Using `iterparse` with manual depth
   tracking, every file was scanned to confirm that essentially all
   meaningful element types (`Sequence`, `VideoClipTrack`,
   `VideoClipTrackItem`, `MasterClip`, `Media`, etc.) occur only as direct
   children of the root `<PremiereData>` element (depth 2), never nested
   inside one another.

3. **Built and tested the ID-reference model against real cross-references.**
   For a specific representative sequence, every step of the chain
   Sequence → TrackGroup → Track → VideoClipTrack → ClipItems/TrackItems →
   VideoClipTrackItem → SubClip → MasterClip → VideoClip/AudioClip → Media
   was followed by hand, using `grep -n 'ObjectID="N"'` /
   `grep -n 'ObjectUID="uuid"'` to jump from a reference to its target and
   back, confirming each hop resolves to a real element with the expected
   shape. This trace is reproduced in [05-traversal.md](05-traversal.md).

4. **Discovered the `ObjectID` scoping bug the hard way.** While tracing the
   chain above, a `grep -n 'ObjectID="791"'` unexpectedly returned two
   matches — one on the `VideoTrackGroup` we wanted, and one on an unrelated
   `TimecodeColumn` UI element buried inside a `ProjectViewState` block.
   This led to writing a small script that counts `ObjectID` duplicates
   among *all* elements in a file versus *only* depth-2 elements. The result
   (4179 depth-2 elements, 4179 unique `ObjectID`s, zero collisions — vs.
   thousands of collisions when nested elements are included) is what
   justified the "only index at depth 2" rule in
   [02-object-model.md](02-object-model.md).

5. **Verified the tick/frame-rate system arithmetically**, not by trusting a
   lookup table. The constant `254,016,000,000` ticks/second was tested
   against every distinct `<FrameRate>` value actually found inside a
   `VideoTrackGroup` or `AudioTrackGroup` across the corpus (not just a
   couple of hand-picked ones), confirming each one divides the constant
   into a recognizable fps or audio sample rate — including one project
   using a non-standard ~30.01 fps rate, which only makes sense as a
   division result, not a table lookup. Full numbers are in
   [06-timing.md](06-timing.md).

6. **Found and disproved a scaling claim from a prior write-up.** An older,
   informal note about this format (found alongside the test files) claimed
   `<FrameRate>` values are "sometimes stored ×1000 too large." A script
   collected every distinct `FrameRate` value that occurs directly inside a
   `VideoTrackGroup/TrackGroup` across the whole corpus. Only three distinct
   values were found, and every one of them divides the tick constant into
   a plausible fps or sample rate at face value — no ×1000 or ×10 scaling
   was observed anywhere. That claim is not repeated here.

7. **Verified the Premiere Pro 2026 breaking change with a controlled
   diff**, using the resaved-project sets described above. For each pair of
   files representing the same edit at two different Project Versions, a
   script counted how many `<TrackItem Version="N">` blocks were missing a
   `<Start>` child. The result was consistent and reproducible across three
   independent projects: at Project Version ≤ 43, no blocks omitted
   `<Start>`; at Project Version 45, a `TrackItem` schema bump to
   `Version="4"` appears, and clips whose timeline start is `0` omit the
   `<Start>` element entirely, always matching clips known to start at the
   very beginning of a track. Full detail, including a representative
   before/after XML diff of the same clip, is in [03-versions.md](03-versions.md).

8. **Built a version-delta matrix mechanically, not by memory.** A script
   walked every depth-2 element in every file in the corpus, grouped by
   `(tag name, Project Version)`, and recorded the distinct
   `(ClassID, element-internal-Version)` pairs seen at each Project Version.
   This produced the full table of "what element versions bump at which
   Premiere Pro release" in [03-versions.md](03-versions.md) — nothing in
   that table was asserted without appearing in this scan.

9. **Checked, and rejected, other claims from the same prior informal
   note** by testing them directly:
   - *"Some files use XML namespaces"* — grepped all decompressed files
     for `xmlns`; zero matches. Not repeated as fact.
   - *"`Node.Name` holds the clip's display name"* — grepped all the corpus
     for the literal string `Node.Name`; zero matches anywhere in the
     corpus. The real mechanism (`SubClip.Name` / `MasterClip.Name`) was
     traced by hand instead and is documented with a worked example in
     [07-names-and-nested-sequences.md](07-names-and-nested-sequences.md).
   - *"Every TrackItem has `InPoint`/`OutPoint`"* — `InPoint`/`OutPoint` do
     exist in the files, but on `VideoClip`/`AudioClip` elements (the
     clip-source-binding layer), not on the timeline `TrackItem` itself.
     Verified by tracing an actual clip end to end.

10. **Sanity-checked filename-based version hints against the real
    `Project Version` number** for every file with a suggestive suffix
    (`_2023`, `_2024`, `_P25`, `_PR2025`, `_P26`, `_PR26`, `_PR2026`) to
    build the tentative version→year table, and explicitly flagged the two
    Project Version numbers (41 and 44) that never appear anywhere in the
    corpus, rather than filling the gap with a guess.

11. **Verified double/triple nested sequences with a real recursive
    chain, not just the single-nesting case.** After documenting how one
    sequence nests inside another (via `VideoSequenceSource`/
    `AudioSequenceSource`), a script built a directed graph of
    "which sequence uses which other sequence as a clip" across every
    file, then searched that graph for chains longer than one hop. This
    found a genuine 4-level-deep chain in one file
    (`Top Sequence → Nested Sequence 28 → Nested Sequence 12 → Nested
    Sequence 27`, plus 13 further sibling sequences at the deepest
    level), which was then confirmed byte-for-byte to use the exact same
    `SubClip`/`MasterClip`/`VideoSequenceSource` XML shape at every hop —
    i.e. nesting depth is not represented anywhere in the schema, it's
    purely an emergent property of how many times a parser has to follow
    the same reference chain. The same script also checked for circular
    nesting (a sequence indirectly containing itself); none was found in
    the corpus. Documented in
    [07-names-and-nested-sequences.md](07-names-and-nested-sequences.md).

12. **Checked the source corpus for features not yet covered by the initial
    documentation**, rather than assuming the first pass was complete. This is
    how three observed features were found and then verified before being
    written up:
    - **Clip speed changes** (`PlaybackSpeed`, `TimeRemapping`) — found in
      many inspected files via a targeted grep, present at every Project Version
      checked (not version-specific). The relationship between
      `PlaybackSpeed` and the `InPoint`/`OutPoint` vs. `Start`/`End`
      values was verified arithmetically on a real 2×-speed clip: its
      source range (`OutPoint - InPoint`) measured exactly double its
      timeline duration (`End - Start`) — `3,048,192,000,000` ticks of
      source vs. `1,524,096,000,000` ticks of timeline, a clean 2:1 ratio
      matching the stored `PlaybackSpeed` of `2`. Documented in
      [06-timing.md](06-timing.md).
    - **`AudioMixTrack`** (the sequence's master/submix audio track) —
      found in all the corpus via grep, but never previously described.
      Traced by hand from `AudioTrackGroup.MasterTrack` through
      `AudioMixTrack.Inlet` to `AudioTrackInlet.Sources`, confirming the
      latter lists the ordinary `AudioClipTrack`s that feed the mix.
      Documented in [04-elements.md](04-elements.md).
    - **Keyframed effect parameters** (`<Keyframes>` on
      `VideoComponentParam`/`AudioComponentParam`/`TimeComponentParam`) —
      previously dismissed wholesale as "irrelevant for timeline
      extraction," which is true for basic clip timing but incomplete for
      effects data. A script collected every `<Keyframes>` string across
      the corpus (many individual keyframe entries) and counted how
      many comma-separated fields each one had: only two shapes appeared,
      8-field and 14-field tuples, with the 14-field shape confined to
      `PointComponentParam`. The first two fields consistently look like
      `(tick position, value)` across a manual sample; the remaining
      fields' exact meaning (most likely interpolation handles/mode) was
      **not** conclusively decoded, and this is stated as an open
      question rather than guessed at, in
      [09-open-questions.md](09-open-questions.md).
    - **Adjustment layers and Lumetri Color** were checked too, but
      turned out not to be new elements at all — an adjustment layer is
      an ordinary `Media`/`MasterClip` with `<AdjustmentLayer>true</
      AdjustmentLayer>`, and Lumetri Color is an ordinary
      `VideoFilterComponent` with `<MatchName>AE.ADBE Lumetri</MatchName>`.
      Both already fit the generic `Media`/effect documentation, so no new
      section was needed for them beyond a one-line callout.
    - **Reversed clip playback** was searched for specifically
      (`<Reverse>`) but every match found in the corpus was on a
      transition, not a clip's speed settings — so this remains
      unconfirmed and is listed as an open question rather than assumed to
      work like a negative `PlaybackSpeed`.

## What is and isn't claimed

- Anything stated as fact in these docs was directly observed in the file
  bytes, using the checks above, and can be reproduced by anyone with the
  same test files and a text editor.
- Where the corpus was insufficient to fully confirm something (e.g. the
  exact semantics of Project Versions 41/44, or whether gzip-vs-plain is
  truly a user preference toggle rather than something else), this is
  stated explicitly in the relevant document and collected in
  [09-open-questions.md](09-open-questions.md) — it is not filled in with a
  plausible-sounding guess.
- Nothing here was checked against Adobe's own source code, official
  documentation, or support staff, because none of that is publicly
  available for this format. Where a claim from the Adobe community forums
  is cited (specifically: that gzip-vs-plain XML is a save-time preference),
  it is labeled as an external, unverified claim rather than something this
  investigation independently proved.
