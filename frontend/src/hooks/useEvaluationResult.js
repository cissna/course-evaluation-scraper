import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { API_BASE_URL } from '../config';

async function jsonRequest(path, options) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error || 'Unable to load evaluations.');
    error.status = response.status;
    throw error;
  }
  return data;
}

export function fetchSaved(selection, signal) {
  return selection.type === 'professor'
    ? jsonRequest(`/api/professor?name=${encodeURIComponent(selection.name)}`, { signal })
    : jsonRequest(`/api/analyze/${selection.code}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ raw_data_mode: true }), signal,
    });
}

function waitForPoll(signal) {
  return new Promise((resolve, reject) => {
    const abort = () => { clearTimeout(timer); reject(new DOMException('Aborted', 'AbortError')); };
    const timer = setTimeout(() => { signal.removeEventListener('abort', abort); resolve(); }, 2000);
    if (signal.aborted) abort();
    else signal.addEventListener('abort', abort, { once: true });
  });
}

export async function checkCourseForUpdates(course, force, signal) {
  let outcome = course;
  if (!course.in_progress) {
    outcome = await jsonRequest(`/api/${force ? 'recheck' : 'refresh'}/${course.course_code}`, { method: 'POST', signal });
  }
  while (outcome.in_progress || outcome.state === 'in_progress') {
    await waitForPoll(signal);
    outcome = await jsonRequest(`/api/refresh-status/${course.course_code}`, { signal });
    if (!outcome.in_progress && (outcome.last_period_failed || outcome.needs_refresh)) {
      throw new Error(`The check for ${course.course_code} did not finish. Please recheck.`);
    }
  }
  return outcome;
}

export async function loadResultWithData(selection, signal) {
  let saved = await fetchSaved(selection, signal);
  if (Object.keys(saved.raw_data.instances || {}).length) return saved;
  const queue = (saved.refresh?.courses || []).filter(course => course.needs_refresh || course.in_progress);
  const failures = [];
  const worker = async () => {
    while (queue.length && !signal.aborted) {
      const course = queue.shift();
      try { await checkCourseForUpdates(course, false, signal); }
      catch (error) { if (error.name !== 'AbortError') failures.push(error.message); }
    }
  };
  await Promise.all(Array.from({ length: Math.min(3, queue.length) }, worker));
  if (signal.aborted) throw new DOMException('Aborted', 'AbortError');
  if (failures.length) throw new Error(failures.join(' '));
  saved = await fetchSaved(selection, signal);
  if (!Object.keys(saved.raw_data.instances || {}).length) throw new Error(`No evaluations found for ${selection.code || selection.name}.`);
  return saved;
}

const fingerprint = raw => JSON.stringify(Object.entries(raw?.instances || {}).sort(([a], [b]) => a.localeCompare(b)));
export const needsCourseCheck = course => course.needs_warning || course.needs_refresh || course.in_progress;
export const coursesToRecheck = (courses, refresh) => refresh.state === 'error'
  ? courses.filter(course => refresh.failedCourseCodes?.includes(course.course_code))
  : courses.filter(needsCourseCheck);

export default function useEvaluationResult(selection, onRefreshComplete) {
  const [rawData, setRawData] = useState(selection.initialSaved?.raw_data || null);
  const [courses, setCourses] = useState(selection.initialSaved?.refresh?.courses || []);
  const [loading, setLoading] = useState(!selection.initialSaved);
  const [error, setError] = useState(null);
  const [refresh, setRefresh] = useState({ state: 'idle' });
  const [pendingData, setPendingData] = useState(null);
  const controller = useRef(null);
  const rawRef = useRef(selection.initialSaved?.raw_data || null);
  const busy = useRef(null);

  const refreshCourses = useCallback(async (statuses, force, signal, checkCourse) => {
    if (!signal || !statuses.length || (busy.current && !busy.current.signal.aborted) || signal.aborted) return;
    const run = { signal };
    busy.current = run;
    const period = [...new Set(statuses.map(status => status.current_period).filter(Boolean))].join(', ');
    const courseCodes = statuses.map(course => course.course_code);
    setRefresh({ state: 'checking', period, courseCodes });
    const failures = [];
    const failedCourseCodes = [];
    const queue = [...statuses];
    // Limit concurrent requests when a professor has many courses.
    const worker = async () => {
      while (queue.length && !signal.aborted) {
        const course = queue.shift();
        try { await (checkCourse ? checkCourse(course) : checkCourseForUpdates(course, force, signal)); }
        catch (failure) {
          if (failure.name !== 'AbortError') {
            failures.push(`${course.course_code}: ${failure.message}`);
            failedCourseCodes.push(course.course_code);
          }
        }
      }
    };
    try {
      await Promise.all(Array.from({ length: Math.min(3, queue.length) }, worker));
      if (signal.aborted) return;
      let saved;
      try { saved = await fetchSaved(selection, signal); }
      catch (failure) {
        if (failure.status !== 404) throw failure;
        if (!rawRef.current) setError(selection.type === 'course' ? `No course evaluations found for ${selection.code}.` : 'No evaluations found for this professor.');
      }
      if (signal.aborted) return;
      const hadCachedData = Boolean(rawRef.current);
      const changed = saved && fingerprint(saved.raw_data) !== fingerprint(rawRef.current);
      if (saved) {
        setCourses(saved.refresh?.courses || []);
        if (!rawRef.current && Object.keys(saved.raw_data.instances).length) {
          rawRef.current = saved.raw_data;
          setRawData(saved.raw_data);
          setError(null);
        } else if (changed) setPendingData(saved.raw_data);
      }
      setRefresh({ state: failures.length ? 'error' : changed ? hadCachedData ? 'updated' : 'applied' : 'complete', period, courseCodes, failedCourseCodes, error: failures.join(' ') });
      const body = failures.length ? 'Some courses could not be checked. See this tab for details.' : changed ? 'Updated evaluations are available in this tab.' : `No new data found for ${period}.`;
      onRefreshComplete(`${selection.code || selection.name}: ${body}`);
    } catch (failure) {
      if (!signal.aborted) setRefresh({ state: 'error', period, courseCodes, failedCourseCodes: courseCodes, error: failure.message });
    } finally {
      if (busy.current === run) busy.current = null;
    }
  }, [selection, onRefreshComplete]);

  useEffect(() => {
    const abortController = new AbortController();
    controller.current = abortController;
    const { signal } = abortController;
    let disposed = false;
    (async () => {
      try {
        const saved = selection.initialSaved || await fetchSaved(selection, signal);
        if (disposed) return;
        const statuses = saved.refresh?.courses || [];
        setCourses(statuses);
        if (Object.keys(saved.raw_data.instances || {}).length) {
          rawRef.current = saved.raw_data;
          setRawData(saved.raw_data);
        }
        setLoading(false);
        const needsCheck = statuses.filter(course => course.needs_refresh || course.in_progress);
        if (needsCheck.length) refreshCourses(needsCheck, false, signal);
      } catch (failure) {
        if (!disposed) { setError(failure.message); setLoading(false); }
      }
    })();
    return () => { disposed = true; abortController.abort(); };
  }, [selection, refreshCourses]);

  useEffect(() => {
    if (!['complete', 'applied'].includes(refresh.state) || pendingData) return;
    const timer = setTimeout(() => setRefresh(previous => previous === refresh ? { ...previous, state: 'dismissed' } : previous), 10_000);
    return () => clearTimeout(timer);
  }, [refresh, pendingData]);

  const recheck = useCallback((checkCourse, targetCodes) => {
    const statuses = targetCodes ? courses.filter(course => targetCodes.has(course.course_code)) : coursesToRecheck(courses, refresh);
    return refreshCourses(statuses, true, controller.current?.signal, checkCourse);
  }, [courses, refresh, refreshCourses]);
  const showUpdated = useCallback(() => {
    if (!pendingData) return;
    rawRef.current = pendingData;
    setRawData(pendingData);
    setPendingData(null);
    setRefresh(previous => ({ ...previous, state: previous.error ? 'error' : 'applied' }));
  }, [pendingData]);
  return useMemo(() => ({ rawData, courses, loading, error, refresh, pendingData, recheck, showUpdated }),
    [rawData, courses, loading, error, refresh, pendingData, recheck, showUpdated]);
}
