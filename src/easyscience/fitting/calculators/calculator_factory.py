#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

"""
Abstract factory for creating physics calculators in EasyScience.

This module provides the foundation for implementing calculator factories that produce
calculator instances. The factory pattern allows different physics calculation backends
to be instantiated without coupling to specific implementations.

Unlike the legacy InterfaceFactoryTemplate, this factory:
- Is stateless (does not track which calculator is "current")
- Only produces calculators, does not hold calculator state
- Follows the pattern established by the minimizers factory

Example usage in a product library::

    from easyscience.fitting.calculators import CalculatorFactoryBase, CalculatorBase

    class MyCalculatorFactory(CalculatorFactoryBase):
        def __init__(self):
            super().__init__()
            self._try_register_calculator('backend_a', 'mypackage.backend_a', 'BackendACalculator')
            self._try_register_calculator('backend_b', 'mypackage.backend_b', 'BackendBCalculator')

        def create(self, calculator_name, model, instrumental_parameters, **kwargs):
            if calculator_name not in self._available_calculators:
                raise ValueError(f"Unknown calculator: {calculator_name}")
            return self._available_calculators[calculator_name](model, instrumental_parameters, **kwargs)
"""

from __future__ import annotations

from abc import ABCMeta
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Type

if TYPE_CHECKING:
    from easyscience.base_classes import NewBase

    from .calculator_base import CalculatorBase


class CalculatorFactoryBase(metaclass=ABCMeta):
    """
    Abstract base class for calculator factories.

    A calculator factory is responsible for creating calculator instances based on
    a requested calculator type. This follows the Factory pattern and is designed
    to be stateless - it only creates calculators without maintaining any state
    about which calculator is "current".

    The factory supports dynamic discovery of available calculators based on what
    packages are actually installed and importable. Subclasses can use the
    `_try_register_calculator` method to probe for optional dependencies.

    This is similar to how the minimizers factory works in EasyScience, where the
    factory simply produces the requested minimizer without tracking state.

    Concrete implementations should call `_try_register_calculator` in their
    `__init__` to build the list of available calculators.

    Examples
    --------
    Creating a concrete factory with dynamic discovery::

        class MyCalculatorFactory(CalculatorFactoryBase):
            def __init__(self):
                super().__init__()
                self._try_register_calculator('backend_a', 'mypackage.backend_a', 'BackendACalculator')
                self._try_register_calculator('backend_b', 'mypackage.backend_b', 'BackendBCalculator')

    Using the factory::

        factory = MyCalculatorFactory()
        print(factory.available_calculators)  # Only shows what's installed
        calculator = factory.create('backend_a', model, instrument)
        result = calculator.calculate(x_values)
    """

    def __init__(self) -> None:
        """Initialize the factory with an empty calculator registry."""
        self._available_calculators: Dict[str, Type[CalculatorBase]] = {}

    def _try_register_calculator(
        self,
        name: str,
        module_path: str,
        class_name: str,
    ) -> bool:
        """
        Attempt to import and register a calculator class.

        This method tries to import a calculator class from the given module path.
        If the import succeeds, the calculator is added to the available calculators.
        If the import fails (e.g., because a dependency is not installed), the
        calculator is silently skipped.

        Parameters
        ----------
        name : str
            The name to register the calculator under.
        module_path : str
            The full module path to import from (e.g., 'easyreflectometry.calculators.refl1d').
        class_name : str
            The name of the calculator class within the module.

        Returns
        -------
        bool
            True if the calculator was successfully registered, False otherwise.

        Examples
        --------
        ::

            # In a subclass __init__:
            self._try_register_calculator(
                'backend_a',
                'mypackage.calculators.backend_a',
                'BackendACalculator'
            )
        """
        try:
            import importlib

            module = importlib.import_module(module_path)
            calculator_class = getattr(module, class_name)
            self._available_calculators[name] = calculator_class
            return True
        except (ImportError, AttributeError):
            # Package not installed or class not found - skip silently
            return False
        except Exception:
            # Any other error during import - skip silently
            return False

    @property
    def available_calculators(self) -> List[str]:
        """
        Return a list of available calculator names.

        Returns
        -------
        List[str]
            Names of all calculators that can be created by this factory.
            Only includes calculators whose dependencies are installed.
        """
        return list(self._available_calculators.keys())

    @abstractmethod
    def create(
        self,
        calculator_name: str,
        model: NewBase,
        instrumental_parameters: Optional[NewBase] = None,
        **kwargs: Any,
    ) -> CalculatorBase:
        """
        Create a calculator instance.

        Parameters
        ----------
        calculator_name : str
            The name of the calculator to create. Must be one of the names
            returned by `available_calculators`.
        model : NewBase
            The physical model (e.g., sample) to pass to the calculator.
        instrumental_parameters : NewBase, optional
            Instrumental parameters to pass to the calculator.
        **kwargs : Any
            Additional arguments to pass to the calculator constructor.

        Returns
        -------
        CalculatorBase
            A new calculator instance configured with the given model and
            instrumental parameters.

        Raises
        ------
        ValueError
            If the requested calculator_name is not available.
        """
        ...

    def __repr__(self) -> str:
        """Return a string representation of the factory."""
        return f'{self.__class__.__name__}(available={self.available_calculators})'


