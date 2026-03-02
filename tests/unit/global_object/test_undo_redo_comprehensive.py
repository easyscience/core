# SPDX-FileCopyrightText: 2021-2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from easyscience.global_object.undo_redo import CommandHolder
from easyscience.global_object.undo_redo import DictStack
from easyscience.global_object.undo_redo import DictStackReCreate
from easyscience.global_object.undo_redo import FunctionStack
from easyscience.global_object.undo_redo import NotarizedDict
from easyscience.global_object.undo_redo import PropertyStack
from easyscience.global_object.undo_redo import UndoCommand
from easyscience.global_object.undo_redo import UndoStack
from easyscience.global_object.undo_redo import dict_stack_deco
from easyscience.global_object.undo_redo import property_stack


class MockUndoCommand(UndoCommand):
    """Mock implementation for testing"""

    def __init__(self, obj, text=None):
        super().__init__(obj)
        if text:
            self.text = text
        self.undo_called = False
        self.redo_called = False

    def undo(self):
        self.undo_called = True

    def redo(self):
        self.redo_called = True


class TestUndoCommand:
    """Test abstract UndoCommand base class"""

    def test_init(self):
        """Test UndoCommand initialization"""
        obj = MagicMock()
        cmd = MockUndoCommand(obj)

        assert cmd._obj is obj
        assert cmd._text is None

    def test_text_property(self):
        """Test text property getter/setter"""
        cmd = MockUndoCommand(MagicMock())

        # Test getter
        assert cmd.text is None

        # Test setter
        cmd.text = 'test text'
        assert cmd.text == 'test text'

    def test_abstract_methods(self):
        """Test that abstract methods are implemented"""
        cmd = MockUndoCommand(MagicMock())

        # Should not raise NotImplementedError
        cmd.undo()
        cmd.redo()
        assert cmd.undo_called
        assert cmd.redo_called


class TestCommandHolder:
    """Test CommandHolder class"""

    def test_init_default(self):
        """Test CommandHolder initialization"""
        holder = CommandHolder()
        assert len(holder) == 0
        assert holder.text == ''
        assert not holder.is_macro

    def test_init_with_text(self):
        """Test CommandHolder initialization with text"""
        holder = CommandHolder('test text')
        assert holder._text == 'test text'

    def test_append_and_pop(self):
        """Test appending and popping commands"""
        holder = CommandHolder()
        cmd = MockUndoCommand(MagicMock())

        holder.append(cmd)
        assert len(holder) == 1
        assert holder.current is cmd

        popped = holder.pop()
        assert popped is cmd
        assert len(holder) == 0

    def test_iteration(self):
        """Test iteration over commands"""
        holder = CommandHolder()
        cmd1 = MockUndoCommand(MagicMock(), 'cmd1')
        cmd2 = MockUndoCommand(MagicMock(), 'cmd2')

        holder.append(cmd1)
        holder.append(cmd2)

        commands = list(holder)
        assert len(commands) == 2
        assert cmd2 in commands  # Last appended should be first (LIFO)

    def test_is_macro_property(self):
        """Test is_macro property"""
        holder = CommandHolder()
        assert not holder.is_macro

        holder.append(MockUndoCommand(MagicMock()))
        assert not holder.is_macro

        holder.append(MockUndoCommand(MagicMock()))
        assert holder.is_macro

    def test_text_property_with_commands(self):
        """Test text property with commands"""
        holder = CommandHolder()
        cmd = MockUndoCommand(MagicMock(), 'command text')
        holder.append(cmd)

        assert holder.text == 'command text'

    def test_text_property_override(self):
        """Test text property with override"""
        holder = CommandHolder('override text')
        cmd = MockUndoCommand(MagicMock(), 'command text')
        holder.append(cmd)

        assert holder.text == 'override text'


