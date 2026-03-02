"""Update or insert SPDX headers in Python files.

- Ensures SPDX-FileCopyrightText has the current year.
- Ensures SPDX-License-Identifier is set to BSD-3-Clause.
"""

import fnmatch
import re
from pathlib import Path

COPYRIGHT_TEXT = (
    '# SPDX-FileCopyrightText: 2021-2026 EasyScience contributors <https://github.com/easyscience>'
)
LICENSE_TEXT = '# SPDX-License-Identifier: BSD-3-Clause'

# Patterns to exclude from SPDX header updates (vendored code)
EXCLUDE_PATTERNS = [
    '*/_vendored/jupyter_dark_detect/*',
]


def should_exclude(file_path: Path) -> bool:
    """Check if a file should be excluded from SPDX header updates."""
    path_str = str(file_path)
    return any(fnmatch.fnmatch(path_str, pattern) for pattern in EXCLUDE_PATTERNS)


def update_spdx_header(file_path: Path):
    # Use Path.open to satisfy lint rule PTH123.
    with file_path.open('r', encoding='utf-8') as f:
        original_lines = f.readlines()

    # Regexes for SPDX lines
    copy_re = re.compile(r'^#\s*SPDX-FileCopyrightText:.*$')
    lic_re = re.compile(r'^#\s*SPDX-License-Identifier:.*$')

    # 1) Preserve any leading shebang / coding cookie lines
    prefix = []
    body_start = 0
    if original_lines:
        # Shebang line like "#!/usr/bin/env python3"
        if original_lines[0].startswith('#!'):
            prefix.append(original_lines[0])
            body_start = 1
        # PEP 263 coding cookie on first or second line
        # e.g. "# -*- coding: utf-8 -*-" or "# coding: utf-8"
        for _ in range(2):  # at most one more line to inspect
            if body_start < len(original_lines):
                line = original_lines[body_start]
                if re.match(r'^#.*coding[:=]\s*[-\w.]+', line):
                    prefix.append(line)
                    body_start += 1
                else:
                    break

    # 2) Work on the remaining body
    body = original_lines[body_start:]

    # Remove any existing SPDX lines anywhere in the body
    body = [ln for ln in body if not (copy_re.match(ln) or lic_re.match(ln))]

    # Strip leading blank lines in the body so header is tight
    while body and not body[0].strip():
        body.pop(0)

    # 3) Build canonical SPDX block: two lines + exactly one blank
    spdx_block = [
        COPYRIGHT_TEXT + '\n',
        LICENSE_TEXT + '\n',
        '\n',
    ]

    # 4) New content: prefix + SPDX + body
    new_lines = prefix + spdx_block + body

    # 5) Normalize: collapse any extra blank lines immediately after
    #    LICENSE to exactly one. This keeps the script idempotent.
    # Find the index of LICENSE we just inserted (prefix may be 0, 1,
    # or 2 lines)
    lic_idx = len(prefix) + 1  # spdx_block[1] is the license line
    # Ensure exactly one blank line after LICENSE
    # Remove all blank lines after lic_idx, then insert a single blank.
    j = lic_idx + 1
    # Remove any number of blank lines following
    while j < len(new_lines) and not new_lines[j].strip():
        new_lines.pop(j)
    # Insert exactly one blank line at this position
    new_lines.insert(j, '\n')

    with file_path.open('w', encoding='utf-8') as f:
        f.writelines(new_lines)


def main():
    """Recursively update or insert SPDX headers in all Python files
    under the 'src' and 'tests' directories.
    """
    for base_dir in ('src', 'tests'):
        for py_file in Path(base_dir).rglob('*.py'):
            if should_exclude(py_file):
                continue
            update_spdx_header(py_file)


if __name__ == '__main__':
    main()
