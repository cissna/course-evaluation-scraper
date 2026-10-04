import React, { useEffect, useLayoutEffect, useMemo } from 'react';
import DataDisplay from './DataDisplay';
import InfoTooltip from './InfoTooltip';
import './GracePeriodWarning.css';
import useEvaluationResult from '../hooks/useEvaluationResult';
import { processAnalysisRequest } from '../utils/analysisEngine';
import { addToSearchHistory } from '../utils/storageUtils';

export const GROUPING_EXPLANATION = 'For some courses, undergraduate reviews are included with the graduate section, so using this separation to understand the undergrad/grad breakdown isn’t useful.';

export function ResultHeading({ selection, metadata, onRemove }) {
  return (
    <div className="result-heading">
      <span className="result-heading-title">{selection.type === 'professor' ? selection.name : metadata?.current_name || selection.code}
        {onRemove && <button className="remove-result" onClick={onRemove} aria-label={`Remove ${selection.code || selection.name} from comparison`}>×</button>}
      </span>
      {selection.type === 'course' && <>
        {metadata?.former_names?.length > 0 && <span className="result-subtitle">(formerly known as {metadata.former_names.join(', ')})</span>}
        {metadata?.current_name && <span className="result-subtitle">{selection.code}</span>}
      </>}
    </div>
  );
}

function RefreshNotice({ selection, state }) {
  const { courses, refresh, pendingData, rawData, recheck, showUpdated, enableNotifications, notificationMessage } = state;
  const stale = courses.filter(course => course.needs_warning || course.needs_refresh || course.in_progress);
  const dates = stale.map(course => course.last_updated || course.last_scrape_date).filter(Boolean).sort();
  const oldest = dates[0] ? new Date(dates[0]).toLocaleDateString() : 'an unknown date';
  const checking = refresh.state === 'checking';
  if (!stale.length && refresh.state === 'idle') return null;
  return (
    <div className="grace-period-warning" aria-live="polite">
      <div className="warning-content">
        <div className="warning-text">
          {selection.type === 'professor' && stale.length > 0 && <div>At least one of the courses this professor teaches may be out of date, last updated at {oldest}.</div>}
          {checking ? <span><span className="refresh-spinner" aria-hidden="true" />Checking for evaluations from {refresh.period}. There may be no new data available.{rawData && ' Previously saved data is shown below.'}</span>
            : pendingData ? <span>Updated evaluations are available.</span>
            : refresh.state === 'complete' ? <span>No new data found for {refresh.period}</span>
            : refresh.state === 'applied' ? <span>Updated data is shown below.</span>
            : refresh.state === 'error' ? <span role="alert">{refresh.error}</span>
            : selection.type === 'course' ? <span>{stale[0]?.current_period} period might have data but hasn't been checked since {stale[0]?.last_scrape_date || 'an unknown date'}, would you like to recheck?</span> : null}
          {pendingData && refresh.error && <div role="alert">{refresh.error}</div>}
          {notificationMessage && <div>{notificationMessage}</div>}
        </div>
        {pendingData && <button className="recheck-button" onClick={showUpdated}>Show updated data</button>}
        {!checking && !pendingData && <button className="recheck-button" onClick={recheck}>Recheck</button>}
        {checking && typeof window.Notification?.requestPermission === 'function' && !notificationMessage &&
          <button className="recheck-button" onClick={enableNotifications}>Notify me when finished</button>}
      </div>
    </div>
  );
}

const ResultView = ({ selection, options, benchmark, onAnalysis, onToggleSeparation, onRemove, headingExtra,
  comparisonMetric, rowTones, significant, onRowSelect, children }) => {
  const state = useEvaluationResult(selection);
  const { rawData } = state;
  const analysis = useMemo(() => {
    if (!rawData) return null;
    const hasTitles = rawData.metadata?.former_names?.length || rawData.metadata?.has_former_names;
    const separationKeys = options.separationKeys.filter(key => key !== 'course_name' || hasTitles);
    return processAnalysisRequest(rawData, { ...options, separationKeys, benchmark, scope: selection });
  }, [rawData, options, benchmark, selection]);
  // Publish new row identities/moments before paint so stale significance never
  // flashes on rows that have just been filtered, separated, or refreshed.
  useLayoutEffect(() => { onAnalysis(selection.id, analysis); }, [selection.id, analysis, onAnalysis]);
  useEffect(() => {
    if (rawData) addToSearchHistory(selection, rawData.metadata?.current_name);
  }, [rawData, selection]);
  const grouping = analysis?.metadata?.grouping_metadata;

  return (
    <section className="result-view" aria-label={selection.type === 'professor' ? selection.name : selection.code}>
      <ResultHeading selection={selection} metadata={analysis?.metadata} onRemove={onRemove} />
      {headingExtra}
      {selection.type === 'course' && grouping?.is_grouped && (
        <div className="grouping-banner">
          This course was automatically grouped with: {' '}
          {grouping.grouped_courses.filter(code => code !== selection.code).map((code, index) => <React.Fragment key={code}>{index > 0 && ', '}<b>{code}</b></React.Fragment>)}{' '}
          <InfoTooltip label="About grouped course reviews">{GROUPING_EXPLANATION}</InfoTooltip>
          <div className="grouping-action"><button onClick={() => onToggleSeparation('course_code')}>
            {options.separationKeys.includes('course_code') ? 'Recombine by Course Code' : 'Separate by Course Code'}
          </button></div>
        </div>
      )}
      {selection.type === 'professor' && <div className="grouping-banner professor-banner">
        <strong>Searching by Professor Name</strong>
        <div className="grouping-action"><button onClick={() => onToggleSeparation('course_group')}>
          {options.separationKeys.includes('course_group') ? 'Click here to recombine courses' : 'Click here to separate by course'}
        </button></div>
      </div>}
      <RefreshNotice selection={selection} state={state} />
      {children}
      {state.loading && <p role="status">Loading saved evaluations…</p>}
      <DataDisplay data={analysis?.data || null} errorMessage={state.error}
        selectedStats={Object.keys(options.stats).filter(key => options.stats[key])}
        statisticsMetadata={analysis?.statistics_metadata} groupLabels={analysis?.group_labels} showPercentiles={options.showPercentiles}
        comparisonMetric={comparisonMetric} rowTones={rowTones} significant={significant}
        onRowSelect={groupName => onRowSelect(selection.id, groupName)}
        yearRangeEmpty={analysis?.year_range_empty} filename={`${selection.type === 'professor' ? selection.name : selection.code}_analysis.csv`} />
      {state.error?.startsWith('No ') && selection.type === 'course' && <p className="evaluation-source-link">No evaluations found at this search: {' '}
        <a href={`https://asen-jhu.evaluationkit.com/Report/Public/Results?Course=${encodeURIComponent(selection.code)}`} target="_blank" rel="noopener noreferrer">{selection.code} on the evaluation site</a>
      </p>}
    </section>
  );
};
export default ResultView;