class SimpleCalculatorFactory(CalculatorFactoryBase):
    """
    A simple implementation of a calculator factory using a dictionary registry.

    This class provides a convenient base for creating calculator factories
    where calculators are registered either via `_try_register_calculator` for
    dynamic discovery or directly via the `register` method.

    Parameters
    ----------
    calculators : Dict[str, Type[CalculatorBase]], optional
        A dictionary mapping calculator names to calculator classes.
        If provided, these are added to the registry immediately.

    Examples
    --------
    Using dynamic registration in a subclass::

        class MyFactory(SimpleCalculatorFactory):
            def __init__(self):
                super().__init__()
                self._try_register_calculator('fast', 'mypackage.fast', 'FastCalculator')
                self._try_register_calculator('accurate', 'mypackage.accurate', 'AccurateCalculator')

        factory = MyFactory()
        calc = factory.create('fast', model, instrument)  # Only if 'fast' is installed

    Using instance-level registration::

        factory = SimpleCalculatorFactory({
            'custom': CustomCalculator,
        })
        calc = factory.create('custom', model, instrument)
    """

    def __init__(
        self,
        calculators: Optional[Dict[str, Type[CalculatorBase]]] = None,
    ) -> None:
        """
        Initialize the factory with optional calculator registry.

        Parameters
        ----------
        calculators : Dict[str, Type[CalculatorBase]], optional
            A dictionary mapping calculator names to calculator classes.
            If provided, these calculators are added to the registry.
        """
        super().__init__()
        if calculators is not None:
            self._available_calculators.update(calculators)

    def create(
        self,
        calculator_name: str,
        model: NewBase,
        instrumental_parameters: Optional[NewBase] = None,
        **kwargs: Any,
    ) -> CalculatorBase:
        """
        Create a calculator instance from the registered calculators.

        Parameters
        ----------
        calculator_name : str
            The name of the calculator to create.
        model : NewBase
            The physical model to pass to the calculator.
        instrumental_parameters : NewBase, optional
            Instrumental parameters to pass to the calculator.
        **kwargs : Any
            Additional arguments to pass to the calculator constructor.

        Returns
        -------
        CalculatorBase
            A new calculator instance.

        Raises
        ------
        ValueError
            If the calculator_name is not in the registry or is not a string.
        TypeError
            If model is None or instrumental_parameters has wrong type.
        """
        if not isinstance(calculator_name, str):
            raise ValueError(f'calculator_name must be a string, got {type(calculator_name).__name__}')

        if calculator_name not in self._available_calculators:
            available = ', '.join(self.available_calculators) if self.available_calculators else 'none'
            raise ValueError(f"Unknown calculator '{calculator_name}'. Available calculators: {available}")

        if model is None:
            raise TypeError('Model cannot be None')

        calculator_class = self._available_calculators[calculator_name]
        try:
            return calculator_class(model, instrumental_parameters, **kwargs)
        except Exception as e:
            raise type(e)(f"Failed to create calculator '{calculator_name}': {e}") from e

    def register(self, name: str, calculator_class: Type[CalculatorBase]) -> None:
        """
        Register a new calculator class with the factory.

        Parameters
        ----------
        name : str
            The name to register the calculator under.
        calculator_class : Type[CalculatorBase]
            The calculator class to register.

        Raises
        ------
        TypeError
            If calculator_class is not a subclass of CalculatorBase.
        ValueError
            If name is empty or not a string.

        Warnings
        --------
        If overwriting an existing calculator, a warning is issued.
        """
        # Import here to avoid circular imports at module level
        import warnings

        from .calculator_base import CalculatorBase

        if not isinstance(name, str) or not name:
            raise ValueError('Calculator name must be a non-empty string')

        if not (isinstance(calculator_class, type) and issubclass(calculator_class, CalculatorBase)):
            raise TypeError(f'calculator_class must be a subclass of CalculatorBase, got {type(calculator_class).__name__}')

        if name in self._available_calculators:
            warnings.warn(f"Overwriting existing calculator '{name}' in {self.__class__.__name__}", UserWarning, stacklevel=2)

        self._available_calculators[name] = calculator_class

    def unregister(self, name: str) -> None:
        """
        Remove a calculator from the registry.

        Parameters
        ----------
        name : str
            The name of the calculator to remove.

        Raises
        ------
        KeyError
            If the calculator name is not in the registry.
        """
        if name not in self._available_calculators:
            raise KeyError(f"Calculator '{name}' is not registered")
        del self._available_calculators[name]
