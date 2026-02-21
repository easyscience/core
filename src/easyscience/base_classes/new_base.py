from __future__ import annotations

#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

import threading
from inspect import signature
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any
    from typing import Dict
    from typing import Iterable
    from typing import List
    from typing import Optional


class Session:
    """
    Holds all mutable-state for NewBase.
    """

    def __init__(self) -> None:
        self._lock: threading.RLock = threading.RLock()
        self._registry: dict[str, NewBase] = {}
        self._name_counters: dict[str, int] = {}
        self._children: dict[str, list[str]] = {}
        self._parent: dict[str, str | None] = {}

    def generate_unique_name(self, prefix: str) -> str:
        with self._lock:
            n = self._name_counters.get(prefix, 0)
            while f'{prefix}_{n}' in self._registry:
                n += 1
            name = f'{prefix}_{n}'
            self._name_counters[prefix] = n + 1
            return name

    def reserve_name(self, name: str, obj: NewBase) -> None:
        with self._lock:
            if name in self._registry:
                existing = self._registry[name]
                if existing is obj:
                    return
                raise ValueError(
                    f"Duplicate unique_name '{name}': already registered for {existing!r}."
                )
            self._registry[name] = obj

    def release_name(self, name: str) -> None:
        with self._lock:
            self._registry.pop(name, None)
            parent = self._parent.pop(name, None)
            if parent is not None and parent in self._children:
                try:
                    self._children[parent].remove(name)
                except ValueError:
                    pass
            for child in self._children.pop(name, []):
                self._parent[child] = None

    def rename(self, old_name: str, new_name: str, obj: NewBase) -> None:
        with self._lock:
            if new_name in self._registry and self._registry[new_name] is not obj:
                raise ValueError(
                    f"Cannot rename '{old_name}' to '{new_name}': name is already registered."
                )
            self._registry.pop(old_name, None)
            self._registry[new_name] = obj

            parent = self._parent.pop(old_name, None)
            self._parent[new_name] = parent
            if parent is not None and parent in self._children:
                try:
                    idx = self._children[parent].index(old_name)
                    self._children[parent][idx] = new_name
                except ValueError:
                    pass

            children = self._children.pop(old_name, [])
            if children:
                self._children[new_name] = children
                for child in children:
                    self._parent[child] = new_name

    def get(self, name: str) -> NewBase:
        try:
            return self._registry[name]
        except KeyError:
            raise KeyError(f"No object with unique_name '{name}' in this session") from None

    def __contains__(self, name: str) -> bool:
        return name in self._registry

    def all_names(self) -> list[str]:
        with self._lock:
            return list(self._registry)

    def add_child(self, parent_name: str, child_name: str) -> None:
        with self._lock:
            self._children.setdefault(parent_name, [])
            if child_name not in self._children[parent_name]:
                self._children[parent_name].append(child_name)
            self._parent[child_name] = parent_name

    def remove_child(self, parent_name: str, child_name: str) -> None:
        with self._lock:
            if parent_name in self._children:
                try:
                    self._children[parent_name].remove(child_name)
                except ValueError:
                    pass
            if self._parent.get(child_name) == parent_name:
                self._parent[child_name] = None

    def children(self, name: str) -> list[str]:
        return list(self._children.get(name, []))

    def parent(self, name: str) -> str | None:
        return self._parent.get(name)


_default_session: Session | None = None
_default_session_lock = threading.Lock()


def get_default_session() -> Session:
    global _default_session
    if _default_session is None:
        with _default_session_lock:
            if _default_session is None:
                _default_session = Session()
    return _default_session


def set_default_session(session: Session) -> None:
    global _default_session
    with _default_session_lock:
        _default_session = session


def reset_default_session() -> None:
    """Reset the default session to a new empty session. Mainly for testing."""
    global _default_session
    with _default_session_lock:
        _default_session = None


