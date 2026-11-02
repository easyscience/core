# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

"""
Unit tests for the examples in the ``easyscience.math`` docstrings.

The examples are doctests. Each test runs the examples of one docstring
with Python's ``doctest`` and compares what they print with the
documented output, so the documentation cannot go stale.
"""

import doctest
import re

import pytest

from easyscience import global_object
from easyscience import math as es_math

FLOAT = re.compile(r'[-+]?\d+\.\d+(?:[eE][-+]?\d+)?')
SIGNIFICANT_DIGITS = 10


def round_floats(text):
    """Round every float in ``text`` to ``SIGNIFICANT_DIGITS`` significant digits."""
    return FLOAT.sub(lambda match: f'{float(match.group()):.{SIGNIFICANT_DIGITS}g}', text)


class FloatTolerantChecker(doctest.OutputChecker):
    """
    Compare doctest output exactly, then again with the floats rounded.

    The last digits of ``sinh``, ``arctan`` and other libm functions differ between platforms,
    so the documented output is compared to about ten significant digits.
    """

    def check_output(self, want, got, optionflags):
        if super().check_output(want, got, optionflags):
            return True
        return super().check_output(round_floats(want), round_floats(got), optionflags)


# Aliases such as ``asin`` are the same objects as ``arcsin`` and share its docstring.
CANONICAL_FUNCTIONS = [name for name in es_math.__all__ if getattr(es_math, name).__name__ == name]
# One doctest per docstring that has examples, keyed by function name, or 'module'.
DOCTESTS = {
    'module' if test.name == es_math.__name__ else test.name.rsplit('.', 1)[-1]: test
    for test in doctest.DocTestFinder().find(es_math)
    if test.examples
}


@pytest.fixture(autouse=True)
def clear():
    global_object.registry.clear()


class TestDocstringExamples:
    @pytest.mark.parametrize('name', ['module', *CANONICAL_FUNCTIONS])
    def test_examples_print_the_documented_output(self, name):
        # WHEN
        test = DOCTESTS[name]
        report = []

        # THEN
        result = doctest.DocTestRunner(checker=FloatTolerantChecker()).run(test, out=report.append)

        # EXPECT
        assert result.failed == 0, ''.join(report)

    @pytest.mark.parametrize('name', CANONICAL_FUNCTIONS)
    def test_every_function_has_an_example(self, name):
        # WHEN THEN
        test = DOCTESTS.get(name)

        # EXPECT
        assert test is not None and test.examples
