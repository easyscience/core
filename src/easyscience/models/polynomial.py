#  SPDX-FileCopyrightText: 2023 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2023 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience


import numbers
from typing import List
from typing import Optional

import numpy as np

from ..base_classes import BaseObj
from ..variable import Parameter


class Polynomial(BaseObj):
    """
    A simple polynomial model.
    """

    def __init__(
        self,
        name: str,
        coefficients: List[numbers.Number],
        unique_name: Optional[str] = None,
    ):
        """
        Construct a polynomial model.

        :param name: Name of this model.
        :param coefficients: List of coefficients of the polynomial. The last coefficient is the constant term, the second to last is the linear term, etc.
        :param unit: Unit of the polynomial.
        :param unique_name: Unique name of this object. This is used to find the object from anywhere in the program.
        
        """  # noqa: E501

        if not isinstance(coefficients, list):
            raise TypeError('coefficients must be a list of numbers')
        if len(coefficients) == 0:
            raise ValueError('list of coefficients cannot be empty')
        for coefficient, index in enumerate(coefficients):
            if not isinstance(coefficient, numbers.Number):
                raise TypeError(f'coefficients must be numbers, found {type(coefficient)} at index {index}')
        self._coefficients = [Parameter(name=f'c{i}', value=c) for i, c in enumerate(coefficients)]

        super().__init__(
            name=name, 
            unique_name=unique_name
            )


    def __call__(self, x: np.ndarray) -> np.ndarray:
        return np.polyval([c.value for c in self._coefficients], x)

    def __repr__(self):
        string = []
        for i, c in enumerate(self._coefficients):
            if i == 0:
                string += [f'{c.value}']
            elif i == 1:
                string += [f'{c.value}x']
            else:
                string += [f'{c.value}x^{i}']
        string.reverse()
        string = ' + '.join(string)
        return 'Polynomial "{}" : {}'.format(self.name, string)

