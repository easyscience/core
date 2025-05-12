__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

from copy import deepcopy
from typing import Type

import pytest

from easyscience.Utils.io.dict import DataDictSerializer
from easyscience.Utils.io.dict import DictSerializer
from easyscience.Objects.variable import DescriptorNumber
from easyscience.Objects.ObjectClasses import BaseObj

from .test_core import check_dict
from .test_core import dp_param_dict
from .test_core import skip_dict
from easyscience import global_object


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
def test_variable_DictSerializer(dp_kwargs: dict, dp_cls: Type[DescriptorNumber], skip):
    data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != "@"}

    obj = dp_cls(**data_dict)

    dp_kwargs = deepcopy(dp_kwargs)

    if isinstance(skip, str):
        del dp_kwargs[skip]

    if not isinstance(skip, list):
        skip = [skip]

    enc = obj.encode(skip=skip, encoder=DictSerializer)

    expected_keys = set(dp_kwargs.keys())
    obtained_keys = set(enc.keys())

    dif = expected_keys.difference(obtained_keys)

    assert len(dif) == 0

    check_dict(dp_kwargs, enc)


@pytest.mark.parametrize(**skip_dict)
@pytest.mark.parametrize(**dp_param_dict)
def test_variable_DataDictSerializer(dp_kwargs: dict, dp_cls: Type[DescriptorNumber], skip):
    data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != "@"}

    obj = dp_cls(**data_dict)

    if isinstance(skip, str):
        del data_dict[skip]

    if not isinstance(skip, list):
        skip = [skip]

    enc_d = obj.encode(skip=skip, encoder=DataDictSerializer)

    expected_keys = set(data_dict.keys())
    obtained_keys = set(enc_d.keys())

    dif = expected_keys.difference(obtained_keys)

    assert len(dif) == 0

    check_dict(data_dict, enc_d)


@pytest.mark.parametrize(
    "encoder", [None, DataDictSerializer], ids=["Default", "DataDictSerializer"]
)
@pytest.mark.parametrize(**skip_dict)
@pytest.mark.parametrize(**dp_param_dict)
def test_variable_encode_data(dp_kwargs: dict, dp_cls: Type[DescriptorNumber], skip, encoder):
    data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != "@"}

    obj = dp_cls(**data_dict)

    if isinstance(skip, str):
        del data_dict[skip]

    if not isinstance(skip, list):
        skip = [skip]

    enc_d = obj.encode_data(skip=skip, encoder=encoder)

    expected_keys = set(data_dict.keys())
    obtained_keys = set(enc_d.keys())

    dif = expected_keys.difference(obtained_keys)

    assert len(dif) == 0

    check_dict(data_dict, enc_d)


########################################################################################################################
# TESTING DECODING
########################################################################################################################
@pytest.mark.parametrize(**dp_param_dict)
def test_variable_DictSerializer_decode(dp_kwargs: dict, dp_cls: Type[DescriptorNumber]):
    data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != "@"}

    obj = dp_cls(**data_dict)

    enc = obj.encode(encoder=DictSerializer)
    global_object.map._clear()
    dec = dp_cls.decode(enc, decoder=DictSerializer)

    for k in data_dict.keys():
        if hasattr(obj, k) and hasattr(dec, k):
            assert getattr(obj, k) == getattr(dec, k)
        else:
            raise AttributeError(f"{k} not found in decoded object")


@pytest.mark.parametrize(**dp_param_dict)
def test_variable_DictSerializer_from_dict(dp_kwargs: dict, dp_cls: Type[DescriptorNumber]):
    data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != "@"}

    obj = dp_cls(**data_dict)

    enc = obj.encode(encoder=DictSerializer)
    global_object.map._clear()
    dec = dp_cls.from_dict(enc)

    for k in data_dict.keys():
        if hasattr(obj, k) and hasattr(dec, k):
            assert getattr(obj, k) == getattr(dec, k)
        else:
            raise AttributeError(f"{k} not found in decoded object")


@pytest.mark.parametrize(**dp_param_dict)
def test_variable_DataDictSerializer_decode(dp_kwargs: dict, dp_cls: Type[DescriptorNumber]):
    data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != "@"}

    obj = dp_cls(**data_dict)

    enc = obj.encode(encoder=DataDictSerializer)
    with pytest.raises(NotImplementedError):
        dec = obj.decode(enc, decoder=DataDictSerializer)


def test_group_encode():
    d0 = DescriptorNumber("a", 0)
    d1 = DescriptorNumber("b", 1)

    from easyscience.Objects.Groups import BaseCollection

    b = BaseCollection("test", d0, d1)
    d = b.as_dict()
    assert isinstance(d["data"], list)


def test_group_encode2():
    d0 = DescriptorNumber("a", 0)
    d1 = DescriptorNumber("b", 1)

    from easyscience.Objects.Groups import BaseCollection

    b = BaseObj("outer", b=BaseCollection("test", d0, d1))
    d = b.as_dict()
    assert isinstance(d["b"], dict)