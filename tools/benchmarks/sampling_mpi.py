# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Quick benchmark: Bayesian DREAM sampling with multiprocessing.

Runs the same small sampling problem sequentially and with process
workers, printing wall-clock times so you can judge the speedup.

Usage::

    python tools/benchmarks/sampling_mpi.py
"""

import time
import warnings

import numpy as np

from easyscience import Parameter
from easyscience.base_classes import ModelBase
from easyscience.fitting import Sampler
from easyscience.fitting import SamplingResults

# -- simple test model --------------------------------------------------------

# Simulate an expensive model by adding a configurable CPU burn per evaluation.
# Set to 0.0 for the trivial model; try 0.02-0.1 to see the multiprocessing speedup.
_MODEL_DELAY = 0.09  # seconds of CPU work per model call


class Line(ModelBase):
    def __init__(self, m_val: float, c_val: float):
        super().__init__(display_name='line')
        self._m = Parameter(m_val, display_name='m', fixed=False)
        self._c = Parameter(c_val, display_name='c', fixed=False)

    @property
    def m(self) -> Parameter:
        return self._m

    @property
    def c(self) -> Parameter:
        return self._c

    def __call__(self, x: np.ndarray) -> np.ndarray:
        if _MODEL_DELAY > 0:
            # burn CPU to simulate a real physics model
            t0 = time.perf_counter()
            while time.perf_counter() - t0 < _MODEL_DELAY:
                _ = np.sum(np.sin(x) ** 2 + np.cos(x) ** 2)
        return self.m.value * x + self.c.value


# -- helpers ------------------------------------------------------------------


def run_sample(n_workers: int | None, **sample_kwargs) -> tuple[SamplingResults, float]:
    """Run one DREAM sampling call and return (results, wall_seconds)."""
    x = np.linspace(0, 10, 60)
    y_true = 2.5 * x + 1.3
    rng = np.random.default_rng(42)
    y = y_true + rng.normal(0, 0.3, size=x.shape)
    weights = np.full_like(x, 1.0 / 0.3)

    model = Line(2.0, 1.0)
    sampler = Sampler(model, model, x, y, weights)

    t0 = time.perf_counter()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        results = sampler.sample(n_workers=n_workers, **sample_kwargs)
    elapsed = time.perf_counter() - t0
    return results, elapsed


def summarise(label: str, results: SamplingResults, elapsed: float) -> None:
    print(
        f'  {label:>12s}  {elapsed:6.2f} s  '
        f'draws shape {results.draws.shape}  '
        f'params: {results.param_names}'
    )


# -- main ---------------------------------------------------------------------


def main() -> None:
    # population=5 with 2 parameters gives 10 chains, so up to 10 workers help.
    sample_kwargs = dict(samples=200, burn=50, thin=2, population=5)

    print('Bayesian multiprocessing quick test')
    print('-----------------------------------')
    print(f'  config: {sample_kwargs}, model delay {_MODEL_DELAY} s')
    print()

    timings = {}
    for label, n_workers in [
        ('sequential', None),
        ('n_workers=1', 1),
        ('n_workers=2', 2),
        ('n_workers=4', 4),
    ]:
        results, elapsed = run_sample(n_workers=n_workers, **sample_kwargs)
        summarise(label, results, elapsed)
        timings[label] = elapsed

    print()
    t_seq = timings['sequential']
    for label in ('n_workers=2', 'n_workers=4'):
        ratio = t_seq / timings[label]
        tag = f'{ratio:.1f}x speedup' if ratio > 1 else f'{1 / ratio:.1f}x slower'
        print(f'  {label:>12s}  {tag}  (seq {t_seq:.2f}s -> {timings[label]:.2f}s)')


if __name__ == '__main__':
    main()
