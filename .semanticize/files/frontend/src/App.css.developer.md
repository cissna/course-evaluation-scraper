# `App.css` Developer Documentation

This file provides the fundamental layout and styling for the main `App` component, establishing the overall visual structure of the application.

## High-Level Summary

The primary purpose of this stylesheet is to create a "sticky footer" layout. It ensures that the main application container (`.App`) always fills the full height of the viewport. The layout is organized into three main sections: a header, a main content area, and a footer that remains at the bottom of the page, even on pages with little content.

## Component/Class Breakdown

### `.App`
- **Purpose**: The root container for the entire application.
- **Functionality**: It uses a vertical flexbox layout (`flex-direction: column`) to arrange its direct children (typically the header, main content, and footer). It's set to a minimum height of the viewport (`100vh`) to ensure the application fills the screen.

### `.App-header`
- **Purpose**: Styles the header section of the application.
- **Functionality**: Provides a distinct, dark-themed header with padding and light-colored text for global branding and navigation.

### `main`
- **Purpose**: Defines the main content area of the application, which sits between the header and the footer.
- **Functionality**: This element is configured to be flexible (`flex: 1`), allowing it to grow and shrink to fill any available vertical space. This is the key component that pushes the `.app-footer` to the bottom of the viewport, creating the "sticky footer" effect.

### `.app-footer`
- **Purpose**: Styles the footer section of the application.
- **Functionality**: The footer has a light background, a top border, and a subtle shadow to visually separate it from the `main` content area. It contains centered text for things like copyright notices or links.

### `.app-footer a`
- **Purpose**: Styles anchor tags (`<a>`) specifically within the footer.
- **Functionality**: Ensures that links in the footer are clearly identifiable with a specific color and an underline.