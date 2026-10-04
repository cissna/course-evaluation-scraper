import { useCallback, useEffect, useRef, useState } from 'react';
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

function fetchSaved(selection, signal) {
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

const fingerprint = raw => JSON.stringify(Object.entries(raw?.instances || {}).sort(([a], [b]) => a.localeCompare(b)));

export default function useEvaluationResult(selection) {
  const [rawData, setRawData] = useState(null);
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refresh, setRefresh] = useState({ state: 'idle' });
  const [pendingData, setPendingData] = useState(null);
  const [notificationMessage, setNotificationMessage] = useState('');
  const controller = useRef(null);
  const rawRef = useRef(null);
  const busy = useRef(null);
  const notify = useRef(false);
  const runNumber = useRef(0);
  const completion = useRef(null);
  const deliverNotification = useCallback(body => {
    try { new window.Notification('Evaluation check finished', { body }); }
    catch { setNotificationMessage('The check finished, but this browser could not display a notification.'); }
  }, []);

  const refreshCourses = useCallback(async (statuses, force, signal) => {
    if (!statuses.length || (busy.current && !busy.current.signal.aborted) || signal.aborted) return;
    const run = { signal, id: ++runNumber.current };
    busy.current = run;
    notify.current = false;
    completion.current = null;
    setNotificationMessage('');
    const period = [...new Set(statuses.map(status => status.current_period).filter(Boolean))].join(', ');
    setRefresh({ state: 'checking', period });
    const failures = [];
    const queue = [...statuses];
    const check = async course => {
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
    };
    // Limit concurrent requests when a professor has many courses.
    const worker = async () => {
      while (queue.length && !signal.aborted) {
        const course = queue.shift();
        try { await check(course); }
        catch (failure) {
          if (failure.name !== 'AbortError') failures.push(`${course.course_code}: ${failure.message}`);
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
      setRefresh({ state: failures.length ? 'error' : changed ? hadCachedData ? 'updated' : 'applied' : 'complete', period, error: failures.join(' ') });
      const body = failures.length ? 'Some courses could not be checked. See this tab for details.' : changed ? 'Updated evaluations are available in this tab.' : `No new data found for ${period}.`;
      completion.current = { id: run.id, body };
      if (notify.current && 'Notification' in window && window.Notification.permission === 'granted') deliverNotification(body);
    } catch (failure) {
      if (!signal.aborted) setRefresh({ state: 'error', period, error: failure.message });
    } finally {
      if (busy.current === run) { busy.current = null; notify.current = false; }
    }
  }, [selection, deliverNotification]);

  useEffect(() => {
    const abortController = new AbortController();
    controller.current = abortController;
    const { signal } = abortController;
    let disposed = false;
    (async () => {
      try {
        const saved = await fetchSaved(selection, signal);
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
    return () => { disposed = true; notify.current = false; abortController.abort(); };
  }, [selection, refreshCourses]);

  const recheck = () => refreshCourses(courses, true, controller.current.signal);
  const showUpdated = () => {
    if (!pendingData) return;
    rawRef.current = pendingData;
    setRawData(pendingData);
    setPendingData(null);
    setRefresh(previous => ({ ...previous, state: previous.error ? 'error' : 'applied' }));
  };
  const enableNotifications = async () => {
    const requestedRun = runNumber.current;
    setNotificationMessage('Waiting for notification permission…');
    try {
      const permission = await window.Notification.requestPermission();
      if (controller.current.signal.aborted || requestedRun !== runNumber.current) return;
      notify.current = permission === 'granted';
      setNotificationMessage(permission === 'granted' ? 'Notifications enabled while this tab is open.' : 'Notifications were not enabled. You can keep checking this tab.');
      if (notify.current && completion.current?.id === requestedRun) {
        deliverNotification(completion.current.body);
        notify.current = false;
      }
    } catch { setNotificationMessage('Notifications are not available in this browser.'); }
  };
  return { rawData, courses, loading, error, refresh, pendingData, recheck, showUpdated, enableNotifications, notificationMessage };
}
