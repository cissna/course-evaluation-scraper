| Prop                   | Type       | Description                                                                                                                                                           |
| ---------------------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `options`              | `Object`   | An object containing the current state of all advanced options. It has the shape: `{ stats: { [statKey]: boolean }, separationKeys: string[], filters: { min_year: string, max_year: string } }`. |
| `onApply`              | `Function` | A callback function invoked whenever an option is changed. It receives the complete, updated `options` object as its only argument.                                     |
| `courseMetadata`       | `Object`   | An object containing metadata for the current course, used to conditionally render certain options. Specifically checks for `courseMetadata.former_names`.             |
| `showLast3YearsActive` | `boolean`  | A boolean flag from the parent component indicating if a "Show Last 3 Years" filter is currently active. This is used to disable the manual year range inputs.        |
| `onDeactivateLast3Years`| `Function` | A callback function to notify the parent component that the "Show Last 3 Years" filter should be deactivated, typically because the user is now setting a manual year range. |

## 4. Internal State

-   **`showOptions`**:
    -   **Type**: `boolean`
    -   **Initial Value**: `false`
    -   **Purpose**: A simple UI state variable that controls whether the advanced options panel is visible or collapsed. It is toggled by the "Advanced Options" / "Hide" button.

## 5. Implementation Details & Logic

### 5.1. Initial Render and Visibility Toggle

-   If `showOptions` is `false`, the component renders only a single `<button>` with the text "Advanced Options".
-   Clicking this button calls `setShowOptions(true)`, which re-renders the component to display the full options panel.
-   When the full panel is visible, a "Hide" button is present. Clicking it calls `setShowOptions(false)`, collapsing the panel.

### 5.2. Event Handlers

#### `handleStatChange(key)`

-   **Parameter**: `key` (string) - The unique identifier for the statistic being toggled (e.g., 'mean_rating').
-   **Logic**:
    1.  Creates a new `stats` object by spreading the existing `options.stats`.
    2.  Toggles the boolean value for the specified `key` (`!options.stats[key]`).
    3.  Calls `onApply` with a new `options` object, containing the updated `stats` object. This propagates the state change to the parent component.

#### `handleSeparationChange(key)`

-   **Parameter**: `key` (string) - The separation option being toggled (e.g., 'instructor', 'year', 'exact_period').
-   **Logic**: This function manages the `separationKeys` array and enforces mutual exclusivity rules.
    1.  It initializes `nextKeys` as a copy of the current `options.separationKeys` array.
    2.  **Mutual Exclusivity Rule**:
        -   If `key` is `'exact_period'`:
            -   If it's being selected, it is added to `nextKeys`, and `'year'` and `'season'` are explicitly filtered out.
            -   If it's being deselected, it is simply filtered out.
        -   If `key` is `'year'` or `'season'`:
            -   If it's being selected, it is added to `nextKeys`, and `'exact_period'` is explicitly filtered out.
            -   If it's being deselected, it is simply filtered out.
    3.  **Standard Toggle Rule**:
        -   For any other `key` (e.g., 'instructor'), it's a standard toggle: if the key is already in the array, it's removed; otherwise, it's added.
    4.  Finally, it calls `onApply` with a new `options` object containing the updated `separationKeys` array.

#### `handleMinYearChange(event)` & `handleMaxYearChange(event)`

-   **Parameter**: `event` (React SyntheticEvent) - The `onChange` event from the input field.
-   **Logic**:
    1.  Retrieves the new `value` from `event.target.value`.
    2.  **Side-effect**: If the `showLast3YearsActive` prop is `true`, it calls `onDeactivateLast3Years()` to signal that the manual year range is overriding the "last 3 years" preset.
    3.  Creates a deeply nested copy of the `options` object.
    4.  Updates either `min_year` or `max_year` within the `filters` object.
    5.  Calls `onApply` with the newly constructed `options` object.

### 5.3. Rendering Logic

The main `return` statement renders the expanded options panel, which is structured using a CSS grid (`options-grid`).

#### Conditional Variables

-   `showCourseNameOption`: A boolean derived from `courseMetadata`. It is `true` only if the course has an array of `former_names` with at least one entry. This is used to conditionally render the "Separate by Course Name" checkbox.
-   `isExactPeriodSelected`: A boolean, `true` if `'exact_period'` is in `options.separationKeys`. Used to disable the 'Year' and 'Season' checkboxes.
-   `isYearOrSeasonSelected`: A boolean, `true` if either `'year'` or `'season'` is in `options.separationKeys`. Used to disable the 'Exact Period' checkbox.

#### Statistics Section

-   Maps over `ALL_STAT_KEYS` to ensure a consistent order.
-   For each `key`, it retrieves the corresponding `config` from `STATISTICS_CONFIG`.
-   Renders a `<label>` and `<input type="checkbox">`.
-   The `checked` attribute is bound to `options.stats[key]`.
-   The `onChange` handler calls `handleStatChange(key)`.
-   The label text is set to `config.displayName`.
-   A CSS class (`default-stat` or `off-by-default-stat`) is applied based on the `config.defaultEnabled` flag for styling purposes.

#### Year Range Section

-   Renders two labeled number inputs for "Min Year" and "Max Year".
-   The `value` of each input is bound to `options.filters.min_year` and `options.filters.max_year` respectively. An empty string is used as a fallback to ensure the inputs are controlled components.
-   The `onChange` handlers are bound to `handleMinYearChange` and `handleMaxYearChange`.
-   The `disabled` attribute is set to the value of the `showLast3YearsActive` prop.

#### Separation Options Section

-   Renders a group of checkboxes for data separation.
-   Each checkbox's `checked` state is determined by checking for the presence of its corresponding key in the `options.separationKeys` array (e.g., `options.separationKeys.includes('instructor')`).
-   The `onChange` handler for each calls `handleSeparationChange` with the appropriate key.
-   The "Year" and "Season" checkboxes are disabled if `isExactPeriodSelected` is true.
-   The "Exact Period" checkbox is disabled if `isYearOrSeasonSelected` is true.
-   The "Course Name" checkbox is only rendered if `showCourseNameOption` is true.