class TestUndoStack:
    """Test UndoStack class"""

    @pytest.fixture
    def stack(self):
        """Create a fresh UndoStack for each test"""
        return UndoStack()

    def test_init_default(self, stack):
        """Test UndoStack initialization"""
        assert stack.enabled is False
        assert len(stack.history) == 0
        assert len(stack.future) == 0
        assert not stack._macro_running
        assert not stack._command_running

    def test_init_with_max_history(self):
        """Test UndoStack initialization with max history"""
        stack = UndoStack(max_history=5)
        assert stack._max_history == 5
        assert stack.history.maxlen == 5
        assert stack.future.maxlen == 5

    def test_enabled_property(self, stack):
        """Test enabled property getter/setter"""
        assert not stack.enabled

        stack.enabled = True
        assert stack.enabled

        stack.enabled = False
        assert not stack.enabled

    def test_enabled_setter_with_running_macro(self, stack):
        """Test that setting enabled=False ends running macro"""
        stack.enabled = True
        stack.beginMacro('test')
        assert stack._macro_running

        stack.enabled = False
        assert not stack._macro_running

    def test_force_state(self, stack):
        """Test force_state method"""
        stack.force_state(True)
        assert stack.enabled

        stack.force_state(False)
        assert not stack.enabled

    def test_push_disabled_stack(self, stack):
        """Test pushing command to disabled stack"""
        cmd = MockUndoCommand(MagicMock())

        stack.push(cmd)

        assert cmd.redo_called
        assert len(stack.history) == 0

    def test_push_enabled_stack(self, stack):
        """Test pushing command to enabled stack"""
        stack.enabled = True
        cmd = MockUndoCommand(MagicMock())

        stack.push(cmd)

        assert cmd.redo_called
        assert len(stack.history) == 1
        assert len(stack.future) == 0

    def test_push_with_macro(self, stack):
        """Test pushing command during macro"""
        stack.enabled = True
        stack.beginMacro('test macro')

        cmd1 = MockUndoCommand(MagicMock())
        cmd2 = MockUndoCommand(MagicMock())

        stack.push(cmd1)
        stack.push(cmd2)

        assert len(stack.history) == 1  # Only the macro holder
        assert len(stack.history[0]) == 2  # Two commands in the macro

    def test_push_clears_future(self, stack):
        """Test that push clears future stack"""
        stack.enabled = True
        cmd1 = MockUndoCommand(MagicMock())
        cmd2 = MockUndoCommand(MagicMock())

        stack.push(cmd1)
        stack.undo()
        assert len(stack.future) == 1

        stack.push(cmd2)
        assert len(stack.future) == 0

    def test_pop(self, stack):
        """Test popping last command"""
        stack.enabled = True
        cmd = MockUndoCommand(MagicMock())

        stack.push(cmd)
        popped = stack.pop()

        assert popped is cmd
        assert len(stack.history) == 0

    def test_pop_from_macro(self, stack):
        """Test popping from macro"""
        stack.enabled = True
        stack.beginMacro('test')

        cmd1 = MockUndoCommand(MagicMock())
        cmd2 = MockUndoCommand(MagicMock())

        stack.push(cmd1)
        stack.push(cmd2)

        popped = stack.pop()
        assert popped is cmd2
        assert len(stack.history[0]) == 1  # One command left in macro

    def test_clear(self, stack):
        """Test clearing the stack"""
        stack.enabled = True
        stack.push(MockUndoCommand(MagicMock()))
        stack.beginMacro('test')

        stack.clear()

        assert len(stack.history) == 0
        assert len(stack.future) == 0
        assert not stack._macro_running

    def test_undo_success(self, stack):
        """Test successful undo operation"""
        stack.enabled = True
        cmd = MockUndoCommand(MagicMock())

        stack.push(cmd)
        stack.undo()

        assert cmd.undo_called
        assert len(stack.history) == 0
        assert len(stack.future) == 1

    def test_undo_cannot_undo(self, stack):
        """Test undo when cannot undo"""
        assert not stack.canUndo()
        stack.undo()  # Should not raise error

    def test_undo_with_exception(self, stack):
        """Test undo with exception in command"""
        stack.enabled = True

        class FailingCommand(UndoCommand):
            def undo(self):
                raise Exception('test error')

            def redo(self):
                pass

        cmd = FailingCommand(MagicMock())
        stack.push(cmd)

        # Should not raise, just print error
        stack.undo()

    def test_redo_success(self, stack):
        """Test successful redo operation"""
        stack.enabled = True
        cmd = MockUndoCommand(MagicMock())

        stack.push(cmd)
        stack.undo()
        stack.redo()

        assert cmd.redo_called
        assert len(stack.history) == 1
        assert len(stack.future) == 0

    def test_redo_cannot_redo(self, stack):
        """Test redo when cannot redo"""
        assert not stack.canRedo()
        stack.redo()  # Should not raise error

    def test_macro_operations(self, stack):
        """Test macro begin/end operations"""
        stack.enabled = True

        stack.beginMacro('test macro')
        assert stack._macro_running

        cmd1 = MockUndoCommand(MagicMock())
        cmd2 = MockUndoCommand(MagicMock())
        stack.push(cmd1)
        stack.push(cmd2)

        stack.endMacro()
        assert not stack._macro_running

        # Undo should undo both commands
        stack.undo()
        assert cmd1.undo_called
        assert cmd2.undo_called

    def test_macro_nested_error(self, stack):
        """Test error on nested macro"""
        stack.enabled = True
        stack.beginMacro('test1')

        with pytest.raises(AssertionError, match='already running'):
            stack.beginMacro('test2')

    def test_end_macro_without_begin_error(self, stack):
        """Test error on ending macro without begin"""
        stack.enabled = True

        with pytest.raises(AssertionError, match='not running'):
            stack.endMacro()

    def test_can_undo_redo_states(self, stack):
        """Test canUndo/canRedo state checking"""
        assert not stack.canUndo()
        assert not stack.canRedo()

        stack.enabled = True
        cmd = MockUndoCommand(MagicMock())
        stack.push(cmd)

        assert stack.canUndo()
        assert not stack.canRedo()

        stack.undo()
        assert not stack.canUndo()
        assert stack.canRedo()

    def test_can_undo_redo_during_macro(self, stack):
        """Test canUndo/canRedo during macro"""
        stack.enabled = True
        stack.push(MockUndoCommand(MagicMock()))

        stack.beginMacro('test')
        assert not stack.canUndo()  # Cannot undo during macro
        assert not stack.canRedo()  # Cannot redo during macro

    def test_undo_redo_text(self, stack):
        """Test undo/redo text retrieval"""
        stack.enabled = True
        cmd = MockUndoCommand(MagicMock(), 'test command')

        stack.push(cmd)
        assert stack.undoText() == 'test command'
        assert stack.redoText() == ''

        stack.undo()
        assert stack.undoText() == ''
        assert stack.redoText() == 'test command'


