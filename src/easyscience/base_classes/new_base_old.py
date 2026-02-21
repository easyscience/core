from __future__ import annotations

#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience
from inspect import signature
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any
    from typing import Dict
    from typing import Iterable
    from typing import List
    from typing import Optional
    from typing import Set

from easyscience import global_object

from ..global_object.undo_redo import property_stack
from ..io.serializer_base import SerializerBase


class NewBase_old:
    """
    Legacy NewBase implementation kept as backup.
    """

    def __init__(self, unique_name: Optional[str] = None, display_name: Optional[str] = None):
        self._global_object = global_object
        if unique_name is None:
            unique_name = self._global_object.generate_unique_name(self.__class__.__name__)
            self._default_unique_name = True
        else:
            self._default_unique_name = False
        if not isinstance(unique_name, str):
            raise TypeError('Unique name has to be a string.')
        self._unique_name = unique_name
        self._global_object.map.add_vertex(self, obj_type='created')
        if display_name is not None and not isinstance(display_name, str):
            raise TypeError('Display name must be a string or None')
        self._display_name = display_name

    @property
    def _arg_spec(self) -> Set[str]:
        sign = signature(self.__class__.__init__)
        names = [param.name for param in sign.parameters.values() if param.kind == param.POSITIONAL_OR_KEYWORD]
        return set(names[1:])

    @property
    def unique_name(self) -> str:
        return self._unique_name

    @unique_name.setter
    def unique_name(self, new_unique_name: str):
        if not isinstance(new_unique_name, str):
            raise TypeError('Unique name has to be a string.')
        self._unique_name = new_unique_name
        self._global_object.map.add_vertex(self)
        self._default_unique_name = False

    @property
    def display_name(self) -> str:
        display_name = self._display_name
        if display_name is None:
            display_name = self.unique_name
        return display_name

    @display_name.setter
    @property_stack
    def display_name(self, name: str | None) -> None:
        if name is not None and not isinstance(name, str):
            raise TypeError('Display name must be a string or None')
        self._display_name = name

    def to_dict(self, skip: Optional[List[str]] = None) -> Dict[str, Any]:
        serializer = SerializerBase()
        if skip is None:
            skip = []
        if self._default_unique_name and 'unique_name' not in skip:
            skip.append('unique_name')
        if self._display_name is None:
            skip.append('display_name')
        return serializer._convert_to_dict(self, skip=skip, full_encode=False)

    @classmethod
    def from_dict(cls, obj_dict: Dict[str, Any]) -> NewBase_old:
        if not SerializerBase._is_serialized_easyscience_object(obj_dict):
            raise ValueError('Input must be a dictionary representing an EasyScience object.')
        if obj_dict['@class'] == cls.__name__:
            kwargs = SerializerBase.deserialize_dict(obj_dict)
            return cls(**kwargs)
        else:
            raise ValueError(f'Class name in dictionary does not match the expected class: {cls.__name__}.')

    def __dir__(self) -> Iterable[str]:
        new_class_objs = list(k for k in dir(self.__class__) if not k.startswith('_'))
        return sorted(new_class_objs)

    def __copy__(self) -> NewBase_old:
        temp = self.to_dict(skip=['unique_name'])
        new_obj = self.__class__.from_dict(temp)
        return new_obj

    def __deepcopy__(self, memo):
        return self.__copy__()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__} `{self.unique_name}`'
