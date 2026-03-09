#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

import pytest

from easyscience import DescriptorNumber
from easyscience import ObjBase
from easyscience import Parameter
from easyscience import global_object
from easyscience.base_classes import CollectionBase


@pytest.fixture(autouse=True)
def clear():
    global_object.map._clear()


def test_collection_base_legacy_constructor_supports_named_items():
    p1 = Parameter('p1', 1.0)
    p2 = Parameter('p2', 2.0)

    collection = CollectionBase('test', first=p1, second=p2)

    assert collection.name == 'test'
    assert len(collection) == 2
    assert collection[0] is p1
    assert collection[1] is p2


def test_collection_base_getitem_supports_unique_name_and_name_fallback():
    p1 = Parameter('dup', 1.0, unique_name='p1')
    p2 = Parameter('dup', 2.0, unique_name='p2')

    collection = CollectionBase('test', p1, p2)

    assert collection['p1'] is p1
    same_name = collection['dup']
    assert isinstance(same_name, CollectionBase)
    assert len(same_name) == 2
    assert list(same_name) == [p1, p2]


def test_collection_base_get_all_variables_includes_direct_leaf_items():
    descriptor = DescriptorNumber('d1', 1.0)
    parameter = Parameter('p1', 2.0)

    collection = CollectionBase('test', descriptor, parameter)

    variables = collection.get_all_variables()

    assert variables == [descriptor, parameter]


def test_collection_base_get_parameters_recurses_into_nested_objects():
    nested = ObjBase('nested', p1=Parameter('p1', 1.0), p2=Parameter('p2', 2.0, fixed=True))
    collection = CollectionBase('test', nested, Parameter('p3', 3.0))

    parameters = collection.get_parameters()
    free_parameters = collection.get_fit_parameters()

    assert [parameter.name for parameter in parameters] == ['p1', 'p2', 'p3']
    assert [parameter.name for parameter in free_parameters] == ['p1', 'p3']


def test_collection_base_supports_numeric_item_assignment():
    parameter = Parameter('p1', 1.0)
    collection = CollectionBase('test', parameter)

    collection[0] = 4.0

    assert collection[0].value == 4.0


def test_collection_base_to_dict_round_trip_preserves_name_and_data():
    p1 = Parameter('p1', 1.0)
    p2 = Parameter('p2', 2.0)
    collection = CollectionBase('test', p1, p2)

    encoded = collection.to_dict()
    decoded = CollectionBase.from_dict(encoded)

    assert decoded.name == 'test'
    assert [item.name for item in decoded] == ['p1', 'p2']
    assert [item.value for item in decoded] == [1.0, 2.0]


def test_collection_base_sort_accepts_mapping_alias():
    collection = CollectionBase('test', Parameter('p1', 3.0), Parameter('p2', 1.0), Parameter('p3', 2.0))

    collection.sort(mapping=lambda item: item.value)

    assert [item.value for item in collection] == [1.0, 2.0, 3.0]