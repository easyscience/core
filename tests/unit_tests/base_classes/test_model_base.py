#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

import pytest
from easyscience import global_object
from easyscience.base_classes import ModelBase
from easyscience import Parameter
from easyscience import DescriptorNumber
from easyscience.variable import DescriptorStr

class MockModelComponent(ModelBase):
    def __init__(self, display_name=None, unique_name=None, temperature=0, room_temperature=22):
        super().__init__(display_name=display_name, unique_name=unique_name)
        self._temperature = Parameter(name="temperature", value=temperature)
        self._room_temperature = DescriptorNumber(name="room_temperature", value=room_temperature)
        self._status = DescriptorStr(name="status", value="OK")

    @property
    def temperature(self):
        return self._temperature
    
    @temperature.setter
    def temperature(self, value):
        self._temperature.value = value

    @property
    def room_temperature(self):
        return self._room_temperature
    
    @room_temperature.setter
    def room_temperature(self, value):
        self._room_temperature.value = value

    @property
    def status(self):
        return self._status
    
    @status.setter
    def status(self, value):
        self._status.value = value

class MockModelFull(ModelBase):
    def __init__(self, display_name=None, unique_name=None, pressure=0):
        super().__init__(display_name=display_name, unique_name=unique_name)
        self._pressure = Parameter(name="pressure", value=pressure)
        self._component = MockModelComponent(temperature=25, room_temperature=22)

    @property
    def pressure(self):
        return self._pressure
    
    @pressure.setter
    def pressure(self, value):
        self._pressure.value = value

    @property
    def component(self):
        return self._component

class TestModelBase:

    def test_init(self):
        # When Then
        model = ModelBase(unique_name="test_model", display_name="Test Model")
        # Expect
        assert model.unique_name == "test_model"
        assert model.display_name == "Test Model"

    # def test_get_all_parameters_flat(self):
    #     # When
    #     model = MockModelComponent(temperature=25, room_temperature=22)
    #     # Then
    #     params = model.get_all_parameters()
    #     # Expect
    #     assert len(params) == 2
    #     assert any(isinstance(p, Parameter) and p.name == "temperature" for p in params)
    #     assert any(type(p) is DescriptorNumber and p.name == "room_temperature" for p in params)