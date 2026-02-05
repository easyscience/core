# Coding Conventions

**Analysis Date:** 2026-02-05

## Naming Patterns

**Files:**
- Module files use `snake_case.py` (e.g., `parameter.py`, `descriptor_number.py`)
- Test files prefixed with `test_` and match module name (e.g., `test_obj_base.py` for `obj_base.py`)
- Classes exported in `__init__.py` files (e.g., `src/easyscience/__init__.py`)

**Functions:**
- Method names use `snake_case` (e.g., `make_model`, `convert_to_pars_obj`)
- Private methods prefixed with single underscore (e.g., `_update_minimizer`, `_fit_function_wrapper`)
- Getter/setter properties use `@property` decorator (e.g., `minimizer`, `available_minimizers`)

**Variables:**
- Local variables use `snake_case`
- Instance variables prefixed with underscore for "private" (e.g., `_fit_object`, `_fit_function`, `_minimizer`)
- Constants appear in uppercase with underscores (e.g., `DEFAULT_MINIMIZER = AvailableMinimizers.LMFit_leastsq`)

**Types:**
- Class names use `PascalCase` (e.g., `ObjBase`, `Parameter`, `Fitter`, `GlobalObject`)
- Enum names in `PascalCase` (e.g., `AvailableMinimizers`)

## Code Style

**Formatting:**
- Tool: `ruff` (linter and formatter)
- Line length: 127 characters (configured in `pyproject.toml`)
- Quote style: Single quotes preferred (ruff format setting)

**Linting:**
- Tool: `ruff` via pre-commit hook
- Rules enforced: E (pycodestyle), F (Pyflakes), I (isort), S (flake8-bandit)
- Special rule: `S101` allows asserts in test files only (`*test_*.py`)
- Configuration in `pyproject.toml` with `[tool.ruff]` and `[tool.ruff.lint]` sections

**Pre-commit hooks:**
- `black` formatter (22.3.0)
- `trailing-whitespace` check
- `check-yaml`, `check-xml`, `check-toml` validators
- `pretty-format-json`, `pretty-format-yaml`
- `detect-private-key` security check

## Import Organization

**Order:**
1. `from __future__ import annotations` (if needed, typically first)
2. Standard library imports (e.g., `import copy`, `import logging`, `from typing import ...`)
3. Third-party imports (e.g., `import numpy as np`, `import pytest`, `from scipp import Variable`)
4. Relative local imports (e.g., `from ..utils.classTools import addLoggedProp`)
5. Conditional TYPE_CHECKING imports wrapped in `if TYPE_CHECKING:` block

**Path Aliases:**
- No aliases configured; uses relative imports within package
- Main package imports use dot-relative paths (e.g., `from ..variable import Parameter`)

**Single-line imports:**
- `isort` configuration enforces `force-single-line = true` in `pyproject.toml`
- Each import statement on separate line (e.g., `from typing import Any`, `from typing import Dict`)

## Error Handling

**Patterns:**
- Type validation before computation: Raise `TypeError` for invalid input types
- Value validation before computation: Raise `ValueError` for invalid values
- Logic/state errors: Raise `AttributeError` for missing or invalid attributes
- Serialization errors: Raise `SyntaxError` with detailed context about what failed
- Index errors: Raise `IndexError` with bounds information or invalid type message
- Not implemented features: Raise `NotImplementedError` with explanation

**Examples from codebase:**
```python
# Type validation (from parameter.py, line 83-88)
if not isinstance(min, numbers.Number):
    raise TypeError('`min` must be a number')
if not isinstance(value, numbers.Number):
    raise TypeError('`value` must be a number')

# Value validation (from parameter.py, line 89-94)
if value < min:
    raise ValueError(f'{value=} can not be less than {min=}')
if value > max:
    raise ValueError(f'{value=} can not be greater than {max=}')

# Attribute errors (from based_base.py, line 70)
if not isinstance(new_unique_name, str):
    raise TypeError('Unique name has to be a string.')

# Detailed serialization errors (from model_base.py)
raise SyntaxError(f"""Could not set parameter {key} during `from_dict` with full deserialized variable.""")
```

**Try/except usage:**
- Sparingly used; mostly to handle optional dependency imports
- Example: `try: import bumps except ImportError: ...` (available_minimizers.py)
- Broad exception catching followed by re-raising with context: `except Exception as e: raise SyntaxError(...)` (model_base.py, line 114-115)

## Logging

**Framework:** Python's standard `logging` module via custom `Logger` class

**Patterns:**
- Global logger instance: `from easyscience import global_object` then access `global_object.log`
- Logger creation: `logger = logging.getLogger(__name__)`
- Log level set at initialization: `logger.setLevel(self.level)` where level defaults to `logging.INFO`
- No conventional logging calls in main source; mostly debug prints (see concerns in debug code)

**Location:**
- Logger class: `src/easyscience/global_object/logger.py`
- Global object integration: `src/easyscience/global_object/global_object.py`

## Comments

**When to Comment:**
- Complex algorithms or non-obvious logic should have inline comments
- Class docstrings required (present in all major classes like `ObjBase`, `Parameter`, `Fitter`)
- Method docstrings required (shown with `:param`, `:return`, `:raises:` format)
- Function purpose statements in docstring

**JSDoc/TSDoc:**
- Uses Python docstrings with standard format:
  - Summary line (one sentence)
  - Blank line
  - Detailed description (optional)
  - `:param name: description` for parameters
  - `:return: description` for return value
  - `:rtype: type` for return type
  - `:raises: ExceptionType` for exceptions

**Example docstring (from fitter.py, line 47-53):**
```python
def initialize(self, fit_object, fit_function: Callable) -> None:
    """
    Set the model and callable in the calculator interface.

    :param fit_object: The EasyScience model object
    :param fit_function: The function to be optimized against.
    """
```

**Example with raises (from based_base.py, line 119-122):**
```python
:raises: AttributeError
...
raise AttributeError('Interface error for generating bindings. `interface` has to be set.')
```

## Function Design

**Size:** Functions typically 5-20 lines; property methods 1-5 lines

**Parameters:**
- Type hints used consistently (e.g., `fit_object, fit_function: Callable`)
- Optional parameters with default values (e.g., `pars=None`)
- `*args` and `**kwargs` used for flexible object construction in base classes (e.g., `ObjBase.__init__`)

**Return Values:**
- Property methods return single values without wrapping
- Class methods return `Callable`, `List[str]`, `Union[type]` as typed
- Methods modifying state typically return `None` (e.g., `_update_minimizer` returns `None`)

## Module Design

**Exports:**
- Public classes/functions listed in module `__init__.py`
- Main package init at `src/easyscience/__init__.py` imports core classes and sets up global object
- Example from `__init__.py`:
```python
from .base_classes import ObjBase
from .fitting import Fitter
from .variable import Parameter
__all__ = [__version__, global_object, ObjBase, Fitter, Parameter]
```

**Barrel Files:**
- Used for subpackages (e.g., `src/easyscience/fitting/__init__.py` exports `Fitter`, `AvailableMinimizers`)
- Pattern: Import from submodules, re-export in `__all__`

**Lazy Initialization:**
- Global object instantiated at module load time with special handling:
```python
# From __init__.py
global_object = GlobalObject()
global_object.instantiate_stack()
global_object.stack.enabled = False
```

## License Headers

All source files include SPDX license header:
```python
#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience
```

---

*Convention analysis: 2026-02-05*
