import React, { useState } from 'react';
import './App.css';
import CourseSearch from './components/CourseSearch';
import DataDisplay from './components/DataDisplay';
import AdvancedOptions from './components/AdvancedOptions';
import LoadingOverlay from './components/LoadingOverlay';
import GracePeriodWarning from './components/GracePeriodWarning';

function App() {
  const [analysisResult, setAnalysisResult] = useState(null);
  const [courseCode, setCourseCode] = useState(null);
  const [timeFilter, setTimeFilter] = useState('all'); // 'all' or 'last3years'
  const [separateByTeacher, setSeparateByTeacher] = useState(false);
  const [analysisError, setAnalysisError] = useState(null);
  const [loadingCount, setLoadingCount] = useState(0);
  const [gracePeriodInfo, setGracePeriodInfo] = useState(null);
  const [dismissedGraceWarnings, setDismissedGraceWarnings] = useState(new Set());
  const isLoading = loadingCount > 0;
  const startLoading = () => setLoadingCount(c => c + 1);
  const stopLoading = () => setLoadingCount(c => Math.max(0, c - 1));

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
        fetchAnalysisData(courseCode, timeFilter, separateByTeacher);
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

  const fetchAnalysisData = (code, filter, separate) => {
    if (!code) return;

    let filters = {};
    if (filter === 'last3years') {
      const currentYear = new Date().getFullYear();
      filters.min_year = currentYear - 3;
    }

    const params = {
      filters: filters,
      separation_key: separate ? 'instructor' : null,
    };

    // reset state before fetch
    setAnalysisError(null);
    setAnalysisResult(null);
    startLoading();

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
      // Handle success, but guard against unexpected error payloads
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
    fetchAnalysisData(newCourseCode, timeFilter, separateByTeacher);
    checkGracePeriodStatus(newCourseCode);
  };

  const handleTimeFilterToggle = () => {
    const newFilter = timeFilter === 'all' ? 'last3years' : 'all';
    setTimeFilter(newFilter);
    fetchAnalysisData(courseCode, newFilter, separateByTeacher);
  };

  const handleSeparateByTeacherToggle = () => {
    const newSeparate = !separateByTeacher;
    setSeparateByTeacher(newSeparate);
    fetchAnalysisData(courseCode, timeFilter, newSeparate);
  };

  const handleApplyAdvancedOptions = (options) => {
    // This function will eventually replace the simpler toggles
    console.log("Advanced options applied:", options);
    // For now, just log the options. Later, this will trigger a new API call.
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
            {timeFilter === 'all' ? 'Show Last 3 Years' : 'Show All Time'}
          </button>
          <button onClick={handleSeparateByTeacherToggle}>
            {separateByTeacher ? 'Combine Teachers' : 'Separate by Teacher'}
          </button>
        </div>
        <AdvancedOptions onApply={handleApplyAdvancedOptions} />
        <DataDisplay
          data={analysisResult ? (() => {
            const { current_name, former_names, ...dataWithoutMetadata } = analysisResult;
            return dataWithoutMetadata;
          })() : null}
          errorMessage={analysisError}
        />
      </main>
      {isLoading && <LoadingOverlay message="Analyzing course evaluations…" />}
    </div>
  );
}

export default App;
