# Technical Documentation for `AdvancedOptions.css`

## 1. Overview

This CSS file provides the styling for the `AdvancedOptions` React component. It defines the layout and appearance of the container, its internal grid system for organizing options, and specific styles for form elements like number inputs and labels. The design is clean and functional, using borders, padding, and background colors to visually separate the advanced options section from other UI elements.

## 2. CSS Rules and Selectors

### `.advanced-options`

- **Purpose**: Styles the main container of the advanced options section.
- **Properties**:
    - `border: 1px solid #ccc;`: Applies a 1-pixel solid border with a light gray color (`#ccc`), visually enclosing the component.
    - `padding: 20px;`: Adds 20 pixels of space between the content and the border, preventing content from touching the edges.
    - `margin-top: 20px;`: Adds 20 pixels of space above the container, separating it from elements that precede it in the document flow.
    - `background-color: #f9f9f9;`: Sets a very light gray background color, making the section stand out slightly from a white background.

### `.advanced-options h3`

- **Purpose**: Styles the `<h3>` heading within the advanced options container.
- **Properties**:
    - `margin-top: 0;`: Removes the default top margin of the `h3` element to ensure it aligns perfectly with the top of the container's padding area.

### `.advanced-options .options-grid`

- **Purpose**: Defines a responsive grid layout for the various option groups.
- **Properties**:
    - `display: grid;`: Establishes the element as a grid container.
    - `grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));`: Creates a responsive column layout.
        - `auto-fit`: The grid container will create as many columns as can fit within its width.
        - `minmax(200px, 1fr)`: Each column will have a minimum width of 200px. If there is extra space, the columns will expand equally to fill it (1fr). On smaller screens, columns that don't fit will wrap to the next line.
    - `gap: 20px;`: Sets a 20-pixel gap between both the rows and columns of the grid, providing consistent spacing.

### `.advanced-options .option-group`

- **Purpose**: Styles a container for a related set of options (e.g., a group of checkboxes).
- **Properties**:
    - `display: flex;`: Establishes the element as a flex container.
    - `flex-direction: column;`: Arranges the items inside the group (e.g., labels, checkboxes) in a vertical stack.

### `.default-stat`

- **Purpose**: Provides a distinct visual style for statistics that are enabled by default.
- **Properties**:
    - `font-weight: 500;`: Sets the font to a medium weight, making it slightly bolder than normal text to draw attention.

### `.off-by-default-stat`

- **Purpose**: Provides a distinct visual style for statistics that are disabled by default.
- **Properties**:
    - `opacity: 0.8;`: Makes the element slightly transparent. This serves as a visual cue that the option is secondary or not currently active.

### `.advanced-options input[type="number"]`

- **Purpose**: Styles number input fields used for year range selection.
- **Properties**:
    - `width: 80px;`: Sets a fixed width for the input fields for a uniform appearance.
    - `padding: 4px 8px;`: Adds 4 pixels of padding on the top/bottom and 8 pixels on the left/right inside the input field.
    - `margin-left: 8px;`: Adds 8 pixels of space to the left of the input, separating it from its associated label text.
    - `border: 1px solid #ccc;`: Applies a standard light gray border.

### `.advanced-options input[type="number"]:disabled`

- **Purpose**: Styles the number input fields when they are in a disabled state.
- **Properties**:
    - `background-color: #f5f5f5;`: Changes the background to a light gray to indicate it's non-interactive.
    - `color: #666;`: Dims the text color.
    - `cursor: not-allowed;`: Changes the mouse cursor to a "not-allowed" symbol when hovering over the disabled input.

### `.advanced-options label`

- **Purpose**: Styles labels, particularly those associated with the year range inputs.
- **Properties**:
    - `display: flex;`: Uses flexbox to lay out the label's content (text and input field).
    - `align-items: center;`: Vertically aligns the label text and the input field to their center.
    - `margin-bottom: 8px;`: Adds 8 pixels of space below each label, separating it from the next form element in a list.