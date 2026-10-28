# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

"""
Maths functions for ``Parameter`` and ``DescriptorNumber`` objects.

Each function evaluates the value with Scipp, which also checks the
unit, and returns a new object with the propagated variance. If any
argument is a ``Parameter``, the result is a ``Parameter`` whose bounds
are the range the function takes while the argument stays within its
own bounds. Otherwise the result is a ``DescriptorNumber`` without
bounds. The result is always the base class, also for a subclass input.

```python
import easyscience as es

amplitude = es.Parameter(
    2.0, display_name='amplitude', variance=0.01, min=0.0, max=5.0
)
phase = es.Parameter(
    30.0,
    display_name='phase',
    unit='deg',
    variance=1.0,
    min=0.0,
    max=90.0,
)

print(es.math.sin(phase))
# <Parameter 'sin(phase)': 0.5000 ± 0.0151, bounds=[0.0:1.0]>
print(es.math.sqrt(amplitude))
# <Parameter 'sqrt(amplitude)': 1.4142 ± 0.0354, bounds=[0.0:2.23606797749979]>
```

A value outside the domain of a function, or a result that is not
finite, raises ``ValueError``. An argument that is not a ``Parameter``
or a ``DescriptorNumber`` raises ``TypeError``.

Two limitations give wrong numbers without raising an error:

- The variance is propagated to first order and assumes uncorrelated
  inputs. A ``Parameter`` stores no covariance, so a function of two
  correlated fit parameters can have a badly wrong variance.
- A result is a snapshot of its inputs and does not follow later
  changes. Inside a model, compute it in ``__call__`` so that it is
  recomputed on every fit evaluation.
"""

import math
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from typing import overload

import numpy as np
import scipp as sc

from easyscience.variable.descriptor_number import DescriptorNumber
from easyscience.variable.parameter import Parameter

# A closed interval ``(lo, hi)`` of an argument, in the unit the bounds strategy works in.
_Interval = tuple[float, float]
_BoundsStrategy = Callable[..., tuple[float, float]]

# tan: closest distance (rad) to an asymptote that is accepted when the value has no variance.
_TAN_ASYMPTOTE_TOLERANCE = 1e-7
# tan: a bound this close (in units of pi) to an asymptote is on it; catches 90 deg after rounding.
_TAN_EDGE_TOLERANCE = 1e-12

# sinc: two consecutive extrema hold the largest maximum and deepest minimum of an interval, and
# the root just below ``lo`` may be filtered out, so four roots are refined.
_SINC_ROOT_COUNT = 4
# Newton's method needs about 4 steps from the asymptotic first guess to reach machine precision.
_SINC_NEWTON_STEPS = 8
# Beyond this the lobes of sinc are below 1e-15 and the lobe index overflows numpy integers.
_SINC_NEGLIGIBLE_LOBES_FROM = 1e15

# Twice the relative tolerance (1e-9) at which ``Parameter`` rejects ``min`` and ``max`` as equal.
_COLLAPSE_PAD = 2e-9
_COLLAPSE_PAD_ZERO = 1e-12

__all__ = [
    'acos',
    'acosh',
    'arccos',
    'arccosh',
    'arcsin',
    'arcsinh',
    'arctan',
    'arctan2',
    'arctanh',
    'asin',
    'asinh',
    'atan',
    'atan2',
    'atanh',
    'cos',
    'cosh',
    'erf',
    'erfc',
    'exp',
    'log',
    'log10',
    'sin',
    'sinc',
    'sinh',
    'sqrt',
    'tan',
    'tanh',
]


# --- Power, exponential and logarithmic functions ---


@overload
def exp(descriptor: Parameter) -> Parameter: ...


@overload
def exp(descriptor: DescriptorNumber) -> DescriptorNumber: ...


def exp(descriptor: DescriptorNumber) -> DescriptorNumber:
    r"""
    Exponential of a dimensionless input.

    $$
    f(x) = e^{x}
    $$

    The value overflows for $x$ above about 709.8. The variance grows
    like $e^{2x}$, so with a unit variance it overflows from about 355.

    Parameters
    ----------
    descriptor : DescriptorNumber
        Dimensionless input.

    Returns
    -------
    DescriptorNumber
        ``exp(descriptor)``, a ``Parameter`` if ``descriptor`` is one.

    Raises
    ------
    UnitError
        If ``descriptor`` is not dimensionless.
    ValueError
        If the value or the variance of the result overflows.

    Examples
    --------
    ```python
    import easyscience as es

    x = es.Parameter(1.0, display_name='x', variance=0.01, min=0.0, max=2.0)
    print(es.math.exp(x))
    # <Parameter 'exp(x)': 2.7183 ± 0.2718, bounds=[1.0:7.38905609893065]>
    ```
    """  # noqa: DOC502 -- raised in _apply
    return _apply(_EXP, descriptor)


@overload
def log(descriptor: Parameter) -> Parameter: ...


@overload
def log(descriptor: DescriptorNumber) -> DescriptorNumber: ...


def log(descriptor: DescriptorNumber) -> DescriptorNumber:
    r"""
    Natural logarithm of a positive, dimensionless input.

    $$
    f(x) = \ln x, \quad x > 0
    $$

    Bounds below zero are clipped to the domain, so bounds ``[-1, 5]``
    give result bounds ``[-inf, ln 5]``.

    Parameters
    ----------
    descriptor : DescriptorNumber
        Dimensionless input with a positive value.

    Returns
    -------
    DescriptorNumber
        ``log(descriptor)``, a ``Parameter`` if ``descriptor`` is one.

    Raises
    ------
    UnitError
        If ``descriptor`` is not dimensionless.
    ValueError
        If the value of ``descriptor`` is not positive.

    Examples
    --------
    ```python
    import easyscience as es

    x = es.Parameter(
        10.0, display_name='x', variance=0.01, min=1.0, max=100.0
    )
    print(es.math.log(x))
    # <Parameter 'log(x)': 2.3026 ± 0.0100, bounds=[0.0:4.605170185988092]>
    ```
    """  # noqa: DOC502 -- raised in _apply
    return _apply(_LOG, descriptor)


@overload
def log10(descriptor: Parameter) -> Parameter: ...


@overload
def log10(descriptor: DescriptorNumber) -> DescriptorNumber: ...


