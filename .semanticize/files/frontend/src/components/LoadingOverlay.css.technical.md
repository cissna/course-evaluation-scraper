## CSS Technical Documentation: `frontend/src/components/LoadingOverlay.css`

This stylesheet defines the appearance and behavior of a loading overlay component, which is used to indicate a loading state to the user, typically during asynchronous operations like data fetching. It consists of a full-screen semi-transparent backdrop, a spinning animation, and an optional message.

### **`.loading-overlay`**

This class styles the main container of the overlay, making it cover the entire viewport.

-   **`position: fixed;`**: This fixes the element's position relative to the browser's viewport. It ensures the overlay covers the entire screen and stays in place even if the user scrolls the page content underneath.
-   **`inset: 0;`**: This is a shorthand property for `top: 0; right: 0; bottom: 0; left: 0;`. It stretches the overlay to fill the entire viewport, from edge to edge.
-   **`background: rgba(0, 0, 0, 0.5);`**: Sets the background of the overlay to a semi-transparent black color. The `0.5` alpha value makes the underlying content partially visible, indicating a modal state without completely obscuring the page.
-   **`display: flex;`**: Establishes the overlay as a flex container, enabling easy centering of its child elements (the spinner and message).
-   **`align-items: center;`**: Vertically aligns the flex items (the spinner and message) to the center of the container.
-   **`justify-content: center;`**: Horizontally aligns the flex items to the center of the container.
-   **`z-index: 9999;`**: Sets a very high stack order for the overlay. This ensures it appears on top of all other content on the page.
-   **`backdrop-filter: blur(2px);`**: Applies a 2-pixel blur effect to the content *behind* the overlay. This enhances the focus on the loading indicator by making the background less distinct. Browser support for this property may vary.

### **`.loading-spinner`**

This class creates the visual representation of the spinner itself.

-   **`width: 48px;`** and **`height: 48px;`**: Define the dimensions of the spinner, making it a square.
-   **`border: 5px solid rgba(255, 255, 255, 0.3);`**: Sets a 5-pixel wide, semi-transparent white border around the element. This forms the "track" of the spinner.
-   **`border-top-color: #fff;`**: Overrides the color of the top part of the border, making it fully opaque white. This creates the "head" of the spinner that appears to be moving.
-   **`border-radius: 50%;`**: Makes the square element a perfect circle.
-   **`animation: spin 1s linear infinite;`**: Applies the `spin` animation to the element.
    -   `spin`: The name of the `@keyframes` rule to use.
    -   `1s`: The duration of one full animation cycle (one rotation) is 1 second.
    -   `linear`: The animation proceeds at a constant speed from start to finish.
    -   `infinite`: The animation repeats indefinitely.

### **`.loading-message`**

This class styles the text that can be displayed below the spinner.

-   **`color: #fff;`**: Sets the text color to white for high contrast against the dark overlay.
-   **`margin-top: 12px;`**: Adds some vertical space between the spinner and the message.
-   **`font-size: 16px;`**: Sets the size of the text.

### **`@keyframes spin`**

This rule defines the rotation animation used by the `.loading-spinner`.

-   **`@keyframes spin`**: Declares an animation named "spin".
-   **`to { transform: rotate(360deg); }`**: Defines the end state of the animation. The element will be rotated a full 360 degrees from its starting position. Since the animation is set to `infinite`, it will continuously rotate from 0 to 360 degrees.