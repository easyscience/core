#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

import pytest
from easyscience import global_object
from easyscience.base_classes import ModelBase
from easyscience import Parameter

class MockModelBase(ModelBase):
    def __init__(self, display_name=None, unique_name=None, temperature=0):
        super().__init__(display_name=display_name, unique_name=unique_name)
        self._temperature = Parameter(name="temperature", value=temperature)

    @property
    def temperature(self):
        return self._temperature
    
    @temperature.setter
    def temperature(self, value):
        self._temperature.value = value

class TestModelBase:

    @pytest.fixture
    def clear(self):
        # Clear the global object map before each test
        global_object.map._clear()

    def test_model_base_inheritance(self, clear):
        # When Then
        obj = ModelBase()
        # Expect
        assert isinstance(obj, ModelBase)
        assert isinstance(obj, NewBase)