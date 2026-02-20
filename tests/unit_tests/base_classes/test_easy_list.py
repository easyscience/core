#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

import warnings

import pytest

from easyscience import global_object
from easyscience.base_classes.easy_list import EasyList
from easyscience.base_classes.new_base import NewBase


class Alpha(NewBase):
    """Concrete subclass of NewBase for testing."""

    def __init__(self, unique_name=None, display_name=None):
        super().__init__(unique_name=unique_name, display_name=display_name)

class Beta(NewBase):
    """Another concrete subclass of NewBase for testing."""

    def __init__(self, unique_name=None, display_name=None):
        super().__init__(unique_name=unique_name, display_name=display_name)

class TestEasyList:
    @pytest.fixture(autouse=True)
    def clear(self):
        global_object.map._clear()

    @pytest.fixture
    def populated_list(self):
        a1 = Alpha(unique_name='a1')
        a2 = Alpha(unique_name='a2')
        a3 = Alpha(unique_name='a3')
        return EasyList(a1, a2, a3, protected_types=Alpha)

    # --- Init ---

    def test_empty_init(self):
        el = EasyList()
        assert len(el) == 0
        assert len(el._protected_types) == 1
        assert el._protected_types[0] == NewBase

    def test_init_with_items(self):
        a = Alpha(unique_name='a1')
        b = Alpha(unique_name='a2')
        el = EasyList(a, b)
        assert len(el) == 2
        assert el[0] is a
        assert el[1] is b

    def test_init_with_list_of_items(self):
        items = [Alpha(unique_name='a1'), Alpha(unique_name='a2')]
        el = EasyList(items)
        assert len(el) == 2

    def test_init_single_protected_type(self):
        el = EasyList(protected_types=Alpha)
        assert el._protected_types == [Alpha]

    def test_init_list_of_protected_types(self):
        el = EasyList(protected_types=[Alpha, Beta])
        assert el._protected_types == [Alpha, Beta]

    def test_init_invalid_protected_types_raises(self):
        with pytest.raises(TypeError, match='protected_types must be a NewBase subclass'):
            EasyList(protected_types=int)

    def test_init_invalid_protected_types_list_raises(self):
        with pytest.raises(TypeError, match='protected_types must be a NewBase subclass'):
            EasyList(protected_types=[int, str])

    def test_init_with_data_kwarg(self):
        """Test deserialization-style init via 'data' keyword."""
        items = [Alpha(unique_name='a1'), Alpha(unique_name='a2')]
        el = EasyList(data=items)
        assert len(el) == 2

    # --- Protected types ---

    def test_append_wrong_type_raises(self):
        el = EasyList(protected_types=Alpha)
        with pytest.raises(TypeError, match='Items must be one of'):
            el.append(Beta(unique_name='b1'))

    def test_append_correct_type_succeeds(self):
        el = EasyList(protected_types=Alpha)
        a = Alpha(unique_name='a1')
        el.append(a)
        assert len(el) == 1

    def test_append_non_newbase_raises(self):
        el = EasyList()
        with pytest.raises(TypeError, match='Items must be one of'):
            el.append('not a NewBase')

    def test_insert_wrong_type_raises(self):
        el = EasyList(protected_types=Alpha)
        with pytest.raises(TypeError, match='Items must be one of'):
            el.insert(0, Beta(unique_name='b1'))

    def test_setitem_wrong_type_raises(self):
        a = Alpha(unique_name='a1')
        el = EasyList(a, protected_types=Alpha)
        with pytest.raises(TypeError, match='Items must be one of'):
            el[0] = Beta(unique_name='b1')

    def test_multiple_protected_types(self):
        el = EasyList(protected_types=[Alpha, Beta])
        a = Alpha(unique_name='a1')
        b = Beta(unique_name='b1')
        el.append(a)
        el.append(b)
        assert len(el) == 2

    def test_init_rejects_wrong_type(self):
        b = Beta(unique_name='b1')
        with pytest.raises(TypeError, match='Items must be one of'):
            EasyList(b, protected_types=Alpha)

    # --- __getitem__ ---

    def test_getitem_int(self, populated_list):
        assert populated_list[0].unique_name == 'a1'
        assert populated_list[1].unique_name == 'a2'
        assert populated_list[-1].unique_name == 'a3'

    def test_getitem_int_out_of_range(self, populated_list):
        with pytest.raises(IndexError):
            populated_list[10]

    def test_getitem_slice(self, populated_list):
        sliced = populated_list[0:2]
        assert isinstance(sliced, EasyList)
        assert len(sliced) == 2
        assert sliced[0].unique_name == 'a1'
        assert sliced[1].unique_name == 'a2'

    def test_getitem_str_lookup(self, populated_list):
        item = populated_list['a2']
        assert item.unique_name == 'a2'

    def test_getitem_str_not_found(self, populated_list):
        with pytest.raises(KeyError, match='No item with unique name'):
            populated_list['nonexistent']

    def test_getitem_invalid_type(self, populated_list):
        with pytest.raises(TypeError, match='Index must be an int, slice, or str'):
            populated_list[3.14]

    # --- __setitem__ ---

    def test_setitem_int(self):
        a1 = Alpha(unique_name='a1')
        a2 = Alpha(unique_name='a2')
        el = EasyList(a1, protected_types=Alpha)
        el[0] = a2
        assert el[0].unique_name == 'a2'

    def test_setitem_slice(self):
        a1 = Alpha(unique_name='a1')
        a2 = Alpha(unique_name='a2')
        a3 = Alpha(unique_name='a3')
        a4 = Alpha(unique_name='a4')
        el = EasyList(a1, a2, protected_types=Alpha)
        el[0:2] = [a3, a4]
        assert el[0].unique_name == 'a3'
        assert el[1].unique_name == 'a4'

    def test_setitem_self_replacement_int(self):
        """e[0] = e[0] should work without warning."""
        a1 = Alpha(unique_name='a1')
        a2 = Alpha(unique_name='a2')
        el = EasyList(a1, a2, protected_types=Alpha)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            el[0] = el[0]
            assert len(w) == 0
        assert el[0].unique_name == 'a1'
        assert len(el) == 2

    def test_setitem_self_replacement_slice(self):
        """e[0:2] = e[0:2] should work without warning."""
        a1 = Alpha(unique_name='a1')
        a2 = Alpha(unique_name='a2')
        el = EasyList(a1, a2, protected_types=Alpha)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            el[0:2] = [el[0], el[1]]
            assert len(w) == 0
        assert el[0].unique_name == 'a1'
        assert el[1].unique_name == 'a2'

    def test_setitem_slice_partial_self_replacement(self):
        """e[0:2] = [e[0], new] should only warn about the new item."""
        a1 = Alpha(unique_name='a1')
        a2 = Alpha(unique_name='a2')
        a3 = Alpha(unique_name='a3')
        el = EasyList(a1, a2, protected_types=Alpha)
        el[0:2] = [el[0], a3]
        assert el[0].unique_name == 'a1'
        assert el[1].unique_name == 'a3'

    def test_setitem_slice_length_mismatch_raises(self):
        a1 = Alpha(unique_name='a1')
        a2 = Alpha(unique_name='a2')
        a3 = Alpha(unique_name='a3')
        el = EasyList(a1, a2, protected_types=Alpha)
        with pytest.raises(ValueError, match='Length of new values must match the length of the slice being replaced'):
            el[0:2] = [a3]  # Only one item provided for a slice of length 2

    def test_setitem_invalid_index_type(self):
        a1 = Alpha(unique_name='a1')
        el = EasyList(a1, protected_types=Alpha)
        with pytest.raises(TypeError, match='Index must be an int or slice'):
            el[3.14] = Alpha(unique_name='a2')

    def test_setitem_slice_non_iterable_raises(self):
        a1 = Alpha(unique_name='a1')
        el = EasyList(a1, protected_types=Alpha)
        with pytest.raises(TypeError, match='Value must be an iterable for slice assignment'):
            el[0:1] = Alpha(unique_name='a2')

    # --- __delitem__ ---

    def test_delitem_int(self, populated_list):
        assert len(populated_list) == 3
        del populated_list[0]
        assert len(populated_list) == 2
        assert populated_list[0].unique_name == 'a2'

    def test_delitem_slice(self, populated_list):
        assert len(populated_list) == 3
        del populated_list[0:2]
        assert len(populated_list) == 1
        assert populated_list[0].unique_name == 'a3'

    def test_delitem_str(self, populated_list):
        del populated_list['a2']
        assert len(populated_list) == 2
        assert populated_list[0].unique_name == 'a1'
        assert populated_list[1].unique_name == 'a3'

    def test_delitem_str_not_found(self, populated_list):
        with pytest.raises(KeyError, match='No item with unique name'):
            del populated_list['nonexistent']

    def test_delitem_invalid_type(self, populated_list):
        with pytest.raises(TypeError, match='Index must be an int, slice, or str'):
            del populated_list[3.14]

    # --- Uniqueness ---

    def test_append_duplicate_warns(self):
        a1 = Alpha(unique_name='a1')
        el = EasyList(a1, protected_types=Alpha)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            el.append(a1)
            assert len(w) == 1
            assert 'already in EasyList' in str(w[0].message)
        assert len(el) == 1

    def test_insert_duplicate_warns(self):
        a1 = Alpha(unique_name='a1')
        el = EasyList(a1, protected_types=Alpha)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            el.insert(0, a1)
            assert len(w) == 1
            assert 'already in EasyList' in str(w[0].message)
        assert len(el) == 1

    def test_setitem_duplicate_warns(self):
        a1 = Alpha(unique_name='a1')
        a2 = Alpha(unique_name='a2')
        el = EasyList(a1, a2, protected_types=Alpha)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            el[0] = a2  # a2 already at index 1
            assert len(w) == 1
            assert 'already in EasyList' in str(w[0].message)
        # Original value should remain unchanged
        assert el[0].unique_name == 'a1'

    def test_setitem_slice_duplicate_warns(self):
        a1 = Alpha(unique_name='a1')
        a2 = Alpha(unique_name='a2')
        a3 = Alpha(unique_name='a3')
        a4 = Alpha(unique_name='a4')
        el = EasyList(a1, a2, a3, protected_types=Alpha)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            el[0:3] = [a1, a3, a4]  # a3 already at index 2
            assert len(w) == 1
            assert 'already in EasyList' in str(w[0].message)
        assert el[0].unique_name == 'a1'
        assert el[1].unique_name == 'a2'  # a3 should not replace a2 because it's a duplicate
        assert el[2].unique_name == 'a4'

    # --- insert ---

    def test_insert_at_beginning(self):
        a1 = Alpha(unique_name='a1')
        a2 = Alpha(unique_name='a2')
        el = EasyList(a1, protected_types=Alpha)
        el.insert(0, a2)
        assert el[0].unique_name == 'a2'
        assert el[1].unique_name == 'a1'

    def test_insert_at_end(self):
        a1 = Alpha(unique_name='a1')
        a2 = Alpha(unique_name='a2')
        el = EasyList(a1, protected_types=Alpha)
        el.insert(100, a2)
        assert el[-1].unique_name == 'a2'

    def test_insert_non_int_index_raises(self):
        el = EasyList(protected_types=Alpha)
        with pytest.raises(TypeError, match='Index must be an integer'):
            el.insert('bad', Alpha(unique_name='a1'))

    # --- __contains__ ---

    def test_contains_by_object(self):
        a1 = Alpha(unique_name='a1')
        el = EasyList(a1, protected_types=Alpha)
        assert a1 in el

    def test_not_contains_by_object(self):
        a1 = Alpha(unique_name='a1')
        a2 = Alpha(unique_name='a2')
        el = EasyList(a1, protected_types=Alpha)
        assert a2 not in el

    def test_contains_by_str(self):
        a1 = Alpha(unique_name='a1')
        el = EasyList(a1, protected_types=Alpha)
        assert 'a1' in el

    def test_not_contains_by_str(self):
        a1 = Alpha(unique_name='a1')
        el = EasyList(a1, protected_types=Alpha)
        assert 'nonexistent' not in el

    # --- reverse ---
    def test_reverse(self):
        a1 = Alpha(unique_name='a1')
        a2 = Alpha(unique_name='a2')
        el = EasyList(a1, a2, protected_types=Alpha)
        reversed_el = list(reversed(el))
        assert reversed_el[0].unique_name == 'a2'
        assert reversed_el[1].unique_name == 'a1'

    # --- index ---

    def test_index_by_object(self, populated_list):
        item = populated_list[1]
        assert populated_list.index(item) == 1

    def test_index_by_str(self, populated_list):
        assert populated_list.index('a2', 0, 3) == 1

    def test_index_str_not_found(self, populated_list):
        with pytest.raises(ValueError, match='is not in EasyList'):
            populated_list.index('nonexistent', 0, 3)

    def test_index_by_object_not_found(self, populated_list):
        other = Alpha(unique_name='other')
        with pytest.raises(ValueError):
            populated_list.index(other, 0, len(populated_list))

    def test_index_not_in_range(self, populated_list):
        with pytest.raises(ValueError):
            populated_list.index('a2', 2, 3)

    # --- pop ---

    def test_pop_default_last(self, populated_list):
        item = populated_list.pop()
        assert item.unique_name == 'a3'
        assert len(populated_list) == 2

    def test_pop_by_int(self, populated_list):
        item = populated_list.pop(0)
        assert item.unique_name == 'a1'
        assert len(populated_list) == 2

    def test_pop_by_str(self, populated_list):
        item = populated_list.pop('a2')
        assert item.unique_name == 'a2'
        assert len(populated_list) == 2

    def test_pop_str_not_found(self, populated_list):
        with pytest.raises(KeyError, match='No item with unique name'):
            populated_list.pop('nonexistent')

    def test_pop_invalid_type(self, populated_list):
        with pytest.raises(TypeError, match='Index must be an int or str'):
            populated_list.pop(3.14)

    # --- sort ---

    def test_sort(self):
        a3 = Alpha(unique_name='c')
        a1 = Alpha(unique_name='a')
        a2 = Alpha(unique_name='b')
        el = EasyList(a3, a1, a2, protected_types=Alpha)
        el.sort(key=lambda x: x.unique_name)
        assert el[0].unique_name == 'a'
        assert el[1].unique_name == 'b'
        assert el[2].unique_name == 'c'

    def test_sort_reverse(self):
        a1 = Alpha(unique_name='a')
        a2 = Alpha(unique_name='b')
        a3 = Alpha(unique_name='c')
        el = EasyList(a1, a2, a3, protected_types=Alpha)
        el.sort(key=lambda x: x.unique_name, reverse=True)
        assert el[0].unique_name == 'c'
        assert el[1].unique_name == 'b'
        assert el[2].unique_name == 'a'

    # --- __iter__ / __len__ ---

    def test_len(self):
        el = EasyList(protected_types=Alpha)
        assert len(el) == 0
        el.append(Alpha(unique_name='a1'))
        assert len(el) == 1

    # --- __repr__ ---

    def test_repr(self):
        el = EasyList(protected_types=Alpha)
        r = repr(el)
        assert 'EasyList' in r
        assert 'length 0' in r
        assert 'Alpha' in r

    # --- MutableSequence behavior ---
    # If we were to inherit from List instead of MutableSequence, we would have to implement all of these manually.

    def test_iter(self):
        a1 = Alpha(unique_name='a1')
        a2 = Alpha(unique_name='a2')
        el = EasyList(a1, a2, protected_types=Alpha)
        names = [item.unique_name for item in el]
        assert names == ['a1', 'a2']

    def test_extend(self):
        a1 = Alpha(unique_name='a1')
        a2 = Alpha(unique_name='a2')
        el = EasyList(protected_types=Alpha)
        el.extend([a1, a2])
        assert len(el) == 2

    def test_remove(self):
        a1 = Alpha(unique_name='a1')
        a2 = Alpha(unique_name='a2')
        el = EasyList(a1, a2, protected_types=Alpha)
        el.remove(a1)
        assert len(el) == 1
        assert el[0].unique_name == 'a2'

    def test_iadd(self):
        a1 = Alpha(unique_name='a1')
        a2 = Alpha(unique_name='a2')
        el = EasyList(a1, protected_types=Alpha)
        el += [a2]
        assert len(el) == 2

    def test_iadd_easylist(self):
        a1 = Alpha(unique_name='a1')
        a2 = Alpha(unique_name='a2')
        el = EasyList(a1, protected_types=Alpha)
        el += EasyList(a2, protected_types=Alpha)
        assert len(el) == 2

    def test_count(self):
        a1 = Alpha(unique_name='a1')
        el = EasyList(a1, protected_types=Alpha)
        assert el.count(a1) == 1

    def test_clear(self):
        a1 = Alpha(unique_name='a1')
        el = EasyList(a1, protected_types=Alpha)
        el.clear()
        assert len(el) == 0

    # --- Serialization ---

    def test_to_dict(self):
        a1 = Alpha(unique_name='a1')
        a2 = Alpha(unique_name='a2')
        el = EasyList(a1, a2, unique_name='my_list', protected_types=Alpha)
        d = el.to_dict()
        assert 'data' in d
        assert len(d['data']) == 2
        assert 'protected_types' in d
        assert d['protected_types'][0]['@class'] == 'Alpha'

    def test_to_dict_default_protected_type_not_serialized(self):
        a1 = NewBase(unique_name='nb1')
        el = EasyList(a1, unique_name='my_list')
        d = el.to_dict()
        assert 'protected_types' not in d

    def test_from_dict_round_trip(self):
        a1 = Alpha(unique_name='a1')
        a2 = Alpha(unique_name='a2')
        el = EasyList(a1, a2, unique_name='my_list', protected_types=Alpha)
        d = el.to_dict()
        # Clear the global map so deserialized objects can reuse the same unique names
        global_object.map._clear()
        el2 = EasyList.from_dict(d)
        assert len(el2) == 2
        assert el2[0].unique_name == 'a1'
        assert el2[1].unique_name == 'a2'
        assert d == el2.to_dict()  # The dicts should be the same after round trip
