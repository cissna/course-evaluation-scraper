import React from 'react';
import { STAT_MAPPINGS } from '../utils/statsMapping';

export const METRIC_HELP = 'Click any two rows in one or more tables to compare their mean ratings. Overall Quality is the default metric, even before choosing a metric here. The most recent selection is red; the older selection is orange. A third selection replaces the orange row. Click a selected row to deselect it.';
export const THRESHOLD_HELP = 'Uses a two-tailed Welch independent two-sample t-test to compare mean ratings in either direction, allowing unequal variances. A result is significant when p < threshold. This is approximate and assumes independent responses. Shared evaluation records cannot be tested as independent samples.';

const ComparisonMetric = ({ visibleMetrics, metric, chosen, onChange, comparison, labels, threshold }) => <div className="metric-comparison">
  <select aria-label="Choose a metric to compare" title={METRIC_HELP} value={chosen && metric ? metric : ''}
    disabled={!visibleMetrics.length} onChange={event => onChange(event.target.value)}>
    <option value="" disabled>Choose a metric to compare</option>
    {visibleMetrics.map(key => <option key={key} value={key}>{STAT_MAPPINGS[key]}</option>)}
  </select>
  {comparison && !comparison.available && <div className="comparison-feedback comparison-unavailable" role="status">Significance unavailable: {comparison.reason}</div>}
  {comparison?.significant && <div className="comparison-feedback comparison-significant" role="status">
    <strong>{labels[0]}</strong> and <strong>{labels[1]}</strong> are significantly different (P&lt;{Number(threshold)})
  </div>}
</div>;
export default ComparisonMetric;
