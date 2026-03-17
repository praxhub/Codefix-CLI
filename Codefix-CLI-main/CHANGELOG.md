# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-03-17

### Added
- Standardized Python package structure (src layout).
- Added `pyproject.toml` for pip installation.
- Integrated `git+https` remote installation support.
- Added `codefixcli` command alias.
- Added automatic installation scripts (`install.ps1`, `install.sh`).

### Changed
- Restructured `codefix.py` into `src/codefixcli/cli.py`.
- Moved debugger logic into the `codefixcli.debugger` subpackage.
- Updated settings loading to use `importlib.resources`.
