#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

"""
Session-based object registry replacing the GlobalObject singleton.

Uses WeakValueDictionary per domain for automatic GC cleanup.
All access is protected by RLock for thread safety.
"""

from __future__ import annotations

import threading
import weakref
from typing import TYPE_CHECKING
from typing import Optional

if TYPE_CHECKING:
    from typing import Any


class Session:
    """
    A scoped object registry replacing the GlobalObject singleton.

    Each Session holds one or more *domains*, each backed by a
    WeakValueDictionary. Objects are automatically removed when
    garbage-collected — no manual dispose() needed. All mutation
    is protected by a reentrant lock, eliminating iteration races.

    A module-level default session preserves backward compatibility.
    Callers that need isolation (tests, multiprocessing, EasyDynamics
    ComponentCollections) create their own Session or domain.

    Attributes
    ----------
    _DEFAULT_DOMAIN : str
        The name of the default domain ('__default__').

    Examples
    --------
    Basic usage with default session:

    >>> from easyscience.global_object.session import get_default_session
    >>> session = get_default_session()
    >>> name = session.generate_unique_name('Parameter')
    >>> name
    'Parameter_0'

    Creating isolated domains for multiprocessing:

    >>> session.create_domain('worker_0')
    >>> session.generate_unique_name('Parameter', domain='worker_0')
    'Parameter_0'
    """

    _DEFAULT_DOMAIN = '__default__'

    def __init__(self) -> None:
        """Initialize a new Session with a default domain."""
        self._lock = threading.RLock()

        # domain_name -> WeakValueDictionary[unique_name, obj]
        self._domains: dict[str, weakref.WeakValueDictionary] = {
            self._DEFAULT_DOMAIN: weakref.WeakValueDictionary(),
        }

        # Monotonic counters per domain+prefix (no dict iteration needed for name generation)
        self._name_counters: dict[str, dict[str, int]] = {
            self._DEFAULT_DOMAIN: {},
        }

        # Parent-child tracking (strong refs are fine here — explicit relationships)
        self._children: dict[str, list[str]] = {}
        self._parent: dict[str, str | None] = {}

        # Future: undo/redo stack per session
        self.undo_stack: Optional[Any] = None

    # -------------------------------------------------------------------------
    # Domain Management
    # -------------------------------------------------------------------------

    def create_domain(self, domain: str) -> None:
        """
        Create a new isolated namespace.

        Use cases: separate threads/processes, EasyDynamics identical
        ComponentCollections, test fixtures.

        Parameters
        ----------
        domain : str
            The name of the domain to create.

        Raises
        ------
        ValueError
            If the domain already exists.

        Examples
        --------
        >>> session = Session()
        >>> session.create_domain('worker_0')
        >>> 'worker_0' in session.list_domains()
        True
        """
        with self._lock:
            if domain in self._domains:
                raise ValueError(f"Domain '{domain}' already exists.")
            self._domains[domain] = weakref.WeakValueDictionary()
            self._name_counters[domain] = {}

    def drop_domain(self, domain: str) -> None:
        """
        Remove a domain and all its registrations.

        Parameters
        ----------
        domain : str
            The name of the domain to remove.

        Raises
        ------
        ValueError
            If attempting to drop the default domain.

        Examples
        --------
        >>> session = Session()
        >>> session.create_domain('temp')
        >>> session.drop_domain('temp')
        >>> 'temp' in session.list_domains()
        False
        """
        with self._lock:
            if domain == self._DEFAULT_DOMAIN:
                raise ValueError('Cannot drop the default domain.')
            self._domains.pop(domain, None)
            self._name_counters.pop(domain, None)

    def list_domains(self) -> list[str]:
        """
        Return a list of all domain names.

        Returns
        -------
        list[str]
            List of domain names including the default domain.
        """
        with self._lock:
            return list(self._domains.keys())

    def has_domain(self, domain: str) -> bool:
        """
        Check if a domain exists.

        Parameters
        ----------
        domain : str
            The domain name to check.

        Returns
        -------
        bool
            True if the domain exists, False otherwise.
        """
        with self._lock:
            return domain in self._domains

    # -------------------------------------------------------------------------
    # Name Generation (monotonic counter, NO dict iteration)
    # -------------------------------------------------------------------------

    def generate_unique_name(self, prefix: str, domain: str = _DEFAULT_DOMAIN) -> str:
        """
        Return a name like 'Prefix_0', 'Prefix_1', ... unique within *domain*.

        Uses a monotonic counter and checks for collisions with manually-set
        names. The lock is held throughout to prevent race conditions.

        Parameters
        ----------
        prefix : str
            The prefix for the unique name (typically class name).
        domain : str, optional
            The domain to generate the name in. Defaults to '__default__'.

        Returns
        -------
        str
            A unique name in the format '{prefix}_{n}'.

        Examples
        --------
        >>> session = Session()
        >>> session.generate_unique_name('Parameter')
        'Parameter_0'
        >>> session.generate_unique_name('Parameter')
        'Parameter_1'
        """
        with self._lock:
            counters = self._name_counters.setdefault(domain, {})
            store = self._domains.get(domain, {})
            count = counters.get(prefix, 0)
            # Skip names that already exist (e.g., manually set unique_names)
            while f'{prefix}_{count}' in store:
                count += 1
            counters[prefix] = count + 1
            return f'{prefix}_{count}'

    # -------------------------------------------------------------------------
    # Object Registration (weak refs)
    # -------------------------------------------------------------------------

    def register(self, obj: Any, domain: str = _DEFAULT_DOMAIN) -> None:
        """
        Register *obj* in the given domain.

        The domain's WeakValueDictionary stores a weak reference — the
        object is automatically unregistered when it is garbage-collected.

        Parameters
        ----------
        obj : Any
            The object to register. Must have a `unique_name` attribute.
        domain : str, optional
            The domain to register in. Defaults to '__default__'.

        Raises
        ------
        ValueError
            If the domain doesn't exist or the name is already registered.

        Examples
        --------
        >>> session = Session()
        >>> class Obj:
        ...     unique_name = 'test_0'
        >>> obj = Obj()
        >>> session.register(obj)
        >>> session.get('test_0') is obj
        True
        """
        with self._lock:
            store = self._domains.get(domain)
            if store is None:
                raise ValueError(f"Domain '{domain}' does not exist.")
            name = obj.unique_name
            if name in store:
                existing = store[name]
                if existing is obj:
                    return  # Already registered
                raise ValueError(f"Name '{name}' already exists in domain '{domain}'.")
            store[name] = obj

    def unregister(self, name: str, domain: str = _DEFAULT_DOMAIN) -> None:
        """
        Explicitly remove *name* from the domain.

        This is optional — GC does this automatically for weak references,
        but useful for eager cleanup or rename operations.

        Parameters
        ----------
        name : str
            The unique name to unregister.
        domain : str, optional
            The domain to unregister from. Defaults to '__default__'.
        """
        with self._lock:
            if domain in self._domains:
                self._domains[domain].pop(name, None)
            # Also clean up parent-child tracking
            parent = self._parent.pop(name, None)
            if parent is not None and parent in self._children:
                try:
                    self._children[parent].remove(name)
                except ValueError:
                    pass
            for child in self._children.pop(name, []):
                self._parent[child] = None

    def rename(self, old_name: str, new_name: str, obj: Any, domain: str = _DEFAULT_DOMAIN) -> None:
        """
        Rename an object from old_name to new_name within a domain.

        Parameters
        ----------
        old_name : str
            The current name of the object.
        new_name : str
            The new name for the object.
        obj : Any
            The object being renamed.
        domain : str, optional
            The domain containing the object. Defaults to '__default__'.

        Raises
        ------
        ValueError
            If the domain doesn't exist or new_name is already taken by a different object.
        """
        with self._lock:
            store = self._domains.get(domain)
            if store is None:
                raise ValueError(f"Domain '{domain}' does not exist.")

            if new_name in store and store[new_name] is not obj:
                raise ValueError(f"Cannot rename '{old_name}' to '{new_name}': name is already registered.")

            store.pop(old_name, None)
            store[new_name] = obj

            # Update parent-child tracking
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

    # -------------------------------------------------------------------------
    # Queries (lock-protected snapshots)
    # -------------------------------------------------------------------------

    def all_names(self, domain: str = _DEFAULT_DOMAIN) -> list[str]:
        """
        Snapshot of currently-alive object names in *domain*.

        Parameters
        ----------
        domain : str, optional
            The domain to query. Defaults to '__default__'.

        Returns
        -------
        list[str]
            List of unique names of currently-alive objects.
        """
        with self._lock:
            store = self._domains.get(domain, {})
            return list(store)

    def get(self, name: str, domain: str = _DEFAULT_DOMAIN) -> Optional[Any]:
        """
        Look up a live object by unique_name, or None if GC'd.

        Parameters
        ----------
        name : str
            The unique name to look up.
        domain : str, optional
            The domain to search in. Defaults to '__default__'.

        Returns
        -------
        Optional[Any]
            The object if found and alive, None otherwise.
        """
        with self._lock:
            store = self._domains.get(domain)
            return store.get(name) if store else None

    def __contains__(self, name: str) -> bool:
        """
        Check if name exists in default domain.

        Parameters
        ----------
        name : str
            The unique name to check.

        Returns
        -------
        bool
            True if the name is registered in the default domain.
        """
        with self._lock:
            store = self._domains.get(self._DEFAULT_DOMAIN, {})
            return name in store

    def contains(self, name: str, domain: str = _DEFAULT_DOMAIN) -> bool:
        """
        Check if name exists in the specified domain.

        Parameters
        ----------
        name : str
            The unique name to check.
        domain : str, optional
            The domain to check. Defaults to '__default__'.

        Returns
        -------
        bool
            True if the name is registered in the specified domain.
        """
        with self._lock:
            store = self._domains.get(domain, {})
            return name in store

    # -------------------------------------------------------------------------
    # Parent-Child Tracking
    # -------------------------------------------------------------------------

    def add_child(self, parent_name: str, child_name: str) -> None:
        """
        Register a parent-child relationship.

        Parameters
        ----------
        parent_name : str
            The unique name of the parent object.
        child_name : str
            The unique name of the child object.
        """
        with self._lock:
            self._children.setdefault(parent_name, [])
            if child_name not in self._children[parent_name]:
                self._children[parent_name].append(child_name)
            self._parent[child_name] = parent_name

    def remove_child(self, parent_name: str, child_name: str) -> None:
        """
        Remove a parent-child relationship.

        Parameters
        ----------
        parent_name : str
            The unique name of the parent object.
        child_name : str
            The unique name of the child object.
        """
        with self._lock:
            if parent_name in self._children:
                try:
                    self._children[parent_name].remove(child_name)
                except ValueError:
                    pass
            if self._parent.get(child_name) == parent_name:
                self._parent[child_name] = None

    def children(self, name: str) -> list[str]:
        """
        Get the names of all children of an object.

        Parameters
        ----------
        name : str
            The unique name of the parent object.

        Returns
        -------
        list[str]
            List of unique names of child objects.
        """
        with self._lock:
            return list(self._children.get(name, []))

    def parent(self, name: str) -> str | None:
        """
        Get the name of the parent of an object.

        Parameters
        ----------
        name : str
            The unique name of the child object.

        Returns
        -------
        str | None
            The unique name of the parent, or None if no parent.
        """
        with self._lock:
            return self._parent.get(name)

    # -------------------------------------------------------------------------
    # Undo/Redo (future)
    # -------------------------------------------------------------------------

    def instantiate_stack(self) -> None:
        """
        Initialize the undo/redo stack for this session.

        This lazily imports UndoStack to avoid circular dependencies.
        """
        from easyscience.global_object.undo_redo import UndoStack

        self.undo_stack = UndoStack()


