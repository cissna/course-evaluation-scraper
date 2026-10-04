import { STAT_MAPPINGS, RATING_STAT_KEYS } from './statsMapping';
import { ordinal } from './percentiles';

function cell(value) {
  let text = value == null ? '' : String(value);
  if (typeof value === 'string' && /^[\s]*[=+@-]/.test(text)) text = `'${text}`;
  return `"${text.replace(/"/g, '""')}"`;
}

export function convertToCSV(data, selectedStats, statisticsMetadata = {}, showPercentiles = false, groupLabels = {}) {
  const stats = selectedStats.filter(key => STAT_MAPPINGS[key]);
  const headers = ['Group'];
  const includeCourseCodes = Object.keys(data).some(group => groupLabels[group]?.tooltip);
  if (includeCourseCodes) headers.push('Course codes');
  for (const stat of stats) {
    const label = STAT_MAPPINGS[stat];
    headers.push(label);
    if (RATING_STAT_KEYS.includes(stat)) {
      headers.push(`${label} — absolute score (1–5)`, `${label} — percentile`, `${label} — response count`,
        `${label} — sample standard deviation (1–5 ratings)`, `${label} — benchmark years`, `${label} — percentile note`);
    }
  }
  const rows = [headers];
  for (const [group, values] of Object.entries(data)) {
    const row = [groupLabels[group]?.label || group];
    if (includeCourseCodes) row.push(groupLabels[group]?.tooltip || '');
    for (const stat of stats) {
      const details = statisticsMetadata[group]?.[stat] || {};
      const value = values[stat];
      const rating = RATING_STAT_KEYS.includes(stat);
      const percentile = Number.isFinite(details.percentile) ? Math.round(details.percentile) : null;
      row.push(rating && showPercentiles ? percentile ?? 'N/A' : typeof value === 'number' ? value.toFixed(2) : value ?? 'N/A');
      if (rating) {
        row.push(details.mean ?? value, percentile !== null ? `${ordinal(percentile)} percentile` : '', details.n ?? '', details.std ?? '',
          details.benchmark_years ?? '', [details.percentile_reason, stat === 'workload' ? 'Higher percentile means heavier reported workload, not a better score.' : null].filter(Boolean).join(' '));
      }
    }
    rows.push(row);
  }
  return rows.map(row => row.map(cell).join(',')).join('\r\n');
}
