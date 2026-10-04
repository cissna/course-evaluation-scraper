import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import App from './App';
import { comparisonSearchHeading } from './components/SearchResults';

const codes = ['EN.601.315', 'EN.553.431', 'EN.601.727', 'AS.180.101', 'AS.050.203'];
const frequencies = (high) => high ? { Good: 10, Excellent: 40 } : { Poor: 20, Weak: 20, Satisfactory: 10 };
function record(code, name, high, group = code) {
  return { course_code: code, course_name: `Course ${code}`, instructor_name: name, course_group_id: group, course_group: group,
    overall_quality_frequency: frequencies(high), instructor_effectiveness_frequency: frequencies(!high),
    workload_frequency: high ? { Typical: 10, 'Much heavier': 30 } : { 'Much lighter': 20, Typical: 10 } };
}
const instances = {
  'EN.601.315.01.FA25': record('EN.601.315', 'Jane Smith', true, 'Databases'),
  'EN.601.315.02.FA24': record('EN.601.315', 'Dana Lee', false, 'Databases'),
  'EN.553.431.01.SP20': { ...record('EN.553.431', 'Jane Smith', true, 'Statistics'), overall_quality_frequency: { Good: 30, Excellent: 20 } },
  'EN.553.631.01.SP20': record('EN.553.631', 'Dana Lee', false, 'Statistics'),
  'EN.601.727.01.SP25': record('EN.601.727', 'Alex Rivera', false),
  'AS.180.101.01.SP25': record('AS.180.101', 'Alex Rivera', true),
  'AS.050.203.01.SP25': record('AS.050.203', 'Robin Jones', true),
};
const json = (data, status = 200) => Promise.resolve({ ok: status < 400, status, json: async () => data });
const matches = (courses, professors) => ({ courses: { results: courses.map(code => ({ course_code: code, course_name: `Course ${code}` })), total_count: courses.length },
  professors: { results: professors.map(name => ({ type: 'professor', name })), total_count: professors.length } });
const professorNames = ['Jane Smith', 'Dana Lee', 'Alex Rivera'];

beforeEach(() => {
  localStorage.clear();
  global.fetch = jest.fn(input => {
    const url = new URL(input, 'http://localhost');
    if (url.pathname === '/api/percentiles') return json({ benchmark: { year_coverage: '2020–2025', metrics: { overall_quality: { scores: [1, 2, 3, 4, 5] } } } });
    if (url.pathname === '/api/search') {
      const query = url.searchParams.get('q');
      if (query === 'both') return json(matches([codes[0]], ['Jane Smith']));
      if (query === 'courses') return json(matches(codes.slice(0, 2), []));
      if (query === 'professors') return json(matches([], professorNames.slice(0, 2)));
      return json(matches([], professorNames.filter(name => name === query)));
    }
    const professor = url.pathname === '/api/professor';
    const name = url.searchParams.get('name');
    const code = url.pathname.split('/').pop();
    const selected = Object.fromEntries(Object.entries(instances).filter(([, value]) => professor ? value.instructor_name === name
      : value.course_code === code || (code === codes[1] && value.course_code === 'EN.553.631')));
    if (!Object.keys(selected).length) return json({ error: 'No data found for this course.' }, 404);
    return json({ raw_data: { instances: selected,
      metadata: { current_name: professor ? name : `Course ${code}`, result_type: professor ? 'professor' : 'course', professor_name: name,
        former_names: !professor && code === codes[1] ? ['Former Statistics'] : [] },
      grouping_metadata: { is_grouped: !professor && code === codes[1], grouped_courses: [codes[1], 'EN.553.631'] } }, refresh: { courses: [] } });
  });
});

async function search(query, intent = 'replace') {
  fireEvent.change(screen.getByRole('textbox'), { target: { value: query } });
  fireEvent.click(screen.getByRole('button', { name: intent === 'add' ? 'Add to comparison' : 'Search', exact: true }));
  await waitFor(() => expect(screen.queryByText('Searching...')).not.toBeInTheDocument());
}
const region = name => screen.getByRole('region', { name, exact: true });

