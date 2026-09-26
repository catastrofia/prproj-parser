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
- Use a fork or branch and open a PR; `main` is maintainer-merge only.
- Prefer one focused change per PR.
- Explain user-visible behavior and include tests or rationale when tests do not apply.
- Squash merge is the default.
- Contributors own CI fixes. Maintainers may push mechanical fixes when maintainer edits are allowed.
- Semantic changes need review or discussion before merge.
- Stale PRs may be marked stale around 30 days and closed around 60 days; reopening is welcome.
- Useful abandoned PRs may be recreated or cherry-picked with attribution.

## Changelog

Add a `CHANGELOG.md` entry only for notable user-facing, API, compatibility, or security changes. Small docs, tests, refactors, and internal-only fixes usually do not need entries.

## Release process

Maintainers cut releases on demand when useful user-facing changes accumulate. A release PR updates `CHANGELOG.md`, version metadata if needed, and the release date. Release notes come from the dated `CHANGELOG.md` section. Maintainers tag and publish releases manually after CI passes.

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

- Require pull requests before merging to `main`.
- Restrict merge access to maintainers.
- Require CI status checks before merge.
- Block force pushes and branch deletion on `main`.
- Enable dependency graph and Dependabot/security alerts.
- Enable private vulnerability reporting if available.
- Keep release tokens scoped narrowly if any are used manually.
- Review issue/PR labels after public-readiness changes.
