# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

"""
Helpers for how units are stored and displayed.

Scipp can display a unit in two ways that surprise a user, and they need
different remedies:

1. It prints a **numeric factor** because it has no name for a scaled unit, so
   ``m/mm`` becomes ``1000`` and ``dm*m`` becomes ``0.1m^2``. The magnitude is then
   hiding inside the unit. This module fixes that, by folding the factor back into
   the value.
2. It prints **a different name than the one that was written**, so ``angstrom``
   becomes ``Å`` and ``nm*m/s`` becomes ``nGy*s``. That is a display concern only, and
   is handled by the descriptors, which remember the spelling a unit arrived as. See
   ``DescriptorNumber.unit``.

The descriptors' ``unit`` property is therefore a *display* string;
``_scalar.unit`` / ``_array.unit`` remains the source of truth for
meaning. The two never disagree about what the unit is, only about how
it is spelled.
"""

from __future__ import annotations

import re
from typing import Optional
from typing import Union

import scipp as sc

# Scipp writes a scaled unit it cannot name as a numeric factor followed by the
# dimensions, in any of the forms '1000', '0.1m^2', '2.57e-44*J^2' and '3.9e+43/J^2'.

# ^: start of string
# \s*: optional whitespace
# (?P<number>[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?): a number, possibly with decimal point and exponent, captured as 'number'
# \s*: optional whitespace
# (?P<separator>[*/])?: an optional separator, either '*' or '/', captured as 'separator'
# \s*: optional whitespace
# (?P<rest>.*): the rest of the string, captured as 'rest'
_NUMERIC_FACTOR = re.compile(
    r'^\s*(?P<number>[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)\s*(?P<separator>[*/])?\s*(?P<rest>.*)$'
)


def has_numeric_factor(unit: Union[str, sc.Unit]) -> bool:
    """
    Report whether a unit carries a numeric factor in the way it is
    written.

    Applied to a ``sc.Unit`` this asks how scipp displays it; applied to
    a string it asks how the user wrote it, which is how a spelling such
    as '10dm^2' is rejected while 'dm*m' is accepted.

    Parameters
    ----------
    unit : Union[str, sc.Unit]
        Unit to inspect.

    Returns
    -------
    bool
        True if the unit is written with a leading multiplier.
    """
    match = _NUMERIC_FACTOR.match(str(unit))
    if match is None:
        return False
    if match.group('rest') == '' and match.group('separator') is None:
        # A pure number, such as '1000'.
        return True
    # The leading '1' of '1/meV' is a placeholder for the numerator, not a factor.
    return float(match.group('number')) != 1.0


def si_base_unit(unit: sc.Unit) -> sc.Unit:
    """
    Return the unit with the same dimensions as ``unit`` but no
    multiplier.

    The dimensions are read from ``sc.Unit.to_dict()``, which stores the
    base units and powers, which is more robust than parsing the string.

    Parameters
    ----------
    unit : sc.Unit
        Unit to reduce.

    Returns
    -------
    sc.Unit
        The corresponding SI base unit, or dimensionless if the unit has
        no dimensions.
    """
    powers = unit.to_dict().get('powers', {})
    if not powers:
        return sc.units.dimensionless
    return sc.Unit('*'.join(f'{base}^{power}' for base, power in powers.items()))


def normalisation_target(unit: sc.Unit, has_spelling: bool = False) -> Optional[str]:
    """
    Return the unit to convert to so that no magnitude is left inside
    the unit.

    A unit which reduces to a pure number, such as 'm/mm', is always
    folded away.

    Beyond that, only units with nothing better to display are
    converted. If the user's own spelling is being kept
    (``has_spelling``), then nothing numeric is on show and there is
    nothing to fix, so a parameter created with '1/meV^2' keeps both its
    spelling and its value, even though scipp would print it as
    '3.9e+43/J^2'.

    Parameters
    ----------
    unit : sc.Unit
        Unit to inspect.
    has_spelling : bool, default=False
        Whether a clean spelling for this unit is being displayed in its
        place.

    Returns
    -------
    Optional[str]
        The unit to convert to, or None if there is nothing to fix, or
        if no safe target could be determined.
    """
    if unit.to_dict().get('e_flag'):
        # Offset units such as degC cannot be converted this way.
        return None
    if not unit.to_dict().get('powers'):
        # A pure number, such as the 1000 that 'm/mm' reduces to.
        return None if unit == sc.units.dimensionless else 'dimensionless'
    if has_spelling or not has_numeric_factor(unit):
        return None
    try:
        base_unit = si_base_unit(unit)
        target = str(base_unit)
        if sc.Unit(target) != base_unit:
            # The target does not survive a round trip, so it is not safe to use.
            return None
    except Exception:
        return None
    return target
