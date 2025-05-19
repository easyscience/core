#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience
from abc import ABCMeta
from abc import abstractmethod

import numpy as np

from ..base_classes.obj_base import ObjBase
from ..fitting.minimizers import MinimizerBase


class AnalysisBase(ObjBase, metaclass=ABCMeta):
    """
    This virtual class allows for the creation of technique-specific Analysis objects.
    """
    def __init__(self, name: str, interface=None, *args, **kwargs):
        super(AnalysisBase, self).__init__(name, *args, **kwargs)
        self.name = name
        self._calculator = None
        self._minimizer = None
        self._fitter = None
        self.interface = interface

    @abstractmethod
    def calculate_theory(self,
                         x: np.ndarray,
                         **kwargs) -> np.ndarray:
        raise NotImplementedError("calculate_theory not implemented")

    @abstractmethod
    def fit(self,
            x: np.ndarray,
            y: np.ndarray,
            e: np.ndarray,
            **kwargs) -> None:
        raise NotImplementedError("fit not implemented")

    @property
    def calculator(self) -> str:
        if self._calculator is None:
            self._calculator = self.interface.current_interface_name
        return self._calculator

    @calculator.setter
    def calculator(self, value) -> None:
        # TODO: check if the calculator is available for the given JobType
        self.interface.switch(value, fitter=self._fitter)

    @property
    def minimizer(self) -> MinimizerBase:
        return self._minimizer

    @minimizer.setter
    def minimizer(self, minimizer: MinimizerBase) -> None:
        self._minimizer = minimizer

    # required dunder methods
    def __str__(self):
        return f"Analysis: {self.name}"
    
    