# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Scaling example: Bayesian DREAM sampling from 1 to 16 CPU cores.

Samples the posterior of a Gaussian peak on a linear background (four
free parameters) with an artificially expensive model, once for each
worker count, and reports wall-clock time, speedup and parallel
efficiency relative to one core.

Every run draws the same number of samples from the same problem, so
the posterior means should agree between runs; only the time changes.

Usage::

    python tools/benchmarks/sampling_scaling.py
    python tools/benchmarks/sampling_scaling.py --workers 1 2 4 8 16 --delay 0.05
    python tools/benchmarks/sampling_scaling.py --plot scaling.png

Notes
-----
* Worker counts above ``os.cpu_count()`` are skipped.
* DREAM evaluates one generation (one point per chain) at a time, and
  ``n_workers`` is capped at the number of chains, so the chain count
  must be at least the largest worker count. With 4 parameters and the
  default ``--population 16`` there are 64 chains, which split evenly
  over 1, 2, 4, 8 and 16 workers. When they do not split evenly (e.g.
  12 workers), every generation waits for the busiest worker.
* The chains are deliberately short, so the posterior means are not
  converged and differ between runs by more than their statistical
  noise. This script measures time, not the posterior.
* The timings include starting the worker pool (the ``spawn`` start
  method launches fresh Python processes), which is why the speedup is
  below the ideal for cheap models or short runs.
"""

import argparse
import math
import os
import time
import warnings

import numpy as np

from easyscience import Parameter
from easyscience.base_classes import ModelBase
from easyscience.fitting import Sampler
from easyscience.fitting import SamplingResults

# -- test system --------------------------------------------------------------


class GaussianPeak(ModelBase):
    """Gaussian peak on a linear background, with a tunable evaluation cost.

    ``delay`` seconds of CPU work are burned on every call to mimic an
    expensive physics model (e.g. a numerical integral or a simulation).
    """

    def __init__(self, delay: float = 0.02):
        super().__init__(display_name='gaussian_peak')
        self._delay = delay
        self._area = Parameter(8.0, display_name='area', fixed=False, min=0.0, max=50.0)
        self._center = Parameter(0.3, display_name='center', fixed=False, min=-3.0, max=3.0)
        self._width = Parameter(1.2, display_name='width', fixed=False, min=0.05, max=5.0)
        self._background = Parameter(
            0.5, display_name='background', fixed=False, min=-5.0, max=5.0
        )

    @property
    def area(self) -> Parameter:
        return self._area

    @property
    def center(self) -> Parameter:
        return self._center

    @property
    def width(self) -> Parameter:
        return self._width

    @property
    def background(self) -> Parameter:
        return self._background

    def __call__(self, x: np.ndarray) -> np.ndarray:
        if self._delay > 0:
            t0 = time.perf_counter()
            while time.perf_counter() - t0 < self._delay:
                _ = np.sum(np.sin(x) ** 2 + np.cos(x) ** 2)
        norm = self.area.value / (self.width.value * math.sqrt(2 * math.pi))
        peak = norm * np.exp(-0.5 * ((x - self.center.value) / self.width.value) ** 2)
        return peak + self.background.value


def make_data(seed: int = 7) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Synthetic data from known parameters plus Gaussian noise."""
    truth = GaussianPeak(delay=0.0)
    truth.area.value = 10.0
    truth.center.value = 0.0
    truth.width.value = 1.0
    truth.background.value = 1.0

    x = np.linspace(-5.0, 5.0, 120)
    sigma = 0.1
    y = truth(x) + np.random.default_rng(seed).normal(0.0, sigma, size=x.shape)
    weights = np.full_like(x, 1.0 / sigma)
    return x, y, weights


PARAMETER_ORDER = ('area', 'center', 'width', 'background')


# -- benchmark ----------------------------------------------------------------


