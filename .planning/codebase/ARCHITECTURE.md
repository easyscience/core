# Architecture

**Analysis Date:** 2026-02-05

## Pattern Overview

**Overall:** Layered architecture with singleton global state management and pluggable minimizers

**Key Characteristics:**
- Central singleton `GlobalObject` that manages logging, undo/redo stack, object mapping, and state across the entire library
- Descriptor-based property system for model parameters (supports both static `Descriptor` and dynamic `Parameter` objects)
- Factory pattern for minimizer/optimizer selection and calculator interface abstraction
- Serialization/deserialization foundation through `SerializerComponent` hierarchy
- Command pattern implementation for undo/redo operations

## Layers

**Variables & Properties Layer:**
- Purpose: Defines the building blocks for scientific model parameters and descriptors
- Location: `src/easyscience/variable/`
- Contains: `Parameter`, `DescriptorNumber`, `DescriptorArray`, `DescriptorBool`, `DescriptorStr`, `DescriptorAnyType`, `DescriptorBase`
- Depends on: `GlobalObject` (for undo/redo), `SerializerComponent`
- Used by: All model and object classes

**Base Classes Layer:**
- Purpose: Provides inheritance hierarchy for all EasyScience objects
- Location: `src/easyscience/base_classes/`
- Contains: `BasedBase`, `ObjBase`, `NewBase`, `ModelBase`, `CollectionBase`
- Depends on: Variables layer, `GlobalObject`, Serialization layer
- Used by: Job layer, Model implementations, any domain-specific objects

**Global Object Layer:**
- Purpose: Manages singleton state, logging, undo/redo, object tracking, and script execution
- Location: `src/easyscience/global_object/`
- Contains: `GlobalObject`, `Logger`, `Map` (object registry), `UndoStack`, `ScriptManager`
- Depends on: Nothing (singleton)
- Used by: Every other layer (injected via `global_object`)

**Serialization Layer:**
- Purpose: Enables encoding/decoding of objects to/from dictionaries and other formats
- Location: `src/easyscience/io/`
- Contains: `SerializerComponent`, `SerializerBase`, `SerializerDict`
- Depends on: Variables layer, Base classes
- Used by: All serializable objects, object reconstruction

**Fitting & Optimization Layer:**
- Purpose: Provides curve fitting and parameter optimization capabilities
- Location: `src/easyscience/fitting/`
- Contains: `Fitter`, `AvailableMinimizers`, minimizer implementations (LMFit, Bumps, DFO-LS), `InterfaceFactoryTemplate`
- Depends on: Variables layer (for `Parameter` objects), Base classes
- Used by: Domain-specific implementations requiring optimization

**Job/Workflow Layer:**
- Purpose: Defines abstract base classes for scientific workflows (theory/experiment/analysis)
- Location: `src/easyscience/job/`
- Contains: `JobBase`, `TheoreticalModelBase`, `ExperimentBase`, `AnalysisBase`
- Depends on: Base classes layer
- Used by: Concrete implementations in domain libraries

**Models & Utilities:**
- Purpose: Specific model implementations and helper utilities
- Location: `src/easyscience/models/`, `src/easyscience/utils/`
- Contains: `Polynomial` model, class tools, decorators, string utilities
- Depends on: Base classes, Variables
- Used by: Model implementations and other modules

## Data Flow

**Object Creation & Registration:**

1. User creates an object (e.g., `Parameter`, `ObjBase` subclass)
2. Object registers itself with `GlobalObject.map` during `__init__`
3. Map tracks object type (`created`, `argument`, `returned`, `created_internal`)
4. Unique name is auto-generated if not provided
5. Object is now available for undo/redo tracking and serialization

**Parameter Value Changes:**

1. User modifies parameter value (e.g., `param.value = 5.0`)
2. Change triggers property setter with `@property_stack` decorator
3. If undo/redo stack is enabled: `UndoStack` records the change as a `Command`
4. Observers/callbacks are notified of the change
5. Change can be undone/redone via `GlobalObject.stack.undo()` / `redo()`

**Model Assembly:**

1. Create model subclass of `ModelBase` or `ObjBase`
2. Define `Parameter` and `Descriptor` fields as class attributes
3. In `__init__`, pass parameters to parent via kwargs
4. Parent `ObjBase` automatically creates dynamic properties for kwargs
5. Model is now serializable and has fittable parameters via `get_free_parameters()`

**Fitting Workflow:**

1. Create `Fitter` with fit_object (model) and fit_function (callback)
2. `Fitter` creates a minimizer via factory based on `AvailableMinimizers` enum
3. Minimizer wraps external libraries (lmfit, bumps, DFO-LS)
4. Call `minimize()` with bounds, constraints
5. Minimizer returns `FitResults` with optimized parameters
6. Results used to update model parameters

