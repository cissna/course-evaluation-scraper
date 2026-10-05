export function formatPercentile(value) {
  const distanceToEnd = Math.min(value, 100 - value);
  // Keep two decimal places within 1% of an endpoint, three within 0.1%,
  // and so on. Positive tail ranks must not round to an apparent 0 or 100.
  const decimals = distanceToEnd > 0 && distanceToEnd < 1
    ? Math.min(100, 1 + Math.ceil(-Math.log10(distanceToEnd))) : 0;
  const displayed = value.toFixed(decimals).replace(/(\.\d*?)0+$/, '$1').replace(/\.$/, '');
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
