#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

"""Unit tests for Session class with WeakRef domains."""

import gc
import threading
import weakref

import pytest

from easyscience.global_object.session import Session
from easyscience.global_object.session import get_default_session
from easyscience.global_object.session import reset_default_session
from easyscience.global_object.session import set_default_session


class MockObject:
    """Mock object for testing Session registration."""

    def __init__(self, unique_name: str):
        self.unique_name = unique_name


@pytest.fixture(autouse=True)
def fresh_session():
    """Reset default session before each test."""
    reset_default_session()
    yield
    reset_default_session()


class TestSessionBasics:
    """Test basic Session functionality."""

    def test_session_creation(self):
        """Test that a new Session is created with default domain."""
        session = Session()
        assert session.has_domain('__default__')
        assert session.all_names() == []

    def test_generate_unique_name_monotonic(self):
        """Test that generate_unique_name uses monotonic counter."""
        session = Session()
        assert session.generate_unique_name('Test') == 'Test_0'
        assert session.generate_unique_name('Test') == 'Test_1'
        assert session.generate_unique_name('Test') == 'Test_2'
        assert session.generate_unique_name('Other') == 'Other_0'

    def test_register_object(self):
        """Test basic object registration."""
        session = Session()
        obj = MockObject('test_0')
        session.register(obj)
        assert 'test_0' in session
        assert session.get('test_0') is obj

    def test_register_duplicate_name_raises(self):
        """Test that registering duplicate name raises ValueError."""
        session = Session()
        obj1 = MockObject('test_0')
        obj2 = MockObject('test_0')
        session.register(obj1)
        with pytest.raises(ValueError, match='already exists'):
            session.register(obj2)

    def test_register_same_object_twice_succeeds(self):
        """Test that registering the same object twice is idempotent."""
        session = Session()
        obj = MockObject('test_0')
        session.register(obj)
        session.register(obj)  # Should not raise
        assert session.get('test_0') is obj

    def test_unregister_object(self):
        """Test explicit object unregistration."""
        session = Session()
        obj = MockObject('test_0')
        session.register(obj)
        assert 'test_0' in session
        session.unregister('test_0')
        assert 'test_0' not in session

    def test_all_names_returns_snapshot(self):
        """Test that all_names returns a snapshot of names."""
        session = Session()
        obj1 = MockObject('test_0')
        obj2 = MockObject('test_1')
        session.register(obj1)
        session.register(obj2)
        names = session.all_names()
        assert sorted(names) == ['test_0', 'test_1']

    def test_get_nonexistent_returns_none(self):
        """Test that get returns None for nonexistent name."""
        session = Session()
        assert session.get('nonexistent') is None


class TestWeakReferenceCleanup:
    """Test that WeakValueDictionary properly cleans up GC'd objects."""

    def test_gc_removes_object_from_session(self):
        """Test that garbage collection removes object from session."""
        session = Session()

        # Create and register object, keeping a strong reference initially
        obj = MockObject('gc_test')
        session.register(obj)
        weak_ref = weakref.ref(obj)

        # Object should be registered while we hold a strong reference
        assert 'gc_test' in session.all_names()
        assert weak_ref() is not None

        # Delete the strong reference
        del obj

        # Force garbage collection
        gc.collect()

        # Object should be removed (weak reference should be dead)
        assert weak_ref() is None
        assert 'gc_test' not in session.all_names()

    def test_reassignment_without_dispose_cleans_up(self):
        """Test that reassigning a variable allows GC to clean up."""
        session = Session()

        obj1 = MockObject('obj_0')
        session.register(obj1)
        weak_ref = weakref.ref(obj1)

        # Verify registered
        assert 'obj_0' in session.all_names()

        # Reassign without calling dispose
        obj1 = MockObject('obj_1')  # noqa: F841 (intentional reassignment)
        gc.collect()

        # Original object should be cleaned up
        assert weak_ref() is None
        assert 'obj_0' not in session.all_names()

    def test_strong_reference_keeps_object_alive(self):
        """Test that keeping a strong reference prevents GC cleanup."""
        session = Session()
        obj = MockObject('kept_alive')
        session.register(obj)

        gc.collect()

        # Object should still be alive
        assert 'kept_alive' in session.all_names()
        assert session.get('kept_alive') is obj


