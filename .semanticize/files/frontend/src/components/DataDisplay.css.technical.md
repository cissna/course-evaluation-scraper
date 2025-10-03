# Technical Documentation for `DataDisplay.css`

This CSS file provides the styling for the `DataDisplay` component and its child elements, including data tables, placeholders, error messages, and interactive tooltips.

## General Layout and Containers

### `.data-display`
- **Purpose**: The main container for the entire data display section.
- **Implementation**:
    - `margin: 20px;`: Applies a 20-pixel margin on all sides, creating space around the component.
    - `display: flex;`: Establishes a flexbox layout context.
    - `flex-direction: column;`: Arranges child elements vertically.
    - `align-items: flex-end;`: Aligns flex items (like the download button) to the right-hand side of the container.

### `.table-container`
- **Purpose**: A wrapper specifically for the data table.
- **Implementation**:
    - `width: 100%;`: Ensures the container spans the full width of its parent (`.data-display`), which in turn makes the table within it responsive to the parent's width.

## Informational Displays

### `.data-display-placeholder`
- **Purpose**: Styles the text shown when there is no data to display.
- **Implementation**:
    - `margin-top: 20px;`: Adds space above the placeholder text.
    - `font-style: italic;`: Italicizes the text.
    - `color: #888;`: Sets the text color to a light gray to indicate it's an informational, non-interactive message.

### `.data-display-error`
- **Purpose**: Styles a prominent error message box.
- **Implementation**:
    - `margin: 20px;`: Adds space around the error box.
    - `padding: 15px;`: Adds internal spacing.
    - `background-color: #fdeaea;`: A light red background.
    - `border: 2px solid #dc3545;`: A solid, darker red border.
    - `color: #721c24;`: A dark red text color for high contrast against the light red background.
    - `font-weight: 500;`: Medium font weight to make the text stand out.
    - `line-height: 1.5;`: Increases spacing between lines of text for better readability.

## Table Styling

### `.data-display table`
- **Purpose**: Defines the base styles for the data table.
- **Implementation**:
    - `width: 100%;`: Makes the table fill the width of its container (`.table-container`).
    - `border-collapse: collapse;`: Merges adjacent cell borders into a single, clean border.
    - `box-shadow: 0 2px 15px rgba(0,0,0,0.1);`: Adds a subtle shadow to lift the table off the page.
    - `background-color: white;`: Sets a solid white background for the table.

### `.data-display th, .data-display td`
- **Purpose**: Common styles for both table header (`th`) and data (`td`) cells.
- **Implementation**:
    - `padding: 12px 15px;`: Sets vertical and horizontal padding inside each cell.
    - `text-align: left;`: Aligns cell content to the left.
    - `border-bottom: 1px solid #ddd;`: Adds a light gray horizontal line at the bottom of each cell, creating row separators.

### `.data-display th`
- **Purpose**: Specific styles for table header cells to distinguish them from data cells.
- **Implementation**:
    - `background-color: #007bff;`: A distinct blue background.
    - `color: white;`: White text for contrast.
    - `font-weight: bold;`: Makes the header text bold.

### `.data-display tr:nth-child(even)`
- **Purpose**: Implements "zebra striping" for table rows to improve readability.
- **Implementation**:
    - This pseudo-class selector targets every even-numbered table row (`<tr>`).
    - `background-color: #f2f2f2;`: Applies a light gray background to these rows, alternating with the default white.

### `.data-display tr:hover`
- **Purpose**: Provides visual feedback when a user hovers over a table row.
- **Implementation**:
    - This pseudo-class selector targets any table row the user's cursor is over.
    - `background-color: #ddd;`: Changes the row's background to a darker gray.

## Interactive Elements

### `.download-btn`
- **Purpose**: Styles the download icon/button.
- **Implementation**:
    - `background: none; border: none;`: Removes default button styling to make it appear as an icon.
    - `cursor: pointer;`: Changes the cursor to a pointer on hover to indicate it's clickable.
    - `font-size: 24px;`: Sets the size of the icon/font within the button.
    - `color: #007bff;`: Sets the icon color to the same blue as the table header for consistency.
    - `margin-top: 5px;`: Adds a small space between the button and the element above it (the table).

### Tooltip Implementation
The tooltip is implemented using a parent-child structure (`.stat-value` and `.stat-tooltip`) and CSS hover effects.

#### `.stat-value`
- **Purpose**: A wrapper for a statistical value that will have a tooltip.
- **Implementation**:
    - `position: relative;`: Establishes a positioning context. Its child, `.stat-tooltip`, will be positioned relative to this element.
    - `display: inline-block;`: Allows the element to have block-like properties (like `position`) while flowing inline with text.

#### `.stat-tooltip`
- **Purpose**: The tooltip box that is hidden by default.
- **Implementation**:
    - `display: none;`: Hides the tooltip by default.
    - `position: absolute;`: Positions the tooltip relative to the nearest positioned ancestor (`.stat-value`).
    - `bottom: 100%;`: Places the tooltip directly above the `.stat-value` element.
    - `left: 50%; transform: translateX(-50%);`: A common technique to horizontally center an absolutely positioned element. It moves the tooltip's left edge to the center of the parent, then shifts the tooltip left by 50% of its own width.
    - `background-color: #333; color: white;`: Standard dark tooltip styling.
    - `padding: 4px 8px; font-size: 0.85em;`: Styles the text inside the tooltip.
    - `white-space: nowrap;`: Prevents the tooltip text from wrapping to a new line.
    - `z-index: 1000;`: Ensures the tooltip appears above other elements on the page.
    - `margin-bottom: 5px;`: Adds a 5px gap between the tooltip and the `.stat-value` element.

#### `.stat-tooltip::after`
- **Purpose**: Creates the small triangle/arrow at the bottom of the tooltip.
- **Implementation**:
    - This pseudo-element is attached to the `.stat-tooltip`.
    - `content: '';`: Required for pseudo-elements to be rendered.
    - `position: absolute;`: Positioned relative to the tooltip itself.
    - `top: 100%; left: 50%; transform: translateX(-50%);`: Places the pseudo-element at the bottom-center of the tooltip.
    - `border: 5px solid transparent;`: Creates a 5px transparent border on all sides.
    - `border-top-color: #333;`: Sets the color of the top border to match the tooltip background. This is the "CSS triangle trick"—the colored top border forms a downward-pointing triangle.

#### `.stat-value:hover .stat-tooltip`
- **Purpose**: The trigger mechanism to show the tooltip.
- **Implementation**:
    - This selector targets the `.stat-tooltip` element *only when* its parent, `.stat-value`, is being hovered over.
    - `display: block;`: Overrides the default `display: none;`, making the tooltip visible.