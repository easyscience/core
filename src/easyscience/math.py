# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

r"""
Maths operations for ``Parameter``, ``DescriptorNumber`` and
``DescriptorArray`` objects.

Each function evaluates Scipp functions of the same name, checks the
unit and propagates the variance, and returns a new object of the same
class as its argument:

- a ``Parameter`` gives a ``Parameter`` whose bounds are the range the
  function takes while the argument stays within its own bounds,
- a ``DescriptorNumber`` gives a ``DescriptorNumber``,
- a ``DescriptorArray`` gives a ``DescriptorArray``, evaluated element
  by element.

The result is always one of these base classes, also for a subclass.
Angles come back in ``rad``; call ``convert_unit('deg')`` on the result
for degrees.

For a ``DescriptorArray``, one element that makes the result infinite or
``nan`` is enough to raise ``ValueError`` for the whole call.

!!! warning "Correlated inputs"

    The variance is propagated to first order and assumes uncorrelated
    inputs. A ``Parameter`` stores no covariance, so a function of two
    correlated fit parameters can have a badly wrong variance.

Notes
-----
Scipp propagates the variance with linear error propagation, which the
Guide to the Expression of Uncertainty in Measurement (GUM) [1] calls
the law of propagation of uncertainty: the function is replaced by its
first-order Taylor expansion around the value of the input. For a
function $f$ of an input $x$ with variance $\sigma_x^2$, the variance of
the result is

$$ \sigma_f^2 = \left(\frac{df}{dx}\right)^2 \sigma_x^2 $$

This is Equation (10) of the GUM for uncorrelated inputs, which is also
what Scipp assumes [2]. It is a good approximation while the function is
close to linear over the spread of the input. When it is strongly curved
there, higher-order terms matter and the propagated variance is less
accurate. The Notes of each function give its own formula.

References
----------
1. JCGM 100:2008, *Evaluation of measurement data: Guide to the
   expression of uncertainty in measurement*, section 5.1.2.
   <https://www.bipm.org/documents/20126/2071204/JCGM_100_2008_E.pdf>
2. Scipp documentation, *Propagation of uncertainties*.
   <https://scipp.github.io/reference/error-propagation.html>

Examples
--------
>>> import easyscience as es
>>> amplitude = es.Parameter(
...     2.0, display_name='amplitude', variance=0.01, min=0.0, max=5.0
... )
>>> phase = es.Parameter(
...     30.0,
...     display_name='phase',
...     unit='deg',
...     variance=1.0,
...     min=0.0,
...     max=90.0,
... )
>>> print(es.math.sqrt(amplitude))
<Parameter 'sqrt(amplitude)': 1.4142 ± 0.0354, bounds=[0.0:2.23606797749979]>
>>> print(es.math.sin(phase))
<Parameter 'sin(phase)': 0.5000 ± 0.0151, bounds=[0.0:1.0]>
"""

import math
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from typing import TYPE_CHECKING
from typing import overload

import numpy as np
import scipp as sc

from easyscience.variable.descriptor_array import DescriptorArray
from easyscience.variable.descriptor_number import DescriptorNumber
from easyscience.variable.parameter import Parameter

# Lower and upper bound of an argument or a result.
_Bounds = tuple[float, float]
# Takes the bounds of each argument and returns the bounds of the result.
_ResultBoundsFunction = Callable[..., _Bounds]

# tan: a bound this close (in units of pi) to an asymptote is on it; catches 90 deg after rounding.
_TAN_EDGE_TOLERANCE = 1e-12

# sinc: two consecutive extrema hold the largest maximum and deepest minimum of a range, and
# the root just below the lower bound may be filtered out, so four roots are refined.
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


@overload
def exp(descriptor: DescriptorArray) -> DescriptorArray: ...


def exp(
    descriptor: DescriptorNumber | DescriptorArray,
) -> DescriptorNumber | DescriptorArray:
    r"""
    Exponential of a dimensionless input.

    Parameters
    ----------
    descriptor : DescriptorNumber | DescriptorArray
        Dimensionless input.

    Returns
    -------
    DescriptorNumber | DescriptorArray
        ``exp(descriptor)``, of the same class as ``descriptor``.

    Raises
    ------
    TypeError
        If ``descriptor`` is not a ``Parameter``, ``DescriptorNumber``
        or ``DescriptorArray``.
    UnitError
        If ``descriptor`` is not dimensionless.
    ValueError
        If ``descriptor`` is so large that the result or its variance
        overflows, or is ``nan``.

    See Also
    --------
    - [`log`][easyscience.math.log]: Natural logarithm.
    - [`scipp.exp`](https://scipp.github.io/generated/functions/scipp.exp): Scipp function that evaluates the value and the variance.

    Notes
    -----
    For $f(x) = e^{x}$, linear error propagation (see the [module
    documentation][easyscience.math]) gives the variance of the result:

    $$ \sigma_f^2 = e^{2x}\,\sigma_x^2 $$

    The function is monotonic, so the result bounds are its values at
    the input bounds.

    Examples
    --------
    >>> import easyscience as es
    >>> x = es.Parameter(1.0, display_name='x', variance=0.01, min=0.0, max=2.0)
    >>> print(es.math.exp(x))
    <Parameter 'exp(x)': 2.7183 ± 0.2718, bounds=[1.0:7.38905609893065]>
    """  # noqa: DOC502 -- raised in _evaluate
    return _evaluate(_EXP, descriptor)


@overload
def log(descriptor: Parameter) -> Parameter: ...


@overload
def log(descriptor: DescriptorNumber) -> DescriptorNumber: ...


@overload
def log(descriptor: DescriptorArray) -> DescriptorArray: ...


def log(
    descriptor: DescriptorNumber | DescriptorArray,
) -> DescriptorNumber | DescriptorArray:
    r"""
    Natural logarithm of a positive, dimensionless input.

    If the lower bound of the input is zero or negative, the result has
    no lower bound.

    Parameters
    ----------
    descriptor : DescriptorNumber | DescriptorArray
        Dimensionless input with positive values.

    Returns
    -------
    DescriptorNumber | DescriptorArray
        ``log(descriptor)``, of the same class as ``descriptor``.

    Raises
    ------
    TypeError
        If ``descriptor`` is not a ``Parameter``, ``DescriptorNumber``
        or ``DescriptorArray``.
    UnitError
        If ``descriptor`` is not dimensionless.
    ValueError
        If ``descriptor`` is zero, negative, infinite or ``nan``.

    See Also
    --------
    - [`exp`][easyscience.math.exp]: Exponential.
    - [`log10`][easyscience.math.log10]: Base-10 logarithm.
    - [`scipp.log`](https://scipp.github.io/generated/functions/scipp.log): Scipp function that evaluates the value and the variance.

    Notes
    -----
    For $f(x) = \ln x$, linear error propagation (see the [module
    documentation][easyscience.math]) gives the variance of the result:

    $$ \sigma_f^2 = \frac{\sigma_x^2}{x^2} $$

    The function is monotonic, so the result bounds are its values at
    the input bounds. Input bounds outside the domain are clipped to it
    first.

    Examples
    --------
    >>> import easyscience as es
    >>> x = es.Parameter(
    ...     10.0, display_name='x', variance=0.01, min=1.0, max=100.0
    ... )
    >>> print(es.math.log(x))
    <Parameter 'log(x)': 2.3026 ± 0.0100, bounds=[0.0:4.605170185988092]>
    """  # noqa: DOC502 -- raised in _evaluate
    return _evaluate(_LOG, descriptor)


@overload
def log10(descriptor: Parameter) -> Parameter: ...


@overload
def log10(descriptor: DescriptorNumber) -> DescriptorNumber: ...


@overload
def log10(descriptor: DescriptorArray) -> DescriptorArray: ...


