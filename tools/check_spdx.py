"""Check SPDX headers in Python files."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from spdx_headers.operations import check_headers


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Check SPDX headers in Python files under the given paths.',
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

    exit_codes = []

    for base_dir in args.paths:
        base_path = Path(base_dir)
        if not base_path.exists():
            parser.error(f'Path does not exist: {base_dir}')

        print('=' * 50)
        print(f'Checking SPDX headers in: {base_dir}')
        exit_codes.append(check_headers(base_dir))

    return 0 if all(code == 0 for code in exit_codes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
