#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

from easyscience import Parameter
from easyscience import ObjBase
import pytest
import gc
import weakref
import numpy as np
from unittest.mock import MagicMock, patch
from easyscience import global_object
from easyscience.global_object.map import _EntryList, Map

class TestEntryList:
    """Test the _EntryList helper class"""
    
    def test_init_default(self):
        """Test _EntryList initialization with defaults"""
        entry = _EntryList()
        assert entry._type == []
        assert entry.finalizer is None
        
    def test_init_with_known_type(self):
        """Test _EntryList initialization with known type"""
        entry = _EntryList(my_type='created')
        assert 'created' in entry._type
        
    def test_init_with_unknown_type(self):
        """Test _EntryList initialization with unknown type"""
        entry = _EntryList(my_type='unknown')
        assert entry._type == []
        
    def test_repr(self):
        """Test string representation"""
        entry = _EntryList()
        repr_str = str(entry)
        assert 'Undefined' in repr_str
        assert 'finalizer' in repr_str
        
        entry.type = 'created'
        repr_str = str(entry)
        assert 'created' in repr_str
        assert 'finalizer' in repr_str
        
    def test_type_property_getter(self):
        """Test type property getter"""
        entry = _EntryList()
        assert entry.type == []
        
    def test_type_property_setter_valid(self):
        """Test type property setter with valid types"""
        entry = _EntryList()
        entry.type = 'created'
        assert 'created' in entry.type
        
        entry.type = 'argument'
        assert 'argument' in entry.type
        assert 'created' in entry.type  # Should be additive
        
    def test_type_property_setter_invalid(self):
        """Test type property setter with invalid type"""
        entry = _EntryList()
        entry.type = 'invalid'
        assert entry.type == []
        
    def test_type_property_setter_duplicate(self):
        """Test type property setter doesn't add duplicates"""
        entry = _EntryList()
        entry.type = 'created'
        entry.type = 'created'  # Try to add again
        assert entry.type.count('created') == 1
        
    def test_remove_type(self):
        """Test removing a type"""
        entry = _EntryList()
        entry.type = 'created'
        entry.type = 'argument'
        
        entry.remove_type('created')
        assert 'created' not in entry.type
        assert 'argument' in entry.type
        
    def test_remove_type_not_present(self):
        """Test removing a type that's not present"""
        entry = _EntryList()
        entry.type = 'created'
        entry.remove_type('argument')  # Not present
        assert 'created' in entry.type
        
    def test_reset_type(self):
        """Test resetting types"""
        entry = _EntryList()
        entry.type = 'created'
        entry.type = 'argument'
        
        entry.reset_type('returned')
        assert entry.type == ['returned']
        
    def test_reset_type_default_none(self):
        """Test resetting types with no default"""
        entry = _EntryList()
        entry.type = 'created'
        
        entry.reset_type()
        assert entry.type == []
        
    def test_boolean_properties(self):
        """Test boolean property helpers"""
        entry = _EntryList()
        
        # Test all false initially
        assert not entry.is_argument
        assert not entry.is_created
        assert not entry.is_created_internal
        assert not entry.is_returned
        
        # Test each property
        entry.type = 'argument'
        assert entry.is_argument
        
        entry.type = 'created'
        assert entry.is_created
        
        entry.type = 'created_internal'
        assert entry.is_created_internal
        
        entry.type = 'returned'
        assert entry.is_returned

