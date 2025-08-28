export const STAT_MAPPINGS = {
  // Default statistics (on by default)
  'overall_quality': 'Overall Quality',
  'instructor_effectiveness': 'Instructor Effectiveness',
  'intellectual_challenge': 'Intellectual Challenge',
  'workload': 'Workload',
  // Statistics that are off by default
  'feedback_frequency': 'Helpful Feedback',
  'ta_frequency': 'TA Quality',
  'periods_run': 'Periods Course Has Been Run'
};

export const DEFAULT_STATS = [
  'overall_quality',
  'instructor_effectiveness',
  'intellectual_challenge',
  'workload'
];

export const OFF_BY_DEFAULT_STATS = [
  'feedback_frequency',
  'ta_frequency',
  'periods_run'
];

export const getBackendKey = (displayName) => {
  return Object.keys(STAT_MAPPINGS).find(key => STAT_MAPPINGS[key] === displayName);
};

export const getDisplayName = (backendKey) => {
  return STAT_MAPPINGS[backendKey] || backendKey;
};

export const isDefaultStat = (statKey) => {
  return DEFAULT_STATS.includes(statKey);
};

export const isOffByDefaultStat = (statKey) => {
  return OFF_BY_DEFAULT_STATS.includes(statKey);
};