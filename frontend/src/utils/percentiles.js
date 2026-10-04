export function ordinal(value) {
  const number = Math.round(value);
  const lastTwo = number % 100;
  const suffix = lastTwo >= 11 && lastTwo <= 13 ? 'th' : ({ 1: 'st', 2: 'nd', 3: 'rd' }[number % 10] || 'th');
  return `${number}${suffix}`;
}

function lowerBound(values, value) {
  let low = 0, high = values.length;
  while (low < high) {
    const mid = Math.floor((low + high) / 2);
    if (values[mid] < value) low = mid + 1;
    else high = mid;
  }
  return low;
}

export function lookupPercentile(mean, metric, benchmark) {
  if (!Number.isFinite(mean)) return { percentile: null, percentile_reason: 'No valid responses for this metric.' };
  const scores = benchmark?.metrics?.[metric]?.scores;
  if (!Array.isArray(scores) || scores.length === 0) {
    return { percentile: null, percentile_reason: 'The percentile benchmark is not available for this metric.' };
  }
  const below = lowerBound(scores, mean - 1e-12);
  const above = lowerBound(scores, mean + 1e-12);
  return { percentile: 100 * (below + (above - below) / 2) / scores.length, percentile_reason: null };
}
