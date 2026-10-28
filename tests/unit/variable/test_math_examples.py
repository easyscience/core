# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

"""
Unit tests for the code examples in the ``easyscience.math`` docstrings.

The examples are Markdown ``python`` code blocks, not doctests. A comment
line directly below a ``print(...)`` line is the expected output of that
print. Each test runs one block and compares what it prints with those
comments, so the documented output cannot go stale.
"""

import inspect
import re
import textwrap

import pytest

from easyscience import global_object
from easyscience import math as es_math

CODE_BLOCK = re.compile(r'```python\n(.*?)```', re.DOTALL)

# Aliases such as ``asin`` are the same objects as ``arcsin`` and share its docstring.
CANONICAL_FUNCTIONS = [name for name in es_math.__all__ if getattr(es_math, name).__name__ == name]


def code_blocks(docstring: str) -> list[str]:
    return [textwrap.dedent(block) for block in CODE_BLOCK.findall(inspect.cleandoc(docstring))]


def split_example(block: str) -> tuple[str, list[str]]:
    """Separate the code from the expected output, the comments below a print."""
    code, expected = [], []
    after_print = False
    for line in block.splitlines():
        if after_print and line.startswith('# '):
            expected.append(line.removeprefix('# '))
            continue
        code.append(line)
        after_print = line.startswith('print(')
    return '\n'.join(code), expected


DOCUMENTED_EXAMPLES = [
    pytest.param(es_math.__doc__, id='module'),
    *(pytest.param(getattr(es_math, name).__doc__, id=name) for name in CANONICAL_FUNCTIONS),
]


@pytest.fixture(autouse=True)
def clear():
    global_object.registry.clear()


class TestDocstringExamples:
    @pytest.mark.parametrize('docstring', DOCUMENTED_EXAMPLES)
    def test_example_prints_the_documented_output(self, docstring, capsys):
        # WHEN
        blocks = code_blocks(docstring)

        # THEN
        results = []
        for block in blocks:
            code, expected = split_example(block)
            exec(code, {})  # noqa: S102 - the code is our own docstring example
            results.append((capsys.readouterr().out.splitlines(), expected))

        # EXPECT
        assert blocks, 'no ```python example in the docstring'
        for printed, expected in results:
            assert expected, 'the example documents no output'
            assert printed == expected

    @pytest.mark.parametrize('name', CANONICAL_FUNCTIONS)
    def test_every_function_has_exactly_one_example(self, name):
        # WHEN
        docstring = getattr(es_math, name).__doc__

        # THEN
        blocks = code_blocks(docstring)

        # EXPECT
        assert len(blocks) == 1


class TestSplitExample:
    def test_comments_after_a_print_are_the_expected_output(self):
        # WHEN
        block = 'x = 1\nprint(x)\n# 1\nprint(x + 1)\n# 2\n'

        # THEN
        code, expected = split_example(block)

        # EXPECT
        assert code == 'x = 1\nprint(x)\nprint(x + 1)'
        assert expected == ['1', '2']

    def test_other_comments_stay_in_the_code(self):
        # WHEN
        block = '# set up\nx = 1\nprint(x)\n# 1\n'

        # THEN
        code, expected = split_example(block)

        # EXPECT
        assert code == '# set up\nx = 1\nprint(x)'
        assert expected == ['1']
