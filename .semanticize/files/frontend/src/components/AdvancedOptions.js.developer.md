# `AdvancedOptions` Component

## Component-Level Summary

The `AdvancedOptions` component provides a user interface for configuring detailed analysis and display settings. It acts as a controlled component, receiving its state via props and communicating user-initiated changes back to its parent through a callback. Its primary role is to manage the UI for toggling statistics, setting year-range filters, and defining how data should be separated for analysis (e.g., by professor, year, or season).

The component manages its own visibility (expanded/collapsed) but relies on the parent component to provide the actual analysis options and to handle the application of those options.

## High-Level Interaction Patterns

- **State Management**: The component is stateless regarding the analysis options themselves. It receives the current `options` (including selected stats, filters, and separation keys) as a prop.
- **Event Handling**: When a user interacts with a control (e.g., checks a box for a statistic or changes a year), the component's internal handlers create a new version of the `options` object.
- **Callback Mechanism**: This new `options` object is passed up to the parent component via the `onApply` prop function. The parent is then responsible for updating the application's state and triggering a re-analysis of the data.
- **Conditional Logic**: The component contains UI-specific logic, such as:
    - Ensuring that separating by "Exact Period" is mutually exclusive with separating by "Year" or "Season".
    - Disabling the manual year-range inputs if a higher-level "Show Last 3 Years" filter is active in the parent.
    - Conditionally displaying a "Separate by Course Name" option only if the course has known former names, based on the `courseMetadata` prop.

## Function/Class Summaries

- **`AdvancedOptions`**: The main functional component.
    - **Props**:
        - `options`: An object containing the current state of all advanced settings (`stats`, `filters`, `separationKeys`).
        - `onApply`: A callback function invoked with the updated `options` object whenever a setting is changed.
        - `courseMetadata`: An object with metadata about the current course, used to conditionally render certain options.
        - `showLast3YearsActive`: A boolean that indicates if an external filter for the last 3 years is active, which disables the component's year inputs.
        - `onDeactivateLast3Years`: A callback to notify the parent that the user is manually setting a year range, thus overriding the "last 3 years" filter.
    - **State**:
        - `showOptions`: A boolean that toggles the visibility of the advanced options panel itself. This is the only piece of state managed internally by the component.
- **Event Handlers (`handleStatChange`, `handleSeparationChange`, etc.)**: These functions are responsible for interpreting user interactions, updating the local copy of the `options` object with the changes, and calling `onApply` to notify the parent. They encapsulate the logic for toggling values and enforcing rules like mutual exclusivity.