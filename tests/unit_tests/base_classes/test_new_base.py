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