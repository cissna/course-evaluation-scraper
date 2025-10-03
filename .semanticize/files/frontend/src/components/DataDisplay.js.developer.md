## DataDisplay Component

The `DataDisplay` component is a presentational component responsible for rendering statistical data about course evaluations in a tabular format. It is designed to be flexible and is driven entirely by the props it receives.

### Core Functionality

-   **Renders Statistical Data**: Its primary role is to display the processed data passed via the `data` prop. The data is expected to be an object where keys are group names (e.g., "EN.601.226 - FA2022 (Fall 2022)") and values are objects containing the calculated statistics.
-   **Dynamic Columns**: The table columns are generated dynamically based on the `selectedStats` prop, which is an array of statistic keys (e.g., `['mean_rating', 'median_rating']`). It uses `STAT_MAPPINGS` to get the display-friendly names for headers.
-   **Informative Tooltips**: For each statistic, it can display a tooltip containing metadata, such as the sample size (`n`) and standard deviation (`σ`). This metadata is provided via the `statisticsMetadata` prop. This gives users deeper insight into the data without cluttering the main view.
-   **CSV Export**: Provides a "Download" button that converts the currently displayed table data into a CSV file and initiates a browser download.

### Interaction Patterns

-   The component is "controlled" by its parent. It does not fetch or calculate any data itself. It simply renders the results of analysis performed by `analysisEngine.js` and passed down from a parent component.
-   If an `errorMessage` prop is provided, the component will render the error message instead of the table, allowing parents to easily communicate issues like failed data fetching or analysis.
-   If no `data` is available, it displays a placeholder prompting the user to enter a course.
-   If no statistics are selected (`selectedStats` is empty), it prompts the user to choose at least one statistic, guiding them on how to use the interface.
-   The only internal state it manages is `downloadClicked`, which provides simple UI feedback to the user when they click the download button.