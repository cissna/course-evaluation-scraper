# Technical Documentation for `SearchHistory.css`

This document provides a detailed technical explanation of the CSS styles in `frontend/src/components/SearchHistory.css`. These styles define the appearance and layout of the search history dropdown component in the React application.

## Overview

The stylesheet is responsible for rendering a dropdown list that appears below a search input. This dropdown displays recently searched courses. The styling covers the main container, header, footer, individual list items, and interactive elements like close and remove buttons. It uses absolute positioning to overlay the dropdown, flexbox for internal alignment, and pseudo-classes for interactive states (`:hover`, `:last-child`).

---

## Class Selectors and Properties

### `.search-history-dropdown`

This is the main container for the entire search history dropdown.

- **`position: absolute;`**: Positions the dropdown relative to the nearest positioned ancestor. This allows it to float over other content on the page, typically appearing directly below the search bar.
- **`top: 100%;`**: Places the top edge of the dropdown at the bottom edge of its parent container.
- **`left: 0;`**: Aligns the left edge of the dropdown with the left edge of its parent.
- **`background: white;`**: Sets a solid white background.
- **`border: 1px solid #ccc;`**: Adds a 1-pixel light gray border around the dropdown.
- **`box-shadow: 0 2px 4px rgba(0,0,0,0.1);`**: Applies a subtle shadow to give the dropdown a sense of depth and lift it off the page.
- **`z-index: 1000;`**: Sets a high stack order to ensure the dropdown appears above other page elements.
- **`max-height: none;`**: Explicitly disables any maximum height, allowing the dropdown to expand vertically to fit all its content without scrolling.
- **`width: 100%;`**: Makes the dropdown's width equal to 100% of its parent container's width.
- **`box-sizing: border-box;`**: Ensures that the `width` property includes padding and borders, simplifying layout calculations.

### `.search-history-header`

Styles the header section of the dropdown, which contains the title.

- **`display: flex;`**: Enables flexbox layout for its children.
- **`justify-content: space-between;`**: Distributes space between flex items, pushing them to opposite ends of the header.
- **`align-items: center;`**: Vertically centers the items within the header.
- **`padding: 8px 12px;`**: Applies padding to the inside of the header.
- **`border-bottom: 1px solid #eee;`**: Adds a very light gray line to separate the header from the list of items.

### `.search-history-title`

Styles the "Recent Searches" title text within the header.

- **`font-weight: bold;`**: Makes the text bold.
- **`font-size: 14px;`**: Sets the font size.

### `.search-history-close`

Styles the 'X' button used to close the entire dropdown, positioned at the top right.

- **`position: absolute;`**: Positions the button relative to the `.search-history-dropdown` container.
- **`top: 0; right: 0;`**: Places the button in the top-right corner of the dropdown.
- **`width: 20px; height: 20px;`**: Defines the button's dimensions.
- **`background: #f0f0f0;`**: Sets a light gray background color.
- **`color: #333;`**: Sets the color of the 'X' icon/text.
- **`border: 1px solid #ccc;`**: Adds a light gray border.
- **`cursor: pointer;`**: Changes the cursor to a pointer on hover to indicate it's clickable.
- **`font-size: 12px;`**: Sets the size of the 'X' character.
- **`line-height: 1;`**: Sets the line height to 1 for tight vertical control of the text.
- **`padding: 0;`**: Removes any default padding.
- **`display: flex; align-items: center; justify-content: center;`**: Uses flexbox to perfectly center the 'X' character within the button's bounds.
- **`z-index: 1001;`**: Gives it a higher z-index than the dropdown itself to ensure it is rendered on top and is clickable.

### `.search-history-close:hover`

Defines the style for the close button when the user hovers over it.

- **`background: #e0e0e0;`**: Darkens the background color to provide visual feedback.

### `.search-history-item`

Styles an individual item (a previously searched course) in the history list.

