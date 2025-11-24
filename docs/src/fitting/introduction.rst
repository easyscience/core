======================
Fitting in EasyScience
======================

EasyScience provides a flexible and powerful fitting framework that supports multiple optimization backends.
This guide covers both basic usage for users wanting to fit their data, and advanced patterns for developers building scientific components.

Overview
--------

The EasyScience fitting system consists of:

* **Parameters**: Scientific values with units, bounds, and fitting capabilities
* **Models**: Objects containing parameters, inheriting from ``ObjBase``
* **Fitter**: The main fitting engine supporting multiple minimizers
* **Minimizers**: Backend optimization engines (LMFit, Bumps, DFO-LS)

Quick Start
-----------

Basic Parameter and Model Setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import numpy as np
    from easyscience import ObjBase, Parameter, Fitter

    # Create a simple model with fittable parameters
    class SineModel(ObjBase):
        def __init__(self, amplitude_val=1.0, frequency_val=1.0, phase_val=0.0):
            amplitude = Parameter("amplitude", amplitude_val, min=0, max=10)
            frequency = Parameter("frequency", frequency_val, min=0.1, max=5)
            phase = Parameter("phase", phase_val, min=-np.pi, max=np.pi)
            super().__init__("sine_model", amplitude=amplitude, frequency=frequency, phase=phase)
        
        def __call__(self, x):
            return self.amplitude.value * np.sin(2 * np.pi * self.frequency.value * x + self.phase.value)

Basic Fitting Example
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Create test data
    x_data = np.linspace(0, 2, 100)
    true_model = SineModel(amplitude_val=2.5, frequency_val=1.5, phase_val=0.5)
    y_data = true_model(x_data) + 0.1 * np.random.normal(size=len(x_data))
    
    # Create model to fit with initial guesses
    fit_model = SineModel(amplitude_val=1.0, frequency_val=1.0, phase_val=0.0)
    
    # Set which parameters to fit (unfix them)
    fit_model.amplitude.fixed = False
    fit_model.frequency.fixed = False
    fit_model.phase.fixed = False
    
    # Create fitter and perform fit
    fitter = Fitter(fit_model, fit_model)
    result = fitter.fit(x=x_data, y=y_data)
    
    # Access results
    print(f"Chi-squared: {result.chi2}")
    print(f"Fitted amplitude: {fit_model.amplitude.value} ± {fit_model.amplitude.error}")
    print(f"Fitted frequency: {fit_model.frequency.value} ± {fit_model.frequency.error}")

Available Minimizers
-------------------

EasyScience supports multiple optimization backends:

.. code-block:: python

    from easyscience import AvailableMinimizers
    
    # View all available minimizers
    fitter = Fitter(model, model)
    print(fitter.available_minimizers)
    # Output: ['LMFit', 'LMFit_leastsq', 'LMFit_powell', 'Bumps', 'Bumps_simplex', 'DFO', 'DFO_leastsq']

Switching Minimizers
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Use LMFit (default)
    fitter.switch_minimizer(AvailableMinimizers.LMFit)
    result1 = fitter.fit(x=x_data, y=y_data)
    
    # Switch to Bumps
    fitter.switch_minimizer(AvailableMinimizers.Bumps)
    result2 = fitter.fit(x=x_data, y=y_data)
    
    # Use DFO for derivative-free optimization
    fitter.switch_minimizer(AvailableMinimizers.DFO)
    result3 = fitter.fit(x=x_data, y=y_data)

Parameter Management
-------------------

Setting Bounds and Constraints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Parameter with bounds
    param = Parameter(name="amplitude", value=1.0, min=0.0, max=10.0, unit="m")
    
    # Fix parameter (exclude from fitting)
    param.fixed = True
    
    # Unfix parameter (include in fitting)
    param.fixed = False
    
    # Change bounds dynamically
    param.min = 0.5
    param.max = 8.0

Parameter Dependencies
~~~~~~~~~~~~~~~~~~~~~

Parameters can depend on other parameters through expressions:

.. code-block:: python

    # Create independent parameters
    length = Parameter("length", 10.0, unit="m", min=1, max=100)
    width = Parameter("width", 5.0, unit="m", min=1, max=50)
    
    # Create dependent parameter
    area = Parameter.from_dependency(
        name="area",
        dependency_expression="length * width",
        dependency_map={"length": length, "width": width}
    )
    
    # When length or width changes, area updates automatically
    length.value = 15.0
    print(area.value)  # Will be 75.0 (15 * 5)

Using make_dependent_on() Method
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also make an existing parameter dependent on other parameters using the ``make_dependent_on()`` method. This is useful when you want to convert an independent parameter into a dependent one:

.. code-block:: python

    # Create independent parameters
    radius = Parameter("radius", 5.0, unit="m", min=1, max=20)
    height = Parameter("height", 10.0, unit="m", min=1, max=50)
    volume = Parameter("volume", 100.0, unit="m³")  # Initially independent
    pi = Parameter("pi", 3.14159, fixed=True)  # Constant parameter

    # Make volume dependent on radius and height
    volume.make_dependent_on(
        dependency_expression="pi * radius**2 * height",
        dependency_map={"radius": radius, "height": height, "pi": pi}
    )

    # Now volume automatically updates when radius or height changes
    radius.value = 8.0
    print(f"New volume: {volume.value:.2f} m³")  # Automatically calculated

    # The parameter becomes dependent and cannot be set directly
    try:
        volume.value = 200.0  # This will raise an AttributeError
    except AttributeError:
        print("Cannot set value of dependent parameter directly")

**What to expect:**

