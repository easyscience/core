#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

from easyscience import Parameter
from easyscience import ObjBase
import pytest
import gc
from easyscience import global_object

class TestMap:
    @pytest.fixture
    def clear(self):
        global_object.map._clear()

    @pytest.fixture
    def base_object(self):
        return ObjBase(name="test")

    @pytest.fixture
    def parameter_object(self):
        return Parameter(value=2.0, name="test2")

    def test_add_vertex(self, clear, base_object, parameter_object):
        # When Then Expect
        assert len(global_object.map._store) == 2
        assert len(global_object.map._Map__type_dict) == 2

    def test_clear(self, clear, base_object):
        # When
        assert len(global_object.map._store) == 1
        assert len(global_object.map._Map__type_dict) == 1
        # Then
        global_object.map._clear()
        # Expect
        assert len(global_object.map._store) == 0
        assert global_object.map._Map__type_dict == {}

    def test_weakref(self, clear):
        # When
        test_obj = ObjBase(name="test")
        assert len(global_object.map._store) == 1
        assert len(global_object.map._Map__type_dict) == 1
        # Then
        del test_obj
        gc.collect()
        # Expect
        assert len(global_object.map._store) == 0
        assert len(global_object.map._Map__type_dict) == 0

    def test_vertices(self, clear, base_object, parameter_object):
        # When Then Expect
        assert global_object.map.vertices() == [base_object.unique_name, parameter_object.unique_name]

    def test_get_item_by_key(self, clear, base_object, parameter_object):
        # When Then Expect
        assert global_object.map.get_item_by_key(base_object.unique_name) == base_object
        assert global_object.map.get_item_by_key(parameter_object.unique_name) == parameter_object

    @pytest.mark.parametrize("cls, kwargs", [(ObjBase, {}), (Parameter, {"value": 2.0})])
    def test_identical_unique_names_auto_rename(self, clear, cls, kwargs):
        # When
        test_obj = cls(name="test", unique_name="test", **kwargs)
        original_unique_name = test_obj.unique_name
        # Then
        test_obj2 = cls(name="test2", unique_name="test", **kwargs)
        # Expect - the second object should be automatically renamed
        assert test_obj.unique_name == original_unique_name  # First object keeps original name
        assert test_obj2.unique_name == "test_1"  # Second object gets suffix
        assert test_obj.unique_name != test_obj2.unique_name  # Names are different
        # Both objects should be in the map with their respective names
        assert global_object.map.get_item_by_key(test_obj.unique_name) == test_obj
        assert global_object.map.get_item_by_key(test_obj2.unique_name) == test_obj2

    def test_multiple_identical_unique_names_increment(self, clear):
        # When - Create multiple objects with the same initial unique name
        obj1 = ObjBase(name="test1", unique_name="duplicate")
        obj2 = ObjBase(name="test2", unique_name="duplicate")
        obj3 = ObjBase(name="test3", unique_name="duplicate")

        # Expect - Each should get a unique incremented name
        assert obj1.unique_name == "duplicate"  # First keeps original
        assert obj2.unique_name == "duplicate_1"  # Second gets _1
        assert obj3.unique_name == "duplicate_2"  # Third gets _2

        # All should be accessible in the map
        assert global_object.map.get_item_by_key("duplicate") == obj1
        assert global_object.map.get_item_by_key("duplicate_1") == obj2
        assert global_object.map.get_item_by_key("duplicate_2") == obj3
        assert len(global_object.map._store) == 3

    def test_unique_name_change_still_in_map(self, clear, base_object, parameter_object):
        # When
        assert global_object.map.get_item_by_key("ObjBase_0") == base_object
        assert global_object.map.get_item_by_key("Parameter_0") == parameter_object
        # Then
        base_object.unique_name = "test3"
        parameter_object.unique_name = "test4"
        # Expect
        assert global_object.map.get_item_by_key("ObjBase_0") == base_object
        assert global_object.map.get_item_by_key("Parameter_0") == parameter_object
        assert global_object.map.get_item_by_key("test3") == base_object
        assert global_object.map.get_item_by_key("test4") == parameter_object

