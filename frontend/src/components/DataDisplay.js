import React, { useEffect, useRef, useState } from 'react';
import './DataDisplay.css';
import { STAT_MAPPINGS, RATING_STAT_KEYS } from '../utils/statsMapping';
import { formatPercentile } from '../utils/percentiles';
import { convertToCSV } from '../utils/csvExport';

export function formatYearRange(range) {
  if (range.min_year && range.max_year) return `${range.min_year}–${range.max_year}`;
  return range.min_year ? `${range.min_year} and later` : `${range.max_year} and earlier`;
}

const DataDisplay = ({ data, errorMessage, selectedStats = [], statisticsMetadata = {}, groupLabels = {}, showPercentiles = false, yearRangeEmpty,
  filename = 'course_analysis.csv', comparisonMetric, rowTones = {}, significant = false, onRowSelect, onMetricSelect }) => {
  const [downloadClicked, setDownloadClicked] = useState(false);
  const timer = useRef(null);
  useEffect(() => () => clearTimeout(timer.current), []);
  if (errorMessage) return <div className="data-display-error" role="alert">{errorMessage}</div>;
  if (!data) return <div className="data-display-placeholder">Enter a course or professor to see the results.</div>;
  if (yearRangeEmpty) return <div className="year-range-empty" role="status">No results for range {formatYearRange(yearRangeEmpty)}, try including some of these years {yearRangeEmpty.available_years.join(', ')}</div>;
  if (!selectedStats.length) return <div className="data-display-placeholder">Select at least one statistic to display results.</div>;
  const stats = selectedStats.filter(key => STAT_MAPPINGS[key]);

  const renderCell = (group, metric, value) => {
    if (!RATING_STAT_KEYS.includes(metric)) return <td key={metric}>{value ?? 'N/A'}</td>;
    const details = statisticsMetadata[group]?.[metric] || {};
    const absolute = typeof value === 'number' ? value.toFixed(2) : 'N/A';
    const hasPercentile = Number.isFinite(details.percentile);
    const percentile = hasPercentile ? formatPercentile(details.percentile) : null;
    const displayed = showPercentiles ? percentile ?? 'N/A' : absolute;
    const tooltip = [
      showPercentiles ? absolute : hasPercentile
        ? `${percentile} percentile${details.percentile_weighted_by_class_size ? ' (weighted by class size)' : ''}` : 'Percentile unavailable',
      !hasPercentile && details.percentile_reason,
      `n = ${details.n ?? 0}, σ = ${Number.isFinite(details.std) ? details.std.toFixed(2) : 'N/A'}`,
      metric === 'workload' ? 'Higher percentiles mean heavier workload.' : null,
    ].filter(Boolean);
    return <td key={metric}>
      <span className="stat-value" tabIndex="0" aria-label={`${displayed}. ${tooltip.join('. ')}`}>
        {showPercentiles && hasPercentile
          ? <>{percentile.slice(0, -2)}<sup className="percentile-suffix">{percentile.slice(-2)}</sup></>
          : displayed}
        <span className="stat-tooltip" role="tooltip">{tooltip.map((line, index) => <span className="tooltip-line" key={index}>{line}</span>)}</span>
      </span>
    </td>;
  };

  const handleDownload = () => {
    setDownloadClicked(true);
    const csv = convertToCSV(data, stats, statisticsMetadata, showPercentiles, groupLabels);
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    timer.current = setTimeout(() => setDownloadClicked(false), 2000);
  };

  return <div className="data-display">
    <div className="table-container">
      <table>
        <thead><tr><th scope="col">Group</th>{stats.map(metric => {
          const selectable = onMetricSelect && RATING_STAT_KEYS.includes(metric);
          return <th scope="col" key={metric}
            className={[comparisonMetric === metric ? 'metric-highlight' : '', selectable ? 'comparison-metric' : ''].filter(Boolean).join(' ')}
            title={selectable ? `Double-click to compare ${STAT_MAPPINGS[metric].toLowerCase()}` : undefined}
            onDoubleClick={selectable ? () => onMetricSelect(metric) : undefined}>
            {STAT_MAPPINGS[metric]}
          </th>;
        })}</tr></thead>
        <tbody>{Object.entries(data).map(([group, values]) => <tr key={group}
          className={[onRowSelect ? 'comparison-row' : '', rowTones[group] ? `row-selected-${rowTones[group]}` : '', significant && rowTones[group] ? 'row-significant' : ''].filter(Boolean).join(' ')}
          tabIndex={onRowSelect ? 0 : undefined} aria-selected={onRowSelect ? Boolean(rowTones[group]) : undefined}
          onClick={onRowSelect ? () => onRowSelect(group) : undefined}
          onKeyDown={event => { if (onRowSelect && event.target === event.currentTarget && (event.key === 'Enter' || event.key === ' ')) { event.preventDefault(); onRowSelect(group); } }}>
          <td>{groupLabels[group]?.tooltip ? <span className="stat-value group-label" tabIndex="0" aria-label={`${groupLabels[group].label}. ${groupLabels[group].tooltip}`}>
            {groupLabels[group].label}
            <span className="stat-tooltip" role="tooltip">{groupLabels[group].tooltip}</span>
          </span> : groupLabels[group]?.label || group}</td>{stats.map(metric => renderCell(group, metric, values[metric]))}
        </tr>)}</tbody>
      </table>
    </div>
    <button onClick={handleDownload} className="download-btn" disabled={downloadClicked} aria-label="Download as CSV" title="Download as CSV">{downloadClicked ? '✅' : '📥'}</button>
  </div>;
};
export default DataDisplay;
