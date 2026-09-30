# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Process-pool evaluation of the DREAM population."""

from __future__ import annotations

import gc
import io
import multiprocessing as mp
import os
import pickle
import sys
import tempfile
import weakref
from typing import TYPE_CHECKING
from typing import Any

import numpy as np

from ..minimizers.utils import FitError

if TYPE_CHECKING:
    from bumps.names import FitProblem

#: The ``FitProblem`` unpickled once per worker process by the pool
#: initializer, so each task only ships the points to evaluate.
_WORKER_PROBLEM = None

_SCIPP_VARIABLE_KEY = '__easyscience_scipp_variable__'


def _serialize_worker_value(value: Any) -> Any:
    """
    Make an attribute value safe to pickle for a worker.

    Scipp scalars are converted to plain dicts, and weak references
    (e.g. the ``weakref.finalize`` hooks on parameters) are dropped.
    Containers are walked recursively.
    """
    try:
        import scipp as sc
    except ImportError:
        sc = None

    if sc is not None and isinstance(value, sc.Variable):
        return {
            _SCIPP_VARIABLE_KEY: True,
            'value': value.value,
            'variance': value.variance,
            'unit': str(value.unit),
        }
    if isinstance(value, (weakref.ReferenceType, weakref.KeyedRef)):
        return None
    if isinstance(value, dict):
        return {key: _serialize_worker_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize_worker_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_serialize_worker_value(item) for item in value)
    if isinstance(value, set):
        return {_serialize_worker_value(item) for item in value}
    return value


def _deserialize_worker_value(value: Any) -> Any:
    """Inverse of :func:`_serialize_worker_value`."""
    if isinstance(value, dict):
        if value.get(_SCIPP_VARIABLE_KEY):
            import scipp as sc

            return sc.scalar(value['value'], unit=value['unit'], variance=value['variance'])
        return {key: _deserialize_worker_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_deserialize_worker_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_deserialize_worker_value(item) for item in value)
    if isinstance(value, set):
        return {_deserialize_worker_value(item) for item in value}
    return value


def _new_object(cls: type) -> object:
    """
    Create a bare instance of ``cls`` without calling ``__init__``.

    Bypassing ``__init__`` keeps the object out of the worker's global
    map (its ``unique_name`` would otherwise be regenerated or clash).
    """
    return cls.__new__(cls)


def _set_object_state(obj: object, state: dict) -> None:
    """
    Restore an object's attributes and attach the worker's global
    object.
    """
    from easyscience import global_object

    obj.__dict__.update(_deserialize_worker_value(state))
    obj._global_object = global_object


def _reduce_object_state(obj: object) -> tuple:
    """
    Pickle reduction for an EasyScience object, omitting the global
    object.

    The object is created first and its state set afterwards (the
    ``state_setter`` form), so pickle memoizes it before descending into
    its attributes. This lets reference cycles, such as a parameter and
    its dependents observing each other, round-trip.
    """
    state = {
        key: _serialize_worker_value(value)
        for key, value in obj.__dict__.items()
        if key != '_global_object'
    }
    return _new_object, (type(obj),), state, None, None, _set_object_state


def _restore_none() -> None:
    return None


def _restore_stream(name: str) -> Any:
    """Return the worker's own ``sys.stdout`` or ``sys.stderr``."""
    return getattr(sys, name)


def _reduce_text_stream(obj: io.TextIOBase) -> tuple:
    """
    Pickle reduction for a text stream.

    Streams cannot be sent to another process. The ones reachable from a
    problem are console writers, e.g. the ``writer``/``err_writer`` of
    the ``asteval`` interpreter behind dependent parameters, so they are
    rebuilt as the worker's own ``stderr`` or ``stdout``. This also
    covers a redirected or captured ``sys.stdout``, which
    ``cloudpickle`` would otherwise fail on.
    """
    name = 'stderr' if obj in (sys.stderr, sys.__stderr__) else 'stdout'
    return _restore_stream, (name,)


def _problem_pickler_class() -> type:
    """
    Build a Pickler subclass that handles BUMPS problem reduction
    locally.

    Uses ``reducer_override`` (instance-scoped) instead of mutating
    ``__reduce__`` on shared classes or ``copyreg.dispatch_table``,
    since those globals would race with any concurrent pickle on another
    thread. ``cloudpickle`` is used so that fit functions and models
    defined interactively (in ``__main__`` or a notebook) are pickled by
    value.

    Returns
    -------
    type
        The ``CloudPickler`` subclass.
    """
    from cloudpickle import CloudPickler

    from easyscience.base_classes.new_base import NewBase

    _parent_reducer = CloudPickler.reducer_override

    class _BumpsProblemPickler(CloudPickler):
        def reducer_override(self, obj):
            if isinstance(obj, (weakref.ReferenceType, weakref.KeyedRef)):
                return _restore_none, ()
            if isinstance(obj, NewBase):
                return _reduce_object_state(obj)
            if isinstance(obj, io.TextIOBase):
                return _reduce_text_stream(obj)
            return _parent_reducer(self, obj)

    return _BumpsProblemPickler


