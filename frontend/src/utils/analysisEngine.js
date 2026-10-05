import { RATING_MAPPINGS } from './statsMapping';
import { lookupPercentile } from './percentiles';

const SEASONS = { FA: 'Fall', SP: 'Spring', SU: 'Summer', IN: 'Intersession' };
const SEMESTER_ORDER = { IN: 0, SP: 1, SU: 2, FA: 3 };
const SEASON_ORDER = { Intersession: 0, Spring: 1, Summer: 2, Fall: 3 };

function periodRank(period) {
  const match = period.match(/^(IN|SP|SU|FA)(\d{2})$/);
  return match ? Number(match[2]) * 4 + SEMESTER_ORDER[match[1]] : null;
}

function comparePeriods(a, b) {
  const rankA = periodRank(a), rankB = periodRank(b);
  if (rankA === null && rankB === null) return a.localeCompare(b);
  if (rankA === null) return 1;
  if (rankB === null) return -1;
  return rankA - rankB;
}

function compareGroupParts(partsA, partsB, keys) {
  for (let index = 0; index < keys.length; index++) {
    const a = partsA[index], b = partsB[index];
    let comparison;
    if (keys[index] === 'exact_period') comparison = comparePeriods(a, b);
    else if (keys[index] === 'season') {
      comparison = (SEASON_ORDER[a] ?? Infinity) - (SEASON_ORDER[b] ?? Infinity);
    } else if (keys[index] === 'year') {
      comparison = (Number(a) || Infinity) - (Number(b) || Infinity);
    } else comparison = a.localeCompare(b);
    if (comparison) return comparison;
  }
  return partsA.join(', ').localeCompare(partsB.join(', '));
}

function getRecordedInstructor(instance) {
  return typeof instance.instructor_name === 'string' ? instance.instructor_name.trim() : '';
}

function periodOf(key) {
  return key.match(/\.((?:IN|SP|SU|FA))(\d{2})$/);
}

function getInstanceYear(key) {
  const period = periodOf(key);
  return period ? 2000 + Number(period[2]) : null;
}

function courseCode(key, instance) {
  return instance.course_code || key.match(/^([A-Z]+\.\d+\.\d+)/)?.[1] || 'Unknown';
}

function yearBound(value) {
  const year = Number(value);
  return value !== '' && value != null && Number.isInteger(year) && year >= 2000 ? year : null;
}

export function filterInstances(allInstances, filters = {}) {
  const minYear = yearBound(filters.min_year);
  const maxYear = yearBound(filters.max_year);
  return Object.fromEntries(Object.entries(allInstances).filter(([key, instance]) => {
    const year = getInstanceYear(key);
    const season = SEASONS[periodOf(key)?.[1]] || 'Unknown';
    if (minYear && (year === null || year < minYear)) return false;
    if (maxYear && (year === null || year > maxYear)) return false;
    if (filters.exclude_summer && season === 'Summer') return false;
    if (filters.exclude_intersession && season === 'Intersession') return false;
    if (filters.seasons?.length && !filters.seasons.includes(season)) return false;
    if (filters.instructors?.length && !filters.instructors.includes(getRecordedInstructor(instance))) return false;
    return true;
  }));
}

function activeSeparationKeys(instances, separationKeys, scope) {
  const codes = new Set(Object.entries(instances).map(([key, instance]) => courseCode(key, instance)));
  const courseGroups = new Set(Object.entries(instances).map(([key, instance]) => instance.course_group_id || courseCode(key, instance)));
  return separationKeys.filter(key =>
    !(key === 'instructor' && scope.type === 'professor') &&
    !(key === 'course_group' && (scope.type !== 'professor' || courseGroups.size <= 1)) &&
    !(key === 'course_code' && codes.size <= 1)
  );
}

function groupParts(key, instance, keys) {
  return keys.map(separation => {
    if (separation === 'instructor') return getRecordedInstructor(instance) || 'Unknown';
    if (separation === 'year') return String(getInstanceYear(key) ?? 'Unknown');
    if (separation === 'season') return SEASONS[periodOf(key)?.[1]] || 'Unknown';
    if (separation === 'exact_period') return periodOf(key)?.slice(1).join('') || 'Unknown';
    if (separation === 'course_code') return courseCode(key, instance);
    if (separation === 'course_group') return instance.course_group || courseCode(key, instance);
    return String(instance[separation] || 'Unknown');
  });
}

function latestCourseNames(instances) {
  const names = new Map();
  for (const [key, instance] of Object.entries(instances)) {
    if (typeof instance.course_name !== 'string' || !instance.course_name.trim()) continue;
    const id = instance.course_group_id || courseCode(key, instance);
    const period = periodOf(key);
    const rank = (getInstanceYear(key) || 0) * 4 + (SEMESTER_ORDER[period?.[1]] || 0);
    const previous = names.get(id);
    if (!previous || rank > previous.rank || (rank === previous.rank && key < previous.key)) {
      names.set(id, { name: instance.course_name.trim(), rank, key });
    }
  }
  return names;
}

export function separateInstances(instances, separationKeys = [], scope = {}) {
  const keys = activeSeparationKeys(instances, separationKeys, scope);
  if (!keys.length) return { 'All Data': Object.values(instances) };
  const groups = Object.create(null);
  const sortParts = Object.create(null);
  for (const [key, instance] of Object.entries(instances)) {
    const parts = groupParts(key, instance, keys);
    const name = parts.join(', ');
    if (!groups[name]) {
      groups[name] = [];
      // Keep parts separate so a comma in a professor/course name is harmless.
      sortParts[name] = parts;
    }
    groups[name].push(instance);
  }
  return Object.fromEntries(Object.entries(groups).sort(([a], [b]) =>
    compareGroupParts(sortParts[a], sortParts[b], keys)
  ));
}

