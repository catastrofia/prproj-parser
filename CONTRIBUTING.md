# Contributing

Thanks for helping improve `prproj-parser`. Keep changes small, focused, and easy to review.

## Setup

```bash
python -m pip install -e ".[dev,all]"
```

## Checks

Run these before asking for review:

```bash
ruff check .
ruff format --check .
mypy src
pytest
python -m build
python -m twine check dist/*
```

## Pull requests

- Open an issue or discussion first for non-trivial behavior, API, dependency, compatibility, or security changes.
- Direct PRs are fine for small docs, tests, and obvious fixes.
- Prefer one focused change per PR.
- Explain user-visible behavior and include tests or rationale when tests do not apply.

## Changelog

Add a `CHANGELOG.md` entry only for notable user-facing, API, compatibility, or security changes. Small docs, tests, refactors, and internal-only fixes usually do not need entries.

## Release process

Maintainers cut releases on demand when useful user-facing changes accumulate. A release PR updates `CHANGELOG.md`, version metadata if needed, and the release date. After CI passes, the maintainer tags the release and uses the dated changelog section as the GitHub Release notes.

## Labels

- `bug`: broken or incorrect behavior.
- `enhancement`: new or changed functionality.
- `documentation`: docs-only change.
- `tests`: test-only change.
- `security`: vulnerability or hardening work.
- `compatibility`: Python, Premiere Pro, XML backend, or platform compatibility.
- `dependencies`: dependency updates or policy changes.
- `good first issue`: small, well-scoped starter task.
- `help wanted`: maintainers welcome outside implementation help.

## Maintainer-only repository settings checklist

- Enable private vulnerability reporting if available.
- Protect the default branch with required CI checks.
- Require review before merge.
- Keep release and publish tokens scoped narrowly.
- Review issue/PR labels after public-readiness changes.