class TestDomains:
    """Test domain management functionality."""

    def test_create_domain(self):
        """Test creating a new domain."""
        session = Session()
        session.create_domain('worker_0')
        assert session.has_domain('worker_0')
        assert 'worker_0' in session.list_domains()

    def test_create_duplicate_domain_raises(self):
        """Test that creating duplicate domain raises ValueError."""
        session = Session()
        session.create_domain('worker_0')
        with pytest.raises(ValueError, match='already exists'):
            session.create_domain('worker_0')

    def test_drop_domain(self):
        """Test dropping a domain."""
        session = Session()
        session.create_domain('temp')
        assert session.has_domain('temp')
        session.drop_domain('temp')
        assert not session.has_domain('temp')

    def test_drop_default_domain_raises(self):
        """Test that dropping default domain raises ValueError."""
        session = Session()
        with pytest.raises(ValueError, match='Cannot drop'):
            session.drop_domain('__default__')

    def test_register_in_custom_domain(self):
        """Test registering object in custom domain."""
        session = Session()
        session.create_domain('worker_0')

        obj = MockObject('test_0')
        session.register(obj, domain='worker_0')

        assert session.contains('test_0', domain='worker_0')
        assert not session.contains('test_0', domain='__default__')

    def test_same_name_different_domains(self):
        """Test that same name can exist in different domains."""
        session = Session()
        session.create_domain('worker_0')
        session.create_domain('worker_1')

        obj0 = MockObject('param_0')
        obj1 = MockObject('param_0')

        session.register(obj0, domain='worker_0')
        session.register(obj1, domain='worker_1')

        assert session.get('param_0', domain='worker_0') is obj0
        assert session.get('param_0', domain='worker_1') is obj1

    def test_generate_unique_name_per_domain(self):
        """Test that name counters are per-domain."""
        session = Session()
        session.create_domain('worker_0')

        # Generate names in default domain
        assert session.generate_unique_name('Test') == 'Test_0'
        assert session.generate_unique_name('Test') == 'Test_1'

        # Generate names in worker_0 domain (should start from 0)
        assert session.generate_unique_name('Test', domain='worker_0') == 'Test_0'
        assert session.generate_unique_name('Test', domain='worker_0') == 'Test_1'

    def test_register_in_nonexistent_domain_raises(self):
        """Test that registering in nonexistent domain raises ValueError."""
        session = Session()
        obj = MockObject('test_0')
        with pytest.raises(ValueError, match='does not exist'):
            session.register(obj, domain='nonexistent')


class TestRename:
    """Test object renaming functionality."""

    def test_rename_object(self):
        """Test renaming an object."""
        session = Session()
        obj = MockObject('old_name')
        session.register(obj)

        session.rename('old_name', 'new_name', obj)
        obj.unique_name = 'new_name'  # Update mock object's name

        assert 'old_name' not in session
        assert 'new_name' in session
        assert session.get('new_name') is obj

    def test_rename_to_existing_name_different_obj_raises(self):
        """Test that renaming to existing name raises ValueError."""
        session = Session()
        obj1 = MockObject('name_1')
        obj2 = MockObject('name_2')
        session.register(obj1)
        session.register(obj2)

        with pytest.raises(ValueError, match='already registered'):
            session.rename('name_1', 'name_2', obj1)

    def test_rename_updates_parent_child_tracking(self):
        """Test that renaming updates parent-child relationships."""
        session = Session()
        parent = MockObject('parent')
        child = MockObject('child')
        session.register(parent)
        session.register(child)
        session.add_child('parent', 'child')

        session.rename('parent', 'new_parent', parent)

        assert session.parent('child') == 'new_parent'
        assert 'child' in session.children('new_parent')


class TestParentChildTracking:
    """Test parent-child relationship tracking."""

    def test_add_child(self):
        """Test adding a child relationship."""
        session = Session()
        parent = MockObject('parent')
        child = MockObject('child')
        session.register(parent)
        session.register(child)

        session.add_child('parent', 'child')

        assert 'child' in session.children('parent')
        assert session.parent('child') == 'parent'

    def test_remove_child(self):
        """Test removing a child relationship."""
        session = Session()
        parent = MockObject('parent')
        child = MockObject('child')
        session.register(parent)
        session.register(child)
        session.add_child('parent', 'child')

        session.remove_child('parent', 'child')

        assert 'child' not in session.children('parent')
        assert session.parent('child') is None

    def test_unregister_cleans_up_parent_child(self):
        """Test that unregister cleans up parent-child relationships."""
        session = Session()
        parent = MockObject('parent')
        child = MockObject('child')
        session.register(parent)
        session.register(child)
        session.add_child('parent', 'child')

        session.unregister('child')

        assert 'child' not in session.children('parent')


class TestDefaultSession:
    """Test module-level default session functions."""

    def test_get_default_session_returns_session(self):
        """Test that get_default_session returns a Session."""
        session = get_default_session()
        assert isinstance(session, Session)

    def test_get_default_session_returns_same_instance(self):
        """Test that get_default_session returns the same instance."""
        session1 = get_default_session()
        session2 = get_default_session()
        assert session1 is session2

    def test_set_default_session(self):
        """Test that set_default_session replaces the default."""
        new_session = Session()
        set_default_session(new_session)
        assert get_default_session() is new_session

    def test_reset_default_session(self):
        """Test that reset_default_session creates a fresh session."""
        old_session = get_default_session()
        old_session.generate_unique_name('Test')  # Add some state

        reset_default_session()
        new_session = get_default_session()

        assert new_session is not old_session
        # New session should have fresh counters
        assert new_session.generate_unique_name('Test') == 'Test_0'


