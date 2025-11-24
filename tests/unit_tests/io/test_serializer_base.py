#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

from easyscience.io import SerializerBase
from easyscience import Parameter
from easyscience.base_classes import NewBase
import pytest
import numpy as np
from unittest.mock import MagicMock

#class ForTesting(NewBase):


class TestSerializerBase:
    def test_import_class(self):
        # When Then
        cls = SerializerBase._import_class(module_name="easyscience", class_name="Parameter")
        # Expect
        assert cls is Parameter

    def test_import_class_missing_module(self):
        # When Then Expect
        with pytest.raises(ImportError):
            SerializerBase._import_class(module_name="non_existent_module", class_name="Parameter")

    def test_import_class_missing_class(self):
        # When Then Expect
        with pytest.raises(ValueError):
            SerializerBase._import_class(module_name="easyscience", class_name="NonExistentClass")

    @pytest.mark.parametrize("dict, expected", [
        ({  '@module': 'easyscience',
            '@class': 'Parameter',
            'name': 'param1',
            'value': 10.0
        }, 
        True
        ),
        ({
            '@module': 'numpy',
            '@class': 'array',
            'unique_name': 'unique1',
            'display_name': 'Display 1'
        }, False
        )], ids=['valid_easyscience_dict', 'invalid_numpy_dict'])
    def test_is_serialized_easyscience_object_false(self, dict, expected):
        # When Then
        result = SerializerBase._is_serialized_easyscience_object(dict)
        # Expect
        assert result is expected

    def test_deserialize_value_non_easyscience(self):
        # When
        serialized_dict = {
            '@module': 'numpy', 
            '@class': 'array', 
            'dtype': 'int64', 
            'data': [0, 1]
            }
        # Then
        obj = SerializerBase._deserialize_value(serialized_dict)
        # Expect
        assert isinstance(obj,  np.ndarray)
        assert obj.dtype == np.int64

    def test_deserialize_value_easyscience_uses_from_dict(self, monkeypatch):
        # When
        serialized_dict = {
            '@module': 'easyscience.base_classes', 
            '@class': 'NewBase', 
            'display_name': 'test', 
            }
        monkeypatch.setattr(NewBase, 'from_dict', MagicMock())
        # Then
        obj = SerializerBase._deserialize_value(serialized_dict)
        # Expect
        NewBase.from_dict.assert_called_once_with(serialized_dict)

    def test_deserialize_value_easyscience_no_from_dict(self, monkeypatch):
        # When
        serialized_dict = {
            '@module': 'easyscience.base_classes', 
            '@class': 'NewBase', 
            'display_name': 'test', 
            }
        monkeypatch.delattr(NewBase, 'from_dict')
        monkeypatch.setattr(SerializerBase, '_convert_from_dict', MagicMock())
        # Then
        obj = SerializerBase._deserialize_value(serialized_dict)
        # Expect
        SerializerBase._convert_from_dict.assert_called_once_with(serialized_dict)

    def test_deserialize_value_easyscience_import_error(self, monkeypatch):
        # When
        serialized_dict = {
            '@module': 'easyscience.base_classes', 
            '@class': 'NewBase', 
            'display_name': 'test', 
            }
        monkeypatch.setattr(SerializerBase, '_import_class', MagicMock(side_effect=ImportError()))
        monkeypatch.setattr(SerializerBase, '_convert_from_dict', MagicMock())
        # Then
        obj = SerializerBase._deserialize_value(serialized_dict)
        # Expect
        SerializerBase._convert_from_dict.assert_called_once_with(serialized_dict)

    def test_deserialize_dict(self, monkeypatch):
        # When
        serialized_dict = {
            '@module': 'easyscience', 
            '@class': 'ParameterContainer',
            'param1': {
                '@module': 'easyscience',
                '@class': 'Parameter',
                'name': 'param1',
                'value': 10.0
            },
            'array1': {
                '@module': 'numpy', 
                '@class': 'array', 
                'dtype': 'int64', 
                'data': [0, 1]
            }
        }
        monkeypatch.setattr(SerializerBase, '_deserialize_value', MagicMock(side_effect=[
            Parameter(name='param1', value=10.0),
            np.array([0, 1], dtype=np.int64)
        ]))
        # Then
        result = SerializerBase.deserialize_dict(serialized_dict)
        # Expect
        SerializerBase._deserialize_value.assert_any_call(serialized_dict['param1'])
        SerializerBase._deserialize_value.assert_any_call(serialized_dict['array1'])
        assert isinstance(result['param1'], Parameter)
        assert isinstance(result['array1'], np.ndarray)
        assert result['array1'].dtype == np.int64