class TestPropertyStack:
    """Test PropertyStack command"""

    def test_init(self):
        """Test PropertyStack initialization"""
        parent = MagicMock()
        func = MagicMock()
        old_value = 10
        new_value = 20

        cmd = PropertyStack(parent, func, old_value, new_value)

        assert cmd._parent is parent
        assert cmd._set_func is func
        assert cmd._old_value == old_value
        assert cmd._new_value == new_value
        assert '10' in cmd.text and '20' in cmd.text

    def test_init_with_custom_text(self):
        """Test PropertyStack with custom text"""
        cmd = PropertyStack(MagicMock(), MagicMock(), 10, 20, 'custom text')
        assert cmd.text == 'custom text'

    def test_undo_redo(self):
        """Test PropertyStack undo/redo"""
        parent = MagicMock()
        func = MagicMock()

        cmd = PropertyStack(parent, func, 10, 20)

        cmd.undo()
        func.assert_called_once_with(parent, 10)

        func.reset_mock()
        cmd.redo()
        func.assert_called_once_with(parent, 20)


class TestFunctionStack:
    """Test FunctionStack command"""

    def test_init(self):
        """Test FunctionStack initialization"""
        parent = MagicMock()
        set_func = MagicMock()
        unset_func = MagicMock()

        cmd = FunctionStack(parent, set_func, unset_func)

        assert cmd._parent is parent
        assert cmd._old_fn is set_func
        assert cmd._new_fn is unset_func

    def test_undo_redo(self):
        """Test FunctionStack undo/redo"""
        set_func = MagicMock()
        unset_func = MagicMock()

        cmd = FunctionStack(MagicMock(), set_func, unset_func)

        cmd.undo()
        unset_func.assert_called_once()

        cmd.redo()
        set_func.assert_called_once()


class TestNotarizedDict:
    """Test NotarizedDict class"""

    def test_init(self):
        """Test NotarizedDict initialization"""
        nd = NotarizedDict(a=1, b=2)

        assert nd['a'] == 1
        assert nd['b'] == 2
        assert not nd._stack_enabled

    def test_setitem_without_stack(self):
        """Test setitem without stack enabled"""
        nd = NotarizedDict()
        nd['key'] = 'value'

        assert nd['key'] == 'value'

    def test_delitem_without_stack(self):
        """Test delitem without stack enabled"""
        nd = NotarizedDict(key='value')
        del nd['key']

        assert 'key' not in nd

    def test_reorder_without_stack(self):
        """Test reorder without stack enabled"""
        nd = NotarizedDict(a=1, b=2)
        nd.reorder(b=2, a=1)

        assert list(nd.keys()) == ['b', 'a']

    def test_repr(self):
        """Test string representation"""
        nd = NotarizedDict(a=1)
        repr_str = repr(nd)

        assert 'NotarizedDict' in repr_str
        assert "'a': 1" in repr_str


