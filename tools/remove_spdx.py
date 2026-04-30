"""Remove SPDX headers from Python files."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from spdx_headers.operations import remove_header_from_py_files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Remove SPDX headers from Python files under the given paths.',
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

    for base_dir in args.paths:
        base_path = Path(base_dir)
        if not base_path.exists():
            parser.error(f'Path does not exist: {base_dir}')

        remove_header_from_py_files(base_dir)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
