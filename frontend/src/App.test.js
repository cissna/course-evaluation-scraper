import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { StrictMode } from 'react';
import App from './App';
import { getSearchHistory } from './utils/storageUtils';

const course = { course_code: 'AS.180.101', primary_course: 'AS.180.101', course_name: 'Introduction to Psychology' };
const raw = (type = 'course', changed = false) => ({
  instances: {
    'AS.180.101.01.SP20': { course_code: 'AS.180.101', instructor_name: 'Jane Smith', overall_quality_frequency: { Good: 3, Excellent: changed ? 7 : 1 }, course_name: 'Introduction to Psychology' },
    'AS.180.101.02.SU20': { course_code: 'AS.180.101', instructor_name: 'Another Teacher', overall_quality_frequency: { Poor: 2 }, course_name: 'Introduction to Psychology' },
  },
  metadata: { current_name: type === 'professor' ? 'Jane Smith' : 'Introduction to Psychology', result_type: type, professor_name: type === 'professor' ? 'Jane Smith' : undefined },
  grouping_metadata: { is_grouped: false, grouped_courses: ['AS.180.101'] },
});
const json = data => Promise.resolve({ ok: true, status: 200, json: async () => data });
const matches = (courses, professors) => ({ courses: { results: courses, total_count: courses.length }, professors: { results: professors, total_count: professors.length } });
const saved = (type = 'course') => ({ raw_data: raw(type), refresh: { courses: [] } });
let searchMatches;

beforeEach(() => {
  localStorage.clear();
  searchMatches = matches([course], []);
  global.fetch = jest.fn(url => {
    if (url.includes('/api/percentiles')) return json({ benchmark: null });
    if (url.includes('/api/search?')) return json(searchMatches);
    return json(saved(url.includes('/api/professor?') ? 'professor' : 'course'));
  });
});
afterEach(() => jest.restoreAllMocks());

const search = value => {
  fireEvent.change(screen.getByRole('textbox'), { target: { value } });
  fireEvent.click(screen.getByRole('button', { name: 'Search', exact: true }));
};

test('single course search preserves the heading, absolute scores, and session filter choices', async () => {
  render(<App />);
  search('AS.180.101');
  await screen.findByText('Introduction to Psychology');
  fireEvent.click(screen.getByRole('button', { name: 'Advanced Options' }));
  fireEvent.click(screen.getByLabelText('Exclude summer'));
  expect(screen.getByText('4.25')).toBeInTheDocument();
  fireEvent.click(screen.getByLabelText('Show percentiles'));
  expect(screen.getByText('Ratings shown as percentiles of course averages.')).toBeInTheDocument();
  search('AS.180.102');
  await screen.findByText('AS.180.102');
  expect(screen.getByLabelText('Exclude summer')).toBeChecked();
  expect(screen.getByLabelText('Show percentiles')).toBeChecked();
  expect(localStorage.getItem('jhuCourseSearchHistory')).not.toContain('exclude_summer');
});

