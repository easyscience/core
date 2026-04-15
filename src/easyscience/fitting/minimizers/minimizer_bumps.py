# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import copy
from typing import Callable
from typing import List
from typing import Optional

import numpy as np
from bumps.fitters import FIT_AVAILABLE_IDS
from bumps.fitters import FITTERS
from bumps.fitters import FitDriver
from bumps.mapper import SerialMapper
from bumps.monitor import Monitor
from bumps.names import Curve
from bumps.names import FitProblem
from bumps.parameter import Parameter as BumpsParameter

# causes circular import when Parameter is imported
# from easyscience.base_classes import ObjBase
from easyscience.variable import Parameter

from ..available_minimizers import AvailableMinimizers
from .minimizer_base import MINIMIZER_PARAMETER_PREFIX
from .minimizer_base import MinimizerBase
from .utils import FitCancelled
from .utils import FitError
from .utils import FitResults

FIT_AVAILABLE_IDS_FILTERED = copy.copy(FIT_AVAILABLE_IDS)
# Considered experimental
FIT_AVAILABLE_IDS_FILTERED.remove('pt')


class _StepCounterMonitor(Monitor):
    """Lightweight monitor that ensures step count is recorded in
    history.
    """

    def __init__(self):
        self.last_step = 0

    def config_history(self, history):
        history.requires(step=1)

    def __call__(self, history):
        self.last_step = int(history.step[0])


class _BumpsProgressMonitor(Monitor):
    def __init__(self, owner, problem, callback):
        self._owner = owner
        self._problem = problem
        self._callback = callback
        self.cancel_requested = False

    def config_history(self, history):
        history.requires(step=1, point=1, value=1)

    def __call__(self, history):
        payload = self._owner._build_progress_payload(
            problem=self._problem,
            iteration=int(history.step[0]),
            point=np.asarray(history.point[0]),
            nllf=float(history.value[0]),
        )
        should_continue = self._callback(payload)
        if should_continue is False:
            self.cancel_requested = True


