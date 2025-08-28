
// yearUtils.js
// Utility functions for calculating year ranges based on period logic

// Period release dates - replicated from config.py
const PERIOD_RELEASE_DATES = {
  'IN': [1, 15],   // Intersession - January 15
  'SP': [5, 15],   // Spring - May 15
  'SU': [8, 15],   // Summer - August 15
  'FA': [12, 15]   // Fall - December 15
};

/**
 * Determines the current evaluation period based on today's date.
 * Replicates the get_current_period() logic from period_logic.py
 * 
 * @returns {string} The current period string (e.g., "FA25")
 */
function getCurrentPeriod() {
  const today = new Date();
  const currentMonth = today.getMonth() + 1; // JavaScript months are 0-indexed
  const currentDay = today.getDate();
  const yearShort = today.getFullYear() % 100;

  // Check periods in reverse chronological order of their release dates
  if (currentMonth > PERIOD_RELEASE_DATES['FA'][0] || 
      (currentMonth === PERIOD_RELEASE_DATES['FA'][0] && currentDay >= PERIOD_RELEASE_DATES['FA'][1])) {
    return `FA${yearShort}`;
  } else if (currentMonth > PERIOD_RELEASE_DATES['SU'][0] || 
             (currentMonth === PERIOD_RELEASE_DATES['SU'][0] && currentDay >= PERIOD_RELEASE_DATES['SU'][1])) {
    return `SU${yearShort}`;
  } else if (currentMonth > PERIOD_RELEASE_DATES['SP'][0] || 
             (currentMonth === PERIOD_RELEASE_DATES['SP'][0] && currentDay >= PERIOD_RELEASE_DATES['SP'][1])) {
    return `SP${yearShort}`;
  } else if (currentMonth > PERIOD_RELEASE_DATES['IN'][0] || 
             (currentMonth === PERIOD_RELEASE_DATES['IN'][0] && currentDay >= PERIOD_RELEASE_DATES['IN'][1])) {
    return `IN${yearShort}`;
  } else {
    // If before the first period release of the year, it's the last period of the previous year
    return `FA${yearShort - 1}`;
  }
}

/**
 * Converts a 2-digit year to a 4-digit year using the same logic as the backend
 * Years < 70 are treated as 20xx, years >= 70 are treated as 19xx
 * 
 * @param {number} yearShort - 2-digit year
 * @returns {number} 4-digit year
 */
function convertToFullYear(yearShort) {
  if (yearShort < 70) {
    return 2000 + yearShort;
  } else {
    return 1900 + yearShort;
  }
}

/**
 * Calculates the "last 3 years" range using sophisticated period logic
 * 
 * @returns {Object} Object with min_year and max_year properties
 */
export function calculateLast3YearsRange() {
  // Get current period using the replicated logic
  const currentPeriod = getCurrentPeriod();
  
  // Extract period type and year from period string (e.g., "FA25" → "FA", 25)
  const periodType = currentPeriod.substring(0, 2);
  const yearShort = parseInt(currentPeriod.substring(2), 10);
  
  // Convert to full year
  const periodYear = convertToFullYear(yearShort);
  
  // If period is "IN" (Intersession), subtract 1 year for base calculation
  const baseYear = periodType === 'IN' ? periodYear - 1 : periodYear;
  
  // Calculate min_year = base_year - 2
  const minYear = baseYear - 2;
  
  // Set max_year = actual current year from new Date().getFullYear()
  const maxYear = new Date().getFullYear();
  
  return {
    min_year: minYear,
    max_year: maxYear
  };
}