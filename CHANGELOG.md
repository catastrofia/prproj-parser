# Changelog

All notable changes to this project are documented here.

## [Unreleased]

### Fixed

- `load()` no longer re-parses the file a second time for projects without
  `VideoClip`/`MediaSource` elements (chain-free projects); the legacy
  chain-map fallback now runs only for indexes built directly instead of
  via the `from_*` builders.
- Bounded the `local_name()` memoization cache (pathological inputs with
  hundreds of thousands of distinct tags no longer grow the process
  without limit).
- `PrprojParseError` raised for invalid gzip files now chains the original
  exception for clearer tracebacks.

## [0.1.0] - 2026-10-13

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

### Changed

- **~9× faster `load()` on large projects.** Indexing is now strictly
  single-pass: the deterministic MasterClip → Media chain maps
  (`VideoClip`/`AudioClip` → Source → Media, plus `PlaybackSpeed`) are
  extracted during the index `iterparse` pass itself instead of a second
  full parse of the file, and the post-parse root cleanup is O(n) instead
  of O(n²) (per-child `remove()` calls rescanned the child list). On an
  8,000-clip synthetic project: ~2.26 s → ~0.23 s on the stdlib and
  defusedxml backends (lxml's C-level element removal already reduces the
  old cleanup cost, so gains there are smaller, ~1.5×). `list_sequences()`
  unchanged.
- `_build_chain_maps()` / `_build_chain_maps_from_bytes()` are now thin
  wrappers over the index's chain maps and are internal helpers (not for
  hot-path use); prefer `ProjectIndex.chain_maps()` (see the new
  `tests/test_performance.py` architecture tests).
- Namespace stripping in `local_name()` is memoized (element tags are
  highly repetitive across large project files).

### Added

- `benchmarks/` — synthetic fixture generator (`gen_fixture.py`) and
  benchmark harness (`bench.py`) for measuring parse performance without
  committing private project files.

### Known limitations

- Nested/multicam sequences are detected but not recursively flattened
  (see README).
