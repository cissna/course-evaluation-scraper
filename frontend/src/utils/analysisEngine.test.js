import { processAnalysisRequest, calculateDetailedStatistics } from './analysisEngine';
import { RATING_MAPPINGS } from './statsMapping';
import { lookupPercentile, ordinal } from './percentiles';
import { toggleSeparation } from './separationOptions';
import { convertToCSV } from './csvExport';

const record = (name = 'Jane Smith', extra = {}) => ({ instructor_name: name, course_name: 'Course', overall_quality_frequency: { Poor: 1, Excellent: 2, 'N/A': 100 }, ...extra });
const params = { stats: { overall_quality: true, periods_course_has_been_run: true }, filters: {}, separationKeys: [] };
const raw = { instances: {
  'EN.601.415.01.SP20': record(),
  'EN.601.415.01.SU21': record('J. Smith'),
  'EN.601.615.01.FA23': record('Jane Smith & Dana Lee'),
  'AS.180.101.01.IN24': record(),
}, metadata: {} };

test('exact professor scope includes teams and excludes name variants', () => {
  const result = processAnalysisRequest(raw, { ...params, scope: { type: 'professor', name: 'Jane Smith' } });
  expect(result.statistics_metadata['All Data'].overall_quality.n).toBe(9);
  expect(result.data['All Data'].periods_course_has_been_run).not.toContain('SU21');
});

test('year-only empty state retains all other filters and exact professor scope', () => {
  const result = processAnalysisRequest(raw, { ...params, filters: { min_year: 2025, exclude_intersession: true }, scope: { type: 'professor', name: 'Jane Smith' } });
  expect(result.year_range_empty).toEqual({ min_year: 2025, max_year: null, available_years: [2020, 2023] });
  const seasons = processAnalysisRequest(raw, { ...params, filters: { min_year: 2025, seasons: ['Summer'], exclude_summer: true } });
  expect(seasons.year_range_empty).toBeNull();
});

test('null statistics and non-year emptiness remain visible instead of a year popup', () => {
  const nullData = { instances: { 'AS.180.101.01.SP25': { instructor_name: 'Jane Smith' } }, metadata: {} };
  const result = processAnalysisRequest(nullData, { ...params, filters: { min_year: 2020 } });
  expect(result.year_range_empty).toBeNull();
  expect(result.data['All Data'].overall_quality).toBeNull();
  expect(processAnalysisRequest(nullData, { ...params, filters: { min_year: 2026 } }).year_range_empty).toBeNull();
  expect(processAnalysisRequest(raw, { ...params, filters: { instructors: ['Nobody'], min_year: 2025 } }).year_range_empty).toBeNull();
});

test('empty range lists unique years ascending and recovers without changing selected filters', () => {
  const empty = processAnalysisRequest(raw, { ...params, filters: { max_year: 2019 } });
  expect(empty.year_range_empty.available_years).toEqual([2020, 2021, 2023, 2024]);
  expect(processAnalysisRequest(raw, { ...params, filters: { max_year: 2021 } }).year_range_empty).toBeNull();
});

test('summer and intersession exclusions are independent', () => {
  for (const [filters, n] of [[{ exclude_summer: true }, 9], [{ exclude_intersession: true }, 9], [{ exclude_summer: true, exclude_intersession: true }, 6]]) {
    expect(processAnalysisRequest(raw, { ...params, filters }).statistics_metadata['All Data'].overall_quality.n).toBe(n);
  }
});

test('course code does not add redundant grouping components to a single-code result', () => {
  const single = { ...raw, instances: { 'EN.601.415.01.SP20': record() } };
  expect(Object.keys(processAnalysisRequest(single, { ...params, separationKeys: ['course_code'] }).data)).toEqual(['All Data']);
  expect(Object.keys(processAnalysisRequest(single, { ...params, separationKeys: ['instructor', 'course_code'] }).data)).toEqual(['Jane Smith']);
});

test('course groups, course codes, and historical titles have different grouping keys', () => {
  const grouped = { instances: {
    a: record('Jane Smith', { course_code: 'EN.553.431', course_group_id: 'stats', course_group: 'EN.553.431/EN.553.631', course_name: 'Old title' }),
    b: record('Jane Smith', { course_code: 'EN.553.631', course_group_id: 'stats', course_group: 'EN.553.431/EN.553.631', course_name: 'New title' }),
    c: record('Jane Smith', { course_code: 'AS.180.101', course_group_id: 'psych', course_group: 'AS.180.101', course_name: 'New title' }),
  }, metadata: {} };
  const scope = { type: 'professor', name: 'Jane Smith' };
  expect(Object.keys(processAnalysisRequest(grouped, { ...params, scope, separationKeys: ['course_group'] }).data)).toEqual(['EN.553.431/EN.553.631', 'AS.180.101']);
  expect(Object.keys(processAnalysisRequest(grouped, { ...params, scope, separationKeys: ['course_code'] }).data)).toHaveLength(3);
  expect(Object.keys(processAnalysisRequest(grouped, { ...params, scope, separationKeys: ['course_name'] }).data)).toEqual(['Old title', 'New title']);
  expect(toggleSeparation(['course_group', 'course_name'], 'course_code')).toEqual(['course_name', 'course_code']);
});

test('statistics retain full-precision moments without expanding responses', () => {
  const details = calculateDetailedStatistics({ Poor: 1, Excellent: 2, 'N/A': 50, Weak: -1, Good: '2' }, RATING_MAPPINGS.overall_quality);
  expect(details.n).toBe(3);
  expect(details.mean).toBeCloseTo(11 / 3, 14);
  expect(details.variance).toBeCloseTo(16 / 3, 14);
  expect(calculateDetailedStatistics({ Good: 10000000 }, RATING_MAPPINGS.overall_quality).n).toBe(10000000);
});

test('fixed percentile lookup uses midranks and handles ties, missing metrics and ordinal endings', () => {
  const benchmark = { metrics: { overall_quality: { scores: [1, 3, 3, 5] } } };
  expect(lookupPercentile(3, 'overall_quality', benchmark).percentile).toBe(50);
  expect(lookupPercentile(5, 'overall_quality', benchmark).percentile).toBe(87.5);
  expect(lookupPercentile(null, 'overall_quality', benchmark).percentile).toBeNull();
  expect(lookupPercentile(4, 'workload', benchmark).percentile).toBeNull();
  expect([1, 2, 3, 11, 12, 13, 21, 87, 100].map(ordinal)).toEqual(['1st', '2nd', '3rd', '11th', '12th', '13th', '21st', '87th', '100th']);
});

test('CSV includes selected optional columns, tooltip data, and escaped text', () => {
  const group = 'A, "quoted"\nname';
  const data = { [group]: { overall_quality: 4.3, periods_course_has_been_run: 'SP23, FA24' } };
  const details = { [group]: { overall_quality: { n: 10, std: 0.42, mean: 4.3, percentile: 87, benchmark_years: '2015–2026' } } };
  const csv = convertToCSV(data, ['overall_quality', 'periods_course_has_been_run'], details, true);
  expect(csv).toContain('"Periods Course Has Been Run"');
  expect(csv).toContain('"SP23, FA24"');
  expect(csv).toContain('"A, ""quoted""\nname"');
  expect(csv).toContain('"87th","4.3","87th percentile","10","0.42","2015–2026"');
  expect(csv).toContain('sample standard deviation');
  expect(csv).not.toContain('Workload');
});
