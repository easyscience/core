#  SPDX-FileCopyrightText: 2025 EasyScience contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2025 Contributors to the EasyScience project <https://github.com/easyScience/EasyScience


from ..base_classes.obj_base import ObjBase


class ExperimentBase(ObjBase):
    """
    This virtual class allows for the creation of technique-specific Experiment objects.
    """
    def __init__(self, name: str, *args, **kwargs):
        super(ExperimentBase, self).__init__(name, *args, **kwargs)
        self._name = name

    # required dunder methods
    def __str__(self):
        return f"Experiment: {self._name}"
    
    