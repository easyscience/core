#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

import pytest
from easyscience import global_object
from easyscience.base_classes import NewBase

class TestNewBase:

    @pytest.fixture
    def clear(self):
        # Clear the global object map before each test
        global_object.map._clear()

    def test_constructor_defaults(self, clear):
        # When Then
        obj = NewBase()
        # Expect
        assert obj._unique_name == 'NewBase_0'
        assert obj._default_unique_name is True
        assert obj._display_name is None
        assert global_object.map.get_item_by_key('NewBase_0') is obj

    def test_constructor_with_arguments(self):
        # When Then
        obj = NewBase(unique_name="custom_name", display_name="My Object")
        # Expect
        assert obj._unique_name == "custom_name"
        assert obj._default_unique_name is False
        assert obj._display_name == "My Object"
        assert global_object.map.get_item_by_key("custom_name") is obj

    def test_constructor_invalid_unique_name(self):
        # When Then Expect
        with pytest.raises(TypeError, match='Unique name has to be a string.'):
            NewBase(unique_name=123)

    def test_constructor_invalid_display_name(self):
        # When Then Expect
        with pytest.raises(TypeError, match='Display name must be a string or None'):
            NewBase(display_name=456)

    def test_arg_spec(self):
        # When
        obj = NewBase()
        # Then
        arg_spec = obj._arg_spec
        # Expect
        assert 'unique_name' in arg_spec
        assert 'display_name' in arg_spec

    def test_unique_name_setter(self, clear):
        # When
        obj = NewBase()
        # Then
        obj.unique_name = "new_unique_name"
        # Expect
        assert obj.unique_name == "new_unique_name"
        assert obj._default_unique_name is False
        assert global_object.map.get_item_by_key("new_unique_name") is obj
        assert global_object.map.get_item_by_key("NewBase_0") is obj

    def test_unique_name_setter_invalid(self):
        # When
        obj = NewBase()
        # Then Expect
        with pytest.raises(TypeError, match='Unique name has to be a string.'):
            obj.unique_name = 789

    def test_default_display_name(self):
        # When
        obj = NewBase()
        # Then
        display_name = obj.display_name
        # Expect
        assert display_name == obj.unique_name
        assert obj._display_name is None

    def test_display_name_setter(self):
        # When
        obj = NewBase()
        # Then
        obj.display_name = "Pretty Name"
        # Expect
        assert obj.display_name == "Pretty Name"
        assert obj._display_name == "Pretty Name"

    def test_display_name_setter_invalid(self):
        # When
        obj = NewBase()
        # Then Expect
        with pytest.raises(TypeError, match='Display name must be a string or None'):
            obj.display_name = 101112

    def test_as_dict_full_params(self):
        # When
        obj = NewBase(unique_name="test_name", display_name="Test Object")
        # Then
        obj_dict = obj.as_dict()
        # Expect
        assert isinstance(obj_dict, dict)
        assert obj_dict['unique_name'] == "test_name"
        assert obj_dict['display_name'] == "Test Object"
        assert obj_dict['@module'] == 'easyscience.base_classes.new_base'
        assert obj_dict['@class'] == 'NewBase'
        assert '@version' in obj_dict

    def test_as_dict_default_params(self):
        # When
        obj = NewBase()
        # Then
        obj_dict = obj.as_dict()
        # Expect
        assert isinstance(obj_dict, dict)
        assert obj_dict['@module'] == 'easyscience.base_classes.new_base'
        assert obj_dict['@class'] == 'NewBase'
        assert '@version' in obj_dict
        assert 'unique_name' not in obj_dict
        assert 'display_name' not in obj_dict

    def test_as_dict_with_skip(self):
        # When
        obj = NewBase(unique_name="skip_test", display_name="Skip Test Object")
        # Then
        obj_dict = obj.as_dict(skip=['display_name'])
        # Expect
        assert isinstance(obj_dict, dict)
        assert obj_dict['unique_name'] == "skip_test"
        assert 'display_name' not in obj_dict
        assert obj_dict['@module'] == 'easyscience.base_classes.new_base'
        assert obj_dict['@class'] == 'NewBase'
        assert '@version' in obj_dict