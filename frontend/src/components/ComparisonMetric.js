import React from 'react';
import { STAT_MAPPINGS } from '../utils/statsMapping';
import InfoTooltip from './InfoTooltip';

const COMPARISON_HELP = 'In this mode, you can select two rows to see if their averages for Overall Quality (or your selected metric) are statistically significantly different. Choose a metric from the dropdown or double-click its column header. Click anywhere in a row to select or deselect it. A third selection replaces the older selection.';
const STATISTICS_HELP = 'We use a two-sided Welch independent two-sample t-test, allowing unequal variances. It uses unrounded means, sample variances, and response counts; p below the selected threshold (0.05 by default) indicates a significant difference. Responses are assumed independent; rows sharing evaluations cannot be tested.';
export const THRESHOLD_HELP = 'Uses a two-tailed Welch independent two-sample t-test to compare mean ratings in either direction, allowing unequal variances. A result is significant when p < threshold. This is approximate and assumes independent responses. Shared evaluation records cannot be tested as independent samples.';

const ComparisonMetric = ({ enabled, onToggle, visibleMetrics, metric, onChange, comparison, labels, sharedLabel, threshold }) => <div className="metric-comparison">
  <div className={`comparison-mode-control${enabled ? ' comparison-mode-active' : ''}`}>
    <button onClick={onToggle} aria-pressed={enabled}>{enabled ? 'Exit comparison mode' : 'Enter comparison mode'}</button>
    <InfoTooltip label="About comparison mode">
      <span>{COMPARISON_HELP}</span>
      <span className="comparison-help-statistics">{STATISTICS_HELP}</span>
    </InfoTooltip>
    {enabled && <select aria-label="Comparison metric" value={metric || ''}
      title="The newest selected row is red; the older row is orange. A third selection replaces the orange row. Click a selected row to deselect it."
      disabled={!visibleMetrics.length} onChange={event => onChange(event.target.value)}>
      {!visibleMetrics.length && <option value="">No rating metrics displayed</option>}
      {visibleMetrics.map(key => <option key={key} value={key}>{STAT_MAPPINGS[key]}</option>)}
    </select>}
  </div>
  {enabled && comparison && <div className="comparison-feedback" role="status">
    {!comparison.available ? <>Significance unavailable: {comparison.reason}</> : <>
      <strong>{comparison.significant ? 'Statistically' : 'Not statistically'} significantly</strong> different {metric === 'ta_frequency' ? 'TA quality' : STAT_MAPPINGS[metric]?.toLowerCase()} (P{comparison.significant ? '<' : '≥'}{Number(threshold)})
      <br />
      between <strong className="comparison-label-orange">{labels[0]}</strong> and <strong className="comparison-label-red">{labels[1]}</strong>{sharedLabel && <> for {sharedLabel}</>}
    </>}
  </div>}
</div>;
export default ComparisonMetric;
