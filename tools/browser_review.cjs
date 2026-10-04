// Run against tools/fixture_server.py only. Requires a local Playwright install.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');

const baseURL = process.env.REVIEW_URL || 'http://127.0.0.1:8765';
if (!['127.0.0.1', 'localhost', '[::1]'].includes(new URL(baseURL).hostname)) {
  throw new Error('Browser review only runs against a local fixture server.');
}
const output = process.env.REVIEW_OUTPUT || path.resolve(__dirname, '../browser-artifacts');

async function search(page, query, button = 'Search') {
  await page.getByRole('textbox').fill(query);
  await page.getByRole('button', { name: button, exact: true }).click();
}

async function main() {
  await fs.mkdir(output, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const results = [];
  try {
    for (const [name, viewport] of [['desktop', { width: 1440, height: 900 }], ['phone', { width: 390, height: 844 }]]) {
      const context = await browser.newContext({ viewport, isMobile: name === 'phone', hasTouch: name === 'phone' });
      const marker = await (await context.request.get(`${baseURL}/__fixture__`)).json();
      assert(marker.fixture_server && marker.synthetic, 'Start the synthetic fixture server, without --snapshot.');
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(baseURL);
      await search(page, 'EN.553.431');
      await page.getByText('Honors Mathematical Statistics', { exact: true }).waitFor();
      await page.getByRole('table').waitFor();
      await page.getByRole('button', { name: 'Separate by Course Code', exact: true }).waitFor();
      assert.equal(await page.getByText(/formerly known as Honors Introduction to Statistics/).count(), 1);
      await page.screenshot({ path: path.join(output, `${name}-single-course.png`), fullPage: true });

      await search(page, 'not-in-the-database');
      await page.getByRole('alert').waitFor();
      const inputBox = await page.getByRole('textbox').boundingBox();
      const searchBox = await page.getByRole('button', { name: 'Search', exact: true }).boundingBox();
      assert(Math.abs(inputBox.height - searchBox.height) < 1, '#15: Search height must track the input during an error.');
      assert(await page.getByRole('table').isVisible(), 'Failed search preserves the previous result.');

      await search(page, 'Jane Smith');
      await page.getByText('Searching by Professor Name', { exact: true }).waitFor();
      await page.getByRole('table').waitFor();
      await page.getByRole('button', { name: 'Separate by Course', exact: true }).click();
      assert.equal(await page.getByRole('button', { name: 'Separate by Professor', exact: true }).count(), 0);
      await page.getByLabel('Show percentiles', { exact: true }).check();
      await page.getByText('Ratings shown as percentiles of course averages.', { exact: true }).waitFor();
      await page.screenshot({ path: path.join(output, `${name}-single-professor.png`), fullPage: true });
      await page.getByRole('button', { name: 'Advanced Options', exact: true }).click();
      await page.getByLabel('Exclude summer', { exact: true }).check();
      await page.getByLabel('Periods Course Has Been Run', { exact: true }).check();
      const downloadPromise = page.waitForEvent('download');
      await page.getByRole('button', { name: 'Download as CSV', exact: true }).click();
      const download = await downloadPromise;
      const csvPath = path.join(output, `${name}-professor.csv`);
      await download.saveAs(csvPath);
      const csv = await fs.readFile(csvPath, 'utf8');
      for (const expected of ['response count', 'sample standard deviation', 'percentile', 'benchmark years', 'Periods Course Has Been Run']) assert(csv.includes(expected));
      await page.getByLabel('Min Year:', { exact: true }).fill('2030');
      await page.getByText(/No results for range 2030 and later/).waitFor();
      assert.equal(await page.getByRole('table').count(), 0);
      await page.getByLabel('Min Year:', { exact: true }).fill('');
      await page.getByRole('table').waitFor();
      assert.deepEqual(errors, []);
      results.push({ viewport: name, checks: ['single course', 'single professor', 'grouping/FKA', 'failed search and button height', 'percentiles', 'CSV', 'year-range recovery'], passed: true });
      await context.close();
    }
    await fs.writeFile(path.join(output, 'results.json'), JSON.stringify(results, null, 2));
    console.log(JSON.stringify(results, null, 2));
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
