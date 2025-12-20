#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

import pytest

import easyscience
from easyscience import global_object
from easyscience import Parameter
from easyscience import DescriptorNumber
from easyscience.base_classes import ModelCollection
from easyscience.base_classes import ModelBase
from easyscience.base_classes import NewBase
from easyscience.fitting.calculators import InterfaceFactoryTemplate


class MockModelItem(ModelBase):
    """A simple mock model item for testing ModelCollection."""

    def __init__(self, name: str = 'item', value: float = 0.0, unique_name=None, display_name=None):
        super().__init__(unique_name=unique_name, display_name=display_name)
        self._name = name
        self._value = Parameter(name='value', value=value)

    @property
    def name(self) -> str:
        return self._name

    @property
    def value(self) -> Parameter:
        return self._value

    @value.setter
    def value(self, new_value: float) -> None:
        self._value.value = new_value


class DerivedModelCollection(ModelCollection):
    """A derived class for testing inheritance."""
    pass


class_constructors = [ModelCollection, DerivedModelCollection]


@pytest.fixture
def clear_global():
    """Clear the global object map before each test."""
    global_object.map._clear()
    yield
    global_object.map._clear()


@pytest.fixture
def sample_items():
    """Create sample items for testing."""
    return [
        MockModelItem(name='item1', value=1.0),
        MockModelItem(name='item2', value=2.0),
        MockModelItem(name='item3', value=3.0),
    ]


# =============================================================================
# Constructor Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_init_empty(cls, clear_global):
    """Test creating an empty collection."""
    coll = cls()
    assert len(coll) == 0
    assert coll.interface is None


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_init_with_items(cls, clear_global, sample_items):
    """Test creating a collection with initial items."""
    coll = cls(*sample_items)
    assert len(coll) == 3
    for i, item in enumerate(coll):
        assert item.name == sample_items[i].name


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_init_with_unique_name(cls, clear_global):
    """Test creating a collection with a custom unique_name."""
    coll = cls(unique_name='custom_unique')
    assert coll.unique_name == 'custom_unique'


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_init_with_display_name(cls, clear_global):
    """Test creating a collection with a custom display_name."""
    coll = cls(display_name='My Display Name')
    assert coll.display_name == 'My Display Name'


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_init_with_list_arg(cls, clear_global, sample_items):
    """Test creating a collection with a list of items (should flatten)."""
    coll = cls(sample_items)
    assert len(coll) == 3


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_init_type_error(cls, clear_global):
    """Test that adding non-NewBase items raises TypeError."""
    with pytest.raises(TypeError):
        cls('not_a_newbase_object')


# =============================================================================
# Interface Property Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_interface_default(cls, clear_global):
    """Test that interface defaults to None."""
    coll = cls()
    assert coll.interface is None


@pytest.mark.parametrize('cls', class_constructors)
@pytest.mark.filterwarnings('ignore::DeprecationWarning')
def test_ModelCollection_interface_propagation(cls, clear_global, sample_items):
    """Test that setting interface propagates to items."""
    # Add interface attribute to items for this test
    for item in sample_items:
        item.interface = None

    coll = cls(*sample_items)

    # Create a mock interface that inherits from InterfaceFactoryTemplate
    class MockInterfaceClass:
        name = "MockInterface"
        def __init__(self, *args, **kwargs):
            pass
        def fit_func(self, *args, **kwargs):
            return "result"
        def create(self, model):
            return []

    mock_interface = InterfaceFactoryTemplate([MockInterfaceClass])
    coll.interface = mock_interface

    assert coll.interface is mock_interface
    for item in coll:
        assert item.interface is mock_interface


@pytest.mark.parametrize('cls', class_constructors)
@pytest.mark.filterwarnings('ignore::DeprecationWarning')
def test_ModelCollection_interface_type_error(cls, clear_global):
    """Test that setting an invalid interface type raises TypeError."""
    coll = cls()
    
    with pytest.raises(TypeError, match='interface must be'):
        coll.interface = 'not_an_interface'


