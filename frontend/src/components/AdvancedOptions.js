import React from 'react';
import './AdvancedOptions.css';
import { STATISTICS_CONFIG, ALL_STAT_KEYS } from '../utils/statsMapping';
import { toggleSeparation } from '../utils/separationOptions';

const AdvancedOptions = ({ options, onApply, hasCourses = true, hasProfessors = false, hasFormerNames = false, showLast3YearsActive, onDeactivateLast3Years, expanded, onExpandedChange }) => {
  const changeFilter = (key, value) => onApply({ ...options, filters: { ...options.filters, [key]: value } });
  const separation = (key, label, disabled = false) => <label key={key}>
    <input type="checkbox" checked={options.separationKeys.includes(key)} disabled={disabled}
      onChange={() => onApply({ ...options, separationKeys: toggleSeparation(options.separationKeys, key) })} />{label}
  </label>;
  if (!expanded) return <button onClick={() => onExpandedChange(true)}>Advanced Options</button>;
  const exact = options.separationKeys.includes('exact_period');
  const yearOrSeason = options.separationKeys.includes('year') || options.separationKeys.includes('season');
  return <div className="advanced-options">
    <h3>Advanced Options</h3>
    <div className="options-grid">
      <div className="option-group">
        <h4>Statistics</h4>
        {ALL_STAT_KEYS.map(key => <label key={key} className={STATISTICS_CONFIG[key].defaultEnabled ? 'default-stat' : 'off-by-default-stat'}>
          <input type="checkbox" checked={options.stats[key]} onChange={() => onApply({ ...options, stats: { ...options.stats, [key]: !options.stats[key] } })} />
          {STATISTICS_CONFIG[key].displayName}
        </label>)}
        <label className="percentile-weighting" title="Each course is weighted by its responses divided by the number of terms it has run, including summer and intersession. Sections in the same term are combined. Applies to percentiles in the table, tooltips, and CSV exports.">
          <input type="checkbox" checked={options.weightPercentilesByClassSize}
            onChange={event => onApply({ ...options, weightPercentilesByClassSize: event.target.checked })} />
          Weight percentiles by average class size
        </label>
      </div>
      <div className="option-group">
        <h4>Year Range</h4>
        {['min_year', 'max_year'].map((key, index) => <label key={key}>{index ? 'Max Year:' : 'Min Year:'}
          <input type="number" min="2000" value={options.filters[key] || ''} disabled={showLast3YearsActive}
            placeholder={index ? 'e.g., 2024' : 'e.g., 2020'} onChange={event => { onDeactivateLast3Years(); changeFilter(key, event.target.value); }} />
        </label>)}
        <h4>Seasons</h4>
        <label><input type="checkbox" checked={Boolean(options.filters.exclude_summer)} onChange={event => changeFilter('exclude_summer', event.target.checked)} />Exclude summer</label>
        <label><input type="checkbox" checked={Boolean(options.filters.exclude_intersession)} onChange={event => changeFilter('exclude_intersession', event.target.checked)} />Exclude intersession</label>
      </div>
      <div className="option-group">
        <h4>Separate By</h4>
        {hasCourses && separation('instructor', 'Professor')}
        {hasProfessors && separation('course_group', 'Course')}
        {hasProfessors && separation('course_code', 'Course code')}
        {separation('year', 'Year', exact)}
        {separation('season', 'Season', exact)}
        {separation('exact_period', 'Exact Period', yearOrSeason)}
        {hasFormerNames && separation('course_name', 'Course title (including former names)')}
      </div>
    </div>
    <button onClick={() => onExpandedChange(false)}>Hide</button>
  </div>;
};
export default AdvancedOptions;
