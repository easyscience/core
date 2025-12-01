#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

"""
Abstract base class for physics calculators in EasyScience.

This module provides the foundation for implementing physics calculators that compute
theoretical results based on a model and instrumental parameters. Concrete implementations
are provided in product-specific libraries (e.g., EasyReflectometryLib).

Example usage in a product library::

    from easyscience.fitting.calculators import CalculatorBase

    class ReflectivityCalculator(CalculatorBase):
        def __init__(self, model, instrumental_parameters, **kwargs):
            super().__init__(model, instrumental_parameters, **kwargs)
            # Initialize calculator-specific internals

        def calculate(self, x):
            # Compute reflectivity using self._model and self._instrumental_parameters
            return reflectivity_curve

        def get_sld_profile(self):
            # Calculator-specific method for SLD profile
            return sld_profile
"""

from __future__ import annotations

from abc import ABCMeta
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Any
from typing import Optional

if TYPE_CHECKING:
    import numpy as np

from easyscience.base_classes import NewBase


class CalculatorBase(NewBase, metaclass=ABCMeta):
    """
    Abstract base class for physics calculators.

    A calculator is responsible for computing theoretical results based on a physical
    model and instrumental parameters. This decouples the physics engine from the
    model definition, allowing different calculation backends to be used interchangeably.

    The calculator:
    - Takes a model (sample) and instrumental parameters in its constructor
    - Provides a `calculate(x)` method for computing theoretical values
    - Allows updating the model and instrumental parameters at runtime

    Parameters
    ----------
    model : NewBase
        The physical model (e.g., sample structure) to calculate from.
    instrumental_parameters : NewBase, optional
        Instrumental parameters (e.g., resolution, wavelength) that affect the calculation.
    **kwargs : Any
        Additional calculator-specific configuration options.

    Attributes
    ----------
    name : str
        The name of this calculator implementation. Should be overridden by subclasses.

    Examples
    --------
    Subclasses must implement the `calculate` method::

        class MyCalculator(CalculatorBase):
            name = "my_calculator"

            def calculate(self, x):
                # Use self._model and self._instrumental_parameters
                return computed_values
    """

    name: str = "base"

    def __init__(
        self,
        model: NewBase,
        instrumental_parameters: Optional[NewBase] = None,
        unique_name: Optional[str] = None,
        display_name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the calculator with a model and instrumental parameters.

        Parameters
        ----------
        model : NewBase
            The physical model to calculate from. This is typically a sample
            or structure definition containing fittable parameters.
        instrumental_parameters : NewBase, optional
            Instrumental parameters that affect the calculation, such as
            resolution, wavelength, or detector settings.
        unique_name : str, optional
            Unique identifier for this calculator instance.
        display_name : str, optional
            Human-readable name for display purposes.
        **kwargs : Any
            Additional calculator-specific options.
        """
        if model is None:
            raise ValueError("Model cannot be None")
        
        # Initialize NewBase with naming
        super().__init__(unique_name=unique_name, display_name=display_name)
        
        self._model = model
        self._instrumental_parameters = instrumental_parameters
        self._additional_kwargs = kwargs

    @property
    def model(self) -> NewBase:
        """
        Get the current physical model.

        Returns
        -------
        NewBase
            The physical model used for calculations.
        """
        return self._model

    @model.setter
    def model(self, new_model: NewBase) -> None:
        """
        Set a new physical model.

        Parameters
        ----------
        new_model : NewBase
            The new physical model to use for calculations.

        Raises
        ------
        ValueError
            If the new model is None.
        """
        if new_model is None:
            raise ValueError("Model cannot be None")
        self._model = new_model

    @property
    def instrumental_parameters(self) -> Optional[NewBase]:
        """
        Get the current instrumental parameters.

        Returns
        -------
        NewBase or None
            The instrumental parameters, or None if not set.
        """
        return self._instrumental_parameters

    @instrumental_parameters.setter
    def instrumental_parameters(self, new_parameters: Optional[NewBase]) -> None:
        """
        Set new instrumental parameters.

        Parameters
        ----------
        new_parameters : NewBase or None
            The new instrumental parameters to use for calculations.
            Truly optional, since instrumental parameters may not always be needed.
        """
        self._instrumental_parameters = new_parameters

    def update_model(self, new_model: NewBase) -> None:
        """
        Update the physical model used for calculations.

        This is an alternative to the `model` property setter that can be
        overridden by subclasses to perform additional setup when the model changes.

        Parameters
        ----------
        new_model : NewBase
            The new physical model to use.

        Raises
        ------
        ValueError
            If the new model is None.
        """
        self.model = new_model

    def update_instrumental_parameters(self, new_parameters: Optional[NewBase]) -> None:
        """
        Update the instrumental parameters used for calculations.

        This is an alternative to the `instrumental_parameters` property setter
        that can be overridden by subclasses to perform additional setup when
        instrumental parameters change.

        Parameters
        ----------
        new_parameters : NewBase or None
            The new instrumental parameters to use.
        """
        self.instrumental_parameters = new_parameters

    @property
    def additional_kwargs(self) -> dict:
        """
        Get additional keyword arguments passed during initialization.

        Returns
        -------
        dict
            Dictionary of additional kwargs passed to __init__.
        """
        return self._additional_kwargs

    @abstractmethod
    def calculate(self, x: np.ndarray) -> np.ndarray:
        """
        Calculate theoretical values at the given points.

        This is the main calculation method that must be implemented by all
        concrete calculator classes. It uses the current model and instrumental
        parameters to compute theoretical predictions.

        Parameters
        ----------
        x : np.ndarray
            The independent variable values (e.g., Q values, angles, energies)
            at which to calculate the theoretical response.

        Returns
        -------
        np.ndarray
            The calculated theoretical values corresponding to the input x values.

        Notes
        -----
        This method is called during fitting and should be thread-safe if
        parallel fitting is to be supported.
        """
        ...

    def __repr__(self) -> str:
        """Return a string representation of the calculator."""
        model_name = getattr(self._model, 'name', type(self._model).__name__)
        instr_info = ""
        if self._instrumental_parameters is not None:
            instr_name = getattr(
                self._instrumental_parameters,
                'name',
                type(self._instrumental_parameters).__name__ # default to class name if no 'name' attribute
            )
            instr_info = f", instrumental_parameters={instr_name}"
        return f"{self.__class__.__name__}(model={model_name}{instr_info})"
