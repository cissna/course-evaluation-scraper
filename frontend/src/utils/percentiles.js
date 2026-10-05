export function formatPercentile(value) {
  let decimals = 0;
  let displayed = value.toFixed(decimals);
  // Add a digit only while rounding looks like an endpoint, all nines
  // (99, 99.9, ...), or the smallest positive decimal (0.1, 0.01, ...).
  // True endpoints stay whole; keep zeros that resolve the ambiguity (99.90).
  const looksLikeExtreme = /^(?:0(?:\.0+)?|100(?:\.0+)?|99(?:\.9+)?|0\.0*1)$/;
  if (value > 0 && value < 100) {
    while (looksLikeExtreme.test(displayed) && decimals < 100) {
      displayed = value.toFixed(++decimals);
    }
  }
  const number = Number(displayed);
  const lastTwo = number % 100;
  const suffix = lastTwo >= 11 && lastTwo <= 13 ? 'th' : ({ 1: 'st', 2: 'nd', 3: 'rd' }[number % 10] || 'th');
  return `${displayed}${suffix}`;
}

export function lookupPercentile(mean, metric, benchmark, weightByClassSize = false) {
  if (!Number.isFinite(mean) || mean < 1 || mean > 5) return { percentile: null, percentile_reason: 'No valid responses for this metric.' };
  const percentiles = benchmark?.metrics?.[metric]?.[weightByClassSize ? 'size_weighted_percentiles' : 'percentiles'];
  // The 401 entries represent 1.00–5.00. Rounding is only for this lookup.
  const percentile = percentiles?.[Math.round(mean * 100) - 100];
  if (benchmark?.version !== 3 || !Array.isArray(percentiles) || percentiles.length !== 401 || !Number.isFinite(percentile)) {
    return { percentile: null, percentile_reason: 'The percentile benchmark is not available for this metric.' };
  }
  return { percentile, percentile_reason: null };
}
