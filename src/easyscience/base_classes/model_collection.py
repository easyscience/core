#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

from __future__ import annotations

from collections.abc import MutableSequence
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Iterable
from typing import List
from typing import Optional
from typing import TypeVar
from typing import Union
from typing import overload

from ..variable import Parameter
from .new_base import NewBase

if TYPE_CHECKING:
    from ..fitting.calculators import InterfaceFactoryTemplate

T = TypeVar('T', bound=NewBase)


class ModelCollection(NewBase, MutableSequence[T]):
    """
    A collection class for NewBase/ModelBase objects.
    This provides list-like functionality while maintaining EasyScience features
    like serialization and interface bindings.
    """

    def __init__(
        self,
        name: str,
        *args: NewBase,
        interface: Optional[InterfaceFactoryTemplate] = None,
        unique_name: Optional[str] = None,
        display_name: Optional[str] = None,
    ):
        """
        Initialize the ModelCollection.

        :param name: Name of this collection
        :param args: Initial items to add to the collection
        :param interface: Optional interface for bindings
        :param unique_name: Optional unique name for the collection
        :param display_name: Optional display name for the collection
        """
        super().__init__(unique_name=unique_name, display_name=display_name)
        self._name = name
        self._data: List[NewBase] = []
        self._interface: Optional[InterfaceFactoryTemplate] = None

        # Add initial items
        for item in args:
            if isinstance(item, list):
                for sub_item in item:
                    self._add_item(sub_item)
            else:
                self._add_item(item)

        # Set interface after adding items so it propagates
        if interface is not None:
            self.interface = interface

    def _add_item(self, item: Any) -> None:
        """Add an item to the collection and set up graph edges."""
        if not isinstance(item, NewBase):
            raise TypeError(f'Items must be NewBase objects, got {type(item)}')
        self._data.append(item)
        self._global_object.map.add_edge(self, item)
        self._global_object.map.reset_type(item, 'created_internal')
        if self._interface is not None and hasattr(item, 'interface'):
            setattr(item, 'interface', self._interface)

    def _remove_item(self, item: NewBase) -> None:
        """Remove an item from the collection and clean up graph edges."""
        self._global_object.map.prune_vertex_from_edge(self, item)

    @property
    def name(self) -> str:
        """Get the name of the collection."""
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        """Set the name of the collection."""
        self._name = new_name

    @property
    def interface(self) -> Optional[InterfaceFactoryTemplate]:
        """Get the current interface of the collection."""
        return self._interface

    @interface.setter
    def interface(self, new_interface: Optional[InterfaceFactoryTemplate]) -> None:
        """Set the interface and propagate to all items."""
        self._interface = new_interface
        for item in self._data:
            if hasattr(item, 'interface'):
                setattr(item, 'interface', new_interface)

    # MutableSequence abstract methods

    # Use @overload to provide precise type hints for different __getitem__ argument types
    @overload
    def __getitem__(self, idx: int) -> T: ...
    @overload
    def __getitem__(self, idx: slice) -> 'ModelCollection[T]': ...
    @overload
    def __getitem__(self, idx: str) -> T: ...

    def __getitem__(self, idx: Union[int, slice, str]) -> Union[T, 'ModelCollection[T]']:
        """
        Get an item by index, slice, or name.

        :param idx: Index, slice, or name of the item
        :return: The item or a new collection for slices
        """
        if isinstance(idx, slice):
            start, stop, step = idx.indices(len(self))
            return self.__class__(self._name, *[self._data[i] for i in range(start, stop, step)])
        if isinstance(idx, str):
            # Search by name
            for item in self._data:
                if hasattr(item, 'name') and getattr(item, 'name') == idx:
                    return item  # type: ignore[return-value]
                if hasattr(item, 'unique_name') and item.unique_name == idx:
                    return item  # type: ignore[return-value]
            raise KeyError(f'No item with name "{idx}" found')
        return self._data[idx]  # type: ignore[return-value]

    @overload
    def __setitem__(self, idx: int, value: T) -> None: ...
    @overload
    def __setitem__(self, idx: slice, value: Iterable[T]) -> None: ...

    def __setitem__(self, idx: Union[int, slice], value: Union[T, Iterable[T]]) -> None:
        """
        Set an item at an index.

        :param idx: Index to set
        :param value: New value
        """
        if isinstance(idx, slice):
            # Handle slice assignment
            values = list(value)  # type: ignore[arg-type]
            # Remove old items
            start, stop, step = idx.indices(len(self))
            for i in range(start, stop, step):
                self._remove_item(self._data[i])
            # Set new items
            self._data[idx] = values  # type: ignore[assignment]
            for v in values:
                self._global_object.map.add_edge(self, v)
                self._global_object.map.reset_type(v, 'created_internal')
                if self._interface is not None and hasattr(v, 'interface'):
                    setattr(v, 'interface', self._interface)
        else:
            if not isinstance(value, NewBase):
                raise TypeError(f'Items must be NewBase objects, got {type(value)}')

            old_item = self._data[idx]
            self._remove_item(old_item)

            self._data[idx] = value  # type: ignore[assignment]
            self._global_object.map.add_edge(self, value)
            self._global_object.map.reset_type(value, 'created_internal')
            if self._interface is not None and hasattr(value, 'interface'):
                setattr(value, 'interface', self._interface)

    @overload
    def __delitem__(self, idx: int) -> None: ...
    @overload
    def __delitem__(self, idx: slice) -> None: ...
    @overload
    def __delitem__(self, idx: str) -> None: ...

    def __delitem__(self, idx: Union[int, slice, str]) -> None:
        """
        Delete an item by index, slice, or name.

        :param idx: Index, slice, or name of item to delete
        """
        if isinstance(idx, slice):
            start, stop, step = idx.indices(len(self))
            indices = list(range(start, stop, step))
            # Remove in reverse order to maintain indices
            for i in reversed(indices):
                item = self._data[i]
                self._remove_item(item)
                del self._data[i]
        elif isinstance(idx, str):
            for i, item in enumerate(self._data):
                if hasattr(item, 'name') and getattr(item, 'name') == idx:
                    idx = i
                    break
                if hasattr(item, 'unique_name') and item.unique_name == idx:
                    idx = i
                    break
            else:
                raise KeyError(f'No item with name "{idx}" found')

            item = self._data[idx]
            self._remove_item(item)
            del self._data[idx]
        else:
            item = self._data[idx]
            self._remove_item(item)
            del self._data[idx]

    def __len__(self) -> int:
        """Return the number of items in the collection."""
        return len(self._data)

    def insert(self, index: int, value: T) -> None:
        """
        Insert an item at an index.

        :param index: Index to insert at
        :param value: Item to insert
        """
        if not isinstance(value, NewBase):
            raise TypeError(f'Items must be NewBase objects, got {type(value)}')

        self._data.insert(index, value)  # type: ignore[arg-type]
        self._global_object.map.add_edge(self, value)
        self._global_object.map.reset_type(value, 'created_internal')
        if self._interface is not None and hasattr(value, 'interface'):
            setattr(value, 'interface', self._interface)

    # Additional utility methods

    @property
    def data(self) -> tuple:
        """Return the data as a tuple."""
        return tuple(self._data)

    def sort(self, mapping: Callable[[T], Any], reverse: bool = False) -> None:
        """
        Sort the collection according to the given mapping.

        :param mapping: Mapping function to sort by
        :param reverse: Whether to reverse the sort
        """
        self._data.sort(key=mapping, reverse=reverse)  # type: ignore[arg-type]

    def __repr__(self) -> str:
        return f'{self.__class__.__name__} `{self._name}` of length {len(self)}'

    def __iter__(self) -> Any:
        return iter(self._data)

    # Serialization support

    def _convert_to_dict(self, in_dict: dict, encoder: Any, skip: Optional[List[str]] = None, **kwargs: Any) -> dict:
        """Convert the collection to a dictionary for serialization."""
        if skip is None:
            skip = []
        d: dict = {}
        if hasattr(self, '_modify_dict'):
            d = self._modify_dict(skip=skip, **kwargs)  # type: ignore[attr-defined]
        in_dict['data'] = [encoder._convert_to_dict(item, skip=skip, **kwargs) for item in self._data]
        return {**in_dict, **d}

    def get_all_variables(self) -> List[Any]:
        """Get all variables from all items in the collection."""
        variables: List[Any] = []
        for item in self._data:
            if hasattr(item, 'get_all_variables'):
                variables.extend(item.get_all_variables())  # type: ignore[attr-defined]
        return variables

    def get_all_parameters(self) -> List[Any]:
        """Get all parameters from all items in the collection."""
        return [var for var in self.get_all_variables() if isinstance(var, Parameter)]

    def get_fit_parameters(self) -> List[Any]:
        """Get all fittable parameters from all items in the collection."""
        parameters: List[Any] = []
        for item in self._data:
            if hasattr(item, 'get_fit_parameters'):
                parameters.extend(item.get_fit_parameters())  # type: ignore[attr-defined]
        return parameters