class TestMap:
    @pytest.fixture
    def clear(self):
        global_object.map._clear()

    @pytest.fixture
    def base_object(self):
        return ObjBase(name="test")

    @pytest.fixture
    def parameter_object(self):
        return Parameter(name="test2", value=2)

    def test_add_vertex(self, clear, base_object, parameter_object):
        # When Then Expect
        assert len(global_object.map._Map__store) == 2
        assert len(global_object.map._Map__type_dict) == 2

    def test_clear(self, clear, base_object):
        # When
        assert len(global_object.map._Map__store) == 1
        assert len(global_object.map._Map__type_dict) == 1
        # Then
        global_object.map._clear()
        # Expect
        assert len(global_object.map._Map__store) == 0
        assert global_object.map._Map__type_dict == {}

    def test_weakref(self, clear):
        # When
        test_obj = ObjBase(name="test")
        assert len(global_object.map._Map__store) == 1
        assert len(global_object.map._Map__type_dict) == 1
        # Then
        del test_obj
        gc.collect()
        # Expect
        assert len(global_object.map._Map__store) == 0
        assert len(global_object.map._Map__type_dict) == 0

    def test_vertices(self, clear, base_object, parameter_object):
        # When Then Expect
        assert global_object.map.vertices() == [base_object.unique_name, parameter_object.unique_name]

    def test_get_item_by_key(self, clear, base_object, parameter_object):
        # When Then Expect
        assert global_object.map.get_item_by_key(base_object.unique_name) == base_object
        assert global_object.map.get_item_by_key(parameter_object.unique_name) == parameter_object

    @pytest.mark.parametrize("cls, kwargs", [(ObjBase, {}), (Parameter, {"value": 2.0})])
    def test_identical_unique_names_exception(self, clear, cls, kwargs):
        # When
        test_obj = cls(name="test", unique_name="test", **kwargs)
        # Then Expect
        with pytest.raises(ValueError):
            test_obj2 = cls(name="test2", unique_name="test", **kwargs)

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

    def test_add_vertex_duplicate_name_error(self, clear, base_object):
        """Test that adding vertex with duplicate name raises error"""
        # When/Then
        with pytest.raises(ValueError, match="already exists"):
            # Try to add another object with same unique_name
            duplicate_obj = ObjBase(name="duplicate", unique_name=base_object.unique_name)
            
    def test_add_vertex_with_object_type(self, clear):
        """Test adding vertex with specific object type"""
        # Given
        obj = ObjBase(name="test")
        
        # When - Object is automatically added during construction
        # Then
        assert global_object.map.is_known(obj)
        assert 'created' in global_object.map.find_type(obj)
        
    def test_is_known_object(self, clear, base_object):
        """Test is_known method"""
        # When/Then
        assert global_object.map.is_known(base_object) is True
        
        # Test with unknown object
        unknown_obj = MagicMock()
        unknown_obj.unique_name = "unknown"
        assert global_object.map.is_known(unknown_obj) is False
        
    def test_find_type_known_object(self, clear, base_object):
        """Test find_type method"""
        # When/Then
        types = global_object.map.find_type(base_object)
        assert isinstance(types, list)
        assert 'created' in types
        
    def test_find_type_unknown_object(self, clear):
        """Test find_type with unknown object"""
        # Given
        unknown_obj = MagicMock()
        unknown_obj.unique_name = "unknown"
        
        # When/Then
        result = global_object.map.find_type(unknown_obj)
        assert result is None
        
    def test_reset_type(self, clear, base_object):
        """Test resetting object type"""
        # Given
        original_types = global_object.map.find_type(base_object)
        
        # When
        global_object.map.reset_type(base_object, 'argument')
        
        # Then
        new_types = global_object.map.find_type(base_object)
        assert new_types == ['argument']
        assert new_types != original_types
        
    def test_change_type(self, clear, base_object):
        """Test changing object type"""
        # Given
        original_types = global_object.map.find_type(base_object)
        original_count = len(original_types)
        
        # When
        global_object.map.change_type(base_object, 'argument')
        
        # Then
        new_types = global_object.map.find_type(base_object)
        assert 'argument' in new_types
        assert len(new_types) >= original_count  # Should be at least the same or more
        
    def test_add_edge(self, clear, base_object, parameter_object):
        """Test adding edges between objects"""
        # When
        global_object.map.add_edge(base_object, parameter_object)
        
        # Then
        edges = global_object.map.get_edges(base_object)
        assert parameter_object.unique_name in edges
        
    def test_add_edge_unknown_start_object(self, clear, parameter_object):
        """Test adding edge with unknown start object"""
        # Given
        unknown_obj = MagicMock()
        unknown_obj.unique_name = "unknown"
        
        # When/Then
        with pytest.raises(AttributeError, match="Start object not in map"):
            global_object.map.add_edge(unknown_obj, parameter_object)
            
    def test_get_edges(self, clear, base_object, parameter_object):
        """Test getting edges for an object"""
        # Given
        global_object.map.add_edge(base_object, parameter_object)
        
        # When
        edges = global_object.map.get_edges(base_object)
        
        # Then
        assert isinstance(edges, list)
        assert parameter_object.unique_name in edges
        
    def test_get_edges_unknown_object(self, clear):
        """Test getting edges for unknown object"""
        # Given
        unknown_obj = MagicMock()
        unknown_obj.unique_name = "unknown"
        
        # When/Then
        with pytest.raises(AttributeError):
            global_object.map.get_edges(unknown_obj)
            
    def test_prune_vertex_from_edge(self, clear, base_object, parameter_object):
        """Test removing edge between objects"""
        # Given
        global_object.map.add_edge(base_object, parameter_object)
        assert parameter_object.unique_name in global_object.map.get_edges(base_object)
        
        # When
        global_object.map.prune_vertex_from_edge(base_object, parameter_object)
        
        # Then
        edges = global_object.map.get_edges(base_object)
        assert parameter_object.unique_name not in edges
        
    def test_prune_vertex_from_edge_none_child(self, clear, base_object):
        """Test pruning edge with None child"""
        # When/Then - Should not raise error
        global_object.map.prune_vertex_from_edge(base_object, None)
        
    def test_prune_vertex(self, clear, base_object):
        """Test pruning a vertex completely"""
        # Given
        unique_name = base_object.unique_name
        assert global_object.map.is_known(base_object)
        
        # When
        global_object.map.prune(unique_name)
        
        # Then
        assert not global_object.map.is_known(base_object)
        assert unique_name not in global_object.map.vertices()
        
    def test_edges_generation(self, clear, base_object, parameter_object):
        """Test edge generation"""
        # Given
        global_object.map.add_edge(base_object, parameter_object)
        
        # When
        edges = global_object.map.edges()
        
        # Then
        assert isinstance(edges, list)
        expected_edge = {base_object.unique_name, parameter_object.unique_name}
        assert expected_edge in edges
        
    def test_type_filtering_properties(self, clear):
        """Test type filtering properties"""
        # Given
        obj1 = ObjBase(name="obj1")  # 'created' type
        obj2 = Parameter(name="obj2", value=1)  # 'created' type
        
        global_object.map.change_type(obj1, 'argument')
        global_object.map.change_type(obj2, 'returned')
        
        # When/Then
        argument_objs = global_object.map.argument_objs
        created_objs = global_object.map.created_objs
        returned_objs = global_object.map.returned_objs
        
        assert obj1.unique_name in argument_objs
        assert obj1.unique_name in created_objs  # Should still be there
        assert obj2.unique_name in created_objs
        assert obj2.unique_name in returned_objs
        
    def test_find_path_simple(self, clear, base_object, parameter_object):
        """Test finding path between objects"""
        # Given
        global_object.map.add_edge(base_object, parameter_object)
        
        # When
        path = global_object.map.find_path(base_object.unique_name, parameter_object.unique_name)
        
        # Then
        assert path == [base_object.unique_name, parameter_object.unique_name]
        
    def test_find_path_same_vertex(self, clear, base_object):
        """Test finding path to same vertex"""
        # When
        path = global_object.map.find_path(base_object.unique_name, base_object.unique_name)
        
        # Then
        assert path == [base_object.unique_name]
        
    def test_find_path_no_path(self, clear, base_object, parameter_object):
        """Test finding path when no path exists"""
        # When - No edge added
        path = global_object.map.find_path(base_object.unique_name, parameter_object.unique_name)
        
        # Then
        assert path == []
        
    def test_find_all_paths(self, clear, base_object, parameter_object):
        """Test finding all paths between objects"""
        # Given
        global_object.map.add_edge(base_object, parameter_object)
        
        # When
        paths = global_object.map.find_all_paths(base_object.unique_name, parameter_object.unique_name)
        
        # Then
        assert len(paths) == 1
        assert paths[0] == [base_object.unique_name, parameter_object.unique_name]
        
    def test_reverse_route_with_start(self, clear, base_object, parameter_object):
        """Test reverse route with specified start"""
        # Given
        global_object.map.add_edge(base_object, parameter_object)
        
        # When
        route = global_object.map.reverse_route(parameter_object.unique_name, base_object.unique_name)
        
        # Then
        assert route == [parameter_object.unique_name, base_object.unique_name]
        
    def test_reverse_route_without_start(self, clear, base_object, parameter_object):
        """Test reverse route without specified start"""
        # Given
        global_object.map.add_edge(base_object, parameter_object)
        
        # When
        route = global_object.map.reverse_route(parameter_object.unique_name)
        
        # Then
        assert len(route) >= 1
        assert route[0] == parameter_object.unique_name
        
    def test_is_connected_single_vertex(self, clear, base_object):
        """Test connectivity with single vertex"""
        # When/Then
        assert global_object.map.is_connected() is True
        
    def test_is_connected_multiple_vertices(self, clear, base_object, parameter_object):
        """Test connectivity with multiple connected vertices"""
        # Given
        global_object.map.add_edge(base_object, parameter_object)
        
        # When/Then
        assert global_object.map.is_connected() is True
        
    def test_map_repr(self, clear, base_object, parameter_object):
        """Test map string representation"""
        # When
        repr_str = str(global_object.map)
        
        # Then
        assert "Map object" in repr_str
        assert "2" in repr_str  # Should show vertex count
        
    def test_get_item_by_key_not_found(self, clear):
        """Test getting item by non-existent key"""
        # When/Then
        with pytest.raises(ValueError, match="Item not in map"):
            global_object.map.get_item_by_key("non_existent")
            
    def test_clear_with_finalizers(self, clear):
        """Test clearing map properly calls finalizers"""
        # Given
        obj = ObjBase(name="test")
        original_count = len(global_object.map.vertices())
        
        # When
        global_object.map._clear()
        
        # Then
        assert len(global_object.map.vertices()) == 0
        
    def test_map_initialization(self):
        """Test Map initialization"""
        # When
        test_map = Map()
        
        # Then
        assert len(test_map.vertices()) == 0
        assert test_map.edges() == []