@pytest.mark.parametrize('cls', class_constructors)
@pytest.mark.filterwarnings('ignore::DeprecationWarning')
def test_ModelCollection_interface_type_error_with_object(cls, clear_global):
    """Test that setting a plain object as interface raises TypeError."""
    coll = cls()
    
    class NotAnInterface:
        pass
    
    with pytest.raises(TypeError, match='interface must be'):
        coll.interface = NotAnInterface()


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_interface_accepts_none(cls, clear_global, sample_items):
    """Test that setting interface to None is allowed."""
    coll = cls(*sample_items)
    coll.interface = None
    assert coll.interface is None


# =============================================================================
# __getitem__ Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_getitem_int(cls, clear_global, sample_items):
    """Test getting items by integer index."""
    coll = cls(*sample_items)
    assert coll[0].name == 'item1'
    assert coll[1].name == 'item2'
    assert coll[2].name == 'item3'
    assert coll[-1].name == 'item3'


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_getitem_int_out_of_range(cls, clear_global, sample_items):
    """Test that out of range index raises IndexError."""
    coll = cls(*sample_items)
    with pytest.raises(IndexError):
        _ = coll[100]


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_getitem_slice(cls, clear_global, sample_items):
    """Test getting items by slice."""
    coll = cls(*sample_items)
    sliced = coll[0:2]
    assert isinstance(sliced, cls)
    assert len(sliced) == 2
    assert sliced[0].name == 'item1'
    assert sliced[1].name == 'item2'


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_getitem_str_by_name(cls, clear_global, sample_items):
    """Test getting items by name string."""
    coll = cls(*sample_items)
    item = coll['item2']
    assert item.name == 'item2'


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_getitem_str_by_unique_name(cls, clear_global, sample_items):
    """Test getting items by unique_name string."""
    coll = cls(*sample_items)
    unique_name = sample_items[1].unique_name
    item = coll[unique_name]
    assert item.unique_name == unique_name


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_getitem_str_not_found(cls, clear_global, sample_items):
    """Test that getting non-existent name raises KeyError."""
    coll = cls(*sample_items)
    with pytest.raises(KeyError):
        _ = coll['nonexistent']


# =============================================================================
# __setitem__ Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_setitem_int(cls, clear_global, sample_items):
    """Test setting items by integer index."""
    coll = cls(*sample_items)
    new_item = MockModelItem(name='new_item', value=99.0)
    old_item = coll[1]

    coll[1] = new_item

    assert len(coll) == 3
    assert coll[1].name == 'new_item'
    assert coll[1].value.value == 99.0

    # Check graph edges
    edges = global_object.map.get_edges(coll)
    assert new_item.unique_name in edges
    assert old_item.unique_name not in edges


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_setitem_type_error(cls, clear_global, sample_items):
    """Test that setting non-NewBase item raises TypeError."""
    coll = cls(*sample_items)
    with pytest.raises(TypeError):
        coll[0] = 'not_a_newbase_object'


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_setitem_slice(cls, clear_global, sample_items):
    """Test setting items by slice."""
    coll = cls(*sample_items)
    new_items = [
        MockModelItem(name='new1', value=10.0),
        MockModelItem(name='new2', value=20.0),
    ]

    coll[0:2] = new_items

    assert len(coll) == 3
    assert coll[0].name == 'new1'
    assert coll[1].name == 'new2'
    assert coll[2].name == 'item3'


