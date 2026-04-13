#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

from __future__ import annotations

import copy
import warnings
from collections.abc import Iterable
from collections.abc import MutableSequence
from importlib import import_module
from numbers import Number
from typing import Any
from typing import Optional

from easyscience.io.serializer_base import SerializerBase

from ..variable.descriptor_base import DescriptorBase
from .model_base import ModelBase


class CollectionBase(ModelBase, MutableSequence):
    """A ModelBase-backed collection that can contain only models and
    other collections.

    Inherits from ``ModelBase`` (identity, serialisation, parameter aggregation)
    and ``MutableSequence`` (list-like interface).  Parameter aggregation
    methods are overridden to recurse into the contained items rather than
    using ``dir()`` introspection.
    """

    _DEFAULT_PROTECTED_TYPES = (ModelBase,)

    def __init__(
        self,
        *items: Any,
        name: Optional[str] = None,
        protected_types: type | Iterable[type] | None = None,
        unique_name: Optional[str] = None,
        display_name: Optional[str] = None,
        data: Optional[Iterable[Any]] = None,
    ):
        """Create a new collection of model objects.

        Items can be supplied as positional arguments or via the *data*
        iterable.  Both sources are merged in order.

        If the first positional argument is a string and *name* is not given,
        it is consumed as the collection name.

        :param items: Model objects to include in the collection.
        :param name: Human-readable name for the collection.
        :param protected_types: Allowed item types.  Defaults to
            ``_DEFAULT_PROTECTED_TYPES``.
        :param unique_name: Machine-friendly unique identifier.
        :param display_name: Display label; defaults to *name*.
        :param data: Additional iterable of items to append.
        :raises AttributeError: If an item fails type validation.
        """
        if items and isinstance(items[0], str) and name is None:
            name = items[0]
            items = items[1:]

        if display_name is None and name is not None:
            display_name = name

        super().__init__(unique_name=unique_name, display_name=display_name)

        self._protected_types = self._normalize_protected_types(protected_types)
        self._name = name if name is not None else self.display_name
        self._data: list[Any] = []

        all_items = self._collect_items(items, data=data)
        for item in all_items:
            try:
                self._validate_item(item)
            except TypeError as exc:
                raise AttributeError(
                    'A collection can only be formed from model objects.'
                ) from exc
            if item in self:
                continue
            self._data.append(item)

    @property
    def name(self) -> str:
        """Human-readable name of the collection."""
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        """Set the collection name and sync *display_name*."""
        if not isinstance(new_name, str):
            raise TypeError('Name must be a string')
        self._name = new_name
        self.display_name = new_name

    # --- MutableSequence abstract methods ---

    def __getitem__(self, idx: int | slice | str) -> Any:
        """Retrieve items by integer index, slice, unique-name key, or
        display name.

        String lookup first tries the unique_name, then falls back to matching
        on the item's *name* attribute.  If multiple items share the same name
        a new ``CollectionBase`` containing all matches is returned.
        """
        if isinstance(idx, bool):
            raise TypeError('Boolean indexing is not supported at the moment')
        if isinstance(idx, int):
            return self._data[idx]
        if isinstance(idx, slice):
            return self._clone_with_items(self._data[idx])
        if isinstance(idx, str):
            element = next((r for r in self._data if self._get_key(r) == idx), None)
            if element is not None:
                return element
            name_matches = [item for item in self._data if getattr(item, 'name', None) == idx]
            if len(name_matches) == 1:
                return name_matches[0]
            if len(name_matches) > 1:
                return self._clone_with_items(name_matches)
            raise KeyError(f'No item with key or name "{idx}" found')
        raise TypeError('Index must be an int, slice, or str')

    def __setitem__(self, idx: int | slice, value: Any) -> None:
        """Set an item by index.

        When *value* is a plain number and the existing item has a ``value``
        attribute, the number is assigned to ``item.value`` (in-place update).
        Otherwise the item is replaced after type validation.
        """
        if isinstance(idx, int) and isinstance(value, Number):
            item = self[idx]
            if not hasattr(item, 'value'):
                raise AttributeError(
                    f'Item at index {idx} does not have a `value` attribute.'
                )
            item.value = value
            return
        if isinstance(idx, int):
            self._validate_item(value)
            if value is not self._data[idx] and value in self:
                warnings.warn(
                    f'Item with unique name "{self._get_key(value)}" already in collection, it will be ignored'
                )
                return
            self._data[idx] = value
            return
        if isinstance(idx, slice):
            if not isinstance(value, Iterable):
                raise TypeError('Value must be an iterable for slice assignment')
            replaced = self._data[idx]
            new_values = list(value)
            for i, v in enumerate(new_values):
                self._validate_item(v)
                if v in self and (i >= len(replaced) or replaced[i] is not v):
                    warnings.warn(
                        f'Item with unique name "{self._get_key(v)}" already in collection, it will be ignored'
                    )
                    if i < len(replaced):
                        new_values[i] = replaced[i]
            self._data[idx] = new_values
            return
        raise TypeError('Index must be an int or slice')

    def __delitem__(self, idx: int | slice | str) -> None:
        """Delete an item by index, slice, unique_name, or name."""
        if isinstance(idx, (int, slice)):
            del self._data[idx]
        elif isinstance(idx, str):
            for i, item in enumerate(self._data):
                if self._get_key(item) == idx:
                    del self._data[i]
                    return
            for i, item in enumerate(self._data):
                if getattr(item, 'name', None) == idx:
                    del self._data[i]
                    return
            raise KeyError(f'No item with key or name "{idx}" found')
        else:
            raise TypeError('Index must be an int, slice, or str')

    def __len__(self) -> int:
        """Return the number of items in the collection."""
        return len(self._data)

    def insert(self, index: int, value: Any) -> None:
        """Insert *value* before *index*, validating it against
        protected types.
        """
        if not isinstance(index, int):
            raise TypeError('Index must be an integer')
        try:
            self._validate_item(value)
        except TypeError as exc:
            raise AttributeError('Only model objects can be put into a CollectionBase') from exc
        if value in self:
            warnings.warn(
                f'Item with unique name "{self._get_key(value)}" already in collection, it will be ignored'
            )
            return
        self._data.insert(index, value)

    # --- Additional list-like methods ---

    def __contains__(self, item: Any) -> bool:
        """Check membership by identity, unique_name, or name."""
        if isinstance(item, str):
            if any(self._get_key(r) == item for r in self._data):
                return True
            return any(getattr(r, 'name', None) == item for r in self._data)
        return item in self._data

    def __repr__(self) -> str:
        return f'{self.__class__.__name__} `{self.name}` of length {len(self)}'

    def sort(self, key=None, reverse: bool = False) -> None:
        """Sort items in place.

        :param key: Single-argument function used to extract a comparison key.
        :param reverse: If ``True``, sort in descending order.
        """
        self._data.sort(key=key, reverse=reverse)

    def index(self, value: Any, start: int = 0, stop: int | None = None) -> int:
        if stop is None:
            stop = len(self._data)
        if isinstance(value, str):
            for i in range(start, min(stop, len(self._data))):
                if self._get_key(self._data[i]) == value:
                    return i
            raise ValueError(f'{value} is not in CollectionBase')
        return self._data.index(value, start, stop)

    def pop(self, index: int | str = -1) -> Any:
        """Remove and return an item at the given index,
        unique_name, or name.
        """
        if isinstance(index, int):
            return self._data.pop(index)
        if isinstance(index, str):
            for i, item in enumerate(self._data):
                if self._get_key(item) == index:
                    return self._data.pop(i)
            for i, item in enumerate(self._data):
                if getattr(item, 'name', None) == index:
                    return self._data.pop(i)
            raise KeyError(f'No item with key or name "{index}" found')
        raise TypeError('Index must be an int or str')

    @staticmethod
    def _get_key(obj: Any) -> str:
        """Return the unique name used as the item key."""
        return obj.unique_name

    # --- Parameter/variable aggregation (override ModelBase) ---

    def get_all_variables(self) -> list[DescriptorBase]:
        """Return all descriptors in this collection, recursing into
        nested items.

        Each variable appears at most once (deduplicated by identity).
        """
        variables: list[DescriptorBase] = []
        seen: set[int] = set()
        for item in self._data:
            if hasattr(item, 'get_all_variables'):
                for variable in item.get_all_variables():
                    if id(variable) not in seen:
                        variables.append(variable)
                        seen.add(id(variable))
        return variables

    @property
    def data(self) -> tuple[Any, ...]:
        """Read-only snapshot of the collection items as a tuple."""
        return tuple(self._data)

    def to_dict(self, skip: Optional[list[str]] = None) -> dict[str, Any]:
        """Full serialization including ``@module``, ``@class``, and
        ``@version`` metadata.

        :param skip: List of attribute names to exclude from the output.
        """
        if skip is None:
            skip = []

        try:
            parent_module = self.__module__.split('.')[0]
            module_version = import_module(parent_module).__version__
        except (AttributeError, ImportError):
            module_version = None

        dict_repr: dict[str, Any] = {
            '@module': self.__module__,
            '@class': self.__class__.__name__,
            '@version': module_version,
        }

        if 'name' not in skip:
            dict_repr['name'] = self.name
        if (
            'display_name' not in skip
            and self._display_name is not None
            and self._display_name != self.name
        ):
            dict_repr['display_name'] = self._display_name
        if 'unique_name' not in skip:
            dict_repr['unique_name'] = self.unique_name
        if (
            self._protected_types != list(self._DEFAULT_PROTECTED_TYPES)
            and 'protected_types' not in skip
        ):
            dict_repr['protected_types'] = [
                {'@module': cls_.__module__, '@class': cls_.__name__}
                for cls_ in self._protected_types
            ]
        dict_repr['data'] = [item.to_dict(skip=skip) for item in self._data]
        return dict_repr

    @classmethod
    def from_dict(cls, obj_dict: dict[str, Any]) -> CollectionBase:
        """Reconstruct a ``CollectionBase`` from a dict produced by
        :meth:`to_dict`.

        :param obj_dict: Dictionary containing ``@module``, ``@class``, and ``data`` keys.
        :raises ValueError: If the dictionary structure or class name is invalid.
        """
        if not isinstance(obj_dict, dict) or '@class' not in obj_dict or '@module' not in obj_dict:
            raise ValueError(
                'Input must be a dictionary representing an EasyScience CollectionBase object.'
            )
        accepted_names = {
            base.__name__ for base in cls.__mro__ if issubclass(base, CollectionBase)
        }
        if obj_dict['@class'] not in accepted_names:
            raise ValueError(
                f'Class name in dictionary does not match the expected class: {cls.__name__}.'
            )

        temp_dict = copy.deepcopy(obj_dict)
        protected_types = temp_dict.pop('protected_types', None)
        if protected_types is not None:
            protected_types = cls._deserialize_protected_types(protected_types)

        raw_data = temp_dict.pop('data', [])
        kwargs = SerializerBase.deserialize_dict(temp_dict)
        data = [cls._deserialize_item(item) for item in raw_data]
        name = kwargs.pop('name', None)
        kwargs.pop('unique_name', None)
        return cls(*data, name=name, protected_types=protected_types, **kwargs)

    @staticmethod
    def _deserialize_protected_types(protected_types: list[dict[str, str]]) -> list[type]:
        """Resolve serialized ``{@module, @class}`` dicts back to live
        type objects.
        """
        deserialized_types: list[type] = []
        for type_dict in protected_types:
            if '@module' not in type_dict or '@class' not in type_dict:
                raise ValueError('Each protected type must contain @module and @class keys')
            module = __import__(
                type_dict['@module'], globals(), locals(), [type_dict['@class']], 0
            )
            deserialized_types.append(getattr(module, type_dict['@class']))
        return deserialized_types

    def _clone_with_items(self, items: Iterable[Any]) -> CollectionBase:
        """Create a shallow copy of this collection containing the given
        *items*.
        """
        return self.__class__(
            *list(items),
            name=self.name,
            protected_types=list(self._protected_types),
            display_name=self._display_name,
        )

    # --- Internal helpers ---

    def _collect_items(
        self,
        items: tuple[Any, ...],
        data: Optional[Iterable[Any]] = None,
    ) -> list[Any]:
        """Merge positional *items* and *data* into a flat list.

        Lists inside *items* are flattened one level.
        """
        collected: list[Any] = []
        for item in items:
            if isinstance(item, list):
                collected.extend(item)
            else:
                collected.append(item)
        if data is not None:
            collected.extend(data)
        return collected

    def _normalize_protected_types(
        self, protected_types: type | Iterable[type] | None
    ) -> list[type]:
        """Coerce *protected_types* into a list, falling back to the
        class default.
        """
        if protected_types is None:
            return list(self._DEFAULT_PROTECTED_TYPES)
        if isinstance(protected_types, type) and issubclass(protected_types, ModelBase):
            return [protected_types]
        if isinstance(protected_types, Iterable):
            normalized = list(protected_types)
            if all(isinstance(item, type) and issubclass(item, ModelBase) for item in normalized):
                return normalized
        raise TypeError(
            'protected_types must be a ModelBase type or an iterable of ModelBase types'
        )

    @staticmethod
    def _deserialize_item(item: Any) -> Any:
        """Deserialize a single item dict back into an EasyScience
        object.
        """
        if not SerializerBase._is_serialized_easyscience_object(item):
            return SerializerBase._deserialize_value(item)

        normalized_item = copy.deepcopy(item)
        normalized_item.pop('unique_name', None)
        return SerializerBase._deserialize_value(normalized_item)

    def _validate_item(self, item: Any) -> None:
        """Raise ``TypeError`` if *item* is not an instance of a
        protected type.
        """
        if not isinstance(item, tuple(self._protected_types)):
            raise TypeError(f'Items must be one of {self._protected_types}, got {type(item)}')