def log10(descriptor: DescriptorNumber) -> DescriptorNumber:
    r"""
    Base-10 logarithm of a positive, dimensionless input.

    $$
    f(x) = \log_{10} x, \quad x > 0
    $$

    Bounds below zero are clipped to the domain.

    Parameters
    ----------
    descriptor : DescriptorNumber
        Dimensionless input with a positive value.

    Returns
    -------
    DescriptorNumber
        ``log10(descriptor)``, a ``Parameter`` if ``descriptor`` is one.

    Raises
    ------
    UnitError
        If ``descriptor`` is not dimensionless.
    ValueError
        If the value of ``descriptor`` is not positive.

    Examples
    --------
    ```python
    import easyscience as es

    x = es.Parameter(
        100.0, display_name='x', variance=1.0, min=10.0, max=1000.0
    )
    print(es.math.log10(x))
    # <Parameter 'log10(x)': 2.0000 ± 0.0043, bounds=[1.0:3.0]>
    ```
    """  # noqa: DOC502 -- raised in _apply
    return _apply(_LOG10, descriptor)


@overload
def sqrt(descriptor: Parameter) -> Parameter: ...


@overload
def sqrt(descriptor: DescriptorNumber) -> DescriptorNumber: ...


def sqrt(descriptor: DescriptorNumber) -> DescriptorNumber:
    r"""
    Square root of a non-negative input.

    $$
    f(x) = \sqrt{x}, \quad x \ge 0
    $$

    The unit is the square root of the input unit, so ``m**2`` gives
    ``m``. At $x = 0$ the derivative is infinite, so a non-zero
    variance there raises ``ValueError``. Bounds below zero are clipped
    to the domain.

    Parameters
    ----------
    descriptor : DescriptorNumber
        Input that is dimensionless or has a squared unit, with a
        non-negative value.

    Returns
    -------
    DescriptorNumber
        ``sqrt(descriptor)``, a ``Parameter`` if ``descriptor`` is one.

    Raises
    ------
    UnitError
        If the unit of ``descriptor`` has no square root, such as ``m``.
    ValueError
        If the value of ``descriptor`` is negative, or the result is not finite.

    Examples
    --------
    ```python
    import easyscience as es

    area = es.Parameter(
        9.0,
        display_name='area',
        unit='m**2',
        variance=0.01,
        min=4.0,
        max=16.0,
    )
    print(es.math.sqrt(area))
    # <Parameter 'sqrt(area)': 3.0000 ± 0.0167 m, bounds=[2.0:4.0]>
    ```
    """  # noqa: DOC502 -- raised in _apply
    return _apply(_SQRT, descriptor)


# --- Special functions ---


@overload
def erf(descriptor: Parameter) -> Parameter: ...


@overload
def erf(descriptor: DescriptorNumber) -> DescriptorNumber: ...


def erf(descriptor: DescriptorNumber) -> DescriptorNumber:
    r"""
    Error function of a dimensionless input.

    $$
    \operatorname{erf}(x) = \frac{2}{\sqrt{\pi}} \int_0^x e^{-t^2}\,dt
    $$

    Scipp cannot propagate a variance through ``erf``, so an input with
    a non-zero variance raises Scipp's ``VariancesError``.

    Parameters
    ----------
    descriptor : DescriptorNumber
        Dimensionless input.

    Returns
    -------
    DescriptorNumber
        ``erf(descriptor)``, a ``Parameter`` if ``descriptor`` is one.

    Raises
    ------
    UnitError
        If ``descriptor`` is not dimensionless.
    VariancesError
        If ``descriptor`` has a non-zero variance.

    Examples
    --------
    ```python
    import easyscience as es

    x = es.Parameter(0.5, display_name='x', min=0.0, max=2.0)
    print(es.math.erf(x))
    # <Parameter 'erf(x)': 0.5205, bounds=[0.0:0.9953222650189527]>
    ```
    """  # noqa: DOC502 -- raised in _apply
    return _apply(_ERF, descriptor)


@overload
def erfc(descriptor: Parameter) -> Parameter: ...


@overload
def erfc(descriptor: DescriptorNumber) -> DescriptorNumber: ...


def erfc(descriptor: DescriptorNumber) -> DescriptorNumber:
    r"""
    Complementary error function of a dimensionless input.

    $$
    \operatorname{erfc}(x) = 1 - \operatorname{erf}(x)
    $$

    Scipp cannot propagate a variance through ``erfc``, so an input with
    a non-zero variance raises Scipp's ``VariancesError``.

    Parameters
    ----------
    descriptor : DescriptorNumber
        Dimensionless input.

    Returns
    -------
    DescriptorNumber
        ``erfc(descriptor)``, a ``Parameter`` if ``descriptor`` is one.

    Raises
    ------
    UnitError
        If ``descriptor`` is not dimensionless.
    VariancesError
        If ``descriptor`` has a non-zero variance.

    Examples
    --------
    ```python
    import easyscience as es

    x = es.Parameter(0.5, display_name='x', min=0.0, max=2.0)
    print(es.math.erfc(x))
    # <Parameter 'erfc(x)': 0.4795, bounds=[0.004677734981047266:1.0]>
    ```
    """  # noqa: DOC502 -- raised in _apply
    return _apply(_ERFC, descriptor)


# --- Trigonometric functions ---


@overload
def sin(descriptor: Parameter) -> Parameter: ...


@overload
def sin(descriptor: DescriptorNumber) -> DescriptorNumber: ...


def sin(descriptor: DescriptorNumber) -> DescriptorNumber:
    """
    Sine of an angle in ``rad`` or ``deg``.

    The result is dimensionless. Its bounds are the exact range of sine
    over the bounds of ``descriptor``, including any maximum or minimum
    inside them.

    Parameters
    ----------
    descriptor : DescriptorNumber
        Angle, with unit ``rad`` or ``deg``.

    Returns
    -------
    DescriptorNumber
        ``sin(descriptor)``, a ``Parameter`` if ``descriptor`` is one.

    Raises
    ------
    UnitError
        If ``descriptor`` is not an angle.

    Examples
    --------
    ```python
    import easyscience as es

    angle = es.Parameter(
        30.0,
        display_name='angle',
        unit='deg',
        variance=1.0,
        min=0.0,
        max=90.0,
    )
    print(es.math.sin(angle))
    # <Parameter 'sin(angle)': 0.5000 ± 0.0151, bounds=[0.0:1.0]>
    ```
    """  # noqa: DOC502 -- raised in _apply
    return _apply(_SIN, descriptor)


@overload
def cos(descriptor: Parameter) -> Parameter: ...


@overload
def cos(descriptor: DescriptorNumber) -> DescriptorNumber: ...


