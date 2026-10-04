import React, { useEffect, useRef, useState } from 'react';
import './DataDisplay.css';
import { STAT_MAPPINGS, RATING_STAT_KEYS } from '../utils/statsMapping';
import { ordinal } from '../utils/percentiles';
import { convertToCSV } from '../utils/csvExport';

export function formatYearRange(range) {
  if (range.min_year && range.max_year) return `${range.min_year}–${range.max_year}`;
  return range.min_year ? `${range.min_year} and later` : `${range.max_year} and earlier`;
}

const DataDisplay = ({ data, errorMessage, selectedStats = [], statisticsMetadata = {}, showPercentiles = false, yearRangeEmpty, filename = 'course_analysis.csv' }) => {
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
    const percentile = Number.isFinite(details.percentile) ? `${ordinal(details.percentile)} percentile` : 'Percentile unavailable';
    const tooltip = [
      `${absolute}${absolute !== 'N/A' ? ' / 5' : ''}`, percentile,
      details.percentile_reason, `n = ${details.n ?? 0}`,
      `Sample standard deviation = ${Number.isFinite(details.std) ? details.std.toFixed(2) : 'N/A'} (original 1–5 ratings)`,
      `Benchmark years: ${details.benchmark_years || 'unavailable'}`,
      metric === 'workload' ? 'A higher percentile means heavier reported workload, not a better score.' : null,
    ].filter(Boolean);
    return <td key={metric}>
      <span className="stat-value" tabIndex="0" aria-label={tooltip.join('. ')}>
        {showPercentiles ? Number.isFinite(details.percentile) ? ordinal(details.percentile) : 'N/A' : absolute}
        <span className="stat-tooltip" role="tooltip">{tooltip.map((line, index) => <span className="tooltip-line" key={index}>{line}</span>)}</span>
      </span>
    </td>;
  };

  const handleDownload = () => {
    setDownloadClicked(true);
    const csv = convertToCSV(data, stats, statisticsMetadata, showPercentiles);
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
        <thead><tr><th scope="col">Group</th>{stats.map(metric => <th scope="col" key={metric}>{STAT_MAPPINGS[metric]}</th>)}</tr></thead>
        <tbody>{Object.entries(data).map(([group, values]) => <tr key={group}>
          <td>{group}</td>{stats.map(metric => renderCell(group, metric, values[metric]))}
        </tr>)}</tbody>
      </table>
    </div>
    <button onClick={handleDownload} className="download-btn" disabled={downloadClicked} aria-label="Download as CSV" title="Download as CSV">{downloadClicked ? '✅' : '📥'}</button>
  </div>;
};
export default DataDisplay;
