#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience

from ..utils.classUtils import singleton
from .hugger.hugger import ScriptManager
from .logger import Logger
from .map import Map


@singleton
class GlobalObject:
    """
    GlobalObject is the assimilated knowledge of `EasyScience`. Every class based on `EasyScience` gets brought
    into the collective.
    """

    __log = Logger()
    __map = Map()
    __stack = None
    __debug = False

    def __init__(self):
        # Logger. This is so there's a unified logging interface
        self.log: Logger = self.__log
        # Debug. Global debugging level
        self.debug: bool = self.__debug
        # Stack. This is where the undo/redo operations are stored.
        self.stack = self.__stack
        #
        self.script: ScriptManager = ScriptManager()
        # Map. This is the conduit database between all global object species
        self.map: Map = self.__map

    def instantiate_stack(self):
        """
        The undo/redo stack references the collective. Hence it has to be imported
        after initialization.

        :return: None
        :rtype: noneType
        """
        from easyscience.global_object.undo_redo import UndoStack

        self.stack = UndoStack()

    def generate_unique_name(self, name_prefix: str) -> str:
        """
        Generate a generic unique name for the object using the class name and a monotonic counter.
        Names are in the format `name_prefix_0`, `name_prefix_1`, `name_prefix_2`, etc.

        The counter for each prefix only ever increases, ensuring that names are never
        reused even after objects are garbage-collected from the map.

        :param name_prefix: The prefix to be used for the name
        """
        # Get the stored counter for this prefix (-1 means no name generated yet)
        current_counter = self.map._name_counters.get(name_prefix, -1)

        # Also check existing map entries to handle explicitly named objects
        # (e.g. created with a user-supplied unique_name or deserialized)
        max_from_map = -1
        names_with_prefix = [name for name in self.map.vertices() if name.startswith(name_prefix + '_')]
        for name in names_with_prefix:
            name_without_prefix = name.replace(name_prefix + '_', '')
            if name_without_prefix.isdecimal():
                max_from_map = max(max_from_map, int(name_without_prefix))

        # Take the maximum of counter and map, then increment
        next_counter = max(current_counter, max_from_map) + 1
        self.map._name_counters[name_prefix] = next_counter

        return f'{name_prefix}_{next_counter}'
