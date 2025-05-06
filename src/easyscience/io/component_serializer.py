#  SPDX-FileCopyrightText: 2023 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2023 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from .dict import DictSerializer

if TYPE_CHECKING:
    from .template import BaseEncoderDecoder


class ComponentSerializer:
    """
    This base class adds the capability of saving and loading (encoding/decoding, serializing/deserializing) easyscience 
    objects via the `encode` and `decode` methods. 
    The default encoder is `DictSerializer`, which converts the object to a dictionary.

    Shortcuts for dictionary and encoding is also present.
    """

    _CORE = True

    def __deepcopy__(self, memo):
        return self.from_dict(self.as_dict())

    def encode(self, skip: Optional[List[str]] = None, encoder: Optional[BaseEncoderDecoder] = None, **kwargs) -> Any:
        """
        Use an encoder to covert an EasyScience object into another format. Default is to a dictionary using `DictSerializer`.

        :param skip: List of field names as strings to skip when forming the encoded object
        :param encoder: The encoder to be used for encoding the data. Default is `DictSerializer`
        :param kwargs: Any additional key word arguments to be passed to the encoder
        :return: encoded object containing all information to reform an EasyScience object.
        """
        if encoder is None:
            encoder = DictSerializer
        encoder_obj = encoder()
        return encoder_obj.encode(self, skip=skip, **kwargs)

    @classmethod
    def decode(cls, obj: Any, decoder: Optional[BaseEncoderDecoder] = None) -> Any:
        """
        Re-create an EasyScience object from the output of an encoder. The default decoder is `DictSerializer`.

        :param obj: encoded EasyScience object
        :param decoder: decoder to be used to reform the EasyScience object
        :return: Reformed EasyScience object
        """

        if decoder is None:
            decoder = DictSerializer
        return decoder.decode(obj)

    def as_dict(self, skip: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert an EasyScience object into a full dictionary using `DictSerializer`.
        This is a shortcut for ```obj.encode(encoder=DictSerializer)```

        :param skip: List of field names as strings to skip when forming the dictionary
        :return: encoded object containing all information to reform an EasyScience object.
        """

        return self.encode(skip=skip, encoder=DictSerializer)

    @classmethod
    def from_dict(cls, obj_dict: Dict[str, Any]) -> None:
        """
        Re-create an EasyScience object from a full encoded dictionary.

        :param obj_dict: dictionary containing the serialized contents (from `DictSerializer`) of an EasyScience object
        :return: Reformed EasyScience object
        """

        return cls.decode(obj_dict, decoder=DictSerializer)
