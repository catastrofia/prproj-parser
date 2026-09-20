# Changelog

All notable changes to this documentation are recorded here. Versioning is
per-document-set (not per-file) — a version bump means the documentation as
a whole was revised, even if only some files changed.

## 1.1 — 2026-09-18

Added coverage for three real, verified features that existed in the test
corpus but were missing from version 1.0:

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

Also added a nested double/triple-nesting section to
[07-names-and-nested-sequences.md](07-names-and-nested-sequences.md)
(from a prior conversation turn, verified against a real 4-level-deep
nesting chain in one test project), and added this version-and-date header
to every document.

## 1.0 — 2026-09-18

Initial release. Covers file format, the flat object-graph model, version
differences between Premiere Pro 2023–2026 (Project Versions 40/42/43/45),
the core element reference, a worked timeline-traversal example, the tick
timing system, clip naming, single-level nested sequences, parser gotchas,
and open questions. See [METHODOLOGY.md](METHODOLOGY.md) for how it was
produced.
