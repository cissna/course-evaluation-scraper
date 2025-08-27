import React, { useState } from 'react';
import './AdvancedOptions.css';
import { STAT_MAPPINGS } from '../utils/statsMapping';

const SEPARATION_OPTIONS = [
  { key: 'instructor', label: 'Instructor' },
  { key: 'year', label: 'Year' },
  { key: 'season', label: 'Season' },
];

const SEASONS = [
  { key: 'FA', label: 'Fall' },
  { key: 'SP', label: 'Spring' },
  { key: 'SU', label: 'Summer' },
  { key: 'IN', label: 'Intersession' }
];

const AdvancedOptions = ({ onApply }) => {
  const statsInit = Object.keys(STAT_MAPPINGS).reduce((acc, key) => {
    acc[key] = true;
    return acc;
  }, {});

  const [showOptions, setShowOptions] = useState(false);
  const [stats, setStats] = useState(statsInit);
  const [filters, setFilters] = useState({
    min_year: '',
    max_year: '',
    seasons: []
  });
  const [separationKeys, setSeparationKeys] = useState([]);

  const handleApply = () => {
    const selectedStats = Object
      .keys(stats)
      .filter(key => stats[key]);

    onApply({
      stats: selectedStats,
      filters: {
        ...filters,
        // Ensure seasons is always present
        seasons: filters.seasons
      },
      separation_keys: separationKeys
    });
  };

  if (!showOptions) {
    return <button onClick={() => setShowOptions(true)}>Advanced Options</button>;
  }

  return (
    <div className="advanced-options">
      <h3>Advanced Options</h3>
      <div className="options-grid">

        {/* Statistics */}
        <div className="option-group">
          <h4>Statistics</h4>
          {Object.entries(STAT_MAPPINGS).map(([key, displayName]) => (
            <label key={key}>
              <input
                type="checkbox"
                checked={stats[key]}
                onChange={() =>
                  setStats(prev => ({ ...prev, [key]: !prev[key] }))
                }
              />
              {displayName}
            </label>
          ))}
        </div>

        {/* Filters */}
        <div className="option-group">
          <h4>Filters</h4>
          <input
            type="number"
            placeholder="Min Year"
            value={filters.min_year}
            onChange={e =>
              setFilters(prev => ({ ...prev, min_year: e.target.value }))
            }
          />
          <input
            type="number"
            placeholder="Max Year"
            value={filters.max_year}
            onChange={e =>
              setFilters(prev => ({ ...prev, max_year: e.target.value }))
            }
          />
          <div className="season-filters">
            <h5>Seasons</h5>
            {SEASONS.map(({ key, label }) => (
              <label key={key}>
                <input
                  type="checkbox"
                  checked={filters.seasons.includes(key)}
                  onChange={() =>
                    setFilters(prev => ({
                      ...prev,
                      seasons: prev.seasons.includes(key)
                        ? prev.seasons.filter(s => s !== key)
                        : [...prev.seasons, key]
                    }))
                  }
                />
                {label}
              </label>
            ))}
          </div>
        </div>

        {/* Separation */}
        <div className="option-group">
          <h4>Separate By</h4>
          {SEPARATION_OPTIONS.map(({ key, label }) => (
            <label key={key}>
              <input
                type="checkbox"
                checked={separationKeys.includes(key)}
                onChange={() =>
                  setSeparationKeys(prev =>
                    prev.includes(key)
                      ? prev.filter(k => k !== key)
                      : [...prev, key]
                  )
                }
              />
              {label}
            </label>
          ))}
        </div>
      </div>
      <button onClick={handleApply}>Apply</button>
      <button onClick={() => setShowOptions(false)}>Hide</button>
    </div>
  );
};

export default AdvancedOptions;