export function toggleSeparation(keys, key) {
  if (keys.includes(key)) return keys.filter(value => value !== key);
  const excludes = {
    exact_period: ['year', 'season'], year: ['exact_period'], season: ['exact_period'],
    course_group: ['course_code'], course_code: ['course_group'],
  };
  return [...keys.filter(value => !(excludes[key] || []).includes(value)), key];
}
