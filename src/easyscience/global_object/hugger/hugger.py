# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from typing import List

from ...utils.classUtils import singleton


@singleton
class Store:
    __log = []
    __var_ident = 'var_'
    __ret_ident = 'ret_'

    def __init__(self):
        self.log = self.__log  # TODO Async problem?
        self.var_ident = self.__var_ident
        self.ret_ident = self.__ret_ident

    @staticmethod
    def get_defaults() -> dict:
        return {
            'log': Store.__log,
            'create_list': Store.__create_list,
            'unique_args': Store.__unique_args,
            'unique_rets': Store.__unique_rets,
            'var_ident': Store.__var_ident,
            'ret_ident': Store.__ret_ident,
        }

    def append_log(self, log_entry: str):
        self.log.append(log_entry)


class ScriptManager:
    def __init__(self, enabled=True):
        self._store = Store()
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value

    def history(self) -> List[str]:
        return self._store.log

    def reset_history(self):
        defaults = Store.get_defaults()
        for key, item in defaults.items():
            setattr(self._store, key, item)

    def append_log(self, log_entry: str):
        self._store.log.append(log_entry)
