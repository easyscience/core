# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from copy import deepcopy
from typing import Type

import pytest

from easyscience import DescriptorNumber
from easyscience import Parameter
from easyscience import global_object
from easyscience.io.serializer_dict import SerializerDict

from .test_serializer_component import check_dict
from .test_serializer_component import dp_param_dict
from .test_serializer_component import skip_dict


def recursive_remove(d, remove_keys: list) -> dict:
    """
    Remove keys from a dictionary.
    """
    if not isinstance(remove_keys, list):
        remove_keys = [remove_keys]
    if isinstance(d, dict):
        dd = {}
        for k in d.keys():
            if k not in remove_keys:
                dd[k] = recursive_remove(d[k], remove_keys)
        return dd
    else:
        return d


########################################################################################################################
# TESTING ENCODING
########################################################################################################################
@pytest.mark.parametrize(**skip_dict)
@pytest.mark.parametrize(**dp_param_dict)
def test_variable_SerializerDict(dp_kwargs: dict, dp_cls: Type[DescriptorNumber], skip):
    data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != '@'}

    obj = dp_cls(**data_dict)

    dp_kwargs = deepcopy(dp_kwargs)

    if isinstance(skip, str):
        del dp_kwargs[skip]

    if not isinstance(skip, list):
        skip = [skip]

    enc = SerializerDict().encode(obj, skip=skip)

    expected_keys = set(dp_kwargs.keys())
    obtained_keys = set(enc.keys())

    dif = expected_keys.difference(obtained_keys)

    assert len(dif) == 0

    check_dict(dp_kwargs, enc)


########################################################################################################################
# TESTING DECODING
########################################################################################################################
@pytest.mark.parametrize(**dp_param_dict)
def test_variable_SerializerDict_decode(dp_kwargs: dict, dp_cls: Type[DescriptorNumber]):
    data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != '@'}

    obj = dp_cls(**data_dict)

    enc = SerializerDict().encode(obj)
    global_object.map._clear()
    dec = SerializerDict.decode(enc)

    for k in data_dict.keys():
        if hasattr(obj, k) and hasattr(dec, k):
            assert getattr(obj, k) == getattr(dec, k)
        else:
            raise AttributeError(f'{k} not found in decoded object')


@pytest.mark.parametrize(**dp_param_dict)
def test_variable_SerializerDict_from_dict(dp_kwargs: dict, dp_cls: Type[DescriptorNumber]):
    data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != '@'}

    obj = dp_cls(**data_dict)

    enc = SerializerDict().encode(obj)
    global_object.map._clear()
    dec = dp_cls.from_dict(enc)

    for k in data_dict.keys():
        if hasattr(obj, k) and hasattr(dec, k):
            assert getattr(obj, k) == getattr(dec, k)
        else:
            raise AttributeError(f'{k} not found in decoded object')


def test_group_encode():
    d0 = DescriptorNumber(0, display_name='a')
    d1 = DescriptorNumber(1, display_name='b')

    from easyscience.base_classes import EasyList

    b = EasyList(d0, d1)
    d = b.to_dict()
    assert isinstance(d['data'], list)


def test_group_encode2():
    p0 = Parameter(0, display_name='a')
    p1 = Parameter(1, display_name='b')

    from easy_test_models import CoefficientModel

    b = CoefficientModel(display_name='outer', coefficients=[p0, p1])
    d = b.to_dict()
    assert isinstance(d['coefficients'], dict)
    assert len(d['coefficients']['data']) == 2


class TestSerializerDictDecodeDispatch:
    """``SerializerDict.decode`` routes by what the dict describes."""

    def test_new_base_uses_from_dict(self):
        from easy_test_models import CoefficientModel

        global_object.map._clear()

        model = CoefficientModel(display_name='model', coefficients=[1.0, 2.0])

        new_model = SerializerDict.decode(model.to_dict())

        assert isinstance(new_model, CoefficientModel)
        assert [c.value for c in new_model.coefficients] == [1.0, 2.0]

    @pytest.mark.parametrize(
        'value',
        [None, 1.5, 'text', [1, 2], {'plain': 'dict'}],
        ids=['none', 'float', 'str', 'list', 'plain_dict'],
    )
    def test_non_easyscience_values_pass_through(self, value):
        assert SerializerDict.decode(value) == value

    def test_numpy_array_uses_generic_path(self):
        import numpy as np

        encoded = {'@module': 'numpy', '@class': 'array', 'dtype': 'float64', 'data': [1.0, 2.0]}

        result = SerializerDict.decode(encoded)

        assert isinstance(result, np.ndarray)
        assert np.array_equal(result, [1.0, 2.0])

    def test_unknown_easyscience_class_falls_back(self):
        """A class missing from its module is left to the generic decoder."""
        encoded = {'@module': 'easyscience.variable', '@class': 'NoSuchClass', 'x': 1}

        assert SerializerDict.decode(encoded) == encoded

    def test_easyscience_non_new_base_uses_generic_path(self):
        """EasyScience classes outside NewBase are rebuilt from their kwargs."""
        from easyscience.fitting.calculators.interface_factory import ItemContainer

        encoded = {
            '@module': 'easyscience.fitting.calculators.interface_factory',
            '@class': 'ItemContainer',
            'link_name': 'link',
            'name_conversion': {'a': 'b'},
            'getter_fn': None,
            'setter_fn': None,
        }

        result = SerializerDict.decode(encoded)

        assert isinstance(result, ItemContainer)
        assert result.link_name == 'link'
