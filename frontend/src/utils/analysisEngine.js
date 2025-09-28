// Port of Python/analysis.py to JavaScript

const STAT_MAPPINGS = {
  overall_quality: {
    displayName: "Overall Quality",
    mapping: {"Poor": 1, "Weak": 2, "Satisfactory": 3, "Good": 4, "Excellent": 5}
  },
  instructor_effectiveness: {
    displayName: "Instructor Effectiveness", 
    mapping: {"Poor": 1, "Weak": 2, "Satisfactory": 3, "Good": 4, "Excellent": 5}
  },
  intellectual_challenge: {
    displayName: "Intellectual Challenge",
    mapping: {"Poor": 1, "Weak": 2, "Satisfactory": 3, "Good": 4, "Excellent": 5}
  },
  workload: {
    displayName: "Workload",
    mapping: {"Much lighter": 1, "Somewhat lighter": 2, "Typical": 3, "Somewhat heavier": 4, "Much heavier": 5}
  },
  feedback_frequency: {
    displayName: "Helpful Feedback",
    mapping: {"Disagree strongly": 1, "Disagree somewhat": 2, "Neither agree nor disagree": 3, "Agree somewhat": 4, "Agree strongly": 5}
  },
  ta_frequency: {
    displayName: "TA Quality",
    mapping: {"Poor": 1, "Weak": 2, "Satisfactory": 3, "Good": 4, "Excellent": 5}
  },
  periods_course_has_been_run: {
    displayName: "Periods Course Has Been Run",
    mapping: {}
  }
};

function simplifyName(name) {
  if (typeof name !== 'string') return "";
  return name.replace(/[^a-zA-Z]/g, '').toLowerCase();
}

function parseSemesterYear(instanceKey) {
  const match = instanceKey.match(/\.((?:IN|SP|SU|FA))(\d{2})$/);
  if (match) {
    const [, semester, year] = match;
    const yearNum = parseInt('20' + year);
    const semesterOrder = {'IN': 0, 'SP': 1, 'SU': 2, 'FA': 3};
    return { year: yearNum, semesterNum: semesterOrder[semester] || 0, semester };
  }
  return { year: 0, semesterNum: 0, semester: null };
}

function getInstanceYear(instanceKey) {
  const match = instanceKey.match(/\.(?:IN|SP|SU|FA)(\d{2})$/);
  if (match) {
    return 2000 + parseInt(match[1]);
  }
  return 2000;
}

function getInstanceSeason(instanceKey) {
  const match = instanceKey.match(/\.((?:IN|SP|SU|FA))\d{2}$/);
  const seasons = {"FA": "Fall", "SP": "Spring", "SU": "Summer", "IN": "Intersession"};
  if (match && seasons[match[1]]) {
    return seasons[match[1]];
  }
  return "Unknown";
}

export function filterInstances(allInstances, filters) {
  const filtered = {};
  const minYear = filters.min_year ? parseInt(filters.min_year) : null;
  const maxYear = filters.max_year ? parseInt(filters.max_year) : null;
  const seasons = filters.seasons || [];
  const instructors = filters.instructors || [];

  for (const [key, instance] of Object.entries(allInstances)) {
    const year = getInstanceYear(key);
    if (minYear && year < minYear) continue;
    if (maxYear && year > maxYear) continue;
    if (seasons.length > 0 && !seasons.includes(getInstanceSeason(key))) continue;
    if (instructors.length > 0 && !instructors.includes(instance.instructor_name)) continue;
    filtered[key] = instance;
  }
  return filtered;
}

export function separateInstances(instances, separationKeys = []) {
  if (!separationKeys || separationKeys.length === 0) {
    return { "All Data": Object.values(instances) };
  }

  const simplifiedToDisplayName = {};
  if (separationKeys.includes('instructor')) {
    const tempMap = {};
    for (const [key, instance] of Object.entries(instances)) {
      const instructor = instance.instructor_name;
      if (!instructor) continue;
      const simplified = simplifyName(instructor);
      if (!simplified) continue;
      const periodTuple = parseSemesterYear(key);
      if (!tempMap[simplified] || periodTuple > tempMap[simplified][0]) {
        tempMap[simplified] = [periodTuple, instructor];
      }
    }
    for (const [simplified, [, displayName]] of Object.entries(tempMap)) {
      simplifiedToDisplayName[simplified] = displayName;
    }
  }
  
  const groups = {};
  
  for (const [key, instance] of Object.entries(instances)) {
    const groupParts = [];
    for (const sepKey of separationKeys) {
      let value = "Unknown";
      if (sepKey === "instructor") {
        const simplified = simplifyName(instance.instructor_name);
        value = simplifiedToDisplayName[simplified] || instance.instructor_name || "Unknown";
      } else if (sepKey === "year") {
        value = String(getInstanceYear(key));
      } else if (sepKey === "season") {
        value = getInstanceSeason(key);
      } else if (sepKey === "exact_period") {
        const match = key.match(/\.([A-Z]{2}\d{2})$/);
        value = match ? match[1] : "Unknown";
      } else if (sepKey === "course_code") {
        value = instance.course_code || key.match(/^([A-Z]+\.\d+\.\d+)/)?.[1] || "Unknown";
      } else {
        value = String(instance[sepKey] || "Unknown");
      }
      groupParts.push(value);
    }
    const groupName = groupParts.join(", ");
    if (!groups[groupName]) groups[groupName] = [];
    groups[groupName].push(instance);
  }
  return groups;
}

