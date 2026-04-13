# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from unittest.mock import MagicMock

import pytest

from easyscience import ObjBase
from easyscience import Parameter
from easyscience.fitting.fitter import Fitter
from easyscience.fitting.multi_fitter import MultiFitter


class Line(ObjBase):
    m: Parameter
    c: Parameter

    def __init__(self, m_val: float, c_val: float):
        m = Parameter('m', m_val)
        c = Parameter('c', c_val)
        super().__init__('line', m=m, c=c)

    def __call__(self, x):
        return self.m.value * x + self.c.value


class TestMultiFitter:
    @pytest.fixture
    def multi_fitter(self, monkeypatch):
        monkeypatch.setattr(Fitter, '_update_minimizer', MagicMock())
        fit_object_1 = Line(1.0, 0.5)
        fit_object_2 = Line(2.0, 1.5)
        return MultiFitter([fit_object_1, fit_object_2], [fit_object_1, fit_object_2])

    def test_fit_progress_callback(self, multi_fitter: MultiFitter):
        # When
        multi_fitter._precompute_reshaping = MagicMock(
            return_value=('x_fit', 'x_new', 'y_new', 'weights', 'dims')
        )
        multi_fitter._fit_function_wrapper = MagicMock(return_value='wrapped_fit_function')
        multi_fitter._post_compute_reshaping = MagicMock(return_value='fit_result')
        multi_fitter._minimizer = MagicMock()
        multi_fitter._minimizer.fit = MagicMock(return_value='result')
        progress_callback = MagicMock()

        # Then
        result = multi_fitter.fit(
            ['x_1', 'x_2'],
            ['y_1', 'y_2'],
            ['weights_1', 'weights_2'],
            progress_callback=progress_callback,
        )

        # Expect
        assert result == 'fit_result'
        multi_fitter._minimizer.fit.assert_called_once_with(
            'x_fit',
            'y_new',
            weights='weights',
            tolerance=None,
            max_evaluations=None,
            progress_callback=progress_callback,
        )