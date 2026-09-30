# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for ``src/easyscience/fitting/samplers/parallel.py``.

Ported from the ``bayesian_mp`` branch, where the pool mapper lived in
``minimizer_bumps.py``.
"""

import io
import os
import pickle
import weakref
from unittest.mock import MagicMock

import numpy as np
import pytest

import easyscience.fitting.samplers.parallel as _parallel
from easyscience import Parameter
from easyscience import global_object
from easyscience.fitting.minimizers.utils import FitError
from easyscience.fitting.samplers.parallel import BumpsPoolMapper
from easyscience.fitting.samplers.parallel import _evaluate_bumps_point
from easyscience.fitting.samplers.parallel import _init_bumps_worker
from easyscience.fitting.samplers.parallel import _problem_pickler_class
from easyscience.fitting.samplers.parallel import _restore_none


def _round_trip(obj):
    buf = io.BytesIO()
    _problem_pickler_class()(buf).dump(obj)
    buf.seek(0)
    return pickle.load(buf)


# ===================================================================
# Worker functions
# ===================================================================


class TestWorkerFunctions:
    def test_evaluate_raises_when_problem_not_initialized(self, monkeypatch):
        monkeypatch.setattr(_parallel, '_WORKER_PROBLEM', None)
        with pytest.raises(RuntimeError, match='not initialized'):
            _evaluate_bumps_point(np.array([1.0]))

    def test_evaluate_calls_nllf_and_returns_python_float(self, monkeypatch):
        mock_problem = MagicMock()
        mock_problem.nllf.return_value = np.float64(3.5)
        monkeypatch.setattr(_parallel, '_WORKER_PROBLEM', mock_problem)

        result = _evaluate_bumps_point(np.array([1.0, 2.0]))

        assert isinstance(result, float)
        assert result == 3.5
        mock_problem.nllf.assert_called_once()
        np.testing.assert_array_equal(mock_problem.nllf.call_args[0][0], np.array([1.0, 2.0]))

    @staticmethod
    def _problem_file(tmp_path, obj):
        path = tmp_path / 'problem.pkl'
        path.write_bytes(pickle.dumps(obj))
        return str(path)

    def test_init_worker_populates_global_problem(self, monkeypatch, tmp_path):
        monkeypatch.setattr(_parallel, '_WORKER_PROBLEM', None)
        _init_bumps_worker(self._problem_file(tmp_path, {'sentinel': True}))
        assert _parallel._WORKER_PROBLEM == {'sentinel': True}

    def test_init_worker_disables_global_stack(self, monkeypatch, tmp_path):
        monkeypatch.setattr(_parallel, '_WORKER_PROBLEM', None)
        stack_status = global_object.stack.enabled
        global_object.stack.enabled = True
        try:
            _init_bumps_worker(self._problem_file(tmp_path, 42))
            assert global_object.stack.enabled is False
        finally:
            global_object.stack.enabled = stack_status


# ===================================================================
# _problem_pickler_class
# ===================================================================


class TestProblemPicklerClass:
    def test_returns_cloudpickler_subclass(self):
        from cloudpickle import CloudPickler

        assert issubclass(_problem_pickler_class(), CloudPickler)

    def test_reducer_override_replaces_weakref_with_none_restorer(self):
        cls = _problem_pickler_class()

        class _Dummy:
            pass

        obj = _Dummy()
        ref = weakref.ref(obj)

        result = cls(io.BytesIO()).reducer_override(ref)
        assert result == (_restore_none, ())

    def test_reducer_override_falls_through_for_plain_dict(self):
        cls = _problem_pickler_class()
        result = cls(io.BytesIO()).reducer_override({'key': 'val'})
        assert result is NotImplemented

    def test_weakref_survives_round_trip_as_none(self):
        class _Dummy:
            pass

        obj = _Dummy()

        class _Container:
            ref = weakref.ref(obj)

        restored = _round_trip(_Container())
        assert restored.ref is None

    def test_text_streams_are_rebuilt_as_worker_streams(self):
        import sys

        restored_err, restored_other = _round_trip((sys.stderr, io.StringIO()))

        assert restored_err is sys.stderr
        assert restored_other is sys.stdout

    def test_parameter_round_trip_keeps_value_and_unit(self):
        global_object.map._clear()
        p = Parameter(2.5, unit='m', variance=0.1, display_name='p', min=0, max=10)

        restored = _round_trip(p)

        assert restored is not p
        assert restored.value == 2.5
        assert str(restored.unit) == 'm'
        assert restored.variance == pytest.approx(0.1)
        assert restored.unique_name == p.unique_name
        assert restored._global_object is global_object
        # Rebuilt without __init__, so it is not registered as a duplicate.
        assert global_object.map.get_item_by_key(p.unique_name) is p

    def test_dependent_parameters_round_trip(self):
        """A parameter and its dependent reference each other (observers
        and dependency map). The cycle must not recurse forever."""
        global_object.map._clear()
        m = Parameter(2.0, display_name='m')
        d = Parameter.from_dependency('2*m', {'m': m}, display_name='d')

        restored_m, restored_d = _round_trip((m, d))

        assert restored_d.value == 4.0
        restored_m.value = 3.0
        assert restored_d.value == 6.0
        # The originals are untouched.
        assert m.value == 2.0
        assert d.value == 4.0


# ===================================================================
# BumpsPoolMapper: lifecycle (terminate / close)
# ===================================================================


class TestBumpsPoolMapperLifecycle:
    def _mapper(self):
        m = BumpsPoolMapper.__new__(BumpsPoolMapper)
        m._pool = MagicMock()
        m.n_workers = 2
        return m

    def test_terminate_shuts_down_pool(self):
        mapper = self._mapper()
        pool = mapper._pool
        mapper.terminate()
        pool.terminate.assert_called_once()
        pool.join.assert_called_once()
        assert mapper._pool is None

    def test_terminate_is_idempotent_when_pool_is_none(self):
        mapper = BumpsPoolMapper.__new__(BumpsPoolMapper)
        mapper._pool = None
        mapper.terminate()  # must not raise

    def test_close_delegates_to_terminate(self):
        mapper = self._mapper()
        pool = mapper._pool
        mapper.close()
        pool.terminate.assert_called_once()
        assert mapper._pool is None


# ===================================================================
# BumpsPoolMapper: __call__
# ===================================================================


class TestBumpsPoolMapperCall:
    def _mapper(self, map_return):
        m = BumpsPoolMapper.__new__(BumpsPoolMapper)
        m._pool = MagicMock()
        m._pool.map.return_value = map_return
        m.n_workers = 2
        return m

    def test_maps_2d_population_and_chunks_across_workers(self):
        pop = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        mapper = self._mapper([1.0, 2.0, 3.0])

        result = mapper(pop)

        assert result == [1.0, 2.0, 3.0]
        # 3 points across 2 workers => ceil(3/2) = 2 points per IPC task,
        # amortizing per-task multiprocessing overhead over the generation.
        assert mapper._pool.map.call_args.kwargs.get('chunksize') == 2

    def test_reshapes_1d_point_to_single_row(self):
        mapper = self._mapper([7.0])

        result = mapper(np.array([1.0, 2.0]))

        assert result == [7.0]
        points_arg = mapper._pool.map.call_args[0][1]
        assert len(points_arg) == 1
        np.testing.assert_array_equal(points_arg[0], np.array([1.0, 2.0]))

    def test_raises_on_result_count_mismatch(self):
        mapper = self._mapper([42.0])  # one result for two points
        with pytest.raises(
            RuntimeError, match='Mapper returned 1 results for 2 population points'
        ):
            mapper(np.array([[1.0], [2.0]]))


# ===================================================================
# BumpsPoolMapper: __init__ (serialization + pool creation)
# ===================================================================


class TestBumpsPoolMapperInit:
    @staticmethod
    def _patch_pickler(monkeypatch, written_bytes=b'fake_problem'):
        class _FakePickler:
            def __init__(self, buf):
                self._buf = buf

            def dump(self, obj):
                self._buf.write(written_bytes)

        monkeypatch.setattr(_parallel, '_problem_pickler_class', lambda: _FakePickler)

    def test_creates_spawn_pool_with_correct_args(self, monkeypatch):
        self._patch_pickler(monkeypatch)
        mock_pool = MagicMock()
        mock_context = MagicMock()
        mock_context.Pool.return_value = mock_pool
        requested = []

        def get_context(method):
            requested.append(method)
            return mock_context

        monkeypatch.setattr(_parallel.mp, 'get_context', get_context)

        mapper = BumpsPoolMapper(MagicMock(), n_workers=3)

        assert requested == ['spawn']
        assert mapper._pool is mock_pool
        # Only the path of the pickled problem goes through the spawn pipe.
        path = mapper._problem_path
        mock_context.Pool.assert_called_once_with(
            processes=3,
            initializer=_parallel._init_bumps_worker,
            initargs=(path,),
        )
        with open(path, 'rb') as fh:
            assert fh.read() == b'fake_problem'

        mapper.terminate()
        assert not os.path.exists(path)
        assert mapper._problem_path is None

    def test_problem_file_removed_when_pool_creation_fails(self, monkeypatch):
        self._patch_pickler(monkeypatch)
        created = []
        real_mkstemp = _parallel.tempfile.mkstemp

        def mkstemp(**kwargs):
            fd, path = real_mkstemp(**kwargs)
            created.append(path)
            return fd, path

        mock_context = MagicMock()
        mock_context.Pool.side_effect = OSError('cannot spawn')
        monkeypatch.setattr(_parallel.tempfile, 'mkstemp', mkstemp)
        monkeypatch.setattr(_parallel.mp, 'get_context', lambda _: mock_context)

        with pytest.raises(OSError, match='cannot spawn'):
            BumpsPoolMapper(MagicMock(), n_workers=2)

        assert len(created) == 1
        assert not os.path.exists(created[0])

    def test_init_worker_reads_problem_written_by_mapper(self, monkeypatch):
        """The file written by the mapper is what the worker initializer loads."""
        monkeypatch.setattr(_parallel.mp, 'get_context', lambda _: MagicMock())
        monkeypatch.setattr(_parallel, '_WORKER_PROBLEM', None)

        mapper = BumpsPoolMapper({'sentinel': [1, 2, 3]}, n_workers=2)
        try:
            _init_bumps_worker(mapper._problem_path)
            assert _parallel._WORKER_PROBLEM == {'sentinel': [1, 2, 3]}
        finally:
            mapper.terminate()

    def test_gc_paused_during_dump_and_restored(self, monkeypatch):
        import gc

        gc_state_during_dump = []

        class _RecordingPickler:
            def __init__(self, buf):
                self._buf = buf

            def dump(self, obj):
                gc_state_during_dump.append(gc.isenabled())
                self._buf.write(b'x')

        monkeypatch.setattr(_parallel, '_problem_pickler_class', lambda: _RecordingPickler)
        monkeypatch.setattr(_parallel.mp, 'get_context', lambda _: MagicMock())

        assert gc.isenabled()
        BumpsPoolMapper(MagicMock(), n_workers=2).terminate()

        assert gc_state_during_dump == [False]
        assert gc.isenabled()

    def test_gc_restored_when_dump_fails(self, monkeypatch):
        import gc

        class _BadPickler:
            def __init__(self, buf):
                pass

            def dump(self, obj):
                raise RuntimeError('dictionary changed size during iteration')

        monkeypatch.setattr(_parallel, '_problem_pickler_class', lambda: _BadPickler)

        with pytest.raises(FitError):
            BumpsPoolMapper(MagicMock(), n_workers=2)
        assert gc.isenabled()

    def test_gc_left_disabled_if_it_was_disabled(self, monkeypatch):
        import gc

        self._patch_pickler(monkeypatch)
        monkeypatch.setattr(_parallel.mp, 'get_context', lambda _: MagicMock())

        gc.disable()
        try:
            BumpsPoolMapper(MagicMock(), n_workers=2).terminate()
            assert not gc.isenabled()
        finally:
            gc.enable()

    def test_serialization_failure_raises_fit_error(self, monkeypatch):
        class _BadPickler:
            def __init__(self, buf):
                pass

            def dump(self, obj):
                raise TypeError('not serializable')

        monkeypatch.setattr(_parallel, '_problem_pickler_class', lambda: _BadPickler)
        with pytest.raises(FitError, match='serializable'):
            BumpsPoolMapper(MagicMock(), n_workers=2)
