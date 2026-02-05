# Codebase Structure

**Analysis Date:** 2026-02-05

## Directory Layout

```
corelib/
├── src/easyscience/                    # Main package source
│   ├── __init__.py                     # Package entry point, exports public API
│   ├── __version__.py                  # Version info (git-managed)
│   ├── base_classes/                   # Core inheritance hierarchy
│   │   ├── based_base.py               # Foundation class (extends SerializerComponent)
│   │   ├── obj_base.py                 # Dynamic kwargs-based object class
│   │   ├── new_base.py                 # Alternative base for certain uses
│   │   ├── model_base.py               # Model-specific base with parameter queries
│   │   ├── collection_base.py          # MutableSequence-based container class
│   │   └── __init__.py                 # Exports all base classes
│   ├── variable/                       # Parameter and descriptor types
│   │   ├── descriptor_base.py          # Abstract base for all property descriptors
│   │   ├── descriptor_number.py        # Numeric property (value, unit, variance)
│   │   ├── descriptor_array.py         # Array-based property
│   │   ├── descriptor_bool.py          # Boolean property
│   │   ├── descriptor_str.py           # String property
│   │   ├── descriptor_any_type.py      # Untyped property
│   │   ├── parameter.py                # Fittable parameter (extends DescriptorNumber)
│   │   ├── parameter_dependency_resolver.py  # Handles parameter constraints
│   │   └── __init__.py                 # Exports all variable types
│   ├── global_object/                  # Singleton state management
│   │   ├── global_object.py            # Main singleton (instantiated in __init__.py)
│   │   ├── logger.py                   # Logging interface
│   │   ├── map.py                      # Object registry/tracking graph
│   │   ├── undo_redo.py                # Command pattern implementation for undo/redo
│   │   ├── hugger/                     # Script execution and property binding
│   │   │   ├── hugger.py               # ScriptManager for dynamic execution
│   │   │   ├── property.py             # Property binding mechanism
│   │   │   └── __init__.py
│   │   └── __init__.py                 # Exports all global objects
│   ├── io/                             # Serialization framework
│   │   ├── serializer_component.py     # Base mixin for serializable objects
│   │   ├── serializer_base.py          # Abstract encoder/decoder interface
│   │   ├── serializer_dict.py          # Dictionary-based serializer implementation
│   │   └── __init__.py                 # Exports serializer classes
│   ├── fitting/                        # Optimization/curve fitting
│   │   ├── available_minimizers.py     # Enum of available minimization algorithms
│   │   ├── fitter.py                   # Main fitting orchestrator
│   │   ├── multi_fitter.py             # Multi-objective fitting (has circular import)
│   │   ├── calculators/                # Calculator interface abstraction
│   │   │   ├── interface_factory.py    # Factory for pluggable calculator interfaces
│   │   │   └── __init__.py
│   │   ├── minimizers/                 # Specific minimizer implementations
│   │   │   ├── minimizer_base.py       # Abstract minimizer base class
│   │   │   ├── minimizer_lmfit.py      # lmfit-based least-squares fitting
│   │   │   ├── minimizer_bumps.py      # Bumps-based MCMC/Bayesian fitting
│   │   │   ├── minimizer_dfo.py        # DFO-LS derivative-free optimization
│   │   │   ├── factory.py              # Factory to create minimizer from enum
│   │   │   ├── utils.py                # FitResults dataclass and utilities
│   │   │   └── __init__.py             # Exports minimizer classes
│   │   └── __init__.py                 # Exports Fitter, AvailableMinimizers, FitResults
│   ├── job/                            # Workflow/job base classes
│   │   ├── job.py                      # JobBase abstract class
│   │   ├── theoreticalmodel.py         # TheoreticalModelBase for model definitions
│   │   ├── experiment.py               # ExperimentBase for experimental data
│   │   ├── analysis.py                 # AnalysisBase for analysis/fitting results
│   │   └── __init__.py                 # Exports job classes
│   ├── models/                         # Concrete model implementations
│   │   ├── polynomial.py               # Polynomial model example
│   │   └── __init__.py
│   ├── utils/                          # Helper utilities
│   │   ├── classTools.py               # Class introspection utilities (addLoggedProp)
│   │   ├── classUtils.py               # Class utilities (singleton decorator)
│   │   ├── decorators.py               # Function decorators
│   │   ├── string.py                   # String manipulation helpers
│   │   ├── io/                         # I/O related utilities
│   │   └── __init__.py
│   ├── objects/                        # Additional object definitions
│   │   ├── variable/                   # Object-specific variables?
│   │   └── __init__.py
│   └── legacy/                         # Deprecated serialization formats
│       ├── legacy_core.py              # Old core implementation
│       ├── dict.py, json.py, xml.py    # Legacy format handlers
│       └── (excluded from wheel build)
├── tests/                              # Test suite
│   ├── unit_tests/                     # Unit tests organized by module
│   │   ├── base_classes/
│   │   ├── Fitting/
│   │   ├── global_object/
│   │   ├── io/
│   │   ├── job/
│   │   ├── legacy/
│   │   ├── models/
│   │   ├── variable/
│   │   └── __init__.py files
│   ├── integration_tests/              # Integration/functional tests
│   │   └── Fitting/
│   ├── coords.py                       # Coordinate/fixture helpers
│   ├── package_test.py                 # Package import tests
│   └── conftest.py                     # Pytest configuration
├── docs/                               # Sphinx documentation
├── Examples/                           # Usage examples
├── examples_old/                       # Deprecated examples
├── resources/                          # Static resources
├── .github/                            # GitHub Actions CI/CD
├── pixi.toml                           # Pixi environment config
├── pyproject.toml                      # Python project metadata
├── README.md                           # Project overview
└── .planning/codebase/                 # GSD mapping documents (this location)
```