test('mixed comparisons share controls while each table keeps its own scope', async () => {
  render(<App />);
  await search(codes[0]);
  await search('Jane Smith', 'add');
  expect(screen.getByRole('heading', { name: 'Comparison', exact: true })).toBeInTheDocument();
  expect(screen.getAllByRole('table')).toHaveLength(2);
  fireEvent.click(screen.getByRole('button', { name: 'Separate by Professor', exact: true }));
  expect(within(region(codes[0])).getAllByRole('row')).toHaveLength(3);
  expect(within(region('Jane Smith')).getAllByRole('row')).toHaveLength(2);
  fireEvent.click(screen.getByRole('button', { name: 'Separate by Course', exact: true }));
  expect(within(region('Jane Smith')).getAllByRole('row')).toHaveLength(3);
  expect(within(region(codes[0])).getAllByRole('row')).toHaveLength(3);
  expect(localStorage.getItem('jhuCourseSearchHistory')).not.toMatch(/initialSaved|instances|frequency/);
});

test('professor-only comparisons show only course separation and are capped with courses', async () => {
  render(<App />); await search('Jane Smith'); await search('Dana Lee', 'add');
  expect(screen.getAllByRole('table')).toHaveLength(2);
  expect(screen.getByRole('button', { name: 'Separate by Course', exact: true })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Separate by Professor', exact: true })).not.toBeInTheDocument();
});

test('add intent survives ambiguous results, whose headings reflect all matching types', async () => {
  render(<App />); await search(codes[2]); await search('both', 'add');
  expect(screen.getByRole('heading', { name: 'Choose a course or professor to add to comparison' })).toBeInTheDocument();
  expect(within(region(codes[2])).getByRole('table')).toBeVisible();
  fireEvent.click(screen.getByRole('tab', { name: 'Professors (1)' }));
  expect(screen.getByRole('heading', { name: 'Choose a course or professor to add to comparison' })).toBeInTheDocument();
  fireEvent.click(within(screen.getByRole('tabpanel')).getByRole('button', { name: /Jane Smith/ }));
  await waitFor(() => expect(screen.getAllByRole('table')).toHaveLength(2));
  expect(region(codes[2])).toBeVisible();
  expect(comparisonSearchHeading(matches(codes, []))).toBe('Choose a course to add to comparison');
  expect(comparisonSearchHeading(matches([], professorNames))).toBe('Choose a professor to add to comparison');
  expect(comparisonSearchHeading({ courses: { total_count: 40, results: [] }, professors: { total_count: 1, results: [] } })).toBe('Choose a course or professor to add to comparison');
});

test('unsuccessful normal and comparison searches keep previous tables, including missing direct codes', async () => {
  render(<App />); await search(codes[0]); await search('Jane Smith', 'add');
  await search('missing name', 'add');
  expect(screen.getByRole('alert')).toHaveTextContent('No matching courses found');
  expect(screen.getAllByRole('table')).toHaveLength(2);
  await search('AS.000.000');
  expect(screen.getByRole('alert')).toHaveTextContent('No data found');
  expect(screen.getAllByRole('table')).toHaveLength(2);
});

test('normal Enter replaces a comparison even when the input is unchanged', async () => {
  render(<App />); await search(codes[0]); await search('Jane Smith', 'add');
  fireEvent.keyDown(screen.getByRole('textbox'), { key: 'Enter' });
  await waitFor(() => expect(screen.getAllByRole('table')).toHaveLength(1));
  expect(region('Jane Smith')).toBeVisible();
  expect(screen.queryByRole('heading', { name: 'Comparison', exact: true })).not.toBeInTheDocument();
});

test('history compare and remove buttons do not navigate the row', async () => {
  render(<App />); await search('Jane Smith'); await search(codes[0]);
  fireEvent.change(screen.getByRole('textbox'), { target: { value: '' } });
  fireEvent.focus(screen.getByRole('textbox'));
  fireEvent.click(screen.getByRole('button', { name: 'compare', exact: true }));
  await waitFor(() => expect(screen.getAllByRole('table')).toHaveLength(2));
  fireEvent.change(screen.getByRole('textbox'), { target: { value: '' } });
  fireEvent.focus(screen.getByRole('textbox'));
  fireEvent.click(screen.getByRole('button', { name: 'Remove Jane Smith from history' }));
  expect(screen.getAllByRole('table')).toHaveLength(2);
  fireEvent.click(screen.getByRole('button', { name: /^Course EN.601.315/ }));
  await waitFor(() => expect(screen.getAllByRole('table')).toHaveLength(1));
});

test('five-item cap disables both entry points and removal restores a single-result layout', async () => {
  render(<App />);
  for (let i = 0; i < codes.length; i++) await search(codes[i], i ? 'add' : 'replace');
  expect(screen.getAllByRole('table')).toHaveLength(5);
  expect(screen.getByRole('button', { name: 'Add to comparison' })).toBeDisabled();
  expect(screen.getByText('Remove a course or professor to add another.')).toBeInTheDocument();
  fireEvent.change(screen.getByRole('textbox'), { target: { value: '' } });
  fireEvent.focus(screen.getByRole('textbox'));
  for (const button of screen.getAllByRole('button', { name: 'compare', exact: true })) {
    expect(button).toBeDisabled();
    fireEvent.click(button);
  }
  expect(screen.getAllByRole('table')).toHaveLength(5);
  fireEvent.click(screen.getByRole('button', { name: 'Close search history' }));
  for (const code of codes.slice(1)) fireEvent.click(screen.getByRole('button', { name: `Remove ${code} from comparison` }));
  expect(screen.getAllByRole('table')).toHaveLength(1);
  expect(screen.queryByRole('heading', { name: 'Comparison', exact: true })).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Add to comparison' })).toBeEnabled();
});

test('code separation omits a redundant code in the single-code table; empty ranges are per table', async () => {
  render(<App />); await search(codes[0]); await search(codes[1], 'add');
  fireEvent.click(screen.getByRole('button', { name: 'Separate by Course Code', exact: true }));
  expect(within(region(codes[0])).getByText('All Data', { exact: true })).toBeInTheDocument();
  expect(within(region(codes[1])).getByRole('cell', { name: codes[1], exact: true })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Advanced Options', exact: true }));
  fireEvent.change(screen.getByLabelText('Min Year:'), { target: { value: '2024' } });
  expect(within(region(codes[0])).getByRole('table')).toBeInTheDocument();
  expect(within(region(codes[1])).queryByRole('table')).not.toBeInTheDocument();
  expect(within(region(codes[1])).getByText('No results for range 2024 and later, try including some of these years 2020')).toBeInTheDocument();
});

const rowFor = (source, label) => within(region(source)).getByRole('cell', { name: label, exact: true }).closest('tr');
const metricDropdown = () => screen.getByRole('combobox', { name: 'Choose a metric to compare' });

test('single-course row clicks use red/orange outlines, default metric highlight, and gold only below the threshold', async () => {
  render(<App />); await search(codes[0]);
  expect(metricDropdown()).toHaveValue('');
  expect(metricDropdown()).toHaveAttribute('title', expect.stringContaining('third selection replaces the orange row'));
  expect(screen.getByRole('columnheader', { name: 'Overall Quality' })).toHaveClass('metric-highlight');
  fireEvent.click(screen.getByRole('button', { name: 'Separate by Professor', exact: true }));
  const jane = rowFor(codes[0], 'Jane Smith'), dana = rowFor(codes[0], 'Dana Lee');
  fireEvent.click(within(jane).getByRole('cell', { name: 'Jane Smith' }));
  expect(jane).toHaveClass('row-selected-red');
  fireEvent.click(dana);
  expect(jane).toHaveClass('row-selected-orange', 'row-significant');
  expect(dana).toHaveClass('row-selected-red', 'row-significant');
  expect(screen.getByRole('status')).toHaveTextContent('Jane Smith and Dana Lee are significantly different (P<0.05)');
  expect(within(screen.getByRole('status')).getByText('Jane Smith').tagName).toBe('STRONG');
  fireEvent.click(screen.getByRole('button', { name: 'Advanced Options', exact: true }));
  fireEvent.change(screen.getByLabelText('Significance threshold for comparisons'), { target: { value: '1e-100' } });
  expect(jane).not.toHaveClass('row-significant');
  expect(dana).toHaveClass('row-selected-red');
  expect(screen.queryByText(/are significantly different/)).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Significance threshold for comparisons'), { target: { value: '0.01' } });
  expect(screen.getByRole('status')).toHaveTextContent('(P<0.01)');
  fireEvent.click(dana);
  expect(jane).toHaveClass('row-selected-red');
  expect(jane).not.toHaveClass('row-significant');
  expect(screen.queryByText(/are significantly different/)).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /Clear selection/ })).not.toBeInTheDocument();
});

