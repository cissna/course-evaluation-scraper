# Technical Documentation for `SearchResults.css`

## 1. Overview

This CSS file provides the styling for the `SearchResults` component in the React application. It is responsible for the layout, typography, color scheme, and responsiveness of the search results page. The design is centered around a clean, card-based layout for displaying course information, with clear visual cues for interactive elements, loading states, and error messages.

## 2. Styling Details

### 2.1. Main Container

#### `.search-results`
- **Purpose**: Defines the main content area for the search results.
- **Implementation**:
    - `max-width: 800px`: Constrains the width to a maximum of 800 pixels to ensure readability on wider screens.
    - `margin: 0 auto`: Centers the container horizontally within its parent.
    - `padding: 20px`: Provides spacing between the container's edge and its content.

### 2.2. Header and Navigation

#### `.search-results-header`
- **Purpose**: Styles the header section containing the title and other metadata.
- **Implementation**:
    - `margin-bottom: 24px`: Adds space below the header.
    - `text-align: center`: Centers the text content within the header.

#### `.back-button`
- **Purpose**: Styles the "Back" button used for navigation.
- **Implementation**:
    - `background: #2196F3`: Sets a blue background color.
    - `color: white`: Sets the text color to white.
    - `padding: 8px 16px`: Defines the inner spacing of the button.
    - `border-radius: 4px`: Applies slightly rounded corners.
    - `cursor: pointer`: Changes the cursor to a pointer on hover to indicate it's clickable.
    - `display: inline-flex`, `align-items: center`: Aligns the button's content (e.g., an icon and text) vertically.
    - `gap: 8px`: Adds space between flex items inside the button.

#### `.back-button:hover`
- **Purpose**: Provides visual feedback when the user hovers over the back button.
- **Implementation**:
    - `background: #1976D2`: Darkens the background color on hover.

### 2.3. Typography and Text Elements

#### `.search-results h2`
- **Purpose**: Styles the main heading of the search results page.
- **Implementation**:
    - `font-size: 1.5rem`: Sets the font size.
    - `color: #333`: Uses a dark gray color for the text.

#### `.search-note`
- **Purpose**: Styles a small, italicized note, likely for disclaimers or hints.
- **Implementation**:
    - `color: #666`: A lighter gray for secondary text.
    - `font-size: 13px`: Small font size.
    - `font-style: italic`: Italicizes the text.

#### `.results-count`
- **Purpose**: Styles the text displaying the number of results found.
- **Implementation**:
    - `color: #666`: Light gray color.
    - `font-size: 14px`: Small font size.

### 2.4. Status and Feedback Messages

#### `.error-message`
- **Purpose**: Styles a prominent box for displaying error messages.
- **Implementation**:
    - `background: #ffebee`: A light red background.
    - `color: #c62828`: A dark red text color.
    - `border: 1px solid #ffcdd2`: A light red border to clearly delineate the message box.
    - `padding: 12px`, `border-radius: 4px`: Provides internal spacing and rounded corners.

#### `.loading-message`
- **Purpose**: Styles the text shown while results are being fetched.
- **Implementation**:
    - `text-align: center`, `padding: 20px`: Centers the text and gives it space.
    - `color: #666`, `font-style: italic`: Styles it as secondary, italicized text.

#### `.end-message`
- **Purpose**: Styles the message indicating the end of the results list.
- **Implementation**:
    - Similar to `.loading-message` but with a `border-top` to visually separate it from the last result item.

### 2.5. Results List and Items

#### `.results-list`
- **Purpose**: The container for the list of individual result items.
- **Implementation**:
    - `display: flex`, `flex-direction: column`: Arranges the result items in a vertical stack.
    - `gap: 8px`: Creates a consistent 8px vertical space between each result item.

#### `.result-item`
- **Purpose**: Styles each individual search result as a "card".
- **Implementation**:
    - `background: white`, `border: 1px solid #e0e0e0`: Standard card styling with a white background and light gray border.
    - `border-radius: 8px`, `padding: 16px`: Rounded corners and internal padding.
    - `cursor: pointer`: Indicates the item is clickable.
    - `transition: all 0.2s ease`: Smoothly animates all property changes (e.g., on hover) over 0.2 seconds.
    - `display: flex`, `flex-direction: column`, `gap: 4px`: Stacks the content within the card (like course code and name) vertically with a small gap.

#### `.result-item:hover`
- **Purpose**: Provides a "lift" effect on hover to give feedback and highlight the active item.
- **Implementation**:
    - `background: #f5f5f5`: Slightly grays out the background.
    - `border-color: #2196F3`: Changes the border color to the theme's accent blue.
    - `transform: translateY(-1px)`: Moves the card up by 1 pixel.
    - `box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1)`: Adds a subtle shadow to enhance the lifting effect.

#### `.course-code`
- **Purpose**: Styles the course code text (e.g., `AS.180.101`).
- **Implementation**:
    - `font-weight: bold`, `color: #2196F3`: Makes the text bold and applies the accent blue color.
    - `font-size: 14px`: Sets a specific font size.
    - `text-transform: uppercase`, `letter-spacing: 0.5px`: Renders the text in uppercase with slight letter spacing for emphasis.

#### `.course-name`
- **Purpose**: Styles the full course name.
- **Implementation**:
    - `color: #333`, `font-size: 16px`: Standard dark text color and a slightly larger font size than the code.
    - `line-height: 1.4`: Increases line spacing for better readability.

### 2.6. Action Buttons

#### `.load-more-button`
- **Purpose**: Styles the button used to load subsequent pages of results.
- **Implementation**:
    - `display: block`, `margin: 24px auto`: Makes the button a block element and centers it horizontally.
    - `background: #4CAF50`: A green background color to indicate a positive action.
    - `padding: 12px 24px`, `font-size: 16px`: Makes the button large and easy to click.

#### `.load-more-button:hover`
- **Purpose**: Darkens the button on hover for visual feedback.
- **Implementation**:
    - `background: #45a049`: A darker shade of green.

### 2.7. Responsive Design

#### `@media (max-width: 600px)`
- **Purpose**: Adjusts the layout for mobile devices and other small screens with a viewport width of 600px or less.
- **Implementation**:
    - `.search-results`: Reduces the main container's padding to `16px` to save space.
    - `.result-item`: Reduces the padding inside each result card to `12px`.
    - `.search-results h2`: Reduces the main heading's font size to `1.25rem`.