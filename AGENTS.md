# Agent Notes

## Commands

```bash
python -m pip install -e ".[dev,all]"
ruff check .
ruff format --check .
mypy src
pytest
python -m build
python -m twine check dist/*
```

Use `.venv/bin/` command paths when the virtualenv exists.

## Constraints

- Commit only tiny synthetic or minimized fixtures.
- Do not add full real user projects.
- Treat `.prproj` files as private: they can contain local paths, names, and client info.
- Do not add dependencies without explaining why stdlib/current deps are insufficient.
- Prefer optional extras for niche functionality.
- Keep the default install dependency-free.
- Run the CI-equivalent checks above before claiming work is done.
