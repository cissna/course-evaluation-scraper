import React, { useEffect, useLayoutEffect, useMemo } from 'react';
import DataDisplay from './DataDisplay';
import InfoTooltip from './InfoTooltip';
import RefreshNotice from './RefreshNotice';
import useEvaluationResult from '../hooks/useEvaluationResult';
import { processAnalysisRequest } from '../utils/analysisEngine';
import { addToSearchHistory } from '../utils/storageUtils';

export const GROUPING_EXPLANATION = 'For some courses, undergraduate reviews are included with the graduate section, so using this separation to understand the undergrad/grad breakdown isn’t useful.';

export function ResultHeading({ selection, metadata, onRemove }) {
  return (
    <div className="result-heading">
      <span className="result-heading-title">{selection.type === 'professor' ? selection.name : metadata?.current_name || selection.code}
        {onRemove && <button className="remove-result" onClick={onRemove} aria-label={`Remove ${selection.code || selection.name} from side-by-side view`}>×</button>}
      </span>
      {selection.type === 'course' && <>
        {metadata?.former_names?.length > 0 && <span className="result-subtitle">(formerly known as {metadata.former_names.join(', ')})</span>}
        {metadata?.current_name && <span className="result-subtitle">{selection.code}</span>}
      </>}
    </div>
  );
}

const ResultView = ({ selection, options, benchmark, onAnalysis, onRefreshState, notifications, sharedRefresh, onToggleSeparation, onRemove, headingExtra,
  comparisonMetric, rowTones, significant, onRowSelect, onMetricSelect, children }) => {
  const state = useEvaluationResult(selection, notifications.notify);
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
  useLayoutEffect(() => { onRefreshState(selection.id, state); }, [selection.id, state, onRefreshState]);
  useEffect(() => {
    if (rawData) addToSearchHistory(selection, rawData.metadata?.current_name);
  }, [rawData, selection]);
  const grouping = analysis?.metadata?.grouping_metadata;

  return (
    <section className="result-view" aria-label={selection.type === 'professor' ? selection.name : selection.code}>
      <div className="result-topbar">
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
        {!sharedRefresh && <RefreshNotice results={[{ selection, state }]} notifications={notifications} />}
        {children}
      </div>
      <div className="result-body">
        {state.loading && <p role="status">Loading saved evaluations…</p>}
        <DataDisplay data={analysis?.data || null} errorMessage={state.error}
          selectedStats={Object.keys(options.stats).filter(key => options.stats[key])}
          statisticsMetadata={analysis?.statistics_metadata} groupLabels={analysis?.group_labels} showPercentiles={options.showPercentiles}
          comparisonMetric={comparisonMetric} rowTones={rowTones} significant={significant} onMetricSelect={onMetricSelect}
          onRowSelect={onRowSelect ? (groupName, ensureSelected) => onRowSelect(selection.id, groupName, ensureSelected) : undefined}
          yearRangeEmpty={analysis?.year_range_empty} filename={`${selection.type === 'professor' ? selection.name : selection.code}_analysis.csv`} />
        {state.error?.startsWith('No ') && selection.type === 'course' && <p className="evaluation-source-link">No evaluations found at this search: {' '}
          <a href={`https://asen-jhu.evaluationkit.com/Report/Public/Results?Course=${encodeURIComponent(selection.code)}`} target="_blank" rel="noopener noreferrer">{selection.code} on the evaluation site</a>
        </p>}
      </div>
    </section>
  );
};
export default ResultView;
