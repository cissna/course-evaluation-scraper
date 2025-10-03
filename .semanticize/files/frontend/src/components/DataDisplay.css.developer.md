## DataDisplay.css Developer Documentation

This file provides the styling for the `DataDisplay` component and its related elements. It defines the layout for the main container, styles for the data table, and visual cues for different states like errors or empty data.

### Component-Level Summary

-   **`.data-display`**: This is the main container for the component. It uses flexbox to organize its content, notably aligning the download button to the right, above the main table.

-   **State Indicators**:
    -   `.data-display-placeholder`: Styles the text that appears when there is no data to show, making it italic and subdued.
    -   `.data-display-error`: Creates a prominent, visually distinct error box with a red border and light red background to alert the user to a problem.

-   **Table Styling**:
    -   `.table-container`: A simple wrapper that ensures the table spans the full width of its parent.
    -   `.data-display table`: Defines the primary look of the data table, including a subtle box shadow, white background, and collapsed borders.
    -   `.data-display th`: Styles the table header with a blue background and white text for clear visual hierarchy.
    -   `.data-display tr`: Implements zebra-striping (`:nth-child(even)`) and a hover effect (`:hover`) on table rows to improve readability and user interaction.

-   **Interactive Elements**:
    -   `.download-btn`: Styles the download icon/button, removing default button appearance to make it look like a clickable icon.
    -   `.stat-value` & `.stat-tooltip`: Together, these classes create a tooltip interaction. The `.stat-value` holds a piece of data, and when hovered, the associated `.stat-tooltip` (which is normally hidden) becomes visible to provide additional context or information. The tooltip is styled as a dark box with a small triangular pointer.