def run(
    n_workers: int, delay: float, samples: int, burn: int, population: float
) -> tuple[SamplingResults, dict[str, float], float]:
    """Run one sampling call.

    Returns the results, the posterior mean of each parameter keyed by
    its display name, and the wall-clock time in seconds.
    """
    x, y, weights = make_data()
    model = GaussianPeak(delay=delay)
    sampler = Sampler(model, model, x, y, weights)

    t0 = time.perf_counter()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        results = sampler.sample(
            samples=samples,
            burn=burn,
            thin=1,
            population=population,
            n_workers=n_workers,
        )
    elapsed = time.perf_counter() - t0

    names = {p.unique_name: p.display_name for p in model.get_fit_parameters()}
    means = {
        names[name]: mean for name, mean in zip(results.param_names, results.draws.mean(axis=0))
    }
    return results, means, elapsed


def plot(worker_counts: list[int], times: list[float], path: str) -> None:
    """Save a speedup plot next to the ideal linear speedup."""
    import matplotlib.pyplot as plt

    speedups = [times[0] / t for t in times]
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot(worker_counts, worker_counts, 'k--', lw=1, label='ideal')
    ax.plot(worker_counts, speedups, 'o-', label='measured')
    ax.set(xlabel='n_workers', ylabel=f'speedup vs {worker_counts[0]} worker(s)')
    ax.set_xticks(worker_counts)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    print(f'\nSaved plot to {path}')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument(
        '--workers',
        type=int,
        nargs='+',
        default=[1, 2, 4, 8, 12, 16],
        help='worker counts to benchmark (default: 1 2 4 8 12 16)',
    )
    parser.add_argument(
        '--delay', type=float, default=0.02, help='seconds of CPU work per model call'
    )
    parser.add_argument('--samples', type=int, default=800, help='raw DREAM samples')
    parser.add_argument('--burn', type=int, default=20, help='burn-in generations')
    parser.add_argument(
        '--population', type=float, default=16, help='DREAM population scale factor'
    )
    parser.add_argument('--plot', metavar='PNG', help='save a speedup plot to this file')
    args = parser.parse_args()

    n_params = len(PARAMETER_ORDER)
    n_chains = math.ceil(args.population * n_params)
    n_cpus = os.cpu_count() or 1
    worker_counts = sorted({w for w in args.workers if 1 <= w <= n_cpus})
    skipped = sorted(set(args.workers) - set(worker_counts))

    # DREAM runs in blocks of 10 generations (see the Sampler documentation).
    generations = args.burn + 10 * math.ceil(args.samples / n_chains / 10)
    evaluations = generations * n_chains

    print('Bayesian DREAM sampling: scaling with the number of worker processes')
    print('=' * 70)
    print(f'  CPU cores available : {n_cpus}')
    print(f'  model cost          : {args.delay * 1000:.0f} ms per evaluation')
    print(f'  chains              : {n_chains} ({n_params} parameters x {args.population:g})')
    print(f'  model evaluations   : ~{evaluations} ({generations} generations)')
    print(f'  sequential estimate : ~{evaluations * args.delay:.0f} s')
    if skipped:
        print(f'  skipped worker counts (more than {n_cpus} cores): {skipped}')
    if worker_counts and worker_counts[-1] > n_chains:
        print(f'  note: n_workers is capped at {n_chains} chains')
    print()

    header = (
        f'{"workers":>8s} {"time [s]":>9s} {"speedup":>8s} {"efficiency":>11s}   '
        f'posterior means (area, center, width, background)'
    )
    print(header)
    print('-' * len(header))

    times = []
    for n_workers in worker_counts:
        _, means, elapsed = run(n_workers, args.delay, args.samples, args.burn, args.population)
        times.append(elapsed)
        speedup = times[0] / elapsed
        efficiency = speedup / (n_workers / worker_counts[0])
        means_str = ', '.join(f'{means[name]:6.3f}' for name in PARAMETER_ORDER)
        print(
            f'{n_workers:>8d} {elapsed:>9.2f} {speedup:>7.2f}x {efficiency:>10.0%}   {means_str}'
        )

    print()
    print('Posterior means differ between runs because these chains are short and')
    print('not converged; this script measures time, not the posterior.')

    if args.plot and len(times) > 1:
        plot(worker_counts, times, args.plot)


if __name__ == '__main__':
    main()
