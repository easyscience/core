import pytest

from easyscience.global_object.session import reset_default_session
from easyscience.variable import DescriptorBool


class TestDescriptorBool:
    @pytest.fixture
    def descriptor(self):
        descriptor = DescriptorBool(
            name='name',
            value=True,
            description='description',
            url='url',
            display_name='display_name',
            parent=None,
        )
        return descriptor

    @pytest.fixture
    def clear(self):
        reset_default_session()

    def test_init(self, descriptor: DescriptorBool):
        # When Then Expect
        assert descriptor._bool_value == True  # noqa: E712

        # From super
        assert descriptor._name == 'name'
        assert descriptor._description == 'description'
        assert descriptor._url == 'url'
        assert descriptor._display_name == 'display_name'

    @pytest.mark.parametrize('bool_value', ['string', 0, 1.0])
    def test_init_bool_value_type_exception(self, bool_value):
        # When Then Expect
        with pytest.raises(ValueError):
            DescriptorBool(
                name='name',
                value=bool_value,
                description='description',
                url='url',
                display_name='display_name',
                parent=None,
            )

    def test_value(self, descriptor: DescriptorBool):
        # When Then Expect
        assert descriptor.value == True  # noqa: E712

    def test_set_value(self, descriptor: DescriptorBool):
        # When Then
        descriptor.value = False

        # Expect
        assert descriptor._bool_value == False  # noqa: E712

    @pytest.mark.parametrize('bool_value', ['string', 0, 0.0])
    def test_set_value_type_exception(self, descriptor: DescriptorBool, bool_value):
        # When Then Expect
        with pytest.raises(TypeError):
            descriptor.value = bool_value

    def test_repr(self, descriptor: DescriptorBool):
        # When Then
        repr_str = str(descriptor)

        # Expect
        assert repr_str == "<DescriptorBool 'name': True>"

    def test_copy(self, descriptor: DescriptorBool):
        # When Then
        descriptor_copy = descriptor.__copy__()

        # Expect
        assert type(descriptor_copy) is DescriptorBool
        assert descriptor_copy._bool_value == descriptor._bool_value
