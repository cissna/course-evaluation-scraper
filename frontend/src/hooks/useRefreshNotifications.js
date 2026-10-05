import { useCallback, useMemo, useRef, useState } from 'react';
import { getRefreshNotificationsPreference, saveRefreshNotificationsPreference } from '../utils/storageUtils';

export default function useRefreshNotifications() {
  const [preferred, setPreferred] = useState(() => getRefreshNotificationsPreference() ?? window.Notification?.permission === 'granted');
  const [requesting, setRequesting] = useState(false);
  const [message, setMessage] = useState('');
  const preferredRef = useRef(preferred);
  const requestPending = useRef(false);
  const waitingCompletions = useRef([]);
  const deliver = useCallback(body => {
    try { new window.Notification('Evaluation check finished', { body }); }
    catch { setMessage('The check finished, but this browser could not display a notification.'); }
  }, []);
  const notify = useCallback(body => {
    if (preferredRef.current && window.Notification?.permission === 'granted') deliver(body);
    else if (requestPending.current) waitingCompletions.current.push(body);
  }, [deliver]);
  const enable = useCallback(async () => {
    if (requestPending.current) return;
    requestPending.current = true;
    waitingCompletions.current = [];
    setRequesting(true);
    setMessage('Waiting for notification permission…');
    try {
      const permission = await window.Notification.requestPermission();
      const granted = permission === 'granted';
      preferredRef.current = granted;
      setPreferred(granted);
      saveRefreshNotificationsPreference(granted);
      setMessage(granted ? '' : 'Notifications were not enabled. You can keep checking this tab.');
      if (granted) waitingCompletions.current.forEach(deliver);
    } catch {
      setMessage('Notifications are not available in this browser.');
    } finally {
      requestPending.current = false;
      waitingCompletions.current = [];
      setRequesting(false);
    }
  }, [deliver]);

  const enabled = preferred && window.Notification?.permission === 'granted';
  return useMemo(() => ({ enabled, requesting, message, enable, notify }), [enabled, requesting, message, enable, notify]);
}