# =============================================================================
# __delitem__ Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_delitem_int(cls, clear_global, sample_items):
    """Test deleting items by integer index."""
    coll = cls(*sample_items)
    deleted_item = coll[1]

    del coll[1]

    assert len(coll) == 2
    assert coll[0].name == 'item1'
    assert coll[1].name == 'item3'

    # Check graph edges
    edges = global_object.map.get_edges(coll)
    assert deleted_item.unique_name not in edges


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_delitem_slice(cls, clear_global, sample_items):
    """Test deleting items by slice."""
    coll = cls(*sample_items)

    del coll[0:2]

    assert len(coll) == 1
    assert coll[0].name == 'item3'


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_delitem_str_by_name(cls, clear_global, sample_items):
    """Test deleting items by name string."""
    coll = cls(*sample_items)

    del coll['item2']

    assert len(coll) == 2
    assert 'item2' not in [item.name for item in coll]


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_delitem_str_not_found(cls, clear_global, sample_items):
    """Test that deleting non-existent name raises KeyError."""
    coll = cls(*sample_items)
    with pytest.raises(KeyError):
        del coll['nonexistent']


# =============================================================================
# __len__ Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
@pytest.mark.parametrize('count', [0, 1, 3, 5])
def test_ModelCollection_len(cls, clear_global, count):
    """Test __len__ returns correct count."""
    items = [MockModelItem(name=f'item{i}', value=float(i)) for i in range(count)]
    coll = cls(*items)
    assert len(coll) == count


# =============================================================================
# insert Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_insert(cls, clear_global, sample_items):
    """Test inserting items at an index."""
    coll = cls(*sample_items)
    new_item = MockModelItem(name='inserted', value=99.0)

    coll.insert(1, new_item)

    assert len(coll) == 4
    assert coll[0].name == 'item1'
    assert coll[1].name == 'inserted'
    assert coll[2].name == 'item2'
    assert coll[3].name == 'item3'

    # Check graph edges
    edges = global_object.map.get_edges(coll)
    assert new_item.unique_name in edges


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_insert_type_error(cls, clear_global, sample_items):
    """Test that inserting non-NewBase item raises TypeError."""
    coll = cls(*sample_items)
    with pytest.raises(TypeError):
        coll.insert(0, 'not_a_newbase_object')


# =============================================================================
# append Tests (inherited from MutableSequence)
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_append(cls, clear_global, sample_items):
    """Test appending items."""
    coll = cls(*sample_items)
    new_item = MockModelItem(name='appended', value=99.0)

    coll.append(new_item)

    assert len(coll) == 4
    assert coll[-1].name == 'appended'

    # Check graph edges
    edges = global_object.map.get_edges(coll)
    assert new_item.unique_name in edges


# =============================================================================
# data Property Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_data_property(cls, clear_global, sample_items):
    """Test that data property returns tuple of items."""
    coll = cls(*sample_items)
    data = coll.data
    assert isinstance(data, tuple)
    assert len(data) == 3
    for i, item in enumerate(data):
        assert item.name == sample_items[i].name


# =============================================================================
# sort Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_sort(cls, clear_global):
    """Test sorting the collection."""
    items = [
        MockModelItem(name='c', value=3.0),
        MockModelItem(name='a', value=1.0),
        MockModelItem(name='b', value=2.0),
    ]
    coll = cls(*items)

    coll.sort(lambda x: x.value.value)

    assert coll[0].name == 'a'
    assert coll[1].name == 'b'
    assert coll[2].name == 'c'


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_sort_reverse(cls, clear_global):
    """Test sorting the collection in reverse."""
    items = [
        MockModelItem(name='a', value=1.0),
        MockModelItem(name='c', value=3.0),
        MockModelItem(name='b', value=2.0),
    ]
    coll = cls(*items)

    coll.sort(lambda x: x.value.value, reverse=True)

    assert coll[0].name == 'c'
    assert coll[1].name == 'b'
    assert coll[2].name == 'a'


# =============================================================================
# __repr__ Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_repr(cls, clear_global, sample_items):
    """Test string representation."""
    coll = cls(*sample_items)
    repr_str = repr(coll)
    assert cls.__name__ in repr_str
    assert '3' in repr_str


# =============================================================================
# __iter__ Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_iter(cls, clear_global, sample_items):
    """Test iteration over collection."""
    coll = cls(*sample_items)

    names = [item.name for item in coll]
    assert names == ['item1', 'item2', 'item3']