- The parameter becomes **dependent** and its ``independent`` property becomes ``False``
- You **cannot directly set** the value, bounds, or variance of a dependent parameter
- The parameter's value is **automatically recalculated** whenever any of its dependencies change
- Dependent parameters **cannot be fitted** (they are automatically fixed)
- The original value, unit, variance, min, and max are **overwritten** by the dependency calculation
- You can **revert to independence** using the ``make_independent()`` method if needed

Advanced Fitting Options
-----------------------

Setting Tolerances and Limits
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    fitter = Fitter(model, model)
    
    # Set convergence tolerance
    fitter.tolerance = 1e-8
    
    # Limit maximum function evaluations
    fitter.max_evaluations = 1000
    
    # Perform fit with custom settings
    result = fitter.fit(x=x_data, y=y_data)

Using Weights
~~~~~~~~~~~~

.. code-block:: python

    # Define weights (inverse variance)
    weights = 1.0 / errors**2  # where errors are your data uncertainties
    
    # Fit with weights
    result = fitter.fit(x=x_data, y=y_data, weights=weights)

Multidimensional Fitting
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    class AbsSin2D(ObjBase):
        def __init__(self, offset_val=0.0, phase_val=0.0):
            offset = Parameter("offset", offset_val)
            phase = Parameter("phase", phase_val)
            super().__init__("sin2D", offset=offset, phase=phase)
        
        def __call__(self, x):
            X, Y = x[:, 0], x[:, 1]  # x is 2D array
            return np.abs(np.sin(self.phase.value * X + self.offset.value)) * \
                   np.abs(np.sin(self.phase.value * Y + self.offset.value))
    
    # Create 2D data
    x_2d = np.column_stack([x_grid.ravel(), y_grid.ravel()])
    
    # Fit 2D model
    model_2d = AbsSin2D(offset_val=0.1, phase_val=1.0)
    model_2d.offset.fixed = False
    model_2d.phase.fixed = False
    
    fitter = Fitter(model_2d, model_2d)
    result = fitter.fit(x=x_2d, y=z_data.ravel())

Accessing Fit Results
--------------------

The ``FitResults`` object contains comprehensive information about the fit:

.. code-block:: python

    result = fitter.fit(x=x_data, y=y_data)
    
    # Fit statistics
    print(f"Chi-squared: {result.chi2}")
    print(f"Reduced chi-squared: {result.reduced_chi}")
    print(f"Number of parameters: {result.n_pars}")
    print(f"Success: {result.success}")
    
    # Parameter values and uncertainties
    for param_name, value in result.p.items():
        error = result.errors.get(param_name, 0.0)
        print(f"{param_name}: {value} ± {error}")
    
    # Calculated values and residuals
    y_calculated = result.y_calc
    residuals = result.residual
    
    # Plot results
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 4))
    plt.subplot(121)
    plt.plot(x_data, y_data, 'o', label='Data')
    plt.plot(x_data, y_calculated, '-', label='Fit')
    plt.legend()
    plt.subplot(122)
    plt.plot(x_data, residuals, 'o')
    plt.axhline(0, color='k', linestyle='--')
    plt.ylabel('Residuals')

Developer Guidelines
-------------------

Creating Custom Models
~~~~~~~~~~~~~~~~~~~~~~

For developers building scientific components:

.. code-block:: python

    from easyscience import ObjBase, Parameter
    
    class CustomModel(ObjBase):
        def __init__(self, param1_val=1.0, param2_val=0.0):
            # Always create Parameters with appropriate bounds and units
            param1 = Parameter("param1", param1_val, min=-10, max=10, unit="m/s")
            param2 = Parameter("param2", param2_val, min=0, max=1, fixed=True)
            
            # Call parent constructor with named parameters
            super().__init__("custom_model", param1=param1, param2=param2)
        
        def __call__(self, x):
            # Implement your model calculation
            return self.param1.value * x + self.param2.value
        
        def get_fit_parameters(self):
            # This is automatically implemented by ObjBase
            # Returns only non-fixed parameters
            return super().get_fit_parameters()

Best Practices
~~~~~~~~~~~~~

1. **Always set appropriate bounds** on parameters to constrain the search space
2. **Use meaningful units** for physical parameters
3. **Fix parameters** that shouldn't be optimized
4. **Test with different minimizers** for robustness
5. **Validate results** by checking chi-squared and residuals

Error Handling
~~~~~~~~~~~~~

.. code-block:: python

    from easyscience.fitting.minimizers import FitError
    
    try:
        result = fitter.fit(x=x_data, y=y_data)
        if not result.success:
            print(f"Fit failed: {result.message}")
    except FitError as e:
        print(f"Fitting error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

Testing Patterns
~~~~~~~~~~~~~~~

When writing tests for fitting code:

.. code-block:: python

    import pytest
    from easyscience import global_object
    
    @pytest.fixture
    def clear_global_map():
        """Clear global map before each test"""
        global_object.map._clear()
        yield
        global_object.map._clear()
    
    def test_model_fitting(clear_global_map):
        # Create model and test fitting
        model = CustomModel()
        model.param1.fixed = False
        
        # Generate test data
        x_test = np.linspace(0, 10, 50)
        y_test = 2.5 * x_test + 0.1 * np.random.normal(size=len(x_test))
        
        # Fit and verify
        fitter = Fitter(model, model)
        result = fitter.fit(x=x_test, y=y_test)
        
        assert result.success
        assert model.param1.value == pytest.approx(2.5, abs=0.1)

This comprehensive guide covers the essential aspects of fitting in EasyScience, from basic usage to advanced developer patterns.
The examples are drawn from the actual test suite and demonstrate real-world usage patterns.