## Directory Purposes

**`src/easyscience/`:**
- Purpose: Main package source code
- Contains: All production code organized by functionality
- Key files: `__init__.py` (entry point), `__version__.py` (version metadata)

**`src/easyscience/base_classes/`:**
- Purpose: Core object model and inheritance hierarchy
- Contains: Abstract and concrete base classes that all domain objects inherit from
- Key files: `based_base.py` (foundation), `obj_base.py` (main user-facing class), `model_base.py` (models)

**`src/easyscience/variable/`:**
- Purpose: Parameter and descriptor system for scientific model properties
- Contains: Type-specific descriptors (number, array, bool, str) and Parameter (fittable variant)
- Key files: `descriptor_base.py` (abstract), `parameter.py` (main), `descriptor_number.py` (numeric values)

**`src/easyscience/global_object/`:**
- Purpose: Singleton state management and cross-cutting services
- Contains: GlobalObject (singleton), Logger, Map (object tracking), UndoStack, ScriptManager
- Key files: `global_object.py` (singleton instance), `map.py` (object registry), `undo_redo.py` (command pattern)

**`src/easyscience/io/`:**
- Purpose: Object serialization and deserialization
- Contains: Serializer implementations for converting objects to/from standard formats
- Key files: `serializer_dict.py` (primary implementation), `serializer_base.py` (abstract interface)

**`src/easyscience/fitting/`:**
- Purpose: Parameter optimization and curve fitting
- Contains: Fitter orchestrator, minimizer implementations, factory for algorithm selection
- Key files: `fitter.py` (main), `available_minimizers.py` (algorithm selection), `minimizers/factory.py` (creation)

**`src/easyscience/job/`:**
- Purpose: Abstract base classes for scientific workflows
- Contains: JobBase (main), TheoreticalModelBase, ExperimentBase, AnalysisBase
- Key files: `job.py` (JobBase), specialized bases for theory/experiment/analysis

**`src/easyscience/models/`:**
- Purpose: Concrete model implementations
- Contains: Specific mathematical models (Polynomial, etc.)
- Key files: `polynomial.py` (example polynomial model)

**`src/easyscience/utils/`:**
- Purpose: Helper utilities and decorators
- Contains: Class introspection, class utilities, decorators, string helpers
- Key files: `classTools.py` (addLoggedProp), `classUtils.py` (singleton), `decorators.py`

**`src/easyscience/legacy/`:**
- Purpose: Deprecated serialization formats (excluded from wheel)
- Contains: Old dict/json/xml serializers for backwards compatibility
- Note: Intentionally excluded from distribution (see pyproject.toml)

**`tests/unit_tests/`:**
- Purpose: Unit tests for individual modules
- Contains: Test files organized to mirror source structure
- Key files: `test_*.py` files (one per module), `conftest.py` for fixtures

**`tests/integration_tests/`:**
- Purpose: Integration and functional tests
- Contains: Cross-module tests, full workflow tests
- Key files: `Fitting/test_fitter.py` (fitting workflows)

## Key File Locations

**Entry Points:**
- `src/easyscience/__init__.py`: Package initialization, GlobalObject creation, public API export
- `src/easyscience/global_object/global_object.py`: Singleton GlobalObject instantiation
- `src/easyscience/fitting/fitter.py`: Fitting workflow entry point

**Configuration:**
- `pyproject.toml`: Project metadata, dependencies, build config, tool settings
- `pixi.toml`: Pixi environment specification
- `.coveragerc`: Coverage configuration
- `pixi.lock`: Locked dependency versions

**Core Logic:**
- `src/easyscience/base_classes/obj_base.py`: Dynamic property creation via kwargs
- `src/easyscience/base_classes/based_base.py`: GlobalObject integration, serialization
- `src/easyscience/variable/parameter.py`: Parameter definition with fitting constraints
- `src/easyscience/global_object/map.py`: Object tracking and relationship management
- `src/easyscience/fitting/fitter.py`: Fitting orchestration

