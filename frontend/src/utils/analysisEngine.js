import { RATING_MAPPINGS } from './statsMapping';
import { lookupPercentile } from './percentiles';

const SEASONS = { FA: 'Fall', SP: 'Spring', SU: 'Summer', IN: 'Intersession' };

export function getRecordedInstructors(instance) {
  const value = instance.instructor_names ?? instance.instructor_name;
  const names = Array.isArray(value) ? value : typeof value === 'string' ? value.split(/[;|\n\r]+|\s+(?:&|and)\s+/) : [];
  return [...new Set(names.filter(name => typeof name === 'string').map(name => name.trim()).filter(Boolean))];
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
    if (filters.instructors?.length && !getRecordedInstructors(instance).some(name => filters.instructors.includes(name))) return false;
    return true;
  }));
}

export function separateInstances(instances, separationKeys = [], scope = {}) {
  const codes = new Set(Object.entries(instances).map(([key, instance]) => courseCode(key, instance)));
  const courseGroups = new Set(Object.entries(instances).map(([key, instance]) => instance.course_group_id || courseCode(key, instance)));
  const keys = separationKeys.filter(key =>
    !(key === 'instructor' && scope.type === 'professor') &&
    !(key === 'course_group' && (scope.type !== 'professor' || courseGroups.size <= 1)) &&
    !(key === 'course_code' && codes.size <= 1)
  );
  if (!keys.length) return { 'All Data': Object.values(instances) };
  const groups = Object.create(null);
  for (const [key, instance] of Object.entries(instances)) {
    const parts = keys.map(separation => {
      if (separation === 'instructor') return typeof instance.instructor_name === 'string' ? instance.instructor_name : getRecordedInstructors(instance).join(' & ') || 'Unknown';
      if (separation === 'year') return String(getInstanceYear(key) ?? 'Unknown');
      if (separation === 'season') return SEASONS[periodOf(key)?.[1]] || 'Unknown';
      if (separation === 'exact_period') return periodOf(key)?.slice(1).join('') || 'Unknown';
      if (separation === 'course_code') return courseCode(key, instance);
      if (separation === 'course_group') return instance.course_group || courseCode(key, instance);
      return String(instance[separation] || 'Unknown');
    });
    const name = parts.join(', ');
    if (!groups[name]) groups[name] = [];
    groups[name].push(instance);
  }
  return groups;
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
    record && typeof record === 'object' && (scope.type !== 'professor' || getRecordedInstructors(record).includes(scope.name))
  ));
  const filters = params.filters || {};
  const filtered = filterInstances(scoped, filters);
  const separated = separateInstances(filtered, params.separation_keys || params.separationKeys || [], scope);
  const stats = Object.keys(params.stats || {}).filter(key => params.stats[key]);
  const data = Object.create(null), metadata = Object.create(null);
  for (const [groupName, instances] of Object.entries(separated)) {
    const entries = Object.entries(filtered).filter(([, instance]) => instances.includes(instance));
    data[groupName] = {};
    metadata[groupName] = {};
    for (const metric of stats) {
      if (metric === 'periods_course_has_been_run') {
        const periods = [...new Set(entries.map(([key]) => periodOf(key)?.slice(1).join('')).filter(Boolean))].sort();
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
        ...lookupPercentile(details.mean, metric, params.benchmark),
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
    year_range_empty: yearRangeEmpty,
  };
}
