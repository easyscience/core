#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

from typing import Any
from typing import cast

import pytest

from easyscience import global_object
from easyscience.base_classes import CollectionBaseEasyList as CollectionBase
from easyscience.base_classes import ModelBase
from easyscience.variable import Parameter


def make_parameter(name: str, value: Any, **kwargs: Any) -> Parameter:
    return Parameter(name, cast(Any, value), **kwargs)


class DummyModel(ModelBase):
    def __init__(
        self,
        name: str,
        value: Any,
        unique_name: str | None = None,
        display_name: str | None = None,
    ):
        if display_name is None:
            display_name = name
        super().__init__(unique_name=unique_name, display_name=display_name)
        self._name = name
        self._value = (
            value if isinstance(value, Parameter) else make_parameter(f'{name}_value', value)
        )

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        self._name = new_name
        self.display_name = new_name

    @property
    def value(self) -> Parameter:
        return self._value

    @value.setter
    def value(self, new_value: float) -> None:
        self._value.value = new_value


@pytest.fixture(autouse=True)
def clear():
    global_object.map._clear()


def test_collection_base_getitem_supports_unique_name_and_name_fallback():
    m1 = DummyModel('dup', make_parameter('p1', 1.0), unique_name='m1')
    m2 = DummyModel('dup', make_parameter('p2', 2.0), unique_name='m2')

    collection = CollectionBase('test', m1, m2)

    assert collection['m1'] is m1
    same_name = collection['dup']
    assert isinstance(same_name, CollectionBase)
    assert len(same_name) == 2
    assert list(same_name) == [m1, m2]


def test_collection_base_get_all_variables_recurses_into_models():
    p1 = make_parameter('p1', 1.0)
    p2 = make_parameter('p2', 2.0)
    model1 = DummyModel('m1', p1)
    model2 = DummyModel('m2', p2)

    collection = CollectionBase('test', model1, model2)

    variables = collection.get_all_variables()

    assert p1 in variables
    assert p2 in variables


def test_collection_base_get_parameters_recurses_into_nested_objects():
    nested = CollectionBase(
        'nested',
        DummyModel('m1', make_parameter('p1', 1.0)),
        DummyModel('m2', make_parameter('p2', 2.0, fixed=True)),
    )
    model = DummyModel('model', make_parameter('p3', 3.0))
    collection = CollectionBase('test', nested, model)

    parameters = collection.get_all_parameters()
    free_parameters = collection.get_free_parameters()

    assert [parameter.name for parameter in parameters] == ['p1', 'p2', 'p3']
    assert [parameter.name for parameter in free_parameters] == ['p1', 'p3']


def test_collection_base_rejects_non_model_items():
    with pytest.raises(AttributeError, match='model objects'):
        CollectionBase('test', make_parameter('p1', 1.0))


def test_collection_base_rejects_basedbase_objects():
    with pytest.raises(AttributeError, match='model objects'):
        from easyscience import ObjBase

        CollectionBase('test', ObjBase('legacy', p=make_parameter('p1', 1.0)))


def test_collection_base_accepts_nested_collections():
    inner = CollectionBase('inner', DummyModel('m', make_parameter('p', 1.0)))
    outer = CollectionBase('outer', inner)

    assert len(outer) == 1
    assert outer[0] is inner


def test_collection_base_to_dict_round_trip_preserves_name_and_data():
    m1 = DummyModel('m1', make_parameter('p1', 1.0))
    m2 = DummyModel('m2', make_parameter('p2', 2.0))
    collection = CollectionBase('test', m1, m2)

    encoded = collection.to_dict()
    decoded = CollectionBase.from_dict(encoded)

    assert decoded.name == 'test'
    assert [item.name for item in decoded] == ['m1', 'm2']


def test_collection_base_sort_accepts_key():
    m1 = DummyModel('m1', make_parameter('p1', 3.0))
    m2 = DummyModel('m2', make_parameter('p2', 1.0))
    m3 = DummyModel('m3', make_parameter('p3', 2.0))
    collection = CollectionBase('test', m1, m2, m3)

    collection.sort(key=lambda item: item.value.value)

    assert [item.name for item in collection] == ['m2', 'm3', 'm1']


def test_collection_base_isinstance_model_base():
    collection = CollectionBase('test')
    assert isinstance(collection, ModelBase)
