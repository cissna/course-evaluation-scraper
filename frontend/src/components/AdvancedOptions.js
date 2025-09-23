import React, { useState } from 'react';
import './AdvancedOptions.css';
import { STATISTICS_CONFIG, ALL_STAT_KEYS } from '../utils/statsMapping';


const AdvancedOptions = ({ options, onApply, courseMetadata, showLast3YearsActive, onDeactivateLast3Years }) => {
  // UI state: control Advanced Options visibility only.
  const [showOptions, setShowOptions] = useState(false);

  // Direct access to statistics configuration - no unnecessary mapping

  // --- Handlers ---

  // Statistics toggling: stats is an object { statKey: boolean }
  const handleStatChange = (key) => {
    const nextStats = {
      ...options.stats,
      [key]: !options.stats[key],
    };
    onApply({
      ...options,
      stats: nextStats,
    });
  };

  // Separation toggling with mutual exclusivity logic
  const handleSeparationChange = (key) => {
    let nextKeys = [...options.separationKeys];
    const isSelected = nextKeys.includes(key);

    if (key === 'exact_period') {
      if (!isSelected) {
        // Add exact_period, remove year/season if present
        nextKeys = [
          ...nextKeys.filter(
            k => k !== 'year' && k !== 'season'
          ),
          'exact_period',
        ];
      } else {
        // Remove exact_period
        nextKeys = nextKeys.filter(k => k !== 'exact_period');
      }
    } else if (key === 'year' || key === 'season') {
      if (!isSelected) {
        // Add year/season, remove exact_period if present
        nextKeys = [
          ...nextKeys.filter(k => k !== 'exact_period'),
          key,
        ];
      } else {
        // Remove year/season
        nextKeys = nextKeys.filter(k => k !== key);
      }
    } else {
      // Regular toggle for other separation options
      if (isSelected) {
        nextKeys = nextKeys.filter(k => k !== key);
      } else {
        nextKeys.push(key);
      }
    }
    onApply({
      ...options,
      separationKeys: nextKeys,
    });
  };

  // Year input handlers
  const handleMinYearChange = (event) => {
    const value = event.target.value;
    if (showLast3YearsActive) {
      onDeactivateLast3Years();
    }
    const nextOptions = {
      ...options,
      filters: {
        ...options.filters,
        min_year: value,
      },
    };
    onApply(nextOptions);
  };

  const handleMaxYearChange = (event) => {
    const value = event.target.value;
    if (showLast3YearsActive) {
      onDeactivateLast3Years();
    }
    const nextOptions = {
      ...options,
      filters: {
        ...options.filters,
        max_year: value,
      },
    };
    onApply(nextOptions);
  };

  // --- Render ---

  // Check for conditional course name separation
  const showCourseNameOption =
    courseMetadata &&
    courseMetadata.former_names &&
    courseMetadata.former_names.length > 0;

  const isExactPeriodSelected = options.separationKeys.includes('exact_period');
  const isYearOrSeasonSelected =
    options.separationKeys.includes('year') ||
    options.separationKeys.includes('season');

  if (!showOptions) {
    return (
      <button onClick={() => setShowOptions(true)}>
        Advanced Options
      </button>
    );
  }

  return (
    <div className="advanced-options">
      <h3>Advanced Options</h3>
      <div className="options-grid">
        {/* Statistics */}
        <div className="option-group">
          <h4>Statistics</h4>
          {ALL_STAT_KEYS.map(key => {
            const config = STATISTICS_CONFIG[key];
            return (
              <label key={key} className={config.defaultEnabled ? 'default-stat' : 'off-by-default-stat'}>
                <input
                  type="checkbox"
                  checked={options.stats[key]}
                  onChange={() => handleStatChange(key)}
                />
                {config.displayName}
              </label>
            );
          })}
        </div>

        {/* Year Range */}
        <div className="option-group">
          <h4>Year Range</h4>
          <label>
            Min Year:
            <input
              type="number"
              value={options.filters.min_year || ''}
              onChange={handleMinYearChange}
              disabled={showLast3YearsActive}
              placeholder="e.g., 2020"
            />
          </label>
          <label>
            Max Year:
            <input
              type="number"
              value={options.filters.max_year || ''}
              onChange={handleMaxYearChange}
              disabled={showLast3YearsActive}
              placeholder="e.g., 2024"
            />
          </label>
        </div>

        {/* Separation Options */}
        <div className="option-group">
          <h4>Separate By</h4>
          {/* Instructor */}
          <label>
            <input
              type="checkbox"
              checked={options.separationKeys.includes('instructor')}
              onChange={() => handleSeparationChange('instructor')}
            />
            Instructor
          </label>
          {/* Year */}
          <label>
            <input
              type="checkbox"
              checked={options.separationKeys.includes('year')}
              onChange={() => handleSeparationChange('year')}
              disabled={isExactPeriodSelected}
            />
            Year
          </label>
          {/* Season */}
          <label>
            <input
              type="checkbox"
              checked={options.separationKeys.includes('season')}
              onChange={() => handleSeparationChange('season')}
              disabled={isExactPeriodSelected}
            />
            Season
          </label>
          {/* Exact Period */}
          <label>
            <input
              type="checkbox"
              checked={options.separationKeys.includes('exact_period')}
              onChange={() => handleSeparationChange('exact_period')}
              disabled={isYearOrSeasonSelected}
            />
            Exact Period
          </label>
          {/* Course Name - conditional */}
          {showCourseNameOption && (
            <label>
              <input
                type="checkbox"
                checked={options.separationKeys.includes('course_name')}
                onChange={() => handleSeparationChange('course_name')}
              />
              Course Name
            </label>
          )}
          {/* Course Code checkbox removed per requirements */}
        </div>
      </div>
      <button onClick={() => onApply(options)}>Apply</button>
      <button onClick={() => setShowOptions(false)}>Hide</button>
    </div>
  );
};

export default AdvancedOptions;