def log10(
    descriptor: DescriptorNumber | DescriptorArray,
) -> DescriptorNumber | DescriptorArray:
    r"""
    Base-10 logarithm of a positive, dimensionless input.

    If the lower bound of the input is zero or negative, the result has
    no lower bound.

    Parameters
    ----------
    descriptor : DescriptorNumber | DescriptorArray
        Dimensionless input with positive values.

    Returns
    -------
    DescriptorNumber | DescriptorArray
        ``log10(descriptor)``, of the same class as ``descriptor``.

    Raises
    ------
    TypeError
        If ``descriptor`` is not a ``Parameter``, ``DescriptorNumber``
        or ``DescriptorArray``.
    UnitError
        If ``descriptor`` is not dimensionless.
    ValueError
        If ``descriptor`` is zero, negative, infinite or ``nan``.

    See Also
    --------
    - [`log`][easyscience.math.log]: Natural logarithm.
    - [`scipp.log10`](https://scipp.github.io/generated/functions/scipp.log10): Scipp function that evaluates the value and the variance.

    Notes
    -----
    For $f(x) = \log_{10} x$, linear error propagation (see the [module
    documentation][easyscience.math]) gives the variance of the result:

    $$ \sigma_f^2 = \frac{\sigma_x^2}{(x \ln 10)^2} $$

    The function is monotonic, so the result bounds are its values at
    the input bounds. Input bounds outside the domain are clipped to it
    first.

    Examples
    --------
    >>> import easyscience as es
    >>> x = es.Parameter(
    ...     100.0, display_name='x', variance=1.0, min=10.0, max=1000.0
    ... )
    >>> print(es.math.log10(x))
    <Parameter 'log10(x)': 2.0000 ± 0.0043, bounds=[1.0:3.0]>
    """  # noqa: DOC502 -- raised in _evaluate
    return _evaluate(_LOG10, descriptor)


@overload
def sqrt(descriptor: Parameter) -> Parameter: ...


@overload
def sqrt(descriptor: DescriptorNumber) -> DescriptorNumber: ...


@overload
def sqrt(descriptor: DescriptorArray) -> DescriptorArray: ...


def sqrt(
    descriptor: DescriptorNumber | DescriptorArray,
) -> DescriptorNumber | DescriptorArray:
    r"""
    Square root of a non-negative input.

    The unit is square-rooted too, so ``m**2`` becomes ``m``.

    Parameters
    ----------
    descriptor : DescriptorNumber | DescriptorArray
        Input that is dimensionless or has a squared unit, with
        non-negative values.

    Returns
    -------
    DescriptorNumber | DescriptorArray
        ``sqrt(descriptor)``, of the same class as ``descriptor``.

    Raises
    ------
    TypeError
        If ``descriptor`` is not a ``Parameter``, ``DescriptorNumber``
        or ``DescriptorArray``.
    UnitError
        If the unit of ``descriptor`` has no square root, such as ``m``.
    ValueError
        If ``descriptor`` is negative, infinite or ``nan``, or is 0 with
        a non-zero variance.

    See Also
    --------
    - [`scipp.sqrt`](https://scipp.github.io/generated/functions/scipp.sqrt): Scipp function that evaluates the value and the variance.

    Notes
    -----
    For $f(x) = \sqrt{x}$, linear error propagation (see the [module
    documentation][easyscience.math]) gives the variance of the result:

    $$ \sigma_f^2 = \frac{\sigma_x^2}{4x} $$

    The function is monotonic, so the result bounds are its values at
    the input bounds. Input bounds outside the domain are clipped to it
    first.

    Examples
    --------
    >>> import easyscience as es
    >>> area = es.Parameter(
    ...     9.0,
    ...     display_name='area',
    ...     unit='m**2',
    ...     variance=0.01,
    ...     min=4.0,
    ...     max=16.0,
    ... )
    >>> print(es.math.sqrt(area))
    <Parameter 'sqrt(area)': 3.0000 ± 0.0167 m, bounds=[2.0:4.0]>
    """  # noqa: DOC502 -- raised in _evaluate
    return _evaluate(_SQRT, descriptor)


# --- Special functions ---


@overload
def erf(descriptor: Parameter) -> Parameter: ...


@overload
def erf(descriptor: DescriptorNumber) -> DescriptorNumber: ...


@overload
def erf(descriptor: DescriptorArray) -> DescriptorArray: ...


def erf(
    descriptor: DescriptorNumber | DescriptorArray,
) -> DescriptorNumber | DescriptorArray:
    r"""
    Error function of a dimensionless input.

    Scipp cannot propagate an uncertainty through this function yet, so
    the input must not have a variance.

    Parameters
    ----------
    descriptor : DescriptorNumber | DescriptorArray
        Dimensionless input.

    Returns
    -------
    DescriptorNumber | DescriptorArray
        ``erf(descriptor)``, of the same class as ``descriptor``.

    Raises
    ------
    TypeError
        If ``descriptor`` is not a ``Parameter``, ``DescriptorNumber``
        or ``DescriptorArray``.
    UnitError
        If ``descriptor`` is not dimensionless.
    VariancesError
        If ``descriptor`` has a non-zero variance.
    ValueError
        If ``descriptor`` is ``nan``.

    See Also
    --------
    - [`erfc`][easyscience.math.erfc]: Complementary error function.
    - [`scipp.erf`](https://scipp.github.io/generated/functions/scipp.erf): Scipp function that evaluates the value; it cannot propagate a variance.

    Notes
    -----
    The function is defined as

    $$ \mathrm{erf}(x) = \frac{2}{\sqrt{\pi}} \int_0^x e^{-t^2}\,dt $$

    The function is monotonic, so the result bounds are its values at
    the input bounds.

    Examples
    --------
    >>> import easyscience as es
    >>> x = es.Parameter(0.5, display_name='x', min=0.0, max=2.0)
    >>> print(es.math.erf(x))
    <Parameter 'erf(x)': 0.5205, bounds=[0.0:0.9953222650189527]>
    """  # noqa: DOC502 -- raised in _evaluate
    return _evaluate(_ERF, descriptor)


@overload
def erfc(descriptor: Parameter) -> Parameter: ...


@overload
def erfc(descriptor: DescriptorNumber) -> DescriptorNumber: ...


@overload
def erfc(descriptor: DescriptorArray) -> DescriptorArray: ...


def erfc(
    descriptor: DescriptorNumber | DescriptorArray,
) -> DescriptorNumber | DescriptorArray:
    r"""
    Complementary error function of a dimensionless input.

    Scipp cannot propagate an uncertainty through this function yet, so
    the input must not have a variance.

    Parameters
    ----------
    descriptor : DescriptorNumber | DescriptorArray
        Dimensionless input.

    Returns
    -------
    DescriptorNumber | DescriptorArray
        ``erfc(descriptor)``, of the same class as ``descriptor``.

    Raises
    ------
    TypeError
        If ``descriptor`` is not a ``Parameter``, ``DescriptorNumber``
        or ``DescriptorArray``.
    UnitError
        If ``descriptor`` is not dimensionless.
    VariancesError
        If ``descriptor`` has a non-zero variance.
    ValueError
        If ``descriptor`` is ``nan``.

    See Also
    --------
    - [`erf`][easyscience.math.erf]: Error function.
    - [`scipp.erfc`](https://scipp.github.io/generated/functions/scipp.erfc): Scipp function that evaluates the value; it cannot propagate a variance.

    Notes
    -----
    The function is defined as

    $$ \mathrm{erfc}(x) = 1 - \mathrm{erf}(x) $$

    The function is monotonic, so the result bounds are its values at
    the input bounds.

    Examples
    --------
    >>> import easyscience as es
    >>> x = es.Parameter(0.5, display_name='x', min=0.0)
    >>> print(es.math.erfc(x))
    <Parameter 'erfc(x)': 0.4795, bounds=[0.0:1.0]>
    """  # noqa: DOC502 -- raised in _evaluate
    return _evaluate(_ERFC, descriptor)


# --- Trigonometric functions ---


@overload
def sin(descriptor: Parameter) -> Parameter: ...


@overload
def sin(descriptor: DescriptorNumber) -> DescriptorNumber: ...


@overload
def sin(descriptor: DescriptorArray) -> DescriptorArray: ...


