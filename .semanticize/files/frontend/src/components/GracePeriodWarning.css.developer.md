## GracePeriodWarning.css Developer Documentation

This file provides the styling for the `GracePeriodWarning` component, which is used to inform users that the displayed course evaluation data may be outdated and from a previous semester.

### High-Level Summary

The stylesheet creates a distinct, non-intrusive warning box with a consistent color scheme (yellows and browns) to draw user attention. It uses a flexbox layout to position the informational text and a "Recheck" button. The design is responsive, adapting the layout for smaller screens to ensure readability and usability on mobile devices.

### Styling Breakdown

-   **`.grace-period-warning`**: The main container for the warning message. It establishes the visual identity of the warning with a light yellow background, a solid gold border, and appropriate padding and margins to separate it from other UI elements.

-   **`.warning-content`**: A flex container that manages the layout of the content inside the warning. On wider screens, it arranges the text and the button horizontally, with the button aligned to the far right. On smaller screens, it stacks them vertically.

-   **`.warning-text`**: Styles the descriptive text within the warning, ensuring it is readable and properly aligned. It is designed to occupy the available flexible space next to the button.

-   **`.recheck-button`**: Defines the appearance of the action button that allows users to trigger a re-scrape of the data. It includes styles for its default, hover, and disabled states to provide clear visual feedback. The color scheme is coordinated with the warning container.

-   **`@media (max-width: 768px)`**: A media query that handles the component's responsive behavior. On screens narrower than 768px, it changes the flex direction to `column`, stacking the text and button vertically. This ensures the component remains functional and well-organized on mobile devices. The button is aligned to the end of the container for a clean mobile UI pattern.