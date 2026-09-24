## Summary

-

## Checklist

- [ ] Change is small and focused.
- [ ] Non-trivial behavior/API/compatibility/security change was discussed first.
- [ ] Tests or rationale are included.
- [ ] Fixtures are tiny synthetic/minimized samples, not full real projects.
- [ ] No private paths, names, client info, or real project data were added.
- [ ] New dependencies are justified, optional where practical, and keep the default install dependency-free.
- [ ] Changelog updated only for notable user-facing/API/compatibility/security changes.
- [ ] Ran relevant checks:
  - [ ] `ruff check .`
  - [ ] `ruff format --check .`
  - [ ] `mypy src`
  - [ ] `pytest`
  - [ ] `python -m build`
  - [ ] `python -m twine check dist/*`

<!-- Maintainers:
- Confirm default branch protection and required CI still cover this change.
- Confirm release/publish tokens are not touched.
- Confirm private vulnerability reporting is enabled or SECURITY.md fallback is current.
- Confirm labels/changelog/release notes are correct for user-facing changes.
-->
