import pytest
import easyscience
from easyscience.global_object.global_object import GlobalObject
from easyscience.variable import DescriptorBool
from easyscience import Parameter, ObjBase, global_object
from unittest.mock import patch, MagicMock

class TestGlobalObject:
    def test_init(self):
        # When Then
        global_object = GlobalObject()

        # Expect
        assert global_object.log == GlobalObject().log 
        assert global_object.map == GlobalObject().map
        assert global_object.stack == GlobalObject().stack
        assert global_object.debug == GlobalObject().debug

    def test_generate_unique_name(self):
        # When Then
        global_object = GlobalObject()
        name = global_object.generate_unique_name("name_prefix")

        # Expect
        assert name == "name_prefix_0"

    def test_generate_unique_name_already_taken(self):
        # When
        global_object = GlobalObject()
        # Block the other_name_prefix_2 name
        keep_due_toweakref_1 = DescriptorBool(name="test", value=True, unique_name="other_name_prefix_2")
        keep_due_toweakref_2 = DescriptorBool(name="test", value=True, unique_name="other_name_prefix_a_3")
        keep_due_toweakref_3 = DescriptorBool(name="test", value=True, unique_name="almost_other_name_prefix_3")

        # Then 
        name = global_object.generate_unique_name("other_name_prefix")

        # Expect
        assert name == "other_name_prefix_3"

    @pytest.fixture
    def clear_global_map(self):
        """Clear global map and name counters before and after each test"""
        global_object.map._clear()
        yield
        global_object.map._clear()

    def test_singleton_behavior(self):
        """Test that GlobalObject is truly a singleton"""
        # When
        obj1 = GlobalObject()
        obj2 = GlobalObject()
        
        # Then
        assert obj1 is obj2
        assert id(obj1) == id(obj2)
        assert obj1.map is obj2.map
        assert obj1.log is obj2.log

    def test_instantiate_stack(self, clear_global_map):
        """Test stack instantiation"""
        # Given
        global_obj = GlobalObject()
        
        # When
        global_obj.instantiate_stack()
        
        # Then
        assert global_obj.stack is not None
        from easyscience.global_object.undo_redo import UndoStack
        assert isinstance(global_obj.stack, UndoStack)

    def test_debug_property(self):
        """Test debug property access"""
        # Given
        global_obj = GlobalObject()
        
        # When/Then
        assert global_obj.debug is False  # Default value
        
        # Test that it's the same across instances
        global_obj2 = GlobalObject()
        assert global_obj.debug is global_obj2.debug

    def test_generate_unique_name_empty_map(self, clear_global_map):
        """Test unique name generation with empty map"""
        # Given
        global_obj = GlobalObject()
        
        # When
        name = global_obj.generate_unique_name("test")
        
        # Then
        assert name == "test_0"

    def test_generate_unique_name_with_gaps(self, clear_global_map):
        """Test unique name generation with gaps in numbering"""
        # Given
        global_obj = GlobalObject()
        # Create objects with non-sequential names
        keep1 = DescriptorBool(name="test", value=True, unique_name="prefix_0")
        keep2 = DescriptorBool(name="test", value=True, unique_name="prefix_2") 
        keep3 = DescriptorBool(name="test", value=True, unique_name="prefix_5")
        
        # When
        name = global_obj.generate_unique_name("prefix")
        
        # Then - Should pick the highest + 1
        assert name == "prefix_6"

    def test_generate_unique_name_non_numeric_suffix(self, clear_global_map):
        """Test that non-numeric suffixes are ignored"""
        # Given
        global_obj = GlobalObject()
        keep1 = DescriptorBool(name="test", value=True, unique_name="prefix_abc")
        keep2 = DescriptorBool(name="test", value=True, unique_name="prefix_1")
        
        # When
        name = global_obj.generate_unique_name("prefix")
        
        # Then
        assert name == "prefix_2"

    def test_generate_unique_name_similar_prefixes(self, clear_global_map):
        """Test that similar but different prefixes don't interfere"""
        # Given
        global_obj = GlobalObject()
        keep1 = DescriptorBool(name="test", value=True, unique_name="test_param_5")
        keep2 = DescriptorBool(name="test", value=True, unique_name="test_parameter_10")
        
        # When
        name1 = global_obj.generate_unique_name("test_param")
        name2 = global_obj.generate_unique_name("test_parameter")
        
        # Then
        assert name1 == "test_param_6"
        assert name2 == "test_parameter_11"

    def test_integration_with_parameter_creation(self, clear_global_map):
        """Test GlobalObject integration with Parameter creation"""
        # Given
        global_obj = GlobalObject()
        
        # When
        param1 = Parameter(name="test1", value=1.0)
        param2 = Parameter(name="test2", value=2.0)
        
        # Then
        assert len(global_obj.map.vertices()) == 2
        assert param1.unique_name in global_obj.map.vertices()
        assert param2.unique_name in global_obj.map.vertices()
        
        # Test retrieval
        retrieved1 = global_obj.map.get_item_by_key(param1.unique_name)
        assert retrieved1 is param1

    def test_unique_names_not_reused_after_gc(self, clear_global_map):
        """Test that unique names are never reused after objects are garbage collected."""
        import gc

        # Given
        global_obj = GlobalObject()

        # Create parameters and record their unique names
        param1 = Parameter(name="a", value=1.0)
        param2 = Parameter(name="b", value=2.0)
        name1 = param1.unique_name
        name2 = param2.unique_name
        assert name1 != name2

        # Delete the parameters so they get GC'd from the WeakValueDictionary
        del param1, param2
        gc.collect()

        # The map should no longer contain the old names (weak refs collected)
        assert name1 not in global_obj.map.vertices()
        assert name2 not in global_obj.map.vertices()

        # Create new parameters — they must NOT reuse the old names
        param3 = Parameter(name="c", value=3.0)
        param4 = Parameter(name="d", value=4.0)
        assert param3.unique_name != name1
        assert param3.unique_name != name2
        assert param4.unique_name != name1
        assert param4.unique_name != name2
        assert param3.unique_name != param4.unique_name

    def test_script_manager_access(self):
        """Test that script manager is accessible"""
        # Given
        global_obj = GlobalObject()
        
        # Then
        assert hasattr(global_obj, 'script')
        from easyscience.global_object.hugger.hugger import ScriptManager
        assert isinstance(global_obj.script, ScriptManager)
