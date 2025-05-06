#  SPDX-FileCopyrightText: 2022 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2022 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience>


import numpy as np
import pytest

from easyscience.models.polynomial import Polynomial

poly_test_cases = (
    (1.,),
    (
        1.,
        2.,
    ),
    (1., 2., 3.),
    (-1., -2., -3.),
    (0.72, 6.48, -0.48),
)

@pytest.mark.parametrize("coo", poly_test_cases)
def test_Polynomial_pars(coo):
    poly = Polynomial(coefficients=coo)

    vals = {coo.value for coo in poly.coefficients}
    assert len(vals.difference(set(coo))) == 0

    x = np.linspace(0, 10, 100)
    y = np.polyval(coo, x)
    assert np.allclose(poly(x), y)
