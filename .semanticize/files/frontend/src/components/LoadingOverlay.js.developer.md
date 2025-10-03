# `LoadingOverlay.js` Developer Documentation

## `LoadingOverlay` Component

### Summary

The `LoadingOverlay` component renders a full-screen modal overlay with a loading spinner and a customizable message. It is designed to block user interaction with the underlying page while a background process, such as data fetching or processing, is active.

### Interaction Patterns

-   **Portal Rendering**: This component uses `ReactDOM.createPortal` to render itself directly into the `document.body`. This ensures it covers the entire viewport, regardless of where it is placed in the React component tree.
-   **Props**: It accepts a single optional prop, `message`, which defaults to "Loading…". This allows developers to display context-specific messages to the user (e.g., "Scraping new data...", "Analyzing results...").
-   **Usage**: To use it, a parent component conditionally renders `<LoadingOverlay />` based on a loading state (e.g., `isLoading`). When rendered, it immediately covers the page. When the loading state becomes false, the component is removed from the DOM, and the overlay disappears.