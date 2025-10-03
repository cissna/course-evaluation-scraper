## AdvancedOptions.css Developer Documentation

This file provides the styling for the `AdvancedOptions` component, which allows users to configure advanced search and display settings. The styles define the layout, appearance, and visual feedback for various controls within this section.

### High-Level Summary

The CSS establishes a distinct visual container for the advanced options, using a grid system to create a responsive layout for the different settings. It also includes specific styles to differentiate between types of statistics and to format input controls like number fields for year ranges.

### Component-Level Styling

-   **`.advanced-options`**: The primary container for the entire "Advanced Options" section. It's styled as a distinct block with a border, padding, and a light background color to visually separate it from other parts of the UI.

-   **`.advanced-options .options-grid`**: Implements a responsive grid layout. This allows the option groups within to automatically reflow and adjust their column count based on the available screen width, ensuring the layout works well on various device sizes.

-   **`.advanced-options .option-group`**: Styles a container for a related set of options (e.g., a group of checkboxes). It uses flexbox to arrange the items within the group in a vertical column.

### Statistical Indicators

-   **`.default-stat`**: A class applied to statistics that are displayed by default. It gives the text a slightly heavier font weight to make it stand out.
-   **`.off-by-default-stat`**: A class for statistics that are not shown by default. It reduces the opacity of the text, providing a visual cue that the user needs to take action to enable it.

### Input and Form Control Styling

-   **`input[type="number"]`**: Styles the number input fields used for setting year ranges. It defines a fixed width and standardizes their padding and borders.
-   **`input[type="number"]:disabled`**: Provides visual feedback for disabled number inputs. The style changes the background and text color and sets the cursor to `not-allowed` to indicate that the field is inactive.
-   **`label`**: Styles the labels associated with form controls, using flexbox to ensure proper alignment between the label text and its corresponding input element.