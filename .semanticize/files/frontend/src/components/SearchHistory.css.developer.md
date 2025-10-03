# `SearchHistory.css` Developer Documentation

This file provides the styling for the `SearchHistory` component, which renders a dropdown list of recently searched courses. The styles define the layout, appearance, and interactive states of the dropdown, its header, individual items, and footer.

## Component-Level Styling

### `.search-history-dropdown`

-   **Purpose**: Styles the main container for the search history dropdown.
-   **Behavior**: It is positioned absolutely to appear directly below its parent element (likely the search input). It has a defined `z-index` to ensure it renders above other page content. The width is set to 100% to match the parent's width, and `max-height` is set to `none`, indicating the dropdown will expand to fit all items without scrolling.

### `.search-history-header`, `.search-history-title`, `.search-history-close`

-   **Purpose**: Style the header section of the dropdown.
-   **Behavior**: The header uses a flexbox layout to position the title and a main close button. The close button is absolutely positioned in the top-right corner of the dropdown container, ensuring it remains in a fixed position even if the header content wraps. It has a higher `z-index` to sit above other header elements.

### `.search-history-item`, `.search-history-item-code`, `.search-history-item-name`, `.search-history-item-remove`

-   **Purpose**: Style an individual entry within the search history list.
-   **Behavior**: Each item is a flex container to align its contents. It has padding to accommodate an individual "remove" button, which is absolutely positioned on the right side.
-   **Interaction**:
    -   The entire item is a `cursor: pointer`, indicating it's clickable.
    -   A light blue background (`#e3f2fd`) is applied on hover or when the item has the `.selected` class, providing visual feedback for keyboard navigation or selection.
    -   The course name (`.search-history-item-name`) uses `text-overflow: ellipsis` to gracefully handle long names that would otherwise overflow the container.
    -   The remove button (`.search-history-item-remove`) is initially transparent and changes background on hover to indicate its interactive area.

### `.search-history-footer`, `.search-history-action`

-   **Purpose**: Style the footer area of the dropdown.
-   **Behavior**: The footer uses a flexbox layout to space out its content, which typically includes action buttons like "Clear History".
-   **Interaction**: Action elements (`.search-history-action`) are styled to look like links and show an underline on hover to indicate they are clickable.