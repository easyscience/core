# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Test-only models shared across the test suite.

``tests/conftest.py`` puts this directory on ``sys.path``, so tests
import from here with ``from easy_test_models import ...``. The module
name starts with ``easy`` on purpose: the serializer only treats a dict
as an EasyScience object (and dispatches to ``from_dict``) when its
``@module`` starts with ``easy``, so this keeps serializer round trips
working for these models.
"""

from __future__ import annotations

from typing import Iterable
from typing import Optional
from typing import Union

import numpy as np

from easyscience.base_classes import EasyList
from easyscience.base_classes import ModelBase
from easyscience.variable import Parameter


class CoefficientModel(ModelBase):
    """
    A minimal model holding its parameters in an ``EasyList``.

    It exercises nested containers in serialization, copying, fitting
    parameter discovery and calculator bindings. Plain numbers become
    ``Parameter`` objects named ``c0``, ``c1``, ... The model evaluates
    as a polynomial with the coefficients in ``numpy.polyval`` order.

    Parameters
    ----------
    display_name : Optional[str], default=None
        Display name of the model.
    coefficients : Optional[Union[Iterable[Union[float, Parameter]], EasyList]], default=None
        Initial coefficients, either numbers/``Parameter`` objects or a
        ready-made ``EasyList``.
    unique_name : Optional[str], default=None
        Unique name of the model.
    """

    def __init__(
        self,
        display_name: Optional[str] = None,
        coefficients: Optional[Union[Iterable[Union[float, Parameter]], EasyList]] = None,
        unique_name: Optional[str] = None,
    ):
        super().__init__(unique_name=unique_name, display_name=display_name)
        if isinstance(coefficients, EasyList):
            self._coefficients = coefficients
            return
        self._coefficients = EasyList(protected_types=Parameter)
        for index, item in enumerate(coefficients or []):
            if not isinstance(item, Parameter):
                item = Parameter(value=float(item), display_name=f'c{index}')
            self._coefficients.append(item)

    @property
    def coefficients(self) -> EasyList:
        """The coefficient parameters."""
        return self._coefficients

    def __call__(self, x: np.ndarray, *args, **kwargs) -> np.ndarray:
        return np.polyval([c.value for c in self.coefficients], x)
