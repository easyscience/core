[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)
[![PyPI badge](http://img.shields.io/pypi/v/EasyScience.svg)](https://pypi.python.org/pypi/EasyScience)
[![License: BSD 3-Clause](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](LICENSE)

# Easyscience

## About

EasyScience package is the foundation of the EasyScience family of projects, providing the building blocks for libraries and applications
which aim to make scientific data simulation and analysis easier.

## Install

**EasyScience** can be downloaded using pip:

```pip install easyscience```

Or direct from the repository:

```pip install https://github.com/easyScience/EasyScience```

### Development with Pixi

For development, we recommend using [pixi](https://pixi.sh), which provides a unified package and environment management solution:

1. Install pixi following the [official installation guide](https://pixi.sh/latest/#installation)

2. Clone the repository and navigate to the project directory:
```bash
git clone https://github.com/easyScience/EasyScience.git
cd EasyScience
```

3. Install dependencies and set up the development environment:
```bash
pixi install
```

4. Run tests:
```bash
pixi run test
```

5. Run linting:
```bash
pixi run lint
```

6. Build the package:
```bash
pixi run build
```

Available pixi tasks:
- `pixi run test` - Run the full test suite with coverage
- `pixi run test-unit` - Run only unit tests
- `pixi run lint` - Check code style with ruff
- `pixi run lint-fix` - Fix code style issues automatically
- `pixi run format` - Format code with ruff
- `pixi run build` - Build the package
- `pixi run docs-build` - Build documentation

## Test

After installation, launch the test suite:

```python -m pytest```

## Documentation

Documentation can be found at:

[https://easyScience.github.io/EasyScience](https://easyScience.github.io/EasyScience)

## Contributing
We absolutely welcome contributions. **EasyScience** is maintained by the ESS and on a volunteer basis and thus we need to foster a community that can support user questions and develop new features to make this software a useful tool for all users while encouraging every member of the community to share their ideas.

## License
While **EasyScience** is under the BSD-3 license, DFO-LS is subject to the GPL license.


