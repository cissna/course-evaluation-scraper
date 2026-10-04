import React, { useCallback, useEffect, useRef, useState } from 'react';
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
import { getShowPercentilesPreference, saveShowPercentilesPreference, getPercentileWeightingPreference, savePercentileWeightingPreference } from './utils/storageUtils';
import { loadResultWithData } from './hooks/useEvaluationResult';
import { API_BASE_URL } from './config';

const MAX_RESULTS = 5;

function App() {
  const [selections, setSelections] = useState([]);
  const [searchView, setSearchView] = useState(null);
  const [analyses, setAnalyses] = useState({});
  const [benchmark, setBenchmark] = useState(null);
  const [expanded, setExpanded] = useState(false);
  const [last3Years, setLast3Years] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const selectionRequest = useRef(null);
  const selectionsRef = useRef(selections);
  selectionsRef.current = selections;
  const [options, setOptions] = useState(() => ({
    stats: getInitialStatsState(),
    filters: { min_year: '', max_year: '', seasons: [], exclude_summer: false, exclude_intersession: false },
    separationKeys: [], showPercentiles: getShowPercentilesPreference(),
    weightPercentilesByClassSize: getPercentileWeightingPreference(),
  }));
  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_BASE_URL}/api/percentiles`, { signal: controller.signal })
      .then(response => response.ok ? response.json() : null)
      .then(payload => { if (payload && !controller.signal.aborted) setBenchmark(payload.benchmark); })
      .catch(() => {});
    return () => { controller.abort(); selectionRequest.current?.abort(); };
  }, []);
  useEffect(() => {
    const ids = new Set(selections.map(result => result.id));
    setAnalyses(previous => Object.fromEntries(Object.entries(previous).filter(([id]) => ids.has(id))));
  }, [selections]);
  const handleAnalysis = useCallback((id, analysis) => {
    setAnalyses(previous => previous[id] === analysis ? previous : { ...previous, [id]: analysis });
  }, []);

  const resetCourseSeparation = () => setOptions(previous => ({ ...previous,
    separationKeys: previous.separationKeys.filter(key => key !== 'course_name' && key !== 'course_code'),
  }));
  const openResult = async (result, intent = 'replace') => {
    if (!result) return;
    selectionRequest.current?.abort();
    setSearchError(null);
    const existing = selectionsRef.current.find(item => item.id === result.id);
    if (existing) {
      if (intent === 'replace') {
        if (selectionsRef.current.length > 1) resetCourseSeparation();
        setSelections([existing]);
      }
      setSearchView(null);
      setResolving(false);
      return;
    }
    if (intent === 'add' && selectionsRef.current.length >= MAX_RESULTS) {
      setSearchError('Remove a course or professor to add another.');
      setResolving(false);
      return;
    }
    const controller = new AbortController();
    selectionRequest.current = controller;
    setResolving(true);
    try {
      // Commit a new destination only once there are actual saved evaluations.
      // Until then, normal and add searches both leave current tables usable.
      const initialSaved = await loadResultWithData(result, controller.signal);
      if (controller.signal.aborted) return;
      const ready = { ...result, initialSaved };
      setSelections(previous => intent === 'replace' ? [ready]
        : previous.length < MAX_RESULTS && !previous.some(item => item.id === ready.id) ? [...previous, ready] : previous);
      // A replacement starts a new course context; additions keep shared controls.
      if (intent === 'replace') resetCourseSeparation();
      setSearchView(null);
    } catch (error) {
      if (!controller.signal.aborted) {
        setSearchError(error.message);
        setSearchView(null);
      }
    } finally {
      if (selectionRequest.current === controller) setResolving(false);
    }
  };
  const removeResult = id => setSelections(previous => previous.filter(result => result.id !== id));
  const separate = key => setOptions(previous => ({ ...previous, separationKeys: toggleSeparation(previous.separationKeys, key) }));
  const changePercentiles = event => {
    const showPercentiles = event.target.checked;
    setOptions(previous => ({ ...previous, showPercentiles }));
    saveShowPercentilesPreference(showPercentiles);
  };
  const applyAdvancedOptions = next => {
    setOptions(next);
    if (next.weightPercentilesByClassSize !== options.weightPercentilesByClassSize) {
      savePercentileWeightingPreference(next.weightPercentilesByClassSize);
    }
  };
  const toggleYears = () => {
    const bounds = last3Years ? { min_year: '', max_year: '' } : calculateLast3YearsRange();
    setOptions(previous => ({ ...previous, filters: { ...previous.filters, ...bounds } }));
    setLast3Years(!last3Years);
  };
  const isComparison = selections.length > 1;
  const hasCourses = !selections.length || selections.some(result => result.type === 'course');
  const hasProfessors = selections.some(result => result.type === 'professor');
  const hasFormerNames = selections.some(result => analyses[result.id]?.metadata?.former_names?.length || analyses[result.id]?.metadata?.has_former_names);
  const controls = <>
    <div className="controls">
      <button onClick={toggleYears}>{last3Years ? 'Show All Time' : 'Show Last 3 Years'}</button>
      {hasCourses && <button onClick={() => separate('instructor')}>{options.separationKeys.includes('instructor') ? 'Combine Professors' : 'Separate by Professor'}</button>}
      {hasProfessors && <button onClick={() => separate('course_group')}>{options.separationKeys.includes('course_group') ? 'Combine Courses' : 'Separate by Course'}</button>}
      <label className="percentile-control"><input type="checkbox" checked={options.showPercentiles} onChange={changePercentiles} />Show percentiles</label>
    </div>
    <AdvancedOptions options={options} onApply={applyAdvancedOptions} hasCourses={hasCourses} hasProfessors={hasProfessors}
      hasFormerNames={hasFormerNames} showLast3YearsActive={last3Years} onDeactivateLast3Years={() => setLast3Years(false)} expanded={expanded} onExpandedChange={setExpanded} />
    {selections.length > 0 && <p className="ratings-caption">{options.showPercentiles
      ? options.weightPercentilesByClassSize ? 'Ratings shown as percentiles of course averages, weighted by average class size.' : 'Ratings shown as percentiles of course averages.'
      : 'Ratings are on a 1–5 scale.'}</p>}
  </>;
  return <div className="App">
    <header className="App-header"><h1>JHU Course Evaluation Analyzer</h1></header>
    <main>
      <div hidden={Boolean(searchView)}><CourseSearch onDataReceived={openResult}
        currentResultId={selections.length === 1 ? selections[0].id : undefined} hasResults={selections.length > 0}
        atComparisonLimit={selections.length >= MAX_RESULTS} resolving={resolving} searchError={searchError} onSearchStart={() => setSearchError(null)}
        onMultipleResults={(query, matches, intent) => setSearchView({ query, matches, intent })} /></div>
      {searchView && <SearchResults key={`${searchView.query}:${searchView.intent}`} searchQuery={searchView.query} initialResults={searchView.matches}
        intent={searchView.intent} resolving={resolving} onResultSelect={openResult} onBack={() => setSearchView(null)} />}
      <div hidden={Boolean(searchView && searchView.intent !== 'add')}>
        {isComparison && <><div className="comparison-heading"><h2>Comparison</h2></div>{controls}</>}
        <div className={isComparison ? 'comparison-results' : 'single-result'}>
          {selections.map(selection => <ResultView key={selection.id} selection={selection} options={options} benchmark={benchmark}
            onAnalysis={handleAnalysis} onToggleSeparation={separate} onRemove={isComparison ? () => removeResult(selection.id) : undefined}>
            {!isComparison && controls}
          </ResultView>)}
        </div>
        {!selections.length && <>{controls}<DataDisplay data={null} /></>}
      </div>
    </main>
    <Footer />
  </div>;
}
export default App;
