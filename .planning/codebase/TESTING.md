# Testing Patterns

**Analysis Date:** 2026-02-05

## Test Framework

**Runner:**
- `pytest` (version listed in `pyproject.toml` dev dependencies)
- Configuration embedded in `pyproject.toml` under `[tool.tox]` with tox + pytest integration
- Multi-version testing: Python 3.11, 3.12, 3.13

**Assertion Library:**
- Python's built-in `assert` statements (not `pytest.assert` helpers)

**Run Commands:**
```bash
pytest --cov --cov-report=xml     # Run all tests with coverage and XML report
pytest tests/unit_tests/          # Run unit tests only
pytest tests/integration_tests/   # Run integration tests only
tox                               # Run tests across Python 3.11, 3.12, 3.13
```

**Coverage:**
- Configuration file: `.coveragerc` (minimal config pointing to source)
- Source tracked: `src/easyscience/`
- Tool: `pytest-cov` plugin (in dev dependencies)
- CI Integration: Reports generated as XML for codecov service

## Test File Organization

**Location:**
- Co-located parallel structure: `tests/` mirrors `src/easyscience/`
- Unit tests: `tests/unit_tests/` (matches source module structure)
- Integration tests: `tests/integration_tests/`

**Naming:**
- Test files: `test_{module_name}.py` (e.g., `test_obj_base.py` for `obj_base.py`)
- Test classes: `Test{FeatureName}` or `Test{ModuleName}` (e.g., `TestGlobalObject`, `TestFitter`)
- Test methods: `test_{feature_being_tested}` (e.g., `test_constructor`, `test_make_model`)
- Test data dictionaries: lowercase (e.g., `test_dict`, `setup_pars`)

**Structure:**
```
tests/
├── unit_tests/
│   ├── base_classes/
│   │   ├── __init__.py
│   │   ├── test_obj_base.py
│   │   ├── test_collection_base.py
│   │   └── test_model_base.py
│   ├── Fitting/
│   │   ├── minimizers/
│   │   │   └── test_*.py
│   │   └── test_fitter.py
│   └── global_object/
│       └── test_*.py
├── integration_tests/
│   └── Fitting/
│       ├── test_fitter.py
│       └── test_multi_fitter.py
├── coords.py              # Test utilities/fixtures
└── package_test.py        # Package-level tests
```

## Test Structure

**Suite Organization - Unit Tests:**
```python
# From test_obj_base.py
from contextlib import contextmanager
import pytest
from easyscience import ObjBase, Parameter

@pytest.fixture
def setup_pars():
    d = {
        "name": "test",
        "par1": Parameter("p1", 0.1, fixed=True),
        "par2": Parameter("p2", 0.1),
    }
    return d

@pytest.mark.parametrize("a, kw", [
    ([], ["par1"]),
    (["par1"], []),
])
def test_ObjBase_create(setup_pars: dict, a: List[str], kw: List[str]):
    name = setup_pars["name"]
    args = []
    for key in a:
        args.append(setup_pars[key])
    kwargs = {key: setup_pars[key] for key in kw}
    base = ObjBase(name, None, *args, **kwargs)
    assert base.name == name
```

**Suite Organization - Class-based Tests:**
```python
# From test_fitter.py
from unittest.mock import MagicMock
import pytest

class TestFitter:
    @pytest.fixture
    def fitter(self, monkeypatch):
        monkeypatch.setattr(Fitter, '_update_minimizer', MagicMock())
        self.mock_fit_object = MagicMock()
        self.mock_fit_function = MagicMock()
        return Fitter(self.mock_fit_object, self.mock_fit_function)

    def test_constructor(self, fitter: Fitter):
        # When Then Expect
        assert fitter._fit_object == self.mock_fit_object
```

**Patterns:**
- Setup via `@pytest.fixture` (function or class scoped)
- Teardown via `yield` in fixtures (implicit cleanup)
- Clear global state: `@pytest.fixture` with `global_object.map._clear()` calls
- Parametrization: `@pytest.mark.parametrize` for testing multiple input combinations
- Mocking: `unittest.mock.MagicMock` and `monkeypatch` fixture from pytest

## Mocking

**Framework:**
- Primary: `unittest.mock.MagicMock` and `unittest.mock.patch`
- Fixture access: `monkeypatch` (pytest built-in)

**Patterns:**
```python
# Direct MagicMock replacement (test_fitter.py, line 12-16)
@pytest.fixture
def fitter(self, monkeypatch):
    monkeypatch.setattr(Fitter, '_update_minimizer', MagicMock())
    self.mock_fit_object = MagicMock()
    self.mock_fit_function = MagicMock()
    return Fitter(self.mock_fit_object, self.mock_fit_function)

# Mock method calls with return values (test_fitter.py, line 29-31)
mock_minimizer = MagicMock()
mock_minimizer.make_model = MagicMock(return_value='model')
fitter._minimizer = mock_minimizer

# Assertion on mock calls (test_fitter.py, line 38)
mock_minimizer.make_model.assert_called_once_with('pars')
```

