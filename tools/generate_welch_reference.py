"""Development-only SciPy oracle; no database or network use.

Run with a Python environment containing numpy/scipy to regenerate the checked-in
reference values used by the browser-side numerical tests.
"""
import json
from pathlib import Path
import numpy as np
import scipy
from scipy.stats import ttest_ind_from_stats


def moments(counts):
    counts = np.asarray(counts, dtype=float)
    values = np.arange(1, 6)
    n = float(counts.sum())
    mean = float((counts * values).sum() / n)
    variance = float((counts * (values - mean) ** 2).sum() / (n - 1))
    return {'n': int(n), 'mean': mean, 'variance': variance}


def main():
    histograms = [
        ([0, 1, 3, 10, 25], [3, 8, 12, 10, 4]),
        ([1, 0, 0, 0, 1], [0, 1, 1, 0, 0]),
        ([0, 0, 0, 5, 5], [0, 0, 0, 5, 5]),
        ([0, 0, 0, 0, 25], [0, 0, 1, 5, 20]),
        ([0, 0, 0, 69980000, 30020000], [0, 0, 0, 70020000, 29980000]),
    ]
    random = np.random.default_rng(20261004)
    for _ in range(100):
        left_n, right_n = random.integers(2, 10000, size=2)
        histograms.append((random.multinomial(left_n, random.dirichlet(np.ones(5))).tolist(),
                           random.multinomial(right_n, random.dirichlet(np.ones(5))).tolist()))
    cases = []
    for left_counts, right_counts in histograms:
        left, right = moments(left_counts), moments(right_counts)
        if not left['variance'] and not right['variance']:
            continue
        expected = ttest_ind_from_stats(left['mean'], np.sqrt(left['variance']), left['n'],
                                        right['mean'], np.sqrt(right['variance']), right['n'],
                                        equal_var=False, alternative='two-sided')
        cases.append({'left': left, 'right': right, 't': float(expected.statistic), 'pValue': float(expected.pvalue)})
    destination = Path(__file__).resolve().parents[1] / 'frontend/src/utils/welchReference.json'
    destination.write_text(json.dumps({'generator': f'SciPy {scipy.__version__}, ttest_ind_from_stats(equal_var=False, alternative="two-sided")', 'cases': cases}, indent=2) + '\n')
    print(f'Wrote {len(cases)} independent reference cases to {destination}')


if __name__ == '__main__':
    main()
