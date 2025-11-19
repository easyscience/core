from __future__ import annotations

#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ..io import SerializerBase
from ..variable import DescriptorNumber
from ..variable import Parameter
from .new_base import NewBase


class ModelBase(NewBase):
    """
    This is the base class for all model classes in EasyScience.
    It provides methods to get parameters for fitting and analysis as well as proper serialization/deserialization for
    DescriptorNumber/Parameter attributes.

    It assumes that Parameters/DescriptorNumbers are assigned as properties with the getters returning the parameter
    but the setter only setting the value of the parameter.
    e.g.
    ```python
    @property
    def my_param(self) -> Parameter:
        return self._my_param

    @my_param.setter
    def my_param(self, new_value: float) -> None:
        self._my_param.value = new_value
    ```
    """

    def __init__(self, unique_name: Optional[str] = None, display_name:  Optional[str] = None):
        super().__init__(unique_name=unique_name, display_name=display_name)

    def get_all_parameters(self) -> List[DescriptorNumber]:
        """
        Get all `Parameters` or `DescriptorNumber` objects as a list.

        :return: List of `DescriptorNumber` or `Parameter` objects.
        """
        params = []
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, DescriptorNumber):
                params.append(attr)
            elif hasattr(attr, 'get_all_parameters'):
                params += attr.get_all_parameters()
        return params

    def get_fit_parameters(self) -> List[Parameter]:
        """
        Get all parameters which can be fitted as a list.

        :return: List of `Parameter` objects.
        """
        params = []
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, Parameter) and attr.independent:
                params.append(attr)
            elif hasattr(attr, 'get_fit_parameters'):
                params += attr.get_fit_parameters()
        return params

    def get_free_parameters(self) -> List[Parameter]:
        """
        Get all parameters which are currently free to be fitted as a list.

        :return: List of `Parameter` objects.
        """
        params = []
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, Parameter) and not attr.fixed and attr.independent:
                params.append(attr)
        return params
    
    @classmethod
    def from_dict(cls, obj_dict: Dict[str, Any]) -> None:
        """
        Re-create an EasyScience object with DescriptorNumber attributes from a full encoded dictionary.

        :param obj_dict: dictionary containing the serialized contents (from `SerializerDict`) of an EasyScience object
        :return: Reformed EasyScience object
        """
        if isinstance(obj_dict, dict):
            if '@module' in obj_dict and obj_dict['@module'].startswith('easy'):
                if '@class' in obj_dict and obj_dict['@class'] == cls.__name__:
                    kwargs = SerializerBase._deserialize_dict(obj_dict)
                    parameter_placeholder = {}
                    for key, value in kwargs.items():
                        if isinstance(value, DescriptorNumber):
                            parameter_placeholder[key] = value
                            kwargs[key] = value.value
                    cls_instance = cls(**kwargs)
                    for key, value in parameter_placeholder.items():
                        temp_param = getattr(cls_instance, key)
                        setattr(cls_instance, '_'+key, value)
                        cls_instance._global_object.map.prune(temp_param.unique_name)
                    return cls_instance
                else:
                    raise ValueError(f'Class name not in dictionary or does not match the expected class: {cls.__name__}.')
            else:
                raise ValueError('Dictionary does not represent an EasyScience object.')
        else:
            raise TypeError('Input must be a dictionary.')