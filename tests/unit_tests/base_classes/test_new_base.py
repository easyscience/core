import copy
import gc
import weakref

import pytest

from easyscience.base_classes import NewBase
from easyscience.global_object.session import Session
from easyscience.global_object.session import reset_default_session


@pytest.fixture(autouse=True)
def fresh_default_session():
    """Reset default session before each test."""
    reset_default_session()


class TestNewBase:
    def test_constructor_defaults(self):
        obj = NewBase()
        assert obj._unique_name == 'NewBase_0'
        assert obj._default_unique_name is True
        assert obj._display_name is None
        assert NewBase.by_name('NewBase_0') is obj

    def test_constructor_with_arguments(self):
        obj = NewBase(unique_name='custom_name', display_name='My Object')
        assert obj._unique_name == 'custom_name'
        assert obj._default_unique_name is False
        assert obj._display_name == 'My Object'
        assert NewBase.by_name('custom_name') is obj

    def test_constructor_invalid_unique_name(self):
        with pytest.raises(TypeError, match='unique_name must be a string'):
            NewBase(unique_name=123)

    def test_constructor_invalid_display_name(self):
        with pytest.raises(TypeError, match='display_name must be a string or None'):
            NewBase(display_name=456)

    def test_arg_spec(self):
        obj = NewBase()
        arg_spec = obj._arg_spec
        assert 'unique_name' in arg_spec
        assert 'display_name' in arg_spec
        assert 'session' in arg_spec
        assert 'domain' in arg_spec

    def test_unique_name_setter(self):
        obj = NewBase()
        obj.unique_name = 'new_unique_name'
        assert obj.unique_name == 'new_unique_name'
        assert obj._default_unique_name is False
        assert NewBase.by_name('new_unique_name') is obj
        # Old name should no longer resolve
        assert NewBase.by_name('NewBase_0') is None

    def test_unique_name_setter_invalid(self):
        obj = NewBase()
        with pytest.raises(TypeError, match='unique_name must be a string'):
            obj.unique_name = 789

    def test_default_display_name(self):
        obj = NewBase()
        assert obj.display_name == obj.unique_name
        assert obj._display_name is None

    def test_display_name_setter(self):
        obj = NewBase()
        obj.display_name = 'Pretty Name'
        assert obj.display_name == 'Pretty Name'
        assert obj._display_name == 'Pretty Name'

    def test_display_name_setter_invalid(self):
        obj = NewBase()
        with pytest.raises(TypeError, match='display_name must be a string or None'):
            obj.display_name = 101112

    def test_duplicate_explicit_name_raises_value_error(self):
        obj = NewBase(unique_name='dup_name')  # Keep reference
        with pytest.raises(ValueError, match='already exists'):
            NewBase(unique_name='dup_name')
        assert obj is not None  # Ensure reference kept

    def test_rename_collision_keeps_original_unique_name(self):
        first = NewBase(unique_name='first')
        second = NewBase(unique_name='second')  # Keep reference
        with pytest.raises(ValueError, match='already registered'):
            first.unique_name = 'second'
        assert first.unique_name == 'first'
        assert NewBase.by_name('first') is first
        assert second is not None  # Ensure reference kept

    def test_to_dict_full_params(self):
        obj = NewBase(unique_name='test_name', display_name='Test Object')
        obj_dict = obj.to_dict()
        assert isinstance(obj_dict, dict)
        assert obj_dict['unique_name'] == 'test_name'
        assert obj_dict['display_name'] == 'Test Object'
        assert obj_dict['@module'] == 'easyscience.base_classes.new_base'
        assert obj_dict['@class'] == 'NewBase'
        assert '@version' in obj_dict

    def test_to_dict_default_params(self):
        obj = NewBase()
        obj_dict = obj.to_dict()
        assert isinstance(obj_dict, dict)
        assert obj_dict['@module'] == 'easyscience.base_classes.new_base'
        assert obj_dict['@class'] == 'NewBase'
        assert '@version' in obj_dict
        assert 'unique_name' not in obj_dict
        assert 'display_name' not in obj_dict
        assert 'session' not in obj_dict

    def test_to_dict_with_skip(self):
        obj = NewBase(unique_name='skip_test', display_name='Skip Test Object')
        obj_dict = obj.to_dict(skip=['display_name'])
        assert isinstance(obj_dict, dict)
        assert obj_dict['unique_name'] == 'skip_test'
        assert 'display_name' not in obj_dict
        assert obj_dict['@module'] == 'easyscience.base_classes.new_base'
        assert obj_dict['@class'] == 'NewBase'
        assert '@version' in obj_dict

    def test_from_dict(self):
        obj_dict = {
            '@module': 'easyscience.base_classes.new_base',
            '@class': 'NewBase',
            'unique_name': 'from_dict_name',
            'display_name': 'From Dict Object',
        }
        obj = NewBase.from_dict(obj_dict)
        assert isinstance(obj, NewBase)
        assert obj.unique_name == 'from_dict_name'
        assert obj.display_name == 'From Dict Object'
        assert NewBase.by_name('from_dict_name') is obj

    def test_from_dict_not_easyscience(self):
        obj_dict = {
            '@module': 'some.other.module',
            '@class': 'NewBase',
            'unique_name': 'invalid_from_dict',
            'display_name': 'Invalid From Dict Object',
        }
        with pytest.raises(ValueError, match='Input must be a dictionary representing an EasyScience object.'):
            NewBase.from_dict(obj_dict)

    def test_from_dict_wrong_class(self):
        obj_dict = {
            '@module': 'easyscience.base_classes.new_base',
            '@class': 'SomeOtherClass',
            'unique_name': 'wrong_class_name',
            'display_name': 'Wrong Class Object',
        }
        with pytest.raises(ValueError, match='Class name in dictionary does not match NewBase'):
            NewBase.from_dict(obj_dict)

    def test__dir__(self):
        obj = NewBase()
        dir_list = dir(obj)
        expected_attributes = ['to_dict', 'unique_name', 'display_name', 'from_dict']
        for attr in expected_attributes:
            assert attr in dir_list

    def test_copy(self):
        obj = NewBase(unique_name='original_name', display_name='Original Object')
        obj_copy = obj.__copy__()
        assert isinstance(obj_copy, NewBase)
        assert obj_copy.unique_name != obj.unique_name
        assert obj_copy.display_name == obj.display_name
        assert NewBase.by_name(obj_copy.unique_name) is obj_copy

    def test_deepcopy(self):
        obj = NewBase(unique_name='deepcopy_name', display_name='Deep Copy Object')
        obj_deepcopy = copy.deepcopy(obj)
        assert isinstance(obj_deepcopy, NewBase)
        assert obj_deepcopy.unique_name != obj.unique_name
        assert obj_deepcopy.display_name == obj.display_name
        assert NewBase.by_name(obj_deepcopy.unique_name) is obj_deepcopy

    def test_gc_removes_object_from_session(self):
        """Test that objects are removed from session when GC'd."""
        session = Session()

        # Create object and get weak reference
        obj = NewBase(unique_name='gc_test', session=session)
        weak_ref = weakref.ref(obj)

        # Should be in session
        assert 'gc_test' in session.all_names()

        # Delete strong reference and force GC
        del obj
        gc.collect()

        # Should be removed from session
        assert weak_ref() is None
        assert 'gc_test' not in session.all_names()

    def test_domain_parameter(self):
        """Test that domain parameter works correctly."""
        session = Session()
        session.create_domain('custom')

        obj = NewBase(unique_name='domain_test', session=session, domain='custom')

        assert obj.domain == 'custom'
        assert session.contains('domain_test', domain='custom')
        assert not session.contains('domain_test', domain='__default__')

    def test_same_name_different_domains(self):
        """Test that same name can exist in different domains."""
        session = Session()
        session.create_domain('domain1')
        session.create_domain('domain2')

        obj1 = NewBase(unique_name='shared_name', session=session, domain='domain1')
        obj2 = NewBase(unique_name='shared_name', session=session, domain='domain2')

        assert obj1 is not obj2
        assert obj1.unique_name == obj2.unique_name
        assert session.get('shared_name', domain='domain1') is obj1
        assert session.get('shared_name', domain='domain2') is obj2