def sin(
    descriptor: DescriptorNumber | DescriptorArray,
) -> DescriptorNumber | DescriptorArray:
    r"""
    Sine of an angle.

    The angle can be in ``rad`` or ``deg``.

    Parameters
    ----------
    descriptor : DescriptorNumber | DescriptorArray
        Angle, with unit ``rad`` or ``deg``.

    Returns
    -------
    DescriptorNumber | DescriptorArray
        ``sin(descriptor)``, of the same class as ``descriptor``.

    Raises
    ------
    TypeError
        If ``descriptor`` is not a ``Parameter``, ``DescriptorNumber``
        or ``DescriptorArray``.
    UnitError
        If ``descriptor`` is not an angle.
    ValueError
        If ``descriptor`` is infinite or ``nan``.

    See Also
    --------
    - [`cos`][easyscience.math.cos]: Cosine.
    - [`tan`][easyscience.math.tan]: Tangent.
    - [`arcsin`][easyscience.math.arcsin]: Inverse sine.
    - [`scipp.sin`](https://scipp.github.io/generated/functions/scipp.sin): Scipp function that evaluates the value and the variance.

    Notes
    -----
    For an angle $x$ in radians (Scipp converts degrees first), linear
    error propagation (see the [module documentation][easyscience.math])
    gives the variance of the result:

    $$ \sigma_f^2 = \cos^2 x \, \sigma_x^2 $$

    The result bounds also include any peak or trough between the input
    bounds.

    Examples
    --------
    >>> import easyscience as es
    >>> angle = es.Parameter(
    ...     30.0,
    ...     display_name='angle',
    ...     unit='deg',
    ...     variance=1.0,
    ...     min=0.0,
    ...     max=90.0,
    ... )
    >>> print(es.math.sin(angle))
    <Parameter 'sin(angle)': 0.5000 ± 0.0151, bounds=[0.0:1.0]>
    """  # noqa: DOC502 -- raised in _evaluate
    return _evaluate(_SIN, descriptor)


@overload
def cos(descriptor: Parameter) -> Parameter: ...


@overload
def cos(descriptor: DescriptorNumber) -> DescriptorNumber: ...


@overload
def cos(descriptor: DescriptorArray) -> DescriptorArray: ...


def cos(
    descriptor: DescriptorNumber | DescriptorArray,
) -> DescriptorNumber | DescriptorArray:
    r"""
    Cosine of an angle.

    The angle can be in ``rad`` or ``deg``.

    Parameters
    ----------
    descriptor : DescriptorNumber | DescriptorArray
        Angle, with unit ``rad`` or ``deg``.

    Returns
    -------
    DescriptorNumber | DescriptorArray
        ``cos(descriptor)``, of the same class as ``descriptor``.

    Raises
    ------
    TypeError
        If ``descriptor`` is not a ``Parameter``, ``DescriptorNumber``
        or ``DescriptorArray``.
    UnitError
        If ``descriptor`` is not an angle.
    ValueError
        If ``descriptor`` is infinite or ``nan``.

    See Also
    --------
    - [`sin`][easyscience.math.sin]: Sine.
    - [`tan`][easyscience.math.tan]: Tangent.
    - [`arccos`][easyscience.math.arccos]: Inverse cosine.
    - [`scipp.cos`](https://scipp.github.io/generated/functions/scipp.cos): Scipp function that evaluates the value and the variance.

    Notes
    -----
    For an angle $x$ in radians (Scipp converts degrees first), linear
    error propagation (see the [module documentation][easyscience.math])
    gives the variance of the result:

    $$ \sigma_f^2 = \sin^2 x \, \sigma_x^2 $$

    The result bounds also include any peak or trough between the input
    bounds.

    Examples
    --------
    >>> import easyscience as es
    >>> angle = es.Parameter(
    ...     60.0,
    ...     display_name='angle',
    ...     unit='deg',
    ...     variance=1.0,
    ...     min=0.0,
    ...     max=180.0,
    ... )
    >>> print(es.math.cos(angle))
    <Parameter 'cos(angle)': 0.5000 ± 0.0151, bounds=[-1.0:1.0]>
    """  # noqa: DOC502 -- raised in _evaluate
    return _evaluate(_COS, descriptor)


@overload
def tan(descriptor: Parameter) -> Parameter: ...


@overload
def tan(descriptor: DescriptorNumber) -> DescriptorNumber: ...


@overload
def tan(descriptor: DescriptorArray) -> DescriptorArray: ...


def tan(
    descriptor: DescriptorNumber | DescriptorArray,
) -> DescriptorNumber | DescriptorArray:
    r"""
    Tangent of an angle.

    The angle can be in ``rad`` or ``deg``. If the input bounds include
    an asymptote, such as 90 deg, the result has no bounds.

    Parameters
    ----------
    descriptor : DescriptorNumber | DescriptorArray
        Angle, with unit ``rad`` or ``deg``.

    Returns
    -------
    DescriptorNumber | DescriptorArray
        ``tan(descriptor)``, of the same class as ``descriptor``.

    Raises
    ------
    TypeError
        If ``descriptor`` is not a ``Parameter``, ``DescriptorNumber``
        or ``DescriptorArray``.
    UnitError
        If ``descriptor`` is not an angle.
    ValueError
        If ``descriptor`` is infinite or ``nan``.

    See Also
    --------
    - [`sin`][easyscience.math.sin]: Sine.
    - [`cos`][easyscience.math.cos]: Cosine.
    - [`arctan`][easyscience.math.arctan]: Inverse tangent.
    - [`scipp.tan`](https://scipp.github.io/generated/functions/scipp.tan): Scipp function that evaluates the value and the variance.

    Notes
    -----
    For an angle $x$ in radians (Scipp converts degrees first), linear
    error propagation (see the [module documentation][easyscience.math])
    gives the variance of the result:

    $$ \sigma_f^2 = \frac{\sigma_x^2}{\cos^4 x} $$

    Between two asymptotes the tangent increases, so the result bounds
    are its values at the input bounds. A bound exactly on an asymptote
    leaves only that side unbounded.

    Examples
    --------
    >>> import easyscience as es
    >>> angle = es.Parameter(
    ...     45.0,
    ...     display_name='angle',
    ...     unit='deg',
    ...     variance=1.0,
    ...     min=0.0,
    ...     max=60.0,
    ... )
    >>> print(es.math.tan(angle))
    <Parameter 'tan(angle)': 1.0000 ± 0.0349, bounds=[0.0:1.7320508075688767]>
    """  # noqa: DOC502 -- raised in _evaluate
    return _evaluate(_TAN, descriptor)


@overload
def arcsin(descriptor: Parameter) -> Parameter: ...


@overload
def arcsin(descriptor: DescriptorNumber) -> DescriptorNumber: ...


@overload
def arcsin(descriptor: DescriptorArray) -> DescriptorArray: ...


def arcsin(
    descriptor: DescriptorNumber | DescriptorArray,
) -> DescriptorNumber | DescriptorArray:
    r"""
    Inverse sine of a dimensionless input in ``[-1, 1]``.

    The result is an angle in ``rad``. Call ``convert_unit('deg')`` on
    it to get degrees.

    Parameters
    ----------
    descriptor : DescriptorNumber | DescriptorArray
        Dimensionless input with values in ``[-1, 1]``.

    Returns
    -------
    DescriptorNumber | DescriptorArray
        ``arcsin(descriptor)``, of the same class as ``descriptor``.

    Raises
    ------
    TypeError
        If ``descriptor`` is not a ``Parameter``, ``DescriptorNumber``
        or ``DescriptorArray``.
    UnitError
        If ``descriptor`` is not dimensionless.
    ValueError
        If ``descriptor`` is outside ``[-1, 1]`` or ``nan``, or is -1 or
        1 with a non-zero variance.

    See Also
    --------
    - [`sin`][easyscience.math.sin]: Sine.
    - [`arccos`][easyscience.math.arccos]: Inverse cosine.
    - [`asin`][easyscience.math.asin]: Alias.
    - [`scipp.asin`](https://scipp.github.io/generated/functions/scipp.asin): Scipp function that evaluates the value and the variance.

    Notes
    -----
    For $f(x) = \arcsin x$, linear error propagation (see the [module
    documentation][easyscience.math]) gives the variance of the result:

    $$ \sigma_f^2 = \frac{\sigma_x^2}{1 - x^2} $$

    The function is monotonic, so the result bounds are its values at
    the input bounds. Input bounds outside the domain are clipped to it
    first.

    Examples
    --------
    >>> import easyscience as es
    >>> x = es.Parameter(
    ...     0.5, display_name='x', variance=0.0001, min=0.0, max=1.0
    ... )
    >>> angle = es.math.arcsin(x)
    >>> angle.convert_unit('deg')
    >>> print(angle)
    <Parameter 'arcsin(x)': 30.0000 ± 0.6616 deg, bounds=[0.0:90.0]>
    """  # noqa: DOC502 -- raised in _evaluate
    return _evaluate(_ARCSIN, descriptor)


