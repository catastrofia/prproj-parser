# File Format

*Doc version 1.1 — 2026-09-18*

## Is it XML?

Yes, always. Every `.prproj` file — across all Premiere Pro versions checked
(2023 through 2026) — is a UTF-8 XML document with one of two possible
wrappers:

1. **Gzip-compressed**, or
2. **Plain, uncompressed XML**

You can tell which one you're looking at from the first two bytes of the
file:

| First bytes | Format |
|---|---|
| `1F 8B` | Gzip-compressed XML |
| `3C 3F` (`<?`) | Plain XML |

```python
with open(path, "rb") as f:
    data = f.read()

if data[:2] == b"\x1f\x8b":
    import gzip

    xml_bytes = gzip.decompress(data)
else:
    xml_bytes = data
```

Don't guess based on the `.prproj` extension or file size — always check the
magic bytes. Both forms are common, and the same project can be saved as
either one at different points in its life, so this is a save-time choice
rather than something tied to a Premiere Pro version. (Adobe's community
forums attribute this to a "Compress Project Files on Save" preference —
that's an external claim, not something this documentation verifies
directly, but it fits what's observed.)

## What's inside

Once decompressed (if needed), every file starts the same way:

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<PremiereData Version="3">
    ...
</PremiereData>
```

- Encoding is always UTF-8.
- The outer `PremiereData Version` attribute stays `"3"` across every
  Premiere Pro release from 2023 through 2026 — it does **not** tell you
  which Premiere Pro release wrote the file. For that, see
  [Version Differences](03-versions.md).
- Indentation is tabs, one per nesting level, consistently.
- No XML namespaces are used in this format — you will not see tags like
  `<ns:Sequence>` or an `xmlns` attribute.

## The two `Project` elements at the top

Right inside `<PremiereData>`, you'll always find two `Project` elements,
one right after the other:

```xml
<PremiereData Version="3">
	<Project ObjectRef="1"/>
	<Project ObjectID="1" ClassID="62ad66dd-0dcd-42da-a660-6d8fbde94876" Version="42">
		...
	</Project>
	...
</PremiereData>
```

The first one, `<Project ObjectRef="1"/>`, is just a pointer — it says "the
project's root object has ID 1." It carries no actual data. The second one
is the real thing, and its `Version` attribute is the number you actually
want (see [Version Differences](03-versions.md) — this is where "42" or "45"
etc. comes from).

## Typical file sizes

`.prproj` files can get large — from under 100 KB for a quick test project up
to several hundred megabytes for a years-old, heavily-edited production
project. A gzip-compressed file typically decompresses to 10–20× its on-disk
size. If you're writing a parser, plan for streaming rather than loading
everything into memory at once — see [Parser Gotchas](08-gotchas.md).