**State Management:**

- `GlobalObject.stack` maintains deque of `UndoCommand` objects
- Each command has `undo()` and `redo()` methods
- Stack is thread-locked to prevent conflicts (see commit 6e823b2)
- Can be enabled/disabled at runtime: `global_object.stack.enabled = False`

## Key Abstractions

**Parameter Family:**
- Purpose: Represents a value with metadata, units, and fitting constraints
- Examples: `src/easyscience/variable/parameter.py`, `src/easyscience/variable/descriptor_number.py`
- Pattern: Inheritance hierarchy where `Parameter` extends `DescriptorNumber` which extends `DescriptorBase`
- Features: Value, unit (via scipp), min/max bounds, variance/error, fixed flag, dependency resolution

**Object Hierarchy:**
- Purpose: Creates serializable scientific objects with dynamic properties
- Examples: `src/easyscience/base_classes/obj_base.py`, `src/easyscience/base_classes/model_base.py`
- Pattern: Deep inheritance (BasedBase → ObjBase/NewBase → ModelBase/CollectionBase)
- Features: Dynamic kwargs-based properties, serialization, undo/redo tracking via `GlobalObject`

**Minimizer Pattern:**
- Purpose: Abstracts different optimization algorithms behind common interface
- Examples: `src/easyscience/fitting/minimizers/minimizer_lmfit.py`, `minimizer_bumps.py`
- Pattern: Factory creates `MinimizerBase` subclass based on enum selection
- Features: Parameter binding, bounds enforcement, callbacks for convergence monitoring

**Map (Object Registry):**
- Purpose: Tracks all created objects and their relationships
- Examples: `src/easyscience/global_object/map.py`
- Pattern: Graph-based tracking with weakref finalizers for garbage collection
- Features: Object relationships, type tracking, name collision detection

## Entry Points

**Module Initialization:**
- Location: `src/easyscience/__init__.py`
- Triggers: When package is imported (`import easyscience`)
- Responsibilities:
  - Creates singleton `GlobalObject` and instantiates undo/redo stack
  - Exports public API: `ObjBase`, `Parameter`, `DescriptorNumber`, `Fitter`, `AvailableMinimizers`
  - Disables undo/redo initially to avoid tracking internal initialization

**Base Object Creation:**
- Location: `src/easyscience/base_classes/based_base.py` (`__init__`)
- Triggers: When any `BasedBase` subclass is instantiated
- Responsibilities:
  - Registers object with `GlobalObject.map`
  - Assigns or generates unique name
  - Sets up interface factory (if provided)

**Minimizer Creation:**
- Location: `src/easyscience/fitting/minimizers/factory.py`
- Triggers: When `Fitter` is instantiated or minimizer is switched
- Responsibilities:
  - Selects appropriate minimizer implementation based on enum
  - Initializes with fit object and function
  - Wraps external library API (lmfit, bumps, DFO-LS)

## Error Handling

**Strategy:** Exception-based with some validation at initialization

**Patterns:**
- Type checking in descriptors and parameters (e.g., `Parameter.__init__` validates name is string)
- Bounds enforcement (min/max) checked during fitting
- Circular import prevention via local imports in `undo_redo.py` and `based_base.py`
- Factory validation: raises `NotImplementedError` if no valid interface exists
- Unique name generation: auto-increments index if collision detected

## Cross-Cutting Concerns

**Logging:**
- Implementation: `GlobalObject.log` is a `Logger` instance
- Access pattern: Via `global_object.log.info()`, `log.warning()`, etc.
- Location: `src/easyscience/global_object/logger.py`

**Validation:**
- Type validation in `Parameter`, `Descriptor` constructors
- Bounds checking during value assignment
- Required fields checked in `Serializer._convert_to_dict()`
- Unique name collision detection via `GlobalObject.map`

**Undo/Redo:**
- Decorator-based tracking: `@property_stack` on setters
- Thread-locked to prevent conflicts (commit 6e823b2)
- Can be disabled: `global_object.stack.enabled = False`
- Supported on: Parameter value, variance, error, bounds, fixed flag, unit, display name

**Serialization:**
- All objects inheriting from `SerializerComponent` are serializable
- Implementation: `encode()` returns dict, `decode()` reconstructs from dict
- Handles cycles via `_REDIRECT` class variable to skip certain fields
- Parameter dependencies tracked separately via `parameter_dependency_resolver.py`

---

*Architecture analysis: 2026-02-05*
