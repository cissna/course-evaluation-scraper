import React from 'react';
import './DataDisplay.css';
import { STAT_MAPPINGS } from '../utils/statsMapping';

const DataDisplay = ({ data, errorMessage, selectedStats = [], statisticsMetadata = {} }) => {
    if (errorMessage) {
        return <div className="data-display-error" dangerouslySetInnerHTML={{ __html: errorMessage }}></div>;
    }
    if (!data) {
        return <div className="data-display-placeholder">Enter a course to see the results.</div>;
    }

    const groups = Object.keys(data);
    // Dynamic header generation based on selectedStats
    const generateHeaders = () => {
        const headers = ["Group"];
        if (selectedStats && selectedStats.length > 0) {
            selectedStats.forEach(statKey => {
                if (STAT_MAPPINGS[statKey]) {
                    headers.push(STAT_MAPPINGS[statKey]);
                }
            });
        }
        return headers;
    };

    const headers = generateHeaders();

    const renderCell = (groupName, statKey, value) => {
        const details = statisticsMetadata[groupName]?.[statKey];

        if (details && details.n !== undefined && details.n !== null) {
            return (
                <td key={statKey}>
                    <span className="stat-value">
                        {typeof value === 'number' ? value.toFixed(2) : value ?? 'N/A'}
                        <span className="stat-tooltip">
                            n = {details.n}
                            {details.std !== undefined && details.std !== null && `, σ = ${details.std.toFixed(2)}`}
                        </span>
                    </span>
                </td>
            );
        }

        // Regular cell without tooltip
        return (
            <td key={statKey}>
                {typeof value === 'number' ? value.toFixed(2) : value ?? 'N/A'}
            </td>
        );
    };

    const convertToCSV = () => {
        const rows = [headers.join(',')];
        groups.forEach(groupName => {
            const row = [`"${groupName}"`];
            if (selectedStats && selectedStats.length > 0) {
                selectedStats.forEach(statKey => {
                    const value = data[groupName][statKey];
                    row.push(typeof value === 'number' ? value.toFixed(2) : value ?? '');
                });
            }
            rows.push(row.join(','));
        });
        return rows.join('\n');
    };

    const handleDownload = () => {
        const csv = convertToCSV();
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', 'course_analysis.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    // Edge case: if selectedStats is undefined/null or empty, show fallback
    if (!selectedStats || selectedStats.length === 0) {
        return (
            <div className="data-display">
                <div className="data-display-placeholder">
                    Select at least one statistic to display results.
                </div>
            </div>
        );
    }

    return (
        <div className="data-display">
            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            {headers.map(h => <th key={h}>{h}</th>)}
                        </tr>
                    </thead>
                    <tbody>
                        {groups.map(groupName => (
                            <tr key={groupName}>
                                <td>{groupName}</td>
                                {selectedStats.map(statKey =>
                                    renderCell(groupName, statKey, data[groupName][statKey])
                                )}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <button onClick={handleDownload} className="download-btn">&#x2913;</button>
        </div>
    );
};

export default DataDisplay;