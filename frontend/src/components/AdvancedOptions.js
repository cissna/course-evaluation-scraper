import React, { useState } from 'react';
import './AdvancedOptions.css';
import { STAT_MAPPINGS, DEFAULT_STATS, OPTIONAL_STATS } from '../utils/statsMapping';

// Optionally add custom separation options for exact period and course_name.
const SEPARATION_OPTIONS = [
  { key: 'instructor', label: 'Instructor' },
  { key: 'year', label: 'Year' },
  { key: 'season', label: 'Season' },
  { key: 'exact_period', label: 'Exact Period' },
];

const AdvancedOptions = ({ options, onApply, courseMetadata }) => {
  // UI state: control Advanced Options visibility only.
  const [showOptions, setShowOptions] = useState(false);

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
          <h4>Default Statistics</h4>
          {DEFAULT_STATS.map(key => (
            <label key={key}>
              <input
                type="checkbox"
                checked={options.stats[key]}
                onChange={() => handleStatChange(key)}
              />
              {STAT_MAPPINGS[key]}
            </label>
          ))}
        </div>
        <div className="option-group">
          <h4>Optional Statistics</h4>
          {OPTIONAL_STATS.map(key => (
            <label key={key}>
              <input
                type="checkbox"
                checked={!!options.stats[key]}
                onChange={() => handleStatChange(key)}
              />
              {STAT_MAPPINGS[key]}
            </label>
          ))}
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
        </div>
      </div>
      <button onClick={() => onApply(options)}>Apply</button>
      <button onClick={() => setShowOptions(false)}>Hide</button>
    </div>
  );
};

export default AdvancedOptions;