# Adobe Premiere Pro `.prproj` Format — Unofficial Documentation

**Version 1.1 — 2026-09-18**
*(See [CHANGELOG.md](CHANGELOG.md) for revision history.)*

Adobe has never published a specification for the `.prproj` project file
format. This documentation describes the format as it actually exists on
disk, written for developers who need to read, parse, or generate `.prproj`
files (for migration tools, media-management scripts, timeline extraction,
QA tooling, etc.).

It covers Premiere Pro project versions **40, 42, 43, and 45** — corresponding
to Premiere Pro 2023 through 2026 — and calls out the differences between
them where they matter to a parser.

## Start here

1. **[File Format](01-file-format.md)** — is it XML? Is it compressed? What's
   the root element?
2. **[Object Model](02-object-model.md)** — the single most important concept:
   `.prproj` is a flat graph of cross-referenced objects, not a nested tree.
3. **[Version Differences](03-versions.md)** — what changed between Premiere
   Pro releases, including a breaking change in the 2026 format.
4. **[Element Reference](04-elements.md)** — the element types you'll
   actually need, with sanitized examples, including effects, keyframed
   parameters, and audio submixing.
5. **[Traversing a Timeline](05-traversal.md)** — a step-by-step walk from a
   sequence name down to its individual clips.
6. **[Timing & Ticks](06-timing.md)** — how Premiere stores time, the
   difference between timeline position and source in/out points, and how
   clip speed changes affect that math.
7. **[Clip Names & Nested Sequences](07-names-and-nested-sequences.md)** —
   how a clip's display name is resolved, and how sequences-within-sequences
   (including sequences nested inside nested sequences) are represented.
8. **[Parser Gotchas](08-gotchas.md)** — pitfalls that will silently corrupt
   your output if you don't handle them.
9. **[Open Questions](09-open-questions.md)** — things this documentation
   does not know, stated plainly instead of guessed at.

## How this documentation was produced

This isn't derived from an Adobe spec (there isn't one) or from
decompiling Premiere Pro itself. It comes from directly inspecting 51 real
`.prproj` project files, several of which are the *same edit* saved across
multiple Premiere Pro versions — which made it possible to isolate exactly
what changes between versions rather than guess.

See **[METHODOLOGY.md](METHODOLOGY.md)** for the full write-up: what was
inspected, how, what tools were used, and which claims are backed by direct
evidence versus which are reasonable inferences. Every non-obvious claim in
these documents is traceable back to that report.
