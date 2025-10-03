# CSS Global Stylesheet (`frontend/src/index.css`)

This file defines fundamental, global CSS resets and base styles applied to the entire application structure, primarily targeting the `<body>` and `<code>` elements.

## Component/Selector Level Summaries

### `body` Selector

**Purpose:** Establishes the foundational styles for the entire document viewport.

**Big-Picture Understanding:** This selector ensures a clean slate by removing default browser margins and sets the primary, system-native font stack for the application's main textual content. It prioritizes modern, crisp rendering across various operating systems.

**High-Level Interaction Patterns:**
*   **Layout Foundation:** Removes the default browser margin, which is crucial for frameworks or component libraries that expect to control layout margins precisely (e.g., full-bleed backgrounds or strict grid systems).
*   **Typography Baseline:** Defines the default font for all non-`code` text, affecting user readability and application aesthetic consistency.

### `code` Selector

**Purpose:** Defines the specific styling for inline or block code snippets within the application.

**Big-Picture Understanding:** This selector isolates code content from the main application typography, ensuring that programming syntax or machine output is visually distinct and uses a monospaced font for clarity.

**High-Level Interaction Patterns:**
*   **Content Differentiation:** Ensures that text enclosed in `<code>` tags (or similar semantic elements styled by this rule) uses a fixed-width font, which is the standard convention for displaying code.
*   **Readability:** Utilizes a comprehensive list of monospace fonts, falling back to the generic `monospace` family if platform-specific fonts are unavailable.