test('a third row replaces orange; removing its result leaves the remaining row red and clears significance', async () => {
  render(<App />); await search(codes[0]);
  fireEvent.click(screen.getByRole('button', { name: 'Separate by Professor', exact: true }));
  await search(codes[2], 'add');
  const jane = rowFor(codes[0], 'Jane Smith'), dana = rowFor(codes[0], 'Dana Lee'), alex = rowFor(codes[2], 'Alex Rivera');
  fireEvent.click(jane); fireEvent.click(dana); fireEvent.click(alex);
  expect(jane).not.toHaveClass('row-selected-orange');
  expect(dana).toHaveClass('row-selected-orange');
  expect(alex).toHaveClass('row-selected-red');
  fireEvent.click(screen.getByRole('button', { name: `Remove ${codes[2]} from comparison` }));
  expect(dana).toHaveClass('row-selected-red');
  expect(dana).not.toHaveClass('row-significant');
  expect(screen.queryByText(/are significantly different/)).not.toBeInTheDocument();
});

test('filtering or separating away selected rows clears them and does not resurrect their selection', async () => {
  render(<App />); await search(codes[0]);
  fireEvent.click(screen.getByRole('button', { name: 'Separate by Professor', exact: true }));
  fireEvent.click(rowFor(codes[0], 'Jane Smith')); fireEvent.click(rowFor(codes[0], 'Dana Lee'));
  fireEvent.click(screen.getByRole('button', { name: 'Advanced Options', exact: true }));
  fireEvent.change(screen.getByLabelText('Min Year:'), { target: { value: '2025' } });
  expect(rowFor(codes[0], 'Jane Smith')).toHaveClass('row-selected-red');
  expect(screen.queryByText(/are significantly different/)).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Min Year:'), { target: { value: '' } });
  expect(rowFor(codes[0], 'Dana Lee')).toHaveAttribute('aria-selected', 'false');
  fireEvent.click(screen.getByRole('button', { name: 'Combine Professors', exact: true }));
  expect(rowFor(codes[0], 'All Data')).toHaveAttribute('aria-selected', 'false');
});

