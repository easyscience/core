# SPDX-FileCopyrightText: 2024 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from dataclasses import dataclass
from enum import Enum
from enum import unique

from easyscience import global_object

# Change to importlib.metadata when Python 3.10 is the minimum version
# import importlib.metadata
# installed_packages = [x.name for x in importlib.metadata.distributions()]

lmfit_engine_available = False
try:
    import lmfit  # noqa: F401

    lmfit_engine_available = True
except ImportError:
    global_object.log.getLogger('fitting').warning(
        'LMFit minimization is not available. Probably lmfit has not been installed.'
    )

bumps_engine_available = False
try:
    import bumps  # noqa: F401

    bumps_engine_available = True
except ImportError:
    global_object.log.getLogger('fitting').warning(
        'Bumps minimization is not available. Probably bumps has not been installed.'
    )

dfo_engine_available = False
try:
    import dfols  # noqa: F401

    dfo_engine_available = True
except ImportError:
    global_object.log.getLogger('fitting').warning(
        'DFO minimization is not available. Probably dfols has not been installed.'
    )


@dataclass
class AvailableMinimizer:
    package: str
    method: str
    enum_id: int


@unique
class Minimizers(AvailableMinimizer, Enum):
    if lmfit_engine_available:
        LMFit = 'lm', 'leastsq', 11
        LMFit_leastsq = 'lm', 'leastsq', 12
        LMFit_powell = 'lm', 'powell', 13
        LMFit_cobyla = 'lm', 'cobyla', 14
        LMFit_differential_evolution = 'lm', 'differential_evolution', 15
        LMFit_scipy_least_squares = 'lm', 'least_squares', 16

    if bumps_engine_available:
        Bumps = 'bumps', 'amoeba', 21
        Bumps_simplex = 'bumps', 'amoeba', 22
        Bumps_newton = 'bumps', 'newton', 23
        Bumps_lm = 'bumps', 'lm', 24

    if dfo_engine_available:
        DFO = 'dfo', 'leastsq', 31
        DFO_leastsq = 'dfo', 'leastsq', 32
