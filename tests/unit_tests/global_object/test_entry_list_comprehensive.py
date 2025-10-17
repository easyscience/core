#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

import pytest
import weakref
from unittest.mock import MagicMock
from easyscience.global_object.map import _EntryList

class TestEntryListComprehensive:
    """Comprehensive tests for _EntryList class"""
    
    def test_inheritance(self):
        """Test that _EntryList properly inherits from list"""
        entry = _EntryList([1, 2, 3])
        
        # Should have list functionality
        assert len(entry) == 3
        assert entry[0] == 1
        assert 2 in entry
        
        # Can append like a normal list
        entry.append(4)
        assert len(entry) == 4
        
    def test_init_with_list_data(self):
        """Test initialization with existing list data"""
        data = ['a', 'b', 'c']
        entry = _EntryList(data, my_type='created')
        
        assert len(entry) == 3
        assert entry[0] == 'a'
        assert 'created' in entry.type
        
    def test_known_types_validation(self):
        """Test validation of known types"""
        entry = _EntryList()
        known_types = {'argument', 'created', 'created_internal', 'returned'}
        
        # Test all known types
        for known_type in known_types:
            entry.type = known_type
            assert known_type in entry.type
            
        # Test unknown type
        entry.type = 'unknown_type'
        assert 'unknown_type' not in entry.type
        
    def test_finalizer_attribute(self):
        """Test finalizer attribute handling"""
        entry = _EntryList()
        
        # Initially None
        assert entry.finalizer is None
        
        # Can set to any value
        mock_finalizer = MagicMock()
        entry.finalizer = mock_finalizer
        assert entry.finalizer is mock_finalizer
        
    def test_delitem_override(self):
        """Test __delitem__ override"""
        entry = _EntryList(['a', 'b', 'c'])
        
        # Should work like normal list deletion
        del entry[1]
        assert len(entry) == 2
        assert entry == ['a', 'c']
        
    def test_repr_variations(self):
        """Test various __repr__ scenarios"""
        # Empty type, no finalizer
        entry = _EntryList()
        repr_str = str(entry)
        assert 'Undefined' in repr_str
        assert 'Without' in repr_str
        
        # Single type, no finalizer
        entry.type = 'created'
        repr_str = str(entry)
        assert 'created' in repr_str
        assert 'Without' in repr_str
        
        # Multiple types, no finalizer
        entry.type = 'argument'
        repr_str = str(entry)
        assert 'created' in repr_str
        assert 'argument' in repr_str
        assert 'Without' in repr_str
        
        # With finalizer
        entry.finalizer = MagicMock()
        repr_str = str(entry)
        assert 'Without' not in repr_str
        
    def test_type_setter_edge_cases(self):
        """Test edge cases for type setter"""
        entry = _EntryList()
        
        # Setting None should not crash
        entry.type = None
        assert None not in entry.type
        
        # Setting empty string
        entry.type = ""
        assert "" not in entry.type
        
        # Setting numeric value
        entry.type = 123
        assert 123 not in entry.type
        
    def test_remove_type_edge_cases(self):
        """Test edge cases for remove_type"""
        entry = _EntryList()
        entry.type = 'created'
        entry.type = 'argument'
        
        # Remove type that exists
        entry.remove_type('created')
        assert 'created' not in entry.type
        assert 'argument' in entry.type
        
        # Remove type that doesn't exist
        entry.remove_type('returned')  # Not in list
        assert 'argument' in entry.type  # Should be unchanged
        
        # Remove unknown type
        entry.remove_type('unknown')
        assert 'argument' in entry.type  # Should be unchanged
        
        # Remove None
        entry.remove_type(None)
        assert 'argument' in entry.type  # Should be unchanged
        
    def test_reset_type_variations(self):
        """Test reset_type with various inputs"""
        entry = _EntryList()
        entry.type = 'created'
        entry.type = 'argument'
        
        # Reset with valid type
        entry.reset_type('returned')
        assert entry.type == ['returned']
        
        # Reset with invalid type
        entry.type = 'created'  # Add something first
        entry.reset_type('invalid')
        assert entry.type == []  # Should be empty since invalid
        
        # Reset with None
        entry.type = 'created'
        entry.reset_type(None)
        assert entry.type == []
        
    def test_boolean_properties_combinations(self):
        """Test boolean properties with multiple types"""
        entry = _EntryList()
        
        # Add multiple types
        entry.type = 'created'
        entry.type = 'argument'
        entry.type = 'returned'
        
        # All should be true
        assert entry.is_created
        assert entry.is_argument
        assert entry.is_returned
        assert not entry.is_created_internal  # Not added
        
        # Remove one
        entry.remove_type('argument')
        assert entry.is_created
        assert not entry.is_argument
        assert entry.is_returned
        
    def test_list_functionality_preserved(self):
        """Test that list functionality is preserved"""
        entry = _EntryList()
        
        # Basic list operations
        entry.append('a')
        entry.append('b')
        entry.insert(1, 'x')
        assert entry == ['a', 'x', 'b']
        
        # List methods
        assert entry.index('x') == 1
        assert entry.count('a') == 1
        
        # Slicing
        subset = entry[1:]
        assert subset == ['x', 'b']
        
        # Iteration
        items = [item for item in entry]
        assert items == ['a', 'x', 'b']
        
    def test_type_persistence_during_list_operations(self):
        """Test that type information persists during list operations"""
        entry = _EntryList(my_type='created')
        entry.type = 'argument'
        
        # Perform list operations
        entry.append('item1')
        entry.extend(['item2', 'item3'])
        entry.sort()
        
        # Type information should be preserved
        assert entry.is_created
        assert entry.is_argument
        
    def test_equality_with_regular_list(self):
        """Test equality comparison with regular list"""
        entry = _EntryList(['a', 'b', 'c'])
        regular_list = ['a', 'b', 'c']
        
        # Should be equal in content
        assert entry == regular_list
        assert regular_list == entry
        
        # But not the same type
        assert type(entry) != type(regular_list)
        assert isinstance(entry, _EntryList)
        assert isinstance(entry, list)
        
    def test_copy_behavior(self):
        """Test copying behavior"""
        import copy
        
        entry = _EntryList(['a', 'b'], my_type='created')
        entry.finalizer = MagicMock()
        
        # Shallow copy
        shallow_copy = copy.copy(entry)
        assert shallow_copy == entry
        assert shallow_copy.type == entry.type
        assert shallow_copy.finalizer is entry.finalizer
        
        # Deep copy
        deep_copy = copy.deepcopy(entry)
        assert deep_copy == entry
        assert deep_copy.type == entry.type
        # Finalizer might be different in deep copy
        
    def test_memory_efficiency(self):
        """Test that _EntryList doesn't consume excessive memory"""
        # Create many entries
        entries = []
        for i in range(1000):
            entry = _EntryList([f"item_{i}"], my_type='created')
            entries.append(entry)
            
        # Should not raise memory errors
        assert len(entries) == 1000
        assert all(entry.is_created for entry in entries)
        
    def test_thread_safety_simulation(self):
        """Test basic thread safety aspects (simulation)"""
        import threading
        import time
        
        entry = _EntryList()
        results = []
        
        def add_type(type_name, delay=0.001):
            time.sleep(delay)
            entry.type = type_name
            results.append(type_name)
            
        # Simulate concurrent access
        threads = []
        for i, type_name in enumerate(['created', 'argument', 'returned']):
            thread = threading.Thread(target=add_type, args=(type_name,))
            threads.append(thread)
            
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()
            
        # All types should be added (order might vary)
        assert len(set(entry.type)) == 3
        assert all(t in entry.type for t in ['created', 'argument', 'returned'])
        
    def test_pickle_serialization(self):
        """Test pickle serialization support"""
        import pickle
        
        entry = _EntryList(['a', 'b', 'c'], my_type='created')
        entry.type = 'argument'
        
        # Serialize
        pickled = pickle.dumps(entry)
        
        # Deserialize
        unpickled = pickle.loads(pickled)
        
        # Should preserve data and types
        assert unpickled == entry
        assert unpickled.type == entry.type
        assert unpickled.is_created
        assert unpickled.is_argument
        
    def test_subclassing(self):
        """Test that _EntryList can be subclassed"""
        class CustomEntryList(_EntryList):
            def __init__(self, *args, custom_attr=None, **kwargs):
                super().__init__(*args, **kwargs)
                self.custom_attr = custom_attr
                
            def custom_method(self):
                return f"Custom: {len(self)} items"
                
        custom = CustomEntryList(['x', 'y'], my_type='created', custom_attr="test")
        
        assert custom.custom_attr == "test"
        assert custom.custom_method() == "Custom: 2 items"
        assert custom.is_created
        assert len(custom) == 2