# =============================================================================
# Module-level default session (backward compatibility)
# =============================================================================

_default_session: Session | None = None
_default_session_lock = threading.Lock()


def get_default_session() -> Session:
    """
    Return the process-wide default session, creating it lazily.

    Returns
    -------
    Session
        The default session instance.

    Examples
    --------
    >>> session = get_default_session()
    >>> isinstance(session, Session)
    True
    """
    global _default_session
    if _default_session is None:
        with _default_session_lock:
            if _default_session is None:
                _default_session = Session()
    return _default_session


def set_default_session(session: Session) -> None:
    """
    Replace the default session.

    Useful in tests and multiprocessing scenarios.

    Parameters
    ----------
    session : Session
        The new default session.

    Examples
    --------
    >>> new_session = Session()
    >>> set_default_session(new_session)
    >>> get_default_session() is new_session
    True
    """
    global _default_session
    with _default_session_lock:
        _default_session = session


def reset_default_session() -> None:
    """
    Reset the default session to a new empty session.

    Also clears the global_object.map to ensure consistency between
    the session and the legacy global object registry.

    Primarily used in testing to ensure clean state between tests.

    Examples
    --------
    >>> reset_default_session()
    >>> session = get_default_session()
    >>> session.all_names()
    []
    """
    global _default_session
    with _default_session_lock:
        _default_session = Session()
    # Also clear global_object.map for backward compatibility
    # Use lazy import to avoid circular imports
    from easyscience import global_object

    global_object.map._clear_no_warn()
