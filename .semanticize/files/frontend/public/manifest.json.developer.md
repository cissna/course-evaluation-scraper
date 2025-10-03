# Web App Manifest (manifest.json)

This file is the web app manifest for the React frontend. It provides the necessary metadata for the browser to treat the application as a Progressive Web App (PWA). This allows users to "install" the app on their mobile or desktop devices, providing a more native-like experience.

## Configuration Details

-   **`short_name` & `name`**: These fields define the name of the application. `short_name` is used where space is limited (e.g., under the app icon on a home screen), while `name` is the full application name.

-   **`icons`**: This array specifies a set of icons for the browser to use in different contexts, such as the home screen icon, task switcher, or splash screen. Multiple sizes are provided to ensure the icon looks sharp on various device resolutions.

-   **`start_url`**: Defines the entry point of the application when it's launched from an installed icon. `.` indicates that it should start from the root of the frontend application's path.

-   **`display`**: Set to `standalone`, this tells the browser to open the app in its own window, without any browser UI (like the address bar or navigation buttons), making it feel like a native application.

-   **`theme_color`**: Specifies the default theme color for the application. This color is used by the operating system to style the UI elements around the app, such as the status bar on mobile devices.

-   **`background_color`**: Defines the background color of the splash screen that is displayed while the application is loading after being launched from the home screen.