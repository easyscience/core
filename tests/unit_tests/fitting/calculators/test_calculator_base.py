#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

"""Unit tests for CalculatorBase abstract class."""

from unittest.mock import MagicMock

import numpy as np
import pytest

from easyscience import global_object
from easyscience.base_classes import ModelBase
from easyscience.fitting.calculators.calculator_base import CalculatorBase


def create_mock_model(name="MockModel"):
    """Helper function to create a mock model that is an instance of ModelBase."""

    class MockModel(ModelBase):
        pass

    model = MockModel(display_name=name)
    return model


class TestCalculatorBase:
    """Tests for the CalculatorBase abstract class."""

    @pytest.fixture
    def clear(self):
        """Clear global map to avoid test contamination."""
        global_object.map._clear()
        yield
        global_object.map._clear()

    @pytest.fixture
    def mock_model(self, clear):
        """Create a mock model object."""
        return create_mock_model("MockModel")

    @pytest.fixture
    def mock_instrumental_parameters(self, clear):
        """Create mock instrumental parameters."""
        return create_mock_model("MockInstrument")

    @pytest.fixture
    def concrete_calculator_class(self):
        """Create a concrete implementation of CalculatorBase for testing."""

        class ConcreteCalculator(CalculatorBase):
            name = "test_calculator"

            def calculate(self, x: np.ndarray) -> np.ndarray:
                # Simple identity function for testing
                return x * 2.0

        return ConcreteCalculator

    @pytest.fixture
    def calculator(self, clear, concrete_calculator_class, mock_model, mock_instrumental_parameters):
        """Create a calculator instance for testing."""
        return concrete_calculator_class(
            mock_model, mock_instrumental_parameters, unique_name="test_calc", display_name="TestCalc"
        )

    # Initialization tests
    def test_init_with_model_only(self, clear, concrete_calculator_class, mock_model):
        """Test initialization with only a model."""
        calc = concrete_calculator_class(mock_model, unique_name="test_1", display_name="Test1")
        assert calc.model is mock_model
        assert calc.instrumental_parameters is None

    def test_init_with_model_and_instrumental_parameters(
        self, clear, concrete_calculator_class, mock_model, mock_instrumental_parameters
    ):
        """Test initialization with model and instrumental parameters."""
        calc = concrete_calculator_class(
            mock_model, mock_instrumental_parameters, unique_name="test_2", display_name="Test2"
        )
        assert calc.model is mock_model
        assert calc.instrumental_parameters is mock_instrumental_parameters

    def test_init_with_kwargs(self, clear, concrete_calculator_class, mock_model):
        """Test initialization with additional kwargs."""
        calc = concrete_calculator_class(
            mock_model, unique_name="test_3", display_name="Test3", custom_option="value"
        )
        assert calc.additional_kwargs == {"custom_option": "value"}

    def test_init_with_none_model_raises_error(self, clear, concrete_calculator_class):
        """Test that initialization with None model raises ValueError."""
        with pytest.raises(ValueError, match="Model must be an instance of ModelBase"):
            concrete_calculator_class(None, unique_name="test_4", display_name="Test4")

    # Model property tests
    def test_model_getter(self, calculator, mock_model):
        """Test model getter property."""
        assert calculator.model is mock_model

    def test_model_setter(self, calculator):
        """Test model setter property."""
        new_model = create_mock_model("NewModel")
        calculator.model = new_model
        assert calculator.model is new_model

    def test_model_setter_with_none_raises_error(self, calculator):
        """Test that setting model to None raises ValueError."""
        with pytest.raises(ValueError, match="Model cannot be None"):
            calculator.model = None

    # Instrumental parameters property tests
    def test_instrumental_parameters_getter(self, calculator, mock_instrumental_parameters):
        """Test instrumental_parameters getter property."""
        assert calculator.instrumental_parameters is mock_instrumental_parameters

    def test_instrumental_parameters_setter(self, calculator):
        """Test instrumental_parameters setter property."""
        new_params = create_mock_model("NewInstrument")
        calculator.instrumental_parameters = new_params
        assert calculator.instrumental_parameters is new_params

    def test_instrumental_parameters_setter_with_none(self, calculator):
        """Test that instrumental_parameters can be set to None."""
        calculator.instrumental_parameters = None
        assert calculator.instrumental_parameters is None

    # Update methods tests
    def test_update_model(self, calculator):
        """Test update_model method."""
        new_model = create_mock_model("UpdatedModel")
        calculator.update_model(new_model)
        assert calculator.model is new_model

    def test_update_model_with_none_raises_error(self, calculator):
        """Test that update_model with None raises ValueError."""
        with pytest.raises(ValueError, match="Model cannot be None"):
            calculator.update_model(None)

    def test_update_instrumental_parameters(self, calculator):
        """Test update_instrumental_parameters method."""
        new_params = create_mock_model("UpdatedInstrument")
        calculator.update_instrumental_parameters(new_params)
        assert calculator.instrumental_parameters is new_params

    def test_update_instrumental_parameters_with_none(self, calculator):
        """Test that update_instrumental_parameters accepts None."""
        calculator.update_instrumental_parameters(None)
        assert calculator.instrumental_parameters is None

    # Calculate method tests
    def test_calculate_returns_array(self, calculator):
        """Test that calculate returns an array."""
        x = np.array([1.0, 2.0, 3.0])
        result = calculator.calculate(x)
        assert isinstance(result, np.ndarray)
        np.testing.assert_array_equal(result, np.array([2.0, 4.0, 6.0]))

    def test_calculate_with_empty_array(self, calculator):
        """Test calculate with empty array."""
        x = np.array([])
        result = calculator.calculate(x)
        assert len(result) == 0

    # Abstract method enforcement tests
    def test_cannot_instantiate_abstract_class(self, clear):
        """Test that CalculatorBase cannot be instantiated directly."""
        mock_model = create_mock_model()
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            CalculatorBase(mock_model)

    def test_subclass_must_implement_calculate(self, clear):
        """Test that subclasses must implement calculate method."""
        mock_model = create_mock_model()

        class IncompleteCalculator(CalculatorBase):
            pass  # Does not implement calculate

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteCalculator(mock_model)

    # Representation tests
    def test_repr_with_model_only(self, clear, concrete_calculator_class, mock_model):
        """Test __repr__ with only model."""
        calc = concrete_calculator_class(mock_model, unique_name="test_5", display_name="Test5")
        repr_str = repr(calc)
        assert "ConcreteCalculator" in repr_str
        assert "model=MockModel" in repr_str
        assert "instrumental_parameters" not in repr_str

    def test_repr_with_model_and_instrumental_parameters(
        self, clear, concrete_calculator_class, mock_model, mock_instrumental_parameters
    ):
        """Test __repr__ with model and instrumental parameters."""
        calc = concrete_calculator_class(mock_model, mock_instrumental_parameters, unique_name="test_6", display_name="Test6")
        repr_str = repr(calc)
        assert "ConcreteCalculator" in repr_str
        assert "model=" in repr_str
        assert "instrumental_parameters=" in repr_str

    def test_repr_with_model_without_name_attribute(self, clear, concrete_calculator_class):
        """Test __repr__ when model has no explicit name attribute (uses class name)."""
        model = create_mock_model()  # ModelBase without explicit name
        calc = concrete_calculator_class(model, unique_name="test_7", display_name="Test7")
        repr_str = repr(calc)
        assert "ConcreteCalculator" in repr_str
        # ModelBase subclass name will appear
        assert "MockModel" in repr_str or "model=" in repr_str

    # Name attribute tests
    def test_calculator_name_attribute(self, calculator):
        """Test that calculator has name attribute."""
        assert calculator.name == "test_calculator"

    def test_default_name_is_base(self):
        """Test that default name is 'base'."""
        assert CalculatorBase.name == "base"

    # Additional kwargs property tests
    def test_additional_kwargs_with_init(self, clear, concrete_calculator_class, mock_model):
        """Test additional_kwargs property with kwargs in init."""
        calc = concrete_calculator_class(
            mock_model,
            unique_name="test_8",
            display_name="Test8",
            custom_option="value",
            numeric_param=42
        )
        assert calc.additional_kwargs == {"custom_option": "value", "numeric_param": 42}

    def test_additional_kwargs_empty_by_default(self, clear, concrete_calculator_class, mock_model):
        """Test that additional_kwargs is empty dict when no kwargs provided."""
        calc = concrete_calculator_class(mock_model, unique_name="test_9", display_name="Test9")
        assert calc.additional_kwargs == {}


