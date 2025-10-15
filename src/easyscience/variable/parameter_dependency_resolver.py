#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

from __future__ import annotations

from typing import Any
from typing import List

from .parameter import Parameter


def resolve_all_parameter_dependencies(obj: Any) -> None:
    """
    Recursively find all Parameter objects in an object hierarchy and resolve their pending dependencies.
    
    This function should be called after deserializing a complex object that contains Parameters
    with dependencies to ensure all dependency relationships are properly established.
    
    :param obj: The object to search for Parameters (can be a single Parameter, list, dict, or complex object)
    """

    def _collect_parameters(item: Any, parameters: List[Parameter]) -> None:
        """Recursively collect all Parameter objects from an item."""
        if isinstance(item, Parameter):
            parameters.append(item)
        elif isinstance(item, dict):
            for value in item.values():
                _collect_parameters(value, parameters)
        elif isinstance(item, (list, tuple)):
            for element in item:
                _collect_parameters(element, parameters)
        elif hasattr(item, '__dict__'):
            # Check object attributes
            for attr_name in dir(item):
                if not attr_name.startswith('_'):  # Skip private attributes
                    try:
                        attr_value = getattr(item, attr_name)
                        if not callable(attr_value):  # Skip methods
                            _collect_parameters(attr_value, parameters)
                    except (AttributeError, Exception):
                        # log the exception
                        print(f"Error accessing attribute '{attr_name}' of {item}")
                        # Skip attributes that can't be accessed
                        continue

    # Collect all parameters
    all_parameters = []
    _collect_parameters(obj, all_parameters)

    # Resolve dependencies for all parameters that have pending dependencies
    resolved_count = 0
    error_count = 0
    errors = []

    for param in all_parameters:
        if hasattr(param, '_pending_dependency_string'):
            try:
                param.resolve_pending_dependencies()
                resolved_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"Failed to resolve dependencies for parameter '{param.name}'" \
                               f" (unique_name: '{param.unique_name}'): {e}")

    # Report results
    if resolved_count > 0:
        print(f"Successfully resolved dependencies for {resolved_count} parameter(s).")

    if error_count > 0:
        error_message = f"Failed to resolve dependencies for {error_count} parameter(s):\n" \
                + "\n".join(errors)
        raise ValueError(error_message)


def get_parameters_with_pending_dependencies(obj: Any) -> List[Parameter]:
    """
    Find all Parameter objects in an object hierarchy that have pending dependencies.

    :param obj: The object to search for Parameters
    :return: List of Parameters with pending dependencies
    """
    parameters_with_pending = []

    def _collect_pending_parameters(item: Any) -> None:
        """Recursively collect all Parameter objects with pending dependencies."""
        if isinstance(item, Parameter):
            if hasattr(item, '_pending_dependency_string'):
                parameters_with_pending.append(item)
        elif isinstance(item, dict):
            for value in item.values():
                _collect_pending_parameters(value)
        elif isinstance(item, (list, tuple)):
            for element in item:
                _collect_pending_parameters(element)
        elif hasattr(item, '__dict__'):
            # Check object attributes
            for attr_name in dir(item):
                if not attr_name.startswith('_'):  # Skip private attributes
                    try:
                        attr_value = getattr(item, attr_name)
                        if not callable(attr_value):  # Skip methods
                            _collect_pending_parameters(attr_value)
                    except (AttributeError, Exception):
                        # log the exception
                        print(f"Error accessing attribute '{attr_name}' of {item}")
                        # Skip attributes that can't be accessed
                        continue

    _collect_pending_parameters(obj)
    return parameters_with_pending
