import React, { useState } from 'react';
import './App.css';
import CourseSearch from './components/CourseSearch';
import DataDisplay from './components/DataDisplay';
import AdvancedOptions from './components/AdvancedOptions';
import LoadingOverlay from './components/LoadingOverlay';
import GracePeriodWarning from './components/GracePeriodWarning';
import { STATISTICS_CONFIG, ALL_STAT_KEYS } from './utils/statsMapping';
import { calculateLast3YearsRange } from './utils/yearUtils';
import { API_BASE_URL } from './config';
import Footer from './components/Footer';
import { addToSearchHistory } from './utils/storageUtils';
import { processAnalysisRequest } from './utils/analysisEngine.js';

function App() {
  const [analysisResult, setAnalysisResult] = useState(null);
  const [rawCourseData, setRawCourseData] = useState(null);
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
  const isLoading = loadingCount > 0;
  const startLoading = () => setLoadingCount(c => c + 1);
  const stopLoading = () => setLoadingCount(c => Math.max(0, c - 1));


  const checkGracePeriodStatus = async (code) => {
    if (!code) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/grace-status/${code}`);
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
        const response = await fetch(`${API_BASE_URL}/api/recheck/${courseCode}`, { method: 'POST' });
        if (response.ok) {
            setDismissedGraceWarnings(prev => new Set(prev).add(courseCode));
            setRawCourseData(null); // Invalidate raw data to force refetch
            fetchAnalysisData(courseCode, advancedOptions, true);
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

  const fetchAnalysisData = (code, options, forceBackend = false) => {
    if (!code) return;

    if (rawCourseData && rawCourseData.courseCode === code && !forceBackend) {
        try {
            const result = processAnalysisRequest(rawCourseData.data, {
                stats: options.stats,
                filters: options.filters,
                separationKeys: options.separationKeys
            });
            setAnalysisResult(result);
        } catch (error) {
            console.error('Frontend processing error:', error);
            fetchAnalysisData(code, options, true); // Fallback to backend
        }
        return;
    }

    setAnalysisError(null);
    setAnalysisResult(null);
    startLoading();

    const params = {
      stats: options.stats,
      filters: options.filters,
      separation_keys: options.separationKeys,
      raw_data_mode: true // NEW FLAG
    };

    fetch(`${API_BASE_URL}/api/analyze/${code}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    })
    .then(async response => {
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        if (response.status === 404 || data?.error === 'No data found for this course.') {
          addToSearchHistory(code, 'No data');
          const searchUrl = `https://asen-jhu.evaluationkit.com/Report/Public/Results?Course=${encodeURIComponent(code)}`;
          setAnalysisError(`No course evaluations found for ${code}.<br/><br/>No evaluations found at this search: <a href="${searchUrl}" target="_blank" rel="noopener noreferrer">${searchUrl}</a>`);
          setAnalysisResult(null);
          return;
        }
        const detail = typeof data?.error === 'string' ? data.error : 'Unknown error';
        setAnalysisError(`An error occurred, email icissna1@jh.edu with the following information to prevent it from happening again:<br/><br/>${detail}`);
        setAnalysisResult(null);
        setRawCourseData(null);
        return;
      }
      
      setRawCourseData({ courseCode: code, data: data.raw_data });
      const result = processAnalysisRequest(data.raw_data, {
          stats: options.stats,
          filters: options.filters,
          separationKeys: options.separationKeys
      });
      setAnalysisResult(result);
      setAnalysisError(null);
      const courseName = result.metadata?.current_name || 'No data';
      addToSearchHistory(code, courseName);
    })
    .catch(error => {
      setAnalysisError(`An error occurred, email icissna1@jh.edu with the following information to prevent it from happening again:<br/><br/>${String(error)}`);
      setAnalysisResult(null);
      setRawCourseData(null);
    })
    .finally(() => { stopLoading(); });
  };

  const handleDataReceived = (newCourseCode) => {
    setCourseCode(newCourseCode);
    setRawCourseData(null);
    setDismissedGraceWarnings(new Set());
    fetchAnalysisData(newCourseCode, advancedOptions, true);
    checkGracePeriodStatus(newCourseCode);
  };

  const handleTimeFilterToggle = () => {
    setAdvancedOptions(prev => {
      let newMinYear, newMaxYear;
      let newShowLast3YearsActive;

      if (showLast3YearsActive) {
        newMinYear = '';
        newMaxYear = '';
        newShowLast3YearsActive = false;
      } else {
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
      if (courseCode) {
        handleApplyAdvancedOptions(updated);
      }
      return updated;
    });
  };

  const handleApplyAdvancedOptions = (options) => {
    setAdvancedOptions(options);
    if (!courseCode) return;

    const validateYear = (year) => {
      if (year === '') return true;
      const parsedYear = parseInt(year, 10);
      return !isNaN(parsedYear) && parsedYear >= 2000;
    };

    const minYearValid = validateYear(options.filters.min_year);
    const maxYearValid = validateYear(options.filters.max_year);

    if (!minYearValid || !maxYearValid) {
      return;
    }

    if (rawCourseData && rawCourseData.courseCode === courseCode) {
        try {
            const result = processAnalysisRequest(rawCourseData.data, {
                stats: options.stats,
                filters: options.filters,
                separationKeys: options.separationKeys
            });
            setAnalysisResult(result);
        } catch (error) {
            console.error('Frontend processing error:', error);
            fetchAnalysisData(courseCode, options, true);
        }
    } else {
        fetchAnalysisData(courseCode, options, true);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>JHU Course Evaluation Analyzer</h1>
      </header>
      <main>
        <CourseSearch 
          onDataReceived={handleDataReceived} 
          onLoadingChange={(is) => is ? startLoading() : stopLoading()}
          currentCourseCode={courseCode} 
        />
        {analysisResult && analysisResult.metadata?.grouping_metadata?.is_grouped && (
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
            {Array.isArray(analysisResult?.metadata?.grouping_metadata?.grouped_courses)
              ? analysisResult.metadata.grouping_metadata.grouped_courses
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
            {analysisResult.metadata?.current_name ? (
              <>
                <span>{analysisResult.metadata.current_name}</span>
                {Array.isArray(analysisResult.metadata.former_names) && analysisResult.metadata.former_names.length > 0 && (
                  <span style={{ fontSize: '1rem', color: 'gray', fontWeight: 'normal', marginTop: '0.2em' }}>
                    (formerly known as {analysisResult.metadata.former_names.join(', ')})
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
            {advancedOptions.separationKeys.includes('instructor') ? 'Combine Professors' : 'Separate by Professor'}
          </button>
        </div>
        <AdvancedOptions
          options={advancedOptions}
          onApply={handleApplyAdvancedOptions}
          courseMetadata={analysisResult?.metadata ? {
            current_name: analysisResult.metadata.current_name,
            former_names: analysisResult.metadata.former_names
          } : null}
          showLast3YearsActive={showLast3YearsActive}
          onDeactivateLast3Years={() => setShowLast3YearsActive(false)}
        />
        {analysisResult && (
          <p style={{ textAlign: 'center', margin: '20px 0', fontWeight: 'bold' }}>
            All numeric results are between 1 and 5
          </p>
        )}
        <DataDisplay
          data={analysisResult?.data || null}
          selectedStats={Object.keys(advancedOptions.stats).filter(k => advancedOptions.stats[k])}
          errorMessage={analysisError}
          statisticsMetadata={analysisResult?.statistics_metadata || {}}
        />
      </main>
      <Footer />
      {isLoading && <LoadingOverlay message="Analyzing course evaluations…" />}
    </div>
  );
}

export default App;