def cos(descriptor: DescriptorNumber) -> DescriptorNumber:
    """
    Cosine of an angle in ``rad`` or ``deg``.

    The result is dimensionless. Its bounds are the exact range of
    cosine over the bounds of ``descriptor``, including any maximum or
    minimum inside them.

    Parameters
    ----------
    descriptor : DescriptorNumber
        Angle, with unit ``rad`` or ``deg``.

    Returns
    -------
    DescriptorNumber
        ``cos(descriptor)``, a ``Parameter`` if ``descriptor`` is one.

    Raises
    ------
    UnitError
        If ``descriptor`` is not an angle.

    Examples
    --------
    ```python
    import easyscience as es

    angle = es.Parameter(
        60.0,
        display_name='angle',
        unit='deg',
        variance=1.0,
        min=0.0,
        max=180.0,
    )
    print(es.math.cos(angle))
    # <Parameter 'cos(angle)': 0.5000 ± 0.0151, bounds=[-1.0:1.0]>
    ```
    """  # noqa: DOC502 -- raised in _apply
    return _apply(_COS, descriptor)


@overload
def tan(descriptor: Parameter) -> Parameter: ...


@overload
def tan(descriptor: DescriptorNumber) -> DescriptorNumber: ...


def tan(descriptor: DescriptorNumber) -> DescriptorNumber:
    r"""
    Tangent of an angle in ``rad`` or ``deg``.

    The value must keep clear of the asymptotes at
    $\frac{\pi}{2} + n\pi$: by one standard deviation of ``descriptor``,
    and by at least 1e-7 rad. The bounds are not restricted. If they
    contain an asymptote, the result bounds are ``(-inf, inf)``. A bound
    exactly on an asymptote makes only that side infinite, so ``[0, 90]``
    deg gives ``[0, inf)``.

    Parameters
    ----------
    descriptor : DescriptorNumber
        Angle, with unit ``rad`` or ``deg``.

    Returns
    -------
    DescriptorNumber
        ``tan(descriptor)``, a ``Parameter`` if ``descriptor`` is one.

    Raises
    ------
    UnitError
        If ``descriptor`` is not an angle.
    ValueError
        If the value of ``descriptor`` is too close to an asymptote.

    Examples
    --------
    ```python
    import easyscience as es

    angle = es.Parameter(
        45.0,
        display_name='angle',
        unit='deg',
        variance=1.0,
        min=0.0,
        max=60.0,
    )
    print(es.math.tan(angle))
    # <Parameter 'tan(angle)': 1.0000 ± 0.0349, bounds=[0.0:1.7320508075688767]>
    ```
    """  # noqa: DOC502 -- raised in _apply and _tan_guard
    return _apply(_TAN, descriptor)


@overload
def arcsin(descriptor: Parameter, *, unit: str = ...) -> Parameter: ...


@overload
def arcsin(descriptor: DescriptorNumber, *, unit: str = ...) -> DescriptorNumber: ...


def arcsin(descriptor: DescriptorNumber, *, unit: str = 'rad') -> DescriptorNumber:
    r"""
    Inverse sine of a dimensionless input in ``[-1, 1]``.

    The angle lies in $[-\frac{\pi}{2}, \frac{\pi}{2}]$. At
    $x = \pm 1$ the derivative is infinite, so a non-zero variance
    there raises ``ValueError``. Bounds outside $[-1, 1]$ are clipped
    to the domain.

    Parameters
    ----------
    descriptor : DescriptorNumber
        Dimensionless input with a value in ``[-1, 1]``.
    unit : str, default='rad'
        Unit of the angle, ``'rad'`` or ``'deg'``.

    Returns
    -------
    DescriptorNumber
        ``arcsin(descriptor)`` in ``unit``, a ``Parameter`` if ``descriptor`` is one.

    Raises
    ------
    UnitError
        If ``descriptor`` is not dimensionless, or ``unit`` is not an angle unit.
    ValueError
        If the value of ``descriptor`` is outside ``[-1, 1]``, or the result is
        not finite.

    Examples
    --------
    ```python
    import easyscience as es

    x = es.Parameter(
        0.5, display_name='x', variance=0.0001, min=0.0, max=1.0
    )
    print(es.math.arcsin(x, unit='deg'))
    # <Parameter 'arcsin(x)': 30.0000 ± 0.6616 deg, bounds=[0.0:90.0]>
    ```
    """  # noqa: DOC502 -- raised in _apply and _angle_in
    return _angle_in(_apply(_ARCSIN, descriptor), unit)


@overload
def arccos(descriptor: Parameter, *, unit: str = ...) -> Parameter: ...


@overload
def arccos(descriptor: DescriptorNumber, *, unit: str = ...) -> DescriptorNumber: ...


def arccos(descriptor: DescriptorNumber, *, unit: str = 'rad') -> DescriptorNumber:
    r"""
    Inverse cosine of a dimensionless input in ``[-1, 1]``.

    The angle lies in $[0, \pi]$. At $x = \pm 1$ the derivative is
    infinite, so a non-zero variance there raises ``ValueError``. Bounds
    outside $[-1, 1]$ are clipped to the domain.

    Parameters
    ----------
    descriptor : DescriptorNumber
        Dimensionless input with a value in ``[-1, 1]``.
    unit : str, default='rad'
        Unit of the angle, ``'rad'`` or ``'deg'``.

    Returns
    -------
    DescriptorNumber
        ``arccos(descriptor)`` in ``unit``, a ``Parameter`` if ``descriptor`` is one.

    Raises
    ------
    UnitError
        If ``descriptor`` is not dimensionless, or ``unit`` is not an angle unit.
    ValueError
        If the value of ``descriptor`` is outside ``[-1, 1]``, or the result is
        not finite.

    Examples
    --------
    ```python
    import easyscience as es

    x = es.Parameter(
        0.5, display_name='x', variance=0.0001, min=0.0, max=1.0
    )
    print(es.math.arccos(x, unit='deg'))
    # <Parameter 'arccos(x)': 60.0000 ± 0.6616 deg, bounds=[0.0:90.0]>
    ```
    """  # noqa: DOC502 -- raised in _apply and _angle_in
    return _angle_in(_apply(_ARCCOS, descriptor), unit)


@overload
def arctan(descriptor: Parameter, *, unit: str = ...) -> Parameter: ...


@overload
def arctan(descriptor: DescriptorNumber, *, unit: str = ...) -> DescriptorNumber: ...


