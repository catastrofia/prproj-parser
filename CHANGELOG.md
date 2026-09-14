# Changelog

All notable changes to this project are documented here.

## [0.1.0] - Unreleased

Initial public release.

### Added

- `load()` / `list_sequences()` high-level API for parsing `.prproj` files
- `Project` / `Sequence` / `Track` / `Clip` / `MediaInfo` data model
- Deterministic MasterClip -> Media reference chain resolution
- Automatic gzip **and** raw-XML `.prproj` file support (Premiere Pro writes both)
- Clip type detection (`Video`, `Audio`, `Image`, `Graphic`, `Premiere element`, `Unknown`)
- `Clip.speed_percent` — resolved from Premiere's `PlaybackSpeed`
- Pluggable XML backend: stdlib, `lxml` (`[fast]`), or `defusedxml` (`[secure]`)
- Custom exception hierarchy (`PrprojParseError`, `PrprojVersionError`, etc.)

### Fixed

- `.prproj` files that are plain XML (not gzip-compressed) — roughly half of
  real-world exported files — previously failed to load entirely, and the
  deterministic media-chain resolution pass silently fell back to
  lower-accuracy heuristic matching for every such file.
- Extension detection matched the *first* dot-group in a path/filename
  rather than the real trailing extension — misclassified any real media
  file whose name contained an email address or dotted folder name
  (e.g. royalty-free audio credits like `...@gmail.com - track.mp3`) as
  `Unknown`.
- Adjustment layers, color mattes, black video, and other Premiere-native
  generators (which have no real underlying media file) were classified as
  `Unknown` instead of the new `Premiere element` type.

### Known limitations

- Nested/multicam sequences are detected but not recursively flattened
  (see README).