asin = arcsin
"""Alias of [`arcsin`][easyscience.math.arcsin]."""


@overload
def arccos(descriptor: Parameter) -> Parameter: ...


@overload
def arccos(descriptor: DescriptorNumber) -> DescriptorNumber: ...


@overload
def arccos(descriptor: DescriptorArray) -> DescriptorArray: ...


def arccos(
    descriptor: DescriptorNumber | DescriptorArray,
) -> DescriptorNumber | DescriptorArray:
    r"""
    Inverse cosine of a dimensionless input in ``[-1, 1]``.

    The result is an angle in ``rad``. Call ``convert_unit('deg')`` on
    it to get degrees.

    Parameters
    ----------
    descriptor : DescriptorNumber | DescriptorArray
        Dimensionless input with values in ``[-1, 1]``.

    Returns
    -------
    DescriptorNumber | DescriptorArray
        ``arccos(descriptor)``, of the same class as ``descriptor``.

    Raises
    ------
    TypeError
        If ``descriptor`` is not a ``Parameter``, ``DescriptorNumber``
        or ``DescriptorArray``.
    UnitError
        If ``descriptor`` is not dimensionless.
    ValueError
        If ``descriptor`` is outside ``[-1, 1]`` or ``nan``, or is -1 or
        1 with a non-zero variance.

    See Also
    --------
    - [`cos`][easyscience.math.cos]: Cosine.
    - [`arcsin`][easyscience.math.arcsin]: Inverse sine.
    - [`acos`][easyscience.math.acos]: Alias.
    - [`scipp.acos`](https://scipp.github.io/generated/functions/scipp.acos): Scipp function that evaluates the value and the variance.

    Notes
    -----
    For $f(x) = \arccos x$, linear error propagation (see the [module
    documentation][easyscience.math]) gives the variance of the result:

    $$ \sigma_f^2 = \frac{\sigma_x^2}{1 - x^2} $$

    The function is monotonic, so the result bounds are its values at
    the input bounds. Input bounds outside the domain are clipped to it
    first.

    Examples
    --------
    >>> import easyscience as es
    >>> x = es.Parameter(
    ...     0.5, display_name='x', variance=0.0001, min=0.0, max=1.0
    ... )
    >>> angle = es.math.arccos(x)
    >>> angle.convert_unit('deg')
    >>> print(angle)
    <Parameter 'arccos(x)': 60.0000 ± 0.6616 deg, bounds=[0.0:90.0]>
    """  # noqa: DOC502 -- raised in _evaluate
    return _evaluate(_ARCCOS, descriptor)


acos = arccos
"""Alias of [`arccos`][easyscience.math.arccos]."""


@overload
def arctan(descriptor: Parameter) -> Parameter: ...


@overload
def arctan(descriptor: DescriptorNumber) -> DescriptorNumber: ...


@overload
def arctan(descriptor: DescriptorArray) -> DescriptorArray: ...


def arctan(
    descriptor: DescriptorNumber | DescriptorArray,
) -> DescriptorNumber | DescriptorArray:
    r"""
    Inverse tangent of a dimensionless input.

    The result is an angle in ``rad``. Call ``convert_unit('deg')`` on
    it to get degrees.

    Parameters
    ----------
    descriptor : DescriptorNumber | DescriptorArray
        Dimensionless input.

    Returns
    -------
    DescriptorNumber | DescriptorArray
        ``arctan(descriptor)``, of the same class as ``descriptor``.

    Raises
    ------
    TypeError
        If ``descriptor`` is not a ``Parameter``, ``DescriptorNumber``
        or ``DescriptorArray``.
    UnitError
        If ``descriptor`` is not dimensionless.
    ValueError
        If ``descriptor`` is ``nan``.

    See Also
    --------
    - [`tan`][easyscience.math.tan]: Tangent.
    - [`arctan2`][easyscience.math.arctan2]: Angle of a point from its two Cartesian coordinates.
    - [`atan`][easyscience.math.atan]: Alias.
    - [`scipp.atan`](https://scipp.github.io/generated/functions/scipp.atan): Scipp function that evaluates the value and the variance.

    Notes
    -----
    For $f(x) = \arctan x$, linear error propagation (see the [module
    documentation][easyscience.math]) gives the variance of the result:

    $$ \sigma_f^2 = \frac{\sigma_x^2}{(1 + x^2)^2} $$

    The function is monotonic, so the result bounds are its values at
    the input bounds.

    Examples
    --------
    >>> import easyscience as es
    >>> x = es.Parameter(
    ...     1.0, display_name='x', variance=0.01, min=0.0, max=10.0
    ... )
    >>> angle = es.math.arctan(x)
    >>> angle.convert_unit('deg')
    >>> print(angle)
    <Parameter 'arctan(x)': 45.0000 ± 2.8648 deg, bounds=[0.0:84.28940686250037]>
    """  # noqa: DOC502 -- raised in _evaluate
    return _evaluate(_ARCTAN, descriptor)


atan = arctan
"""Alias of [`arctan`][easyscience.math.arctan]."""


@overload
def arctan2(y: Parameter, x: DescriptorNumber) -> Parameter: ...


@overload
def arctan2(y: DescriptorNumber, x: Parameter) -> Parameter: ...


@overload
def arctan2(y: DescriptorNumber, x: DescriptorNumber) -> DescriptorNumber: ...


@overload
def arctan2(y: DescriptorArray, x: DescriptorNumber | DescriptorArray) -> DescriptorArray: ...


@overload
def arctan2(y: DescriptorNumber, x: DescriptorArray) -> DescriptorArray: ...


def arctan2(
    y: DescriptorNumber | DescriptorArray, x: DescriptorNumber | DescriptorArray
) -> DescriptorNumber | DescriptorArray:
    r"""
    Angle of a point given by its Cartesian coordinates.

    Unlike ``arctan(y / x)``, this uses the signs of both coordinates,
    so the angle lands in the right quadrant. ``y`` and ``x`` must have
    the same unit, and the result is in ``rad``. Scipp cannot propagate
    an uncertainty through this function yet, so neither input may have
    a variance.

    Parameters
    ----------
    y : DescriptorNumber | DescriptorArray
        Cartesian y-coordinate.
    x : DescriptorNumber | DescriptorArray
        Cartesian x-coordinate, with the same unit as ``y``.

    Returns
    -------
    DescriptorNumber | DescriptorArray
        The angle: a ``DescriptorArray`` if ``y`` or ``x`` is one,
        otherwise a ``Parameter`` if ``y`` or ``x`` is one, otherwise a
        ``DescriptorNumber``.

    Raises
    ------
    TypeError
        If ``y`` or ``x`` is not a ``Parameter``, ``DescriptorNumber``
        or ``DescriptorArray``.
    UnitError
        If ``y`` and ``x`` have different units.
    VariancesError
        If ``y`` or ``x`` has a non-zero variance.
    ValueError
        If ``y`` or ``x`` is ``nan``.

    See Also
    --------
    - [`arctan`][easyscience.math.arctan]: Inverse tangent.
    - [`atan2`][easyscience.math.atan2]: Alias.
    - [`scipp.atan2`](https://scipp.github.io/generated/functions/scipp.atan2): Scipp function that evaluates the value; it cannot propagate a variance.

    Notes
    -----
    The result bounds come from the corners of the box spanned by the
    input bounds. If the box crosses the negative $x$ axis, where the
    angle jumps from $\pi$ to $-\pi$, the bounds are $[-\pi, \pi]$.

    Examples
    --------
    >>> import easyscience as es
    >>> y = es.Parameter(1.0, display_name='y', unit='m', min=0.5, max=2.0)
    >>> x = es.Parameter(1.0, display_name='x', unit='m', min=1.0, max=3.0)
    >>> angle = es.math.arctan2(y, x)
    >>> angle.convert_unit('deg')
    >>> print(angle)
    <Parameter 'arctan2(y, x)': 45.0000 deg, bounds=[9.462322208025617:63.43494882292201]>
    """  # noqa: DOC502 -- raised in _evaluate
    return _evaluate(_ARCTAN2, y, x)


