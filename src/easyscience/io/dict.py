from __future__ import annotations

__author__ = "https://github.com/materialsvirtuallab/monty/blob/master/monty/json.py"
__version__ = "3.0.0"
#  SPDX-FileCopyrightText: 2023 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2023 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience


from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from .template import BaseEncoderDecoder

if TYPE_CHECKING:
    from .component_serializer import ComponentSerializer


class DictSerializer(BaseEncoderDecoder):
    """
    This is a serializer that can encode and decode EasyScience objects to a JSON encoded dictionary.
    """

    def encode(
        self,
        obj: ComponentSerializer,
        skip: Optional[List[str]] = None,
        full_encode: bool = False,
        **kwargs,
    ):
        """
        Convert an EasyScience object to a JSON encoded dictionary

        :param obj: Object to be encoded.
        :param skip: List of field names as strings to skip when forming the encoded object
        :param full_encode: Should the data also be JSON encoded (default False)
        :param kwargs: Any additional key word arguments to be passed to the encoder
        :return: object encoded to dictionary containing all information to reform an EasyScience object.
        """

        return self._convert_to_dict(obj, skip=skip, full_encode=full_encode, **kwargs)

    @classmethod
    def decode(cls, d: Dict) -> ComponentSerializer:
        """
        :param d: Dict representation.
        :return: ComponentSerializer class.
        """

        return BaseEncoderDecoder._convert_from_dict(d)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> ComponentSerializer:
        """
        :param d: Dict representation.
        :return: ComponentSerializer class.
        """
        return BaseEncoderDecoder._convert_from_dict(d)