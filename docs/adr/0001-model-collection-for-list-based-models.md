# ADR 0001: ModelCollection for List-Based Model Management

## Status

Proposed

## Context

The EasyScience corelib provides base classes for building scientific models, including `ModelBase` which extends from `NewBase`. However, there was no dedicated collection class that combines the list-like functionality of Python's built-in containers with the EasyScience features such as:

- Interface propagation to contained items
- Graph-based dependency tracking
- Serialization support
- Parameter management across collections

Users who needed to manage collections of model objects had to either:
1. Use Python's built-in list types, losing EasyScience features
2. Use the existing `CollectionBase` which is based on `BasedBase` (older architecture)
3. Create custom collection implementations for each use case

This gap in the architecture made it difficult to create clean, maintainable code when working with multiple related model objects that need to share interfaces and participate in the EasyScience ecosystem.

## Decision

We have decided to introduce a new `ModelCollection` class that:

1. **Extends ModelBase**: Inherits all EasyScience features from `ModelBase`
2. **Implements MutableSequence**: Provides full list-like functionality through Python's `collections.abc.MutableSequence` interface
3. **Supports Interface Propagation**: Automatically propagates interface bindings to all items in the collection
4. **Maintains Graph Edges**: Properly manages graph relationships through the global object map
5. **Enables Type Safety**: Uses Python's typing system with generics (`TypeVar`) for better IDE support
6. **Provides Multiple Access Methods**: Supports indexing by integer, slice, name, or unique_name

### Key Design Decisions

#### 1. Inheritance from ModelBase and MutableSequence

```python
class ModelCollection(ModelBase, MutableSequence[T]):
```

This dual inheritance provides:
- ModelBase features: serialization, parameter management, graph tracking
- MutableSequence interface: standard Python list operations (append, insert, pop, etc.)

#### 2. Interface Propagation

The collection automatically propagates its interface to all contained items:

```python
@interface.setter
def interface(self, new_interface: InterfaceType) -> None:
    self._interface = new_interface
    for item in self._data:
        if hasattr(item, 'interface'):
            setattr(item, 'interface', new_interface)
```

This ensures that when a collection's interface changes, all items are updated automatically.

#### 3. Graph Edge Management

All collection operations (add, remove, replace) properly maintain graph edges:

```python
def _add_item(self, item: Any) -> None:
    if not isinstance(item, NewBase):
        raise TypeError(f'Items must be NewBase objects, got {type(item)}')
    if item in self._data:
        return  # Skip duplicates
    self._data.append(item)
    self._global_object.map.add_edge(self, item)
    self._global_object.map.reset_type(item, 'created_internal')
```

#### 4. Multiple Access Patterns

Support for accessing items by:
- Integer index: `collection[0]`
- Slice: `collection[0:2]`
- Name: `collection['item_name']`
- Unique name: `collection[unique_id]`

#### 5. Type Safety with Generics

Using `TypeVar` and `@overload` decorators for precise type hints:

```python
T = TypeVar('T', bound=NewBase)

@overload
def __getitem__(self, idx: int) -> T: ...
@overload
def __getitem__(self, idx: slice) -> 'ModelCollection[T]': ...
@overload
def __getitem__(self, idx: str) -> T: ...
```

## Consequences

### Positive

1. **Unified API**: Users get familiar list operations while maintaining EasyScience features
2. **Type Safety**: Better IDE support and static analysis through comprehensive type hints
3. **Automatic Interface Management**: Interface changes propagate automatically to all items
4. **Clean Architecture**: Separation of concerns with `_add_item` and `_remove_item` helpers
5. **Backward Compatible**: Doesn't break existing code, adds new functionality
6. **Well-Tested**: Comprehensive test suite (102 tests covering all functionality)
7. **Flexible Access**: Multiple ways to access items (by index, name, or unique_name)

### Negative

1. **Additional Complexity**: Users need to understand when to use `ModelCollection` vs `CollectionBase`
2. **Memory Overhead**: Graph edge tracking adds some memory overhead
3. **Learning Curve**: New users need to understand the interface propagation mechanism
4. **Type Checking Limitations**: Some dynamic operations may not be fully type-checked

### Neutral

1. **Migration Path**: Existing code using plain lists can be migrated gradually
2. **Documentation Needs**: Requires documentation and examples for effective use
3. **CollectionBase Relationship**: Need to clarify relationship with existing `CollectionBase`

## Implementation Details

### File Changes

Based on PR #180, the implementation includes:

1. **New File**: `src/easyscience/base_classes/model_collection.py` (278 lines)
   - Core `ModelCollection` class implementation
   - Complete MutableSequence interface
   - Interface propagation logic
   - Serialization support

2. **Modified**: `src/easyscience/base_classes/__init__.py`
   - Export `ModelCollection` from base_classes module

3. **Modified**: `src/easyscience/base_classes/collection_base.py`
   - Update to accept `NewBase` objects (not just `BasedBase`)

4. **New File**: `tests/unit_tests/base_classes/test_model_collection.py` (953 lines)
   - 102 comprehensive unit tests
   - Tests for all MutableSequence operations
   - Interface propagation tests
   - Graph edge management tests

### Key Methods

- `__init__`: Initialize collection with optional items and interface
- `__getitem__`: Support int, slice, and string (name) indexing
- `__setitem__`: Replace items while maintaining graph edges
- `__delitem__`: Remove items and clean up graph edges
- `insert`: Add items at specific positions
- `interface` property: Get/set interface with propagation
- `get_all_variables`: Collect variables from all items
- `sort`: Sort collection by custom mapping function
- `_convert_to_dict`: Serialize collection to dictionary

## Alternatives Considered

1. **Extending CollectionBase**: 
   - Rejected because CollectionBase is based on BasedBase (older architecture)
   - Would not provide the clean MutableSequence interface

2. **Composition over Inheritance**:
   - Could wrap a list instead of inheriting from MutableSequence
   - Rejected because it would require manually implementing all list methods

3. **Using Python's Built-in list**:
   - Simplest approach but loses all EasyScience features
   - No interface propagation or graph tracking

4. **Generic Container Class**:
   - Could create a more generic container for any object type
   - Rejected to maintain type safety and EasyScience feature integration

## References

- Pull Request #180: https://github.com/easyscience/corelib/pull/180
- Related Issue: New collection base functionality
- Python MutableSequence: https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableSequence
- Type Hints PEP 484: https://www.python.org/dev/peps/pep-0484/

## Notes

This ADR documents the design decisions made in PR #180 (New collection base). The implementation is currently in draft/review stage. Once merged, this ADR should be updated to "Accepted" status.

### Future Considerations

1. Consider adding more specialized collection types (e.g., ordered, sorted)
2. Evaluate performance with large collections (1000+ items)
3. Consider adding collection-level operations (filter, map, reduce)
4. Potential for async/lazy loading of items for very large datasets
5. Integration with numpy arrays or pandas DataFrames for numerical operations

## Decision Date

2026-01-05

## Revision History

- 2026-01-05: Initial ADR proposal based on PR #180