class TestDictStack:
    """Test DictStack command"""

    def test_init_deletion(self):
        """Test DictStack initialization for deletion"""
        nd = NotarizedDict(key='value')
        cmd = DictStack(nd, 'key')

        assert cmd._deletion is True
        assert cmd._creation is False
        assert cmd._key == 'key'
        assert cmd._old_value == 'value'
        assert cmd._index == 0

    def test_init_creation(self):
        """Test DictStack initialization for creation"""
        nd = NotarizedDict()
        cmd = DictStack(nd, 'key', 'value')

        assert cmd._creation is True
        assert cmd._deletion is False
        assert cmd._key == 'key'
        assert cmd._new_value == 'value'

    def test_init_modification(self):
        """Test DictStack initialization for modification"""
        nd = NotarizedDict(key='old_value')
        cmd = DictStack(nd, 'key', 'new_value')

        assert not cmd._creation
        assert not cmd._deletion
        assert cmd._old_value == 'old_value'
        assert cmd._new_value == 'new_value'

    def test_undo_redo_creation(self):
        """Test undo/redo for creation"""
        nd = NotarizedDict()
        cmd = DictStack(nd, 'key', 'value')

        # Simulate the initial operation (like UndoStack.push() does)
        cmd.redo()
        assert nd.data['key'] == 'value'

        # After creation, undo should delete the key
        cmd.undo()
        assert 'key' not in nd.data

        # After undo, redo should create/set new value
        cmd.redo()
        assert nd.data['key'] == 'value'

    def test_undo_redo_modification(self):
        """Test undo/redo for modification"""
        nd = NotarizedDict()
        nd['key'] = 'old_value'
        cmd = DictStack(nd, 'key', 'new_value')

        # Simulate the initial operation (like UndoStack.push() does)
        cmd.redo()
        assert nd.data['key'] == 'new_value'

        # After modification, undo should revert to old value
        cmd.undo()
        assert nd.data['key'] == 'old_value'

        # After undo, redo should set new value
        cmd.redo()
        assert nd.data['key'] == 'new_value'

    def test_undo_redo_deletion(self):
        """Test undo/redo for deletion"""
        nd = NotarizedDict(key='value')
        cmd = DictStack(nd, 'key')

        # Simulate the initial operation (like UndoStack.push() does)
        cmd.redo()
        assert 'key' not in nd.data

        # After deletion, undo should restore
        cmd.undo()
        assert nd.data['key'] == 'value'

        # After undo, redo should delete
        cmd.redo()
        assert 'key' not in nd.data


class TestDictStackReCreate:
    """Test DictStackReCreate command"""

    def test_init(self):
        """Test DictStackReCreate initialization"""
        nd = NotarizedDict(a=1, b=2)
        new_dict = {'c': 3, 'd': 4}

        cmd = DictStackReCreate(nd, **new_dict)

        assert cmd._old_value == {'a': 1, 'b': 2}
        assert cmd._new_value == new_dict

    def test_undo_redo(self):
        """Test undo/redo operations"""
        nd = NotarizedDict(a=1, b=2)
        old_data = nd.data.copy()
        new_dict = {'c': 3, 'd': 4}

        cmd = DictStackReCreate(nd, **new_dict)

        cmd.undo()
        assert nd.data == old_data

        cmd.redo()
        assert nd.data == new_dict


class TestPropertyStackDecorator:
    """Test property_stack decorator"""

    def test_decorator_without_args(self):
        """Test decorator applied without arguments"""

        @property_stack
        def test_func(obj, value):
            obj.value = value

        assert hasattr(test_func, 'func')

    def test_decorator_with_string_arg(self):
        """Test decorator applied with string argument"""

        @property_stack('Custom text')
        def test_func(obj, value):
            obj.value = value

        assert hasattr(test_func, 'func')

    def test_decorator_no_change_no_push(self):
        """Test decorator doesn't push when value unchanged"""

        class TestObj:
            def __init__(self):
                self.value = 10

        @property_stack
        def value(obj, new_value):
            obj.value = new_value

        obj = TestObj()

        with patch('easyscience.global_object') as mock_global:
            mock_stack = MagicMock()
            mock_global.stack = mock_stack

            value(obj, 10)  # Same value

            # Should NOT have pushed anything since value didn't change
            mock_stack.push.assert_not_called()


class TestDictStackDecorator:
    """Test dict_stack_deco decorator"""

    def test_decorator_with_stack_disabled(self):
        """Test decorator when stack is disabled"""
        nd = NotarizedDict()
        nd._stack_enabled = False

        @dict_stack_deco
        def test_func(obj, key, value):
            obj[key] = value

        # Should call the function directly
        with patch('easyscience.global_object') as mock_global:
            mock_stack = MagicMock()
            mock_global.stack = mock_stack
            test_func(nd, 'key', 'value')
            mock_stack.push.assert_not_called()

    def test_decorator_with_stack_enabled(self):
        """Test decorator when stack is enabled"""
        nd = NotarizedDict()
        nd._stack_enabled = True

        @dict_stack_deco
        def test_func(obj, key, value):
            pass  # Don't actually modify

        with patch('easyscience.global_object') as mock_global:
            mock_stack = MagicMock()
            mock_global.stack = mock_stack

            test_func(nd, 'key', 'value')

            # Should push a DictStack command
            mock_stack.push.assert_called_once()
            args = mock_stack.push.call_args[0]
            assert isinstance(args[0], DictStack)
