
#  SPDX-FileCopyrightText: 2023 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2023 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

import pytest
import copy

import easyscience
from easyscience.base_classes import CollectionBase
from easyscience import ObjBase
from easyscience import DescriptorNumber
from easyscience import Parameter
from easyscience import global_object

test_dict = {
    "@module": "easyscience.base_classes",
    "@class": "CollectionBase",
    "@version": easyscience.__version__,
    "unique_name": "testing",
    "data": [
        {
            "@module": DescriptorNumber.__module__,
            "@class": DescriptorNumber.__name__,
            "@version": easyscience.__version__,
            "value": 1.0,
            "unit": "dimensionless",
            "variance": None,
            "unique_name": "DescriptorNumber_0",
            "description": "",
            "url": "",
            "display_name": "par1",
        }
    ],
}


class Alpha(CollectionBase):
    pass


class_constructors = [CollectionBase, Alpha]


@pytest.fixture
def setup_pars():
    d = {
        "par1": Parameter(0.2, fixed=True),
        "des1": DescriptorNumber(0.1),
        "par2": Parameter(1),
        "des2": DescriptorNumber(2),
        "par3": Parameter(3),
    }
    return d


@pytest.mark.parametrize("cls", class_constructors)
def test_CollectionBase_from_base(cls, setup_pars):
    coll = cls(**setup_pars)

    assert len(coll) == 5
    assert coll.user_data == {}

    for item, key in zip(coll, setup_pars.keys()):
        assert item.unique_name == setup_pars[key].unique_name
        assert item.value == setup_pars[key].value


@pytest.mark.parametrize("cls", class_constructors)
@pytest.mark.parametrize("value", range(1, 11))
def test_CollectionBase_from_ObjBase(cls, setup_pars: dict, value: int):
    objs = {}
    global_object.map._clear()
    prefix = "obj"
    for idx in range(value):
        objs[prefix + str(idx)] = ObjBase(unique_name=prefix + str(idx), **setup_pars)

    coll = cls(**objs)

    assert len(coll) == value
    assert coll.user_data == {}

    idx = 0
    for item, key in zip(coll, objs.keys()):
        assert item.unique_name == prefix + str(idx)
        assert isinstance(item, objs[key].__class__)
        idx += 1


@pytest.mark.parametrize("cls", class_constructors)
@pytest.mark.parametrize("value", ("abc", False, (), []))
def test_CollectionBase_create_fail(cls, setup_pars, value):
    setup_pars["to_fail"] = value

    with pytest.raises(AttributeError):
        coll = cls(**setup_pars)


@pytest.mark.parametrize("cls", class_constructors)
@pytest.mark.parametrize("key", ("user_data", "_kwargs", "interface"))
def test_CollectionBase_create_fail2(cls, setup_pars, key):
    setup_pars[key] = DescriptorNumber(0)

    with pytest.raises(AttributeError):
        coll = cls(**setup_pars)


@pytest.mark.parametrize("cls", class_constructors)
def test_CollectionBase_append_base(cls, setup_pars):

    new_item_name = "boo"
    new_item_value = 100
    new_item = Parameter(value=new_item_value, display_name=new_item_name)

    coll = cls(**setup_pars)
    n_before = len(coll)

    coll.append(new_item)
    assert len(coll) == n_before + 1
    assert coll[-1].display_name == new_item_name
    assert coll[-1].value == new_item_value


@pytest.mark.parametrize("cls", class_constructors)
@pytest.mark.parametrize("value", ("abc", False, (), []))
def test_CollectionBase_append_fail(cls, setup_pars, value):

    coll = cls(**setup_pars)
    with pytest.raises(AttributeError):
        coll.append(value)


@pytest.mark.parametrize("cls", class_constructors)
@pytest.mark.parametrize("value", (0, 1, 3, "par1", "des1"))
def test_CollectionBase_getItem(cls, setup_pars, value):

    coll = cls(**setup_pars)

    get_item = coll[value]
    if isinstance(value, str):
        key = value
    else:
        key = list(setup_pars.keys())[value]
    assert get_item.unique_name == setup_pars[key].unique_name


@pytest.mark.parametrize("cls", class_constructors)
@pytest.mark.parametrize("value", (False, [], (), 100, 100.4))
def test_CollectionBase_getItem_type_fail(cls, setup_pars, value):

    coll = cls(**setup_pars)

    with pytest.raises((IndexError, TypeError)):
        get_item = coll[value]


@pytest.mark.parametrize("cls", class_constructors)
def test_CollectionBase_getItem_slice(cls, setup_pars):

    coll = cls(**setup_pars)

    get_item = coll[0:2]
    assert len(get_item) == 2