def arctan(descriptor: DescriptorNumber, *, unit: str = 'rad') -> DescriptorNumber:
    r"""
    Inverse tangent of a dimensionless input.

    The angle lies in $(-\frac{\pi}{2}, \frac{\pi}{2})$. To get the
    full-circle angle of a point, use ``arctan2``.

    Parameters
    ----------
    descriptor : DescriptorNumber
        Dimensionless input.
    unit : str, default='rad'
        Unit of the angle, ``'rad'`` or ``'deg'``.

    Returns
    -------
    DescriptorNumber
        ``arctan(descriptor)`` in ``unit``, a ``Parameter`` if ``descriptor`` is one.

    Raises
    ------
    UnitError
        If ``descriptor`` is not dimensionless, or ``unit`` is not an angle unit.

    Examples
    --------
    ```python
    import easyscience as es

    x = es.Parameter(
        1.0, display_name='x', variance=0.01, min=0.0, max=10.0
    )
    print(es.math.arctan(x, unit='deg'))
    # <Parameter 'arctan(x)': 45.0000 ± 2.8648 deg, bounds=[0.0:84.28940686250037]>
    ```
    """  # noqa: DOC502 -- raised in _apply and _angle_in
    return _angle_in(_apply(_ARCTAN, descriptor), unit)


@overload
def arctan2(y: Parameter, x: DescriptorNumber, *, unit: str = ...) -> Parameter: ...


@overload
def arctan2(y: DescriptorNumber, x: Parameter, *, unit: str = ...) -> Parameter: ...


@overload
def arctan2(y: DescriptorNumber, x: DescriptorNumber, *, unit: str = ...) -> DescriptorNumber: ...


def arctan2(y: DescriptorNumber, x: DescriptorNumber, *, unit: str = 'rad') -> DescriptorNumber:
    r"""
    Angle of the point ``(x, y)``, using both signs to find the quadrant.

    The angle lies in $[-\pi, \pi]$. Scipp cannot propagate a variance
    through ``atan2``, so an argument with a non-zero variance raises
    Scipp's ``VariancesError``.

    The bounds are the range of the angle over the box spanned by the
    bounds of ``y`` and ``x``. If the box touches the negative ``x``
    axis, where the angle jumps from $\pi$ to $-\pi$, the bounds are
    $[-\pi, \pi]$.

    Parameters
    ----------
    y : DescriptorNumber
        Cartesian y-coordinate.
    x : DescriptorNumber
        Cartesian x-coordinate, with the same unit as ``y``.
    unit : str, default='rad'
        Unit of the angle, ``'rad'`` or ``'deg'``.

    Returns
    -------
    DescriptorNumber
        The angle in ``unit``, a ``Parameter`` if ``y`` or ``x`` is one.

    Raises
    ------
    UnitError
        If ``y`` and ``x`` have different units, or ``unit`` is not an
        angle unit.
    VariancesError
        If ``y`` or ``x`` has a non-zero variance.

    Examples
    --------
    ```python
    import easyscience as es

    y = es.Parameter(1.0, display_name='y', unit='m', min=0.5, max=2.0)
    x = es.Parameter(1.0, display_name='x', unit='m', min=1.0, max=3.0)
    print(es.math.arctan2(y, x, unit='deg'))
    # <Parameter 'arctan2(y, x)': 45.0000 deg, bounds=[9.462322208025617:63.43494882292201]>
    ```
    """  # noqa: DOC502 -- raised in _apply and _angle_in
    return _angle_in(_apply(_ARCTAN2, y, x), unit)


@overload
def sinc(descriptor: Parameter) -> Parameter: ...


@overload
def sinc(descriptor: DescriptorNumber) -> DescriptorNumber: ...


def sinc(descriptor: DescriptorNumber) -> DescriptorNumber:
    r"""
    Unnormalised sinc of a dimensionless input or an angle in ``rad``.

    $$
    \operatorname{sinc}(x) = \frac{\sin x}{x}, \quad
    \operatorname{sinc}(0) = 1
    $$

    This is the convention of Scipp and of physics. NumPy's ``np.sinc``
    is the normalised $\frac{\sin \pi x}{\pi x}$.

    Parameters
    ----------
    descriptor : DescriptorNumber
        Input that is dimensionless or in ``rad``.

    Returns
    -------
    DescriptorNumber
        ``sinc(descriptor)``, dimensionless, a ``Parameter`` if ``descriptor`` is one.

    Raises
    ------
    UnitError
        If the unit of ``descriptor`` is neither dimensionless nor ``rad``.

    Examples
    --------
    ```python
    import easyscience as es

    x = es.Parameter(1.0, display_name='x', variance=0.01, min=0.5, max=2.0)
    print(es.math.sinc(x))
    # <Parameter 'sinc(x)': 0.8415 ± 0.0301, bounds=[0.45464871341284085:0.958851077208406]>
    ```
    """  # noqa: DOC502 -- raised in _apply
    return _apply(_SINC, descriptor)


# --- Hyperbolic functions ---


@overload
def sinh(descriptor: Parameter) -> Parameter: ...


@overload
def sinh(descriptor: DescriptorNumber) -> DescriptorNumber: ...


def sinh(descriptor: DescriptorNumber) -> DescriptorNumber:
    r"""
    Hyperbolic sine of a dimensionless input.

    $$
    \sinh x = \frac{e^{x} - e^{-x}}{2}
    $$

    Parameters
    ----------
    descriptor : DescriptorNumber
        Dimensionless input.

    Returns
    -------
    DescriptorNumber
        ``sinh(descriptor)``, a ``Parameter`` if ``descriptor`` is one.

    Raises
    ------
    UnitError
        If ``descriptor`` is not dimensionless.
    ValueError
        If the value or the variance of the result overflows.

    Examples
    --------
    ```python
    import easyscience as es

    x = es.Parameter(1.0, display_name='x', variance=0.01, min=0.0, max=2.0)
    print(es.math.sinh(x))
    # <Parameter 'sinh(x)': 1.1752 ± 0.1543, bounds=[0.0:3.6268604078470186]>
    ```
    """  # noqa: DOC502 -- raised in _apply
    return _apply(_SINH, descriptor)


@overload
def cosh(descriptor: Parameter) -> Parameter: ...


@overload
def cosh(descriptor: DescriptorNumber) -> DescriptorNumber: ...


def cosh(descriptor: DescriptorNumber) -> DescriptorNumber:
    r"""
    Hyperbolic cosine of a dimensionless input.

    $$
    \cosh x = \frac{e^{x} + e^{-x}}{2}
    $$

    The minimum is 1 at $x = 0$, so bounds that include 0 give a lower
    result bound of 1.

    Parameters
    ----------
    descriptor : DescriptorNumber
        Dimensionless input.

    Returns
    -------
    DescriptorNumber
        ``cosh(descriptor)``, a ``Parameter`` if ``descriptor`` is one.

    Raises
    ------
    UnitError
        If ``descriptor`` is not dimensionless.
    ValueError
        If the value or the variance of the result overflows.

    Examples
    --------
    ```python
    import easyscience as es

    x = es.Parameter(
        1.0, display_name='x', variance=0.01, min=-1.0, max=2.0
    )
    print(es.math.cosh(x))
    # <Parameter 'cosh(x)': 1.5431 ± 0.1175, bounds=[1.0:3.7621956910836314]>
    ```
    """  # noqa: DOC502 -- raised in _apply
    return _apply(_COSH, descriptor)