class Bumps(MinimizerBase):
    """
    This is a wrapper to Bumps: https://bumps.readthedocs.io/
    It allows for the Bumps fitting engine to use parameters declared in an `EasyScience.base_classes.ObjBase`.
    """

    package = 'bumps'

    def __init__(
        self,
        obj,  #: ObjBase,
        fit_function: Callable,
        minimizer_enum: Optional[AvailableMinimizers] = None,
    ):  # todo after constraint changes, add type hint: obj: ObjBase  # noqa: E501
        """Initialize the fitting engine with a `ObjBase` and an
        arbitrary fitting function.

        :param obj: Object containing elements of the `Parameter` class
        :type obj: ObjBase
        :param fit_function: function that when called returns y values. 'x' must be the first
                            and only positional argument. Additional values can be supplied by
                            keyword/value pairs
        :type fit_function: Callable
        """
        super().__init__(obj=obj, fit_function=fit_function, minimizer_enum=minimizer_enum)
        self._p_0 = {}

    @staticmethod
    def all_methods() -> List[str]:
        return FIT_AVAILABLE_IDS_FILTERED

    @staticmethod
    def supported_methods() -> List[str]:
        # only a small subset
        methods = ['amoeba', 'newton', 'lm']
        return methods

    def fit(
        self,
        x: np.ndarray,
        y: np.ndarray,
        weights: np.ndarray,
        model: Optional[Callable] = None,
        parameters: Optional[Parameter] = None,
        method: Optional[str] = None,
        tolerance: Optional[float] = None,
        max_evaluations: Optional[int] = None,
        progress_callback: Optional[Callable[[dict], Optional[bool]]] = None,
        minimizer_kwargs: Optional[dict] = None,
        engine_kwargs: Optional[dict] = None,
        **kwargs,
    ) -> FitResults:
        """Perform a fit using the BUMPS engine.

        :param x: points to be calculated at
        :type x: np.ndarray
        :param y: measured points
        :type y: np.ndarray
        :param weights: Weights for supplied measured points
        :type weights: np.ndarray
        :param model: Optional Model which is being fitted to
        :param parameters: Optional parameters for the fit
        :type parameters: List[BumpsParameter]
        :param method: Method for minimization
        :type method: str
        :param progress_callback: Optional callback for progress updates
        :type progress_callback: Callable
        :return: Fit results
        :rtype: FitResults
        """
        method_dict = self._get_method_kwargs(method)

        x, y, weights = np.asarray(x), np.asarray(y), np.asarray(weights)

        if y.shape != x.shape:
            raise ValueError('x and y must have the same shape.')

        if weights.shape != x.shape:
            raise ValueError('Weights must have the same shape as x and y.')

        if not np.isfinite(weights).all():
            raise ValueError('Weights cannot be NaN or infinite.')

        if (weights <= 0).any():
            raise ValueError('Weights must be strictly positive and non-zero.')

        if engine_kwargs is None:
            engine_kwargs = {}

        if minimizer_kwargs is None:
            minimizer_kwargs = {}
        minimizer_kwargs.update(engine_kwargs)

        if tolerance is not None:
            minimizer_kwargs['ftol'] = tolerance
            minimizer_kwargs['xtol'] = tolerance
        if max_evaluations is not None:
            minimizer_kwargs['steps'] = max_evaluations

        if model is None:
            model_function = self._make_model(parameters=parameters)
            model = model_function(x, y, weights)
        self._cached_model = model

        self._p_0 = {f'p{key}': self._cached_pars[key].value for key in self._cached_pars.keys()}

        problem = FitProblem(model)

        method_str = method_dict.get('method', self._method)
        fitclass = self._resolve_fitclass(method_str)

        step_counter = _StepCounterMonitor()
        monitors = [step_counter]
        progress_monitor = None
        if progress_callback is not None:
            progress_monitor = _BumpsProgressMonitor(self, problem, progress_callback)
            monitors.append(progress_monitor)

        abort_test = (lambda: progress_monitor.cancel_requested) if progress_monitor else None

        mapper = SerialMapper.start_mapper(problem, [])
        driver = FitDriver(
            fitclass=fitclass,
            problem=problem,
            monitors=monitors,
            abort_test=abort_test,
            mapper=mapper,
            **minimizer_kwargs,
        )
        driver.clip()

        # Why do we do this? Because a fitting template has to have global_object instantiated outside pre-runtime
        from easyscience import global_object

        stack_status = global_object.stack.enabled
        global_object.stack.enabled = False

        try:
            x_result, fx = driver.fit()
            if progress_monitor is not None and progress_monitor.cancel_requested:
                raise FitCancelled()
            self._set_parameter_fit_result(x_result, driver, stack_status, problem._parameters)
            results = self._gen_fit_results(
                x_result, fx, driver, step_counter.last_step, max_evaluations
            )
        except FitCancelled:
            self._restore_parameter_values()
            raise
        except Exception as e:
            self._restore_parameter_values()
            raise FitError(e)
        finally:
            global_object.stack.enabled = stack_status
        return results

    @staticmethod
    def _resolve_fitclass(method: str):
        for fitclass in FITTERS:
            if fitclass.id == method:
                return fitclass
        raise FitError(f'Unknown BUMPS fitting method: {method}')

    def _build_progress_payload(
        self, problem, iteration: int, point: np.ndarray, nllf: float
    ) -> dict:
        # Use the nllf already computed by the fitter to avoid a costly
        # model re-evaluation.  For Gaussian likelihoods:
        #   nllf = sum(residuals**2) / 2  =>  chi2 = 2 * nllf
        chi2 = 2.0 * nllf
        dof = problem.dof
        reduced_chi2 = chi2 / dof if dof > 0 else chi2

        parameter_values = self._current_parameter_snapshot(problem, point)

        return {
            'iteration': iteration,
            'chi2': chi2,
            'reduced_chi2': reduced_chi2,
            'parameter_values': parameter_values,
            'refresh_plots': False,
            'finished': False,
        }

    def _current_parameter_snapshot(self, problem, point: np.ndarray) -> dict:
        labels = problem.labels()
        values = problem.getp() if point is None else point
        snapshot = {}
        for label, value in zip(labels, values):
            dict_name = label[len(MINIMIZER_PARAMETER_PREFIX) :]
            snapshot[dict_name] = float(value)
        return snapshot

    def convert_to_pars_obj(self, par_list: Optional[List] = None) -> List[BumpsParameter]:
        """Create a container with the `Parameters` converted from the
        base object.

        :param par_list: If only a single/selection of parameter is
            required. Specify as a list
        :type par_list: List[str]
        :return: bumps Parameters list
        :rtype: List[BumpsParameter]
        """
        if par_list is None:
            # Assume that we have a ObjBase for which we can obtain a list
            par_list = self._object.get_fit_parameters()
        pars_obj = [self.__class__.convert_to_par_object(obj) for obj in par_list]
        return pars_obj

    # For some reason I have to double staticmethod :-/
    @staticmethod
    def convert_to_par_object(obj) -> BumpsParameter:
        """Convert an `EasyScience.variable.Parameter` object to a bumps
        Parameter object.

        :return: bumps Parameter compatible object.
        :rtype: BumpsParameter
        """

        value = obj.value

        return BumpsParameter(
            name=MINIMIZER_PARAMETER_PREFIX + obj.unique_name,
            value=value,
            bounds=[obj.min, obj.max],
            fixed=obj.fixed,
        )

    def _make_model(self, parameters: Optional[List[BumpsParameter]] = None) -> Callable:
        """Generate a bumps model from the supplied `fit_function` and
        parameters in the base object. Note that this makes a callable
        as it needs to be initialized with *x*, *y*, *weights*

        Weights are converted to dy (standard deviation of y).

        :return: Callable to make a bumps Curve model
        :rtype: Callable
        """
        fit_func = self._generate_fit_function()

        def _outer(obj):
            def _make_func(x, y, weights):
                bumps_pars = {}
                if not parameters:
                    for name, par in obj._cached_pars.items():
                        bumps_pars[MINIMIZER_PARAMETER_PREFIX + str(name)] = (
                            obj.convert_to_par_object(par)
                        )
                else:
                    for par in parameters:
                        bumps_pars[MINIMIZER_PARAMETER_PREFIX + par.unique_name] = (
                            obj.convert_to_par_object(par)
                        )
                return Curve(fit_func, x, y, dy=1 / weights, **bumps_pars)

            return _make_func

        return _outer(self)

    def _set_parameter_fit_result(
        self,
        x_result: np.ndarray,
        driver: FitDriver,
        stack_status: bool,
        par_list: List[BumpsParameter],
    ):
        """Update parameters to their final values and assign a std
        error to them.

        :param x_result: Optimized parameter values from FitDriver
        :param driver: The FitDriver instance (provides stderr)
        :param stack_status: Whether the undo stack was enabled
        :param par_list: List of BUMPS parameter objects
        """
        from easyscience import global_object

        pars = self._cached_pars
        stderr = driver.stderr()

        if stack_status:
            for name in pars.keys():
                pars[name].value = self._cached_pars_vals[name][0]
                pars[name].error = self._cached_pars_vals[name][1]
            global_object.stack.enabled = True
            global_object.stack.beginMacro('Fitting routine')

        for index, name in enumerate([par.name for par in par_list]):
            dict_name = name[len(MINIMIZER_PARAMETER_PREFIX) :]
            pars[dict_name].value = x_result[index]
            pars[dict_name].error = stderr[index]
        if stack_status:
            global_object.stack.endMacro()

    def _gen_fit_results(
        self,
        x_result: np.ndarray,
        fx: float,
        driver: FitDriver,
        n_evaluations: int = 0,
        max_evaluations: Optional[int] = None,
        **kwargs,
    ) -> FitResults:
        """Convert fit results into the unified `FitResults` format.

        :param x_result: Optimized parameter values from FitDriver
        :param fx: Final objective function value
        :param driver: The FitDriver instance
        :param n_evaluations: Number of iterations completed
        :param max_evaluations: Maximum evaluations budget (if set)
        :return: fit results container
        :rtype: FitResults
        """

        results = FitResults()
        for name, value in kwargs.items():
            if getattr(results, name, False):
                setattr(results, name, value)
        results.n_evaluations = n_evaluations
        # Bumps step counter is 0-indexed, so the last step of a budget of N
        # is N-1.  We therefore compare with ``max_evaluations - 1``.
        if max_evaluations is not None and n_evaluations >= max_evaluations - 1:
            results.success = False
            results.message = f'Maximum number of evaluations ({max_evaluations}) reached'
        else:
            results.success = True
            results.message = 'Optimization terminated successfully'
        pars = self._cached_pars
        item = {}
        for index, name in enumerate(self._cached_model.pars.keys()):
            dict_name = name[len(MINIMIZER_PARAMETER_PREFIX) :]
            item[name] = pars[dict_name].value

        results.p0 = self._p_0
        results.p = item
        results.x = self._cached_model.x
        results.y_obs = self._cached_model.y
        results.y_calc = self.evaluate(results.x, minimizer_parameters=results.p)
        results.y_err = self._cached_model.dy
        results.minimizer_engine = self.__class__
        results.fit_args = None
        results.engine_result = driver
        return results
