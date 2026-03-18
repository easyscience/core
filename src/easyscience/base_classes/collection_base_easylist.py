#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

from __future__ import annotations

import copy
import warnings
from collections.abc import Iterable
from importlib import import_module
from numbers import Number
from typing import Any
from typing import Optional

from easyscience.io.serializer_base import SerializerBase
from easyscience.io.serializer_dict import SerializerDict

from ..variable.descriptor_base import DescriptorBase
from ..variable.parameter import Parameter
from .based_base import BasedBase
from .easy_list import EasyList
from .new_base import NewBase


class CollectionBase(EasyList):
    """
    EasyList-backed collection with a small compatibility layer for migration.

    The collection delegates storage and MutableSequence behavior to EasyList,
    adding only scientific-parameter aggregation methods and a thin compatibility
    layer for existing callers.
    """

    # Base types that items in this collection must be instances of when no
    # custom ``protected_types`` are supplied by the caller.  The validation
    # check in ``_validate_item`` uses this list to reject plain Python objects
    # that are not part of the EasyScience type hierarchy.
    # ``BasedBase`` is only kept for backwards compatibility.
    _DEFAULT_PROTECTED_TYPES = (DescriptorBase, BasedBase, NewBase)

    # Mapping checked by ``SerializerBase._convert_to_dict`` to
    # decide how to serialise each constructor argument.  ``None``
    # tells the serialiser to skip that attribute entirely,
    # a callable value would be invoked to produce the serialised form.
    # ``interface`` should never be persistent and it will soon be removed.
    _REDIRECT = {'interface': None}

    def __init__(
        self,
        *items: Any,
        name: Optional[str] = None,
        protected_types: type | Iterable[type] | None = None,
        unique_name: Optional[str] = None,
        display_name: Optional[str] = None,
        interface: Any = None,  # legacy, should be None and will soon be removed
        data: Optional[Iterable[Any]] = None,
    ):
        """Create a new collection of EasyScience objects.

        Items can be supplied as positional arguments or via the *data*
        iterable.  Both sources are merged in order.

        If the first positional argument is a string and *name* is not given,
        it is consumed as the collection name.

        :param items: EasyScience objects to include in the collection.
        :param name: Human-readable name for the collection.
        :param protected_types: Allowed item types.  Defaults to
            ``_DEFAULT_PROTECTED_TYPES``.
        :param unique_name: Machine-friendly unique identifier.
        :param display_name: Display label; defaults to *name*.
        :param interface: Reserved internal attribute — must be ``None``.
        :param data: Additional iterable of items to append.
        :raises AttributeError: If *interface* is not ``None`` or an item
            fails type validation.
        """
        if items and isinstance(items[0], str) and name is None:
            name = items[0]
            items = items[1:]

        if display_name is None and name is not None:
            display_name = name

        super().__init__(unique_name=unique_name, display_name=display_name)

        if interface is not None:
            raise AttributeError(
                'Given kwarg: `interface`, is an internal attribute. Please rename.'
            )

        self._protected_types = self._normalize_protected_types(protected_types)
        self._name = name if name is not None else self.display_name
        self.user_data: dict[str, Any] = {}
        self.interface = None

        all_items = self._collect_items(items, data=data)
        for item in all_items:
            try:
                self._validate_item(item)
            except TypeError as exc:
                raise AttributeError(
                    'A collection can only be formed from easyscience objects.'
                ) from exc
            if item in self:
                warnings.warn(
                    f'Item with unique name "{self._get_key(item)}" already in CollectionBase, it will be ignored'
                )
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

    # --- Minimal overrides (compatibility shims) ---

    def __getitem__(self, idx: int | slice | str) -> Any:
        """Retrieve items by integer index, slice, unique-name key, or display name.

        String lookup first tries the EasyList key (unique_name), then falls
        back to matching on the item's *name* attribute.  If multiple items
        share the same name a new ``CollectionBase`` containing all matches is
        returned.
        """
        if isinstance(idx, bool):
            raise TypeError('Boolean indexing is not supported at the moment')
        if isinstance(idx, slice):
            return self._clone_with_items(self._data[idx])
        if isinstance(idx, str):
            try:
                return super().__getitem__(idx)
            except KeyError:
                pass
            name_matches = [item for item in self._data if getattr(item, 'name', None) == idx]
            if len(name_matches) == 1:
                return name_matches[0]
            if len(name_matches) > 1:
                return self._clone_with_items(name_matches)
            raise KeyError(f'No item with key or name "{idx}" found')
        return super().__getitem__(idx)

    def __setitem__(self, idx: int | slice, value: Any) -> None:
        """Set an item by index.

        When *value* is a plain number and the existing item has a ``value``
        attribute, the number is assigned to ``item.value`` (in-place update).
        Otherwise the item is replaced via the EasyList, which
        enforces type validation.
        """
        if isinstance(idx, int) and isinstance(value, Number):
            item = self[idx]
            if not hasattr(item, 'value'):
                raise NotImplementedError(
                    'At the moment only numerical values or EasyScience objects can be set.'
                )
            item.value = value
            return
        try:
            super().__setitem__(idx, value)
        except TypeError as exc:
            raise NotImplementedError(
                'At the moment only numerical values or EasyScience objects can be set.'
            ) from exc

    def insert(self, index: int, value: Any) -> None:
        """Insert *value* before *index*, validating it against protected types."""
        try:
            super().insert(index, value)
        except TypeError as exc:
            raise AttributeError(
                'Only EasyScience objects can be put into an EasyScience group'
            ) from exc

    def __repr__(self) -> str:
        return f'{self.__class__.__name__} `{self.name}` of length {len(self)}'

    def sort(self, key=None, reverse: bool = False, mapping=None) -> None:
        """Sort items in place.

        :param key: Single-argument function used to extract a comparison key.
        :param reverse: If ``True``, sort in descending order.
        :param mapping: Deprecated alias for *key*.
        """
        if mapping is not None:
            if key is not None:
                raise TypeError('Use either key or mapping, not both')
            warnings.warn(
                'sort(mapping=...) is deprecated; use sort(key=...) instead', DeprecationWarning
            )
            key = mapping
        super().sort(key=key, reverse=reverse)

    # --- Parameter/variable aggregation ---

    def get_all_variables(self) -> list[DescriptorBase]:
        """Return all descriptors in this collection, recursing into nested items."""
        variables: list[DescriptorBase] = []
        for item in self._data:
            if isinstance(item, DescriptorBase):
                variables.append(item)
            elif hasattr(item, 'get_all_variables'):
                variables.extend(item.get_all_variables())
        return variables

    def get_all_parameters(self) -> list[Parameter]:
        """Return all parameters in this collection, recursing into nested items.

        Each parameter appears at most once (deduplicated by identity).
        """
        parameters: list[Parameter] = []
        seen = set()
        for item in self._data:
            if isinstance(item, Parameter):
                parameters.append(item)
                seen.add(id(item))
                continue
            if hasattr(item, 'get_all_parameters'):
                for parameter in item.get_all_parameters():
                    if id(parameter) not in seen:
                        parameters.append(parameter)
                        seen.add(id(parameter))
                continue
            if hasattr(item, 'get_parameters'):
                for parameter in item.get_parameters():
                    if id(parameter) not in seen:
                        parameters.append(parameter)
                        seen.add(id(parameter))
                continue
            if hasattr(item, 'get_all_variables'):
                for variable in item.get_all_variables():
                    if isinstance(variable, Parameter) and id(variable) not in seen:
                        parameters.append(variable)
                        seen.add(id(variable))
        return parameters

    def get_parameters(self) -> list[Parameter]:
        """Alias for :meth:`get_all_parameters`."""
        return self.get_all_parameters()

    def get_fittable_parameters(self) -> list[Parameter]:
        """Return all independent (fittable) parameters."""
        return [parameter for parameter in self.get_all_parameters() if parameter.independent]

    def get_free_parameters(self) -> list[Parameter]:
        """Return all fittable parameters that are not fixed."""
        return [parameter for parameter in self.get_fittable_parameters() if not parameter.fixed]

    def get_fit_parameters(self) -> list[Parameter]:
        """Legacy alias for :meth:`get_free_parameters`."""
        return self.get_free_parameters()

    @property
    def data(self) -> tuple[Any, ...]:
        """Read-only snapshot of the collection items as a tuple."""
        return tuple(self._data)

    # --- Serialization ---

    def as_dict(self, skip: Optional[list[str]] = None) -> dict[str, Any]:
        """Legacy. Serialize to a dict, always excluding ``unique_name``."""
        if skip is None:
            skip = []
        if 'unique_name' not in skip:
            skip = [*skip, 'unique_name']
        return self.to_dict(skip=skip)

    def encode(self, skip: Optional[list[str]] = None, encoder=None, **kwargs: Any) -> Any:
        """Legacy. Encode the collection using the given encoder (default: ``SerializerDict``)."""
        if encoder is None:
            encoder = SerializerDict
        return encoder().encode(self, skip=skip, **kwargs)

    @classmethod
    def decode(cls, obj: Any, decoder=None) -> Any:
        """Reconstruct a ``CollectionBase`` from a previously encoded object."""
        if decoder is None or decoder is SerializerDict:
            return cls.from_dict(obj)
        return decoder.decode(obj)

    def to_dict(self, skip: Optional[list[str]] = None) -> dict[str, Any]:
        """Full serialization including ``@module``, ``@class``, and ``@version`` metadata.

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
        dict_repr['data'] = [self._serialize_item(item, skip=skip) for item in self._data]
        return dict_repr

    @classmethod
    def from_dict(cls, obj_dict: dict[str, Any]) -> CollectionBase:
        """Reconstruct a ``CollectionBase`` from a dict produced by :meth:`to_dict`.

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

    def _convert_to_dict(
        self,
        in_dict: dict[str, Any],
        encoder: Any,
        skip: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Legacy. Hook used by ``SerializerBase`` to populate *in_dict* with collection data."""
        if skip is None:
            skip = []
        if 'name' not in skip:
            in_dict['name'] = self.name
        if (
            self._display_name is not None
            and self._display_name != self.name
            and 'display_name' not in skip
        ):
            in_dict['display_name'] = self._display_name
        in_dict['data'] = [
            encoder._convert_to_dict(item, skip=skip, **kwargs) for item in self._data
        ]
        return in_dict

    @staticmethod
    def _deserialize_protected_types(protected_types: list[dict[str, str]]) -> list[type]:
        """Resolve serialized ``{@module, @class}`` dicts back to live type objects."""
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
        """Create a shallow copy of this collection containing the given *items*."""
        return self.__class__(
            *list(items),
            name=self.name,
            protected_types=list(self._protected_types),
            display_name=self._display_name,
        )

    # --- Compatibility surface ---

    def __dir__(self) -> Iterable[str]:
        # Names that exist on the class but should not be shown to users.
        # These are internal/new-API names
        hidden = {
            'display_name',
            'get_all_parameters',
            'get_all_variables',
            'get_fittable_parameters',
            'get_free_parameters',
            'to_dict',
        }
        # Names that the old BasedBase/BaseObj API exposed and that
        # downstream code may rely on for introspection
        legacy = {
            'append',
            'as_dict',
            'clear',
            'constraints',
            'count',
            'data',
            'decode',
            'encode',
            'extend',
            'from_dict',
            'generate_bindings',
            'get_fit_parameters',
            'get_parameters',
            'index',
            'insert',
            'interface',
            'name',
            'pop',
            'remove',
            'reverse',
            'sort',
            'switch_interface',
            'unique_name',
            'user_data',
        }
        public_names = {name for name in dir(self.__class__) if not name.startswith('_')}
        return sorted((public_names | legacy) - hidden)

    @property
    def constraints(self) -> list[Any]:
        """Compatibility stub — always returns an empty list."""
        return []

    def generate_bindings(self) -> None:
        """Compatibility stub — requires ``interface`` to be set."""
        if self.interface is None:
            raise AttributeError(
                'Interface error for generating bindings. `interface` has to be set.'
            )

    def switch_interface(self, new_interface_name: str) -> None:
        """Compatibility stub — requires ``interface`` to be set."""
        if self.interface is None:
            raise AttributeError(
                'Interface error for generating bindings. `interface` has to be set.'
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
        """Coerce *protected_types* into a list, falling back to the class default."""
        if protected_types is None:
            return list(self._DEFAULT_PROTECTED_TYPES)
        if isinstance(protected_types, type):
            return [protected_types]
        if isinstance(protected_types, Iterable):
            normalized = list(protected_types)
            if all(isinstance(item, type) for item in normalized):
                return normalized
        raise TypeError('protected_types must be a type or an iterable of types')

    def _serialize_item(self, item: Any, skip: Optional[list[str]] = None) -> dict[str, Any]:
        """Serialize a single item via its ``to_dict`` or ``as_dict`` method."""
        if hasattr(item, 'to_dict'):
            return item.to_dict()
        if hasattr(item, 'as_dict'):
            return item.as_dict(skip=skip)
        raise TypeError(f'Unable to serialize item of type {type(item)}')

    @staticmethod
    def _deserialize_item(item: Any) -> Any:
        """Deserialize a single item dict back into an EasyScience object."""
        if not SerializerBase._is_serialized_easyscience_object(item):
            return SerializerBase._deserialize_value(item)

        normalized_item = copy.deepcopy(item)
        normalized_item.pop('unique_name', None)
        return SerializerBase._deserialize_value(normalized_item)

    def _validate_item(self, item: Any) -> None:
        """Raise ``TypeError`` if *item* is not an instance of a protected type."""
        if not isinstance(item, tuple(self._protected_types)):
            raise TypeError(f'Items must be one of {self._protected_types}, got {type(item)}')
