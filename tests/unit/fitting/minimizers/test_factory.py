# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from unittest.mock import MagicMock

import pytest

from easyscience import Minimizers
from easyscience.fitting.minimizers import MinimizerBase
from easyscience.fitting.minimizers.factory import factory


class TestFactory:
    def pull_minminizer(self, minimizer: Minimizers) -> MinimizerBase:
        mock_fit_object = MagicMock()
        mock_fit_function = MagicMock()
        minimizer = factory(minimizer, mock_fit_object, mock_fit_function)
        return minimizer

    @pytest.mark.parametrize(
        'minimizer_method,minimizer_enum',
        [
            ('leastsq', Minimizers.LMFit),
            ('leastsq', Minimizers.LMFit_leastsq),
            ('powell', Minimizers.LMFit_powell),
            ('cobyla', Minimizers.LMFit_cobyla),
            ('differential_evolution', Minimizers.LMFit_differential_evolution),
            ('least_squares', Minimizers.LMFit_scipy_least_squares),
        ],
    )
    def test_factory_lm_fit(self, minimizer_method, minimizer_enum):
        minimizer = self.pull_minminizer(minimizer_enum)
        assert minimizer._method == minimizer_method
        assert minimizer.package == 'lmfit'

    @pytest.mark.parametrize(
        'minimizer_method,minimizer_enum',
        [
            ('amoeba', Minimizers.Bumps),
            ('amoeba', Minimizers.Bumps_simplex),
            ('newton', Minimizers.Bumps_newton),
            ('lm', Minimizers.Bumps_lm),
        ],
    )
    def test_factory_bumps_fit(self, minimizer_method, minimizer_enum):
        minimizer = self.pull_minminizer(minimizer_enum)
        assert minimizer._method == minimizer_method
        assert minimizer.package == 'bumps'

    @pytest.mark.parametrize(
        'minimizer_method,minimizer_enum',
        [('leastsq', Minimizers.DFO), ('leastsq', Minimizers.DFO_leastsq)],
    )
    def test_factory_dfo_fit(self, minimizer_method, minimizer_enum):
        minimizer = self.pull_minminizer(minimizer_enum)
        assert minimizer._method == minimizer_method
        assert minimizer.package == 'dfo'


def test_available_minimizers():
    assert Minimizers.LMFit
    assert Minimizers.LMFit_leastsq
    assert Minimizers.LMFit_powell
    assert Minimizers.LMFit_cobyla
    assert Minimizers.LMFit_differential_evolution
    assert Minimizers.LMFit_scipy_least_squares
    assert Minimizers.Bumps
    assert Minimizers.Bumps_simplex
    assert Minimizers.Bumps_newton
    assert Minimizers.Bumps_lm
    assert Minimizers.DFO
    assert Minimizers.DFO_leastsq
    assert len(Minimizers) == 12