class TestSessionIsolation:
    """Test that sessions provide proper isolation."""

    def test_session_isolation_same_names(self):
        """Test that different sessions can have objects with identical names."""
        session1 = Session()
        session2 = Session()

        obj1 = NewBase(unique_name='test_obj', session=session1)
        obj2 = NewBase(unique_name='test_obj', session=session2)

        assert obj1.unique_name == 'test_obj'
        assert obj2.unique_name == 'test_obj'
        assert obj1.session is session1
        assert obj2.session is session2
        assert obj1 is not obj2

        # Can retrieve from correct session
        assert NewBase.by_name('test_obj', session=session1) is obj1
        assert NewBase.by_name('test_obj', session=session2) is obj2

    def test_session_isolation_different_names(self):
        """Test that sessions maintain separate name registries."""
        session1 = Session()
        session2 = Session()

        obj1 = NewBase(unique_name='obj1', session=session1)  # noqa: F841
        obj2 = NewBase(unique_name='obj2', session=session2)  # noqa: F841

        assert session1.all_names() == ['obj1']
        assert session2.all_names() == ['obj2']

        # Cross-session lookup should return None
        assert NewBase.by_name('obj1', session=session2) is None
        assert NewBase.by_name('obj2', session=session1) is None

    def test_session_isolation_auto_naming(self):
        """Test that auto-generated names are isolated per session."""
        session1 = Session()
        session2 = Session()

        obj1a = NewBase(session=session1)
        obj1b = NewBase(session=session1)
        obj2a = NewBase(session=session2)
        obj2b = NewBase(session=session2)

        assert obj1a.unique_name == 'NewBase_0'
        assert obj1b.unique_name == 'NewBase_1'
        assert obj2a.unique_name == 'NewBase_0'
        assert obj2b.unique_name == 'NewBase_1'

        assert session1.all_names() == ['NewBase_0', 'NewBase_1']
        assert session2.all_names() == ['NewBase_0', 'NewBase_1']

    def test_session_isolation_duplicate_names_within_session(self):
        """Test that duplicate names within the same session are rejected."""
        session = Session()
        obj = NewBase(unique_name='dup', session=session)  # Keep reference

        with pytest.raises(ValueError, match='already exists'):
            NewBase(unique_name='dup', session=session)
        assert obj is not None  # Ensure reference kept

    def test_session_isolation_duplicate_names_across_sessions_allowed(self):
        """Test that duplicate names across different sessions are allowed."""
        session1 = Session()
        session2 = Session()

        obj1 = NewBase(unique_name='same_name', session=session1)
        obj2 = NewBase(unique_name='same_name', session=session2)

        assert obj1.unique_name == 'same_name'
        assert obj2.unique_name == 'same_name'
        assert obj1.session is not obj2.session


