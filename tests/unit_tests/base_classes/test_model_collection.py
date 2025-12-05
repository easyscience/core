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
    coll = cls('test_collection')
    assert coll.name == 'test_collection'
    assert len(coll) == 0
    assert coll.interface is None


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_init_with_items(cls, clear_global, sample_items):
    """Test creating a collection with initial items."""
    coll = cls('test_collection', *sample_items)
    assert coll.name == 'test_collection'
    assert len(coll) == 3
    for i, item in enumerate(coll):
        assert item.name == sample_items[i].name


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_init_with_unique_name(cls, clear_global):
    """Test creating a collection with a custom unique_name."""
    coll = cls('test_collection', unique_name='custom_unique')
    assert coll.unique_name == 'custom_unique'


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_init_with_display_name(cls, clear_global):
    """Test creating a collection with a custom display_name."""
    coll = cls('test_collection', display_name='My Display Name')
    assert coll.display_name == 'My Display Name'


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_init_with_list_arg(cls, clear_global, sample_items):
    """Test creating a collection with a list of items (should flatten)."""
    coll = cls('test_collection', sample_items)
    assert len(coll) == 3


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_init_type_error(cls, clear_global):
    """Test that adding non-NewBase items raises TypeError."""
    with pytest.raises(TypeError):
        cls('test_collection', 'not_a_newbase_object')


# =============================================================================
# Name Property Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_name_getter(cls, clear_global):
    """Test getting the collection name."""
    coll = cls('my_collection')
    assert coll.name == 'my_collection'


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_name_setter(cls, clear_global):
    """Test setting the collection name."""
    coll = cls('old_name')
    coll.name = 'new_name'
    assert coll.name == 'new_name'


# =============================================================================
# Interface Property Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_interface_default(cls, clear_global):
    """Test that interface defaults to None."""
    coll = cls('test_collection')
    assert coll.interface is None


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_interface_propagation(cls, clear_global, sample_items):
    """Test that setting interface propagates to items."""
    # Add interface attribute to items for this test
    for item in sample_items:
        item.interface = None

    coll = cls('test_collection', *sample_items)

    class MockInterface:
        pass

    mock_interface = MockInterface()
    coll.interface = mock_interface

    assert coll.interface is mock_interface
    for item in coll:
        assert item.interface is mock_interface


# =============================================================================
# __getitem__ Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_getitem_int(cls, clear_global, sample_items):
    """Test getting items by integer index."""
    coll = cls('test_collection', *sample_items)
    assert coll[0].name == 'item1'
    assert coll[1].name == 'item2'
    assert coll[2].name == 'item3'
    assert coll[-1].name == 'item3'


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_getitem_int_out_of_range(cls, clear_global, sample_items):
    """Test that out of range index raises IndexError."""
    coll = cls('test_collection', *sample_items)
    with pytest.raises(IndexError):
        _ = coll[100]


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_getitem_slice(cls, clear_global, sample_items):
    """Test getting items by slice."""
    coll = cls('test_collection', *sample_items)
    sliced = coll[0:2]
    assert isinstance(sliced, cls)
    assert len(sliced) == 2
    assert sliced[0].name == 'item1'
    assert sliced[1].name == 'item2'


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_getitem_str_by_name(cls, clear_global, sample_items):
    """Test getting items by name string."""
    coll = cls('test_collection', *sample_items)
    item = coll['item2']
    assert item.name == 'item2'


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_getitem_str_by_unique_name(cls, clear_global, sample_items):
    """Test getting items by unique_name string."""
    coll = cls('test_collection', *sample_items)
    unique_name = sample_items[1].unique_name
    item = coll[unique_name]
    assert item.unique_name == unique_name


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_getitem_str_not_found(cls, clear_global, sample_items):
    """Test that getting non-existent name raises KeyError."""
    coll = cls('test_collection', *sample_items)
    with pytest.raises(KeyError):
        _ = coll['nonexistent']


# =============================================================================
# __setitem__ Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_setitem_int(cls, clear_global, sample_items):
    """Test setting items by integer index."""
    coll = cls('test_collection', *sample_items)
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
    coll = cls('test_collection', *sample_items)
    with pytest.raises(TypeError):
        coll[0] = 'not_a_newbase_object'


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_setitem_slice(cls, clear_global, sample_items):
    """Test setting items by slice."""
    coll = cls('test_collection', *sample_items)
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
    coll = cls('test_collection', *sample_items)
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
    coll = cls('test_collection', *sample_items)

    del coll[0:2]

    assert len(coll) == 1
    assert coll[0].name == 'item3'


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_delitem_str_by_name(cls, clear_global, sample_items):
    """Test deleting items by name string."""
    coll = cls('test_collection', *sample_items)

    del coll['item2']

    assert len(coll) == 2
    assert 'item2' not in [item.name for item in coll]


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_delitem_str_not_found(cls, clear_global, sample_items):
    """Test that deleting non-existent name raises KeyError."""
    coll = cls('test_collection', *sample_items)
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
    coll = cls('test_collection', *items)
    assert len(coll) == count


