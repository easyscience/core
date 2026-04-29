# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import pytest

from easyscience import global_object
from easyscience.base_classes import EasyCollection
from easyscience.base_classes import NewBase


class Alpha(NewBase):
    def __init__(self, unique_name=None, display_name=None):
        super().__init__(unique_name=unique_name, display_name=display_name)


class TestEasyCollection:
    @pytest.fixture(autouse=True)
    def clear(self):
        global_object.map._clear()

    def test_init_accepts_newbase_items_by_default(self):
        alpha = Alpha(unique_name='alpha')

        collection = EasyCollection(alpha, display_name='collection')

        assert collection.display_name == 'collection'
        assert collection[0] is alpha

    def test_init_flattens_positional_list_args(self):
        first = Alpha(unique_name='first')
        second = Alpha(unique_name='second')
        third = Alpha(unique_name='third')

        collection = EasyCollection([first, second], third)

        assert list(collection) == [first, second, third]

    def test_protected_types_are_enforced(self):
        collection = EasyCollection(protected_types=Alpha)

        collection.append(Alpha(unique_name='alpha'))

        with pytest.raises(TypeError, match='Items must be one of'):
            collection.append(NewBase(unique_name='new-base'))

    def test_graph_edges_are_applied_on_append_insert_and_replace(self):
        first = Alpha(unique_name='first')
        second = Alpha(unique_name='second')
        replacement = Alpha(unique_name='replacement')
        collection = EasyCollection(first)

        collection.insert(0, second)
        collection[1] = replacement

        assert first.unique_name not in global_object.map.get_edges(collection)
        assert second.unique_name in global_object.map.get_edges(collection)
        assert replacement.unique_name in global_object.map.get_edges(collection)

    def test_delete_and_pop_prune_graph_edges(self):
        first = Alpha(unique_name='first')
        second = Alpha(unique_name='second')
        collection = EasyCollection(first, second)

        del collection[0]
        popped = collection.pop('second')

        assert popped is second
        assert first.unique_name not in global_object.map.get_edges(collection)
        assert second.unique_name not in global_object.map.get_edges(collection)
        assert len(collection) == 0

    def test_string_lookup_uses_unique_name(self):
        first = Alpha(unique_name='first')
        second = Alpha(unique_name='second')
        collection = EasyCollection(first, second)

        assert collection['second'] is second
        with pytest.raises(KeyError, match='No item with unique name'):
            collection['missing']

    def test_missing_unique_name_removal_raises_key_error(self):
        collection = EasyCollection(Alpha(unique_name='first'))

        with pytest.raises(KeyError, match='No item with unique name'):
            del collection['missing']

        with pytest.raises(KeyError, match='No item with unique name'):
            collection.pop('missing')

    def test_slice_preserves_collection_metadata(self):
        first = Alpha(unique_name='first')
        second = Alpha(unique_name='second')
        collection = EasyCollection(first, second, display_name='collection')

        sliced = collection[:1]

        assert isinstance(sliced, EasyCollection)
        assert sliced.display_name == collection.display_name
        assert list(sliced) == [first]

    def test_to_dict_and_from_dict_round_trip(self):
        first = Alpha(unique_name='first')
        second = Alpha(unique_name='second')
        collection = EasyCollection(first, second, unique_name='collection_key', protected_types=Alpha)

        collection_dict = collection.to_dict()
        global_object.map._clear()
        deserialized = EasyCollection.from_dict(collection_dict)

        assert deserialized.unique_name == 'collection_key'
        assert [item.unique_name for item in deserialized] == ['first', 'second']
        assert deserialized.to_dict() == collection_dict

    def test_as_dict_is_compatibility_alias(self):
        collection = EasyCollection(Alpha(unique_name='alpha'))

        assert collection.as_dict() == collection.to_dict()

    def test_empty_collection_round_trip_does_not_repopulate(self):
        collection = EasyCollection()

        collection_dict = collection.to_dict()
        global_object.map._clear()
        deserialized = EasyCollection.from_dict(collection_dict)

        assert len(deserialized) == 0
        assert list(deserialized) == []
        assert deserialized.to_dict() == collection_dict

    def test_slice_assignment_rejects_within_batch_duplicates(self):
        first = Alpha(unique_name='first')
        second = Alpha(unique_name='second')
        duplicate = Alpha(unique_name='dup')
        collection = EasyCollection(first, second)

        with pytest.warns(UserWarning, match='already in EasyCollection'):
            collection[0:2] = [duplicate, duplicate]

        # Second slot should fall back to the original ``second`` because the
        # batch already contained ``duplicate``.
        assert collection[0] is duplicate
        assert collection[1] is second