@overload
def tanh(descriptor: Parameter) -> Parameter: ...


@overload
def tanh(descriptor: DescriptorNumber) -> DescriptorNumber: ...


def tanh(descriptor: DescriptorNumber) -> DescriptorNumber:
    r"""
    Hyperbolic tangent of a dimensionless input.

    $$
    \tanh x = \frac{\sinh x}{\cosh x}
    $$

    Parameters
    ----------
    descriptor : DescriptorNumber
        Dimensionless input.

    Returns
    -------
    DescriptorNumber
        ``tanh(descriptor)``, a ``Parameter`` if ``descriptor`` is one.

    Raises
    ------
    UnitError
        If ``descriptor`` is not dimensionless.

    Examples
    --------
    ```python
    import easyscience as es

    x = es.Parameter(1.0, display_name='x', variance=0.01, min=0.0, max=2.0)
    print(es.math.tanh(x))
    # <Parameter 'tanh(x)': 0.7616 ± 0.0420, bounds=[0.0:0.9640275800758169]>
    ```
    """  # noqa: DOC502 -- raised in _apply
    return _apply(_TANH, descriptor)


@overload
def arcsinh(descriptor: Parameter) -> Parameter: ...


@overload
def arcsinh(descriptor: DescriptorNumber) -> DescriptorNumber: ...


def arcsinh(descriptor: DescriptorNumber) -> DescriptorNumber:
    r"""
    Inverse hyperbolic sine of a dimensionless input.

    $$
    \operatorname{arcsinh} x = \ln\left(x + \sqrt{x^2 + 1}\right)
    $$

    Parameters
    ----------
    descriptor : DescriptorNumber
        Dimensionless input.

    Returns
    -------
    DescriptorNumber
        ``arcsinh(descriptor)``, a ``Parameter`` if ``descriptor`` is one.

    Raises
    ------
    UnitError
        If ``descriptor`` is not dimensionless.

    Examples
    --------
    ```python
    import easyscience as es

    x = es.Parameter(1.0, display_name='x', variance=0.01, min=0.0, max=2.0)
    print(es.math.arcsinh(x))
    # <Parameter 'arcsinh(x)': 0.8814 ± 0.0707, bounds=[0.0:1.4436354751788103]>
    ```
    """  # noqa: DOC502 -- raised in _apply
    return _apply(_ARCSINH, descriptor)


@overload
def arccosh(descriptor: Parameter) -> Parameter: ...


@overload
def arccosh(descriptor: DescriptorNumber) -> DescriptorNumber: ...


def arccosh(descriptor: DescriptorNumber) -> DescriptorNumber:
    r"""
    Inverse hyperbolic cosine of a dimensionless input of at least 1.

    $$
    \operatorname{arccosh} x = \ln\left(x + \sqrt{x^2 - 1}\right),
    \quad x \ge 1
    $$

    At $x = 1$ the derivative is infinite, so a non-zero variance
    there raises ``ValueError``. Bounds below 1 are clipped to the
    domain.

    Parameters
    ----------
    descriptor : DescriptorNumber
        Dimensionless input with a value of at least 1.

    Returns
    -------
    DescriptorNumber
        ``arccosh(descriptor)``, a ``Parameter`` if ``descriptor`` is one.

    Raises
    ------
    UnitError
        If ``descriptor`` is not dimensionless.
    ValueError
        If the value of ``descriptor`` is below 1, or the result is not finite.

    Examples
    --------
    ```python
    import easyscience as es

    x = es.Parameter(2.0, display_name='x', variance=0.01, min=1.0, max=3.0)
    print(es.math.arccosh(x))
    # <Parameter 'arccosh(x)': 1.3170 ± 0.0577, bounds=[0.0:1.762747174039086]>
    ```
    """  # noqa: DOC502 -- raised in _apply
    return _apply(_ARCCOSH, descriptor)


@overload
def arctanh(descriptor: Parameter) -> Parameter: ...


@overload
def arctanh(descriptor: DescriptorNumber) -> DescriptorNumber: ...


def arctanh(descriptor: DescriptorNumber) -> DescriptorNumber:
    r"""
    Inverse hyperbolic tangent of a dimensionless input in ``(-1, 1)``.

    $$
    \operatorname{arctanh} x = \frac{1}{2} \ln\frac{1 + x}{1 - x},
    \quad -1 < x < 1
    $$

    Bounds outside $(-1, 1)$ are clipped to the domain and give infinite
    result bounds.

    Parameters
    ----------
    descriptor : DescriptorNumber
        Dimensionless input with a value strictly between -1 and 1.

    Returns
    -------
    DescriptorNumber
        ``arctanh(descriptor)``, a ``Parameter`` if ``descriptor`` is one.

    Raises
    ------
    UnitError
        If ``descriptor`` is not dimensionless.
    ValueError
        If the value of ``descriptor`` is not strictly between -1 and 1.

    Examples
    --------
    ```python
    import easyscience as es

    x = es.Parameter(
        0.5, display_name='x', variance=0.0001, min=0.0, max=0.9
    )
    print(es.math.arctanh(x))
    # <Parameter 'arctanh(x)': 0.5493 ± 0.0133, bounds=[0.0:1.4722194895832204]>
    ```
    """  # noqa: DOC502 -- raised in _apply
    return _apply(_ARCTANH, descriptor)


# --- Aliases ---
# The C / Scipp spellings of the inverse functions. They are the same function objects, so
# they share the docstring, and the parameters they return are named after the canonical
# function (``asin(x)`` returns a parameter called ``arcsin(x)``).

asin = arcsin
acos = arccos
atan = arctan
atan2 = arctan2
asinh = arcsinh
acosh = arccosh
atanh = arctanh


# --- Specification of a maths operation ---


@dataclass(frozen=True)
class _Domain:
    """
    The set of argument values a function accepts: an interval, open or
    closed at each end.
    """

    lo: float = -np.inf
    hi: float = np.inf
    open_lo: bool = False
    open_hi: bool = False

    def contains(self, value: float) -> bool:
        above = value > self.lo if self.open_lo else value >= self.lo
        below = value < self.hi if self.open_hi else value <= self.hi
        return above and below

    def clip(self, lo: float, hi: float) -> _Interval:
        """
        Restrict ``[lo, hi]`` to the domain (open ends clip to the edge:
        the limit).
        """
        return max(lo, self.lo), min(hi, self.hi)

    def __str__(self) -> str:
        left = '(' if self.open_lo else '['
        right = ')' if self.open_hi else ']'
        return f'{left}{self.lo}, {self.hi}{right}'


