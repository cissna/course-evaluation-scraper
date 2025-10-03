## SearchResults.css Developer Documentation

This file provides the styling for the `SearchResults` component, which is responsible for displaying a list of course evaluation search results. The styles create a clean, centered, and responsive layout for users to browse and interact with the results.

### Overall Layout

-   `.search-results`: This is the main container for the entire search results view. It centers the content on the page with a maximum width and adds padding around it.

### Header and Navigation

-   `.search-results-header`: Styles the top section of the page, which includes the main title and a count of the results. It centers the text.
-   `.back-button`: Defines the appearance of the button used to navigate away from the search results. It's styled to be a clear call-to-action with a background color and hover effect.
-   `.search-results h2`: Styles the main title of the page.
-   `.results-count`: A simple style for the text that displays the number of results found.
-   `.search-note`: Styles for a small, italicized piece of text below the title, likely used for providing extra context to the user.

### Results List

-   `.results-list`: A flex container that arranges the individual result items in a vertical column with consistent spacing between them.
-   `.result-item`: Styles a single course in the search results. It's designed to look like a clickable card with a border, padding, and a subtle hover effect (background color change, border highlight, and shadow) to indicate interactivity.
-   `.course-code`: Styles the course identifier (e.g., "AS.180.101") within a result item, making it bold and colored to stand out.
-   `.course-name`: Styles the full name of the course within a result item.

### Asynchronous State Indicators

-   `.loading-message`: A centered, italicized message displayed to the user while the search results are being fetched.
-   `.error-message`: A distinctively styled box with a reddish background and border, used to display any errors that occur during the search process.
-   `.load-more-button`: A prominent button, typically shown after the initial list of results, that allows the user to fetch the next page of results.
-   `.end-message`: A simple, centered message shown at the bottom of the list when all available results have been loaded, indicating there is no more data to fetch.

### Responsive Design

-   `@media (max-width: 600px)`: This media query adjusts the layout for smaller screens (like mobile devices). It reduces the padding on the main container and individual result items, and decreases the font size of the main header to ensure the content remains readable and well-proportioned on smaller viewports.