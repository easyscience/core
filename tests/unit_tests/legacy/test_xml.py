# import sys
# import xml.etree.ElementTree as ET
# from copy import deepcopy
# from typing import Type

# import pytest

# from easyscience.legacy.xml import XMLSerializer
# from easyscience.variable import DescriptorNumber

# from ..io.test_core import dp_param_dict
# from ..io.test_core import skip_dict
# from easyscience import global_object

# def recursive_remove(d, remove_keys: list) -> dict:
#     """
#     Remove keys from a dictionary.
#     """
#     if not isinstance(remove_keys, list):
#         remove_keys = [remove_keys]
#     if isinstance(d, dict):
#         dd = {}
#         for k in d.keys():
#             if k not in remove_keys:
#                 dd[k] = recursive_remove(d[k], remove_keys)
#         return dd
#     else:
#         return d


# def recursive_test(testing_obj, reference_obj):
#     for i, (k, v) in enumerate(testing_obj.items()):
#         if isinstance(v, dict):
#             recursive_test(v, reference_obj[i])
#         else:
#             assert v == XMLSerializer.string_to_variable(reference_obj[i].text)


# ########################################################################################################################
# # TESTING ENCODING
# ########################################################################################################################
# @pytest.mark.parametrize(**skip_dict)
# @pytest.mark.parametrize(**dp_param_dict)
# def test_variable_XMLDictSerializer(dp_kwargs: dict, dp_cls: Type[DescriptorNumber], skip):
#     data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != "@"}

#     obj = dp_cls(**data_dict)

#     dp_kwargs = deepcopy(dp_kwargs)

#     if isinstance(skip, str):
#         del dp_kwargs[skip]

#     if not isinstance(skip, list):
#         skip = [skip]

#     enc = obj.encode(skip=skip, encoder=XMLSerializer)
#     ref_encode = obj.encode(skip=skip)
#     assert isinstance(enc, str)
#     data_xml = ET.XML(enc)
#     assert data_xml.tag == "data"
#     recursive_test(data_xml, ref_encode)

# # ########################################################################################################################
# # # TESTING DECODING
# # ########################################################################################################################
# @pytest.mark.parametrize(**dp_param_dict)
# def test_variable_XMLDictSerializer_decode(dp_kwargs: dict, dp_cls: Type[DescriptorNumber]):
#     data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != "@"}

#     obj = dp_cls(**data_dict)

#     enc = obj.encode(encoder=XMLSerializer)
#     assert isinstance(enc, str)
#     data_xml = ET.XML(enc)
#     assert data_xml.tag == "data"
#     global_object.map._clear()
#     dec = dp_cls.decode(enc, decoder=XMLSerializer)

#     for k in data_dict.keys():
#         if hasattr(obj, k) and hasattr(dec, k):
#             assert getattr(obj, k) == getattr(dec, k)
#         else:
#             raise AttributeError(f"{k} not found in decoded object")


# def test_slow_encode():

#     if sys.version_info < (3, 9):
#         pytest.skip("This test is only for python 3.9+")

#     a = {"a": [1, 2, 3]}
#     slow_xml = XMLSerializer().encode(a, fast=False)
#     reference = """<data>
#   <a>1</a>
#   <a>2</a>
#   <a>3</a>
# </data>"""
#     assert slow_xml == reference


# def test_include_header():

#     if sys.version_info < (3, 9):
#         pytest.skip("This test is only for python 3.9+")

#     a = {"a": [1, 2, 3]}
#     header_xml = XMLSerializer().encode(a, use_header=True)
#     reference = '?xml version="1.0"  encoding="UTF-8"?\n<data>\n  <a>1</a>\n  <a>2</a>\n  <a>3</a>\n</data>'
#     assert header_xml == reference
