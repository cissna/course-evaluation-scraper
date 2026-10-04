import { compareSamples, isValidThreshold, toggleRowSelection } from './significance';
import reference from './welchReference.json';
import { processAnalysisRequest } from './analysisEngine';

test('two-sided Welch results match independently generated SciPy reference values', () => {
  expect(reference.cases.length).toBeGreaterThan(100);
  for (const expected of reference.cases) {
    const actual = compareSamples(expected.left, expected.right);
    expect(actual.available).toBe(true);
    expect(actual.t).toBeCloseTo(expected.t, 10);
    expect(actual.pValue).toBeCloseTo(expected.pValue, 8);
    expect(actual.significant).toBe(expected.pValue < 0.05);
    expect(compareSamples(expected.right, expected.left).pValue).toBeCloseTo(expected.pValue, 8);
  }
});

test('sample moments are used even when both table means round to the same score', () => {
  const example = reference.cases[4];
  expect(example.left.mean.toFixed(2)).toBe(example.right.mean.toFixed(2));
  expect(compareSamples(example.left, example.right).significant).toBe(true);
});

test('overlapping contributing source records are unavailable, regardless of names or scores', () => {
  const sample = { mean: 4, variance: 0.5, n: 30, source_ids: ['course-section-term'] };
  expect(compareSamples(sample, { ...sample, mean: 1 }).reason).toBe('these groups share evaluations.');
  expect(compareSamples(sample, { ...sample, source_ids: ['another-section'] }).available).toBe(true);
});

test('overlap is checked for contributions to the currently selected metric after filtering', () => {
  const common = { instructor_name: 'Jane Smith', overall_quality_frequency: { Good: 5 }, workload_frequency: { 'N/A': 5 } };
  const make = (uniqueKey, counts) => ({ instances: {
    'shared.SP25': common,
    [uniqueKey]: { instructor_name: 'Jane Smith', workload_frequency: counts },
  }, metadata: {} });
  const options = { stats: { overall_quality: true, workload: true }, filters: {} };
  const a = processAnalysisRequest(make('a.SP24', { Typical: 5, 'Much heavier': 5 }), options).statistics_metadata['All Data'];
  const b = processAnalysisRequest(make('b.SP24', { 'Much lighter': 10, Typical: 5 }), options).statistics_metadata['All Data'];
  expect(compareSamples(a.overall_quality, b.overall_quality).reason).toBe('these groups share evaluations.');
  expect(compareSamples(a.workload, b.workload).available).toBe(true);
  const filtered = processAnalysisRequest(make('a.SP24', { Typical: 5 }), { ...options, filters: { max_year: 2024 } });
  expect(filtered.statistics_metadata['All Data'].overall_quality.source_ids).toEqual([]);
});

test('insufficient responses and two zero variances are unavailable; one zero variance is supported', () => {
  const sample = { n: 10, mean: 4, variance: 0.5 };
  expect(compareSamples(sample, { ...sample, n: 1 }).reason).toMatch(/two valid responses/);
  expect(compareSamples({ ...sample, variance: 0 }, { ...sample, mean: 5, variance: 0 }).reason).toMatch(/zero variance/);
  expect(compareSamples(sample, { ...sample, variance: 0 }).available).toBe(true);
});

test('threshold uses strict p < threshold, and invalid thresholds cannot produce gold', () => {
  const a = { n: 10, mean: 3, variance: 1 }, b = { n: 12, mean: 4, variance: 2 };
  const { pValue } = compareSamples(a, b);
  expect(compareSamples(a, b, pValue).significant).toBe(false);
  expect(compareSamples(a, b, pValue + 0.00001).significant).toBe(true);
  for (const invalid of ['', 0, 1, -1, 'oops', NaN]) {
    expect(isValidThreshold(invalid)).toBe(false);
    expect(compareSamples(a, b, invalid).significant).toBe(false);
  }
});

test('third selection replaces the oldest and clicking a selected row deselects it', () => {
  const a = { resultId: 'a', groupName: 'All Data' }, b = { resultId: 'b', groupName: 'All Data' }, c = { resultId: 'c', groupName: 'All Data' };
  expect(toggleRowSelection([a, b], c)).toEqual([b, c]);
  expect(toggleRowSelection([a, b], a)).toEqual([b]);
  expect(toggleRowSelection([a], a)).toEqual([]);
});
