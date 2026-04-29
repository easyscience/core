# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import copy
import warnings
from importlib import import_module
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Type
from typing import cast
from typing import overload

from easyscience.io.serializer_base import SerializerBase

from .easy_list import EasyList
from .new_base import NewBase

CollectionItem = NewBase


class EasyCollection(EasyList[CollectionItem]):
    """Collection built on :class:`EasyList` for ``NewBase`` objects.

    This class keeps the list storage and ``NewBase`` inheritance from
    ``EasyList`` while adding parent-child edges in the global object map.
    """

    _DEFAULT_PROTECTED_TYPES = [NewBase]

    def __init__(
        self,
        *args: CollectionItem | list[CollectionItem],
        protected_types: list[Type[NewBase]] | Type[NewBase] | None = None,
        unique_name: Optional[str] = None,
        display_name: Optional[str] = None,
    ):
        """Initialize the collection.

        :param args: Initial collection items.
        :param protected_types: Types allowed in the collection.
        :param unique_name: Optional unique name for the collection.
        :param display_name: Optional display name for the collection.
        """
        self.user_data: dict = {}
        self._protected_types_explicit = protected_types is not None

        super().__init__(unique_name=unique_name, display_name=display_name)
        self._protected_types = self._normalize_protected_types(protected_types)

        for item in self._flatten_items(args):
            self.append(item)

    @overload
    def __getitem__(self, idx: int) -> CollectionItem: ...
    @overload
    def __getitem__(self, idx: slice) -> EasyCollection: ...
    @overload
    def __getitem__(self, idx: str) -> CollectionItem: ...
    def __getitem__(self, idx: int | slice | str) -> CollectionItem | EasyCollection:
        """Get an item by index, slice, or unique name.

        String lookup returns the single item with the matching ``unique_name``.
        Duplicate ``unique_name`` values are rejected at insertion time, so a
        successful lookup always resolves to exactly one item.
        """
        if isinstance(idx, int):
            return self._data[idx]
        if isinstance(idx, slice):
            return self._new_like(self._data[idx])
        if isinstance(idx, str):
            for item in self._data:
                if self._get_key(item) == idx:
                    return item
            raise KeyError(f'No item with unique name "{idx}" found')
        raise TypeError('Index must be an int, slice, or str')

    @overload
    def __setitem__(self, idx: int, value: CollectionItem) -> None: ...
    @overload
    def __setitem__(self, idx: slice, value: Iterable[CollectionItem]) -> None: ...
    def __setitem__(
        self, idx: int | slice, value: CollectionItem | Iterable[CollectionItem]
    ) -> None:
        """Set collection items and keep graph state synchronized."""
        if isinstance(idx, int):
            # cast(CollectionItem, value) tells the type checker:
            # “for this branch, treat value as one item.”
            self._set_single_item(idx, cast(CollectionItem, value))
            return
        if isinstance(idx, slice):
            if not isinstance(value, Iterable):
                raise TypeError('Value must be an iterable for slice assignment')
            self._set_slice(idx, value)
            return
        raise TypeError('Index must be an int or slice')

    def __delitem__(self, idx: int | slice | str) -> None:
        """Delete collection items and prune graph edges."""
        if isinstance(idx, int):
            item = self._data[idx]
            self._prune_child_relation(item)
            del self._data[idx]
            return
        if isinstance(idx, slice):
            for item in self._data[idx]:
                self._prune_child_relation(item)
            del self._data[idx]
            return
        if isinstance(idx, str):
            # Find the matching unique-name entry so missing string keys raise KeyError.
            for i, item in enumerate(self._data):
                if self._get_key(item) == idx:
                    self._prune_child_relation(item)
                    del self._data[i]
                    return
            raise KeyError(f'No item with unique name "{idx}" found')
        raise TypeError('Index must be an int, slice, or str')

    def insert(self, index: int, value: CollectionItem) -> None:
        """Insert an item and register it as a child of the
        collection.
        """
        if not isinstance(index, int):
            raise TypeError('Index must be an integer')
        self._validate_item(value)
        if self._contains_key(self._get_key(value)):
            warnings.warn(
                f'Item with unique name "{self._get_key(value)}" already in EasyCollection, it will be ignored'
            )
            return
        self._data.insert(index, value)
        self._add_child_relation(value)

    def pop(self, index: int | str = -1) -> CollectionItem:
        """Remove and return an item by index or unique name.

        Extends :class:`collections.abc.MutableSequence`'s int-only ``pop``
        signature to also accept a ``unique_name`` string for symmetry with
        :meth:`__getitem__` and :meth:`__delitem__`.
        """
        if isinstance(index, int):
            item = self._data[index]
            del self[index]
            return item
        if isinstance(index, str):
            # Find the matching unique-name entry so missing string keys raise KeyError.
            for i, item in enumerate(self._data):
                if self._get_key(item) == index:
                    del self[i]
                    return item
            raise KeyError(f'No item with unique name "{index}" found')
        raise TypeError('Index must be an int or str')

    def __contains__(self, item: CollectionItem | str) -> bool:
        """Return whether an item object or unique name exists in the
        collection.
        """
        if isinstance(item, str):
            return self._contains_key(item)
        return item in self._data

    def index(self, value: CollectionItem | str, start: int = 0, stop: int | None = None) -> int:
        """Return the index of an item object or the first item with the
        given unique name.
        """
        if stop is None:
            stop = len(self._data)
        if isinstance(value, str):
            for i in range(start, min(stop, len(self._data))):
                item = self._data[i]
                if self._get_key(item) == value:
                    return i
            raise ValueError(f'{value} is not in EasyCollection')
        return self._data.index(value, start, stop)

    def to_dict(self, skip: Optional[List[str]] = None) -> Dict[str, Any]:
        """Convert the collection to a serialized dictionary."""
        if skip is None:
            skip = []
        dict_repr = self._metadata_dict()
        if not self._default_unique_name and 'unique_name' not in skip:
            dict_repr['unique_name'] = self.unique_name
        if self._display_name is not None and 'display_name' not in skip:
            dict_repr['display_name'] = self._display_name
        if self._protected_types_explicit and 'protected_types' not in skip:
            dict_repr['protected_types'] = [
                {'@module': cls_.__module__, '@class': cls_.__name__}
                for cls_ in self._protected_types
            ]
        dict_repr['data'] = [self._item_to_dict(item, skip=skip) for item in self._data]
        return dict_repr

    def as_dict(self, skip: Optional[List[str]] = None) -> Dict[str, Any]:
        """Compatibility alias for legacy callers."""
        return self.to_dict(skip=skip)

    @classmethod
    def from_dict(cls, obj_dict: Dict[str, Any]) -> EasyCollection:
        """Create an ``EasyCollection`` from a serialized dictionary.

        The payload's ``@class`` field must match ``cls.__name__`` exactly;
        subclass payloads are not accepted through a parent class. Dispatch to
        the correct concrete subclass via :class:`SerializerBase` (or call
        ``from_dict`` on the matching subclass directly) before invoking this.
        """
        if not SerializerBase._is_serialized_easyscience_object(obj_dict):
            raise ValueError(
                'Input must be a dictionary representing an EasyScience EasyCollection object.'
            )
        temp_dict = copy.deepcopy(obj_dict)
        if temp_dict['@class'] != cls.__name__:
            raise ValueError(
                f'Class name in dictionary does not match the expected class: {cls.__name__}.'
            )

        protected_types = cls._deserialize_protected_types(temp_dict.pop('protected_types', None))
        kwargs = SerializerBase.deserialize_dict(temp_dict)
        data = kwargs.pop('data', [])
        return cls(*data, protected_types=protected_types, **kwargs)

    def _new_like(self, data: Iterable[CollectionItem]) -> EasyCollection:
        """Create a same-class collection for slice and duplicate-name
        results.
        """
        return self.__class__(
            list(data),
            protected_types=self._protected_types,
            display_name=self._display_name,
        )

    @classmethod
    def _normalize_protected_types(
        cls, protected_types: list[Type[NewBase]] | Type[NewBase] | None
    ) -> list[Type[NewBase]]:
        """Return protected types as a validated list of ``NewBase``
        subclasses.
        """
        if protected_types is None:
            return list(cls._DEFAULT_PROTECTED_TYPES)
        if isinstance(protected_types, type) and issubclass(protected_types, NewBase):
            protected_types = [protected_types]
        elif isinstance(protected_types, Iterable) and all(
            issubclass(t, NewBase) for t in protected_types
        ):
            protected_types = list(protected_types)
        else:
            raise TypeError(
                'protected_types must be a NewBase subclass or an iterable of NewBase subclasses'
            )
        return protected_types

    @staticmethod
    def _flatten_items(args: tuple[Any, ...]) -> list[CollectionItem]:
        """Flatten positional item lists into the sequence inserted into
        the collection.
        """
        items = []
        for item in args:
            if isinstance(item, list):
                items.extend(item)
            else:
                items.append(item)
        return items

    def _validate_item(self, value: CollectionItem) -> None:
        """Raise if the value is not one of the configured protected
        types.
        """
        if not isinstance(value, tuple(self._protected_types)):
            raise TypeError(f'Items must be one of {self._protected_types}, got {type(value)}')

    def _contains_key(self, key: str) -> bool:
        """Return whether the collection contains an item with the given
        unique name.
        """
        return any(self._get_key(item) == key for item in self._data)

    def _set_single_item(self, idx: int, value: CollectionItem) -> None:
        """Replace one item while preserving unique-name and graph
        invariants.
        """
        self._validate_item(value)
        old_item = self._data[idx]
        value_key = self._get_key(value)
        if value is not old_item and any(
            self._get_key(item) == value_key for item in self._data if item is not old_item
        ):
            # Warn if the new item has the same unique name as another existing item (other than the one being replaced)
            # and skip the update to avoid duplicate keys.
            # Or should we raise here instead?
            warnings.warn(
                f'Item with unique name "{value_key}" already in EasyCollection, it will be ignored'
            )
            return
        self._prune_child_relation(old_item)
        self._data[idx] = value
        self._add_child_relation(value)

    def _set_slice(self, idx: slice, value: Iterable[CollectionItem]) -> None:
        """Replace a slice while preserving length, unique-name, and
        graph invariants.
        """
        replaced = self._data[idx]
        new_values = list(value)
        if len(new_values) != len(replaced):
            raise ValueError(
                'Length of new values must match the length of the slice being replaced'
            )
        for new_value in new_values:
            self._validate_item(new_value)

        existing_keys = {
            self._get_key(item)
            for item in self._data
            if all(item is not replaced_item for replaced_item in replaced)
        }
        seen_batch_keys: set[str] = set()
        # Track unique names already accepted from ``new_values`` so that
        # passing the same item (or two items sharing a unique name) inside one
        # slice assignment is rejected the same way as collisions with items
        # outside the slice.
        for position, new_value in enumerate(new_values):
            key = self._get_key(new_value)
            if key in existing_keys or key in seen_batch_keys:
                warnings.warn(
                    f'Item with unique name "{key}" already in EasyCollection, it will be ignored'
                )
                new_values[position] = replaced[position]
                continue
            seen_batch_keys.add(key)

        for old_item in replaced:
            self._prune_child_relation(old_item)
        self._data[idx] = new_values
        for new_value in new_values:
            self._add_child_relation(new_value)

    def _add_child_relation(self, value: CollectionItem) -> None:
        """Register a collection-child edge in the global object map."""
        # ``get_edges`` returns the list of child ``unique_name`` strings, which
        # is the same key space as ``_get_key`` so the membership check is direct.
        edges = self._global_object.map.get_edges(self)
        if self._get_key(value) not in edges:
            self._global_object.map.add_edge(self, value)
        self._global_object.map.reset_type(value, 'created_internal')

    def _prune_child_relation(self, value: CollectionItem) -> None:
        """Remove the collection-child edge for a removed item."""
        self._global_object.map.prune_vertex_from_edge(self, value)

    def _metadata_dict(self) -> Dict[str, Any]:
        """Return serialization metadata for the concrete collection
        class.
        """
        dict_repr: Dict[str, Any] = {'@module': self.__module__, '@class': self.__class__.__name__}
        try:
            module_version = import_module('easyscience').__version__
            dict_repr['@version'] = f'{module_version}'
        except (AttributeError, ImportError):
            dict_repr['@version'] = None
        return dict_repr

    @staticmethod
    def _item_to_dict(item: CollectionItem, skip: List[str]) -> Any:
        """Serialize one collection item using the best available
        EasyScience encoder.
        """
        if hasattr(item, 'to_dict'):
            return item.to_dict(skip=skip)
        as_dict = getattr(item, 'as_dict', None)
        if callable(as_dict):
            return as_dict(skip=skip)
        return SerializerBase()._recursive_encoder(item, skip=skip)

    @staticmethod
    def _deserialize_protected_types(
        protected_types: list[dict[str, str]] | None,
    ) -> list[Type] | None:
        """Convert serialized protected-type metadata back into Python
        classes.
        """
        if protected_types is None:
            return None
        deserialized_types = []
        for type_dict in protected_types:
            if '@module' not in type_dict or '@class' not in type_dict:
                raise ValueError(
                    'Each protected type must be a serialized EasyScience class with @module and @class keys'
                )
            mod = __import__(type_dict['@module'], globals(), locals(), [type_dict['@class']], 0)
            if not hasattr(mod, type_dict['@class']):
                raise ImportError(
                    f'Could not import class {type_dict["@class"]} from module {type_dict["@module"]}'
                )
            deserialized_types.append(getattr(mod, type_dict['@class']))
        return deserialized_types
