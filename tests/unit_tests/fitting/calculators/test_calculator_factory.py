#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

"""Unit tests for CalculatorFactoryBase and SimpleCalculatorFactory classes."""

from typing import List
from unittest.mock import MagicMock

import numpy as np
import pytest

from easyscience import global_object
from easyscience.base_classes import ModelBase
from easyscience.fitting.calculators.calculator_base import CalculatorBase
from easyscience.fitting.calculators.calculator_factory import (
    CalculatorFactoryBase,
    SimpleCalculatorFactory,
)


def create_mock_model():
    """Helper function to create a mock model that is an instance of ModelBase."""

    class MockModel(ModelBase):
        pass

    return MockModel()


class TestCalculatorFactoryBase:
    """Tests for the CalculatorFactoryBase abstract class."""

    @pytest.fixture
    def clear(self):
        """Clear global map to avoid test contamination."""
        global_object.map._clear()
        yield
        global_object.map._clear()

    @pytest.fixture
    def mock_model(self, clear):
        """Create a mock model object."""

        class MockModel(ModelBase):
            pass

        return MockModel()

    @pytest.fixture
    def mock_instrumental_parameters(self, clear):
        """Create mock instrumental parameters."""

        class MockInstrument(ModelBase):
            pass

        return MockInstrument()

    @pytest.fixture
    def concrete_calculator_class(self):
        """Create a concrete calculator implementation."""

        class TestCalculator(CalculatorBase):
            name = "test"

            def calculate(self, x: np.ndarray) -> np.ndarray:
                return x * 2.0

        return TestCalculator

    @pytest.fixture
    def concrete_factory_class(self, concrete_calculator_class):
        """Create a concrete factory implementation."""

        calc_class = concrete_calculator_class

        class TestFactory(CalculatorFactoryBase):
            def __init__(self):
                super().__init__()
                self._available_calculators["test"] = calc_class

            def create(self, calculator_name, model, instrumental_parameters=None, **kwargs):
                if calculator_name not in self._available_calculators:
                    raise ValueError(f"Unknown calculator: {calculator_name}")
                return self._available_calculators[calculator_name](model, instrumental_parameters, **kwargs)

        return TestFactory

    # Abstract class enforcement tests
    def test_cannot_instantiate_abstract_factory(self):
        """Test that CalculatorFactoryBase cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            CalculatorFactoryBase()

    def test_subclass_must_implement_create(self):
        """Test that subclasses must implement create method."""

        class IncompleteFactory(CalculatorFactoryBase):
            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteFactory()

    # Concrete factory tests
    def test_factory_available_calculators(self, concrete_factory_class):
        """Test available_calculators property."""
        factory = concrete_factory_class()
        assert factory.available_calculators == ["test"]

    def test_factory_create_calculator(self, concrete_factory_class, mock_model, mock_instrumental_parameters):
        """Test creating a calculator via factory."""
        factory = concrete_factory_class()
        calculator = factory.create("test", mock_model, mock_instrumental_parameters)
        assert isinstance(calculator, CalculatorBase)
        assert calculator.model is mock_model
        assert calculator.instrumental_parameters is mock_instrumental_parameters

    def test_factory_create_with_model_only(self, concrete_factory_class, mock_model):
        """Test creating calculator with only model."""
        factory = concrete_factory_class()
        calculator = factory.create("test", mock_model)
        assert calculator.model is mock_model
        assert calculator.instrumental_parameters is None

    def test_factory_create_unknown_calculator_raises_error(self, concrete_factory_class, mock_model):
        """Test that creating unknown calculator raises ValueError."""
        factory = concrete_factory_class()
        with pytest.raises(ValueError, match="Unknown calculator"):
            factory.create("unknown", mock_model)

    # Repr tests
    def test_factory_repr(self, concrete_factory_class):
        """Test factory __repr__."""
        factory = concrete_factory_class()
        repr_str = repr(factory)
        assert "TestFactory" in repr_str
        assert "test" in repr_str


class TestSimpleCalculatorFactory:
    """Tests for SimpleCalculatorFactory class."""

    @pytest.fixture
    def clear(self):
        """Clear global map to avoid test contamination."""
        global_object.map._clear()
        yield
        global_object.map._clear()

    @pytest.fixture
    def mock_model(self, clear):
        """Create a mock model object."""

        class MockModel(ModelBase):
            pass

        return MockModel()

    @pytest.fixture
    def mock_instrumental_parameters(self, clear):
        """Create mock instrumental parameters."""

        class MockInstrument(ModelBase):
            pass

        return MockInstrument()

    @pytest.fixture
    def calculator_class_a(self):
        """Create first concrete calculator class."""

        class CalculatorA(CalculatorBase):
            name = "calc_a"

            def calculate(self, x: np.ndarray) -> np.ndarray:
                return x * 2.0

        return CalculatorA

    @pytest.fixture
    def calculator_class_b(self):
        """Create second concrete calculator class."""

        class CalculatorB(CalculatorBase):
            name = "calc_b"

            def calculate(self, x: np.ndarray) -> np.ndarray:
                return x * 3.0

        return CalculatorB

    # Initialization tests
    def test_init_empty(self):
        """Test initialization with no calculators."""
        factory = SimpleCalculatorFactory()
        assert factory.available_calculators == []

    def test_init_with_calculators_dict(self, calculator_class_a, calculator_class_b):
        """Test initialization with calculators dictionary."""
        factory = SimpleCalculatorFactory({
            "a": calculator_class_a,
            "b": calculator_class_b,
        })
        assert set(factory.available_calculators) == {"a", "b"}

    # Available calculators tests
    def test_available_calculators_returns_list(self, calculator_class_a):
        """Test that available_calculators returns a list."""
        factory = SimpleCalculatorFactory({"a": calculator_class_a})
        result = factory.available_calculators
        assert isinstance(result, list)
        assert "a" in result

    # Create tests
    def test_create_calculator(self, calculator_class_a, mock_model, mock_instrumental_parameters):
        """Test creating a calculator."""
        factory = SimpleCalculatorFactory({"a": calculator_class_a})
        calculator = factory.create("a", mock_model, mock_instrumental_parameters)
        assert isinstance(calculator, CalculatorBase)
        assert calculator.model is mock_model
        assert calculator.instrumental_parameters is mock_instrumental_parameters

    def test_create_with_kwargs(self, calculator_class_a, mock_model):
        """Test creating calculator with additional kwargs."""
        factory = SimpleCalculatorFactory({"a": calculator_class_a})
        calculator = factory.create("a", mock_model, custom_option="value")
        assert calculator.additional_kwargs == {"custom_option": "value"}

    def test_create_unknown_calculator_raises_error(self, calculator_class_a, mock_model):
        """Test that creating unknown calculator raises ValueError."""
        factory = SimpleCalculatorFactory({"a": calculator_class_a})
        with pytest.raises(ValueError, match="Unknown calculator 'unknown'"):
            factory.create("unknown", mock_model)

    def test_create_error_message_includes_available(self, calculator_class_a, calculator_class_b, mock_model):
        """Test that error message includes available calculators."""
        factory = SimpleCalculatorFactory({
            "a": calculator_class_a,
            "b": calculator_class_b,
        })
        with pytest.raises(ValueError) as exc_info:
            factory.create("unknown", mock_model)
        assert "a" in str(exc_info.value) or "b" in str(exc_info.value)

    # Register tests
    def test_register_calculator(self, calculator_class_a, calculator_class_b):
        """Test registering a new calculator."""
        factory = SimpleCalculatorFactory({"a": calculator_class_a})
        factory.register("b", calculator_class_b)
        assert "b" in factory.available_calculators

    def test_register_overwrites_existing(self, calculator_class_a, calculator_class_b, clear):
        """Test that registering with existing name overwrites."""
        factory = SimpleCalculatorFactory({"a": calculator_class_a})
        factory.register("a", calculator_class_b)
        # Now "a" should create CalculatorB
        calc = factory.create("a", create_mock_model())
        assert calc.name == "calc_b"

    def test_register_invalid_class_raises_error(self, calculator_class_a):
        """Test that registering non-CalculatorBase raises TypeError."""
        factory = SimpleCalculatorFactory({"a": calculator_class_a})

        class NotACalculator:
            pass

        with pytest.raises(TypeError, match="must be a subclass of CalculatorBase"):
            factory.register("bad", NotACalculator)

    def test_register_non_class_raises_error(self, calculator_class_a):
        """Test that registering a non-class raises TypeError."""
        factory = SimpleCalculatorFactory({"a": calculator_class_a})
        with pytest.raises(TypeError, match="must be a subclass of CalculatorBase"):
            factory.register("bad", "not a class")

    # Unregister tests
    def test_unregister_calculator(self, calculator_class_a, calculator_class_b):
        """Test unregistering a calculator."""
        factory = SimpleCalculatorFactory({
            "a": calculator_class_a,
            "b": calculator_class_b,
        })
        factory.unregister("a")
        assert "a" not in factory.available_calculators
        assert "b" in factory.available_calculators

    def test_unregister_unknown_raises_error(self, calculator_class_a):
        """Test that unregistering unknown calculator raises KeyError."""
        factory = SimpleCalculatorFactory({"a": calculator_class_a})
        with pytest.raises(KeyError, match="Calculator 'unknown' is not registered"):
            factory.unregister("unknown")

    # Repr tests
    def test_repr_empty_factory(self):
        """Test __repr__ with empty factory."""
        factory = SimpleCalculatorFactory()
        repr_str = repr(factory)
        assert "SimpleCalculatorFactory" in repr_str
        assert "available=[]" in repr_str

    def test_repr_with_calculators(self, calculator_class_a, calculator_class_b):
        """Test __repr__ with calculators."""
        factory = SimpleCalculatorFactory({
            "a": calculator_class_a,
            "b": calculator_class_b,
        })
        repr_str = repr(factory)
        assert "SimpleCalculatorFactory" in repr_str
        assert "a" in repr_str or "b" in repr_str

    # Integration tests
    def test_created_calculator_works(self, calculator_class_a, mock_model):
        """Test that created calculator actually works."""
        factory = SimpleCalculatorFactory({"a": calculator_class_a})
        calculator = factory.create("a", mock_model)
        x = np.array([1.0, 2.0, 3.0])
        result = calculator.calculate(x)
        np.testing.assert_array_equal(result, np.array([2.0, 4.0, 6.0]))

    def test_create_multiple_calculators_independently(
        self, calculator_class_a, calculator_class_b, clear
    ):
        """Test creating multiple independent calculators."""
        factory = SimpleCalculatorFactory({
            "a": calculator_class_a,
            "b": calculator_class_b,
        })

        model_a = create_mock_model()
        model_b = create_mock_model()

        calc_a = factory.create("a", model_a)
        calc_b = factory.create("b", model_b)

        # They should be independent
        assert calc_a.model is model_a
        assert calc_b.model is model_b
        assert calc_a is not calc_b

        # And calculate differently
        x = np.array([1.0, 2.0])
        np.testing.assert_array_equal(calc_a.calculate(x), np.array([2.0, 4.0]))
        np.testing.assert_array_equal(calc_b.calculate(x), np.array([3.0, 6.0]))


class TestFactoryStatelessness:
    """Tests to verify that the factory is truly stateless."""

    @pytest.fixture
    def clear(self):
        """Clear global map to avoid test contamination."""
        global_object.map._clear()
        yield
        global_object.map._clear()

    @pytest.fixture
    def calculator_class(self):
        """Create a calculator class with counter for instances."""

        class CountingCalculator(CalculatorBase):
            name = "counting"
            instance_count = 0

            def __init__(self, model, instrumental_parameters=None, **kwargs):
                super().__init__(model, instrumental_parameters, **kwargs)
                CountingCalculator.instance_count += 1
                self.instance_id = CountingCalculator.instance_count

            def calculate(self, x: np.ndarray) -> np.ndarray:
                return x

        # Reset counter before each test
        CountingCalculator.instance_count = 0
        return CountingCalculator

    def test_factory_does_not_store_calculator_instances(self, calculator_class, clear):
        """Test that factory doesn't store references to created calculators."""
        factory = SimpleCalculatorFactory({"calc": calculator_class})
        mock_model = create_mock_model()

        calc1 = factory.create("calc", mock_model)
        calc2 = factory.create("calc", mock_model)

        # Each create should produce a new instance
        assert calc1 is not calc2
        assert calc1.instance_id == 1
        assert calc2.instance_id == 2

    def test_factory_has_no_current_calculator_attribute(self, calculator_class):
        """Test that factory has no 'current' calculator state."""
        factory = SimpleCalculatorFactory({"calc": calculator_class})

        # Should not have any attributes tracking current state
        assert not hasattr(factory, "_current_calculator")
        assert not hasattr(factory, "current_calculator")
        assert not hasattr(factory, "_current")

    def test_multiple_factories_are_independent(self, calculator_class, clear):
        """Test that multiple factory instances are independent."""
        factory1 = SimpleCalculatorFactory({"calc": calculator_class})
        factory2 = SimpleCalculatorFactory({"calc": calculator_class})

        mock_model = create_mock_model()

        calc1 = factory1.create("calc", mock_model)
        calc2 = factory2.create("calc", mock_model)

        # Each factory creates independent calculators
        assert calc1 is not calc2


