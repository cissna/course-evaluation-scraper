import React, { useState } from 'react';
import './App.css';
import CourseSearch from './components/CourseSearch';
import DataDisplay from './components/DataDisplay';
import AdvancedOptions from './components/AdvancedOptions';

function App() {
  const [analysisResult, setAnalysisResult] = useState(null);
  const [courseCode, setCourseCode] = useState(null);
  const [timeFilter, setTimeFilter] = useState('all'); // 'all' or 'last3years'
  const [separateByTeacher, setSeparateByTeacher] = useState(false);

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

    fetch(`http://127.0.0.1:5000/api/analyze/${code}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    })
    .then(response => response.json())
    .then(data => setAnalysisResult(data))
    .catch(error => console.error("Analysis API call failed:", error));
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
        <CourseSearch onDataReceived={handleDataReceived} />
        <div className="controls">
          <button onClick={handleTimeFilterToggle}>
            {timeFilter === 'all' ? 'Show Last 3 Years' : 'Show All Time'}
          </button>
          <button onClick={handleSeparateByTeacherToggle}>
            {separateByTeacher ? 'Combine Teachers' : 'Separate by Teacher'}
          </button>
        </div>
        <AdvancedOptions onApply={handleApplyAdvancedOptions} />
        <DataDisplay data={analysisResult} />
      </main>
    </div>
  );
}

export default App;