**What to Mock:**
- External dependencies and services (minimizers, interfaces)
- Constructor initialization for isolation testing
- Methods with side effects to verify call behavior

**What NOT to Mock:**
- Core domain objects being tested (e.g., Parameter, ObjBase)
- The class under test itself (unless testing delegation)
- Simple getter/setter behavior

## Fixtures and Factories

**Test Data:**
```python
# Reusable parameter setup (test_obj_base.py, line 30-39)
@pytest.fixture
def setup_pars():
    d = {
        "name": "test",
        "par1": Parameter("p1", 0.1, fixed=True),
        "des1": DescriptorNumber("d1", 0.1),
        "par2": Parameter("p2", 0.1),
        "des2": DescriptorNumber("d2", 0.1),
        "par3": Parameter("p3", 0.1),
    }
    return d

# Model classes for testing (test_fitter.py, line 16-27)
class AbsSin(ObjBase):
    phase: Parameter
    offset: Parameter

    def __init__(self, offset_val: float, phase_val: float):
        offset = Parameter("offset", offset_val)
        phase = Parameter("phase", phase_val)
        super().__init__("sin", offset=offset, phase=phase)

    def __call__(self, x):
        return np.abs(np.sin(self.phase.value * x + self.offset.value))
```

**Location:**
- Fixtures defined in test files themselves (no shared conftest.py)
- Test data classes defined at module level within test file
- Reusable class-level fixtures within test classes

**Factory pattern:**
- Classes like `AbsSin`, `AbsSin2D` used as test factories
- Subclass pattern for creating variations (e.g., `AbsSin2DL(AbsSin2D)`)

## Coverage

**Requirements:** No explicit enforcement, but coverage reports generated

**View Coverage:**
```bash
pytest --cov=src/easyscience --cov-report=html
pytest --cov --cov-report=xml              # For CI/codecov
```

**Coverage configuration:**
- File: `.coveragerc`
- Source path: `src/easyscience/`
- XML reports used by CI/codecov service

## Test Types

**Unit Tests:**
- Location: `tests/unit_tests/`
- Scope: Individual classes and methods in isolation
- Approach: Direct instantiation, MagicMock for dependencies, parametrization for variants
- Example: `test_ObjBase_create`, `test_Fitter_constructor`

**Integration Tests:**
- Location: `tests/integration_tests/`
- Scope: Multiple components working together
- Approach: Real object creation, actual fitting operations, real parameter changes
- Example: `test_fitter.py` with actual numpy fitting against synthetic data

**E2E Tests:**
- Framework: Not explicitly used
- Status: Integration tests serve as higher-level validation

## Common Patterns

**Async Testing:**
- Not applicable; codebase is synchronous

**Error Testing:**
```python
# Parametrized error cases (test_obj_base.py, line 98-101)
@pytest.mark.parametrize("value", ("abc", False, (), []))
def test_CollectionBase_create_fail(cls, setup_pars, value):
    name = setup_pars["name"]
    del setup_pars["name"]
    with pytest.raises(AttributeError):
        cls(name, bad_item=value)
```

**Parametrized Testing:**
```python
# Multi-value parametrization (test_collection_base.py, line 73-74)
@pytest.mark.parametrize("cls", class_constructors)
@pytest.mark.parametrize("value", range(1, 11))
def test_CollectionBase_from_ObjBase(cls, setup_pars: dict, value: int):
    # Tests with 10 different values, multiple classes
```

**Custom Context Managers:**
```python
# Custom assert helper (test_obj_base.py, line 42-55)
@contextmanager
def not_raises(expected_exception: Union[Type[BaseException], List[Type[BaseException]]]):
    try:
        yield
    except expected_exception:
        raise pytest.fail("Did raise exception when it should not.")
    except Exception as err:
        raise pytest.fail(f"An unexpected exception {repr(err)} raised.")
```

**Global State Management:**
```python
# Clear global map before/after tests (test_global_object.py, line 41-46)
@pytest.fixture
def clear_global_map(self):
    """Clear global map before and after each test"""
    global_object.map._clear()
    yield
    global_object.map._clear()
```

**Test Organization - When/Then/Expect pattern:**
```python
# Observed in multiple tests (test_fitter.py, test_global_object.py)
def test_feature(self, fixture):
    # When Then
    result = some_operation()

    # Expect
    assert result == expected_value
```

---

*Testing analysis: 2026-02-05*
