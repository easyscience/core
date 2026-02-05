# Technology Stack

**Analysis Date:** 2026-02-05

## Languages

**Primary:**
- Python 3.11+ - Core language for all source code and utilities

**Supported Versions:**
- Python 3.11
- Python 3.12
- Python 3.13

## Runtime

**Environment:**
- CPython via Conda-Forge

**Package Manager:**
- pip - For PyPI dependencies
- pixi - For unified environment and dependency management across platforms
- Lockfile: `pixi.lock` - Fully specified environment for reproducible builds

**Platforms Supported:**
- Linux (linux-64)
- macOS (osx-64)
- macOS Intel (osx-arm64)
- Windows (win-64)

## Frameworks

**Core:**
- No web framework (library package)

**Scientific Computing:**
- numpy - Numerical array operations
- scipp - Scientific units and dimensions
- uncertainties - Propagation of measurement uncertainties

**Optimization/Fitting:**
- bumps - Flexible optimization framework with multiple algorithms
- lmfit - Extended Levenberg-Marquardt fitting
- DFO-LS - Derivative-Free Optimization for Least Squares

**Mathematical/Expression Evaluation:**
- asteval - Mathematical expression evaluation
- lmfit - Includes constraint solving and parameter management

**Build/Development:**
- hatchling (<=1.21.0) - Build backend
- setuptools-git-versioning - Version management from git tags
- build - Build package builder tool
- ruff - Fast Python linter and formatter (primary QA tool)
- pytest - Testing framework
- pytest-cov - Coverage plugin
- tox-gh-actions - GitHub Actions integration for tox

**Documentation:**
- Sphinx - Documentation generator
- sphinx_autodoc_typehints - Type hints in auto-documentation
- sphinx_book_theme - Modern documentation theme
- sphinx_gallery - Code gallery for documentation
- toml - TOML config parsing for docs
- doc8 - Documentation style checker
- readme-renderer - Markdown/RST rendering

## Key Dependencies

**Critical (core functionality):**
- `bumps` - Primary fitting engine with multiple algorithms (pt, de, dream, amoeba, etc.)
- `lmfit` - Extended Levenberg-Marquardt with constraints and bounds
- `DFO-LS` - Derivative-free optimization for least-squares problems
- `numpy` - Numerical operations and array handling
- `scipp` - Scientific data with units and dimensions
- `asteval` - Safe expression evaluation for model definitions
- `uncertainties` - Error propagation calculations

**Development (QA/Testing):**
- `pytest` - Test runner with fixtures and plugins
- `pytest-cov` - Code coverage measurement
- `ruff` - Linting and formatting enforcement
- `tox` - Multi-environment testing orchestration
- `codecov` - Coverage reporting to Codecov.io
- `matplotlib` - For visualization in examples
- `jupyterlab` - Interactive notebooks for development

**Build/Release:**
- `hatchling` - PEP 517/518 build backend
- `setuptools-git-versioning` - Dynamic versioning from git tags
- `build` - PEP 517 compatible build tool

## Configuration

**Build System:**
- Uses hatchling backend via `[build-system]` in `pyproject.toml`
- Version sourced from `src/easyscience/__version__.py` via git tags
- Excludes `src/easyscience/legacy` from wheel builds

**Linting & Formatting:**
- Tool: `ruff`
- Config: `[tool.ruff]` section in `pyproject.toml`
- Line length: 127 characters
- Quote style: Single quotes
- isort configuration for import ordering (force-single-line)
- Enforced rules: E, F, I, S (pycodestyle, pyflakes, isort, bandit)

**Testing:**
- Framework: `pytest`
- Configuration in `pyproject.toml` with coverage settings
- Coverage source: `src/easyscience`
- Test commands via pixi tasks
- Unit tests: `tests/unit_tests/`
- Integration tests: `tests/integration_tests/`

**Pixi Configuration (`pixi.toml`):**
- Workspace name: easyscience
- Conda channel: conda-forge
- Features for different environments: build, dev, docs
- Tasks for: test, test-unit, test-integration, lint, format, build, docs, clean
- Development environment combines all features

## Package Information

**Package Name:** easyscience
**Current Version:** 2.1.0 (managed via git tags)
**License:** BSD-3-Clause
**Repository:** https://github.com/EasyScience/EasyScience
**Documentation:** https://easyscience.github.io/EasyScience/
**Package Type:** Pure Python library (wheel distribution)

## Installation

**From PyPI:**
```bash
pip install easyscience
```

**From source (editable install):**
```bash
pixi run build
# or
pip install -e ".[dev]"  # includes development dependencies
```

**Optional feature installation:**
```bash
pip install "easyscience[dev]"   # Development tools
pip install "easyscience[docs]"  # Documentation tools
pip install "easyscience[build]" # Build tools
```

## Minimum Requirements

**Python:**
- >=3.11 (per `requires-python` in pyproject.toml)

**Core Dependencies:**
- No pinned versions for most dependencies; follows semantic versioning
- hatchling and setuptools-git-versioning have version caps (<=1.21.0)

**Operating System:**
- Cross-platform: Linux, macOS, Windows
- All platforms tested in CI/CD matrix

---

*Stack analysis: 2026-02-05*