atan2 = arctan2
"""Alias of [`arctan2`][easyscience.math.arctan2]."""


@overload
def sinc(descriptor: Parameter) -> Parameter: ...


@overload
def sinc(descriptor: DescriptorNumber) -> DescriptorNumber: ...


@overload
def sinc(descriptor: DescriptorArray) -> DescriptorArray: ...


def sinc(
    descriptor: DescriptorNumber | DescriptorArray,
) -> DescriptorNumber | DescriptorArray:
    r"""
    Unnormalised cardinal sine of a dimensionless input or an angle in
    radians.

    This is the physics convention, also used by Scipp. NumPy's
    ``np.sinc`` computes $\sin(\pi x) / (\pi x)$ instead.

    Parameters
    ----------
    descriptor : DescriptorNumber | DescriptorArray
        Input that is dimensionless or in ``rad``.

    Returns
    -------
    DescriptorNumber | DescriptorArray
        ``sinc(descriptor)``, of the same class as ``descriptor``.

    Raises
    ------
    TypeError
        If ``descriptor`` is not a ``Parameter``, ``DescriptorNumber``
        or ``DescriptorArray``.
    UnitError
        If the unit of ``descriptor`` is neither dimensionless nor
        ``rad``.
    ValueError
        If ``descriptor`` is infinite or ``nan``.

    See Also
    --------
    - [`sin`][easyscience.math.sin]: Sine.
    - [`scipp.sinc`](https://scipp.github.io/generated/functions/scipp.sinc): Scipp function that evaluates the value and the variance.

    Notes
    -----
    The function is defined as

    $$ \operatorname{sinc}(x) = \frac{\sin x}{x} $$

    $$ \operatorname{sinc}(0) = 1 $$

    With its derivative $f'(x)$, linear error propagation (see the
    [module documentation][easyscience.math]) gives the variance of the
    result:

    $$ f'(x) = \frac{x \cos x - \sin x}{x^2} $$

    $$ \sigma_f^2 = f'(x)^2 \, \sigma_x^2 $$

    The result bounds also include the peak at 0 and any other peak or
    trough between the input bounds. Those are found numerically.

    Examples
    --------
    >>> import easyscience as es
    >>> x = es.Parameter(1.0, display_name='x', variance=0.01, min=0.5, max=2.0)
    >>> print(es.math.sinc(x))
    <Parameter 'sinc(x)': 0.8415 ± 0.0301, bounds=[0.45464871341284085:0.958851077208406]>
    """  # noqa: DOC502 -- raised in _evaluate
    return _evaluate(_SINC, descriptor)


# --- Hyperbolic functions ---


@overload
def sinh(descriptor: Parameter) -> Parameter: ...


@overload
def sinh(descriptor: DescriptorNumber) -> DescriptorNumber: ...


@overload
def sinh(descriptor: DescriptorArray) -> DescriptorArray: ...


def sinh(
    descriptor: DescriptorNumber | DescriptorArray,
) -> DescriptorNumber | DescriptorArray:
    r"""
    Hyperbolic sine of a dimensionless input.

    Parameters
    ----------
    descriptor : DescriptorNumber | DescriptorArray
        Dimensionless input.

    Returns
    -------
    DescriptorNumber | DescriptorArray
        ``sinh(descriptor)``, of the same class as ``descriptor``.

    Raises
    ------
    TypeError
        If ``descriptor`` is not a ``Parameter``, ``DescriptorNumber``
        or ``DescriptorArray``.
    UnitError
        If ``descriptor`` is not dimensionless.
    ValueError
        If ``descriptor`` is so large in magnitude that the result or
        its variance overflows, or is ``nan``.

    See Also
    --------
    - [`cosh`][easyscience.math.cosh]: Hyperbolic cosine.
    - [`tanh`][easyscience.math.tanh]: Hyperbolic tangent.
    - [`arcsinh`][easyscience.math.arcsinh]: Inverse hyperbolic sine.
    - [`scipp.sinh`](https://scipp.github.io/generated/functions/scipp.sinh): Scipp function that evaluates the value and the variance.

    Notes
    -----
    The function is defined as

    $$ \sinh x = \frac{e^{x} - e^{-x}}{2} $$

    Linear error propagation (see the [module
    documentation][easyscience.math]) gives the variance of the result:

    $$ \sigma_f^2 = \cosh^2 x \, \sigma_x^2 $$

    The function is monotonic, so the result bounds are its values at
    the input bounds.

    Examples
    --------
    >>> import easyscience as es
    >>> x = es.Parameter(1.0, display_name='x', variance=0.01, min=0.0, max=2.0)
    >>> print(es.math.sinh(x))
    <Parameter 'sinh(x)': 1.1752 ± 0.1543, bounds=[0.0:3.6268604078470186]>
    """  # noqa: DOC502 -- raised in _evaluate
    return _evaluate(_SINH, descriptor)


@overload
def cosh(descriptor: Parameter) -> Parameter: ...


@overload
def cosh(descriptor: DescriptorNumber) -> DescriptorNumber: ...


@overload
def cosh(descriptor: DescriptorArray) -> DescriptorArray: ...


def cosh(
    descriptor: DescriptorNumber | DescriptorArray,
) -> DescriptorNumber | DescriptorArray:
    r"""
    Hyperbolic cosine of a dimensionless input.

    Parameters
    ----------
    descriptor : DescriptorNumber | DescriptorArray
        Dimensionless input.

    Returns
    -------
    DescriptorNumber | DescriptorArray
        ``cosh(descriptor)``, of the same class as ``descriptor``.

    Raises
    ------
    TypeError
        If ``descriptor`` is not a ``Parameter``, ``DescriptorNumber``
        or ``DescriptorArray``.
    UnitError
        If ``descriptor`` is not dimensionless.
    ValueError
        If ``descriptor`` is so large in magnitude that the result or
        its variance overflows, or is ``nan``.

    See Also
    --------
    - [`sinh`][easyscience.math.sinh]: Hyperbolic sine.
    - [`tanh`][easyscience.math.tanh]: Hyperbolic tangent.
    - [`arccosh`][easyscience.math.arccosh]: Inverse hyperbolic cosine.
    - [`scipp.cosh`](https://scipp.github.io/generated/functions/scipp.cosh): Scipp function that evaluates the value and the variance.

    Notes
    -----
    The function is defined as

    $$ \cosh x = \frac{e^{x} + e^{-x}}{2} $$

    Linear error propagation (see the [module
    documentation][easyscience.math]) gives the variance of the result:

    $$ \sigma_f^2 = \sinh^2 x \, \sigma_x^2 $$

    The result bounds also include the minimum of 1 at 0, if 0 lies
    between the input bounds.

    Examples
    --------
    >>> import easyscience as es
    >>> x = es.Parameter(
    ...     1.0, display_name='x', variance=0.01, min=-1.0, max=2.0
    ... )
    >>> print(es.math.cosh(x))
    <Parameter 'cosh(x)': 1.5431 ± 0.1175, bounds=[1.0:3.7621956910836314]>
    """  # noqa: DOC502 -- raised in _evaluate
    return _evaluate(_COSH, descriptor)


@overload
def tanh(descriptor: Parameter) -> Parameter: ...


@overload
def tanh(descriptor: DescriptorNumber) -> DescriptorNumber: ...


@overload
def tanh(descriptor: DescriptorArray) -> DescriptorArray: ...


