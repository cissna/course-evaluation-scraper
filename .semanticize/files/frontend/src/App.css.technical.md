# Technical Documentation for `frontend/src/App.css`

## 1. Overview

This CSS file defines the fundamental layout and styling for the main application component, typically rendered within an element having the class `App`. It establishes a full-height flexbox container to ensure a consistent structure with a header, a main content area, and a footer that "sticks" to the bottom of the viewport, even on pages with little content.

## 2. Layout Implementation: Sticky Footer

The primary architectural feature of this stylesheet is the implementation of a sticky footer using the CSS Flexbox model.

### `.App` Class (Flex Container)

-   **`min-height: 100vh;`**: Ensures the `.App` container spans at least the full height of the browser's viewport.
-   **`display: flex;`**: Establishes the `.App` element as a flex container.
-   **`flex-direction: column;`**: Arranges the direct children of the `.App` container (e.g., `<header>`, `<main>`, `<footer>`) vertically in a column.

### `main` Element (Flex Item)

-   **`flex: 1;`**: This is the key property that makes the layout work. It's a shorthand for `flex-grow: 1`, `flex-shrink: 1`, and `flex-basis: 0%`.
    -   **`flex-grow: 1`**: Allows the `<main>` element to grow and occupy any available vertical space within the `.App` flex container.
    -   When the content is shorter than the viewport, the `<main>` element expands to fill the gap between the header and the footer, pushing the footer to the bottom of the screen.
    -   When the content is longer than the viewport, the `<main>` element expands with the content, and the page becomes scrollable as expected.

## 3. Class and Element Styles

### `.App`
- **`text-align: center;`**: Centers all inline content (like text) within the `.App` container and its children, unless overridden by a more specific rule.

### `.App-header`
- **`background-color: #282c34;`**: Sets a dark, charcoal-like background color for the header.
- **`padding: 20px;`**: Applies 20 pixels of padding on all four sides of the header's content.
- **`color: white;`**: Sets the default text color within the header to white for contrast against the dark background.

### `.app-footer`
- **`padding: 18px 8px;`**: Applies 18 pixels of vertical padding (top and bottom) and 8 pixels of horizontal padding (left and right).
- **`text-align: center;`**: Centers the footer's content.
- **`background: #f9fafb;`**: Sets a very light, off-white background color.
- **`color: #222;`**: Sets the text color to a dark grey.
- **`font-size: 1rem;`**: Sets the font size to be the same as the root element's font size (typically 16px).
- **`border-top: 1px solid #e2e2e2;`**: Adds a thin, light-grey line at the top of the footer, visually separating it from the main content.
- **`box-shadow: 0 -1px 6px rgba(0,0,0,0.05);`**: Applies a subtle shadow on the top edge of the footer (`-1px` on the y-axis). This gives it a slight "lifted" appearance over the main content area.

### `.app-footer a`
- **`color: #3977d2;`**: Styles all `<a>` (anchor/link) elements within the footer with a specific shade of blue.
- **`text-decoration: underline;`**: Adds an underline to the links, making them clearly identifiable as clickable.