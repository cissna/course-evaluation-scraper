import React from 'react';
import './DataDisplay.css';
import { STAT_MAPPINGS } from '../utils/statsMapping';

const DataDisplay = ({ data, errorMessage, selectedStats = [] }) => {
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
            <button onClick={handleDownload} className="download-btn">Download as CSV</button>
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
                            {selectedStats.map(statKey => (
                                <td key={statKey}>
                                    {typeof data[groupName][statKey] === 'number'
                                        ? data[groupName][statKey].toFixed(2)
                                        : data[groupName][statKey] ?? 'N/A'}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default DataDisplay;