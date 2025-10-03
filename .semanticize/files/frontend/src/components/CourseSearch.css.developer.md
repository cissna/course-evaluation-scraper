# `CourseSearch.css` Developer Documentation

This file provides the styling for the `CourseSearch` component, which consists of a text input, a search button, and an optional error message. The layout is managed using Flexbox to ensure proper alignment and responsiveness.

## Component-Level Styling

### `.course-search`
- **Purpose**: The main container for the entire search bar component.
- **Layout**: Uses `display: flex` to arrange the search input and button horizontally. `justify-content: center` centers the component on the page, and `align-items: flex-start` aligns the items to the top.

### `.search-input-container`
- **Purpose**: A wrapper for the `<input>` element.
- **Functionality**: It is a flex-item that grows (`flex-grow: 1`) to fill available space but is constrained by a `max-width`. Its `position: relative` is crucial for positioning child elements, such as the search history dropdown, relative to the input field.

### `.course-search input`
- **Purpose**: Styles the main text input field for course searches.
- **Behavior**: The input is styled to be responsive (`width: 100%`) within its container. The most notable interaction is handled by the `:focus.dropdown-visible` selector, which removes the bottom border of the input when it is focused and the search history dropdown is visible. This creates a seamless visual connection between the input field and the dropdown list below it.

### `.course-search > button`
- **Purpose**: Styles the search button adjacent to the input field.
- **Layout**: It is configured not to shrink (`flex-shrink: 0`) and to stretch vertically (`align-self: stretch`) to match the height of the input field, creating a cohesive unit.
- **State**: A `:disabled` state is provided to give clear visual feedback when the search action is not available.

### `.error-message`
- **Purpose**: Styles the text used to display validation or search-related errors to the user.
- **Appearance**: It simply renders text in red to draw attention to the error.