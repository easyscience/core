from __future__ import annotations

#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience
from inspect import getfullargspec
from typing import TYPE_CHECKING
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set

from easyscience import global_object

from ..io import SerializerComponent
from ..variable import Parameter
from ..variable.descriptor_base import DescriptorBase

if TYPE_CHECKING:
    from ..fitting.calculators import InterfaceFactoryTemplate


class BasedBase(SerializerComponent):
    __slots__ = ['_name', '_global_object', 'user_data', '_kwargs']

    _REDIRECT = {}

    def __init__(self, name: str, interface: Optional[InterfaceFactoryTemplate] = None, unique_name: Optional[str] = None):
        self._global_object = global_object
        if unique_name is None:
            unique_name = self._global_object.generate_unique_name(self.__class__.__name__)
        self._unique_name = unique_name
        self._name = name
        self._global_object.map.add_vertex(self, obj_type='created')
        self.interface = interface
        self.user_data: dict = {}

    @property
    def _arg_spec(self) -> Set[str]:
        base_cls = getattr(self, '__old_class__', self.__class__)
        spec = getfullargspec(base_cls.__init__)
        names = set(spec.args[1:])
        return names

    def __reduce__(self):
        """
        Make the class picklable.
        Due to the nature of the dynamic class definitions special measures need to be taken.

        :return: Tuple consisting of how to make the object
        :rtype: tuple
        """
        state = self.encode()
        cls = getattr(self, '__old_class__', self.__class__)
        return cls.from_dict, (state,)

    @property
    def unique_name(self) -> str:
        """Get the unique name of the object."""
        return self._unique_name

    @unique_name.setter
    def unique_name(self, new_unique_name: str):
        """Set a new unique name for the object. The old name is still kept in the map.

        :param new_unique_name: New unique name for the object"""
        if not isinstance(new_unique_name, str):
            raise TypeError('Unique name has to be a string.')
        self._unique_name = new_unique_name
        self._global_object.map.add_vertex(self)

    @property
    def name(self) -> str:
        """
        Get the common name of the object.

        :return: Common name of the object
        """
        return self._name

    @name.setter
    def name(self, new_name: str):
        """
        Set a new common name for the object.

        :param new_name: New name for the object
        :return: None
        """
        self._name = new_name

    @property
    def interface(self) -> InterfaceFactoryTemplate:
        """
        Get the current interface of the object
        """
        return self._interface

    @interface.setter
    def interface(self, new_interface: InterfaceFactoryTemplate):
        """
        Set the current interface to the object and generate bindings if possible. iF.e.
        ```
        def __init__(self, bar, interface=None, **kwargs):
            super().__init__(self, **kwargs)
            self.foo = bar
            self.interface = interface # As final step after initialization to set correct bindings.
        ```
        """
        self._interface = new_interface
        if new_interface is not None:
            self.generate_bindings()

    def generate_bindings(self):
        """
        Generate or re-generate bindings to an interface (if exists)

        :raises: AttributeError
        """
        if self.interface is None:
            raise AttributeError('Interface error for generating bindings. `interface` has to be set.')
        interfaceable_children = [
            key
            for key in self._global_object.map.get_edges(self)
            if issubclass(type(self._global_object.map.get_item_by_key(key)), BasedBase)
        ]
        for child_key in interfaceable_children:
            child = self._global_object.map.get_item_by_key(child_key)
            child.interface = self.interface
        self.interface.generate_bindings(self)

    def switch_interface(self, new_interface_name: str):
        """
        Switch or create a new interface.
        """
        if self.interface is None:
            raise AttributeError('Interface error for generating bindings. `interface` has to be set.')
        self.interface.switch(new_interface_name)
        self.generate_bindings()

    def get_parameters(self) -> List[Parameter]:
        """
        Get all parameter objects as a list.

        :return: List of `Parameter` objects.
        """
        par_list = []
        for key, item in self._kwargs.items():
            if hasattr(item, 'get_parameters'):
                par_list = [*par_list, *item.get_parameters()]
            elif isinstance(item, Parameter):
                par_list.append(item)
        return par_list

    def _get_linkable_attributes(self) -> List[DescriptorBase]:
        """
        Get all objects which can be linked against as a list.

        :return: List of `Descriptor`/`Parameter` objects.
        """
        item_list = []
        for key, item in self._kwargs.items():
            if hasattr(item, '_get_linkable_attributes'):
                item_list = [*item_list, *item._get_linkable_attributes()]
            elif issubclass(type(item), (DescriptorBase)):
                item_list.append(item)
        return item_list

    def get_fit_parameters(self) -> List[Parameter]:
        """
        Get all objects which can be fitted (and are not fixed) as a list.

        :return: List of `Parameter` objects which can be used in fitting.
        """
        fit_list = []
        for key, item in self._kwargs.items():
            if hasattr(item, 'get_fit_parameters'):
                fit_list = [*fit_list, *item.get_fit_parameters()]
            elif isinstance(item, Parameter):
                if item.independent and not item.fixed:
                    fit_list.append(item)
        return fit_list

    def __dir__(self) -> Iterable[str]:
        """
        This creates auto-completion and helps out in iPython notebooks.

        :return: list of function and parameter names for auto-completion
        """
        new_class_objs = list(k for k in dir(self.__class__) if not k.startswith('_'))
        return sorted(new_class_objs)

    def __copy__(self) -> BasedBase:
        """Return a copy of the object."""
        temp = self.as_dict(skip=['unique_name'])
        new_obj = self.__class__.from_dict(temp)
        return new_obj