# =============================================================================
# insert Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_insert(cls, clear_global, sample_items):
    """Test inserting items at an index."""
    coll = cls('test_collection', *sample_items)
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
    coll = cls('test_collection', *sample_items)
    with pytest.raises(TypeError):
        coll.insert(0, 'not_a_newbase_object')


# =============================================================================
# append Tests (inherited from MutableSequence)
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_append(cls, clear_global, sample_items):
    """Test appending items."""
    coll = cls('test_collection', *sample_items)
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
    coll = cls('test_collection', *sample_items)
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
    coll = cls('test_collection', *items)

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
    coll = cls('test_collection', *items)

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
    coll = cls('my_collection', *sample_items)
    repr_str = repr(coll)
    assert cls.__name__ in repr_str
    assert 'my_collection' in repr_str
    assert '3' in repr_str


# =============================================================================
# __iter__ Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_iter(cls, clear_global, sample_items):
    """Test iteration over collection."""
    coll = cls('test_collection', *sample_items)

    names = [item.name for item in coll]
    assert names == ['item1', 'item2', 'item3']


# =============================================================================
# get_all_variables Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_get_all_variables(cls, clear_global, sample_items):
    """Test getting all variables from items."""
    coll = cls('test_collection', *sample_items)
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
    coll = cls('test_collection', *sample_items)
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

    coll = cls('test_collection', *sample_items)
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
    coll = cls('test_collection', *sample_items)

    edges = global_object.map.get_edges(coll)
    assert len(edges) == 3

    for item in sample_items:
        assert item.unique_name in edges


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_graph_edges_after_append(cls, clear_global, sample_items):
    """Test graph edges are updated after append."""
    coll = cls('test_collection', *sample_items)
    new_item = MockModelItem(name='new', value=99.0)

    coll.append(new_item)

    edges = global_object.map.get_edges(coll)
    assert len(edges) == 4
    assert new_item.unique_name in edges


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_graph_edges_after_delete(cls, clear_global, sample_items):
    """Test graph edges are updated after delete."""
    coll = cls('test_collection', *sample_items)
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
    coll = cls('test_collection', sample_items[0])
    coll.extend([sample_items[1], sample_items[2]])

    assert len(coll) == 3
    assert coll[1].name == 'item2'
    assert coll[2].name == 'item3'


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_pop(cls, clear_global, sample_items):
    """Test pop method (inherited from MutableSequence)."""
    coll = cls('test_collection', *sample_items)

    popped = coll.pop()
    assert popped.name == 'item3'
    assert len(coll) == 2


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_pop_index(cls, clear_global, sample_items):
    """Test pop method with index (inherited from MutableSequence)."""
    coll = cls('test_collection', *sample_items)

    popped = coll.pop(0)
    assert popped.name == 'item1'
    assert len(coll) == 2
    assert coll[0].name == 'item2'


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_remove(cls, clear_global, sample_items):
    """Test remove method (inherited from MutableSequence)."""
    coll = cls('test_collection', *sample_items)
    item_to_remove = sample_items[1]

    coll.remove(item_to_remove)

    assert len(coll) == 2
    assert item_to_remove not in coll


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_clear(cls, clear_global, sample_items):
    """Test clear method (inherited from MutableSequence)."""
    coll = cls('test_collection', *sample_items)

    coll.clear()

    assert len(coll) == 0


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_reverse(cls, clear_global, sample_items):
    """Test reverse method (inherited from MutableSequence)."""
    coll = cls('test_collection', *sample_items)

    coll.reverse()

    assert coll[0].name == 'item3'
    assert coll[1].name == 'item2'
    assert coll[2].name == 'item1'


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_count(cls, clear_global, sample_items):
    """Test count method (inherited from MutableSequence)."""
    coll = cls('test_collection', *sample_items)

    count = coll.count(sample_items[0])
    assert count == 1


@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_index(cls, clear_global, sample_items):
    """Test index method (inherited from MutableSequence)."""
    coll = cls('test_collection', *sample_items)

    idx = coll.index(sample_items[1])
    assert idx == 1


# =============================================================================
# Contains Tests
# =============================================================================

@pytest.mark.parametrize('cls', class_constructors)
def test_ModelCollection_contains(cls, clear_global, sample_items):
    """Test __contains__ (in operator)."""
    coll = cls('test_collection', *sample_items)

    assert sample_items[0] in coll
    assert sample_items[1] in coll

    new_item = MockModelItem(name='not_in_collection', value=999.0)
    assert new_item not in coll
