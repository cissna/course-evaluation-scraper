import React from 'react';
import { checkCourseForUpdates, coursesToRecheck, needsCourseCheck } from '../hooks/useEvaluationResult';
import './GracePeriodWarning.css';

const unique = values => [...new Set(values.filter(Boolean))];
const checkedCodes = entries => unique(entries.flatMap(({ state }) => state.refresh.courseCodes || []));
const periods = entries => unique(entries.map(({ state }) => state.refresh.period)).join(', ');

export default function RefreshNotice({ results, notifications, shared = false }) {
  const entries = results.filter(({ state }) => state && (state.pendingData ||
    (state.refresh.state === 'idle' ? state.courses.some(needsCourseCheck) : state.refresh.state !== 'dismissed')));
  const checking = entries.filter(({ state }) => state.refresh.state === 'checking');
  const pending = entries.filter(({ state }) => state.pendingData);
  const completed = entries.filter(({ state }) => state.refresh.state === 'complete');
  const applied = entries.filter(({ state }) => state.refresh.state === 'applied');
  const failures = entries.filter(({ state }) => state.refresh.state === 'error');
  const waiting = entries.filter(({ state }) => state.refresh.state === 'idle');
  const staleCourses = waiting.flatMap(({ state }) => state.courses.filter(needsCourseCheck));
  const staleCodes = unique(staleCourses.map(course => course.course_code));
  const recheckable = entries.filter(({ state }) => !state.pendingData && ['idle', 'error'].includes(state.refresh.state));
  if (!entries.length) return null;

  const recheckAll = async () => {
    // Shared course/professor results can contain the same course. Reuse each
    // request within this batch, then reload every affected result's saved data.
    const controller = new AbortController();
    const checks = new Map();
    const targetCodes = new Set(recheckable.flatMap(({ state }) => coursesToRecheck(state.courses, state.refresh).map(course => course.course_code)));
    const affected = results.filter(({ state }) => state?.courses.some(course => targetCodes.has(course.course_code)));
    const check = course => {
      if (!checks.has(course.course_code)) {
        checks.set(course.course_code, checkCourseForUpdates(course, true, controller.signal));
      }
      return checks.get(course.course_code);
    };
    try { await Promise.all(affected.map(({ state }) => state.recheck(check, targetCodes))); }
    finally { controller.abort(); }
  };
  const singleCourse = !shared && results[0]?.selection.type === 'course';
  return <div className={`grace-period-warning${shared ? ' shared-refresh-notice' : ''}`} aria-live="polite">
    <div className="warning-content">
      <div className="warning-text">
        {staleCodes.length > 0 && <div>{singleCourse
          ? `${staleCourses[0].current_period} period might have data but hasn't been checked since ${staleCourses[0].last_scrape_date || 'an unknown date'}, would you like to recheck?`
          : `Recent evaluations may be missing for: ${staleCodes.join(', ')}.`}</div>}
        {checking.length > 0 && <div><span className="refresh-spinner" aria-hidden="true" />
          {shared ? `Checking ${checkedCodes(checking).join(', ')} for evaluations from ${periods(checking)}.` : `Checking for evaluations from ${periods(checking)}.`}{' '}
          There may be no new data available. Previously saved data is shown below.
        </div>}
        {pending.length > 0 && <div>{shared
          ? `Updated evaluations are available for ${pending.map(({ selection }) => selection.code || selection.name).join(', ')}.`
          : 'Updated evaluations are available.'}</div>}
        {completed.length > 0 && <div>No new data found for {shared ? `${checkedCodes(completed).join(', ')} (${periods(completed)})` : periods(completed)}.</div>}
        {applied.length > 0 && <div>Updated data is shown below.</div>}
        {failures.map(({ selection, state }) => <div key={selection.id} role="alert">{state.refresh.error}</div>)}
        {notifications.message && <div>{notifications.message}</div>}
      </div>
      {pending.length > 0 && <button className="recheck-button" onClick={() => pending.forEach(({ state }) => state.showUpdated())}>Show updated data</button>}
      {recheckable.length > 0 && !checking.length && <button className="recheck-button" onClick={recheckAll}>{shared ? 'Recheck all' : 'Recheck'}</button>}
      {checking.length > 0 && typeof window.Notification?.requestPermission === 'function' && !notifications.enabled &&
        <button className="recheck-button" onClick={notifications.enable} disabled={notifications.requesting}>Notify me when finished</button>}
    </div>
  </div>;
}
