# SPDX-FileCopyrightText: 2024 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Iterable
from typing import Optional
from typing import Union

import numpy as np

from ..base_classes import EasyList
from ..base_classes import ModelBase
from ..variable import Parameter


class Polynomial(ModelBase):
    """
    A polynomial model.

    Parameters
    ----------
    display_name : Optional[str], default='polynomial'
        The display name of the model.
    coefficients : Optional[Union[Iterable[Union[float, Parameter]], EasyList]], default=None
        Coefficients used to populate ``self.coefficients``.
    unique_name : Optional[str], default=None
        Unique name of the model. By default, None.

    Raises
    ------
    TypeError
        If ``coefficients`` is neither an ``EasyList`` nor an iterable
        of floats or ``Parameter`` instances.
    """

    def __init__(
        self,
        display_name: Optional[str] = 'polynomial',
        coefficients: Optional[Union[Iterable[Union[float, Parameter]], EasyList]] = None,
        unique_name: Optional[str] = None,
    ):
        super(Polynomial, self).__init__(unique_name=unique_name, display_name=display_name)
        self._coefficients = EasyList(protected_types=Parameter)
        if coefficients is not None:
            if isinstance(coefficients, EasyList):
                self._coefficients = coefficients
            elif isinstance(coefficients, Iterable):
                for index, item in enumerate(coefficients):
                    if issubclass(type(item), Parameter):
                        self._coefficients.append(item)
                    elif isinstance(item, float):
                        self._coefficients.append(
                            Parameter(value=item, display_name='c{}'.format(index))
                        )
                    else:
                        raise TypeError('Coefficients must be floats or Parameters')
            else:
                raise TypeError('coefficients must be a list or an EasyList')

    @property
    def coefficients(self) -> EasyList:
        """
        Get the coefficients of the polynomial.

        Returns
        -------
        EasyList
            Coefficients of the polynomial.
        """
        return self._coefficients

    def __call__(self, x: np.ndarray, *args, **kwargs) -> np.ndarray:
        return np.polyval([c.value for c in self.coefficients], x)

    def __repr__(self):
        s = []
        if len(self.coefficients) >= 1:
            s += [f'{self.coefficients[0].value}']
            if len(self.coefficients) >= 2:
                s += [f'{self.coefficients[1].value}x']
                if len(self.coefficients) >= 3:
                    s += [
                        f'{c.value}x^{i + 2}'
                        for i, c in enumerate(self.coefficients[2:])
                        if c.value != 0
                    ]
        s.reverse()
        s = ' + '.join(s)
        return 'Polynomial({}, {})'.format(self.display_name, s)