def tanh(
    descriptor: DescriptorNumber | DescriptorArray,
) -> DescriptorNumber | DescriptorArray:
    r"""
    Hyperbolic tangent of a dimensionless input.

    Parameters
    ----------
    descriptor : DescriptorNumber | DescriptorArray
        Dimensionless input.

    Returns
    -------
    DescriptorNumber | DescriptorArray
        ``tanh(descriptor)``, of the same class as ``descriptor``.

    Raises
    ------
    TypeError
        If ``descriptor`` is not a ``Parameter``, ``DescriptorNumber``
        or ``DescriptorArray``.
    UnitError
        If ``descriptor`` is not dimensionless.
    ValueError
        If ``descriptor`` is ``nan``.

    See Also
    --------
    - [`sinh`][easyscience.math.sinh]: Hyperbolic sine.
    - [`cosh`][easyscience.math.cosh]: Hyperbolic cosine.
    - [`arctanh`][easyscience.math.arctanh]: Inverse hyperbolic tangent.
    - [`scipp.tanh`](https://scipp.github.io/generated/functions/scipp.tanh): Scipp function that evaluates the value and the variance.

    Notes
    -----
    The function is defined as

    $$ \tanh x = \frac{\sinh x}{\cosh x} $$

    Linear error propagation (see the [module
    documentation][easyscience.math]) gives the variance of the result:

    $$ \sigma_f^2 = \frac{\sigma_x^2}{\cosh^4 x} $$

    The function is monotonic, so the result bounds are its values at
    the input bounds.

    Examples
    --------
    >>> import easyscience as es
    >>> x = es.Parameter(1.0, display_name='x', variance=0.01, min=0.0, max=2.0)
    >>> print(es.math.tanh(x))
    <Parameter 'tanh(x)': 0.7616 ± 0.0420, bounds=[0.0:0.9640275800758169]>
    """  # noqa: DOC502 -- raised in _evaluate
    return _evaluate(_TANH, descriptor)


@overload
def arcsinh(descriptor: Parameter) -> Parameter: ...


@overload
def arcsinh(descriptor: DescriptorNumber) -> DescriptorNumber: ...


@overload
def arcsinh(descriptor: DescriptorArray) -> DescriptorArray: ...


def arcsinh(
    descriptor: DescriptorNumber | DescriptorArray,
) -> DescriptorNumber | DescriptorArray:
    r"""
    Inverse hyperbolic sine of a dimensionless input.

    Parameters
    ----------
    descriptor : DescriptorNumber | DescriptorArray
        Dimensionless input.

    Returns
    -------
    DescriptorNumber | DescriptorArray
        ``arcsinh(descriptor)``, of the same class as ``descriptor``.

    Raises
    ------
    TypeError
        If ``descriptor`` is not a ``Parameter``, ``DescriptorNumber``
        or ``DescriptorArray``.
    UnitError
        If ``descriptor`` is not dimensionless.
    ValueError
        If ``descriptor`` is infinite or ``nan``.

    See Also
    --------
    - [`sinh`][easyscience.math.sinh]: Hyperbolic sine.
    - [`asinh`][easyscience.math.asinh]: Alias.
    - [`scipp.asinh`](https://scipp.github.io/generated/functions/scipp.asinh): Scipp function that evaluates the value and the variance.

    Notes
    -----
    The function is defined as

    $$ \sinh^{-1} x = \ln\left(x + \sqrt{x^2 + 1}\right) $$

    Linear error propagation (see the [module
    documentation][easyscience.math]) gives the variance of the result:

    $$ \sigma_f^2 = \frac{\sigma_x^2}{x^2 + 1} $$

    The function is monotonic, so the result bounds are its values at
    the input bounds.

    Examples
    --------
    >>> import easyscience as es
    >>> x = es.Parameter(1.0, display_name='x', variance=0.01, min=0.0, max=2.0)
    >>> print(es.math.arcsinh(x))
    <Parameter 'arcsinh(x)': 0.8814 ± 0.0707, bounds=[0.0:1.4436354751788103]>
    """  # noqa: DOC502 -- raised in _evaluate
    return _evaluate(_ARCSINH, descriptor)


asinh = arcsinh
"""Alias of [`arcsinh`][easyscience.math.arcsinh]."""


@overload
def arccosh(descriptor: Parameter) -> Parameter: ...


@overload
def arccosh(descriptor: DescriptorNumber) -> DescriptorNumber: ...


@overload
def arccosh(descriptor: DescriptorArray) -> DescriptorArray: ...


def arccosh(
    descriptor: DescriptorNumber | DescriptorArray,
) -> DescriptorNumber | DescriptorArray:
    r"""
    Inverse hyperbolic cosine of a dimensionless input of at least 1.

    Parameters
    ----------
    descriptor : DescriptorNumber | DescriptorArray
        Dimensionless input with values of at least 1.

    Returns
    -------
    DescriptorNumber | DescriptorArray
        ``arccosh(descriptor)``, of the same class as ``descriptor``.

    Raises
    ------
    TypeError
        If ``descriptor`` is not a ``Parameter``, ``DescriptorNumber``
        or ``DescriptorArray``.
    UnitError
        If ``descriptor`` is not dimensionless.
    ValueError
        If ``descriptor`` is below 1, infinite or ``nan``, or is 1 with
        a non-zero variance.

    See Also
    --------
    - [`cosh`][easyscience.math.cosh]: Hyperbolic cosine.
    - [`acosh`][easyscience.math.acosh]: Alias.
    - [`scipp.acosh`](https://scipp.github.io/generated/functions/scipp.acosh): Scipp function that evaluates the value and the variance.

    Notes
    -----
    The function is defined as

    $$ \cosh^{-1} x = \ln\left(x + \sqrt{x^2 - 1}\right) $$

    Linear error propagation (see the [module
    documentation][easyscience.math]) gives the variance of the result:

    $$ \sigma_f^2 = \frac{\sigma_x^2}{x^2 - 1} $$

    The function is monotonic, so the result bounds are its values at
    the input bounds. Input bounds outside the domain are clipped to it
    first.

    Examples
    --------
    >>> import easyscience as es
    >>> x = es.Parameter(2.0, display_name='x', variance=0.01, min=1.0, max=3.0)
    >>> print(es.math.arccosh(x))
    <Parameter 'arccosh(x)': 1.3170 ± 0.0577, bounds=[0.0:1.762747174039086]>
    """  # noqa: DOC502 -- raised in _evaluate
    return _evaluate(_ARCCOSH, descriptor)


acosh = arccosh
"""Alias of [`arccosh`][easyscience.math.arccosh]."""


@overload
def arctanh(descriptor: Parameter) -> Parameter: ...


@overload
def arctanh(descriptor: DescriptorNumber) -> DescriptorNumber: ...


@overload
def arctanh(descriptor: DescriptorArray) -> DescriptorArray: ...


def arctanh(
    descriptor: DescriptorNumber | DescriptorArray,
) -> DescriptorNumber | DescriptorArray:
    r"""
    Inverse hyperbolic tangent of a dimensionless input in ``(-1, 1)``.

    Parameters
    ----------
    descriptor : DescriptorNumber | DescriptorArray
        Dimensionless input with values strictly between -1 and 1.

    Returns
    -------
    DescriptorNumber | DescriptorArray
        ``arctanh(descriptor)``, of the same class as ``descriptor``.

    Raises
    ------
    TypeError
        If ``descriptor`` is not a ``Parameter``, ``DescriptorNumber``
        or ``DescriptorArray``.
    UnitError
        If ``descriptor`` is not dimensionless.
    ValueError
        If ``descriptor`` is not strictly between -1 and 1, or is
        ``nan``.

    See Also
    --------
    - [`tanh`][easyscience.math.tanh]: Hyperbolic tangent.
    - [`atanh`][easyscience.math.atanh]: Alias.
    - [`scipp.atanh`](https://scipp.github.io/generated/functions/scipp.atanh): Scipp function that evaluates the value and the variance.

    Notes
    -----
    The function is defined as

    $$ \tanh^{-1} x = \frac{1}{2} \ln\frac{1 + x}{1 - x} $$

    Linear error propagation (see the [module
    documentation][easyscience.math]) gives the variance of the result:

    $$ \sigma_f^2 = \frac{\sigma_x^2}{(1 - x^2)^2} $$

    The function is monotonic, so the result bounds are its values at
    the input bounds. Input bounds outside the domain are clipped to it
    first.

    Examples
    --------
    >>> import easyscience as es
    >>> x = es.Parameter(
    ...     0.5, display_name='x', variance=0.0001, min=0.0, max=0.9
    ... )
    >>> print(es.math.arctanh(x))
    <Parameter 'arctanh(x)': 0.5493 ± 0.0133, bounds=[0.0:1.4722194895832204]>
    """  # noqa: DOC502 -- raised in _evaluate
    return _evaluate(_ARCTANH, descriptor)


