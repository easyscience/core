# SPDX-FileCopyrightText: 2021-2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

#  © 2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience>


import numpy as np
import pytest

from easyscience import global_object
from easyscience.base_classes import CollectionBase
from easyscience.models.polynomial import Polynomial
from easyscience.variable import Parameter


@pytest.fixture
def clear():
    """Clear global object map before each test."""
    global_object.map._clear()


poly_test_cases = (
    (1.0,),
    (
        1.0,
        2.0,
    ),
    (1.0, 2.0, 3.0),
    (-1.0, -2.0, -3.0),
    (0.72, 6.48, -0.48),
)


@pytest.mark.parametrize('coo', poly_test_cases)
def test_Polynomial_pars(clear, coo):
    poly = Polynomial(coefficients=coo)

    vals = {coo.value for coo in poly.coefficients}
    assert len(vals.difference(set(coo))) == 0

    x = np.linspace(0, 10, 100)
    y = np.polyval(coo, x)
    assert np.allclose(poly(x), y)


def test_Polynomial_default_initialization(clear):
    """Test Polynomial with no coefficients."""
    poly = Polynomial(name='test_poly')

    assert poly.name == 'test_poly'
    assert len(poly.coefficients) == 0

    # Test that calling the polynomial with empty coefficients works
    x = np.array([1, 2, 3])
    result = poly(x)
    assert len(result) == len(x)


def test_Polynomial_with_Parameter_objects(clear):
    """Test Polynomial with Parameter objects as coefficients."""
    p0 = Parameter('c0', value=1.0)
    p1 = Parameter('c1', value=2.0)
    p2 = Parameter('c2', value=3.0)

    poly = Polynomial(coefficients=[p0, p1, p2])

    assert len(poly.coefficients) == 3
    assert poly.coefficients[0].name == 'c0'
    assert poly.coefficients[1].name == 'c1'
    assert poly.coefficients[2].name == 'c2'
    assert poly.coefficients[0].value == 1.0
    assert poly.coefficients[1].value == 2.0
    assert poly.coefficients[2].value == 3.0

    # Test evaluation - coefficients passed directly to polyval
    # polyval([1.0, 2.0, 3.0], x) = 1.0*x^2 + 2.0*x + 3.0
    x = np.array([0, 1, 2])
    expected = np.polyval([1.0, 2.0, 3.0], x)
    assert np.allclose(poly(x), expected)


def test_Polynomial_with_mixed_coefficients(clear):
    """Test Polynomial with mixed float and Parameter coefficients."""
    p0 = Parameter('c0', value=5.0)

    poly = Polynomial(coefficients=[p0, 2.0, 1.0])

    assert len(poly.coefficients) == 3
    assert poly.coefficients[0].name == 'c0'
    assert poly.coefficients[1].name == 'c1'
    assert poly.coefficients[2].name == 'c2'

    # polyval([5.0, 2.0, 1.0], x) = 5.0*x^2 + 2.0*x + 1.0
    x = np.array([1, 2, 3])
    expected = np.polyval([5.0, 2.0, 1.0], x)
    assert np.allclose(poly(x), expected)


def test_Polynomial_with_CollectionBase(clear):
    """Test Polynomial initialized with a CollectionBase."""
    collection = CollectionBase('coeffs')
    collection.append(Parameter('c0', value=1.0))
    collection.append(Parameter('c1', value=2.0))
    collection.append(Parameter('c2', value=3.0))

    poly = Polynomial(coefficients=collection)

    assert poly.coefficients is collection
    assert len(poly.coefficients) == 3

    # polyval([1.0, 2.0, 3.0], x) = 1.0*x^2 + 2.0*x + 3.0
    x = np.array([0, 1, 2])
    expected = np.polyval([1.0, 2.0, 3.0], x)
    assert np.allclose(poly(x), expected)


def test_Polynomial_invalid_coefficient_type(clear):
    """Test that invalid coefficient types raise TypeError."""
    with pytest.raises(TypeError, match='Coefficients must be floats or Parameters'):
        Polynomial(coefficients=[1.0, 'invalid', 3.0])

    with pytest.raises(TypeError, match='Coefficients must be floats or Parameters'):
        Polynomial(coefficients=[1, 2, 3])  # integers, not floats


def test_Polynomial_invalid_coefficients_type(clear):
    """Test that invalid coefficients argument type raises TypeError."""
    # String is iterable, so it will iterate over characters and fail with first error
    with pytest.raises(TypeError, match='Coefficients must be floats or Parameters'):
        Polynomial(coefficients='invalid')

    # Integer is not iterable, so it will fail with second error
    with pytest.raises(TypeError, match='coefficients must be a list or a CollectionBase'):
        Polynomial(coefficients=42)


def test_Polynomial_repr_no_coefficients(clear):
    """Test __repr__ with no coefficients."""
    poly = Polynomial(name='empty')

    repr_str = repr(poly)
    assert 'Polynomial(empty, )' == repr_str


def test_Polynomial_repr_one_coefficient(clear):
    """Test __repr__ with one coefficient."""
    poly = Polynomial(coefficients=[5.0])

    repr_str = repr(poly)
    assert 'Polynomial(polynomial, 5.0)' == repr_str


def test_Polynomial_repr_two_coefficients(clear):
    """Test __repr__ with two coefficients."""
    poly = Polynomial(coefficients=[3.0, 2.0])

    repr_str = repr(poly)
    assert 'Polynomial(polynomial, 2.0x + 3.0)' == repr_str


def test_Polynomial_repr_three_coefficients(clear):
    """Test __repr__ with three coefficients."""
    poly = Polynomial(coefficients=[1.0, 2.0, 3.0])

    repr_str = repr(poly)
    assert 'Polynomial(polynomial, 3.0x^2 + 2.0x + 1.0)' == repr_str


def test_Polynomial_repr_with_zero_coefficients(clear):
    """Test __repr__ with some zero coefficients."""
    poly = Polynomial(coefficients=[1.0, 0.0, 3.0, 0.0, 5.0])

    repr_str = repr(poly)
    # Zero coefficients for higher powers should be excluded
    assert 'Polynomial(polynomial, 5.0x^4 + 3.0x^2 + 0.0x + 1.0)' == repr_str


def test_Polynomial_repr_negative_coefficients(clear):
    """Test __repr__ with negative coefficients."""
    poly = Polynomial(coefficients=[-1.0, -2.0, -3.0])

    repr_str = repr(poly)
    assert 'Polynomial(polynomial, -3.0x^2 + -2.0x + -1.0)' == repr_str


def test_Polynomial_call_with_args_kwargs(clear):
    """Test that __call__ accepts *args and **kwargs."""
    poly = Polynomial(coefficients=[1.0, 2.0, 3.0])

    x = np.array([0, 1, 2])
    # These additional args/kwargs should be ignored
    result = poly(x, 'extra_arg', extra_kwarg='value')
    # polyval([1.0, 2.0, 3.0], x) = 1.0*x^2 + 2.0*x + 3.0
    expected = np.polyval([1.0, 2.0, 3.0], x)
    assert np.allclose(result, expected)
