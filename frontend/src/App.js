import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import './App.css';
import CourseSearch from './components/CourseSearch';
import SearchResults from './components/SearchResults';
import ResultView from './components/ResultView';
import AdvancedOptions from './components/AdvancedOptions';
import DataDisplay from './components/DataDisplay';
import Footer from './components/Footer';
import ComparisonMetric from './components/ComparisonMetric';
import RefreshNotice from './components/RefreshNotice';
import { RATING_STAT_KEYS } from './utils/statsMapping';
import { compareSamples, toggleRowSelection } from './utils/significance';
import { calculateLast3YearsRange } from './utils/yearUtils';
import { toggleSeparation } from './utils/separationOptions';
import { getShowPercentilesPreference, saveShowPercentilesPreference, getPercentileWeightingPreference, savePercentileWeightingPreference,
  getStatisticsPreferences, saveStatisticsPreferences } from './utils/storageUtils';
import { loadResultWithData } from './hooks/useEvaluationResult';
import useRefreshNotifications from './hooks/useRefreshNotifications';
import { API_BASE_URL } from './config';

const MAX_RESULTS = 5;

function App() {
  const [selections, setSelections] = useState([]);
  const [searchView, setSearchView] = useState(null);
  const [analyses, setAnalyses] = useState({});
  const [refreshStates, setRefreshStates] = useState({});
  const notifications = useRefreshNotifications();
  const [benchmark, setBenchmark] = useState(null);
  const [expanded, setExpanded] = useState(false);
  const [last3Years, setLast3Years] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [selectedRows, setSelectedRows] = useState([]);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [metric, setMetric] = useState('overall_quality');
  const selectionRequest = useRef(null);
  const selectionsRef = useRef(selections);
  selectionsRef.current = selections;
  const [options, setOptions] = useState(() => ({
    ...getStatisticsPreferences(),
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
    setRefreshStates(previous => Object.fromEntries(Object.entries(previous).filter(([id]) => ids.has(id))));
  }, [selections]);
  const handleAnalysis = useCallback((id, analysis) => {
    setAnalyses(previous => previous[id] === analysis ? previous : { ...previous, [id]: analysis });
  }, []);
  const handleRefreshState = useCallback((id, state) => {
    setRefreshStates(previous => previous[id] === state ? previous : { ...previous, [id]: state });
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
        setSelectedRows([]);
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
      if (intent === 'replace') setSelectedRows([]);
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
    if (next.stats !== options.stats || next.significanceThreshold !== options.significanceThreshold) saveStatisticsPreferences(next);
    if (next.weightPercentilesByClassSize !== options.weightPercentilesByClassSize) {
      savePercentileWeightingPreference(next.weightPercentilesByClassSize);
    }
  };
  const toggleYears = () => {
    const bounds = last3Years ? { min_year: '', max_year: '' } : calculateLast3YearsRange();
    setOptions(previous => ({ ...previous, filters: { ...previous.filters, ...bounds } }));
    setLast3Years(!last3Years);
  };
  const isSideBySide = selections.length > 1;
  const hasCourses = !selections.length || selections.some(result => result.type === 'course');
  const hasProfessors = selections.some(result => result.type === 'professor');
  const hasFormerNames = selections.some(result => analyses[result.id]?.metadata?.former_names?.length || analyses[result.id]?.metadata?.has_former_names);
  const visibleMetrics = RATING_STAT_KEYS.filter(key => options.stats[key]);
  const effectiveMetric = visibleMetrics.includes(metric) ? metric : visibleMetrics[0] || null;
  useEffect(() => {
    if (metric !== effectiveMetric) setMetric(effectiveMetric);
  }, [metric, effectiveMetric]);
  const displayedRowCount = Object.values(options.stats).some(Boolean) ? selections.reduce((count, result) => {
    const analysis = analyses[result.id];
    return count + (analysis?.year_range_empty ? 0 : Object.keys(analysis?.data || {}).length);
  }, 0) : 0;
  const canSelectRows = comparisonMode && displayedRowCount >= 2;
  const activeRows = useMemo(() => canSelectRows ? selectedRows.filter(row =>
    selections.some(result => result.id === row.resultId) && Object.values(options.stats).some(Boolean) &&
    !analyses[row.resultId]?.year_range_empty && Object.prototype.hasOwnProperty.call(analyses[row.resultId]?.data || {}, row.groupName)
  ) : [], [canSelectRows, selectedRows, selections, analyses, options.stats]);
  useEffect(() => {
    if (activeRows.length !== selectedRows.length) setSelectedRows(activeRows);
  }, [activeRows, selectedRows.length]);
  const toggleComparisonMode = () => {
    if (!comparisonMode && displayedRowCount < 2) {
      window.alert(selections.length === 1 && selections[0].type === 'professor'
        ? "You cannot enter comparison mode before you add a course or professor to compare or separate the entries of this professor (e.g. by course)."
        : 'You cannot enter comparison mode before you add a course to compare or separate the entries of this course (e.g. by professor).');
      return;
    }
    setComparisonMode(previous => !previous);
    setSelectedRows([]);
  };
  const selectRow = (resultId, groupName) => {
    if (canSelectRows) setSelectedRows(previous => toggleRowSelection(previous, { resultId, groupName }));
  };
  const comparison = activeRows.length === 2 ? effectiveMetric ? compareSamples(
    analyses[activeRows[0].resultId]?.statistics_metadata?.[activeRows[0].groupName]?.[effectiveMetric],
    analyses[activeRows[1].resultId]?.statistics_metadata?.[activeRows[1].groupName]?.[effectiveMetric],
    options.significanceThreshold
  ) : { available: false, significant: false, reason: 'show a rating metric to compare these rows.' } : null;
  const labelParts = activeRows.map(row => {
    const source = selections.find(result => result.id === row.resultId);
    const sourceLabel = source.type === 'course' ? source.code : source.name;
    const groupLabel = analyses[row.resultId]?.group_labels?.[row.groupName]?.label || row.groupName;
    return { ...row, sourceLabel, groupLabel };
  });
  const sharedSource = labelParts.length === 2 && labelParts[0].resultId === labelParts[1].resultId;
  const sharedGroup = labelParts.length === 2 && labelParts[0].groupLabel === labelParts[1].groupLabel;
  const sharedLabel = sharedSource ? labelParts[0].sourceLabel : sharedGroup ? labelParts[0].groupLabel : null;
  const rowLabels = labelParts.map(({ sourceLabel, groupLabel }) =>
    sharedSource ? groupLabel : sharedGroup ? sourceLabel : `${sourceLabel} — ${groupLabel}`);
  const metricControl = <ComparisonMetric enabled={comparisonMode} onToggle={toggleComparisonMode}
    visibleMetrics={visibleMetrics} metric={effectiveMetric} onChange={setMetric}
    comparison={comparison} labels={rowLabels} sharedLabel={sharedLabel} threshold={options.significanceThreshold} />;
  const controls = <>
    <div className="controls">
      <button onClick={toggleYears}>{last3Years ? 'Show All Time' : 'Show Last 3 Years'}</button>
      {hasCourses && <button onClick={() => separate('instructor')}>{options.separationKeys.includes('instructor') ? 'Combine Professors' : 'Separate by Professor'}</button>}
      {hasProfessors && <button onClick={() => separate('course_group')}>{options.separationKeys.includes('course_group') ? 'Combine Courses' : 'Separate by Course'}</button>}
      <label className="percentile-control"><input type="checkbox" checked={options.showPercentiles} onChange={changePercentiles} />Show percentiles</label>
    </div>
    <AdvancedOptions options={options} onApply={applyAdvancedOptions} hasCourses={hasCourses} hasProfessors={hasProfessors}
      hasFormerNames={hasFormerNames} comparisonMode={comparisonMode} showLast3YearsActive={last3Years} onDeactivateLast3Years={() => setLast3Years(false)} expanded={expanded} onExpandedChange={setExpanded} />
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
        {isSideBySide && <><div className="comparison-heading"><h2>{comparisonMode ? 'Comparison View' : 'Side-by-Side View'}</h2>{metricControl}</div>{controls}
          <RefreshNotice results={selections.map(selection => ({ selection, state: refreshStates[selection.id] }))} notifications={notifications} shared />
        </>}
        <div className={isSideBySide ? 'comparison-results' : 'single-result'}>
          {selections.map(selection => <ResultView key={selection.id} selection={selection} options={options} benchmark={benchmark}
            headingExtra={!isSideBySide && metricControl} comparisonMetric={comparisonMode ? effectiveMetric : null} significant={comparison?.significant}
            rowTones={Object.fromEntries(activeRows.map((row, index) => [row, index]).filter(([row]) => row.resultId === selection.id)
              .map(([row, index]) => [row.groupName, index === activeRows.length - 1 ? 'red' : 'orange']))}
            onRowSelect={canSelectRows ? selectRow : undefined}
            onMetricSelect={comparisonMode ? setMetric : undefined}
            onAnalysis={handleAnalysis} onRefreshState={handleRefreshState} notifications={notifications} sharedRefresh={isSideBySide}
            onToggleSeparation={separate} onRemove={isSideBySide ? () => removeResult(selection.id) : undefined}>
            {!isSideBySide && controls}
          </ResultView>)}
        </div>
        {!selections.length && <>{controls}<DataDisplay data={null} /></>}
      </div>
    </main>
    <Footer />
  </div>;
}
export default App;
