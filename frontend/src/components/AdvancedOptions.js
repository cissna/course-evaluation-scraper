import React, { useState } from 'react';
import './AdvancedOptions.css';

const AdvancedOptions = ({ onApply }) => {
    const [showOptions, setShowOptions] = useState(false);
    const [stats, setStats] = useState({
        overall_quality: true,
        instructor_effectiveness: true,
        intellectual_challenge: true,
        workload: true,
    });
    const [filters, setFilters] = useState({
        min_year: '',
        max_year: '',
        seasons: [],
    });
    const [separationKey, setSeparationKey] = useState('');

    const handleApply = () => {
        const selectedStats = Object.keys(stats).filter(key => stats[key]);
        onApply({ stats: selectedStats, filters, separation_key: separationKey });
    };

    if (!showOptions) {
        return <button onClick={() => setShowOptions(true)}>Advanced Options</button>;
    }

    return (
        <div className="advanced-options">
            <h3>Advanced Options</h3>
            <div className="options-grid">
                <div className="option-group">
                    <h4>Statistics</h4>
                    {Object.keys(stats).map(key => (
                        <label key={key}>
                            <input
                                type="checkbox"
                                checked={stats[key]}
                                onChange={() => setStats(prev => ({ ...prev, [key]: !prev[key] }))}
                            />
                            {key.replace(/_/g, ' ')}
                        </label>
                    ))}
                </div>
                <div className="option-group">
                    <h4>Filters</h4>
                    <input
                        type="number"
                        placeholder="Min Year"
                        value={filters.min_year}
                        onChange={(e) => setFilters(prev => ({ ...prev, min_year: e.target.value }))}
                    />
                    <input
                        type="number"
                        placeholder="Max Year"
                        value={filters.max_year}
                        onChange={(e) => setFilters(prev => ({ ...prev, max_year: e.target.value }))}
                    />
                    {/* Season checkboxes would go here */}
                </div>
                <div className="option-group">
                    <h4>Separation</h4>
                    <select value={separationKey} onChange={(e) => setSeparationKey(e.target.value)}>
                        <option value="">None</option>
                        <option value="instructor">Instructor</option>
                        <option value="year">Year</option>
                        <option value="season">Season</option>
                    </select>
                </div>
            </div>
            <button onClick={handleApply}>Apply</button>
            <button onClick={() => setShowOptions(false)}>Hide</button>
        </div>
    );
};

export default AdvancedOptions;