test('ambiguity includes both result types and defaults to courses', async () => {
  searchMatches = matches([course], [{ type: 'professor', name: 'Jane Smith' }]);
  render(<App />);
  search('Smith');
  await screen.findByRole('heading', { name: 'Search Results for "Smith"' });
  expect(screen.getByRole('tab', { name: 'Course names (1)' })).toHaveAttribute('aria-selected', 'true');
  fireEvent.click(screen.getByRole('tab', { name: 'Professors (1)' }));
  fireEvent.click(within(screen.getByRole('tabpanel')).getByRole('button', { name: /Professor Jane Smith/ }));
  await screen.findByText('Searching by Professor Name');
  expect(screen.getByRole('button', { name: 'Separate by Course', exact: true })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Separate by Professor' })).not.toBeInTheDocument();
  expect(await screen.findByText('4.25')).toBeInTheDocument();
  expect(getSearchHistory()[0]).toMatchObject({ type: 'professor', name: 'Jane Smith' });
});

test('professor-only matches default to professors and disable the empty course tab', async () => {
  searchMatches = matches([], [{ name: 'Jane Smith' }, { name: 'J. Smith' }]);
  render(<App />); search('Smith');
  expect(await screen.findByRole('tab', { name: 'Course names (0)' })).toBeDisabled();
  expect(screen.getByRole('tab', { name: 'Professors (2)' })).toHaveAttribute('aria-selected', 'true');
});

test('one professor match opens directly, and a failed search keeps the existing result', async () => {
  searchMatches = matches([], [{ type: 'professor', name: 'Jane Smith' }]);
  render(<App />); search('Jane Smith');
  await screen.findByText('Searching by Professor Name');
  searchMatches = matches([], []);
  search('unknown');
  await screen.findByRole('alert');
  expect(screen.getByText('Searching by Professor Name')).toBeVisible();
  expect(screen.queryByRole('heading', { name: /Search Results/ })).not.toBeInTheDocument();
});

test('year empty state replaces only the table and restores it when bounds change', async () => {
  render(<App />); search('AS.180.101');
  await screen.findByText('Introduction to Psychology');
  fireEvent.click(screen.getByRole('button', { name: 'Advanced Options' }));
  fireEvent.change(screen.getByLabelText('Min Year:'), { target: { value: '2025' } });
  expect(screen.getByText('No results for range 2025 and later, try including some of these years 2020')).toBeInTheDocument();
  expect(screen.queryByRole('table')).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Min Year:'), { target: { value: '2019' } });
  expect(screen.getByRole('table')).toBeInTheDocument();
});

test('cached data stays usable during refresh and the update preserves chosen filters', async () => {
  let finish;
  let refreshed = false;
  const pending = new Promise(resolve => { finish = () => { refreshed = true; resolve({ ok: true, status: 200, json: async () => ({ state: 'complete', new_data_found: true }) }); }; });
  global.fetch = jest.fn(url => {
    if (url.includes('/api/percentiles')) return json({ benchmark: null });
    if (url.includes('/api/refresh/')) return pending;
    return json({ raw_data: raw('course', refreshed), refresh: { courses: [{ course_code: 'AS.180.101', current_period: 'SU26', needs_refresh: !refreshed }] } });
  });
  render(<App />); search('AS.180.101');
  await screen.findByText(/Previously saved data is shown below/);
  expect(screen.getByRole('table')).toBeVisible();
  fireEvent.click(screen.getByRole('button', { name: 'Advanced Options' }));
  fireEvent.click(screen.getByLabelText('Exclude summer'));
  expect(screen.getByText('4.25')).toBeInTheDocument();
  finish();
  fireEvent.click(await screen.findByRole('button', { name: 'Show updated data' }));
  await waitFor(() => expect(screen.getByText('4.70')).toBeInTheDocument());
  expect(screen.getByLabelText('Exclude summer')).toBeChecked();
});

test('professor mode controls share course/code settings and use the oldest stale course date', async () => {
  searchMatches = matches([], [{ type: 'professor', name: 'Jane Smith' }]);
  global.fetch = jest.fn(url => {
    if (url.includes('/api/percentiles')) return json({ benchmark: null });
    if (url.includes('/api/search?')) return json(searchMatches);
    return json({ raw_data: raw('professor'), refresh: { courses: [
      { course_code: 'AS.180.101', needs_warning: true, last_updated: '2026-08-20T00:00:00Z' },
      { course_code: 'EN.553.431', needs_warning: true, last_updated: '2026-07-10T00:00:00Z' },
    ] } });
  });
  render(<App />); search('Jane Smith');
  await screen.findByText('4.25');
  const expectedDate = new Date('2026-07-10T00:00:00Z').toLocaleDateString();
  expect(screen.getByText(`At least one of the courses this professor teaches may be out of date, last updated at ${expectedDate}.`)).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Click here to separate by course' }));
  fireEvent.click(screen.getByRole('button', { name: 'Advanced Options' }));
  expect(screen.getByLabelText('Course', { exact: true })).toBeChecked();
  expect(screen.queryByLabelText('Professor', { exact: true })).not.toBeInTheDocument();
  fireEvent.click(screen.getByLabelText('Course code', { exact: true }));
  expect(screen.getByLabelText('Course', { exact: true })).not.toBeChecked();
  expect(screen.getByLabelText('Course code', { exact: true })).toBeChecked();
});

test('notification permission is requested only by the optional button, not by automatic checking', async () => {
  let finish;
  const pending = new Promise(resolve => { finish = () => resolve({ ok: true, status: 200, json: async () => ({ state: 'complete' }) }); });
  const notification = jest.fn();
  notification.requestPermission = jest.fn(async () => 'denied');
  notification.permission = 'default';
  const original = window.Notification;
  window.Notification = notification;
  global.fetch = jest.fn(url => {
    if (url.includes('/api/percentiles')) return json({ benchmark: null });
    if (url.includes('/api/refresh/')) return pending;
    return json({ raw_data: raw(), refresh: { courses: [{ course_code: 'AS.180.101', current_period: 'SU26', needs_refresh: true }] } });
  });
  try {
    render(<App />); search('AS.180.101');
    const button = await screen.findByRole('button', { name: 'Notify me when finished' });
    expect(notification.requestPermission).not.toHaveBeenCalled();
    fireEvent.click(button);
    await screen.findByText('Notifications were not enabled. You can keep checking this tab.');
    expect(notification.requestPermission).toHaveBeenCalledTimes(1);
    finish();
    await screen.findByText('No new data found for SU26');
    expect(notification).not.toHaveBeenCalled();
  } finally { window.Notification = original; }
});

test('new page sessions reset season and percentile options while preserving typed history', async () => {
  localStorage.setItem('jhuCourseSearchHistory', JSON.stringify({ version: 1, items: [{ code: 'AS.180.101', name: 'Old history' }] }));
  const view = render(<App />);
  fireEvent.click(screen.getByLabelText('Show percentiles'));
  fireEvent.click(screen.getByRole('button', { name: 'Advanced Options' }));
  fireEvent.click(screen.getByLabelText('Exclude intersession'));
  view.unmount();
  render(<App />);
  expect(screen.getByLabelText('Show percentiles')).not.toBeChecked();
  fireEvent.click(screen.getByRole('button', { name: 'Advanced Options' }));
  expect(screen.getByLabelText('Exclude intersession')).not.toBeChecked();
  expect(getSearchHistory()[0]).toMatchObject({ type: 'course', code: 'AS.180.101' });
  await waitFor(() => expect(global.fetch).toHaveBeenCalled());
});


test('development StrictMode can restart an aborted refresh without leaving a stuck progress banner', async () => {
  const checks = [];
  global.fetch = jest.fn((url, options = {}) => {
    if (url.includes('/api/percentiles')) return json({ benchmark: null });
    if (url.includes('/api/refresh/')) return new Promise((resolve, reject) => {
      checks.push({ signal: options.signal, resolve });
      options.signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true });
    });
    return json({ raw_data: raw(), refresh: { courses: [{ course_code: 'AS.180.101', current_period: 'SU26', needs_refresh: true }] } });
  });
  render(<StrictMode><App /></StrictMode>); search('AS.180.101');
  await screen.findByText(/Previously saved data is shown below/);
  await waitFor(() => expect(checks.some(check => !check.signal.aborted)).toBe(true));
  for (const check of checks.filter(check => !check.signal.aborted)) check.resolve({ ok: true, status: 200, json: async () => ({ state: 'complete' }) });
  await screen.findByText('No new data found for SU26');
});

