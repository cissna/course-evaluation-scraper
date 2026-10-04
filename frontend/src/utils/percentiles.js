export function ordinal(value) {
  const number = Math.round(value);
  const lastTwo = number % 100;
  const suffix = lastTwo >= 11 && lastTwo <= 13 ? 'th' : ({ 1: 'st', 2: 'nd', 3: 'rd' }[number % 10] || 'th');
  return `${number}${suffix}`;
}

export function lookupPercentile(mean, metric, benchmark) {
  if (!Number.isFinite(mean) || mean < 1 || mean > 5) return { percentile: null, percentile_reason: 'No valid responses for this metric.' };
  const percentiles = benchmark?.metrics?.[metric]?.percentiles;
  // The 401 entries represent 1.00–5.00. Rounding is only for this lookup.
  const percentile = percentiles?.[Math.round(mean * 100) - 100];
  if (benchmark?.version !== 2 || !Array.isArray(percentiles) || percentiles.length !== 401 || !Number.isFinite(percentile)) {
    return { percentile: null, percentile_reason: 'The percentile benchmark is not available for this metric.' };
  }
  return { percentile, percentile_reason: null };
}
