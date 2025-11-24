==============
API Reference
==============

This reference provides detailed documentation for all EasyScience classes and functions.

Core Variables and Descriptors
==============================

Descriptor Base Classes
-----------------------

.. autoclass:: easyscience.variable.DescriptorBase
   :members:
   :inherited-members:
   :show-inheritance:

.. autoclass:: easyscience.variable.DescriptorNumber
   :members:
   :inherited-members:
   :show-inheritance:

.. autoclass:: easyscience.variable.DescriptorArray
   :members:
   :inherited-members:
   :show-inheritance:

.. autoclass:: easyscience.variable.DescriptorStr
   :members:
   :inherited-members:
   :show-inheritance:

.. autoclass:: easyscience.variable.DescriptorBool
   :members:
   :inherited-members:
   :show-inheritance:

.. autoclass:: easyscience.variable.DescriptorAnyType
   :members:
   :inherited-members:
   :show-inheritance:

Parameters
----------

.. autoclass:: easyscience.variable.Parameter
   :members:
   :inherited-members:
   :show-inheritance:

   The Parameter class extends DescriptorNumber with fitting capabilities, bounds, and dependency relationships.

   **Key Methods:**

   .. automethod:: from_dependency
      :noindex:
   .. automethod:: make_dependent_on
      :noindex:
   .. automethod:: make_independent
      :noindex:
   .. automethod:: resolve_pending_dependencies
      :noindex:

Base Classes for Models
=======================

BasedBase
---------

.. autoclass:: easyscience.base_classes.BasedBase
   :members:
   :inherited-members:
   :show-inheritance:

   Base class providing serialization, global object registration, and interface management.

ObjBase
-------

.. autoclass:: easyscience.base_classes.ObjBase
   :members:
   :inherited-members:
   :show-inheritance:

   Container class for creating scientific models with parameters. All user-defined models should inherit from this class.

   **Key Methods:**

   .. automethod:: get_fit_parameters
      :noindex:
   .. automethod:: get_parameters
      :noindex:
   .. automethod:: _add_component

Collections
-----------

.. autoclass:: easyscience.base_classes.CollectionBase
   :members:
   :inherited-members:
   :show-inheritance:

   Mutable sequence container for scientific objects with automatic parameter tracking.

Fitting and Optimization
=========================

Fitter
-------

.. autoclass:: easyscience.fitting.Fitter
   :members:
   :show-inheritance:

   Main fitting engine supporting multiple optimization backends.

   **Key Methods:**

   .. autoproperty:: fit
      :noindex:
   .. automethod:: switch_minimizer
      :noindex:
   .. automethod:: make_model
   .. automethod:: evaluate

Available Minimizers
--------------------

.. autoclass:: easyscience.fitting.AvailableMinimizers
   :members:
   :show-inheritance:

   Enumeration of available optimization backends.

Fit Results
-----------

.. autoclass:: easyscience.fitting.FitResults
   :members:
   :show-inheritance:

   Container for fitting results including parameters, statistics, and diagnostics.

Minimizer Base Classes
----------------------

.. autoclass:: easyscience.fitting.minimizers.MinimizerBase
   :members:
   :show-inheritance:

   Abstract base class for all minimizer implementations.

.. autoclass:: easyscience.fitting.minimizers.LMFit
   :members:
   :show-inheritance:

   LMFit-based minimizer implementation.

.. autoclass:: easyscience.fitting.minimizers.Bumps
   :members:
   :show-inheritance:

   Bumps-based minimizer implementation.

.. autoclass:: easyscience.fitting.minimizers.DFO
   :members:
   :show-inheritance:

   DFO-LS-based minimizer implementation.

Global State Management
========================

Global Object
-------------

.. autoclass:: easyscience.global_object.GlobalObject
   :members:
   :show-inheritance:

   Singleton managing global state, logging, and object tracking.

Object Map
----------

.. autoclass:: easyscience.global_object.Map
   :members:
   :show-inheritance:

   Graph-based registry for tracking object relationships and dependencies.

Undo/Redo System
----------------

.. autoclass:: easyscience.global_object.undo_redo.UndoStack
   :members:
   :show-inheritance:

   Stack-based undo/redo system for parameter changes.

Serialization and I/O
=====================

Serializer Components
---------------------

.. autoclass:: easyscience.io.SerializerComponent
   :members:
   :show-inheritance:

   Base class providing serialization capabilities.

.. autoclass:: easyscience.io.SerializerDict
   :members:
   :show-inheritance:

   Dictionary-based serialization implementation.

.. autoclass:: easyscience.io.SerializerBase
   :members:
   :show-inheritance:

   Base serialization functionality.

Models and Examples
===================

Polynomial Model
----------------

.. autoclass:: easyscience.models.Polynomial
   :members:
   :show-inheritance:

   Built-in polynomial model for demonstration and testing.

Job Management
==============

Analysis and Experiments
------------------------

.. autoclass:: easyscience.job.AnalysisBase
   :members:
   :show-inheritance:

.. autoclass:: easyscience.job.ExperimentBase
   :members:
   :show-inheritance:

.. autoclass:: easyscience.job.JobBase
   :members:
   :show-inheritance:

.. autoclass:: easyscience.job.TheoreticalModelBase
   :members:
   :show-inheritance:

Utility Functions
=================

Decorators
----------

.. autofunction:: easyscience.global_object.undo_redo.property_stack

   Decorator for properties that should be tracked in the undo/redo system.

Class Tools
-----------

.. autofunction:: easyscience.utils.classTools.addLoggedProp

   Utility for adding logged properties to classes.

String Utilities
----------------

.. automodule:: easyscience.utils.string
   :members:

Parameter Dependencies
-----------------------

.. autofunction:: easyscience.variable.parameter_dependency_resolver.resolve_all_parameter_dependencies

   Resolve all pending parameter dependencies after deserialization.

.. autofunction:: easyscience.variable.parameter_dependency_resolver.get_parameters_with_pending_dependencies

   Find parameters that have unresolved dependencies.

Constants and Enumerations
===========================

.. autodata:: easyscience.global_object
   :annotation: GlobalObject

   Global singleton instance managing application state.

Exception Classes
=================

.. autoclass:: easyscience.fitting.minimizers.FitError
   :show-inheritance:

   Exception raised when fitting operations fail.

.. autoclass:: scipp.UnitError
   :show-inheritance:

   Exception raised for unit-related errors (from scipp dependency).

Usage Examples
==============

For practical usage examples and tutorials, see:

* :doc:`../getting-started/overview` - Introduction and key concepts
* :doc:`../fitting/introduction` - Comprehensive fitting guide
* :doc:`../getting-started/installation` - Installation instructions

The API reference covers all public classes and methods. For implementation details and advanced usage patterns, refer to the source code and test suites in the repository.
