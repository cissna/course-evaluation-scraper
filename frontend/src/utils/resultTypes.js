export const NO_RESULTS_MESSAGE = 'No matching courses found in existing database. Use a full course code if this is a new course.';

export const compactCourseCode = value => value.trim().replace(/\./g, '').toLowerCase();

export function asResult(value) {
  if (typeof value === 'string') return { type: 'course', code: value, id: `course:${value}` };
  if (value.type === 'professor') return { ...value, id: `professor:${value.name}` };
  const code = value.primary_course || value.code || value.course_code;
  return { ...value, type: 'course', code, id: `course:${code}` };
}

export function filterSearchHistory(history, query, currentId) {
  const needle = query.trim().toLowerCase();
  const codeNeedle = compactCourseCode(query);
  return history.filter(item => item.id !== currentId && (
    `${item.code || ''} ${item.name}`.toLowerCase().includes(needle) ||
    (codeNeedle && item.code && compactCourseCode(item.code).includes(codeNeedle))
  ));
}