# =============================================================================
# get_all_variables Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_get_all_variables(cls, clear_global, sample_items):
    """Test getting all variables from items."""
    coll = cls(*sample_items)
    variables = coll.get_all_variables()

    # Each MockModelItem has one Parameter (value)
    assert len(variables) == 3
    for var in variables:
        assert isinstance(var, Parameter)


# =============================================================================
# get_all_parameters Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_get_all_parameters(cls, clear_global, sample_items):
    """Test getting all parameters from items."""
    coll = cls(*sample_items)
    parameters = coll.get_all_parameters()

    assert len(parameters) == 3
    for param in parameters:
        assert isinstance(param, Parameter)


# =============================================================================
# get_fit_parameters Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_get_fit_parameters(cls, clear_global, sample_items):
    """Test getting fit parameters from items."""
    # Fix one parameter so we can test filtering
    sample_items[0].value.fixed = True

    coll = cls(*sample_items)
    fit_params = coll.get_fit_parameters()

    # All 3 parameters should be returned (get_fit_parameters on items)
    # since MockModelItem.get_fit_parameters returns free params
    assert len(fit_params) == 2


# =============================================================================
# Graph Edge Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_graph_edges(cls, clear_global, sample_items):
    """Test that graph edges are correctly maintained."""
    coll = cls(*sample_items)

    edges = global_object.map.get_edges(coll)
    assert len(edges) == 3

    for item in sample_items:
        assert item.unique_name in edges


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_graph_edges_after_append(cls, clear_global, sample_items):
    """Test graph edges are updated after append."""
    coll = cls(*sample_items)
    new_item = MockModelItem(name='new', value=99.0)

    coll.append(new_item)

    edges = global_object.map.get_edges(coll)
    assert len(edges) == 4
    assert new_item.unique_name in edges


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_graph_edges_after_delete(cls, clear_global, sample_items):
    """Test graph edges are updated after delete."""
    coll = cls(*sample_items)
    deleted_item = sample_items[1]

    del coll[1]

    edges = global_object.map.get_edges(coll)
    assert len(edges) == 2
    assert deleted_item.unique_name not in edges


# =============================================================================
# MutableSequence Interface Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_extend(cls, clear_global, sample_items):
    """Test extend method (inherited from MutableSequence)."""
    coll = cls(sample_items[0])
    coll.extend([sample_items[1], sample_items[2]])

    assert len(coll) == 3
    assert coll[1].name == 'item2'
    assert coll[2].name == 'item3'


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_pop(cls, clear_global, sample_items):
    """Test pop method (inherited from MutableSequence)."""
    coll = cls(*sample_items)

    popped = coll.pop()
    assert popped.name == 'item3'
    assert len(coll) == 2


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_pop_index(cls, clear_global, sample_items):
    """Test pop method with index (inherited from MutableSequence)."""
    coll = cls(*sample_items)

    popped = coll.pop(0)
    assert popped.name == 'item1'
    assert len(coll) == 2
    assert coll[0].name == 'item2'


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_remove(cls, clear_global, sample_items):
    """Test remove method (inherited from MutableSequence)."""
    coll = cls(*sample_items)
    item_to_remove = sample_items[1]

    coll.remove(item_to_remove)

    assert len(coll) == 2
    assert item_to_remove not in coll


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_clear(cls, clear_global, sample_items):
    """Test clear method (inherited from MutableSequence)."""
    coll = cls(*sample_items)

    coll.clear()

    assert len(coll) == 0


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_reverse(cls, clear_global, sample_items):
    """Test reverse method (inherited from MutableSequence)."""
    coll = cls(*sample_items)

    coll.reverse()

    assert coll[0].name == 'item3'
    assert coll[1].name == 'item2'
    assert coll[2].name == 'item1'


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_count(cls, clear_global, sample_items):
    """Test count method (inherited from MutableSequence)."""
    coll = cls(*sample_items)

    count = coll.count(sample_items[0])
    assert count == 1


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_index(cls, clear_global, sample_items):
    """Test index method (inherited from MutableSequence)."""
    coll = cls(*sample_items)

    idx = coll.index(sample_items[1])
    assert idx == 1