test('metric hiding moves every highlight, disables comparison when none remain, and recovers when one returns', async () => {
  render(<App />); await search(codes[0]); await search(codes[2], 'add');
  fireEvent.click(rowFor(codes[0], 'All Data')); fireEvent.click(rowFor(codes[2], 'All Data'));
  fireEvent.change(metricDropdown(), { target: { value: 'workload' } });
  for (const header of screen.getAllByRole('columnheader', { name: 'Workload' })) expect(header).toHaveClass('metric-highlight');
  fireEvent.click(screen.getByRole('button', { name: 'Advanced Options', exact: true }));
  fireEvent.click(screen.getByLabelText('Workload', { exact: true }));
  expect(metricDropdown()).toHaveValue('overall_quality');
  for (const header of screen.getAllByRole('columnheader', { name: 'Overall Quality' })) expect(header).toHaveClass('metric-highlight');
  fireEvent.click(screen.getByLabelText('Periods Course Has Been Run', { exact: true }));
  for (const label of ['Overall Quality', 'Instructor Effectiveness', 'Intellectual Challenge']) fireEvent.click(screen.getByLabelText(label, { exact: true }));
  expect(metricDropdown()).toBeDisabled();
  expect(document.querySelectorAll('.metric-highlight, .row-significant')).toHaveLength(0);
  expect(screen.queryByText(/Significance unavailable|are significantly different/)).not.toBeInTheDocument();
  fireEvent.click(screen.getByLabelText('Overall Quality', { exact: true }));
  expect(metricDropdown()).toBeEnabled();
  expect(metricDropdown()).toHaveValue('overall_quality');
  expect(document.querySelectorAll('.row-significant')).toHaveLength(2);
});