function calculateDetailedStatistics(frequencyDict, valueMapping) {
  const dataPoints = [];
  let totalResponses = 0;
  for (const [response, count] of Object.entries(frequencyDict)) {
    if (valueMapping[response] && count > 0) {
      const value = valueMapping[response];
      for (let i = 0; i < count; i++) {
        dataPoints.push(value);
      }
      totalResponses += count;
    }
  }
  
  if (totalResponses === 0) {
    return { mean: null, std: null, n: 0 };
  }
  
  const mean = dataPoints.reduce((a, b) => a + b, 0) / totalResponses;
  let std = 0;
  if (totalResponses > 1) {
    const variance = dataPoints.reduce((sum, x) => sum + Math.pow(x - mean, 2), 0) / (totalResponses - 1);
    std = Math.sqrt(variance);
  }
  
  return {
    mean: Math.round(mean * 100) / 100,
    std: Math.round(std * 100) / 100,
    n: totalResponses
  };
}

function calculateGroupStatistics(groupInstances, statsToCalculate, instanceKeys = []) {
  const aggregatedFrequencies = {};
  for (const key of statsToCalculate) {
    aggregatedFrequencies[key] = {};
  }

  for (const instance of groupInstances) {
    for (const stat of statsToCalculate) {
      const freqKey = stat.endsWith('_frequency') ? stat : stat + '_frequency';
      if (instance[freqKey]) {
        for (const [response, count] of Object.entries(instance[freqKey])) {
          if (!aggregatedFrequencies[stat][response]) {
            aggregatedFrequencies[stat][response] = 0;
          }
          aggregatedFrequencies[stat][response] += count;
        }
      }
    }
  }

  const results = {};
  const details = {};

  for (const key of statsToCalculate) {
    const statConfig = STAT_MAPPINGS[key];
    if (!statConfig) continue;

    if (key === "periods_course_has_been_run") {
      const periods = new Set();
      for (const k of instanceKeys) {
        const match = k.match(/\.([A-Z]{2}\d{2})$/);
        if (match) periods.add(match[1]);
      }
      results[key] = periods.size > 0 ? Array.from(periods).sort().join(', ') : 'N/A';
      details[key] = { n: null, std: null };
    } else {
      const detailed = calculateDetailedStatistics(aggregatedFrequencies[key], statConfig.mapping);
      results[key] = detailed.mean;
      details[key] = { n: detailed.n, std: detailed.std };
    }
  }
  return { values: results, details: details };
}

export function processAnalysisRequest(rawData, params) {
  // 1. Filter instances
  const filtered = filterInstances(rawData.instances, params.filters);
  
  // 2. Separate into groups
  const separated = separateInstances(filtered, params.separation_keys || params.separationKeys);
  
  // 3. Calculate statistics for each group
  const analysisResults = {};
  const statisticsMetadata = {};
  
  // Map frontend stat keys to backend keys
  const statsToSend = Object.keys(params.stats).filter(k => params.stats[k]);
  const backendStatKeys = statsToSend.map(stat => {
    if (stat === 'periods_course_has_been_run') return stat;
    if (['feedback_frequency', 'ta_frequency'].includes(stat)) return stat;
    return stat + '_frequency';
  });

  for (const [groupName, instances] of Object.entries(separated)) {
    // Get instance keys for this group
    const groupInstanceKeys = Object.keys(filtered).filter(key => instances.includes(filtered[key]));
    
    const result = calculateGroupStatistics(instances, statsToSend, groupInstanceKeys);
    
    // Map back to frontend keys
    const groupData = {};
    const groupMetadata = {};
    for (const [backendKey, value] of Object.entries(result.values)) {
      const frontendKey = backendKey.replace('_frequency', '');
      groupData[frontendKey] = value;
    }
    for (const [backendKey, value] of Object.entries(result.details)) {
      const frontendKey = backendKey.replace('_frequency', '');
      groupMetadata[frontendKey] = value;
    }
    analysisResults[groupName] = groupData;
    statisticsMetadata[groupName] = groupMetadata;
  }

  return {
    data: analysisResults,
    metadata: {
      ...rawData.metadata,
      grouping_metadata: rawData.grouping_metadata
    },
    statistics_metadata: statisticsMetadata
  };
}