# =============================================================================
# Contains Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_contains(cls, clear_global, sample_items):
    """Test __contains__ (in operator)."""
    coll = cls(*sample_items)

    assert sample_items[0] in coll
    assert sample_items[1] in coll

    new_item = MockModelItem(name='not_in_collection', value=999.0)
    assert new_item not in coll

@pytest.mark.parametrize('cls', class_constructors)
@pytest.mark.filterwarnings('ignore::DeprecationWarning')
def test_ModelCollection_init_with_interface_propagates_to_items(cls, clear_global, sample_items):
    """Test that interface passed to __init__ propagates to items."""
    for item in sample_items:
        item.interface = None

    class MockInterfaceClass:
        name = "MockInterface"
        def __init__(self, *args, **kwargs):
            pass
        def fit_func(self, *args, **kwargs):
            return "result"
        def create(self, model):
            return []

    mock_interface = InterfaceFactoryTemplate([MockInterfaceClass])
    coll = cls(*sample_items, interface=mock_interface)

    assert coll.interface is mock_interface
    for item in coll:
        assert item.interface is mock_interface


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_duplicate_items_silently_ignored(cls, clear_global):
    """Test that adding the same object twice only stores one copy."""
    item = MockModelItem(name='dupe', value=1.0)

    coll = cls(item, item)

    assert len(coll) == 1
    edges = global_object.map.get_edges(coll)
    assert edges == [item.unique_name]


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_delitem_str_by_unique_name(cls, clear_global, sample_items):
    """Test deleting items by unique_name string."""
    coll = cls(*sample_items)
    unique_name = sample_items[1].unique_name

    del coll[unique_name]

    assert len(coll) == 2
    assert sample_items[1] not in coll


@pytest.mark.parametrize('cls', class_constructors)
@pytest.mark.filterwarnings('ignore::DeprecationWarning')
def test_ModelCollection_setitem_int_with_interface_propagation(cls, clear_global, sample_items):
    """Test that setitem with int propagates interface to new item."""
    for item in sample_items:
        item.interface = None

    class MockInterfaceClass:
        name = "MockInterface"
        def __init__(self, *args, **kwargs):
            pass
        def fit_func(self, *args, **kwargs):
            return "result"
        def create(self, model):
            return []

    mock_interface = InterfaceFactoryTemplate([MockInterfaceClass])
    coll = cls(*sample_items)
    coll.interface = mock_interface

    new_item = MockModelItem(name='new_item', value=99.0)
    new_item.interface = None

    coll[1] = new_item

    assert new_item.interface is mock_interface


@pytest.mark.parametrize('cls', class_constructors)
@pytest.mark.filterwarnings('ignore::DeprecationWarning')
def test_ModelCollection_setitem_slice_with_interface_propagation(cls, clear_global, sample_items):
    """Test that setitem with slice propagates interface to new items."""
    for item in sample_items:
        item.interface = None

    class MockInterfaceClass:
        name = "MockInterface"
        def __init__(self, *args, **kwargs):
            pass
        def fit_func(self, *args, **kwargs):
            return "result"
        def create(self, model):
            return []

    mock_interface = InterfaceFactoryTemplate([MockInterfaceClass])
    coll = cls(*sample_items)
    coll.interface = mock_interface

    new_items = [MockModelItem(name='new1', value=10.0), MockModelItem(name='new2', value=20.0)]
    for item in new_items:
        item.interface = None

    coll[0:2] = new_items

    for item in new_items:
        assert item.interface is mock_interface