class TestFactoryIsolation:
    """Tests to ensure calculator registries don't bleed between factory instances or subclasses."""

    @pytest.fixture
    def calculator_class_x(self):
        """First test calculator class."""
        class CalculatorX(CalculatorBase):
            name = "x"
            def calculate(self, x: np.ndarray) -> np.ndarray:
                return x
        return CalculatorX

    @pytest.fixture
    def calculator_class_y(self):
        """Second test calculator class."""
        class CalculatorY(CalculatorBase):
            name = "y"
            def calculate(self, x: np.ndarray) -> np.ndarray:
                return x * 2
        return CalculatorY

    @pytest.fixture
    def calculator_class_z(self):
        """Third test calculator class."""
        class CalculatorZ(CalculatorBase):
            name = "z"
            def calculate(self, x: np.ndarray) -> np.ndarray:
                return x * 3
        return CalculatorZ

    def test_instance_registration_does_not_affect_other_instances(
        self, calculator_class_x, calculator_class_y, calculator_class_z
    ):
        """Test that registering to one instance doesn't affect others."""
        factory1 = SimpleCalculatorFactory({"x": calculator_class_x})
        factory2 = SimpleCalculatorFactory({"y": calculator_class_y})

        # Register z to factory1 only
        factory1.register("z", calculator_class_z)

        # factory1 should have both x and z
        assert "x" in factory1.available_calculators
        assert "z" in factory1.available_calculators
        assert "y" not in factory1.available_calculators

        # factory2 should only have y
        assert "y" in factory2.available_calculators
        assert "x" not in factory2.available_calculators
        assert "z" not in factory2.available_calculators

    def test_subclass_registration_does_not_affect_parent_or_siblings(
        self, calculator_class_x, calculator_class_y
    ):
        """Test that subclass registries are independent."""

        calc_x = calculator_class_x
        calc_y = calculator_class_y

        class FactoryA(SimpleCalculatorFactory):
            def __init__(self):
                super().__init__()
                self._available_calculators["x"] = calc_x

        class FactoryB(SimpleCalculatorFactory):
            def __init__(self):
                super().__init__()
                self._available_calculators["y"] = calc_y

        factory_a = FactoryA()
        factory_b = FactoryB()

        # Each should have their own calculators
        assert "x" in factory_a.available_calculators
        assert "y" not in factory_a.available_calculators

        assert "y" in factory_b.available_calculators
        assert "x" not in factory_b.available_calculators

    def test_class_level_registry_not_modified_by_instance_register(
        self, calculator_class_x, calculator_class_y
    ):
        """Test that instance.register() doesn't modify other instances."""

        calc_x = calculator_class_x

        class MyFactory(SimpleCalculatorFactory):
            def __init__(self):
                super().__init__()
                self._available_calculators["x"] = calc_x

        # Create instance and register to it
        factory = MyFactory()
        factory.register("y", calculator_class_y)

        # Instance should have both
        assert "x" in factory.available_calculators
        assert "y" in factory.available_calculators

        # Create new instance - should NOT have y
        factory2 = MyFactory()
        assert "x" in factory2.available_calculators
        assert "y" not in factory2.available_calculators

    def test_unregister_from_one_instance_does_not_affect_others(
        self, calculator_class_x
    ):
        """Test that unregistering from one instance doesn't affect others."""
        factory1 = SimpleCalculatorFactory({"x": calculator_class_x})
        factory2 = SimpleCalculatorFactory({"x": calculator_class_x})
        
        # Unregister from factory1
        factory1.unregister("x")
        
        # factory1 should not have x
        assert "x" not in factory1.available_calculators
        
        # factory2 should still have x
        assert "x" in factory2.available_calculators


