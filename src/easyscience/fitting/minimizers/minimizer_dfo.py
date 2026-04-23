# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import warnings
from dataclasses import dataclass
from numbers import Integral
from typing import Callable
from typing import Dict
from typing import List

import dfols
import numpy as np

# causes circular import when Parameter is imported
# from easyscience.base_classes import ObjBase
from easyscience.variable import Parameter

from ..available_minimizers import AvailableMinimizers
from .minimizer_base import MINIMIZER_PARAMETER_PREFIX
from .minimizer_base import MinimizerBase
from .utils import FitError
from .utils import FitResults


@dataclass(frozen=True)
class DFOCallbackState:
    """Snapshot of a DFO objective evaluation."""

    evaluation: int
    xk: np.ndarray
    residuals: np.ndarray
    objective: float
    parameters: dict[str, float]
    best_xk: np.ndarray
    best_objective: float
    best_parameters: dict[str, float]
    improved: bool


class DFO(MinimizerBase):
    """
    This is a wrapper to Derivative Free Optimisation for Least Square: https://numericalalgorithmsgroup.github.io/dfols/
    """

    package = 'dfo'

    def __init__(
        self,
        obj,  #: ObjBase,
        fit_function: Callable,
        minimizer_enum: AvailableMinimizers | None = None,
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
    def supported_methods() -> List[str]:
        return ['leastsq']

    @staticmethod
    def all_methods() -> List[str]:
        return ['leastsq']

    def fit(
        self,
        x: np.ndarray,
        y: np.ndarray,
        weights: np.ndarray,
        model: Callable | None = None,
        parameters: List[Parameter] | None = None,
        method: str | None = None,
        tolerance: float | None = None,
        max_evaluations: int | None = None,
        progress_callback: Callable[[dict], bool | None] | None = None,
        callback: Callable[[DFOCallbackState], None] | None = None,
        callback_every: int = 1,
        callback_on_improvement_only: bool = False,
        **kwargs,
    ) -> FitResults:
        """Perform a fit using the DFO-ls engine.

        :param x: points to be calculated at
        :type x: np.ndarray
        :param y: measured points
        :type y: np.ndarray
        :param weights: Weights for supplied measured points.
        :type weights: np.ndarray
        :param model: Optional Model which is being fitted to
        :type model: lmModel
        :param parameters: Optional parameters for the fit
        :type parameters: List[bumpsParameter]
        :param kwargs: Additional arguments for the fitting function.
        :param method: Method for minimization
        :type method: str
        :return: Fit results
        :rtype: ModelResult For standard least squares, the weights
            should be 1/sigma, where sigma is the standard deviation of
            the measurement. For unweighted least squares, these should
            be 1.
        """
        x, y, weights = np.asarray(x), np.asarray(y), np.asarray(weights)

        if y.shape != x.shape:
            raise ValueError('x and y must have the same shape.')

        if weights.shape != x.shape:
            raise ValueError('Weights must have the same shape as x and y.')

        if not np.isfinite(weights).all():
            raise ValueError('Weights cannot be NaN or infinite.')

        if (weights <= 0).any():
            raise ValueError('Weights must be strictly positive and non-zero.')

        if not isinstance(callback_every, Integral) or isinstance(callback_every, bool):
            raise ValueError('callback_every must be a positive integer.')

        if callback_every < 1:
            raise ValueError('callback_every must be a positive integer.')

        # Bridge progress_callback into the DFO callback mechanism
        if progress_callback is not None and callback is None:
            dof = max(len(x) - len(self._cached_pars), 1)
            callback = self._make_progress_adapter(progress_callback, dof)

        if model is None:
            model_function = self._make_model(
                parameters=parameters,
                callback=callback,
                callback_every=callback_every,
                callback_on_improvement_only=callback_on_improvement_only,
            )
            model = model_function(x, y, weights)
        elif callback is not None:
            model = self._wrap_model_with_callback(
                model,
                self._get_callback_parameter_names(parameters),
                callback,
                callback_every,
                callback_on_improvement_only,
            )
        self._cached_model = model
        self._cached_model.x = x
        self._cached_model.y = y

        self._p_0 = {f'p{key}': self._cached_pars[key].value for key in self._cached_pars.keys()}

        # Why do we do this? Because a fitting template has to have global_object instantiated outside pre-runtime
        from easyscience import global_object

        stack_status = global_object.stack.enabled
        global_object.stack.enabled = False

        kwargs = self._prepare_kwargs(tolerance, max_evaluations, **kwargs)

        try:
            model_results = self._dfo_fit(self._cached_pars, model, **kwargs)
            self._set_parameter_fit_result(model_results, stack_status)
            results = self._gen_fit_results(model_results, weights)
        except FitError:
            self._restore_parameter_values()
            raise
        except Exception as e:
            self._restore_parameter_values()
            raise FitError(e)
        finally:
            global_object.stack.enabled = stack_status
        return results

    def convert_to_pars_obj(self, par_list: List[Parameter] | None = None):
        """Required by interface but not needed for DFO-LS."""
        pass

    @staticmethod
    def convert_to_par_object(obj) -> None:
        """Required by interface but not needed for DFO-LS."""
        pass

    def _make_model(
        self,
        parameters: List[Parameter] | None = None,
        callback: Callable[[DFOCallbackState], None] | None = None,
        callback_every: int = 1,
        callback_on_improvement_only: bool = False,
    ) -> Callable:
        """Generate a model from the supplied `fit_function` and
        parameters in the base object. Note that this makes a callable
        as it needs to be initialized with *x*, *y*, *weights*

        :return: Callable model which returns residuals
        :rtype: Callable
        """
        fit_func = self._generate_fit_function()

        def _outer(obj: DFO):
            def _make_func(x, y, weights):
                dfo_pars = {}
                if not parameters:
                    for name, par in obj._cached_pars.items():
                        dfo_pars[MINIMIZER_PARAMETER_PREFIX + str(name)] = par.value
                else:
                    for par in parameters:
                        dfo_pars[MINIMIZER_PARAMETER_PREFIX + par.unique_name] = par.value

                def _residuals(pars_values: List[float]) -> np.ndarray:
                    for idx, par_name in enumerate(dfo_pars.keys()):
                        dfo_pars[par_name] = pars_values[idx]
                    return (y - fit_func(x, **dfo_pars)) * weights

                return obj._wrap_model_with_callback(
                    _residuals,
                    list(dfo_pars.keys()),
                    callback,
                    callback_every,
                    callback_on_improvement_only,
                )

            return _make_func

        return _outer(self)

    def _get_callback_parameter_names(
        self, parameters: List[Parameter] | None = None
    ) -> list[str]:
        if parameters is not None:
            return [MINIMIZER_PARAMETER_PREFIX + parameter.unique_name for parameter in parameters]
        return [MINIMIZER_PARAMETER_PREFIX + name for name in self._cached_pars.keys()]

    @staticmethod
    def _wrap_model_with_callback(
        model: Callable,
        parameter_names: list[str],
        callback: Callable[[DFOCallbackState], None] | None,
        callback_every: int,
        callback_on_improvement_only: bool,
    ) -> Callable:
        if callback is None:
            return model

        evaluation = 0
        best_objective = np.inf
        best_xk = np.array([], dtype=float)
        best_parameters: dict[str, float] = {}

        def wrapped_model(pars_values: List[float]) -> np.ndarray:
            nonlocal evaluation, best_objective, best_xk, best_parameters

            residuals = np.asarray(model(pars_values), dtype=float)
            xk = np.asarray(pars_values, dtype=float).copy()
            parameters = {name: value for name, value in zip(parameter_names, xk)}
            objective = float(np.dot(residuals.ravel(), residuals.ravel()))

            evaluation += 1
            improved = objective < best_objective
            if improved:
                best_objective = objective
                best_xk = xk.copy()
                best_parameters = parameters.copy()

            should_notify = evaluation % callback_every == 0
            if callback_on_improvement_only:
                should_notify = should_notify and improved

            if should_notify:
                callback(
                    DFOCallbackState(
                        evaluation=evaluation,
                        xk=xk,
                        residuals=residuals.copy(),
                        objective=objective,
                        parameters=parameters,
                        best_xk=best_xk.copy(),
                        best_objective=best_objective,
                        best_parameters=best_parameters.copy(),
                        improved=improved,
                    )
                )

            return residuals

        return wrapped_model

    @staticmethod
    def _make_progress_adapter(
        progress_callback: Callable[[dict], bool | None],
        dof: int,
    ) -> Callable[['DFOCallbackState'], None]:
        """Create a DFO callback that translates DFOCallbackState into
        the standard progress_callback dict format used by the GUI.

        :param progress_callback: Standard progress callback (dict ->
            bool|None)
        :param dof: Degrees of freedom for reduced chi2 calculation
        :return: DFO-compatible callback
        """

        def adapter(state: 'DFOCallbackState') -> None:
            chi2 = state.best_objective
            reduced_chi2 = chi2 / dof if dof > 0 else chi2
            param_snapshot = {
                name[len(MINIMIZER_PARAMETER_PREFIX) :]: float(val)
                for name, val in state.best_parameters.items()
            }
            payload = {
                'iteration': state.evaluation,
                'chi2': chi2,
                'reduced_chi2': reduced_chi2,
                'parameter_values': param_snapshot,
                'refresh_plots': False,
                'finished': False,
            }
            progress_callback(payload)

        return adapter

    def _set_parameter_fit_result(self, fit_result, stack_status, ci: float = 0.95) -> None:
        """Update parameters to their final values and assign a std
        error to them.

        :param fit_result: Fit object which contains info on the fit
        :param ci: Confidence interval for calculating errors. Default
            95%
        :return: None
        :rtype: noneType
        """
        from easyscience import global_object

        pars = self._cached_pars
        if stack_status:
            self._restore_parameter_values()
            global_object.stack.enabled = True
            global_object.stack.beginMacro('Fitting routine')

        error_matrix = self._error_from_jacobian(fit_result.jacobian, fit_result.resid, ci)
        for idx, par in enumerate(pars.values()):
            par.value = fit_result.x[idx]
            par.error = error_matrix[idx, idx]

        if stack_status:
            global_object.stack.endMacro()

    def _gen_fit_results(self, fit_results, weights, **kwargs) -> FitResults:
        """Convert fit results into the unified `FitResults` format.

        :param fit_result: Fit object which contains info on the fit
        :return: fit results container
        :rtype: FitResults
        """

        results = FitResults()
        for name, value in kwargs.items():
            if getattr(results, name, False):
                setattr(results, name, value)
        # DFO-LS stores fixed exit-code constants on each result object;
        # EXIT_SUCCESS is 0 and EXIT_MAXFUN_WARNING keeps a different flag value.
        results.success = fit_results.flag == fit_results.EXIT_SUCCESS

        pars = {}
        for p_name, par in self._cached_pars.items():
            pars[f'p{p_name}'] = par.value
        results.p = pars

        results.p0 = self._p_0
        results.x = self._cached_model.x
        results.y_obs = self._cached_model.y
        results.y_calc = self.evaluate(results.x, minimizer_parameters=results.p)
        results.y_err = weights
        results.n_evaluations = int(fit_results.nf)
        results.message = str(fit_results.msg)
        if not results.success:
            warning_message = results.message or 'DFO fit did not succeed.'
            warnings.warn(warning_message, UserWarning, stacklevel=2)
        # results.residual = results.y_obs - results.y_calc
        # results.goodness_of_fit = fit_results.f

        results.minimizer_engine = self.__class__
        results.fit_args = None
        results.engine_result = fit_results
        # results.check_sanity()

        return results

    @staticmethod
    def _dfo_fit(
        pars: Dict[str, Parameter],
        model: Callable,
        **kwargs,
    ):
        """Method to convert EasyScience styling to DFO-LS styling (yes,
        again)

        :param model: Model which accepts f(x[0])
        :type model: Callable
        :param kwargs: Any additional arguments for dfols.solver
        :type kwargs: dict
        :return: dfols fit results container
        """

        pars_values = np.array([par.value for par in pars.values()])

        bounds = (
            np.array([par.min for par in pars.values()]),
            np.array([par.max for par in pars.values()]),
        )
        # https://numericalalgorithmsgroup.github.io/dfols/build/html/userguide.html
        if not np.isinf(bounds).any():
            # It is only possible to scale (normalize) variables if they are bound (different from inf)
            kwargs['scaling_within_bounds'] = True

        results = dfols.solve(model, pars_values, bounds=bounds, **kwargs)

        # DFO-LS uses EXIT_MAXFUN_WARNING when it stops on the evaluation budget;
        # we still return the partial fit result and let the unified result mark it as non-success.
        if results.flag in {results.EXIT_SUCCESS, results.EXIT_MAXFUN_WARNING}:
            return results

        raise FitError(f'Fit failed with message: {results.msg}')

    @staticmethod
    def _prepare_kwargs(
        tolerance: float | None = None,
        max_evaluations: int | None = None,
        **kwargs,
    ) -> dict[str:str]:
        if max_evaluations is not None:
            kwargs['maxfun'] = max_evaluations  # max number of function evaluations
        if tolerance is not None:
            if 0.1 < tolerance:  # dfo module throws errer if larger value
                raise ValueError('Tolerance must be equal or smaller than 0.1')
            kwargs['rhoend'] = tolerance  # size of the trust region
        return kwargs