@pytest.mark.parametrize('cls', class_constructors)
@pytest.mark.filterwarnings('ignore::DeprecationWarning')
def test_ModelCollection_insert_with_interface_propagation(cls, clear_global, sample_items):
    """Test that insert propagates interface to new item."""
    for item in sample_items:
        item.interface = None

    class MockInterfaceClass:
        name = "MockInterface"
        def __init__(self, *args, **kwargs):
            pass
        def fit_func(self, *args, **kwargs):
            return "result"
        def create(self, model):
            return []

    mock_interface = InterfaceFactoryTemplate([MockInterfaceClass])
    coll = cls(*sample_items)
    coll.interface = mock_interface

    new_item = MockModelItem(name='inserted', value=99.0)
    new_item.interface = None

    coll.insert(1, new_item)

    assert new_item.interface is mock_interface


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_convert_to_dict_with_modify_dict(cls, clear_global, sample_items):
    """Test _convert_to_dict calls _modify_dict when present."""
    class DerivedWithModifyDict(cls):
        def _modify_dict(self, skip=None, **kwargs):
            return {'extra_key': 'extra_value'}

    coll = DerivedWithModifyDict(*sample_items)

    class DummyEncoder:
        def _convert_to_dict(self, item, skip=None, **kwargs):
            return {'name': getattr(item, 'name', 'unknown')}

    encoder = DummyEncoder()
    result = coll._convert_to_dict({}, encoder)

    assert result['extra_key'] == 'extra_value'
    assert 'data' in result


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_convert_to_dict_skip_none(cls, clear_global, sample_items):
    """Test _convert_to_dict handles skip=None correctly."""
    coll = cls(*sample_items)

    class DummyEncoder:
        def _convert_to_dict(self, item, skip=None, **kwargs):
            return {'name': getattr(item, 'name', 'unknown'), 'skip': skip}

    encoder = DummyEncoder()
    result = coll._convert_to_dict({}, encoder, skip=None)

    assert 'data' in result
    # skip should default to [] when None is passed
    for item_dict in result['data']:
        assert item_dict['skip'] == []


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_get_all_variables_item_without_method(cls, clear_global):
    """Test get_all_variables skips items without get_all_variables method."""
    # Create a minimal NewBase subclass without get_all_variables
    class MinimalItem(NewBase):
        def __init__(self, name):
            super().__init__()
            self._name = name

        @property
        def name(self):
            return self._name

    item_with = MockModelItem(name='with_vars', value=1.0)
    item_without = MinimalItem(name='no_vars')

    coll = cls(item_with, item_without)
    variables = coll.get_all_variables()

    # Only item_with has variables
    assert len(variables) == 1


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_getitem_str_item_without_name_attr(cls, clear_global):
    """Test __getitem__ with string searches by unique_name when item lacks name attr."""
    # Create item without name property
    class ItemWithoutName(NewBase):
        def __init__(self):
            super().__init__()

    item = ItemWithoutName()
    coll = cls(item)

    # Should find by unique_name
    found = coll[item.unique_name]
    assert found is item


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_delitem_slice_edges_updated(cls, clear_global, sample_items):
    """Test that deleting by slice updates graph edges correctly."""
    coll = cls(*sample_items)
    deleted_items = [sample_items[0], sample_items[2]]

    del coll[::2]  # Delete items at indices 0 and 2

    assert len(coll) == 1
    edges = global_object.map.get_edges(coll)
    for item in deleted_items:
        assert item.unique_name not in edges
    assert sample_items[1].unique_name in edges


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_setitem_slice_edges_updated(cls, clear_global, sample_items):
    """Test that setitem with slice updates graph edges correctly."""
    coll = cls(*sample_items)
    old_items = [sample_items[0], sample_items[1]]

    new_items = [MockModelItem(name='new1', value=10.0), MockModelItem(name='new2', value=20.0)]
    coll[0:2] = new_items

    edges = global_object.map.get_edges(coll)
    for item in old_items:
        assert item.unique_name not in edges
    for item in new_items:
        assert item.unique_name in edges