@dataclass(frozen=True)
class _MathOp:
    """
    Everything that makes one maths function different from another.

    Attributes
    ----------
    name : str
        Name used in error messages and in the name of the resulting
        ``Parameter``.
    sc_func : Callable
        The Scipp function (it validates units and propagates variance,
        if it can).
    bounds : _BoundsStrategy
        Maps one ``(lo, hi)`` interval per argument to the ``(min,
        max)`` of the result.
    domain : _Domain, default=_Domain()
        Accepted argument values. Applies to every argument.
    native_unit : str | None, default=None
        If set, bounds are converted to this unit before ``bounds`` runs
        (``'rad'`` for the trigonometric functions, whose numpy versions
        assume radians).
    guard : Callable[..., None] | None, default=None
        Extra check of the arguments' values, ``guard(*params)``,
        raising ``ValueError`` where the variance would explode (tan
        asymptotes).
    """

    name: str
    sc_func: Callable
    bounds: _BoundsStrategy
    domain: _Domain = _Domain()
    native_unit: str | None = None
    guard: Callable[..., None] | None = None


# --- The dispatcher ---


# NOTE(): Every result is an independent, non-fixed ``Parameter`` that is a snapshot of its inputs
# (as are the results of ``Parameter.__mul__`` and friends): it does not follow later changes and,
# if handed to a ``Fitter``, would be varied as a free parameter of its own. Whether results should
# be ``fixed=True``, or linked to their inputs (compare ``Parameter.from_dependency``), is for the
# lead developer to decide.
# TODO(): Cost. A chain of five es.math / Parameter operations (a Gaussian width derived from a
# FWHM inside a model's __call__) took about 1.3 ms per evaluation, constant over thousands of
# evaluations and without leaking. That is fine for ordinary fits, but it has not been profiled
# where the time goes: profile before using es.math in hot loops (tens of thousands of
# evaluations), and consider a cheaper path if it matters.
def _apply(op: _MathOp, *params: DescriptorNumber) -> DescriptorNumber:
    """
    Evaluate ``op`` on ``params``: validate, call Scipp, derive bounds,
    repack.

    Scipp validates the units, so a wrong unit raises its ``UnitError``
    before any of the checks below.

    Parameters
    ----------
    op : _MathOp
        Specification of the function.
    *params : DescriptorNumber
        The arguments (a ``Parameter`` is a ``DescriptorNumber``).

    Returns
    -------
    DescriptorNumber
        A new ``Parameter`` named ``'<op>(<arg names>)'`` if any
        argument is a ``Parameter``, otherwise a new
        ``DescriptorNumber`` with that name.

    Raises
    ------
    TypeError
        If an argument is not a ``Parameter`` or ``DescriptorNumber``.
    ValueError
        If an argument's value is outside the domain, or the result is
        not finite.
    """
    for param in params:
        if not isinstance(param, DescriptorNumber):
            raise TypeError(
                'EasyScience math functions currently only support `Parameter` and '
                '`DescriptorNumber` objects. Raw numbers and arrays are not yet supported. '
                f'Found: {type(param)}'
            )

    # 1. Scipp first: it owns the unit rules, so a unit error is reported before anything else.
    sc_args = [_to_scipp_scalar(param) for param in params]
    sc_result = op.sc_func(*sc_args)

    # 2. Values are validated strictly: a bad value would break a fit loop.
    for param in params:
        if not op.domain.contains(param.value):
            raise ValueError(
                f"The value of '{param.display_name}' ({param.value}) is outside the domain "
                f'{op.domain} of {op.name}().'
            )
    if op.guard is not None:
        op.guard(*params)

    label = ', '.join(param.display_name for param in params)
    if not _is_finite(sc_result.value) or not _is_finite(sc_result.variance):
        raise ValueError(
            f'{op.name}({label}) is not finite: value={sc_result.value}, '
            f'variance={sc_result.variance}. Check the value and variance of the argument(s).'
        )

    # A plain DescriptorNumber has no bounds, so neither has a result made only from those.
    if not any(isinstance(param, Parameter) for param in params):
        return DescriptorNumber.from_scipp(
            display_name=f'{op.name}({label})', full_value=sc_result
        )

    # 3. Bounds are permissive: clip to the domain, convert, and let the strategy decide.
    intervals = [_native_interval(op, param) for param in params]
    with np.errstate(all='ignore'):
        new_min, new_max = op.bounds(*intervals)
    # Guard against round-off at an extremum: the value is always inside its own bounds.
    new_min, new_max = min(new_min, sc_result.value), max(new_max, sc_result.value)
    # Parameter rejects (nearly) identical bounds, so bounds that collapsed are padded.
    new_min, new_max = _pad_if_collapsed(new_min, new_max, sc_result.value)

    return Parameter.from_scipp(
        display_name=f'{op.name}({label})',
        full_value=sc_result,
        min=new_min,
        max=new_max,
    )


# TODO(): ``rtol=1e-9`` below mirrors the literal tolerance in the min/max setters of ``Parameter``,
# which is not a named constant. Expose it in parameter.py and import it here, so that the two
# cannot drift apart (if ``Parameter`` tightens its tolerance this padding would silently stop
# preventing the 'identical bounds' ValueError).
def _pad_if_collapsed(lo: float, hi: float, value: float) -> tuple[float, float]:
    """
    Widen bounds that ``Parameter`` would reject as identical,
    symmetrically around ``value``.

    Parameters
    ----------
    lo : float
        Lower bound.
    hi : float
        Upper bound.
    value : float
        The result value, which lies inside ``[lo, hi]``.

    Returns
    -------
    tuple[float, float]
        ``(lo, hi)`` unchanged, or padded by ``_COLLAPSE_PAD * |value|``
        (``_COLLAPSE_PAD_ZERO`` if the value is 0) on each side if they
        are equal or within ``Parameter``'s tolerance.
    """
    if not math.isclose(lo, hi, rel_tol=1e-9, abs_tol=0.0):
        return lo, hi
    pad = abs(value) * _COLLAPSE_PAD or _COLLAPSE_PAD_ZERO
    return lo - pad, hi + pad


