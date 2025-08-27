export const STAT_MAPPINGS = {
  'overall_quality': 'Overall Quality',
  'instructor_effectiveness': 'Instructor Effectiveness', 
  'intellectual_challenge': 'Intellectual Challenge',
  'workload': 'Workload'
  // Easy to extend for new statistics
};

export const getBackendKey = (displayName) => {
  return Object.keys(STAT_MAPPINGS).find(key => STAT_MAPPINGS[key] === displayName);
};

export const getDisplayName = (backendKey) => {
  return STAT_MAPPINGS[backendKey] || backendKey;
};