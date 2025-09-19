#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience


from typing import ClassVar
from typing import Iterable
from typing import Optional
from typing import Union

import numpy as np

from ..base_classes import CollectionBase
from ..base_classes import ObjBase
from ..variable import Parameter


class Polynomial(ObjBase):
    """
    A polynomial model.

    Parameters
    ----------
    name : str
        The name of the model.
    degree : int
        The degree of the polynomial.
    """

    coefficients: ClassVar[CollectionBase]

    def __init__(
        self,
        name: str = 'polynomial',
        coefficients: Optional[Union[Iterable[Union[float, Parameter]], CollectionBase]] = None,
    ):
        super(Polynomial, self).__init__(name, coefficients=CollectionBase('coefficients'))
        if coefficients is not None:
            if issubclass(type(coefficients), CollectionBase):
                self.coefficients = coefficients
            elif isinstance(coefficients, Iterable):
                for index, item in enumerate(coefficients):
                    if issubclass(type(item), Parameter):
                        self.coefficients.append(item)
                    elif isinstance(item, float):
                        self.coefficients.append(Parameter(name='c{}'.format(index), value=item))
                    else:
                        raise TypeError('Coefficients must be floats or Parameters')
            else:
                raise TypeError('coefficients must be a list or a CollectionBase')

    def __call__(self, x: np.ndarray, *args, **kwargs) -> np.ndarray:
        return np.polyval([c.value for c in self.coefficients], x)

    def __repr__(self):
        s = []
        if len(self.coefficients) >= 1:
            s += [f'{self.coefficients[0].value}']
            if len(self.coefficients) >= 2:
                s += [f'{self.coefficients[1].value}x']
                if len(self.coefficients) >= 3:
                    s += [f'{c.value}x^{i+2}' for i, c in enumerate(self.coefficients[2:]) if c.value != 0]
        s.reverse()
        s = ' + '.join(s)
        return 'Polynomial({}, {})'.format(self.name, s)

