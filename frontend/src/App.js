import React, { useState } from 'react';
import './App.css';
import CourseSearch from './components/CourseSearch';
import DataDisplay from './components/DataDisplay';
import AdvancedOptions from './components/AdvancedOptions';
import LoadingOverlay from './components/LoadingOverlay';
import GracePeriodWarning from './components/GracePeriodWarning';
import { STAT_MAPPINGS, DEFAULT_STATS, OPTIONAL_STATS } from './utils/statsMapping';

function App() {
  const [analysisResult, setAnalysisResult] = useState(null);
  const [courseCode, setCourseCode] = useState(null);
  const [advancedOptions, setAdvancedOptions] = useState({
    stats: {
      ...DEFAULT_STATS.reduce((acc, key) => ({ ...acc, [key]: true }), {}),
      ...OPTIONAL_STATS.reduce((acc, key) => ({ ...acc, [key]: false }), {})
    },
    filters: { min_year: '', max_year: '', seasons: [] },
    separationKeys: []
  });
  const [analysisError, setAnalysisError] = useState(null);
  const [loadingCount, setLoadingCount] = useState(0);
  const [gracePeriodInfo, setGracePeriodInfo] = useState(null);
  const [dismissedGraceWarnings, setDismissedGraceWarnings] = useState(new Set());
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
    const currentYear = new Date().getFullYear();
    setAdvancedOptions(prev => {
      const newMinYear = prev.filters.min_year ? '' : currentYear - 3;
      const newMaxYear = prev.filters.min_year ? '' : currentYear;
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

  const handleApplyAdvancedOptions = (options) => {
    // Always update advanceOptions for column/rerender
    setAdvancedOptions(options);
    if (!courseCode) return;
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
            {advancedOptions.filters.min_year === '' ? 'Show Last 3 Years' : 'Show All Time'}
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
        />
        <DataDisplay
          data={analysisResult ? (() => {
            const { current_name, former_names, ...dataWithoutMetadata } = analysisResult;
            return dataWithoutMetadata;
          })() : null}
          selectedStats={Object.keys(advancedOptions.stats).filter(k => advancedOptions.stats[k])}
          errorMessage={analysisError}
        />
      </main>
      {isLoading && <LoadingOverlay message="Analyzing course evaluations…" />}
    </div>
  );
}

export default App;