class TestFactoryErrorHandling:
    """Tests for improved error handling and validation."""

    @pytest.fixture
    def clear(self):
        """Clear global map to avoid test contamination."""
        global_object.map._clear()
        yield
        global_object.map._clear()

    @pytest.fixture
    def calculator_class(self):
        """Simple test calculator."""
        class TestCalc(CalculatorBase):
            name = "test"
            def calculate(self, x: np.ndarray) -> np.ndarray:
                return x
        return TestCalc

    def test_register_with_empty_name_raises_error(self, calculator_class):
        """Test that empty calculator name raises ValueError."""
        factory = SimpleCalculatorFactory()
        with pytest.raises(ValueError, match="non-empty string"):
            factory.register("", calculator_class)

    def test_register_with_non_string_name_raises_error(self, calculator_class):
        """Test that non-string calculator name raises ValueError."""
        factory = SimpleCalculatorFactory()
        with pytest.raises(ValueError, match="non-empty string"):
            factory.register(123, calculator_class)

    def test_register_overwrites_with_warning(self, calculator_class):
        """Test that overwriting existing calculator issues warning."""
        factory = SimpleCalculatorFactory({"test": calculator_class})
        
        class NewCalc(CalculatorBase):
            name = "new"
            def calculate(self, x: np.ndarray) -> np.ndarray:
                return x * 2
        
        with pytest.warns(UserWarning, match="Overwriting existing calculator 'test'"):
            factory.register("test", NewCalc)

    def test_create_with_non_string_name_raises_error(self, calculator_class, clear):
        """Test that create with non-string name raises ValueError."""
        factory = SimpleCalculatorFactory({"test": calculator_class})
        with pytest.raises(ValueError, match="must be a string"):
            factory.create(123, create_mock_model())

    def test_create_with_none_model_raises_error(self, calculator_class):
        """Test that create with None model raises TypeError."""
        factory = SimpleCalculatorFactory({"test": calculator_class})
        with pytest.raises(TypeError, match="Model cannot be None"):
            factory.create("test", None)

    def test_create_unknown_calculator_shows_available_in_error(self, calculator_class, clear):
        """Test that error message includes available calculators."""
        factory = SimpleCalculatorFactory({"calc1": calculator_class})
        with pytest.raises(ValueError, match="calc1") as exc_info:
            factory.create("unknown", create_mock_model())
        assert "Available calculators" in str(exc_info.value)

    def test_create_empty_factory_error_shows_none_available(self, clear):
        """Test error message when factory has no calculators."""
        factory = SimpleCalculatorFactory()
        with pytest.raises(ValueError, match="none") as exc_info:
            factory.create("anything", create_mock_model())
        assert "Available calculators: none" in str(exc_info.value)

    def test_create_wraps_calculator_init_errors(self, calculator_class, clear):
        """Test that calculator initialization errors are wrapped."""
        
        class BrokenCalc(CalculatorBase):
            name = "broken"
            def __init__(self, model, instrumental_parameters=None, **kwargs):
                raise RuntimeError("Something went wrong")
            def calculate(self, x: np.ndarray) -> np.ndarray:
                return x
        
        factory = SimpleCalculatorFactory({"broken": BrokenCalc})
        with pytest.raises(RuntimeError, match="Failed to create calculator 'broken'"):
            factory.create("broken", create_mock_model())


