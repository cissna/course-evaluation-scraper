import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import App from './App';

jest.mock('./components/CourseSearch', () => ({ onDataReceived }) => (
  <div>
    <button onClick={() => onDataReceived('AS.111.111')}>Load grouped course</button>
    <button onClick={() => onDataReceived('AS.222.222')}>Load single course</button>
  </div>
));
jest.mock('./components/SearchResults', () => () => null);
jest.mock('./components/DataDisplay', () => () => null);
jest.mock('./components/AdvancedOptions', () => () => null);
jest.mock('./components/LoadingOverlay', () => () => null);
jest.mock('./components/GracePeriodWarning', () => () => null);
jest.mock('./components/Footer', () => () => null);
jest.mock('./utils/storageUtils', () => ({ addToSearchHistory: jest.fn() }));

beforeEach(() => {
  global.fetch = jest.fn((url) => {
    if (url.includes('/api/analyze/AS.111.111')) {
      return Promise.resolve({
        ok: true,
        json: async () => ({
          raw_data: {
            instances: {
              'AS.111.111.01.FA24': {
                course_name: 'Grouped Course',
                instructor_name: 'Instructor A',
                overall_quality_frequency: { Good: 1 }
              }
            },
            metadata: { current_name: 'Grouped Course', former_names: [] },
            grouping_metadata: { is_grouped: true, grouped_courses: ['AS.111.111', 'AS.333.333'] }
          }
        })
      });
    }
    if (url.includes('/api/analyze/AS.222.222')) {
      return Promise.resolve({
        ok: true,
        json: async () => ({
          raw_data: {
            instances: {
              'AS.222.222.01.FA24': {
                course_name: 'Single Course',
                instructor_name: 'Instructor B',
                overall_quality_frequency: { Good: 1 }
              }
            },
            metadata: { current_name: 'Single Course', former_names: [] },
            grouping_metadata: { is_grouped: false, grouped_courses: [] }
          }
        })
      });
    }
    if (url.includes('/api/grace-status/')) {
      return Promise.resolve({
        ok: true,
        json: async () => ({ in_grace_period: false })
      });
    }
    return Promise.reject(new Error(`Unhandled fetch URL: ${url}`));
  });
});

afterEach(() => {
  jest.clearAllMocks();
});

test('resets course code separation when switching courses', async () => {
  render(<App />);

  fireEvent.click(screen.getByText('Load grouped course'));
  await screen.findByText('Grouped Course');
  await screen.findByText('Separate by Course Code');

  fireEvent.click(screen.getByText('Separate by Course Code'));
  expect(screen.getByText('Recombine by Course Code')).toBeInTheDocument();

  fireEvent.click(screen.getByText('Load single course'));
  await screen.findByText('Single Course');
  await waitFor(() => {
    expect(screen.queryByText('Recombine by Course Code')).not.toBeInTheDocument();
    expect(screen.queryByText('Separate by Course Code')).not.toBeInTheDocument();
  });

  fireEvent.click(screen.getByText('Load grouped course'));
  await screen.findByText('Separate by Course Code');
  expect(screen.queryByText('Recombine by Course Code')).not.toBeInTheDocument();
});