test('late notification permission and a delivery failure do not change the completed refresh result', async () => {
  let finish, allow;
  const pending = new Promise(resolve => { finish = () => resolve({ ok: true, status: 200, json: async () => ({ state: 'complete' }) }); });
  const permission = new Promise(resolve => { allow = () => resolve('granted'); });
  const notification = jest.fn(() => { throw new Error('Browser notification delivery unavailable'); });
  notification.requestPermission = jest.fn(() => permission);
  notification.permission = 'granted';
  const original = window.Notification;
  window.Notification = notification;
  global.fetch = jest.fn(url => {
    if (url.includes('/api/percentiles')) return json({ benchmark: null });
    if (url.includes('/api/refresh/')) return pending;
    return json({ raw_data: raw(), refresh: { courses: [{ course_code: 'AS.180.101', current_period: 'SU26', needs_refresh: true }] } });
  });
  try {
    render(<App />); search('AS.180.101');
    fireEvent.click(await screen.findByRole('button', { name: 'Notify me when finished' }));
    finish();
    await screen.findByText('No new data found for SU26');
    allow();
    await screen.findByText('The check finished, but this browser could not display a notification.');
    expect(notification).toHaveBeenCalledTimes(1);
    expect(screen.getByText('No new data found for SU26')).toBeInTheDocument();
  } finally {
    if (original === undefined) delete window.Notification;
    else window.Notification = original;
  }
});
