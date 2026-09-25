# `.prproj` Format Research Notes

**Version 1.1 — 2026-09-18**
*(See [11-changelog.md](11-changelog.md) for revision history.)*

These are unofficial research notes, not an Adobe-authoritative specification. They describe patterns observed in `.prproj` files for developers who need to read or parse projects: migration tools, media-management scripts, timeline extraction, QA tooling, and similar work.

It covers observed Premiere Pro project versions **40, 42, 43, and 45** — likely corresponding to Premiere Pro 2023 through 2026 — and calls out differences where they matter to a parser. Some notes describe format features that this package does not currently expose.

## Start here

1. **[File Format](01-file-format.md)** — is it XML? Is it compressed? What's
   the root element?
2. **[Object Model](02-object-model.md)** — the single most important concept:
   `.prproj` is a flat graph of cross-referenced objects, not a nested tree.
3. **[Version Differences](03-versions.md)** — what changed between Premiere
   Pro releases, including a breaking change in the 2026 format.
4. **[Element Reference](04-elements.md)** — the element types you'll
   actually need, with real examples, including effects, keyframed
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

## Evidence and caveats

This is not derived from an Adobe spec or from decompiling Premiere Pro. It comes from directly inspecting a private corpus of real `.prproj` files, with identifying details redacted. Several files were the same edit saved across multiple Premiere Pro versions, which made it possible to isolate version changes rather than guess.

See **[10-methodology.md](10-methodology.md)** for the full write-up: what was inspected, how, what tools were used, which claims are backed by direct evidence, and which are reasonable inferences. Open questions are called out instead of guessed.
