import React from 'react';
import './AdvancedOptions.css';
import { STATISTICS_CONFIG, ALL_STAT_KEYS } from '../utils/statsMapping';
import { toggleSeparation } from '../utils/separationOptions';
import { THRESHOLD_HELP } from './ComparisonMetric';
import { isValidThreshold } from '../utils/significance';

const AdvancedOptions = ({ options, onApply, hasCourses = true, hasProfessors = false, hasFormerNames = false, comparisonMode = false, showLast3YearsActive, onDeactivateLast3Years, expanded, onExpandedChange }) => {
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
        <label className="percentile-weighting" title="Depending on your perspective, this is a more truthful way to interpret the percentiles, since you are more likely to take classes with more people.">
          <input type="checkbox" checked={options.weightPercentilesByClassSize}
            onChange={event => onApply({ ...options, weightPercentilesByClassSize: event.target.checked })} />
          Weight percentiles by average class size
        </label>
        {comparisonMode && <><label className="significance-threshold" title={THRESHOLD_HELP}>
          Significance threshold for comparisons
          <input type="number" step="any" min="0" max="1" value={options.significanceThreshold}
            aria-invalid={!isValidThreshold(options.significanceThreshold)} title={THRESHOLD_HELP}
            onChange={event => onApply({ ...options, significanceThreshold: event.target.value })} />
        </label>
        {!isValidThreshold(options.significanceThreshold) && <small role="alert">Enter a value greater than 0 and less than 1.</small>}</>}
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
