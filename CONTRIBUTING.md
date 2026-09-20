# Contributing

Small, focused issues and pull requests are easiest to review.

## Local setup

```bash
python -m pip install -e ".[all]" pytest
pytest
```

## Development workflow

1. Open an issue for behavior changes unless the change is a typo or docs-only fix.
2. Keep pull requests focused on one parser behavior, one docs correction, or one maintenance change.
3. Add or update a test for parser behavior changes.
4. Run `pytest` before opening a pull request.
5. If the change affects packaging or public docs, run:

```bash
python -m pip install build twine
python -m build
twine check dist/*
```

## Sharing `.prproj` examples

`.prproj` files can contain local paths, usernames, project names, clip names, client names, and production metadata.

Do not attach real client or production project files publicly unless you have permission and have checked the contents. Prefer the smallest sanitized XML excerpt or a tiny synthetic project that reproduces the issue.

Sanitized examples must not contain:

- real client names
- real project names
- usernames
- host paths
- media paths
- clip names from private work
- sensitive IDs or production identifiers

## Documentation changes

For format documentation corrections, include the Premiere Pro version and the evidence source when possible. It is fine to say when something is an inference rather than directly verified.