atanh = arctanh
"""Alias of [`arctanh`][easyscience.math.arctanh]."""


# --- How a maths function is described ---


@dataclass(frozen=True)
class _InputRange:
    """The argument values a function is defined for."""

    lower_limit: float = -np.inf
    upper_limit: float = np.inf

    def clip(self, lower: float, upper: float) -> _Bounds:
        """Restrict the bounds ``[lower, upper]`` to this range."""
        return max(lower, self.lower_limit), min(upper, self.upper_limit)


@dataclass(frozen=True)
class _MathFunction:
    """
    What a public maths function evaluates and how its result bounds are
    found.

    Attributes
    ----------
    name : str
        Public name, used in error messages and in the name of the
        result.
    scipp_function : Callable
        Scipp function that evaluates the value and the variance and
        checks the units.
    result_bounds : _ResultBoundsFunction
        Takes the bounds of each argument and returns the bounds of the
        result.
    input_range : _InputRange, default=_InputRange()
        Argument values the function is defined for. Argument bounds are
        clipped to it before ``result_bounds`` runs.
    bounds_unit : str | None, default=None
        Unit that ``result_bounds`` expects the argument bounds in:
        ``'rad'`` for the trigonometric functions, whose NumPy versions
        take radians.
    """

    name: str
    scipp_function: Callable
    result_bounds: _ResultBoundsFunction
    input_range: _InputRange = _InputRange()
    bounds_unit: str | None = None


# --- Evaluating a maths function ---


def _evaluate(
    function: _MathFunction, *args: DescriptorNumber | DescriptorArray
) -> DescriptorNumber | DescriptorArray:
    """
    Evaluate a maths function with Scipp and wrap the result.

    Scipp checks the units and propagates the variances. A
    ``DescriptorArray`` result has no bounds; a ``Parameter`` result
    gets the range of ``function`` over the bounds of its arguments.

    Parameters
    ----------
    function : _MathFunction
        Specification of the function.
    *args : DescriptorNumber | DescriptorArray
        The arguments (a ``Parameter`` is a ``DescriptorNumber``).

    Returns
    -------
    DescriptorNumber | DescriptorArray
        A ``DescriptorArray`` if any argument is one, otherwise a
        ``Parameter`` if any argument is one, otherwise a
        ``DescriptorNumber``, named ``'<function>(<argument names>)'``.

    Raises
    ------
    TypeError
        If an argument is of another type.
    ValueError
        If a value or variance of the result is not finite.
    """
    for arg in args:
        if not isinstance(arg, (DescriptorNumber, DescriptorArray)):
            raise TypeError(
                'EasyScience math functions support `Parameter`, `DescriptorNumber` and '
                f'`DescriptorArray` objects, not {type(arg)}.'
            )

    result = function.scipp_function(*(_scipp_value(arg) for arg in args))
    name = f'{function.name}({", ".join(arg.display_name for arg in args)})'
    if not _all_finite(result):
        raise ValueError(
            f'{name} is not finite. Check that the values lie in the domain of {function.name}() '
            'and that the variances are finite.'
        )

    if any(isinstance(arg, DescriptorArray) for arg in args):
        return DescriptorArray.from_scipp(result, display_name=name)
    if not any(isinstance(arg, Parameter) for arg in args):
        return DescriptorNumber.from_scipp(result, display_name=name)

    argument_bounds = [_argument_bounds(function, arg) for arg in args]
    with np.errstate(all='ignore'):
        new_min, new_max = function.result_bounds(*argument_bounds)
    # Round-off at an extremum can leave the value just outside its own bounds.
    new_min, new_max = min(new_min, result.value), max(new_max, result.value)
    new_min, new_max = _widen_collapsed_bounds(new_min, new_max, result.value)
    return Parameter.from_scipp(result, display_name=name, min=new_min, max=new_max)


# TODO(): ``Parameter`` rejects ``min`` and ``max`` within a relative 1e-9 of each other, a literal
# in its ``__init__`` and its min/max setters. Make it a named constant in parameter.py and use it
# here, so that the two cannot drift apart.
def _widen_collapsed_bounds(
    lower: float | np.ndarray, upper: float | np.ndarray, value: float | np.ndarray
) -> tuple[float | np.ndarray, float | np.ndarray]:
    """
    Widen bounds that ``Parameter`` would reject as equal.

    The bounds are widened symmetrically around ``value``. The check is
    the one ``Parameter`` uses, and it works element by element on
    arrays as well as on single numbers.

    Parameters
    ----------
    lower : float | np.ndarray
        Lower bound.
    upper : float | np.ndarray
        Upper bound.
    value : float | np.ndarray
        The result value, which lies inside ``[lower, upper]``.

    Returns
    -------
    tuple[float | np.ndarray, float | np.ndarray]
        ``(lower, upper)``, padded on each side where they are within
        the tolerance of ``Parameter``: by ``_COLLAPSE_PAD * |value|``,
        or by ``_COLLAPSE_PAD_ZERO`` where the value is 0.
    """
    collapsed = np.isclose(lower, upper, rtol=1e-9, atol=0.0)
    pad = np.where(value == 0, _COLLAPSE_PAD_ZERO, np.abs(value) * _COLLAPSE_PAD)
    pad = np.where(collapsed, pad, 0.0)
    return lower - pad, upper + pad


def _scipp_value(descriptor: DescriptorNumber | DescriptorArray) -> sc.Variable:
    """
    Scipp value of a descriptor, without variances if they are all zero.

    A ``Parameter`` stores a variance of 0.0 by default. Scipp would
    propagate it to ``nan`` where the derivative is infinite, and its
    ``erf``, ``erfc`` and ``atan2`` refuse any variance, so a zero
    variance is dropped.
    """
    value = descriptor.full_value
    if value.variances is not None and not np.any(value.variances):
        return sc.values(value)
    return value


def _all_finite(result: sc.Variable) -> bool:
    """
    Whether every value and every variance of ``result`` is finite.
    """
    if not np.all(np.isfinite(result.values)):
        return False
    return result.variances is None or bool(np.all(np.isfinite(result.variances)))


@cache
def _unit_factor(unit: str, target_unit: str | None) -> float:
    """
    Factor that converts ``unit`` to ``target_unit``; 1.0 if none is
    needed.
    """
    if target_unit is None or unit == target_unit:
        return 1.0
    return float(sc.scalar(1.0, unit=unit).to(unit=target_unit).value)


def _argument_bounds(function: _MathFunction, param: DescriptorNumber) -> _Bounds:
    """
    Bounds of one argument, clipped to the input range of the function.

    They are converted to the unit that ``function.result_bounds``
    expects. A plain ``DescriptorNumber`` has no bounds, so its bounds
    are its value.
    """
    if isinstance(param, Parameter):
        lower, upper = float(param.min), float(param.max)
    else:
        lower = upper = float(param.value)
    lower, upper = function.input_range.clip(lower, upper)
    if function.bounds_unit is None:
        return lower, upper
    factor = _unit_factor(str(param.unit), function.bounds_unit)
    return lower * factor, upper * factor


# --- Result bounds ---
# Each function below takes the bounds of every argument and returns the exact lower and upper
# bound of the result. They run under ``np.errstate(all='ignore')``, so an edge value such as
# log(0) = -inf is returned without a warning.


def _monotonic_bounds(function_values: Callable) -> _ResultBoundsFunction:
    """
    Result bounds of a monotonic function: its values at the argument
    bounds.
    """

    def bounds(argument_bounds: _Bounds) -> tuple[float, float]:
        lower, upper = argument_bounds
        at_lower, at_upper = float(function_values(lower)), float(function_values(upper))
        return min(at_lower, at_upper), max(at_lower, at_upper)

    return bounds


def _bounds_from_extrema(
    function_values: Callable, extrema: Callable[[float, float], np.ndarray]
) -> _ResultBoundsFunction:
    """
    Result bounds of a non-monotonic function.

    The bounds are the smallest and largest of its values at the
    argument bounds and at ``extrema(lower, upper)``, the maxima and
    minima between them. A ``nan`` value, such as ``sin(inf)``, is
    ignored.
    """

    def bounds(argument_bounds: _Bounds) -> tuple[float, float]:
        lower, upper = argument_bounds
        candidates = np.concatenate(([lower, upper], extrema(lower, upper)))
        values = np.asarray(function_values(candidates), dtype=float)
        return float(np.nanmin(values)), float(np.nanmax(values))

    return bounds