test('mixed source overlap is unavailable; independent cross-table rows use source-prefixed bold labels', async () => {
  render(<App />); await search(codes[0]); await search('Jane Smith', 'add');
  fireEvent.click(rowFor(codes[0], 'All Data')); fireEvent.click(rowFor('Jane Smith', 'All Data'));
  expect(screen.getByRole('status')).toHaveTextContent('Significance unavailable: these groups share evaluations.');
  expect(document.querySelectorAll('.row-significant')).toHaveLength(0);
  expect(document.querySelectorAll('.row-selected-red, .row-selected-orange')).toHaveLength(2);
  fireEvent.click(screen.getByRole('button', { name: 'Separate by Professor', exact: true }));
  fireEvent.click(rowFor(codes[0], 'Dana Lee'));
  expect(screen.getByRole('status')).toHaveTextContent('are significantly different (P<0.05)');
  expect(within(screen.getByRole('status')).getByText('EN.601.315 — Dana Lee').tagName).toBe('STRONG');
  expect(within(screen.getByRole('status')).getByText('Jane Smith — All Data').tagName).toBe('STRONG');
  expect(screen.getAllByRole('combobox', { name: 'Choose a metric to compare' })).toHaveLength(1);
});

test('single-professor course rows and professor-versus-professor pairs can be compared', async () => {
  render(<App />); await search('Jane Smith');
  fireEvent.click(screen.getByRole('button', { name: 'Separate by Course', exact: true }));
  fireEvent.click(rowFor('Jane Smith', 'Databases')); fireEvent.click(rowFor('Jane Smith', 'Statistics'));
  expect(screen.getByRole('status')).toHaveTextContent('Databases and Statistics are significantly different');
  fireEvent.click(screen.getByRole('button', { name: 'Combine Courses', exact: true }));
  await search('Dana Lee', 'add');
  fireEvent.click(rowFor('Jane Smith', 'All Data')); fireEvent.click(rowFor('Dana Lee', 'All Data'));
  expect(screen.getByRole('status')).toHaveTextContent('Jane Smith — All Data and Dana Lee — All Data are significantly different');
});

test('a metric with too few responses gives compact unavailable feedback and no gold', async () => {
  render(<App />); await search(codes[0]); await search(codes[2], 'add');
  fireEvent.click(rowFor(codes[0], 'All Data')); fireEvent.click(rowFor(codes[2], 'All Data'));
  fireEvent.change(metricDropdown(), { target: { value: 'intellectual_challenge' } });
  expect(screen.getByRole('status')).toHaveTextContent('Significance unavailable: each group needs at least two valid responses.');
  expect(document.querySelectorAll('.row-significant')).toHaveLength(0);
});
