from __future__ import annotations

#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience
from inspect import signature
from typing import TYPE_CHECKING

from easyscience.global_object.session import Session
from easyscience.global_object.session import get_default_session
from easyscience.global_object.session import reset_default_session  # noqa: F401 (re-export)
from easyscience.global_object.session import set_default_session  # noqa: F401 (re-export)

if TYPE_CHECKING:
    from typing import Any
    from typing import Dict
    from typing import Iterable
    from typing import List
    from typing import Optional


class NewBase:
    """
    New base class with session-backed name registry and ownership tracking.

    Objects are registered in a Session using WeakValueDictionary, which
    means they are automatically removed when garbage-collected. No manual
    dispose() is needed.

    Parameters
    ----------
    unique_name : str, optional
        A unique identifier for this object. If not provided, one is
        generated automatically using the class name and a counter.
    display_name : str, optional
        A human-readable name for display purposes.
    session : Session, optional
        The session to register this object in. If not provided, the
        default session is used.
    domain : str, optional
        The domain within the session to register in. Defaults to '__default__'.
        Use different domains to allow identical names in separate namespaces
        (useful for multiprocessing or parallel model instances).
    """

    def __init__(
        self,
        unique_name: Optional[str] = None,
        display_name: Optional[str] = None,
        session: Session | None = None,
        domain: str = Session._DEFAULT_DOMAIN,
    ) -> None:
        if session is None:
            session = get_default_session()

        self._session: Session = session
        self._domain: str = domain

        if unique_name is None:
            unique_name = self._session.generate_unique_name(self.__class__.__name__, domain=self._domain)
            self._default_unique_name = True
        else:
            if not isinstance(unique_name, str):
                raise TypeError('unique_name must be a string.')
            self._default_unique_name = False

        self._unique_name: str = unique_name
        self._session.register(self, domain=self._domain)

        if display_name is not None and not isinstance(display_name, str):
            raise TypeError('display_name must be a string or None.')
        self._display_name: str | None = display_name

    @property
    def unique_name(self) -> str:
        """Get the unique name of the object."""
        return self._unique_name

    @unique_name.setter
    def unique_name(self, new_name: str) -> None:
        """Set a new unique name for the object."""
        if not isinstance(new_name, str):
            raise TypeError('unique_name must be a string.')
        old_name = self._unique_name
        if old_name == new_name:
            return
        self._session.rename(old_name, new_name, self, domain=self._domain)
        self._unique_name = new_name
        self._default_unique_name = False

    @property
    def display_name(self) -> str:
        """Get the display name (falls back to unique_name if not set)."""
        return self._display_name if self._display_name is not None else self._unique_name

    @display_name.setter
    def display_name(self, name: str | None) -> None:
        """Set the display name."""
        if name is not None and not isinstance(name, str):
            raise TypeError('display_name must be a string or None.')
        self._display_name = name

    @property
    def session(self) -> Session:
        """Get the session this object is registered in."""
        return self._session

    @property
    def domain(self) -> str:
        """Get the domain this object is registered in."""
        return self._domain

    @property
    def _arg_spec(self) -> set[str]:
        """Get the argument names for this class's __init__ method."""
        sign = signature(self.__class__.__init__)
        names = [p.name for p in sign.parameters.values() if p.kind == p.POSITIONAL_OR_KEYWORD]
        return set(names[1:])

    def add_child(self, child: NewBase) -> None:
        """
        Register a parent-child relationship.

        Parameters
        ----------
        child : NewBase
            The child object to add.

        Raises
        ------
        ValueError
            If the child is from a different session.
        """
        if child.session is not self.session:
            raise ValueError('Cannot add child from different session.')
        self._session.add_child(self._unique_name, child.unique_name)

    def remove_child(self, child: NewBase) -> None:
        """
        Remove a parent-child relationship.

        Parameters
        ----------
        child : NewBase
            The child object to remove.

        Raises
        ------
        ValueError
            If the child is from a different session.
        """
        if child.session is not self.session:
            raise ValueError('Cannot remove child from different session.')
        self._session.remove_child(self._unique_name, child.unique_name)

    def get_parent(self) -> NewBase | None:
        """
        Get the parent of this object.

        Returns
        -------
        NewBase | None
            The parent object, or None if no parent or parent was GC'd.
        """
        parent_name = self._session.parent(self._unique_name)
        if parent_name is None:
            return None
        return self._session.get(parent_name, domain=self._domain)

    def get_children(self) -> list[NewBase]:
        """
        Get all children of this object.

        Returns
        -------
        list[NewBase]
            List of child objects (excluding any that were GC'd).
        """
        children = []
        for name in self._session.children(self._unique_name):
            child = self._session.get(name, domain=self._domain)
            if child is not None:
                children.append(child)
        return children

    @classmethod
    def by_name(
        cls,
        name: str,
        session: Session | None = None,
        domain: str = Session._DEFAULT_DOMAIN,
    ) -> NewBase | None:
        """
        Look up an object by unique name.

        Parameters
        ----------
        name : str
            The unique name to look up.
        session : Session, optional
            The session to search in. Defaults to the default session.
        domain : str, optional
            The domain to search in. Defaults to '__default__'.

        Returns
        -------
        NewBase | None
            The object if found and alive, None otherwise.
        """
        s = session if session is not None else get_default_session()
        return s.get(name, domain=domain)

    def to_dict(self, skip: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Serialize this object to a dictionary.

        Parameters
        ----------
        skip : list[str], optional
            List of attribute names to skip during serialization.

        Returns
        -------
        dict
            Dictionary representation of this object.
        """
        from ..io.serializer_base import SerializerBase

        serializer = SerializerBase()
        if skip is None:
            skip = []
        if self._default_unique_name and 'unique_name' not in skip:
            skip.append('unique_name')
        if self._display_name is None and 'display_name' not in skip:
            skip.append('display_name')
        if 'session' not in skip:
            skip.append('session')
        if 'domain' not in skip:
            skip.append('domain')
        return serializer._convert_to_dict(self, skip=skip, full_encode=False)

    @classmethod
    def from_dict(
        cls,
        obj_dict: Dict[str, Any],
        session: Session | None = None,
        domain: str = Session._DEFAULT_DOMAIN,
    ) -> NewBase:
        """
        Deserialize an object from a dictionary.

        Parameters
        ----------
        obj_dict : dict
            Dictionary representation of the object.
        session : Session, optional
            The session to register the new object in.
        domain : str, optional
            The domain to register the new object in.

        Returns
        -------
        NewBase
            The deserialized object.

        Raises
        ------
        ValueError
            If the dictionary is not a valid EasyScience object representation.
        """
        from ..io.serializer_base import SerializerBase

        if not SerializerBase._is_serialized_easyscience_object(obj_dict):
            raise ValueError('Input must be a dictionary representing an EasyScience object.')
        if obj_dict['@class'] != cls.__name__:
            raise ValueError(f'Class name in dictionary does not match {cls.__name__}.')
        kwargs = SerializerBase.deserialize_dict(obj_dict)
        if session is not None:
            kwargs['session'] = session
        kwargs['domain'] = domain
        return cls(**kwargs)

    def __dir__(self) -> Iterable[str]:
        return sorted(k for k in dir(self.__class__) if not k.startswith('_'))

    def __copy__(self) -> NewBase:
        copied = self.__class__.from_dict(
            self.to_dict(skip=['unique_name']),
            session=self._session,
            domain=self._domain,
        )
        copied.display_name = self.display_name
        return copied

    def __deepcopy__(self, memo: dict) -> NewBase:
        return self.__copy__()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__} `{self._unique_name}`'
