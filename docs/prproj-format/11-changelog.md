# Documentation history

This file records the history of the source documentation before it was
migrated into this repository.

## 1.1 — 2026-09-18

The source documentation added coverage for three observed features that had
not been covered in its initial version:

- **Clip speed changes** (`PlaybackSpeed`, `TimeRemapping`) — new section in
  [06-timing.md](06-timing.md), with an example verified against real
  in/out-point math (a 2× speed clip's source duration is exactly double its
  timeline duration). Cross-referenced from
  [04-elements.md](04-elements.md) and [08-gotchas.md](08-gotchas.md).
- **Audio submix routing** (`AudioMixTrack`, `AudioTrackInlet`, `Panner`) —
  new subsection in [04-elements.md](04-elements.md) under Sequences and
  Tracks, explaining what `AudioTrackGroup.MasterTrack` actually points to.
- **Keyframed (animated) effect parameters** — the `<Keyframes>` string
  format on `VideoComponentParam`/`AudioComponentParam`/`TimeComponentParam`
  is now acknowledged with what's confirmed about its shape (semicolon-
  separated keyframe entries, each a comma-separated tuple starting with a
  tick position and a value). The exact meaning of every field beyond that
  was **not** fully decoded — documented honestly as a gap in
  [09-open-questions.md](09-open-questions.md) rather than guessed at.

The source documentation also added a nested double/triple-nesting section to
[07-names-and-nested-sequences.md](07-names-and-nested-sequences.md), based on
an observed multi-level nesting chain in one source project.

## 1.0 — 2026-09-18

Initial source documentation. Covers file format, the flat object-graph model,
version differences between Premiere Pro 2023–2026 (Project Versions
40/42/43/45), the core element reference, a worked timeline-traversal example,
the tick timing system, clip naming, single-level nested sequences, parser
gotchas, and open questions. See [10-methodology.md](10-methodology.md) for how
it was produced.
