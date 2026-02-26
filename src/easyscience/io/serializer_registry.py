"""
serializer_registry.py

Thread-safe plug-in registry for deserializers.

Usage patterns:
- register("pint.quantity.v1", handler)
- handler = get("pint.quantity.v1")
- deserialize({"__registry_type__": "pint.quantity.v1", ...})
- use @serializer_for("key") decorator to register a handler
- use temporary_register(...) as a context manager for test-scoped registrations
"""

import contextlib
import threading
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import Optional

# Handler signature: Callable[[dict], Any]
_Registry = Dict[str, Callable[[dict], Any]]
_REGISTRY: _Registry = {}
_LOCK = threading.RLock()


def register(key: str, handler: Callable[[dict], Any], *, override: bool = False) -> None:
    """
    Register a deserializer handler under `key`.
    Raises KeyError if key exists and override is False.
    """
    if not isinstance(key, str) or not key:
        raise ValueError('key must be a non-empty string')
    if not callable(handler):
        raise ValueError('handler must be callable')

    with _LOCK:
        if key in _REGISTRY and not override:
            raise KeyError(f"a handler is already registered for key '{key}'")
        _REGISTRY[key] = handler


def unregister(key: str) -> None:
    """Unregister handler for key. Raises KeyError if missing."""
    with _LOCK:
        if key not in _REGISTRY:
            raise KeyError(f"no handler registered for key '{key}'")
        del _REGISTRY[key]


def get_deserializer(key: str) -> Optional[Callable[[dict], Any]]:
    """Return the handler registered for key, or None if not found."""
    with _LOCK:
        return _REGISTRY.get(key)


def list_keys() -> Iterable[str]:
    """Return a snapshot iterable of registered keys."""
    with _LOCK:
        return list(_REGISTRY.keys())


def deserialize(obj: dict) -> Any:
    """
    Dispatch deserialization based on the registry key inside obj.
    Expects obj to include a "__registry_type__" key.
    Raises KeyError if key missing or no handler registered.
    """
    if not isinstance(obj, dict):
        raise ValueError('deserialize expects a dict')

    key = obj.get('__registry_type__')
    if not key:
        raise KeyError("missing '__registry_type__' in object dict")

    handler = get_deserializer(key)
    if handler is None:
        raise KeyError(f"no deserializer registered for key '{key}'")
    return handler(obj)


def clear_registry() -> None:
    """Remove all registrations. Useful for tests."""
    with _LOCK:
        _REGISTRY.clear()


@contextlib.contextmanager
def temporary_register(key: str, handler: Callable[[dict], Any]):
    """
    Context manager to temporarily register a handler.
    On exit, restores previous handler or removes the key.
    """
    if not isinstance(key, str) or not key:
        raise ValueError('key must be a non-empty string')
    if not callable(handler):
        raise ValueError('handler must be callable')

    with _LOCK:
        previous = _REGISTRY.get(key, None)
        had_previous = key in _REGISTRY
        _REGISTRY[key] = handler
    try:
        yield
    finally:
        with _LOCK:
            if had_previous:
                _REGISTRY[key] = previous  # restore
            else:
                _REGISTRY.pop(key, None)


def serializer_for(key: str, *, override: bool = False):
    """
    Decorator to register a function as a serializer handler.
    Example:
        @serializer_for("pint.quantity.v1")
        def pint_handler(d): ...
    """

    def decorator(fn: Callable[[dict], Any]):
        register(key, fn, override=override)
        return fn

    return decorator
