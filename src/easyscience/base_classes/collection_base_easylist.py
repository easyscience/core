# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from collections.abc import MutableSequence
from typing import Any

from easyscience.io.serializer_base import SerializerBase

from .model_base import ModelBase


class CollectionBaseEasyList(ModelBase, MutableSequence[ModelBase]):
    """Compatibility model-aware collection with list semantics.

    This preserves the older `CollectionBaseEasyList` API expected by legacy
    tests while keeping the newer `CollectionBase` implementation unchanged.
    """

    def __init__(
        self,
        name: str,
        *args: ModelBase | list[ModelBase],
        unique_name: str | None = None,
        display_name: str | None = None,
    ):
        if display_name is None:
            display_name = name
        super().__init__(unique_name=unique_name, display_name=display_name)
        self._name = name
        self._data: list[ModelBase] = []

        for item in args:
            if isinstance(item, list):
                for nested_item in item:
                    self.append(nested_item)
            else:
                self.append(item)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        self._name = new_name
        self.display_name = new_name

    def _get_key(self, obj: ModelBase) -> str:
        return obj.unique_name

    def _is_duplicate(self, value: ModelBase) -> bool:
        for existing in self._data:
            try:
                if self._get_key(existing) == self._get_key(value):
                    return True
            except AttributeError:
                if existing is value:
                    return True
        return False

    def get_all_variables(self):
        variables = []
        for item in self._data:
            variables.extend(item.get_all_variables())
        return variables

    def get_all_parameters(self):
        parameters = []
        for item in self._data:
            parameters.extend(item.get_all_parameters())
        return parameters

    def get_free_parameters(self):
        parameters = []
        for item in self._data:
            parameters.extend(item.get_free_parameters())
        return parameters

    def __getitem__(self, idx: int | slice | str):
        if isinstance(idx, int):
            return self._data[idx]
        if isinstance(idx, slice):
            return self.__class__(self.name, self._data[idx])
        if isinstance(idx, str):
            unique_name_match = next(
                (item for item in self._data if item.unique_name == idx), None
            )
            if unique_name_match is not None:
                return unique_name_match

            matches = [item for item in self._data if item.name == idx]
            if not matches:
                raise IndexError('Given index does not exist')
            if len(matches) == 1:
                return matches[0]
            return self.__class__(self.name, matches)
        raise TypeError('Index must be an int, slice, or str')

    def __setitem__(self, idx: int | slice, value):
        if isinstance(idx, int):
            if not isinstance(value, ModelBase):
                raise AttributeError('CollectionBaseEasyList can only contain model objects')
            self._data[idx] = value
            return
        if isinstance(idx, slice):
            replacement = list(value)
            if not all(isinstance(item, ModelBase) for item in replacement):
                raise AttributeError('CollectionBaseEasyList can only contain model objects')
            self._data[idx] = replacement
            return
        raise TypeError('Index must be an int or slice')

    def __delitem__(self, idx: int | slice) -> None:
        del self._data[idx]

    def __len__(self) -> int:
        return len(self._data)

    def insert(self, index: int, value: ModelBase) -> None:
        if not isinstance(value, ModelBase):
            raise AttributeError('CollectionBaseEasyList can only contain model objects')
        if self._is_duplicate(value):
            return
        self._data.insert(index, value)

    def sort(self, key=None, reverse: bool = False) -> None:
        self._data.sort(key=key, reverse=reverse)

    def _convert_to_dict(self, in_dict, encoder, skip=None, **kwargs) -> dict:
        if skip is None:
            skip = []
        in_dict['data'] = [
            encoder._convert_to_dict(item, skip=skip, **kwargs) for item in self._data
        ]
        return in_dict

    @classmethod
    def from_dict(cls, obj_dict: dict[str, Any]) -> CollectionBaseEasyList:
        if not SerializerBase._is_serialized_easyscience_object(obj_dict):
            raise ValueError(
                'Input must be a dictionary representing an EasyScience CollectionBaseEasyList object.'
            )
        if obj_dict['@class'] != cls.__name__:
            raise ValueError(
                f'Class name in dictionary does not match the expected class: {cls.__name__}.'
            )

        kwargs = SerializerBase.deserialize_dict(obj_dict)
        data = kwargs.pop('data', [])
        name = kwargs.pop('name')
        return cls(name, data, **kwargs)
