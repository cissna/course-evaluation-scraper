# Technical Documentation for `CourseSearch.css`

This document provides a detailed technical explanation of the `CourseSearch.css` stylesheet. It is intended for engineers who need a comprehensive understanding of the styling rules applied to the course search component.

## File Overview

This CSS file defines the styles for the main search bar component of the application. It uses a flexbox layout to create a responsive search input field and an accompanying search button. The styles also handle visual states like focus, disabled, and error display.

---

## CSS Rule Breakdown

### `.course-search`

This is the main container for the entire search component, including the input field and the search button.

- **`margin: 20px;`**
  - Adds 20 pixels of space on all four sides of the container, separating it from other elements on the page.

- **`display: flex;`**
  - Establishes a flexbox layout for its direct children (`.search-input-container` and `button`). This enables flexible alignment and sizing of the input and button.

- **`justify-content: center;`**
  - Horizontally centers the flex items (the input container and button) within the `.course-search` container.

- **`align-items: flex-start;`**
  - Aligns the flex items to the top of the container's cross-axis. This means the top edges of the input and button will be aligned.

- **`gap: 0;`**
  - Removes any space between the flex items, making the search input and button appear directly adjacent to each other.

### `.search-input-container`

This class styles the wrapper around the `<input>` element. It is used to control the input's growth and positioning context.

- **`position: relative;`**
  - Sets the positioning context. This is crucial for positioning child elements absolutely within this container, such as a search suggestions dropdown.

- **`flex-grow: 1;`**
  - Allows the container to grow and fill any available horizontal space within the parent flex container (`.course-search`).

- **`max-width: 500px;`**
  - Constrains the maximum width of the search input container to 500 pixels, preventing it from becoming excessively wide on larger screens.

### `.course-search input`

This rule targets the `<input>` element directly within the `.course-search` component.

- **`padding: 10px;`**
  - Adds 10 pixels of internal spacing within the input field, between the text and the border.

- **`font-size: 16px;`**
  - Sets the size of the text typed into the input field.

- **`border: 1px solid #ccc;`**
  - Applies a 1-pixel solid, light gray border around the input field.

- **`border-radius: 0;`**
  - Removes any rounded corners, resulting in a sharp rectangular shape.

- **`width: 100%;`**
  - Makes the input field expand to the full width of its parent, `.search-input-container`.

- **`box-sizing: border-box;`**
  - A critical property that includes the `padding` and `border` within the element's total width and height calculation. This prevents the padding and border from adding to the specified width, simplifying layout management.

### `.course-search input:focus`

This rule applies when the user clicks into the input field.

- **`outline: none;`**
  - Removes the default browser-specific outline that appears on focused elements, allowing for custom focus styling.

- **`border-radius: 0;`**
  - Re-affirms the sharp corners, ensuring consistency in the focused state across different browsers.

### `.course-search input:focus.dropdown-visible`

This is a compound selector that applies only when the input is in focus *and* it has the class `dropdown-visible` dynamically added to it (presumably via JavaScript when a search history or suggestions dropdown is displayed).

- **`border-bottom: 1px solid white;`**
  - Changes the bottom border color to white. The purpose is to visually merge the input field with the top of the dropdown menu that appears below it, creating a seamless, integrated look.

### `.course-search > button`

This rule targets a `<button>` element that is a direct child of the `.course-search` container.

- **`padding: 10px 20px;`**
  - Sets 10 pixels of padding on the top and bottom, and 20 pixels on the left and right.

- **`font-size: 16px;`**
  - Matches the font size of the input field for visual consistency.

- **`cursor: pointer;`**
  - Changes the mouse cursor to a pointer (hand icon) when hovering over the button, indicating it is clickable.

- **`background-color: #007bff;`**
  - Sets the button's background to a standard shade of blue.

- **`color: white;`**
  - Sets the button's text color to white.

- **`border: none;`**
  - Removes any default border from the button.

- **`border-radius: 0;`**
  - Ensures the button has sharp corners, matching the style of the input field.

- **`flex-shrink: 0;`**
  - Prevents the button from shrinking if the flex container lacks space. It will maintain its width as defined by its content and padding.

- **`box-sizing: border-box;`**
  - Same as for the input, ensures padding is included in the element's total size calculation.

- **`align-self: stretch;`**
  - Overrides the `align-items: flex-start` from the parent flex container. This forces the button to stretch vertically to match the height of the tallest item in the flex line (which is the input field, due to its padding and border).

### `.course-search > button:disabled`

This rule applies to the search button when its `disabled` attribute is set to `true`.

- **`background-color: #ccc;`**
  - Changes the background color to light gray, providing a visual cue that the button is inactive.

- **`cursor: not-allowed;`**
  - Changes the mouse cursor to a "not-allowed" symbol (a circle with a slash) on hover, reinforcing its disabled state.

### `.error-message`

This class is used for displaying error text, likely below the search component.

- **`color: red;`**
  - Sets the text color to red to draw the user's attention to the error.

- **`margin-top: 10px;`**
  - Adds 10 pixels of space above the error message, separating it from the search bar.