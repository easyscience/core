# Parameter Dependency Serialization

This document explains how to serialize and deserialize `Parameter` objects that have dependencies.

## Overview

Parameters with dependencies can now be serialized to dictionaries (and JSON) while preserving their dependency relationships. After deserialization, the dependencies are automatically reconstructed using the `unique_name` attribute to match parameters.

## Key Features

- **Automatic dependency serialization**: Dependency expressions and maps are automatically saved during serialization
- **Unique name matching**: Dependencies are resolved using `unique_name` attributes after deserialization  
- **Bulk dependency resolution**: Utility functions help resolve all dependencies at once
- **JSON compatibility**: Full support for JSON serialization/deserialization

## Usage

### Basic Serialization/Deserialization

```python
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

# Serialize to dictionary
b_dict = b.as_dict()

# Clear global map (simulate new environment)
global_object.map._clear()

# Deserialize
new_b = Parameter.from_dict(b_dict) 

# Resolve dependencies
resolve_all_parameter_dependencies({"b": new_b})

# Dependencies are now working
a.value = 5.0
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

During serialization, the following additional fields are added to dependent parameters:

- `_dependency_string`: The original dependency expression
- `_dependency_map_unique_names`: A mapping of dependency keys to unique names
- `_independent`: Boolean flag indicating if the parameter is dependent

### Deserialization

During deserialization:

1. Parameters are created normally but marked as independent temporarily
2. Dependency information is stored in `_pending_dependency_string` and `_pending_dependency_map_unique_names` attributes
3. After all parameters are loaded, `resolve_all_parameter_dependencies()` establishes the dependency relationships

### Dependency Resolution

The dependency resolution process:

1. Scans for parameters with pending dependencies
2. Looks up dependency objects by their `unique_name` in the global map
3. Calls `make_dependent_on()` to establish the dependency relationship
4. Cleans up temporary attributes

## Error Handling

The system provides detailed error messages for common issues:

- Missing dependencies (parameter with required unique_name not found)
- Invalid dependency expressions
- Circular dependency detection

## Utility Functions

### `resolve_all_parameter_dependencies(obj)`

Recursively finds all Parameter objects with pending dependencies and resolves them.

**Parameters:**
- `obj`: Object to search for Parameters (can be Parameter, list, dict, or complex object)

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

1. **Always resolve dependencies after deserialization**: Use `resolve_all_parameter_dependencies()` after loading serialized parameters

2. **Handle the global map carefully**: The global map must contain all referenced parameters for dependency resolution to work

3. **Use unique names for cross-references**: When creating dependency expressions that reference other parameters, consider using unique names with quotes: `'Parameter_0'`

4. **Error handling**: Wrap dependency resolution in try-catch blocks for robust error handling

5. **Bulk operations**: For complex object hierarchies, use the utility functions to handle all parameters at once

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

This system ensures that complex parameter hierarchies with dependencies can be reliably serialized and reconstructed while maintaining their behavioral relationships.