# CLAUDE.md for LaserCam

## Build and Execution Commands
- **Run application**: `export PYTHONPATH=$PYTHONPATH:. && . /tmp/lasercam_venv/bin/activate && /tmp/lasercam_venv/bin/python -m mvp.app`
- **Run tests**: `export PYTHONPATH=$PYTHONPATH:. && . /tmp/lasercam_venv/bin/activate && pytest mvp/tests/`
- **Install dependencies**: `uv pip install -r requirements.txt` (Note: use `/tmp` venv to avoid NTFS symlink issues in WSL)

## Code Conventions
- **Naming**: Use snake_case for Python files, functions, and variables. PascalCase for classes.
- **Imports**: Use relative imports within the `mvp` package when appropriate. Always run with `python -m`.
- **Testing**: Use `pytest` for unit testing. Mock GUI dependencies (tkinter, PIL) in headless environments.
- **Style**: Follow PEP 8 (formatting with `black`, sorting with `isort`, style checking with `flake8`).