def _periodic_extrema(offset: float) -> Callable[[float, float], np.ndarray]:
    """
    Maxima and minima of sine or cosine, at ``offset + n*pi``.

    The offset is ``pi/2`` for sine and 0 for cosine. An infinite range,
    or one of a whole period, contains a maximum and a minimum, so two
    points are returned without listing them all.
    """

    def points(lower: float, upper: float) -> np.ndarray:
        if not (np.isfinite(lower) and np.isfinite(upper)) or upper - lower >= 2 * np.pi:
            return np.array([offset, offset + np.pi])
        n = np.arange(np.ceil((lower - offset) / np.pi), np.floor((upper - offset) / np.pi) + 1)
        return offset + n * np.pi

    return points


def _cosh_minimum(lower: float, upper: float) -> np.ndarray:
    """The single minimum of cosh, at 0."""
    return np.array([0.0]) if lower <= 0.0 <= upper else np.array([])


def _unnormalized_sinc(x) -> np.ndarray:
    """
    sin(x)/x, with sinc(0) = 1 and the limit sinc(±inf) = 0.

    ``np.sinc`` is the *normalised* sin(pi x)/(pi x), so the argument is
    scaled by 1/pi.
    """
    x = np.asarray(x, dtype=float)
    return np.where(np.isinf(x), 0.0, np.sinc(x / np.pi))


def _sinc_positive_extrema(
    lower: float, upper: float, count: int = _SINC_ROOT_COUNT
) -> np.ndarray:
    """
    Maxima and minima of sinc on the positive axis, nearest the lower
    bound.

    They are the positive roots of ``tan(x) = x``, one in each ``(k*pi,
    k*pi + pi/2)``. The heights of the lobes fall off like 1/x, so the
    largest maximum and the deepest minimum in the range are among the
    first few roots at or after ``lower``.

    Beyond ``_SINC_NEGLIGIBLE_LOBES_FROM`` the lobes are negligible and
    none are returned.

    All ``count`` roots are refined at once with Newton's method on
    ``g(x) = x cos(x) - sin(x)``, ``g'(x) = -x sin(x)``, with the
    vectorised update ``x <- x - g(x) / g'(x)``.
    """
    if upper <= 0.0 or lower > _SINC_NEGLIGIBLE_LOBES_FROM:
        return np.array([])
    first = max(1, int(np.floor(max(lower, 0.0) / np.pi)))
    k = np.arange(first, first + count)
    x = (k + 0.5) * np.pi
    x = x - 1.0 / x  # asymptotic first guess for the root of tan(x) = x
    for _ in range(_SINC_NEWTON_STEPS):
        x = x - (x * np.cos(x) - np.sin(x)) / (-x * np.sin(x))
    return x[(x >= lower) & (x <= upper)]


def _sinc_extrema(lower: float, upper: float) -> np.ndarray:
    """
    Maxima and minima of sinc: 0, its largest value, and the roots of
    tan(x) = x.
    """
    points = [_sinc_positive_extrema(lower, upper), -_sinc_positive_extrema(-upper, -lower)]
    if lower <= 0.0 <= upper:
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


def _tan_bounds(argument_bounds: _Bounds) -> tuple[float, float]:
    """
    Result bounds of tan(x), for argument bounds in radians.

    tan increases between asymptotes (``pi/2 + n*pi``). Bounds that
    contain an asymptote give all real numbers. A bound exactly on an
    asymptote makes the result unbounded on that side only: ``[0,
    pi/2]`` gives ``[0, inf)``.
    """
    lower, upper = argument_bounds
    if not (np.isfinite(lower) and np.isfinite(upper)):
        return -np.inf, np.inf
    branch_lower, lower_on_asymptote = _tan_branch((lower - np.pi / 2) / np.pi)
    branch_upper, upper_on_asymptote = _tan_branch((upper - np.pi / 2) / np.pi)
    if upper_on_asymptote:
        branch_upper -= 1  # an upper bound on an asymptote closes the branch below it
    if branch_lower != branch_upper:
        return -np.inf, np.inf
    lower = -np.inf if lower_on_asymptote else float(np.tan(lower))
    upper = np.inf if upper_on_asymptote else float(np.tan(upper))
    return lower, upper


def _arctan2_bounds(y_bounds: _Bounds, x_bounds: _Bounds) -> tuple[float, float]:
    """
    Result bounds of arctan2(y, x) over the box spanned by the bounds.

    The angle is a harmonic function, so away from the branch cut its
    extremes sit on the corners of the box. If the box touches the cut
    (``y = 0`` with ``x < 0``) the angle jumps between -pi and pi and
    the range is the full ``[-pi, pi]``.
    """
    (y_lower, y_upper), (x_lower, x_upper) = y_bounds, x_bounds
    if y_lower < 0.0 <= y_upper and x_lower < 0.0:
        return -np.pi, np.pi
    corners = [np.arctan2(y, x) for y in (y_lower, y_upper) for x in (x_lower, x_upper)]
    return float(min(corners)), float(max(corners))


# --- What each public function evaluates, and how its result bounds are found ---

_NON_NEGATIVE = _InputRange(lower_limit=0.0)
_AT_LEAST_ONE = _InputRange(lower_limit=1.0)
_UNIT_INTERVAL = _InputRange(lower_limit=-1.0, upper_limit=1.0)

_EXP = _MathFunction('exp', sc.exp, _monotonic_bounds(np.exp))
_LOG = _MathFunction('log', sc.log, _monotonic_bounds(np.log), input_range=_NON_NEGATIVE)
_LOG10 = _MathFunction('log10', sc.log10, _monotonic_bounds(np.log10), input_range=_NON_NEGATIVE)
_SQRT = _MathFunction('sqrt', sc.sqrt, _monotonic_bounds(np.sqrt), input_range=_NON_NEGATIVE)
_ERF = _MathFunction('erf', sc.erf, _monotonic_bounds(math.erf))
_ERFC = _MathFunction('erfc', sc.erfc, _monotonic_bounds(math.erfc))

_SIN = _MathFunction(
    'sin', sc.sin, _bounds_from_extrema(np.sin, _periodic_extrema(np.pi / 2)), bounds_unit='rad'
)
_COS = _MathFunction(
    'cos', sc.cos, _bounds_from_extrema(np.cos, _periodic_extrema(0.0)), bounds_unit='rad'
)
_TAN = _MathFunction('tan', sc.tan, _tan_bounds, bounds_unit='rad')
_ARCSIN = _MathFunction(
    'arcsin', sc.asin, _monotonic_bounds(np.arcsin), input_range=_UNIT_INTERVAL
)
_ARCCOS = _MathFunction(
    'arccos', sc.acos, _monotonic_bounds(np.arccos), input_range=_UNIT_INTERVAL
)
_ARCTAN = _MathFunction('arctan', sc.atan, _monotonic_bounds(np.arctan))
_ARCTAN2 = _MathFunction(
    'arctan2',
    lambda y, x: sc.atan2(y=y, x=x),  # Scipp's atan2 is keyword-only
    _arctan2_bounds,
)
_SINC = _MathFunction('sinc', sc.sinc, _bounds_from_extrema(_unnormalized_sinc, _sinc_extrema))

_SINH = _MathFunction('sinh', sc.sinh, _monotonic_bounds(np.sinh))
_COSH = _MathFunction('cosh', sc.cosh, _bounds_from_extrema(np.cosh, _cosh_minimum))
_TANH = _MathFunction('tanh', sc.tanh, _monotonic_bounds(np.tanh))
_ARCSINH = _MathFunction('arcsinh', sc.asinh, _monotonic_bounds(np.arcsinh))
_ARCCOSH = _MathFunction(
    'arccosh', sc.acosh, _monotonic_bounds(np.arccosh), input_range=_AT_LEAST_ONE
)
_ARCTANH = _MathFunction(
    'arctanh', sc.atanh, _monotonic_bounds(np.arctanh), input_range=_UNIT_INTERVAL
)