class TestWeakRefCleanup:
    """Tests for automatic GC cleanup (replaces disposal tests)."""

    def test_gc_removes_from_session(self):
        """Test that GC removes object from session registry."""
        session = Session()
        obj = NewBase(unique_name='to_gc', session=session)
        weak_ref = weakref.ref(obj)

        assert 'to_gc' in session
        assert session.all_names() == ['to_gc']

        del obj
        gc.collect()

        assert 'to_gc' not in session
        assert session.all_names() == []
        assert weak_ref() is None

    def test_gc_with_children(self):
        """Test that GC'ing parent cleans up child relationships via unregister."""
        session = Session()
        parent = NewBase(unique_name='parent', session=session)
        child = NewBase(unique_name='child', session=session)

        parent.add_child(child)
        assert parent.get_children() == [child]
        assert child.get_parent() is parent

        # Delete parent - it will be GC'd
        del parent
        gc.collect()

        # Parent should be gone
        assert 'parent' not in session
        # Child should still exist
        assert 'child' in session
        # Note: Parent-child tracking uses names, so we need to manually clean up
        # if parent is GC'd without explicit unregister. This is expected behavior.

    def test_gc_with_parent_reference(self):
        """Test that GC'ing child affects parent references."""
        session = Session()
        parent = NewBase(unique_name='parent', session=session)
        child = NewBase(unique_name='child', session=session)

        parent.add_child(child)

        # Get children before GC
        assert parent.get_children() == [child]

        # Delete child
        del child
        gc.collect()

        # Child should be gone
        assert 'child' not in session
        # Parent should still exist
        assert 'parent' in session
        # get_children filters out None (GC'd objects)
        assert parent.get_children() == []


