# API Reference

This reference provides detailed documentation for all EasyScience classes and functions.

## Core Variables and Descriptors

### Descriptor Base Classes

::: easyscience.variable.DescriptorBase
    options:
      members: true

::: easyscience.variable.DescriptorNumber
    options:
      members: true

::: easyscience.variable.DescriptorArray
    options:
      members: true

::: easyscience.variable.DescriptorStr
    options:
      members: true

::: easyscience.variable.DescriptorBool
    options:
      members: true

::: easyscience.variable.DescriptorAnyType
    options:
      members: true

### Parameters

::: easyscience.variable.Parameter
    options:
      members: true

The Parameter class extends DescriptorNumber with fitting capabilities, bounds, and dependency relationships.

## Base Classes for Models

### BasedBase

::: easyscience.base_classes.BasedBase
    options:
      members: true

Base class providing serialization, global object registration, and interface management.

### ObjBase

::: easyscience.base_classes.ObjBase
    options:
      members: true

Container class for creating scientific models with parameters. All user-defined models should inherit from this class.

### Collections

::: easyscience.base_classes.CollectionBase
    options:
      members: true

Mutable sequence container for scientific objects with automatic parameter tracking.

## Fitting and Optimization

### Fitter

::: easyscience.fitting.Fitter
    options:
      members: true

Main fitting engine supporting multiple optimization backends.

### Available Minimizers

::: easyscience.fitting.AvailableMinimizers
    options:
      members: true

Enumeration of available optimization backends.

### Fit Results

::: easyscience.fitting.FitResults
    options:
      members: true

Container for fitting results including parameters, statistics, and diagnostics.

### Minimizer Base Classes

::: easyscience.fitting.minimizers.MinimizerBase
    options:
      members: true

Abstract base class for all minimizer implementations.

::: easyscience.fitting.minimizers.LMFit
    options:
      members: true

LMFit-based minimizer implementation.

::: easyscience.fitting.minimizers.Bumps
    options:
      members: true

Bumps-based minimizer implementation.

::: easyscience.fitting.minimizers.DFO
    options:
      members: true

DFO-LS-based minimizer implementation.

## Global State Management

### Global Object

::: easyscience.global_object.GlobalObject
    options:
      members: true

Singleton managing global state, logging, and object tracking.

### Object Map

::: easyscience.global_object.Map
    options:
      members: true

Graph-based registry for tracking object relationships and dependencies.

### Undo/Redo System

::: easyscience.global_object.undo_redo.UndoStack
    options:
      members: true

Stack-based undo/redo system for parameter changes.

## Serialization and I/O

### Serializer Components

::: easyscience.io.SerializerComponent
    options:
      members: true

Base class providing serialization capabilities.

::: easyscience.io.SerializerDict
    options:
      members: true

Dictionary-based serialization implementation.

::: easyscience.io.SerializerBase
    options:
      members: true

Base serialization functionality.

## Models and Examples

### Polynomial Model

::: easyscience.models.Polynomial
    options:
      members: true

Built-in polynomial model for demonstration and testing.

## Job Management

### Analysis and Experiments

::: easyscience.job.AnalysisBase
    options:
      members: true

::: easyscience.job.ExperimentBase
    options:
      members: true

::: easyscience.job.JobBase
    options:
      members: true

::: easyscience.job.TheoreticalModelBase
    options:
      members: true

## Utility Functions

### Decorators

::: easyscience.global_object.undo_redo.property_stack

Decorator for properties that should be tracked in the undo/redo system.

### Class Tools

::: easyscience.utils.classTools.addLoggedProp

Utility for adding logged properties to classes.

### String Utilities

::: easyscience.utils.string
    options:
      members: true

### Parameter Dependencies

::: easyscience.variable.parameter_dependency_resolver.resolve_all_parameter_dependencies

Resolve all pending parameter dependencies after deserialization.

::: easyscience.variable.parameter_dependency_resolver.get_parameters_with_pending_dependencies

Find parameters that have unresolved dependencies.

## Constants and Enumerations

The `easyscience.global_object` is a global singleton instance managing application state.

## Exception Classes

::: easyscience.fitting.minimizers.FitError

Exception raised when fitting operations fail.

## Usage Examples

For practical usage examples and tutorials, see:

* [Overview](../getting-started/overview.md) - Introduction and key concepts
* [Fitting Introduction](../fitting/introduction.md) - Comprehensive fitting guide
* [Installation](../getting-started/installation.md) - Installation instructions

The API reference covers all public classes and methods. For implementation details and advanced usage patterns, refer to the source code and test suites in the repository.