export function calculateDetailedStatistics(frequencies, mapping) {
  const values = Object.entries(frequencies || {}).filter(([label, count]) =>
    mapping[label] && Number.isSafeInteger(count) && count > 0
  );
  const n = values.reduce((total, [, count]) => total + count, 0);
  if (!n) return { mean: null, std: null, variance: null, n: 0 };
  const mean = values.reduce((total, [label, count]) => total + mapping[label] * count, 0) / n;
  const variance = n > 1 ? values.reduce((sum, [label, count]) => sum + count * (mapping[label] - mean) ** 2, 0) / (n - 1) : null;
  return { mean, n, variance, std: variance === null ? null : Math.sqrt(variance) };
}

function frequencyField(metric) {
  return metric.endsWith('_frequency') ? metric : `${metric}_frequency`;
}

function hasResponses(instance) {
  return Object.entries(RATING_MAPPINGS).some(([metric, mapping]) =>
    Object.entries(instance[frequencyField(metric)] || {}).some(([label, count]) => mapping[label] && Number.isSafeInteger(count) && count > 0)
  );
}

export function processAnalysisRequest(rawData, params) {
  const scope = params.scope || { type: rawData.metadata?.result_type || 'course', name: rawData.metadata?.professor_name };
  const scoped = Object.fromEntries(Object.entries(rawData.instances || {}).filter(([, record]) =>
    record && typeof record === 'object' && (scope.type !== 'professor' || getRecordedInstructor(record) === scope.name)
  ));
  const filters = params.filters || {};
  const filtered = filterInstances(scoped, filters);
  const separationKeys = activeSeparationKeys(filtered, params.separation_keys || params.separationKeys || [], scope);
  const separated = separateInstances(filtered, separationKeys, scope);
  const courseGroupIndex = separationKeys.indexOf('course_group');
  // Choose the latest recorded title before filtering so year/season changes
  // do not rename a course or split its existing group into historical titles.
  const courseNames = courseGroupIndex >= 0 ? latestCourseNames(scoped) : null;
  const stats = Object.keys(params.stats || {}).filter(key => params.stats[key]);
  const data = Object.create(null), metadata = Object.create(null), groupLabels = Object.create(null);
  for (const [groupName, instances] of Object.entries(separated)) {
    const entries = Object.entries(filtered).filter(([, instance]) => instances.includes(instance));
    data[groupName] = {};
    metadata[groupName] = {};
    if (courseNames && entries.length) {
      const [key, instance] = entries[0];
      const parts = groupParts(key, instance, separationKeys);
      parts[courseGroupIndex] = courseNames.get(instance.course_group_id || courseCode(key, instance))?.name || parts[courseGroupIndex];
      // Keep course codes in a tooltip for now. If this cell ever needs another
      // tooltip, consider moving codes into the label, probably only for repeated
      // course names. That is an ugly fallback, but better than losing the
      // distinction; for now the tooltip is better than cluttering every label.
      groupLabels[groupName] = { label: parts.join(', '), tooltip: instance.course_group || courseCode(key, instance) };
    }
    for (const metric of stats) {
      if (metric === 'periods_course_has_been_run') {
        const periods = [...new Set(entries.map(([key]) => periodOf(key)?.slice(1).join('')).filter(Boolean))].sort(comparePeriods);
        data[groupName][metric] = periods.join(', ') || 'N/A';
        continue;
      }
      const mapping = RATING_MAPPINGS[metric];
      if (!mapping) continue;
      const totals = {};
      const sourceIds = [];
      for (const [key, record] of entries) {
        let contributed = false;
        for (const [label, count] of Object.entries(record[frequencyField(metric)] || {})) {
          if (!mapping[label] || !Number.isSafeInteger(count) || count <= 0) continue;
          totals[label] = (totals[label] || 0) + count;
          contributed = true;
        }
        if (contributed) sourceIds.push(record.source_evaluation_id || key);
      }
      const details = calculateDetailedStatistics(totals, mapping);
      data[groupName][metric] = details.mean === null ? null : Math.round(details.mean * 100) / 100;
      metadata[groupName][metric] = {
        ...details,
        source_ids: [...new Set(sourceIds)],
        ...lookupPercentile(details.mean, metric, params.benchmark, params.weightPercentilesByClassSize),
        percentile_weighted_by_class_size: Boolean(params.weightPercentilesByClassSize),
        benchmark_years: params.benchmark?.year_coverage || null,
      };
    }
  }

  let yearRangeEmpty = null;
  const minYear = yearBound(filters.min_year), maxYear = yearBound(filters.max_year);
  if ((minYear || maxYear) && Object.keys(filtered).length === 0) {
    const withoutYears = filterInstances(scoped, { ...filters, min_year: '', max_year: '' });
    const availableYears = [...new Set(Object.entries(withoutYears)
      .filter(([, instance]) => hasResponses(instance))
      .map(([key]) => getInstanceYear(key)).filter(year => year !== null))].sort((a, b) => a - b);
    if (availableYears.length) {
      yearRangeEmpty = { min_year: minYear, max_year: maxYear, available_years: availableYears };
    }
  }
  return {
    data,
    metadata: { ...rawData.metadata, grouping_metadata: rawData.grouping_metadata },
    statistics_metadata: metadata,
    group_labels: groupLabels,
    year_range_empty: yearRangeEmpty,
  };
}
