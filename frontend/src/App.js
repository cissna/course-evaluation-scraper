import React, { useCallback, useEffect, useState } from 'react';
import './App.css';
import CourseSearch from './components/CourseSearch';
import SearchResults from './components/SearchResults';
import ResultView from './components/ResultView';
import AdvancedOptions from './components/AdvancedOptions';
import DataDisplay from './components/DataDisplay';
import Footer from './components/Footer';
import { getInitialStatsState } from './utils/statsMapping';
import { calculateLast3YearsRange } from './utils/yearUtils';
import { toggleSeparation } from './utils/separationOptions';
import { API_BASE_URL } from './config';

function App() {
  const [selection, setSelection] = useState(null);
  const [searchView, setSearchView] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [benchmark, setBenchmark] = useState(null);
  const [expanded, setExpanded] = useState(false);
  const [last3Years, setLast3Years] = useState(false);
  const [options, setOptions] = useState({
    stats: getInitialStatsState(),
    filters: { min_year: '', max_year: '', seasons: [], exclude_summer: false, exclude_intersession: false },
    separationKeys: [], showPercentiles: false,
  });
  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_BASE_URL}/api/percentiles`, { signal: controller.signal })
      .then(response => response.ok ? response.json() : null)
      .then(payload => { if (payload && !controller.signal.aborted) setBenchmark(payload.benchmark); })
      .catch(() => {});
    return () => controller.abort();
  }, []);
  const handleMetadata = useCallback(next => setMetadata(next), []);
  const openResult = result => {
    if (!result) return;
    setSearchView(null);
    if (selection?.id !== result.id) { setMetadata(null); setSelection(result); }
  };
  const separate = key => setOptions(previous => ({ ...previous, separationKeys: toggleSeparation(previous.separationKeys, key) }));
  const toggleYears = () => {
    const bounds = last3Years ? { min_year: '', max_year: '' } : calculateLast3YearsRange();
    setOptions(previous => ({ ...previous, filters: { ...previous.filters, ...bounds } }));
    setLast3Years(!last3Years);
  };
  const professor = selection?.type === 'professor';
  const controls = <>
    <div className="controls">
      <button onClick={toggleYears}>{last3Years ? 'Show All Time' : 'Show Last 3 Years'}</button>
      {professor ? <button onClick={() => separate('course_group')}>{options.separationKeys.includes('course_group') ? 'Combine Courses' : 'Separate by Course'}</button>
        : <button onClick={() => separate('instructor')}>{options.separationKeys.includes('instructor') ? 'Combine Professors' : 'Separate by Professor'}</button>}
      <label className="percentile-control"><input type="checkbox" checked={options.showPercentiles} onChange={event => setOptions(previous => ({ ...previous, showPercentiles: event.target.checked }))} />Show percentiles</label>
    </div>
    <AdvancedOptions options={options} onApply={setOptions} hasCourses={!professor} hasProfessors={professor}
      hasFormerNames={Boolean(metadata?.former_names?.length || metadata?.has_former_names)}
      showLast3YearsActive={last3Years} onDeactivateLast3Years={() => setLast3Years(false)} expanded={expanded} onExpandedChange={setExpanded} />
    {selection && <p className="ratings-caption">{options.showPercentiles ? 'Ratings shown as percentiles of course averages.' : 'Ratings are on a 1–5 scale.'}</p>}
  </>;
  return <div className="App">
    <header className="App-header"><h1>JHU Course Evaluation Analyzer</h1></header>
    <main>
      <div hidden={Boolean(searchView)}><CourseSearch onDataReceived={openResult} currentResultId={selection?.id}
        onMultipleResults={(query, matches) => setSearchView({ query, matches })} /></div>
      {searchView && <SearchResults key={searchView.query} searchQuery={searchView.query} initialResults={searchView.matches} onResultSelect={openResult} onBack={() => setSearchView(null)} />}
      <div hidden={Boolean(searchView)}>
        {selection ? <ResultView key={selection.id} selection={selection} options={options} benchmark={benchmark}
          onMetadata={handleMetadata} onToggleSeparation={separate}>{controls}</ResultView>
          : <>{controls}<DataDisplay data={null} /></>}
      </div>
    </main>
    <Footer />
  </div>;
}
export default App;