class TestInteractionWithExistingCode:
    """Test interaction with existing EasyScience code."""

    def test_serialization_preserves_session(self):
        """Test that serialization/deserialization works with sessions."""
        session = Session()
        obj = NewBase(unique_name='serialized', display_name='Test', session=session)

        # Serialize
        data = obj.to_dict()

        # Delete original to free the name (weak ref allows GC)
        del obj
        gc.collect()

        # Deserialize with same session
        restored = NewBase.from_dict(data, session=session)

        assert restored.unique_name == 'serialized'
        assert restored.display_name == 'Test'
        assert restored.session is session

    def test_serialization_without_session_uses_default(self):
        """Test that deserialization without explicit session uses default."""
        obj = NewBase(unique_name='default_session_test')

        data = obj.to_dict()

        # Delete original to free the name
        del obj
        gc.collect()

        restored = NewBase.from_dict(data)  # No session specified

        assert restored.unique_name == 'default_session_test'
        # Should be in default session
        assert NewBase.by_name('default_session_test') is restored

    def test_copy_preserves_session(self):
        """Test that copying preserves the session."""
        session = Session()
        obj = NewBase(unique_name='original', session=session)

        copied = obj.__copy__()

        assert copied.session is session
        assert copied.unique_name != 'original'  # Should get new name
        assert copied.display_name == obj.display_name

    def test_deepcopy_preserves_session(self):
        """Test that deep copying preserves the session."""
        session = Session()
        obj = NewBase(unique_name='deep_original', session=session)

        deep_copied = copy.deepcopy(obj)

        assert deep_copied.session is session
        assert deep_copied.unique_name != 'deep_original'
        assert deep_copied.display_name == obj.display_name

    def test_relationships_across_sessions_not_allowed(self):
        """Test that parent-child relationships cannot span sessions."""
        session1 = Session()
        session2 = Session()

        parent = NewBase(unique_name='parent', session=session1)
        child = NewBase(unique_name='child', session=session2)

        # This should raise an error
        with pytest.raises(ValueError, match='Cannot add child from different session'):
            parent.add_child(child)

    def test_session_thread_safety(self):
        """Test that session operations are thread-safe."""
        import threading
        import time

        session = Session()
        errors = []
        all_objects = []  # Keep strong references to prevent GC
        all_objects_lock = threading.Lock()

        def create_objects(thread_id):
            try:
                for i in range(10):
                    obj = NewBase(session=session)
                    with all_objects_lock:
                        all_objects.append(obj)  # Keep reference
                    time.sleep(0.001)  # Small delay to encourage race conditions
            except Exception as e:
                errors.append(f'Thread {thread_id}: {e}')

        threads = []
        for i in range(5):
            t = threading.Thread(target=create_objects, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0, f'Thread safety errors: {errors}'
        assert len(session.all_names()) == 50  # 5 threads * 10 objects each
        assert len(all_objects) == 50
