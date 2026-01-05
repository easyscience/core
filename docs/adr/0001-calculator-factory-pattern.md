# ADR-0001: Separate Calculator Factory from Collection Base Classes

## Status

Proposed (Draft PR #181)

## Context

The EasyScience framework provides base classes for scientific modeling and fitting. The legacy `InterfaceFactoryTemplate` class served as both a calculator factory and a state manager, tightly coupling calculator creation with calculator lifecycle management. This design has several issues:

1. **Tight Coupling**: The `InterfaceFactoryTemplate` maintains state about the "current" calculator, mixing factory responsibilities with state management
2. **Inconsistency**: Other factories in EasyScience (e.g., minimizers) are stateless, creating confusion about architectural patterns
3. **Inheritance Issues**: The factory is tightly coupled with `NewCollectionBase`, making it difficult to use calculators independently of collection classes
4. **Complexity**: The mixed responsibilities make the code harder to understand, test, and maintain
5. **Extensibility**: Product libraries (like EasyReflectometry) struggle to implement calculator switching without inheriting unnecessary collection base class functionality

The need for a cleaner calculator architecture was discussed in Discussion #160, leading to the proposal to separate calculator concerns from collection management.

## Decision

We will introduce a new calculator architecture with the following components:

### 1. CalculatorBase

An abstract base class for all physics calculators:

- **Purpose**: Define the interface that all calculators must implement
- **Key Methods**:
  - `calculate(x)`: Abstract method for performing calculations
  - `model` property: Get/set the physical model
  - `instrumental_parameters` property: Get/set instrumental parameters
  - `update_model()` and `update_instrumental_parameters()`: Explicit update methods
- **Design Principles**:
  - Inherits from `ModelBase` to integrate with EasyScience's object graph
  - Stateless from factory perspective - each instance is independent
  - Allows custom calculators to add domain-specific methods

### 2. CalculatorFactoryBase

An abstract factory for creating calculator instances:

- **Purpose**: Provide a consistent pattern for calculator instantiation
- **Key Features**:
  - `_try_register_calculator()`: Dynamic discovery of available calculators based on installed dependencies
  - `available_calculators` property: List calculators that can be created
  - `create()`: Abstract method to instantiate a calculator
- **Design Principles**:
  - Stateless - does not track which calculator is "current"
  - Follows the same pattern as the minimizers factory
  - Supports graceful degradation when optional dependencies are missing

### 3. SimpleCalculatorFactory

A concrete factory implementation:

- **Purpose**: Provide a ready-to-use factory with a dictionary-based registry
- **Key Features**:
  - `register()`: Dynamically add calculators to the factory
  - `unregister()`: Remove calculators from the factory
  - Supports both static initialization and dynamic registration
- **Design Principles**:
  - Instance registries are independent (no shared state between factory instances)
  - Validates calculator classes at registration time
  - Provides clear error messages when calculators are not available

### 4. Deprecation of InterfaceFactoryTemplate

- Mark `InterfaceFactoryTemplate` as deprecated with a `DeprecationWarning`
- Keep it functional for backward compatibility
- Document migration path to new calculator classes

### 5. Encapsulation Improvements

- Make `Map._store` private (`__store`) to enforce encapsulation
- Update code that accessed `_store` directly to use public APIs (`vertices()`, `get_item_by_key()`)

## Consequences

### Positive

1. **Separation of Concerns**: Calculator creation is now separate from calculator state management and collection management
2. **Consistency**: The new factory pattern matches the minimizers factory, creating a consistent architectural style
3. **Flexibility**: Product libraries can use calculators independently without inheriting from collection base classes
4. **Extensibility**: New calculator types can be added without modifying the factory base
5. **Testability**: Stateless factories are easier to test and reason about
6. **Dynamic Discovery**: Optional dependencies can be detected at runtime without hard dependencies
7. **Better Encapsulation**: Private `__store` enforces proper API usage in the Map class

### Negative

1. **Migration Effort**: Existing code using `InterfaceFactoryTemplate` will need to be updated
2. **Deprecation Period**: We must maintain the old `InterfaceFactoryTemplate` during a transition period
3. **Documentation**: All product libraries need updated documentation showing how to use the new classes
4. **Breaking Change Risk**: While the old class remains, product libraries must eventually migrate

### Neutral

1. **Code Volume**: The new architecture adds ~600 lines of new code (base classes and factories)
2. **Test Coverage**: Added ~1100 lines of comprehensive unit tests, improving overall test coverage
3. **Learning Curve**: Developers need to understand the factory pattern, though it's simpler than the old approach

## Implementation

The implementation is provided in draft PR #181:

- `src/easyscience/fitting/calculators/calculator_base.py` - New CalculatorBase class
- `src/easyscience/fitting/calculators/calculator_factory.py` - New factory classes
- `src/easyscience/fitting/calculators/interface_factory.py` - Deprecation warning added
- `src/easyscience/global_object/map.py` - Encapsulation improvement (`_store` → `__store`)
- `src/easyscience/variable/parameter.py` - Updated to use public Map API
- Comprehensive test suites for all new classes

## Migration Path

For product libraries currently using `InterfaceFactoryTemplate`:

### Before (Legacy Pattern)

```python
from easyscience.fitting.calculators import InterfaceFactoryTemplate

class MyInterfaceFactory(InterfaceFactoryTemplate):
    def __init__(self):
        super().__init__([BackendA, BackendB])
        # Factory maintains state about current interface
```

### After (New Pattern)

```python
from easyscience.fitting.calculators import SimpleCalculatorFactory

class MyCalculatorFactory(SimpleCalculatorFactory):
    def __init__(self):
        super().__init__()
        self._try_register_calculator('backend_a', 'mypackage.backend_a', 'BackendA')
        self._try_register_calculator('backend_b', 'mypackage.backend_b', 'BackendB')

# Create calculators on demand
factory = MyCalculatorFactory()
calculator = factory.create('backend_a', model, instrument)
result = calculator.calculate(x_values)
```

## References

- Discussion #160: Original architecture discussion (referenced in PR #181)
- PR #181: Implementation of the new calculator architecture
- Minimizers factory: Example of the stateless factory pattern already used in EasyScience

## Notes

- The new classes are in the `easyscience.fitting.calculators` module, matching the location of the legacy `InterfaceFactoryTemplate`
- Product libraries like EasyReflectometry will benefit most from this change, as they can now implement calculator switching without complex inheritance hierarchies
- The `_try_register_calculator` method enables graceful handling of optional dependencies, improving user experience when not all calculator backends are installed