class TestCalculatorKwargsProperty:
    """Tests for the additional_kwargs property on CalculatorBase."""

    @pytest.fixture
    def clear(self):
        """Clear global map to avoid test contamination."""
        global_object.map._clear()
        yield
        global_object.map._clear()

    @pytest.fixture
    def calculator_class(self):
        """Simple calculator class for testing."""
        class TestCalc(CalculatorBase):
            name = "test"
            def calculate(self, x: np.ndarray) -> np.ndarray:
                return x
        return TestCalc

    def test_additional_kwargs_accessible(self, calculator_class, clear):
        """Test that additional_kwargs property is accessible."""
        calc = calculator_class(
            create_mock_model(),
            custom_param="value",
            another_option=42
        )
        kwargs = calc.additional_kwargs
        assert isinstance(kwargs, dict)
        assert kwargs["custom_param"] == "value"
        assert kwargs["another_option"] == 42

    def test_additional_kwargs_empty_when_none_provided(self, calculator_class, clear):
        """Test that additional_kwargs is empty dict when no kwargs provided."""
        calc = calculator_class(create_mock_model())
        assert calc.additional_kwargs == {}

    def test_additional_kwargs_via_factory(self, calculator_class, clear):
        """Test that kwargs passed through factory are accessible."""
        factory = SimpleCalculatorFactory({"test": calculator_class})
        calc = factory.create(
            "test",
            create_mock_model(),
            option1="value1",
            option2=123
        )
        assert calc.additional_kwargs["option1"] == "value1"
        assert calc.additional_kwargs["option2"] == 123


