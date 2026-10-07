// Two-sided Welch t-test. The Student-t tail is evaluated with the regularized
// incomplete beta function; no normal approximation or rounded table scores.
// Formula reference: https://www.itl.nist.gov/div898/handbook/eda/section3/eda353.htm
const LANCZOS = [676.5203681218851, -1259.1392167224028, 771.3234287776531,
  -176.6150291621406, 12.507343278686905, -0.13857109526572012,
  9.984369578019572e-6, 1.5056327351493116e-7];

function logGamma(z) {
  if (z < 0.5) return Math.log(Math.PI) - Math.log(Math.sin(Math.PI * z)) - logGamma(1 - z);
  z -= 1;
  let series = 0.9999999999998099;
  LANCZOS.forEach((coefficient, index) => { series += coefficient / (z + index + 1); });
  const t = z + 7.5;
  return 0.5 * Math.log(2 * Math.PI) + (z + 0.5) * Math.log(t) - t + Math.log(series);
}

function betaFraction(a, b, x) {
  const protect = value => Math.abs(value) < 1e-300 ? (value < 0 ? -1e-300 : 1e-300) : value;
  let c = 1;
  let d = 1 / protect(1 - (a + b) * x / (a + 1));
  let fraction = d;
  for (let iteration = 1; iteration <= 500; iteration++) {
    let coefficient = iteration * (b - iteration) * x / ((a + 2 * iteration - 1) * (a + 2 * iteration));
    d = 1 / protect(1 + coefficient * d);
    c = protect(1 + coefficient / c);
    fraction *= d * c;
    coefficient = -(a + iteration) * (a + b + iteration) * x / ((a + 2 * iteration) * (a + 2 * iteration + 1));
    d = 1 / protect(1 + coefficient * d);
    c = protect(1 + coefficient / c);
    const change = d * c;
    fraction *= change;
    if (Math.abs(change - 1) < 3e-14) return fraction;
  }
  return NaN;
}

function regularizedBeta(x, a, b) {
  if (x <= 0) return 0;
  if (x >= 1) return 1;
  const factor = Math.exp(logGamma(a + b) - logGamma(a) - logGamma(b) + a * Math.log(x) + b * Math.log1p(-x));
  return x < (a + 1) / (a + b + 2)
    ? factor * betaFraction(a, b, x) / a
    : 1 - factor * betaFraction(b, a, 1 - x) / b;
}

export function isValidThreshold(value) {
  return value !== '' && value != null && Number.isFinite(Number(value)) && Number(value) > 0 && Number(value) < 1;
}

export function compareSamples(left, right, threshold = 0.05) {
  const unavailable = reason => ({ available: false, significant: false, reason });
  if (!left || !right) return unavailable('the selected metric has no valid sample.');
  const leftSources = new Set(left.source_ids || []);
  if ((right.source_ids || []).some(id => leftSources.has(id))) return unavailable('these groups share evaluations.');
  if (!Number.isFinite(left.n) || !Number.isFinite(right.n) || left.n < 2 || right.n < 2) {
    return unavailable('each group needs at least two valid responses.');
  }
  if (![left.mean, right.mean, left.variance, right.variance].every(Number.isFinite) || left.variance < 0 || right.variance < 0) {
    return unavailable('the selected metric has no valid sample variance.');
  }
  if (left.variance === 0 && right.variance === 0) return unavailable('both groups have zero variance.');
  if (!isValidThreshold(threshold)) return unavailable('enter a significance threshold greater than 0 and less than 1.');
  const leftError = left.variance / left.n, rightError = right.variance / right.n;
  const error = leftError + rightError;
  const t = (left.mean - right.mean) / Math.sqrt(error);
  const degreesOfFreedom = error ** 2 / (leftError ** 2 / (left.n - 1) + rightError ** 2 / (right.n - 1));
  const pValue = Math.max(0, Math.min(1, regularizedBeta(degreesOfFreedom / (degreesOfFreedom + t * t), degreesOfFreedom / 2, 0.5)));
  if (!Number.isFinite(pValue)) return unavailable('the numerical calculation did not converge.');
  return { available: true, t, degreesOfFreedom, pValue, significant: pValue < Number(threshold) };
}

export function toggleRowSelection(rows, row) {
  const existing = rows.some(item => item.resultId === row.resultId && item.groupName === row.groupName);
  return existing ? rows.filter(item => item.resultId !== row.resultId || item.groupName !== row.groupName) : [...rows, row].slice(-2);
}
