# Open Questions

*Doc version 1.1 — 2026-09-18*

This documentation is built entirely from direct observation of real files
(see [METHODOLOGY.md](METHODOLOGY.md) for how). Where the available files
didn't provide enough evidence to state something as fact, it's listed
here instead of being filled in with a guess.

## Project Versions 41 and 44

Only Project Versions 40, 42, 43, and 45 were available to inspect. Versions
41 and 44 have no known corresponding Premiere Pro release in this
documentation, and no test file at either version was available to check
whether they represent a distinct schema, a minor point release, or
something else. If you have a `.prproj` file at Version 41 or 44, diffing it
against the 40/42/43/45 findings in [Version Differences](03-versions.md)
would resolve this.

## Whether gzip-vs-plain-XML is really a save-time preference

The observation that the same project can be saved in both gzip and plain
XML form is directly verified. The explanation — that this is controlled by
a "Compress Project Files on Save" preference in Premiere Pro — comes from
posts on Adobe's community forums, not from anything independently confirmed
in this investigation (there's no way to inspect Premiere's own preference
storage from the project files themselves). It's presented as the most
plausible explanation, not a proven one.

## The exact binary layout of caption text (`FormattedTextData`)

Caption text is confirmed to be embedded, along with a font family name, as
readable UTF-8 substrings inside a base64-encoded binary blob (see
[Element Reference](04-elements.md)). What was not determined is the full
layout of that binary format — the meaning of the surrounding bytes (likely
a serialized rich-text/formatting-run structure, based on its size and the
presence of floating-point-looking values near the text), field boundaries,
or how multiple text runs/formatting spans within one caption block would
be represented. Extracting caption text by scanning for UTF-8 text runs
inside the blob works for simple captions but hasn't been validated against
multi-format-run or styled captions.

## The exact per-field meaning of the `<Keyframes>` animation-curve format

Covered in [Element Reference](04-elements.md#videocomponentparam--audiocomponentparam-and-keyframed-values).
Confirmed: `<Keyframes>` on an animated `VideoComponentParam`/
`AudioComponentParam`/`TimeComponentParam` is a `;`-separated list of
`,`-separated tuples, where the first field is a tick position and the
second is the parameter's value at that keyframe. Every tuple observed
across the corpus had either 8 or 14 comma-separated fields — 14-field
tuples were only seen on `PointComponentParam` (2D values), 8-field tuples
everywhere else — but the meaning of fields 3 onward (almost certainly
interpolation handles and an interpolation-mode flag, based on their
value ranges) was not conclusively decoded. A parser that needs the
sampled value of an animated parameter at a given time can linearly
interpolate between the first-two-fields of the surrounding keyframes as
an approximation; a parser that needs to preserve or reproduce Premiere's
exact interpolation curve (e.g. a bezier ease) should treat this field as
an opaque blob to copy through unmodified rather than reconstruct.

## Whether every element type was captured

This documentation focuses on the elements needed to read a timeline: its
sequences, tracks, clips, media references, markers, links, and captions.
The full format includes many more element types purely for UI/preference
state (column layouts, panel positions, per-user view settings, effect
preset browsing history, etc.) that were not catalogued here because they
don't affect timeline or media data. If you need one of those, expect to
find it as an ordinary top-level element following the same
`ObjectID`/`ObjectRef` conventions described in
[Object Model](02-object-model.md) — nothing observed suggests they follow
different rules, but this wasn't exhaustively checked for every UI element
type in the format.

## Multi-camera / production ("Productions" feature) projects

None of the files inspected used Premiere's "Productions" (multi-project)
feature or multi-camera source sequences specifically. The structures
described here should still apply (production projects are still `.prproj`
files with the same underlying format), but no direct verification was done
for how a Production's cross-project references or a multi-camera clip's
angle-switching data are represented.

## Reversed clip playback

Constant-speed changes (`<PlaybackSpeed>`) and animated speed ramps
(`<TimeRemapping>`) are both confirmed — see
[Timing & Ticks](06-timing.md). Premiere Pro also supports reversing a
clip's playback direction as a separate toggle from its speed, but no clip
using that toggle was identified with certainty in the test corpus (a
`<Reverse>` element exists, but every instance found was on a transition,
not a clip's speed settings, so it wasn't possible to confirm the
clip-reversal representation from these files). Don't assume a negative
`<PlaybackSpeed>` value is how reversal is stored — that's a guess, not a
finding — until it's checked against a real reversed clip.