class TestThreadSafety:
    """Test thread safety of Session operations."""

    def test_concurrent_name_generation(self):
        """Test that concurrent name generation produces unique names."""
        session = Session()
        names = []
        lock = threading.Lock()

        def generate_names():
            for _ in range(100):
                name = session.generate_unique_name('Concurrent')
                with lock:
                    names.append(name)

        threads = [threading.Thread(target=generate_names) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All names should be unique
        assert len(names) == len(set(names))
        assert len(names) == 400

    def test_concurrent_registration(self):
        """Test that concurrent registration is thread-safe."""
        session = Session()
        registered = []
        lock = threading.Lock()

        def register_objects(thread_id):
            for i in range(50):
                obj = MockObject(f'thread_{thread_id}_obj_{i}')
                try:
                    session.register(obj)
                    with lock:
                        registered.append(obj)
                except ValueError:
                    pass  # Expected if name collision (shouldn't happen with unique names)

        threads = [threading.Thread(target=register_objects, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All objects should be registered
        assert len(registered) == 200
        all_names = session.all_names()
        assert len(all_names) == 200


class TestInstantiateStack:
    """Test undo/redo stack initialization."""

    def test_instantiate_stack(self):
        """Test that instantiate_stack creates an UndoStack."""
        session = Session()
        assert session.undo_stack is None

        session.instantiate_stack()

        assert session.undo_stack is not None
        from easyscience.global_object.undo_redo import UndoStack

        assert isinstance(session.undo_stack, UndoStack)


class TestGlobalObjectMapSync:
    """Test that reset_default_session() also clears global_object.map."""

    def test_reset_clears_both_session_and_map(self):
        """Test that reset_default_session clears both session and global_object.map."""
        from easyscience import Parameter
        from easyscience import global_object
        from easyscience.global_object.session import get_default_session
        from easyscience.global_object.session import reset_default_session

        # Create parameters - they register in both session and global_object.map
        p1 = Parameter('test1', 1.0)  # noqa: F841
        p2 = Parameter('test2', 2.0)  # noqa: F841

        session = get_default_session()
        assert len(session.all_names()) >= 2
        assert len(global_object.map.vertices()) >= 2

        # Reset session
        reset_default_session()

        # Both should be cleared
        session = get_default_session()
        assert len(session.all_names()) == 0
        assert len(global_object.map.vertices()) == 0

    def test_no_deprecation_warning_from_reset(self):
        """Test that reset_default_session does not emit deprecation warnings."""
        import warnings

        from easyscience import Parameter
        from easyscience.global_object.session import reset_default_session

        # Create parameter
        Parameter('test', 1.0)

        # Reset should not emit deprecation warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            reset_default_session()
            # Filter for DeprecationWarning
            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) == 0, (
                f'Got deprecation warnings: {[str(x.message) for x in deprecation_warnings]}'
            )  # noqa: E501


class TestDomainIsolationWithMockObjects:
    """Test domain isolation with mock objects.

    Note: Full domain support for Parameter/DescriptorBase is planned for
    future work. These tests verify the Session infrastructure works correctly.
    """

    def test_mock_object_in_custom_domain(self):
        """Test creating mock object in a custom domain."""
        session = Session()
        session.create_domain('worker_0')

        # Create mock object in custom domain
        obj = MockObject('test_obj')
        session.register(obj, domain='worker_0')

        # Should be registered in worker_0 domain
        assert session.contains('test_obj', domain='worker_0')
        # Should NOT be in default domain
        assert not session.contains('test_obj', domain='__default__')

    def test_unique_name_generation_isolated_per_domain(self):
        """Test that name counters are truly isolated per domain."""
        session = Session()
        session.create_domain('worker_0')
        session.create_domain('worker_1')

        # Generate names in default domain
        default_names = [session.generate_unique_name('Item') for _ in range(3)]
        assert default_names == ['Item_0', 'Item_1', 'Item_2']

        # Generate names in worker_0 - should start fresh from 0
        worker0_names = [session.generate_unique_name('Item', domain='worker_0') for _ in range(3)]
        assert worker0_names == ['Item_0', 'Item_1', 'Item_2']

        # Generate names in worker_1 - should also start fresh from 0
        worker1_names = [session.generate_unique_name('Item', domain='worker_1') for _ in range(3)]
        assert worker1_names == ['Item_0', 'Item_1', 'Item_2']

    def test_gc_cleanup_per_domain(self):
        """Test that GC cleanup works correctly per domain."""
        import gc

        session = Session()
        session.create_domain('worker_0')

        # Create and register object in worker_0
        obj = MockObject('temp_obj')
        session.register(obj, domain='worker_0')
        assert session.contains('temp_obj', domain='worker_0')

        # Delete object and force GC
        del obj
        gc.collect()

        # Object should be removed from worker_0 domain
        assert not session.contains('temp_obj', domain='worker_0')
