"""Add SPDX headers to Python files.

- SPDX-FileCopyrightText with the license holder name and organization
  URL from ``pyproject.toml`` as well as the file's creation year.
- SPDX-License-Identifier is taken from the project license value in
  ``pyproject.toml``.
"""

from __future__ import annotations

import argparse
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Optional
from typing import Union

from git import Repo
from spdx_headers.core import find_repository_root
from spdx_headers.core import get_copyright_info
from spdx_headers.data import load_license_data
from spdx_headers.operations import add_header_to_single_file

LICENSE_DATABASE = load_license_data()


def load_pyproject(repo_path: Union[str, Path]) -> dict:
    """Load and return parsed ``pyproject.toml`` data for the
    repository.
    """
    repo_root = find_repository_root(repo_path)
    pyproject_path = repo_root / 'pyproject.toml'

    with open(pyproject_path, 'rb') as file_handle:
        return tomllib.load(file_handle)


def get_file_creation_year(file_path: Union[str, Path]) -> str:
    """Return the year the file was first added to Git history.

    If the year cannot be determined, fall back to the current year.
    """
    file_path = Path(file_path)

    repo = Repo(file_path, search_parent_directories=True)
    root = Path(repo.working_tree_dir).resolve()
    rel_path = file_path.resolve().relative_to(root)

    rel_path_git = rel_path.as_posix()  # IMPORTANT for git pathspec

    # Get the year when the file was first added to Git history.
    # NOTE: Do not combine `--reverse` with `--max-count=1` here, as it can
    # yield an empty result with some Git versions. Instead, get the full
    # filtered output and take the first line.
    log_output = repo.git.log(
        '--follow',
        '--diff-filter=A',
        '--reverse',
        '--format=%ad',
        '--date=format:%Y',
        '--',
        rel_path_git,
    ).strip()

    year = log_output.splitlines()[0].strip() if log_output else ''

    return year or str(datetime.now().year)


def get_org_url(repo_path: Union[str, Path]) -> str:
    """Return the organization URL derived from the repository source
    URL.
    """
    pyproject_data = load_pyproject(repo_path)
    repo_url = pyproject_data['project']['urls']['Source Code']
    return repo_url.rsplit('/', 1)[0]


def get_project_license(repo_path: Union[str, Path]) -> str:
    """Return the project license value from ``pyproject.toml``."""
    pyproject_data = load_pyproject(repo_path)
    return pyproject_data['project']['license']


def get_copyright_holder(repo_path: Union[str, Path]) -> str:
    """Return the repository copyright holder name."""
    _, name, _ = get_copyright_info(repo_path)
    return name


def add_spdx_header(
    target_file: Union[str, Path],
    *,
    license_key: str,
    copyright_holder: str,
    org_url: str,
) -> None:
    """Add SPDX headers."""
    year = get_file_creation_year(target_file)

    add_header_to_single_file(
        filepath=target_file,
        license_key=license_key,
        license_data=LICENSE_DATABASE,
        year=year,
        name=copyright_holder,
        email=org_url,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Add SPDX headers to Python files under the given paths.',
    )
    parser.add_argument(
        'paths',
        nargs='+',
        help='Relative paths to scan (e.g. src tests)',
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_path = Path('.').resolve()
    license_key = get_project_license(repo_path)
    copyright_holder = get_copyright_holder(repo_path)
    org_url = get_org_url(repo_path)

    for base_dir in args.paths:
        base_path = Path(base_dir)
        if not base_path.exists():
            parser.error(f'Path does not exist: {base_dir}')

        for py_file in base_path.rglob('*.py'):
            add_spdx_header(
                py_file,
                license_key=license_key,
                copyright_holder=copyright_holder,
                org_url=org_url,
            )

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
