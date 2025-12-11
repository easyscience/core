# Welcome to EasyScience's documentation!

**EasyScience** is a foundational Python library that provides the building blocks for scientific data simulation, analysis, and fitting.
It implements a descriptor-based object system with global state management, making it easier to create scientific models with parameters
that have units, bounds, and dependencies.

```python
from easyscience import Parameter, ObjBase, Fitter

# Create a model with scientific parameters
class SineModel(ObjBase):
    def __init__(self, amplitude=1.0, frequency=1.0, phase=0.0):
        amp = Parameter("amplitude", amplitude, min=0, max=10, unit="V")
        freq = Parameter("frequency", frequency, min=0.1, max=5, unit="Hz") 
        phase = Parameter("phase", phase, min=-3.14, max=3.14, unit="rad")
        super().__init__("sine_model", amplitude=amp, frequency=freq, phase=phase)
    
    def __call__(self, x):
        return self.amplitude.value * np.sin(2*np.pi*self.frequency.value*x + self.phase.value)

# Fit to experimental data
model = SineModel()
model.amplitude.fixed = False  # Allow fitting
fitter = Fitter(model, model)
result = fitter.fit(x=x_data, y=y_data)
```

## Key Features

**Scientific Parameters with Units**
:   Parameters automatically handle physical units, bounds, and uncertainties using [scipp](https://scipp.github.io/) integration.

**Parameter Dependencies**
:   Express mathematical relationships between parameters that update automatically when dependencies change.

**Multi-Backend Fitting**
:   Unified interface to LMFit, Bumps, and DFO-LS optimization engines with easy algorithm comparison.

**Complete Serialization**
:   Save and restore entire model states including parameter relationships and dependencies.

**Global State Management**
:   Automatic tracking of all objects and their relationships with built-in undo/redo capabilities.

**Developer-Friendly**
:   Clean APIs, comprehensive testing utilities, and extensive documentation for building scientific applications.

## Why EasyScience?

**Type Safety & Units**
:   Prevent common scientific computing errors with automatic unit checking and strong typing.

**Reproducible Research**
:   Complete state serialization ensures exact reproducibility of scientific analyses.

**Algorithm Flexibility**
:   Compare different optimization approaches without changing your model code.

**Extensible Architecture**
:   Descriptor pattern makes it easy to create new parameter types and model components.

## Open Source & Cross-Platform

EasyScience is free and open-source software with the source code openly shared on [GitHub repository](https://github.com/easyScience/EasyScience).

* **Cross-platform** - Written in Python and available for Windows, macOS, and Linux
* **Well-tested** - Comprehensive test suite ensuring reliability across platforms  
* **Community-driven** - Open to contributions and feature requests
* **Production-ready** - Used in multiple scientific applications worldwide

## Projects Built with EasyScience

EasyScience serves as the foundation for several scientific applications:

**easyDiffraction**

<img src="https://raw.githubusercontent.com/easyScience/easyDiffractionWww/master/assets/img/card.png" alt="easyDiffraction" width="300">

Scientific software for modeling and analysis of neutron diffraction data, providing an intuitive interface for crystallographic refinement.

[Visit easyDiffraction](https://easydiffraction.org)

**easyReflectometry**

<img src="https://raw.githubusercontent.com/easyScience/easyReflectometryWww/master/assets/img/card.png" alt="easyReflectometry" width="300">

Scientific software for modeling and analysis of neutron reflectometry data, enabling detailed study of thin film structures.

[Visit easyReflectometry](https://easyreflectometry.org)


EasyScience's flexible architecture makes it ideal for building domain-specific scientific applications. The comprehensive API and documentation help you get started quickly.

## Quick Start

Ready to begin? Here's how to get started:

1. **Install EasyScience**: `pip install easyscience`
2. **Read the Overview**: Understand the core concepts and architecture
3. **Try the Examples**: Work through practical fitting examples
4. **Explore the API**: Dive into the comprehensive reference documentation

```bash
pip install easyscience
```

Then explore the tutorials and examples to learn the key concepts!

## Need Help?

* **GitHub Issues**: Report bugs or request features on [GitHub Issues](https://github.com/easyScience/EasyScience/issues)
* **Discussions**: Ask questions in [GitHub Discussions](https://github.com/easyScience/EasyScience/discussions)  
* **API Reference**: Complete documentation of all classes and methods
* **Examples**: Practical tutorials and code samples

## Contributing

EasyScience is developed openly and welcomes contributions! Whether you're fixing bugs, adding features, improving documentation, or sharing usage examples, your contributions help make scientific computing more accessible.

Visit our [GitHub repository](https://github.com/easyScience/EasyScience) to:

* Report issues or suggest features
* Submit pull requests
* Join discussions about development
* Help improve documentation
