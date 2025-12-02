.. _overview:

Overview
========

EasyScience is a foundational Python library that provides the building blocks for scientific data simulation, analysis, and fitting.
It implements a descriptor-based object system with global state management, making it easy to create scientific models with parameters
that have units, bounds, and dependencies.

What is EasyScience?
--------------------

EasyScience serves as the core foundation for the EasyScience family of projects, offering:

* **Scientific Parameters**: Values with units, uncertainties, bounds, and fitting capabilities
* **Model Building**: Base classes for creating complex scientific models
* **Multi-backend Fitting**: Support for LMFit, Bumps, and DFO-LS optimization engines
* **Parameter Dependencies**: Express relationships between parameters through mathematical expressions
* **Serialization**: Save and load complete model states including parameter relationships
* **Undo/Redo System**: Track and revert changes to model parameters
* **Global State Management**: Unified tracking of all objects and their relationships

Key Concepts
------------

Descriptor-Based Architecture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

EasyScience uses a hierarchical descriptor system:

.. code-block:: python

    from easyscience import Parameter, ObjBase
    
    # Scientific parameter with units and bounds
    temperature = Parameter(
        name="temperature", 
        value=300.0, 
        unit="K", 
        min=0, 
        max=1000,
        description="Sample temperature"
    )
    
    # Model containing parameters
    class ThermalModel(ObjBase):
        def __init__(self, temp_val=300.0, coeff_val=1.0):
            temperature = Parameter("temperature", temp_val, unit="K", min=0, max=1000)
            coefficient = Parameter("coefficient", coeff_val, min=0, max=10)
            super().__init__("thermal_model", temperature=temperature, coefficient=coefficient)

The hierarchy flows from:

* ``DescriptorBase`` → ``DescriptorNumber`` → ``Parameter`` (fittable scientific values)
* ``BasedBase`` → ``ObjBase`` (containers for parameters and scientific models)
* ``CollectionBase`` (mutable sequences of scientific objects)

Units and Physical Quantities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

EasyScience integrates with `scipp <https://scipp.github.io/>`_ for robust unit handling:

.. code-block:: python

    # Parameters automatically handle units
    length = Parameter("length", 100, unit="cm", min=0, max=1000)
    
    # Unit conversions are automatic
    length.convert_unit("m")
    print(length.value)  # 1.0
    print(length.unit)   # m
    
    # Arithmetic operations preserve units
    area = length * length  # Results in m^2

Parameter Dependencies
~~~~~~~~~~~~~~~~~~~~~~~

Parameters can depend on other parameters through mathematical expressions:

.. code-block:: python

    # Independent parameters
    radius = Parameter("radius", 5.0, unit="m", min=0, max=100)
    height = Parameter("height", 10.0, unit="m", min=0, max=200)
    
    # Dependent parameter using mathematical expression
    volume = Parameter.from_dependency(
        name="volume",
        dependency_expression="3.14159 * radius**2 * height",
        dependency_map={"radius": radius, "height": height}
    )
    
    # Automatic updates
    radius.value = 10.0
    print(volume.value)  # Automatically recalculated

Global State Management
~~~~~~~~~~~~~~~~~~~~~~~

All EasyScience objects register with a global map for dependency tracking:

.. code-block:: python

    from easyscience import global_object
    
    # All objects are automatically tracked
    param = Parameter("test", 1.0)
    print(param.unique_name)  # Automatically generated unique identifier
    
    # Access global registry
    all_objects = global_object.map.vertices()
    
    # Clear for testing (important in unit tests)
    global_object.map._clear()

Fitting and Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~

EasyScience provides a unified interface to multiple optimization backends:

.. code-block:: python

    from easyscience import Fitter, AvailableMinimizers
    
    # Create fitter with model
    fitter = Fitter(model, model)  # model serves as both object and function
    
    # Switch between different optimizers
    fitter.switch_minimizer(AvailableMinimizers.LMFit)    # Levenberg-Marquardt
    fitter.switch_minimizer(AvailableMinimizers.Bumps)    # Bayesian inference
    fitter.switch_minimizer(AvailableMinimizers.DFO)      # Derivative-free
    
    # Perform fit
    result = fitter.fit(x=x_data, y=y_data, weights=weights)

Serialization and Persistence  
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Complete model states can be saved and restored:

.. code-block:: python

    # Save model to dictionary
    model_dict = model.as_dict()
    
    # Save to JSON
    import json
    with open('model.json', 'w') as f:
        json.dump(model_dict, f, indent=2, default=str)
    
    # Restore model
    with open('model.json', 'r') as f:
        loaded_dict = json.load(f)
    
    new_model = Model.from_dict(loaded_dict)
    
    # Resolve parameter dependencies after loading
    from easyscience.variable.parameter_dependency_resolver import resolve_all_parameter_dependencies
    resolve_all_parameter_dependencies(new_model)

Use Cases
---------

EasyScience is designed for:

Scientific Modeling
~~~~~~~~~~~~~~~~~~~~

* Creating physics-based models with parameters that have physical meaning
* Handling units consistently throughout calculations
* Managing complex parameter relationships and constraints

Data Fitting and Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~

* Fitting experimental data to theoretical models
* Comparing different optimization algorithms
* Uncertainty quantification and error propagation

Software Development
~~~~~~~~~~~~~~~~~~~~

* Building domain-specific scientific applications
* Creating reusable model components
* Implementing complex scientific workflows

Research and Education
~~~~~~~~~~~~~~~~~~~~~~

* Reproducible scientific computing
* Teaching scientific programming concepts
* Collaborative model development

Architecture Benefits
---------------------

**Type Safety**: Strong typing with unit checking prevents common errors

**Flexibility**: Multiple optimization backends allow algorithm comparison

**Extensibility**: Descriptor pattern makes it easy to add new parameter types

**Reproducibility**: Complete serialization enables exact state restoration

**Performance**: Efficient observer pattern minimizes unnecessary recalculations

**Testing**: Global state management with cleanup utilities supports robust testing

Getting Started
---------------

The best way to learn EasyScience is through examples:

1. **Basic Usage**: Start with simple parameters and models
2. **Fitting Tutorial**: Learn the fitting system with real data
3. **Advanced Features**: Explore parameter dependencies and serialization
4. **Development Guide**: Build your own scientific components

See the :doc:`installation` guide to get started, then explore the :doc:`../fitting/introduction` for practical examples.

EasyScience forms the foundation for more specialized packages in the EasyScience ecosystem, providing the core abstractions that make scientific computing more accessible and reliable.