@pytest.mark.parametrize("cls", class_constructors)
@pytest.mark.parametrize("value", (0, 1, 3))
def test_CollectionBase_setItem(cls, setup_pars, value):

    coll = cls(**setup_pars)
    n_coll = len(coll)
    name_coll_idx = coll[value].unique_name

    new_item_value = 100

    coll[value] = new_item_value

    assert len(coll) == n_coll
    assert coll[value].unique_name == name_coll_idx
    assert coll[value].value == new_item_value


@pytest.mark.parametrize("cls", class_constructors)
@pytest.mark.parametrize("value", ("abc", (), []))
def test_CollectionBase_setItem_fail(cls, setup_pars, value):

    coll = cls(**setup_pars)

    with pytest.raises(NotImplementedError):
        for idx in range(len(coll)):
            coll[idx] = value


@pytest.mark.parametrize("cls", class_constructors)
@pytest.mark.parametrize("value", (0, 1, 3))
def test_CollectionBase_delItem(cls, setup_pars, value):

    coll = cls(**setup_pars)
    n_coll = len(coll)
    # On del we should shift left
    name_coll_idx = coll[value].unique_name
    name_coll_idxp = coll[value + 1].unique_name

    del coll[value]

    assert len(coll) == n_coll - 1
    assert coll[value].unique_name == name_coll_idxp
    assert name_coll_idx not in [col.unique_name for col in coll]


@pytest.mark.parametrize("cls", class_constructors)
@pytest.mark.parametrize("value", (0, 1, 3))
def test_CollectionBase_len(cls, setup_pars, value):

    keys = list(setup_pars.keys())
    keys = keys[0 : (value + 1)]

    coll = cls(**{key: setup_pars[key] for key in keys})
    assert len(coll) == (value + 1)


@pytest.mark.parametrize("cls", class_constructors)
def test_CollectionBase_get_parameters(cls, setup_pars):
    obj = cls(**setup_pars)
    pars = obj.get_parameters()
    assert len(pars) == 3


@pytest.mark.parametrize("cls", class_constructors)
def test_CollectionBase_get_parameters_nested(cls, setup_pars):
    obj = ObjBase(**setup_pars)

    obj2 = cls(obj=obj, **setup_pars)

    pars = obj2.get_parameters()
    assert len(pars) == 6


@pytest.mark.parametrize("cls", class_constructors)
def test_CollectionBase_get_fit_parameters(cls, setup_pars):
    obj = cls(**setup_pars)
    pars = obj.get_fit_parameters()
    assert len(pars) == 2


@pytest.mark.parametrize("cls", class_constructors)
def test_CollectionBase_get_fit_parameters_nested(cls, setup_pars):
    obj = ObjBase(**setup_pars)

    obj2 = cls(obj=obj, **setup_pars)

    pars = obj2.get_fit_parameters()
    assert len(pars) == 4


@pytest.mark.parametrize("cls", class_constructors)
def test_CollectionBase_dir(cls):
    kwargs = {"p1": DescriptorNumber(1)}
    obj = cls(**kwargs)
    d = set(dir(obj))

    expected = {
        "user_data",
        "reverse",
        "constraints",
        "get_fit_parameters",
        "append",
        "unique_name",
        "index",
        "as_dict",
        "clear",
        "extend",
        "encode",
        "remove",
        "interface",
        "from_dict",
        "switch_interface",
        "get_parameters",
        "insert",
        "data",
        "pop",
        "count",
        "generate_bindings",
        "decode",
        "sort",
    }
    assert not d.difference(expected)


@pytest.mark.parametrize("cls", class_constructors)
def test_CollectionBase_as_dict(cls):
    kwargs = {"p1": DescriptorNumber(1, display_name="par1")}
    obj = cls(**kwargs)
    d = obj.as_dict()

    def check_dict(dict_1: dict, dict_2: dict):
        keys_1 = list(dict_1.keys())
        keys_2 = list(dict_2.keys())
        if "unique_name" in keys_1:
            del keys_1[keys_1.index("unique_name")]
        if "unique_name" in keys_2:
            del keys_2[keys_2.index("unique_name")]

        assert not set(keys_1).difference(set(keys_2))

        def testit(item1, item2):
            if isinstance(item1, dict) and isinstance(item2, dict):
                check_dict(item1, item2)
            elif isinstance(item1, list) and isinstance(item2, list):
                for v1, v2 in zip(item1, item2):
                    testit(v1, v2)
            else:
                if isinstance(item1, str) and isinstance(item2, str):
                    assert item1 == item2
                elif isinstance(item1, float) and isinstance(item2, float):
                    assert item1 == item2
                else:
                    assert item1 is item2

        keys_1 = list(keys_1)
        keys_1.sort()
        keys_2 = list(keys_2)
        keys_2.sort()

        for k1, k2 in zip(keys_1, keys_2):
            if k1[0] == "@":
                continue
            testit(dict_1[k1], dict_2[k2])

    check_dict(d, test_dict)


