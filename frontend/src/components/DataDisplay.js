import React from 'react';
import './DataDisplay.css';

const DataDisplay = ({ data, errorMessage }) => {
    if (errorMessage) {
        return <div className="data-display-placeholder">{errorMessage}</div>;
    }
    if (!data) {
        return <div className="data-display-placeholder">Enter a course to see the results.</div>;
    }

    const groups = Object.keys(data);
    const headers = ["Group", "Overall Quality", "Instructor Effectiveness", "Intellectual Challenge", "Workload"];

    const convertToCSV = () => {
        const rows = [headers.join(',')];
        groups.forEach(groupName => {
            const row = [
                `"${groupName}"`,
                data[groupName].overall_quality?.toFixed(2) ?? '',
                data[groupName].instructor_effectiveness?.toFixed(2) ?? '',
                data[groupName].intellectual_challenge?.toFixed(2) ?? '',
                data[groupName].workload?.toFixed(2) ?? ''
            ];
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
                            <td>{data[groupName].overall_quality?.toFixed(2) ?? 'N/A'}</td>
                            <td>{data[groupName].instructor_effectiveness?.toFixed(2) ?? 'N/A'}</td>
                            <td>{data[groupName].intellectual_challenge?.toFixed(2) ?? 'N/A'}</td>
                            <td>{data[groupName].workload?.toFixed(2) ?? 'N/A'}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default DataDisplay;