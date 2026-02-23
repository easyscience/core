import copy

import pytest

from easyscience.base_classes import NewBase
from easyscience.base_classes.new_base import Session
from easyscience.base_classes.new_base import set_default_session


@pytest.fixture(autouse=True)
def fresh_default_session():
    set_default_session(Session())


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

    def test_unique_name_setter(self):
        obj = NewBase()
        obj.unique_name = 'new_unique_name'
        assert obj.unique_name == 'new_unique_name'
        assert obj._default_unique_name is False
        assert NewBase.by_name('new_unique_name') is obj
        with pytest.raises(KeyError, match="No object with unique_name 'NewBase_0'"):
            NewBase.by_name('NewBase_0')

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
        NewBase(unique_name='dup_name')
        with pytest.raises(ValueError, match="Duplicate unique_name 'dup_name'"):
            NewBase(unique_name='dup_name')

    def test_rename_collision_keeps_original_unique_name(self):
        first = NewBase(unique_name='first')
        NewBase(unique_name='second')
        with pytest.raises(ValueError, match="Cannot rename 'first' to 'second'"):
            first.unique_name = 'second'
        assert first.unique_name == 'first'
        assert NewBase.by_name('first') is first

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

    def test_dispose_is_enforced_and_idempotent(self):
        parent = NewBase(unique_name='parent')
        child = NewBase(unique_name='child')
        parent.add_child(child)

        parent.dispose()

        with pytest.raises(KeyError, match="No object with unique_name 'parent'"):
            NewBase.by_name('parent')

        with pytest.raises(RuntimeError, match="Object 'parent' has been disposed"):
            parent.display_name = 'new name'

        with pytest.raises(RuntimeError, match="Object 'parent' has been disposed"):
            parent.unique_name = 'parent_renamed'

        with pytest.raises(RuntimeError, match="Object 'parent' has been disposed"):
            parent.add_child(child)

        parent.dispose()


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

        obj1 = NewBase(unique_name='obj1', session=session1)
        obj2 = NewBase(unique_name='obj2', session=session2)

        assert session1.all_names() == ['obj1']
        assert session2.all_names() == ['obj2']

        # Cross-session lookup should fail
        with pytest.raises(KeyError):
            NewBase.by_name('obj1', session=session2)
        with pytest.raises(KeyError):
            NewBase.by_name('obj2', session=session1)

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
        NewBase(unique_name='dup', session=session)

        with pytest.raises(ValueError, match="Duplicate unique_name 'dup'"):
            NewBase(unique_name='dup', session=session)

    def test_session_isolation_duplicate_names_across_sessions_allowed(self):
        """Test that duplicate names across different sessions are allowed."""
        session1 = Session()
        session2 = Session()

        obj1 = NewBase(unique_name='same_name', session=session1)
        obj2 = NewBase(unique_name='same_name', session=session2)

        assert obj1.unique_name == 'same_name'
        assert obj2.unique_name == 'same_name'
        assert obj1.session is not obj2.session


class TestDisposal:
    """Comprehensive tests for object disposal functionality."""

    def test_disposal_removes_from_session(self):
        """Test that disposal removes object from session registry."""
        session = Session()
        obj = NewBase(unique_name='to_dispose', session=session)

        assert 'to_dispose' in session
        assert session.all_names() == ['to_dispose']

        obj.dispose()

        assert 'to_dispose' not in session
        assert session.all_names() == []

    def test_disposal_with_children(self):
        """Test that disposing parent also cleans up child relationships."""
        session = Session()
        parent = NewBase(unique_name='parent', session=session)
        child = NewBase(unique_name='child', session=session)

        parent.add_child(child)
        assert parent.get_children() == [child]
        assert child.get_parent() is parent

        parent.dispose()

        # Parent should be gone
        assert 'parent' not in session
        # Child should still exist but parent relationship should be cleaned up
        assert 'child' in session
        assert child.get_parent() is None

    def test_disposal_with_parent_reference(self):
        """Test that disposing child cleans up parent references."""
        session = Session()
        parent = NewBase(unique_name='parent', session=session)
        child = NewBase(unique_name='child', session=session)

        parent.add_child(child)
        child.dispose()

        # Child should be gone
        assert 'child' not in session
        # Parent should still exist but child reference should be cleaned up
        assert 'parent' in session
        assert parent.get_children() == []

    def test_disposal_prevents_modification(self):
        """Test that disposed objects cannot be modified."""
        obj = NewBase(unique_name='disposed_obj')

        obj.dispose()

        with pytest.raises(RuntimeError, match="Object 'disposed_obj' has been disposed"):
            obj.unique_name = 'new_name'

        with pytest.raises(RuntimeError, match="Object 'disposed_obj' has been disposed"):
            obj.display_name = 'new_display'

        with pytest.raises(RuntimeError, match="Object 'disposed_obj' has been disposed"):
            obj.add_child(NewBase())

    def test_disposal_idempotent(self):
        """Test that disposal can be called multiple times safely."""
        obj = NewBase(unique_name='idempotent')

        obj.dispose()
        obj.dispose()  # Should not raise

        assert 'idempotent' not in obj.session

    def test_disposal_lookup_fails(self):
        """Test that disposed objects cannot be looked up."""
        obj = NewBase(unique_name='lookup_test')

        obj.dispose()

        with pytest.raises(KeyError, match="No object with unique_name 'lookup_test'"):
            NewBase.by_name('lookup_test')


class TestInteractionWithExistingCode:
    """Test interaction with existing EasyScience code."""

    def test_serialization_preserves_session(self):
        """Test that serialization/deserialization works with sessions."""
        session = Session()
        obj = NewBase(unique_name='serialized', display_name='Test', session=session)

        # Serialize
        data = obj.to_dict()

        obj.dispose()  # Dispose original

        # Deserialize with same session
        restored = NewBase.from_dict(data, session=session)

        assert restored.unique_name == 'serialized'
        assert restored.display_name == 'Test'
        assert restored.session is session

    def test_serialization_without_session_uses_default(self):
        """Test that deserialization without explicit session uses default."""
        obj = NewBase(unique_name='default_session_test')

        data = obj.to_dict()
        obj.dispose()  # Dispose original to free the name
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

        def create_objects(thread_id):
            try:
                for i in range(10):
                    obj = NewBase(session=session)
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
