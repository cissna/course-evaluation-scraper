import React, { useState } from 'react';
import './App.css';
import CourseSearch from './components/CourseSearch';
import DataDisplay from './components/DataDisplay';
import AdvancedOptions from './components/AdvancedOptions';
import LoadingOverlay from './components/LoadingOverlay';

function App() {
  const [analysisResult, setAnalysisResult] = useState(null);
  const [courseCode, setCourseCode] = useState(null);
  const [timeFilter, setTimeFilter] = useState('all'); // 'all' or 'last3years'
  const [separateByTeacher, setSeparateByTeacher] = useState(false);
  const [analysisError, setAnalysisError] = useState(null);
  const [loadingCount, setLoadingCount] = useState(0);
  const isLoading = loadingCount > 0;
  const startLoading = () => setLoadingCount(c => c + 1);
  const stopLoading = () => setLoadingCount(c => Math.max(0, c - 1));

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
          setAnalysisError(`No course evaluations found for ${code}`);
          setAnalysisResult(null);
          return;
        }
        // Generic error handling with details
        const detail = typeof data?.error === 'string' ? data.error : 'Unknown error';
        setAnalysisError(`An error occurred, email icissna1@jh.edu with the following information to prevent it from happening again:\n${detail}`);
        setAnalysisResult(null);
        return;
      }
      // Handle success, but guard against unexpected error payloads
      if (data && !data.error) {
        setAnalysisResult(data);
        setAnalysisError(null);
      } else {
        const detail = typeof data?.error === 'string' ? data.error : 'Unknown error';
        setAnalysisError(`An error occurred, email icissna1@jh.edu with the following information to prevent it from happening again:\n${detail}`);
        setAnalysisResult(null);
      }
    })
    .catch(error => {
      setAnalysisError(`An error occurred, email icissna1@jh.edu with the following information to prevent it from happening again:\n${String(error)}`);
      setAnalysisResult(null);
    })
    .finally(() => { stopLoading(); });
  };

  const handleDataReceived = (newCourseCode) => {
    setCourseCode(newCourseCode);
    fetchAnalysisData(newCourseCode, timeFilter, separateByTeacher);
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
        <div className="controls">
          <button onClick={handleTimeFilterToggle}>
            {timeFilter === 'all' ? 'Show Last 3 Years' : 'Show All Time'}
          </button>
          <button onClick={handleSeparateByTeacherToggle}>
            {separateByTeacher ? 'Combine Teachers' : 'Separate by Teacher'}
          </button>
        </div>
        <AdvancedOptions onApply={handleApplyAdvancedOptions} />
        <DataDisplay data={analysisResult} errorMessage={analysisError} />
      </main>
      {isLoading && <LoadingOverlay message="Analyzing course evaluations…" />}
    </div>
  );
}

export default App;
