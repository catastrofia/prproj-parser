# prproj-parser

A pure-Python parser for Adobe Premiere Pro `.prproj` project files. Extracts sequences, tracks, and clips (with resolved media paths, timecodes, and clip types) without needing Premiere Pro installed.

`.prproj` files store a flat, gzip-compressed XML object graph — sequences, tracks, and clips reference each other by ID rather than nesting. This library resolves that reference graph into a simple, typed object model.

## Install

```bash
pip install prproj-parser
```

Optional extras:

```bash
pip install prproj-parser[fast]    # lxml backend (faster parsing)
pip install prproj-parser[secure]  # defusedxml backend (hardened against XML entity attacks)
pip install prproj-parser[all]     # both
```

Requires Python 3.9+. No dependencies by default — falls back to the stdlib `xml.etree.ElementTree`.

## Quick start

```python
from prproj_parser import load

project = load("my_project.prproj")

for seq in project.sequences:
    print(seq.name, seq.frame_rate, seq.duration_seconds)
    for clip in seq.clips:
        print(f"  [{clip.clip_type}] {clip.name}  {clip.start_timecode}-{clip.end_timecode}")
        if clip.media:
            print(f"    media: {clip.media.best_path}")
```

For just the sequence names (near-zero memory, doesn't resolve clips):

```python
from prproj_parser import list_sequences

names = list_sequences("my_project.prproj")
```

## API

| Function / Class | Purpose |
|---|---|
| `load(file_path)` | Parse a `.prproj` file, return a fully-resolved `Project`. |
| `list_sequences(file_path)` | Ultra-lightweight: just sequence names. |
| `Project` | `.sequences`, `.sequence_names`, `.get_sequence(name)` |
| `Sequence` | `.clips`, `.video_clips`, `.audio_clips`, `.tracks`, `.frame_rate`, `.duration_seconds` |
| `Track` | `.index`, `.track_type`, `.clips` |
| `Clip` | `.name`, `.start_timecode`/`.end_timecode`, `.start_seconds`/`.end_seconds`, `.duration_seconds`, `.clip_type`, `.speed_percent`, `.media`, `.is_nested_sequence` |
| `MediaInfo` | `.best_path`, `.file_path`, `.actual_path`, `.relative_path`, `.title` |

`clip_type` is one of `"Video"`, `"Audio"`, `"Image"`, `"Graphic"`, `"Premiere element"` (adjustment layers, color mattes, black video, bars & tone — no real underlying media file), or `"Unknown"`.

`speed_percent` is `100.0` for normal speed, `200.0` for 2x, `50.0` for half speed, etc.

Both `.prproj` files that are gzip-compressed (the common case) and files that are plain UTF-8 XML (also produced by Premiere Pro) are supported transparently.

See the module docstrings (`help(prproj_parser)`) for full API details — the package ships with type hints (`py.typed`).

## Format documentation

This parser is based on observed `.prproj` files, not an Adobe-published specification. See [docs/prproj-format](docs/prproj-format/README.md) for the detailed unofficial format notes, traversal model, timing rules, and known gotchas.

## Known limitations

- **Nested/multicam sequences are not flattened.** A sequence nested inside another timeline is detected (`clip.is_nested_sequence == True`) but its own clips are not recursively resolved. Tracked in [#1](https://github.com/catastrofia/prproj-parser/issues/1).
- **Speed ramps / time remapping** (as opposed to a single constant speed) report the clip's base `PlaybackSpeed` value; keyframed speed changes over the clip's duration are not modeled.
- Verified against Premiere Pro project files from 2023–2026. The detailed format notes describe both the root `<PremiereData Version="3">` value and observed project-file versions 40, 42, 43, and 45.

## Development

```bash
pip install -e ".[all]"
pip install pytest
pytest
```

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) before opening an issue or pull request, especially if you plan to share `.prproj` examples.

## License

MIT
