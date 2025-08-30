import React, { useState } from 'react';
import './App.css';
import CourseSearch from './components/CourseSearch';
import DataDisplay from './components/DataDisplay';
import AdvancedOptions from './components/AdvancedOptions';
import LoadingOverlay from './components/LoadingOverlay';
import GracePeriodWarning from './components/GracePeriodWarning';
import { STAT_MAPPINGS, STATISTICS_CONFIG, ALL_STAT_KEYS } from './utils/statsMapping';
import { calculateLast3YearsRange } from './utils/yearUtils';

function App() {
  const [analysisResult, setAnalysisResult] = useState(null);
  const [courseCode, setCourseCode] = useState(null);
  const [advancedOptions, setAdvancedOptions] = useState({
    stats: Object.fromEntries(
      ALL_STAT_KEYS.map(key => [key, STATISTICS_CONFIG[key].defaultEnabled])
    ),
    filters: { min_year: '', max_year: '', seasons: [] },
    separationKeys: []
  });
  const [showLast3YearsActive, setShowLast3YearsActive] = useState(false);
  const [analysisError, setAnalysisError] = useState(null);
  const [loadingCount, setLoadingCount] = useState(0);
  const [gracePeriodInfo, setGracePeriodInfo] = useState(null);
  const [dismissedGraceWarnings, setDismissedGraceWarnings] = useState(new Set());
  // (No longer tracking a separate autoGroupingBanner state: always show based on analysisResult.grouping_metadata.is_grouped)
  const isLoading = loadingCount > 0;
  const startLoading = () => setLoadingCount(c => c + 1);
  const stopLoading = () => setLoadingCount(c => Math.max(0, c - 1));

  // Helper: checks if stats are the only thing changed
  const onlyStatsChanged = (newOptions, prevOptions) => {
    // Compare stats deep equality, filters and separationKeys referential
    const statsKeys = Object.keys(newOptions.stats);
    const statsSame =
      statsKeys.length === Object.keys(prevOptions.stats).length &&
      statsKeys.every(
        k => newOptions.stats[k] === prevOptions.stats[k]
      );
    const filtersSame = JSON.stringify(newOptions.filters) === JSON.stringify(prevOptions.filters);
    const separationSame = JSON.stringify(newOptions.separationKeys) === JSON.stringify(prevOptions.separationKeys);
    return statsSame && (!filtersSame || !separationSame ? false : true);
  };

  // Called when advanced options (checkbox) toggled
  const handleAdvancedOptionsApply = (options) => {
    console.log('[App] AdvancedOptions applied:', options);

    // If only stats changed, no API needed, just update advancedOptions state for column hiding/showing
    const statsChanged =
      JSON.stringify(options.stats) !== JSON.stringify(advancedOptions.stats);
    const filtersChanged =
      JSON.stringify(options.filters) !== JSON.stringify(advancedOptions.filters);
    const separationChanged =
      JSON.stringify(options.separationKeys) !== JSON.stringify(advancedOptions.separationKeys);

    setAdvancedOptions(options);

    if (
      courseCode &&
      (filtersChanged || separationChanged)
    ) {
      // Fetch new analysis if filters or separation changed
      console.log('[App] Fetching new analysis for course:', courseCode, 'due to filter or separation change.');
      fetchAnalysisData(courseCode, options);
    } else if (statsChanged) {
      // Column show/hide only, no data fetch
      console.log('[App] Stats columns changed only, not refetching data.');
    } else {
      // Edge case: nothing substantial changed
      console.log('[App] AdvancedOptions applied but changes do not need new analysis or column update.');
    }
    // Show current loading state
    console.log('[App] isLoading after apply:', isLoading, 'loadingCount:', loadingCount);
  };

  const checkGracePeriodStatus = async (code) => {
    if (!code) return;
    
    try {
      const response = await fetch(`http://127.0.0.1:5000/api/grace-status/${code}`);
      const graceStatus = await response.json();
      setGracePeriodInfo(graceStatus);
    } catch (error) {
      console.error('Failed to check grace period status:', error);
      setGracePeriodInfo(null);
    }
  };

  const handleRecheck = async () => {
    if (!courseCode) return;
    
    startLoading();
    try {
      const response = await fetch(`http://127.0.0.1:5000/api/recheck/${courseCode}`, {
        method: 'POST',
      });
      
      if (response.ok) {
        // Dismiss the warning temporarily and refresh analysis
        setDismissedGraceWarnings(prev => new Set(prev).add(courseCode));
        fetchAnalysisData(courseCode, advancedOptions);
      } else {
        const errorData = await response.json().catch(() => ({}));
        setAnalysisError(`Recheck failed: ${errorData.error || 'Unknown error'}`);
      }
    } catch (error) {
      setAnalysisError(`Recheck failed: ${String(error)}`);
    } finally {
      stopLoading();
    }
  };

  const fetchAnalysisData = (code, options) => {
    if (!code) return;

    setAnalysisError(null);
    setAnalysisResult(null);
    startLoading();

    // Shape the request body from advanced options
    const params = {
      stats: options.stats,
      filters: options.filters,
      separation_keys: options.separationKeys
    };

    fetch(`http://127.0.0.1:5000/api/analyze/${code}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    })
    .then(async response => {
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        // Specific 404/no data handling
        if (response.status === 404 || data?.error === 'No data found for this course.') {
          const searchUrl = `https://asen-jhu.evaluationkit.com/Report/Public/Results?Course=${encodeURIComponent(code)}`;
          setAnalysisError(`No course evaluations found for ${code}.<br/><br/>No evaluations found at this search: <a href="${searchUrl}" target="_blank" rel="noopener noreferrer">${searchUrl}</a>`);
          setAnalysisResult(null);
          return;
        }
        // Generic error handling with details
        const detail = typeof data?.error === 'string' ? data.error : 'Unknown error';
        setAnalysisError(`An error occurred, email icissna1@jh.edu with the following information to prevent it from happening again:<br/><br/>${detail}`);
        setAnalysisResult(null);
        return;
      }
      // Success
      console.log(data)
      if (data && !data.error) {
        setAnalysisResult(data);
        setAnalysisError(null);
      } else {
        const detail = typeof data?.error === 'string' ? data.error : 'Unknown error';
        setAnalysisError(`An error occurred, email icissna1@jh.edu with the following information to prevent it from happening again:<br/><br/>${detail}`);
        setAnalysisResult(null);
      }
    })
    .catch(error => {
      setAnalysisError(`An error occurred, email icissna1@jh.edu with the following information to prevent it from happening again:<br/><br/>${String(error)}`);
      setAnalysisResult(null);
    })
    .finally(() => { stopLoading(); });
  };

  const handleDataReceived = (newCourseCode) => {
    setCourseCode(newCourseCode);
    setDismissedGraceWarnings(new Set()); // Clear dismissed warnings for new course
    fetchAnalysisData(newCourseCode, advancedOptions);
    checkGracePeriodStatus(newCourseCode);
  };

  const handleTimeFilterToggle = () => {
    setAdvancedOptions(prev => {
      let newMinYear, newMaxYear;
      let newShowLast3YearsActive;

      if (showLast3YearsActive) {
        // Toggle off - clear the values
        newMinYear = '';
        newMaxYear = '';
        newShowLast3YearsActive = false;
      } else {
        // Toggle on - use sophisticated period-based calculation
        const yearRange = calculateLast3YearsRange();
        newMinYear = yearRange.min_year;
        newMaxYear = yearRange.max_year;
        newShowLast3YearsActive = true;
      }
      
      const updated = {
        ...prev,
        filters: {
          ...prev.filters,
          min_year: newMinYear,
          max_year: newMaxYear
        }
      };
      // Trigger backend call
      if (courseCode) {
        handleApplyAdvancedOptions(updated);
      }
      setShowLast3YearsActive(newShowLast3YearsActive);
      return updated;
    });
  };

  const handleSeparateByTeacherToggle = () => {
    setAdvancedOptions(prev => {
      const hasInstr = prev.separationKeys.includes('instructor');
      const newKeys = hasInstr
        ? prev.separationKeys.filter(key => key !== 'instructor')
        : [...prev.separationKeys, 'instructor'];
      const updated = { ...prev, separationKeys: newKeys };
      // Trigger backend call
      if (courseCode) {
        handleApplyAdvancedOptions(updated);
      }
      return updated;
    });
  };

  const handleSeparateByCourseCode = () => {
    setAdvancedOptions(prev => {
      const hasCourseCode = prev.separationKeys.includes('course_code');
      const newKeys = hasCourseCode
        ? prev.separationKeys.filter(key => key !== 'course_code')
        : [...prev.separationKeys, 'course_code'];
      const updated = { ...prev, separationKeys: newKeys };
      // Trigger backend call
      if (courseCode) {
        handleApplyAdvancedOptions(updated);
      }
      return updated;
    });
  };



  const handleApplyAdvancedOptions = (options) => {
    // Always update advanceOptions for column/rerender
    setAdvancedOptions(options);
    if (!courseCode) return;

    const validateYear = (year) => {
      if (year === '') return true; // Allow empty string to clear filter
      const parsedYear = parseInt(year, 10);
      return !isNaN(parsedYear) && parsedYear >= 2000;
    };

    const minYearValid = validateYear(options.filters.min_year);
    const maxYearValid = validateYear(options.filters.max_year);

    if (!minYearValid || !maxYearValid) {
      return;
    }

    // Only refetch for separation/filter changes, not stats-only
    const filtersChanged =
      JSON.stringify(options.filters) !== JSON.stringify(advancedOptions.filters);
    const separationChanged =
      JSON.stringify(options.separationKeys) !== JSON.stringify(advancedOptions.separationKeys);
    if (filtersChanged || separationChanged) {
      fetchAnalysisData(courseCode, options);
    }
    // For stats-only, DataDisplay will update immediately due to props/state
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>JHU Course Evaluation Analyzer</h1>
      </header>
      <main>
        <CourseSearch onDataReceived={handleDataReceived} onLoadingChange={(is) => is ? startLoading() : stopLoading()} />
        {/* Grouped courses codes banner - always show if grouped */}
        {analysisResult && analysisResult.grouping_metadata && analysisResult.grouping_metadata.is_grouped && (
          <div
            style={{
              background: "#ffe066",
              borderRadius: "6px",
              color: "#442",
              padding: "8px 16px",
              margin: "16px auto 0 auto",
              fontSize: "1.1rem",
              textAlign: "center",
              maxWidth: 650,
              border: "1px solid #ffcb66",
            }}
          >
            This course was automatically grouped with:&nbsp;
            {Array.isArray(analysisResult?.grouping_metadata?.grouped_courses)
              ? analysisResult.grouping_metadata.grouped_courses
                  .filter(code => code !== courseCode)
                  .map((code, idx, arr) =>
                    <span key={code}>
                      <b>{code}</b>{idx < arr.length - 1 ? ', ' : ''}
                    </span>
                  )
              : ''}
            <div style={{ marginTop: '12px' }}>
              <button 
                onClick={() => handleSeparateByCourseCode()}
                style={{
                  background: '#4CAF50',
                  color: 'white',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Separate by Course Code
              </button>
            </div>
          </div>
        )}
        {analysisResult && courseCode && (
          <div
            style={{
              marginTop: '20px',
              marginBottom: '10px',
              textAlign: 'center',
              fontWeight: 'bold',
              fontSize: '2rem',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center'
            }}
          >
            {/* If backend returns current_name and former_names fields, use them.
                Fallback to courseCode if not present. */}
            {analysisResult.current_name ? (
              <>
                <span>{analysisResult.current_name}</span>
                {Array.isArray(analysisResult.former_names) && analysisResult.former_names.length > 0 && (
                  <span style={{ fontSize: '1rem', color: 'gray', fontWeight: 'normal', marginTop: '0.2em' }}>
                    (formerly known as {analysisResult.former_names.join(', ')})
                  </span>
                )}
              </>
            ) : (
              <span>{courseCode}</span>
            )}
          </div>
        )}
        <GracePeriodWarning
          courseCode={courseCode}
          gracePeriodInfo={gracePeriodInfo}
          isDismissed={dismissedGraceWarnings.has(courseCode)}
          onRecheck={handleRecheck}
        />
        <div className="controls">
          <button onClick={handleTimeFilterToggle}>
            {showLast3YearsActive ? 'Show All Time' : 'Show Last 3 Years'}
          </button>
          <button onClick={handleSeparateByTeacherToggle}>
            {advancedOptions.separationKeys.includes('instructor') ? 'Combine Teachers' : 'Separate by Teacher'}
          </button>
        </div>
        <AdvancedOptions
          options={advancedOptions}
          onApply={handleApplyAdvancedOptions}
          courseMetadata={analysisResult ? {
            current_name: analysisResult.current_name,
            former_names: analysisResult.former_names
          } : null}
          showLast3YearsActive={showLast3YearsActive}
          onDeactivateLast3Years={() => setShowLast3YearsActive(false)}
        />
        <DataDisplay
          data={analysisResult ? (() => {
            const {
              current_name,
              former_names,
              last_period_gathered,
              last_period_failed,
              relevant_periods,
              last_scrape_during_grace_period,
              grouping_metadata,
              ...dataWithoutMetadata
            } = analysisResult;
            return dataWithoutMetadata;
          })() : null}
          selectedStats={Object.keys(advancedOptions.stats).filter(k => advancedOptions.stats[k])}
          errorMessage={analysisError}
        />
      </main>
      <footer className="app-footer">
        For questions, suggestions, bug reports, or <b>to combine the results of courses with multiple course codes (e.g. EN.601.4XX and EN.601.6XX)</b>, email <a href="mailto:icissna1@jh.edu">icissna1@jh.edu</a>
      </footer>
      {isLoading && <LoadingOverlay message="Analyzing course evaluations…" />}
    </div>
  );
}

export default App;