def _angle_in(result: DescriptorNumber, unit: str) -> DescriptorNumber:
    """
    Express an angle ``result`` (in radians, as Scipp returns it) in
    ``unit``.

    The value, the variance and the bounds are converted together by
    ``Parameter.convert_unit``.

    Parameters
    ----------
    result : DescriptorNumber
        An angle in radians. It is converted in place.
    unit : str
        Target unit, ``'rad'`` or ``'deg'``.

    Returns
    -------
    DescriptorNumber
        ``result``, in ``unit``.

    Raises
    ------
    UnitError
        If ``unit`` is not an angle unit.
    """  # noqa: DOC502 -- raised by Parameter.convert_unit
    if unit != result.unit:
        result.convert_unit(unit)
    return result


def _variance(param: DescriptorNumber) -> float:
    """
    Variance of a parameter; a missing (``None``) or zero variance
    counts as 0.0.
    """
    return float(param.variance) if param.variance else 0.0


def _to_scipp_scalar(param: DescriptorNumber) -> sc.Variable:
    """
    Convert a Parameter to a Scipp scalar; a zero or missing variance is
    dropped.
    """
    kwargs = {'value': float(param.value), 'unit': param.unit}
    variance = _variance(param)
    if variance > 0:
        kwargs['variance'] = variance
    return sc.scalar(**kwargs)


def _is_finite(value: float | None) -> bool:
    """
    Whether ``value`` is finite; a missing value (no variance) counts as
    fine.
    """
    return value is None or bool(np.isfinite(value))


@cache
def _native_factor(unit: str, native_unit: str | None) -> float:
    """
    Factor converting ``unit`` to ``native_unit`` (1.0 if none is
    needed), asked of Scipp once.
    """
    if native_unit is None or unit == native_unit:
        return 1.0
    return float(sc.scalar(1.0, unit=unit).to(unit=native_unit).value)


def _native_interval(op: _MathOp, param: DescriptorNumber) -> _Interval:
    """
    The parameter's bounds, clipped to the domain and in the unit the
    strategy expects.
    """
    if isinstance(param, Parameter):
        lo, hi = float(param.min), float(param.max)
    else:  # a plain DescriptorNumber has no bounds: it is the single point at its value
        lo = hi = float(param.value)
    lo, hi = op.domain.clip(lo, hi)
    if op.native_unit is None:
        return lo, hi
    factor = _native_factor(str(param.unit), op.native_unit)
    return lo * factor, hi * factor


# --- Bounds strategies ---
# Each takes one (lo, hi) interval per argument and returns the exact (min, max) of the
# function over that interval. They run inside ``np.errstate(all='ignore')``, so an edge
# such as log(0) = -inf is returned instead of warning.


def _monotonic(func: Callable) -> _BoundsStrategy:
    """
    Monotonic function (increasing or decreasing): the extremes sit at
    the endpoints.
    """

    def bounds(interval: _Interval) -> tuple[float, float]:
        lo, hi = interval
        at_lo, at_hi = float(func(lo)), float(func(hi))
        return min(at_lo, at_hi), max(at_lo, at_hi)

    return bounds


def _extrema(
    func: Callable, critical_points: Callable[[float, float], np.ndarray]
) -> _BoundsStrategy:
    """
    Non-monotonic function: the extremes sit at the endpoints or at
    critical points.

    ``critical_points(lo, hi)`` returns the points inside ``[lo, hi]``
    where the function may have a local extremum. ``nan`` candidates,
    such as ``sin(inf)``, are ignored.
    """

    def bounds(interval: _Interval) -> tuple[float, float]:
        lo, hi = interval
        candidates = np.concatenate(([lo, hi], critical_points(lo, hi)))
        values = np.asarray(func(candidates), dtype=float)
        return float(np.nanmin(values)), float(np.nanmax(values))

    return bounds


def _periodic_critical_points(offset: float) -> Callable[[float, float], np.ndarray]:
    """
    Critical points ``offset + n*pi`` (n an integer) of sin (``pi/2``)
    or cos (``0``).

    A whole period, or an infinite interval, holds a maximum and a
    minimum, so those two are returned without enumerating.
    """

    def points(lo: float, hi: float) -> np.ndarray:
        if not (np.isfinite(lo) and np.isfinite(hi)) or hi - lo >= 2 * np.pi:
            return np.array([offset, offset + np.pi])
        n = np.arange(np.ceil((lo - offset) / np.pi), np.floor((hi - offset) / np.pi) + 1)
        return offset + n * np.pi

    return points


def _cosh_critical_points(lo: float, hi: float) -> np.ndarray:
    """The single minimum of cosh, at 0."""
    return np.array([0.0]) if lo <= 0.0 <= hi else np.array([])


def _unnormalized_sinc(x) -> np.ndarray:
    """
    sin(x)/x, with sinc(0) = 1 and the limit sinc(±inf) = 0.

    ``np.sinc`` is the *normalised* sin(pi x)/(pi x), so the argument is
    scaled by 1/pi.
    """
    x = np.asarray(x, dtype=float)
    return np.where(np.isinf(x), 0.0, np.sinc(x / np.pi))


def _sinc_positive_extrema(lo: float, hi: float, count: int = _SINC_ROOT_COUNT) -> np.ndarray:
    """
    Stationary points of sinc on the positive axis inside ``[lo, hi]``,
    nearest to ``lo``.

    They are the positive roots of ``tan(x) = x``, one in each ``(k*pi,
    k*pi + pi/2)``. The heights of the lobes fall off like 1/x, so the
    largest maximum and the deepest minimum in the interval are among
    the first few roots at or after ``lo``.

    Beyond ``_SINC_NEGLIGIBLE_LOBES_FROM`` the lobes are negligible and
    none are returned.

    All ``count`` roots are refined at once with Newton's method on
    ``g(x) = x cos(x) - sin(x)``, ``g'(x) = -x sin(x)``, with the
    vectorised update ``x <- x - g(x) / g'(x)`` (no Python loop over the
    roots).
    """
    if hi <= 0.0 or lo > _SINC_NEGLIGIBLE_LOBES_FROM:
        return np.array([])
    first = max(1, int(np.floor(max(lo, 0.0) / np.pi)))
    k = np.arange(first, first + count)
    x = (k + 0.5) * np.pi
    x = x - 1.0 / x  # asymptotic first guess for the root of tan(x) = x
    for _ in range(_SINC_NEWTON_STEPS):
        x = x - (x * np.cos(x) - np.sin(x)) / (-x * np.sin(x))
    return x[(x >= lo) & (x <= hi)]


def _sinc_critical_points(lo: float, hi: float) -> np.ndarray:
    """
    Stationary points of sinc: 0 (the global maximum) and the roots of
    tan(x) = x on both sides.
    """
    points = [_sinc_positive_extrema(lo, hi), -_sinc_positive_extrema(-hi, -lo)]
    if lo <= 0.0 <= hi:
        points.append(np.array([0.0]))
    return np.concatenate(points)


