// Unified statistics configuration - single source of truth
// Each statistic has its key, display name, and default enabled state
export const STATISTICS_CONFIG = {
  'overall_quality': {
    displayName: 'Overall Quality',
    defaultEnabled: true
  },
  'instructor_effectiveness': {
    displayName: 'Instructor Effectiveness',
    defaultEnabled: true
  },
  'intellectual_challenge': {
    displayName: 'Intellectual Challenge',
    defaultEnabled: true
  },
  'workload': {
    displayName: 'Workload',
    defaultEnabled: true
  },
  'feedback_frequency': {
    displayName: 'Helpful Feedback',
    defaultEnabled: false
  },
  'ta_frequency': {
    displayName: 'TA Quality',
    defaultEnabled: false
  },
  'periods_course_has_been_run': {
    displayName: 'Periods Course Has Been Run',
    defaultEnabled: false
  }
};

// Derived utilities - no more separate arrays needed
export const ALL_STAT_KEYS = Object.keys(STATISTICS_CONFIG);

// Legacy mapping object for backward compatibility
export const STAT_MAPPINGS = Object.fromEntries(
  ALL_STAT_KEYS.map(key => [key, STATISTICS_CONFIG[key].displayName])
);

// Simplified utility functions
export const getDisplayName = (backendKey) => {
  return STATISTICS_CONFIG[backendKey]?.displayName || backendKey;
};

export const getAllStatistics = () => {
  return ALL_STAT_KEYS.map(key => ({
    key,
    displayName: STATISTICS_CONFIG[key].displayName,
    defaultEnabled: STATISTICS_CONFIG[key].defaultEnabled
  }));
};

export const getInitialStatsState = () => {
  return Object.fromEntries(
    ALL_STAT_KEYS.map(key => [key, STATISTICS_CONFIG[key].defaultEnabled])
  );
};