# Module: `frontend/src/reportWebVitals.js`

This module is responsible for conditionally loading and running the `web-vitals` library to report Core Web Vitals performance metrics if a callback function is provided. It acts as an abstraction layer to integrate performance measurement without blocking the main application startup if the functionality is not explicitly requested or supported.

## Function Summary

### `reportWebVitals(onPerfEntry)`

**Purpose:** Initializes the reporting of Core Web Vitals (CLS, FID, FCP, LCP, TTFB) by dynamically importing the `web-vitals` library and passing the provided callback function to each metric reporter.

**Component Role:** This function serves as the entry point for performance metric collection during the application's lifecycle (typically called early in the root component initialization, e.g., `index.js` or `App.js`).

**Big-Picture Understanding:** It ensures that performance metrics are only collected and reported if a valid callback function (`onPerfEntry`) exists. It uses dynamic `import()` to load the `web-vitals` package asynchronously, preventing synchronous loading overhead if performance monitoring isn't needed.

**High-Level Interaction Patterns:**
1. **Check:** Validates if `onPerfEntry` is present and is a function.
2. **Load (Async):** If valid, it dynamically imports the necessary metric functions (`getCLS`, `getFID`, etc.) from the `web-vitals` package.
3. **Report:** Once loaded, it calls each metric function, passing `onPerfEntry` to each one. This registers the respective metric listeners with the browser, which will execute `onPerfEntry` when the metric value is finalized.

**Parameters:**
* `onPerfEntry` (`function`): The callback function that will receive the performance metric results (e.g., `(metric) => console.log(metric)`).