@pytest.mark.parametrize("cls", class_constructors)
def test_CollectionBase_from_dict(cls):
    kwargs = {"p1": DescriptorNumber(1, display_name="par1")}
    new_dict = copy.deepcopy(test_dict)
    del new_dict["data"][0]["unique_name"]
    expected = cls.from_dict(new_dict)
    ref = cls(**kwargs)

    assert len(ref) == len(expected)
    for item1, item2 in zip(ref, expected):
        assert item1.display_name == item2.display_name
        assert item1.value == item2.value


@pytest.mark.parametrize("cls", class_constructors)
def test_CollectionBase_repr(cls):

    p1 = Parameter(1)
    obj = cls(p1, unique_name="test")
    test_str = str(obj)
    ref_str = f"{cls.__name__} `test` of length 1"
    assert test_str == ref_str


@pytest.mark.parametrize("cls", class_constructors)
def test_CollectionBase_iterator(cls):
    p1 = Parameter(1)
    p2 = Parameter(2)
    p3 = Parameter(3)
    p4 = Parameter(4)

    l_object = [p1, p2, p3, p4]

    obj = cls(*l_object)

    for index, item in enumerate(obj):
        assert item == l_object[index]


@pytest.mark.parametrize("cls", class_constructors)
def test_CollectionBase_iterator_dict(cls):
    p1 = Parameter(1)
    p2 = Parameter(2)
    p3 = Parameter(3)
    p4 = Parameter(4)

    l_object = [p1, p2, p3, p4]

    obj = cls(*l_object)
    d = obj.as_dict()
    global_object.map._clear()
    obj2 = cls.from_dict(d)

    for index, item in enumerate(obj2):
        assert item.value == l_object[index].value

@pytest.mark.parametrize("cls", class_constructors)
def test_CollectionBase_set_index(cls):
    p1 = Parameter(1)
    p2 = Parameter(2)
    p3 = Parameter(3)
    p4 = Parameter(4)

    l_object = [p1, p2, p3]
    obj = cls(*l_object)

    idx = 1
    assert obj[idx] == p2
    obj[idx] = p4
    assert obj[idx] == p4
    edges = obj._global_object.map.get_edges(obj)
    assert len(edges) == len(obj)
    for item in obj:
        assert item.unique_name in edges
    assert p2.unique_name not in edges


@pytest.mark.parametrize("cls", class_constructors)
def test_CollectionBase_set_index_based(cls):
    p1 = Parameter(1)
    p2 = Parameter(2)
    p3 = Parameter(3)
    p4 = Parameter(4)
    p5 = Parameter(5)
    d = cls(p1, p2)

    l_object = [p3, p4, p5]
    obj = cls(*l_object)

    idx = 1
    assert obj[idx] == p4
    obj[idx] = d
    assert obj[idx] == d
    edges = obj._global_object.map.get_edges(obj)
    assert len(edges) == len(obj)
    for item in obj:
        assert item.unique_name in edges
    assert p4.unique_name not in edges


@pytest.mark.parametrize("cls", class_constructors)
def test_CollectionBase_sort(cls):
    v = [1, 4, 3, 2, 5]
    expected = [1, 2, 3, 4, 5]
    d = cls(*[Parameter(v[i]) for i in range(len(v))])
    d.sort(lambda x: x.value)
    for i, item in enumerate(d):
        assert item.value == expected[i]


@pytest.mark.parametrize("cls", class_constructors)
def test_CollectionBase_sort_reverse(cls):
    v = [1, 4, 3, 2, 5]
    expected = [1, 2, 3, 4, 5]
    expected.reverse()
    d = cls(*[Parameter(v[i]) for i in range(len(v))])
    d.sort(lambda x: x.value, reverse=True)
    for i, item in enumerate(d):
        assert item.value == expected[i]


class Beta(ObjBase):
    pass


@pytest.mark.parametrize("cls", class_constructors)
def test_CollectionBaseGraph(cls):
    from easyscience import global_object

    G = global_object.map
    p = [Parameter(1), Parameter(2)]
    p_id = [_p.unique_name for _p in p]
    bb = cls(*p)
    bb_id = bb.unique_name
    b = Beta(bb=bb)
    b_id = b.unique_name
    for _id in p_id:
        assert _id in G.get_edges(bb)
    assert len(p) == len(G.get_edges(bb))
    assert bb_id in G.get_edges(b)
    assert 1 == len(G.get_edges(b))