**Testing:**
- `tests/unit_tests/base_classes/test_obj_base.py`: ObjBase behavior tests
- `tests/integration_tests/Fitting/test_fitter.py`: Fitting workflow tests
- `tests/conftest.py`: Global pytest fixtures and configuration

## Naming Conventions

**Files:**
- Module files use `snake_case`: `obj_base.py`, `descriptor_number.py`, `interface_factory.py`
- Test files use `test_*.py`: `test_obj_base.py`, `test_fitter.py`
- Package directories use `snake_case`: `base_classes`, `global_object`, `fitting`

**Classes:**
- Base classes use `Base` suffix: `BasedBase`, `ObjBase`, `ModelBase`, `CollectionBase`, `DescriptorBase`
- Concrete implementations often use specific type: `DescriptorNumber`, `DescriptorArray`, `DescriptorBool`
- Factories use `Factory` suffix: `InterfaceFactoryTemplate`
- Minimizers use `Minimizer` prefix: `MinimizerLMFit`, `MinimizerBumps`, `MinimizerDFO`

**Functions:**
- Private methods/functions use leading underscore: `_update_minimizer()`, `_add_component()`
- Properties use lowercase: `value`, `fixed`, `bounds`
- Getters explicitly named or use `@property`: `get_all_parameters()`, `get_free_parameters()`

**Variables:**
- Module-level globals use `UPPERCASE`: `DEFAULT_MINIMIZER`
- Instance attributes use leading underscore: `_name`, `_value`, `_global_object`
- Private class attributes use double underscore: `__log` (in GlobalObject)

## Where to Add New Code

**New Model/Object:**
- Create class in `src/easyscience/models/` or domain-specific package
- Inherit from `ModelBase` (if parameter queries needed) or `ObjBase` (if simple)
- Add `Parameter` and `Descriptor` fields as kwargs or class attributes
- Implement tests in `tests/unit_tests/models/` or domain-specific test directory
- Export from `src/easyscience/models/__init__.py`

**New Minimizer Algorithm:**
- Create file `src/easyscience/fitting/minimizers/minimizer_{name}.py`
- Inherit from `MinimizerBase` in `src/easyscience/fitting/minimizers/minimizer_base.py`
- Implement required methods: `minimize()`, `make_model()`, `evaluate()`
- Add enum entry in `src/easyscience/fitting/available_minimizers.py`
- Register in factory: `src/easyscience/fitting/minimizers/factory.py`
- Add tests: `tests/unit_tests/Fitting/minimizers/test_minimizer_{name}.py`

**New Serializer Format:**
- Create file `src/easyscience/io/serializer_{format}.py`
- Inherit from `SerializerBase`
- Implement `encode()` and `decode()` abstract methods
- Use `_convert_to_dict()` helper from base class
- Export from `src/easyscience/io/__init__.py`

**Shared Utilities:**
- Small utilities (functions, decorators): `src/easyscience/utils/`
- Class-related tools: `src/easyscience/utils/classTools.py`
- General decorators: `src/easyscience/utils/decorators.py`
- String helpers: `src/easyscience/utils/string.py`

**Job/Workflow Base Classes:**
- Create abstract class in `src/easyscience/job/`
- Inherit from appropriate base (JobBase, TheoreticalModelBase, etc.)
- Document required subclass implementation
- Add tests in `tests/unit_tests/job/`

## Special Directories

**`src/easyscience/legacy/`:**
- Purpose: Deprecated serialization formats
- Generated: No (hand-maintained for compatibility)
- Committed: Yes, but excluded from wheel build (see pyproject.toml line 81)
- Note: Should not be imported in production; use for migration only

**`src/easyscience/objects/`:**
- Purpose: Additional object definitions (currently minimal)
- Generated: No
- Committed: Yes
- Note: May be future home for additional object types

**`src/easyscience/utils/io/`:**
- Purpose: I/O-related utilities (separate from main io module)
- Generated: No
- Committed: Yes
- Note: Currently minimal, for future expansion

**`.planning/codebase/`:**
- Purpose: GSD mapping documents (ARCHITECTURE.md, STRUCTURE.md, etc.)
- Generated: Yes (by GSD mapping process)
- Committed: Yes
- Note: Should reflect current state of codebase; updated when architecture changes

**`tests/__pycache__/` and `src/easyscience/__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes (automatic)
- Committed: No (.gitignore)

**`.pytest_cache/` and `.ruff_cache/`:**
- Purpose: Tool-specific caches
- Generated: Yes (automatic)
- Committed: No (.gitignore)

---

*Structure analysis: 2026-02-05*
