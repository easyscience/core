#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

from __future__ import annotations

import datetime
import json
from abc import abstractmethod
from enum import Enum
from importlib import import_module
from inspect import getfullargspec
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import MutableSequence
from typing import Optional
from typing import Tuple

import numpy as np

if TYPE_CHECKING:
    from .serializer_component import SerializerComponent

_e = json.JSONEncoder()


class SerializerBase:
    """
    This is the base class for creating an encoder/decoder which can convert EasyScience objects. `encode` and `decode` are
    abstract methods to be implemented for each serializer. It is expected that the helper function `_convert_to_dict`
    will be used as a base for encoding (or the `SerializerDict` as it's more flexible).
    """

    @abstractmethod
    def encode(self, obj: SerializerComponent, skip: Optional[List[str]] = None, **kwargs) -> any:
        """
        Abstract implementation of an encoder.

        :param obj: Object to be encoded.
        :param skip: List of field names as strings to skip when forming the encoded object
        :param kwargs: Any additional key word arguments to be passed to the encoder
        :return: encoded object containing all information to reform an EasyScience object.
        """

        pass

    @classmethod
    @abstractmethod
    def decode(cls, obj: Any) -> Any:
        """
        Re-create an EasyScience object from the output of an encoder. The default decoder is `SerializerDict`.

        :param obj: encoded EasyScience object
        :return: Reformed EasyScience object
        """
        pass

    @staticmethod
    def get_arg_spec(func: Callable) -> Tuple[Any, List[str]]:
        """
        Get the full argument specification of a function (typically `__init__`)

        :param func: Function to be inspected
        :return: Tuple of argument spec and arguments
        """

        spec = getfullargspec(func)
        args = spec.args[1:]
        return spec, args

    @staticmethod
    def _encode_objs(obj: Any) -> Dict[str, Any]:
        """
        A JSON serializable dict representation of an object.

        :param obj: any object to be encoded
        :param skip: List of field names as strings to skip when forming the encoded object
        :param kwargs: Key-words to pass to `SerializerBase`
        :return: JSON encoded dictionary
        """

        if isinstance(obj, datetime.datetime):
            return {
                '@module': 'datetime',
                '@class': 'datetime',
                'string': obj.__str__(),
            }
        if np is not None:
            if isinstance(obj, np.ndarray):
                if str(obj.dtype).startswith('complex'):
                    return {
                        '@module': 'numpy',
                        '@class': 'array',
                        'dtype': obj.dtype.__str__(),
                        'data': [obj.real.tolist(), obj.imag.tolist()],
                    }
                return {
                    '@module': 'numpy',
                    '@class': 'array',
                    'dtype': obj.dtype.__str__(),
                    'data': obj.tolist(),
                }
            if isinstance(obj, np.generic):
                return obj.item()
        try:
            return _e.default(obj)
        except TypeError:
            return obj

    def _convert_to_dict(
        self,
        obj: SerializerComponent,
        skip: Optional[List[str]] = None,
        full_encode: bool = False,
        **kwargs,
    ) -> dict:
        """
        A JSON serializable dict representation of an object.
        """
        if skip is None:
            skip = []

        if full_encode:
            new_obj = SerializerBase._encode_objs(obj)
            if new_obj is not obj:
                return new_obj

        d = {'@module': obj.__module__, '@class': obj.__class__.__name__}

        try:
            parent_module = obj.__module__.split('.')[0]
            module_version = import_module(parent_module).__version__  # type: ignore
            d['@version'] = '{}'.format(module_version)
        except (AttributeError, ImportError):
            d['@version'] = None  # type: ignore

        spec, args = SerializerBase.get_arg_spec(obj.__class__.__init__)
        if hasattr(obj, '_arg_spec'):
            args = obj._arg_spec

        redirect = getattr(obj, '_REDIRECT', {})

        def runner(o):
            if full_encode:
                return SerializerBase._encode_objs(o)
            else:
                return o

        for c in args:
            if c not in skip:
                if c in redirect.keys():
                    if redirect[c] is None:
                        continue
                    a = runner(redirect[c](obj))
                else:
                    try:
                        a = runner(obj.__getattribute__(c))
                    except AttributeError:
                        try:
                            a = runner(obj.__getattribute__('_' + c))
                        except AttributeError:
                            err = True
                            if hasattr(obj, 'kwargs'):
                                # type: ignore
                                option = getattr(obj, 'kwargs')
                                if hasattr(option, c):
                                    v = getattr(option, c)
                                    delattr(option, c)
                                    d.update(runner(v))  # pylint: disable=E1101
                                    err = False
                            if hasattr(obj, '_kwargs'):
                                # type: ignore
                                option = getattr(obj, '_kwargs')
                                if hasattr(option, c):
                                    v = getattr(option, c)
                                    delattr(option, c)
                                    d.update(runner(v))  # pylint: disable=E1101
                                    err = False
                            if err:
                                raise NotImplementedError(
                                    'Unable to automatically determine as_dict '
                                    'format from class. MSONAble requires all '
                                    'args to be present as either self.argname or '
                                    'self._argname, and kwargs to be present under'
                                    'a self.kwargs variable to automatically '
                                    'determine the dict format. Alternatively, '
                                    'you can implement both as_dict and from_dict.'
                                )
                d[c] = self._recursive_encoder(a, skip=skip, encoder=self, full_encode=full_encode, **kwargs)
        if spec.varargs is not None and getattr(obj, spec.varargs, None) is not None:
            d.update({spec.varargs: getattr(obj, spec.varargs)})
        if hasattr(obj, '_kwargs'):
            if not issubclass(type(obj), MutableSequence):
                d_k = list(d.keys())
                for k, v in getattr(obj, '_kwargs').items():
                    # We should have already obtained `key` and `_key`
                    if k not in skip and k not in d_k:
                        if k[0] == '_' and k[1:] in d_k:
                            continue
                        vv = v
                        if k in redirect.keys():
                            if redirect[k] is None:
                                continue
                            vv = redirect[k](obj)
                        v_ = runner(vv)
                        d[k] = self._recursive_encoder(
                            v_,
                            skip=skip,
                            encoder=self,
                            full_encode=full_encode,
                            **kwargs,
                        )
        if isinstance(obj, Enum):
            d.update({'value': runner(obj.value)})  # pylint: disable=E1101
        if hasattr(obj, '_convert_to_dict'):
            d = obj._convert_to_dict(d, self, skip=skip, **kwargs)
        if hasattr(obj, '_global_object') and 'unique_name' not in d and 'unique_name' not in skip:
            d['unique_name'] = obj.unique_name
        return d

    @staticmethod
    def _convert_from_dict(d):
        """
        Recursive method to support decoding dicts and lists containing EasyScience objects

        :param d: Dictionary containing JSONed EasyScience objects
        :return: Reformed EasyScience object

        """
        T_ = type(d)
        if isinstance(d, dict):
            if '@module' in d and '@class' in d:
                modname = d['@module']
                classname = d['@class']
            else:
                modname = None
                classname = None
            if modname and modname not in ['bson.objectid', 'numpy']:
                if modname == 'datetime' and classname == 'datetime':
                    try:
                        dt = datetime.datetime.strptime(d['string'], '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        dt = datetime.datetime.strptime(d['string'], '%Y-%m-%d %H:%M:%S')
                    return dt

                mod = __import__(modname, globals(), locals(), [classname], 0)
                if hasattr(mod, classname):
                    cls_ = getattr(mod, classname)
                    data = {k: SerializerBase._convert_from_dict(v) for k, v in d.items() if not k.startswith('@')}
                    return cls_(**data)
            elif np is not None and modname == 'numpy' and classname == 'array':
                if d['dtype'].startswith('complex'):
                    return np.array([r + i * 1j for r, i in zip(*d['data'])], dtype=d['dtype'])
                return np.array(d['data'], dtype=d['dtype'])

        if issubclass(T_, (list, MutableSequence)):
            return [SerializerBase._convert_from_dict(x) for x in d]
        return d

    def _recursive_encoder(self, obj, skip: List[str] = [], encoder=None, full_encode=False, **kwargs):
        """
        Walk through an object encoding it
        """
        if encoder is None:
            encoder = SerializerBase()
        T_ = type(obj)
        if issubclass(T_, (list, tuple, MutableSequence)):
            # Is it a core MutableSequence?
            if hasattr(obj, 'encode') and obj.__class__.__module__ != 'builtins':  # strings have encode
                return encoder._convert_to_dict(obj, skip, full_encode, **kwargs)
            else:
                return [self._recursive_encoder(it, skip, encoder, full_encode, **kwargs) for it in obj]
        if isinstance(obj, dict):
            return {kk: self._recursive_encoder(vv, skip, encoder, full_encode, **kwargs) for kk, vv in obj.items()}
        if hasattr(obj, 'encode') and obj.__class__.__module__ != 'builtins':  # strings have encode
            return encoder._convert_to_dict(obj, skip, full_encode, **kwargs)
        return obj

