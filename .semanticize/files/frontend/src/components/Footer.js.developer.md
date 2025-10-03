## Footer Component

### Summary

The `Footer` component is a functional React component that renders the application's footer. It provides contact information and additional help text within a collapsible section.

### Interaction and State

-   **State**: The component manages a single piece of state, `isOpen` (a boolean), which determines whether the detailed help content is visible.
-   **Interaction**: Users can click on the main footer area to toggle the `isOpen` state. A caret icon visually indicates whether the section is open or closed.

### Functionality

-   **Contact Information**: Displays a primary contact email address, which is always visible.
-   **Collapsible Content**: Contains supplementary information that is shown or hidden based on the `isOpen` state. This content instructs users on how to report bugs, make suggestions, or request the grouping of related course codes (e.g., cross-listed courses).