class TestTryRegisterCalculator:
    """Tests for the _try_register_calculator method."""

    @pytest.fixture
    def calculator_class(self):
        """Simple calculator class for testing."""

        class TestCalc(CalculatorBase):
            name = "test"

            def calculate(self, x: np.ndarray) -> np.ndarray:
                return x

        return TestCalc

    @pytest.fixture
    def concrete_factory(self, calculator_class):
        """Create a concrete factory for testing."""
        calc_class = calculator_class

        class TestFactory(CalculatorFactoryBase):
            def __init__(self):
                super().__init__()

            def create(self, calculator_name, model, instrumental_parameters=None, **kwargs):
                if calculator_name not in self._available_calculators:
                    raise ValueError(f"Unknown calculator: {calculator_name}")
                return self._available_calculators[calculator_name](model, instrumental_parameters, **kwargs)

        return TestFactory

    def test_try_register_existing_package_succeeds(self, concrete_factory):
        """Test that registering from an existing package works."""
        factory = concrete_factory()
        # json is always available in Python
        result = factory._try_register_calculator("json_encoder", "json", "JSONEncoder")
        assert result is True
        assert "json_encoder" in factory.available_calculators

    def test_try_register_nonexistent_package_returns_false(self, concrete_factory):
        """Test that registering from non-existent package returns False."""
        factory = concrete_factory()
        result = factory._try_register_calculator(
            "nonexistent", "this_package_does_not_exist_12345", "SomeClass"
        )
        assert result is False
        assert "nonexistent" not in factory.available_calculators

    def test_try_register_nonexistent_class_returns_false(self, concrete_factory):
        """Test that registering non-existent class returns False."""
        factory = concrete_factory()
        result = factory._try_register_calculator(
            "bad_class", "json", "ThisClassDoesNotExist12345"
        )
        assert result is False
        assert "bad_class" not in factory.available_calculators

    def test_try_register_multiple_calculators(self, concrete_factory):
        """Test registering multiple calculators with mixed success."""
        factory = concrete_factory()

        # This should succeed
        result1 = factory._try_register_calculator("encoder", "json", "JSONEncoder")
        # This should fail
        result2 = factory._try_register_calculator("fake", "nonexistent_pkg", "FakeClass")
        # This should succeed
        result3 = factory._try_register_calculator("decoder", "json", "JSONDecoder")

        assert result1 is True
        assert result2 is False
        assert result3 is True

        assert "encoder" in factory.available_calculators
        assert "fake" not in factory.available_calculators
        assert "decoder" in factory.available_calculators
        assert len(factory.available_calculators) == 2

    def test_try_register_does_not_affect_other_instances(self, concrete_factory):
        """Test that _try_register on one instance doesn't affect others."""
        factory1 = concrete_factory()
        factory2 = concrete_factory()

        factory1._try_register_calculator("encoder", "json", "JSONEncoder")

        assert "encoder" in factory1.available_calculators
        assert "encoder" not in factory2.available_calculators

    def test_try_register_in_subclass_init(self, calculator_class):
        """Test using _try_register_calculator in subclass __init__."""
        calc_class = calculator_class

        class DynamicFactory(CalculatorFactoryBase):
            def __init__(self):
                super().__init__()
                # Register one that exists
                self._try_register_calculator("encoder", "json", "JSONEncoder")
                # Register one that doesn't exist - should be silently skipped
                self._try_register_calculator("fake", "no_such_package", "NoClass")

            def create(self, calculator_name, model, instrumental_parameters=None, **kwargs):
                if calculator_name not in self._available_calculators:
                    raise ValueError(f"Unknown calculator: {calculator_name}")
                return self._available_calculators[calculator_name](model, instrumental_parameters, **kwargs)

        factory = DynamicFactory()
        assert "encoder" in factory.available_calculators
        assert "fake" not in factory.available_calculators
