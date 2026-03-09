"""Test runner for tutorial scripts in the 'tutorials' directory.

This test discovers and executes all Python scripts located under the
'tutorials' directory to ensure they run without errors.

Important: each script must be executed in a fresh Python process.
Running many tutorials in-process (e.g. via runpy) leaks global state
between scripts (notably cached calculator dictionaries keyed only by
model/experiment names), which can cause false failures.
"""

import os
import subprocess  # noqa: S404
import sys
from pathlib import Path

import pytest

_repo_root = Path(__file__).resolve().parents[1]
_src_root = _repo_root / 'src'

# Discover tutorial scripts, excluding temporary checkpoint files
TUTORIALS = [
    p for p in Path('docs/docs/tutorials').rglob('*.py') if '.ipynb_checkpoints' not in p.parts
]


@pytest.mark.parametrize('script_path', TUTORIALS)
def test_script_runs(script_path: Path):
    """Execute a tutorial script and fail if it raises an exception.

    Each script is run in the context of __main__ to mimic standalone
    execution.
    """
    env = os.environ.copy()
    if _src_root.exists():
        existing = env.get('PYTHONPATH', '')
        env['PYTHONPATH'] = (
            str(_src_root) if not existing else str(_src_root) + os.pathsep + existing
        )

    # This is a test harness executing repo-local tutorial scripts.
    # We intentionally use subprocess isolation to prevent cross-test
    # global state leaks (e.g. calculator caches) that can cause false
    # failures when running tutorials in a shared interpreter.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(script_path)],
        cwd=str(_repo_root),
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        details = (result.stdout or '') + (result.stderr or '')
        pytest.fail(f'{script_path}\n{details.strip()}')
