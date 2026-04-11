import { processAnalysisRequest } from './analysisEngine';

describe('analysisEngine chronological term ordering', () => {
  const rawData = {
    instances: {
      'AS.180.101.01.FA24': { instructor_name: 'A' },
      'AS.180.101.01.SP24': { instructor_name: 'A' },
      'AS.180.101.01.IN24': { instructor_name: 'A' },
      'AS.180.101.01.SU24': { instructor_name: 'A' }
    },
    metadata: {},
    grouping_metadata: {}
  };

  test('sorts exact period split chronologically', () => {
    const result = processAnalysisRequest(rawData, {
      stats: { periods_course_has_been_run: true },
      filters: {},
      separationKeys: ['exact_period']
    });

    expect(Object.keys(result.data)).toEqual(['IN24', 'SP24', 'SU24', 'FA24']);
  });

  test('sorts year and season split chronologically', () => {
    const result = processAnalysisRequest(rawData, {
      stats: { periods_course_has_been_run: true },
      filters: {},
      separationKeys: ['year', 'season']
    });

    expect(Object.keys(result.data)).toEqual([
      '2024, Intersession',
      '2024, Spring',
      '2024, Summer',
      '2024, Fall'
    ]);
  });

  test('sorts periods_course_has_been_run chronologically', () => {
    const result = processAnalysisRequest(rawData, {
      stats: { periods_course_has_been_run: true },
      filters: {},
      separationKeys: []
    });

    expect(result.data['All Data'].periods_course_has_been_run).toBe('IN24, SP24, SU24, FA24');
  });
});