class TestCalculatorBaseWithRealModel:
    """Integration-style tests using actual EasyScience objects."""

    @pytest.fixture
    def clear(self):
        """Clear global map to avoid test contamination."""
        global_object.map._clear()
        yield
        global_object.map._clear()

    @pytest.fixture
    def real_parameter(self, clear):
        """Create a real Parameter object."""
        from easyscience.variable import Parameter
        return Parameter("test_param", value=5.0, unit="m")

    @pytest.fixture
    def concrete_calculator_class(self):
        """Create a concrete implementation that uses model parameters."""

        class ParameterAwareCalculator(CalculatorBase):
            name = "param_aware"

            def calculate(self, x: np.ndarray) -> np.ndarray:
                # Access parameter from model if available
                if hasattr(self._model, 'get_parameters'):
                    params = self._model.get_parameters()
                    if params:
                        scale = params[0].value
                        return x * scale
                return x

        return ParameterAwareCalculator

    def test_calculator_can_access_model_parameters(
        self, clear, concrete_calculator_class, real_parameter
    ):
        """Test that calculator can access parameters from model."""
        # Create a model that returns our real parameter
        class TestModel(ModelBase):
            def __init__(self, param):
                super().__init__(display_name="TestModel")
                self._param = param

            def get_parameters(self):
                return [self._param]

        model = TestModel(real_parameter)

        calc = concrete_calculator_class(model, unique_name="test_10", display_name="Test10")
        x = np.array([1.0, 2.0, 3.0])
        result = calc.calculate(x)

        # Should multiply by parameter value (5.0)
        np.testing.assert_array_equal(result, np.array([5.0, 10.0, 15.0]))