class NewBase:
    """
    New base class with session-backed name registry and ownership tracking.
    """

    def __init__(
        self,
        unique_name: Optional[str] = None,
        display_name: Optional[str] = None,
        session: Session | None = None,
    ) -> None:
        if session is None:
            session = get_default_session()

        self._session: Session = session

        if unique_name is None:
            unique_name = self._session.generate_unique_name(self.__class__.__name__)
            self._default_unique_name = True
        else:
            if not isinstance(unique_name, str):
                raise TypeError('unique_name must be a string.')
            self._default_unique_name = False

        self._unique_name: str = unique_name
        self._session.reserve_name(unique_name, self)
        self._disposed = False

        if display_name is not None and not isinstance(display_name, str):
            raise TypeError('display_name must be a string or None.')
        self._display_name: str | None = display_name

    @property
    def unique_name(self) -> str:
        return self._unique_name

    @unique_name.setter
    def unique_name(self, new_name: str) -> None:
        self._ensure_not_disposed()
        if not isinstance(new_name, str):
            raise TypeError('unique_name must be a string.')
        old_name = self._unique_name
        if old_name == new_name:
            return
        self._session.rename(old_name, new_name, self)
        self._unique_name = new_name
        self._default_unique_name = False

    @property
    def display_name(self) -> str:
        return self._display_name if self._display_name is not None else self._unique_name

    @display_name.setter
    def display_name(self, name: str | None) -> None:
        self._ensure_not_disposed()
        if name is not None and not isinstance(name, str):
            raise TypeError('display_name must be a string or None.')
        self._display_name = name

    @property
    def session(self) -> Session:
        return self._session

    @property
    def _arg_spec(self) -> set[str]:
        sign = signature(self.__class__.__init__)
        names = [p.name for p in sign.parameters.values() if p.kind == p.POSITIONAL_OR_KEYWORD]
        return set(names[1:])

    def add_child(self, child: NewBase) -> None:
        self._ensure_not_disposed()
        child._ensure_not_disposed()
        if child.session is not self.session:
            raise ValueError("Cannot add child from different session.")
        self._session.add_child(self._unique_name, child.unique_name)

    def remove_child(self, child: NewBase) -> None:
        self._ensure_not_disposed()
        child._ensure_not_disposed()
        if child.session is not self.session:
            raise ValueError("Cannot remove child from different session.")
        self._session.remove_child(self._unique_name, child.unique_name)

    def get_parent(self) -> NewBase | None:
        self._ensure_not_disposed()
        parent_name = self._session.parent(self._unique_name)
        if parent_name is None:
            return None
        return self._session.get(parent_name)

    def get_children(self) -> list[NewBase]:
        self._ensure_not_disposed()
        return [self._session.get(n) for n in self._session.children(self._unique_name)]

    @classmethod
    def by_name(cls, name: str, session: Session | None = None) -> NewBase:
        s = session if session is not None else get_default_session()
        return s.get(name)

    def dispose(self) -> None:
        if self._disposed:
            return
        name = self.unique_name
        self._session.release_name(name)
        self._disposed = True

    def _ensure_not_disposed(self) -> None:
        if self._disposed:
            raise RuntimeError(f"Object '{self._unique_name}' has been disposed.")

    def to_dict(self, skip: Optional[List[str]] = None) -> Dict[str, Any]:
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
        return serializer._convert_to_dict(self, skip=skip, full_encode=False)

    @classmethod
    def from_dict(cls, obj_dict: Dict[str, Any], session: Session | None = None) -> NewBase:
        from ..io.serializer_base import SerializerBase

        if not SerializerBase._is_serialized_easyscience_object(obj_dict):
            raise ValueError('Input must be a dictionary representing an EasyScience object.')
        if obj_dict['@class'] != cls.__name__:
            raise ValueError(f'Class name in dictionary does not match {cls.__name__}.')
        kwargs = SerializerBase.deserialize_dict(obj_dict)
        if session is not None:
            kwargs['session'] = session
        return cls(**kwargs)

    def __dir__(self) -> Iterable[str]:
        return sorted(k for k in dir(self.__class__) if not k.startswith('_'))

    def __copy__(self) -> NewBase:
        copied = self.__class__.from_dict(self.to_dict(skip=['unique_name']), session=self._session)
        copied.display_name = self.display_name
        return copied

    def __deepcopy__(self, memo: dict) -> NewBase:
        return self.__copy__()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__} `{self._unique_name}`'
