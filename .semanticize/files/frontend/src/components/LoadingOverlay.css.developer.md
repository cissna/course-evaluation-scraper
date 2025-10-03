# `LoadingOverlay.css` Developer Documentation

This stylesheet defines the appearance and animation for a full-screen loading overlay component. It is designed to be simple, modern, and visually unobtrusive, indicating a background process to the user while blocking UI interaction.

## Class and Animation Summary

### `.loading-overlay`

-   **What it does:** Creates a full-screen modal overlay that covers the entire viewport. It uses a semi-transparent black background and a `backdrop-filter` to blur the content underneath, focusing the user's attention on the loading state. It also acts as a flex container to center the spinner and message.
-   **Interaction:** This is the main container for the loading indicator. It should be rendered conditionally in the DOM to show or hide the entire loading screen. The high `z-index` ensures it appears on top of all other page content.

### `.loading-spinner`

-   **What it does:** Renders a circular spinning animation. The visual effect of a rotating circle is achieved by using a mostly transparent border with a solid-colored top border and applying a CSS keyframe animation.
-   **Interaction:** This element is purely visual and provides feedback to the user that the application is active and processing a request.

### `.loading-message`

-   **What it does:** Styles the text that can be displayed below the spinner. It ensures the text is legible against the dark overlay.
-   **Interaction:** This provides optional, additional context to the user about what is happening (e.g., "Loading data...", "Analyzing results...").

### `@keyframes spin`

-   **What it does:** Defines the infinite rotation animation applied to the `.loading-spinner` class.
-   **Interaction:** It continuously transforms the spinner element by rotating it 360 degrees, creating the visual effect of spinning.