# Parameter Dependency Serialization

This document explains how to serialize and deserialize `Parameter`
objects that have dependencies.

## Overview

Parameters with dependencies can now be serialized to dictionaries (and
JSON) while preserving their dependency relationships. After
deserialization, the dependencies are automatically reconstructed using
the `serializer_id` attribute to match parameters, with `unique_name`
attribute being used as a fallback.

## Key Features

- **Automatic dependency serialization**: Dependency expressions and
  maps are automatically saved during serialization
- **Reliable dependency resolution**: Dependencies are resolved using
  stable `serializer_id` attributes with `unique_name` as fallback after
  deserialization
- **Order-independent loading**: Parameters can be loaded in any order
  thanks to the reliable ID system
- **Bulk dependency resolution**: Utility functions help resolve all
  dependencies at once
- **JSON compatibility**: Full support for JSON
  serialization/deserialization
- **Backward compatibility**: Existing code using `unique_name`
  continues to work as fallback

## Usage

### Basic Serialization/Deserialization

```python
import json
from easyscience import Parameter, global_object
from easyscience.variable.parameter_dependency_resolver import resolve_all_parameter_dependencies

# Create parameters with dependencies
a = Parameter(name="a", value=2.0, unit="m", min=0, max=10)
b = Parameter.from_dependency(
    name="b",
    dependency_expression="2 * a",
    dependency_map={"a": a},
    unit="m"
)

# Serialize to dictionary and save to file
params_dict = {"a": a.as_dict(), "b": b.as_dict()}
with open("parameters.json", "w") as f:
    json.dump(params_dict, f, indent=2, default=str)

print("Parameters saved to parameters.json")
```

In a new Python session:

```python
import json
from easyscience import Parameter, global_object
from easyscience.variable.parameter_dependency_resolver import resolve_all_parameter_dependencies

# Load parameters from file
with open("parameters.json", "r") as f:
    params_dict = json.load(f)

# Clear global map (simulate new environment)
global_object.map._clear()

# Deserialize parameters
new_a = Parameter.from_dict(params_dict["a"])
new_b = Parameter.from_dict(params_dict["b"])

# Resolve dependencies
resolve_all_parameter_dependencies({"a": new_a, "b": new_b})

# Dependencies are now working
new_a.value = 5.0
print(new_b.value)  # Will be 10.0 (2 * 5.0)
```

### JSON Serialization

```python
import json

# Serialize to JSON
param_dict = parameter.as_dict()
json_str = json.dumps(param_dict, default=str)

# Deserialize from JSON
loaded_dict = json.loads(json_str)
new_param = Parameter.from_dict(loaded_dict)

# Resolve dependencies
resolve_all_parameter_dependencies(new_param)
```

### Bulk Operations

```python
from easyscience.variable.parameter_dependency_resolver import get_parameters_with_pending_dependencies

# Create multiple parameters with dependencies
params = create_parameter_hierarchy()  # Your function

# Serialize all
serialized = {name: param.as_dict() for name, param in params.items()}

# Clear and deserialize
global_object.map._clear()
new_params = {name: Parameter.from_dict(d) for name, d in serialized.items()}

# Check which parameters have pending dependencies
pending = get_parameters_with_pending_dependencies(new_params)
print(f"Found {len(pending)} parameters with pending dependencies")

# Resolve all at once
resolve_all_parameter_dependencies(new_params)
```

## Implementation Details

### Serialization

During serialization, the following additional fields are added to
dependent parameters:

- `_dependency_string`: The original dependency expression
- `_dependency_map_serializer_ids`: A mapping of dependency keys to
  stable dependency IDs (preferred)
- `_dependency_map_unique_names`: A mapping of dependency keys to unique
  names (fallback)
- `__serializer_id`: The parameter's own unique dependency ID
- `_independent`: Boolean flag indicating if the parameter is dependent

### Deserialization

During deserialization:

1. Parameters are created normally but marked as independent temporarily
2. Dependency information is stored in `_pending_dependency_string`,
   `_pending_dependency_map_serializer_ids`, and
   `_pending_dependency_map_unique_names` attributes
3. The parameter's own `__serializer_id` is restored from serialized
   data
4. After all parameters are loaded,
   `resolve_all_parameter_dependencies()` establishes the dependency
   relationships using dependency IDs first, then unique names as
   fallback

### Dependency Resolution

The dependency resolution process:

1. Scans for parameters with pending dependencies
2. First attempts to look up dependency objects by their stable
   `serializer_id`
3. Falls back to `unique_name` lookup in the global map if serializer_id
   is not available
4. Calls `make_dependent_on()` to establish the dependency relationship
5. Cleans up temporary attributes

This dual-strategy approach ensures reliable dependency resolution
regardless of parameter loading order while maintaining backward
compatibility.

## Error Handling

The system provides detailed error messages for common issues:

- Missing dependencies (parameter with required unique_name not found)
- Invalid dependency expressions
- Circular dependency detection

## Utility Functions

### `resolve_all_parameter_dependencies(obj)`

Recursively finds all Parameter objects with pending dependencies and
resolves them.

**Parameters:**

- `obj`: Object to search for Parameters (can be Parameter, list, dict,
  or complex object)

**Returns:**

- None (modifies parameters in place)

**Raises:**

- `ValueError`: If dependency resolution fails

### `get_parameters_with_pending_dependencies(obj)`

Finds all Parameter objects that have pending dependencies.

**Parameters:**

- `obj`: Object to search for Parameters

**Returns:**

- `List[Parameter]`: List of parameters with pending dependencies

## Best Practices

1. **Always resolve dependencies after deserialization**: Use
   `resolve_all_parameter_dependencies()` after loading serialized
   parameters

2. **Handle the global map carefully**: The global map must contain all
   referenced parameters for dependency resolution to work

3. **Use unique names for cross-references**: When creating dependency
   expressions that reference other parameters, consider using unique
   names with quotes: `'Parameter_0'`

4. **Error handling**: Wrap dependency resolution in try-catch blocks
   for robust error handling

5. **Bulk operations**: For complex object hierarchies, use the utility
   functions to handle all parameters at once

6. **Reliable ordering**: With the new dependency ID system, parameters
   can be loaded in any order without affecting dependency resolution

7. **Access dependency ID**: Use `parameter.serializer_id` to access the
   stable ID for debugging or manual cross-referencing

## Example: Complex Hierarchy

```python
def save_model(model):
    \"\"\"Save a model with parameter dependencies to JSON.\"\"\"
    model_dict = model.as_dict()
    with open('model.json', 'w') as f:
        json.dump(model_dict, f, indent=2, default=str)

def load_model(filename):
    \"\"\"Load a model from JSON and resolve dependencies.\"\"\"
    global_object.map._clear()  # Start fresh

    with open(filename) as f:
        model_dict = json.load(f)

    model = Model.from_dict(model_dict)

    # Resolve all parameter dependencies
    resolve_all_parameter_dependencies(model)

    return model
```

This system ensures that complex parameter hierarchies with dependencies
can be reliably serialized and reconstructed while maintaining their
behavioral relationships.