def _init_bumps_worker(problem_path: str) -> None:
    global _WORKER_PROBLEM
    with open(problem_path, 'rb') as fh:
        _WORKER_PROBLEM = pickle.loads(fh.read())

    from easyscience import global_object

    global_object.stack.enabled = False


def _evaluate_bumps_point(point: np.ndarray) -> float:
    if _WORKER_PROBLEM is None:
        raise RuntimeError('BUMPS worker problem was not initialized')
    return float(_WORKER_PROBLEM.nllf(point))


def _dump_problem(problem: FitProblem) -> bytes:
    """Serialize ``problem`` for the workers.

    The cyclic garbage collector is paused for the duration of the dump.
    A collection that runs mid-dump fires the finalizers of objects left
    over from earlier runs (for instance the global map's clean-up of
    freed parameters), and those can resize a dictionary the pickler is
    iterating, failing the dump with ``RuntimeError: dictionary changed
    size during iteration``. The dump is a single synchronous call, so
    postponing collection until it finishes is safe.

    Parameters
    ----------
    problem : FitProblem
        The BUMPS problem to serialize.

    Returns
    -------
    bytes
        The pickled problem.
    """
    buffer = io.BytesIO()
    gc_was_enabled = gc.isenabled()
    gc.disable()
    try:
        _problem_pickler_class()(buffer).dump(problem)
    finally:
        if gc_was_enabled:
            gc.enable()
    return buffer.getvalue()


class BumpsPoolMapper:
    """
    Multiprocessing mapper for BUMPS DREAM population evaluation.

    The ``FitProblem`` is serialized once to a private temporary file,
    which the pool initializer unpickles in every worker; each
    generation then only sends the population points and receives their
    negative log-likelihoods. Workers are started with the ``spawn``
    method on every platform, so behaviour matches between Linux, macOS
    and Windows. The file is removed when the pool is shut down.

    The problem is passed by file rather than as an initializer
    argument because ``spawn`` sends initializer arguments through a
    pipe. On Python < 3.14, when that payload does not fit in the pipe
    buffer, starting each worker blocks until the previous one has
    finished importing the main module, so pool start-up grows linearly
    with the number of workers (seconds per worker).

    Parameters
    ----------
    problem : FitProblem
        The BUMPS problem whose ``nllf`` the workers evaluate.
    n_workers : int
        Number of worker processes.

    Raises
    ------
    FitError
        If the problem (including the model and fit function) cannot be
        serialized for the worker processes.
    """

    def __init__(self, problem: FitProblem, n_workers: int):
        self._pool = None
        self._problem_path = None
        self.n_workers = n_workers
        try:
            problem_bytes = _dump_problem(problem)
        except Exception as exc:
            raise FitError(
                'BUMPS multiprocessing requires the FitProblem and fit function to be '
                'serializable. Use n_workers=1 for sequential sampling.'
            ) from exc

        fd, self._problem_path = tempfile.mkstemp(prefix='easyscience-bumps-', suffix='.pkl')
        started = False
        try:
            with os.fdopen(fd, 'wb') as fh:
                fh.write(problem_bytes)
            context = mp.get_context('spawn')
            self._pool = context.Pool(
                processes=n_workers,
                initializer=_init_bumps_worker,
                initargs=(self._problem_path,),
            )
            started = True
        finally:
            if not started:
                self._remove_problem_file()

    def __call__(self, population: np.ndarray) -> list[float]:
        """
        Evaluate the negative log-likelihood of each population point.

        Parameters
        ----------
        population : np.ndarray
            A single point (1-D) or a population (2-D, one row per
            chain).

        Returns
        -------
        list[float]
            One value per population point.

        Raises
        ------
        RuntimeError
            If the pool returns a different number of values than points
            were sent.
        """
        # BUMPS may pass either a single point (1D) or a population (2D).
        # Always reshape to 2D so list() produces one element per chain member.
        pop = np.atleast_2d(np.asarray(population))
        n_points = pop.shape[0]
        # Distribute the population across workers in as few tasks as possible.
        # DREAM evaluations are individually cheap, so per-task IPC overhead
        # (pickling + queue round-trip) dominates when chunksize=1. Sending one
        # chunk per worker amortizes that overhead across the whole generation.
        chunksize = max(1, (n_points + self.n_workers - 1) // self.n_workers)
        results = self._pool.map(_evaluate_bumps_point, list(pop), chunksize=chunksize)

        # Safety check: BUMPS DREAM state corruption can occur if the
        # mapper returns a different number of values than expected.
        if len(results) != n_points:
            raise RuntimeError(
                f'Mapper returned {len(results)} results for {n_points} population points'
            )
        return results

    def close(self) -> None:
        """Shut down the worker pool."""
        self.terminate()

    def terminate(self) -> None:
        """Shut down the worker pool; safe to call more than once."""
        if self._pool is not None:
            self._pool.terminate()
            self._pool.join()
            self._pool = None
        self._remove_problem_file()

    def _remove_problem_file(self) -> None:
        """Delete the temporary problem file, if any."""
        path = getattr(self, '_problem_path', None)
        self._problem_path = None
        if path is not None:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass
