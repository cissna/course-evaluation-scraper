import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CourseSearch from './CourseSearch';

const defaultProps = {
  onDataReceived: jest.fn(),
  onMultipleResults: jest.fn(),
  currentResultId: undefined,
  hasResults: true,
  atComparisonLimit: false,
  resolving: false,
  searchError: null,
  onSearchStart: jest.fn(),
};

describe('CourseSearch', () => {
  beforeEach(() => {
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          courses: { total_count: 0, results: [] },
          professors: { total_count: 0, results: [] },
        }),
      })
    );
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  test('renders no-results alert inside status area, not inside search controls', async () => {
    const { container } = render(<CourseSearch {...defaultProps} />);
    await userEvent.type(screen.getByRole('textbox'), 'Westfall');
    await userEvent.click(screen.getByRole('button', { name: 'Search' }));

    const alert = await screen.findByRole('alert');
    const controls = container.querySelector('.search-controls');
    const status = container.querySelector('.search-status');

    expect(status).toContainElement(alert);
    expect(controls).not.toContainElement(alert);
  });
});