- **`padding: 8px 40px 8px 12px;`**: Sets the internal padding. The large right padding (`40px`) is intentional to prevent the item's text from overlapping with the remove button.
- **`cursor: pointer;`**: Indicates the item is selectable.
- **`position: relative;`**: Establishes a positioning context for its absolutely positioned children, specifically the `.search-history-item-remove` button.
- **`display: flex; align-items: center;`**: Uses flexbox to vertically align the content (course code and name) within the item.
- **`border-bottom: 1px solid #f5f5f5;`**: Adds a very light gray separator line below each item.

### `.search-history-item:last-child`

A pseudo-class that targets the last item in the list.

- **`border-bottom: none;`**: Removes the bottom border from the final item to avoid a double border with the footer.

### `.search-history-item:hover, .search-history-item.selected`

Styles an item when it is hovered over or has the `.selected` class (used for keyboard navigation).

- **`background: #e3f2fd;`**: Changes the background to a light blue to highlight the active/selected item.

### `.search-history-item-code`

Styles the course code part of a history item (e.g., "AS.180.101").

- **`font-weight: bold;`**: Makes the course code text bold.
- **`margin-right: 8px;`**: Adds space between the code and the course name.
- **`font-family: monospace;`**: Renders the text in a monospaced font for better readability of code-like text.

### `.search-history-item-name`

Styles the course name part of a history item.

- **`color: #555;`**: Sets a medium-dark gray text color.
- **`white-space: nowrap;`**: Prevents the course name from wrapping to a new line.
- **`overflow: hidden;`**: Hides any part of the text that overflows the element's width.
- **`text-overflow: ellipsis;`**: Displays an ellipsis (`...`) to indicate that the visible text has been truncated. This trio of properties creates a clean single-line truncation effect.

### `.search-history-item-remove`

Styles the 'X' button on an individual history item, used to remove it from the list.

- **`position: absolute;`**: Positions the button relative to its parent, `.search-history-item`.
- **`right: 8px;`**: Places the button 8px from the right edge of the item.
- **`top: 50%; transform: translateY(-50%);`**: A common CSS technique to perfectly vertically center an absolutely positioned element.
- **`width: 24px; height: 24px;`**: Defines the button's clickable area.
- **`background: transparent; border: none;`**: Makes the button itself transparent, with no border.
- **`cursor: pointer;`**: Indicates the button is clickable.
- **`font-size: 16px; line-height: 1;`**: Styles the '×' character.
- **`display: flex; align-items: center; justify-content: center;`**: Centers the '×' character within the button.
- **`color: #999;`**: Sets a light gray color for the '×', making it subtle.

### `.search-history-item-remove:hover`

Defines the hover state for the remove button.

- **`background: #f0f0f0;`**: Adds a light gray circular background on hover.
- **`color: #333;`**: Darkens the '×' character for better visibility.

### `.search-history-footer`

Styles the footer section of the dropdown, which contains actions like "Clear History".

- **`display: flex;`**: Enables flexbox layout.
- **`justify-content: space-between;`**: Distributes space between the action items.
- **`padding: 8px 12px;`**: Sets internal padding.
- **`background: #f9f9f9;`**: Applies a very light gray background to distinguish the footer.
- **`border-top: 1px solid #eee;`**: Adds a light gray line to separate the footer from the item list.

### `.search-history-action`

Styles the action links/buttons within the footer.

- **`color: #1976d2;`**: Sets a standard blue link color.
- **`text-decoration: none;`**: Removes the default underline from the link.
- **`cursor: pointer;`**: Ensures a pointer cursor.
- **`font-size: 12px;`**: Uses a smaller font size for footer actions.
- **`background: none; border: none; padding: 0;`**: Resets default button styles to make it appear as a plain text link.
- **`font-family: inherit;`**: Ensures the button uses the same font as its parent container.

### `.search-history-action:hover`

Defines the hover state for footer actions.

- **`text-decoration: underline;`**: Adds an underline on hover, a common UX pattern for indicating interactivity.