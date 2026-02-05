# External Integrations

**Analysis Date:** 2026-02-05

## APIs & External Services

**No Active External APIs Detected**

This codebase is a scientific computing library with no active integrations to external APIs. It is designed as a standalone package consumed by other applications rather than as a service that calls external endpoints.

## Data Storage

**Databases:**
- Not applicable - Pure library package
- No database integrations

**File Storage:**
- Local filesystem only
- No cloud storage integrations (S3, Azure Blob, etc.)
- Serialization to JSON and XML via internal modules:
  - `src/easyscience/io/` - Contains serializer implementations
  - `src/easyscience/legacy/json.py` - JSON encoding/decoding
  - `src/easyscience/legacy/xml.py` - XML serialization

**Caching:**
- None - Pure computational library

## Authentication & Identity

**Auth Provider:**
- Not applicable - Library with no user authentication

**Authorization:**
- Not applicable

## Monitoring & Observability

**Error Tracking:**
- Not integrated - No Sentry, Rollbar, or similar services

**Logging:**
- Standard Python logging module (stdlib)
- Implementation: `src/easyscience/global_object/logger.py`
- Logger accessed via GlobalObject singleton
- Supports configurable log levels
- No external logging services or structured logging frameworks

**Debugging:**
- Debug mode available via `GlobalObject.debug` flag
- No remote debugging tools integrated

## CI/CD & Deployment

**Package Registry:**
- PyPI - Primary distribution channel
- Action: `pypa/gh-action-pypi-publish@release/v1`
- Credentials: `${{ secrets.PYPI_TOKEN_ES }}`

**Code Quality Monitoring:**
- Codecov - Coverage report aggregation
  - Action: `codecov/codecov-action@v5`
  - Token: `${{ secrets.CODECOV_TOKEN }}`
  - Scope: EasyScience/corelib repository
  - Reports: Unit test coverage to codecov.io

**Code Scanning:**
- CodeQL - Static security analysis
  - Workflow: `.github/workflows/codeql-analysis.yml`
- OSSAR - Microsoft's Open Source Security Analysis
  - Workflow: `.github/workflows/ossar-analysis.yml`

**Hosting:**
- GitHub - Repository and CI/CD
- GitHub Actions - Build and test orchestration
- GitHub Pages - Documentation hosting

**CI Pipeline:**
- GitHub Actions primary workflow: `.github/workflows/python-ci.yml`
- Additional workflows:
  - `python-package.yml` - Package build on master branch
  - `python-publish.yml` - PyPI publish on version tags
  - `documentation-build.yml` - Sphinx documentation generation
  - `nightly-check.yml` - Scheduled verification tests
  - `release-drafter.yml` - Automated release note generation

## Webhooks & Callbacks

**Incoming:**
- None - Library package receives no webhooks

**Outgoing:**
- None - Library makes no webhook calls

## Version Control & Release

**Git Repository:**
- Platform: GitHub
- URL: https://github.com/EasyScience/EasyScience
- Versioning: Git tags in format `v*` trigger PyPI publishing
- Main branch: master
- Development branch: develop

**Release Management:**
- Release Drafter: Automated changelog from pull requests
- Version bumping: Via git tags (setuptools-git-versioning)
- Release workflow triggers on `push tags: ['v*']`

## Pre-commit & Code Standards

**Pre-commit Hooks:**
- Tool: pre-commit framework
- Config: `.pre-commit-config.yaml`
- Active hooks:
  - Black (v22.3.0) - Code formatting (legacy, may be replaced by ruff)
  - Pre-commit standard hooks:
    - trailing-whitespace
    - check-yaml
    - check-xml
    - check-toml
    - pretty-format-json
    - detect-private-key
  - Language formatter hooks:
    - pretty-format-yaml (with autofix and indent=2)

## Documentation & Community

**Documentation Hosting:**
- GitHub Pages - Served from repository
- URL: https://easyscience.github.io/EasyScience/
- Generator: Sphinx
- Build workflow: `.github/workflows/documentation-build.yml`

**Package Metadata:**
- Homepage: https://github.com/EasyScience/EasyScience
- License: BSD-3-Clause

## Environment Variables & Secrets

**Required Secrets (for CI/CD):**
- `PYPI_TOKEN_ES` - PyPI authentication for publishing
- `CODECOV_TOKEN` - Codecov authentication for coverage reporting

**Configuration Files:**
- `.codecov.yml` - Codecov behavior configuration
  - GitHub checks enabled with annotations
  - Comment layout: reach, diff, flags, files
  - Requires head report for posting comments

**Build Artifacts:**
- Uploaded to GitHub Actions as artifacts
- Distribution files stored in `dist/` directory
- Wheel and source distributions built via hatchling

## Platform-Specific Integrations

**Development Environment:**
- Pixi for cross-platform environment management
- Channels: conda-forge only
- Tested on:
  - ubuntu-latest
  - macos-latest
  - macos-15-intel
  - windows-latest

**Dependency Sources:**
- PyPI (primary) - All Python packages
- Conda-Forge (via pixi) - Optional conda packages

---

*Integration audit: 2026-02-05*