def _tan_branch(position: float) -> tuple[float, bool]:
    """
    Branch of tan that a point lies on, and whether it sits exactly on
    an asymptote.

    Parameters
    ----------
    position : float
        ``(x - pi/2) / pi``, so that the asymptotes ``pi/2 + n*pi`` are
        the integers.

    Returns
    -------
    tuple[float, bool]
        The branch index (the asymptote's own index if the point sits on
        one) and whether the point sits on an asymptote.
    """
    nearest = float(np.round(position))
    on_asymptote = abs(position - nearest) <= _TAN_EDGE_TOLERANCE
    return (nearest if on_asymptote else float(np.floor(position))), on_asymptote


def _tan_bounds(interval: _Interval) -> tuple[float, float]:
    """
    Bounds of tan(x) for ``x`` in radians.

    tan is increasing between asymptotes (``pi/2 + n*pi``). An interval
    that contains an asymptote in its interior covers all real numbers.
    A bound exactly on an asymptote makes the result unbounded on that
    side only: ``[0, pi/2]`` gives ``[0, inf)``.
    """
    lo, hi = interval
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return -np.inf, np.inf
    branch_lo, lo_on_asymptote = _tan_branch((lo - np.pi / 2) / np.pi)
    branch_hi, hi_on_asymptote = _tan_branch((hi - np.pi / 2) / np.pi)
    if hi_on_asymptote:
        branch_hi -= 1  # an upper bound on an asymptote closes the branch below it
    if branch_lo != branch_hi:
        return -np.inf, np.inf
    lower = -np.inf if lo_on_asymptote else float(np.tan(lo))
    upper = np.inf if hi_on_asymptote else float(np.tan(hi))
    return lower, upper


def _std(param: DescriptorNumber) -> float:
    """Standard deviation of a parameter; 0 if it has no variance."""
    return math.sqrt(_variance(param))


# NOTE(): Design decision awaiting sign-off. The guards below reject a
# value that lies within one standard deviation of a tan asymptote, because first-order
# propagation is meaningless there. The price is that a legitimate fit result consistent with the
# asymptote cannot be turned into a derived quantity. Alternatives: only warn, or return a very
# large variance instead of raising.
def _tan_guard(param: DescriptorNumber) -> None:
    """
    The value must keep clear of a tan asymptote, where the variance
    would explode.

    The delta method is only meaningful if the asymptote lies more than
    one standard deviation away, so that distance (never less than
    ``_TAN_ASYMPTOTE_TOLERANCE``) is the limit.
    """
    factor = _native_factor(str(param.unit), 'rad')
    value = float(param.value) * factor
    margin = max(_TAN_ASYMPTOTE_TOLERANCE, _std(param) * factor)
    distance = abs(value % np.pi - np.pi / 2)
    if distance <= margin:
        raise ValueError(
            f"The value of '{param.display_name}' ({param.value} {param.unit}) is within "
            f'{margin:.3g} rad of a tan asymptote (pi/2 + n*pi); the propagated variance '
            f'would explode.'
        )


def _arctan2_bounds(y_interval: _Interval, x_interval: _Interval) -> tuple[float, float]:
    """
    Bounds of arctan2(y, x) over the box ``y_interval x x_interval``.

    The angle is a harmonic function, so away from the branch cut its
    extremes sit on the corners of the box. If the box touches the cut
    (``y = 0`` with ``x < 0``) the angle jumps between -pi and pi and
    the range is the full ``[-pi, pi]``.
    """
    (y_lo, y_hi), (x_lo, x_hi) = y_interval, x_interval
    if y_lo < 0.0 <= y_hi and x_lo < 0.0:
        return -np.pi, np.pi
    corners = [np.arctan2(y, x) for y in (y_lo, y_hi) for x in (x_lo, x_hi)]
    return float(min(corners)), float(max(corners))


# --- The specifications ---

_POSITIVE = _Domain(lo=0.0, open_lo=True)
_NON_NEGATIVE = _Domain(lo=0.0)
_AT_LEAST_ONE = _Domain(lo=1.0)
_CLOSED_UNIT_INTERVAL = _Domain(lo=-1.0, hi=1.0)
_OPEN_UNIT_INTERVAL = _Domain(lo=-1.0, hi=1.0, open_lo=True, open_hi=True)

_EXP = _MathOp('exp', sc.exp, _monotonic(np.exp))
_LOG = _MathOp('log', sc.log, _monotonic(np.log), domain=_POSITIVE)
_LOG10 = _MathOp('log10', sc.log10, _monotonic(np.log10), domain=_POSITIVE)
_SQRT = _MathOp('sqrt', sc.sqrt, _monotonic(np.sqrt), domain=_NON_NEGATIVE)
_ERF = _MathOp('erf', sc.erf, _monotonic(math.erf))
_ERFC = _MathOp('erfc', sc.erfc, _monotonic(math.erfc))

_SIN = _MathOp(
    'sin', sc.sin, _extrema(np.sin, _periodic_critical_points(np.pi / 2)), native_unit='rad'
)
_COS = _MathOp('cos', sc.cos, _extrema(np.cos, _periodic_critical_points(0.0)), native_unit='rad')
_TAN = _MathOp('tan', sc.tan, _tan_bounds, native_unit='rad', guard=_tan_guard)
_ARCSIN = _MathOp('arcsin', sc.asin, _monotonic(np.arcsin), domain=_CLOSED_UNIT_INTERVAL)
_ARCCOS = _MathOp('arccos', sc.acos, _monotonic(np.arccos), domain=_CLOSED_UNIT_INTERVAL)
_ARCTAN = _MathOp('arctan', sc.atan, _monotonic(np.arctan))
_ARCTAN2 = _MathOp(
    'arctan2',
    lambda y, x: sc.atan2(y=y, x=x),  # Scipp's atan2 is keyword-only
    _arctan2_bounds,
)
_SINC = _MathOp('sinc', sc.sinc, _extrema(_unnormalized_sinc, _sinc_critical_points))

_SINH = _MathOp('sinh', sc.sinh, _monotonic(np.sinh))
_COSH = _MathOp('cosh', sc.cosh, _extrema(np.cosh, _cosh_critical_points))
_TANH = _MathOp('tanh', sc.tanh, _monotonic(np.tanh))
_ARCSINH = _MathOp('arcsinh', sc.asinh, _monotonic(np.arcsinh))
_ARCCOSH = _MathOp('arccosh', sc.acosh, _monotonic(np.arccosh), domain=_AT_LEAST_ONE)
_ARCTANH = _MathOp('arctanh', sc.atanh, _monotonic(np.arctanh), domain=_OPEN_UNIT_INTERVAL)
