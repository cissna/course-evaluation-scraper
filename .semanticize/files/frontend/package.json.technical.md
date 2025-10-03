# Technical Documentation for `frontend/package.json`

This file serves as the manifest for the Node.js project, defining its metadata, dependencies, and scripts. It is the central configuration file used by `npm` (Node Package Manager) and other tools in the JavaScript ecosystem to manage the project.

## Root-Level Properties

-   **`name`**: `"frontend"`
    -   Specifies the name of the package. This is used to identify the project, especially if it were to be published to a registry like npm.

-   **`version`**: `"0.1.0"`
    -   Defines the current version of the application, following Semantic Versioning (SemVer). This helps in tracking releases and managing dependencies.

-   **`private`**: `true`
    -   A boolean flag that, when set to `true`, prevents the package from being accidentally published to a public registry like npm. This is a safeguard for private or application-specific codebases.

## `dependencies`

This object lists all the packages required for the application to run in a production environment. The versions specified follow SemVer ranges (e.g., `^16.3.0` means any compatible version from 16.3.0 up to, but not including, 17.0.0).

-   **`@testing-library/dom`**: `"^10.4.0"`
    -   Provides core utilities for querying and interacting with the DOM in a way that encourages testing practices that resemble how users interact with the application. It's a dependency for other `@testing-library` packages.

-   **`@testing-library/jest-dom`**: `"^6.6.3"`
    -   Provides a set of custom Jest matchers to assert the state of the DOM. This allows for more readable and declarative tests, such as using `expect(element).toBeInTheDocument()`.

-   **`@testing-library/react`**: `"^16.3.0"`
    -   The primary testing utility for React components. It builds on `@testing-library/dom` to provide APIs for rendering components into a virtual DOM, querying them, and firing events.

-   **`@testing-library/user-event`**: `"^13.5.0"`
    -   A companion library for `@testing-library` that simulates user interactions (like typing, clicking, hovering) more realistically than `fireEvent`.

-   **`@vercel/analytics`**: `"^1.0.0"`
    -   The official Vercel Analytics package for React. It is used to track web vitals and other performance metrics when the application is deployed on the Vercel platform.

-   **`react`**: `"^19.1.0"`
    -   The core library for building user interfaces. It provides the component model, state management (e.g., `useState`, `useEffect`), and the reconciliation algorithm (Fiber).

-   **`react-dom`**: `"^19.1.0"`
    -   Acts as the entry point to the DOM and server-side rendering for React. It provides DOM-specific methods, with the most common being `ReactDOM.createRoot()` to render a React component tree into a specific DOM element.

-   **`react-scripts`**: `"5.0.1"`
    -   A set of scripts and configurations from the Create React App (CRA) toolkit. It abstracts away the complex build setup (Webpack, Babel, ESLint, etc.) into a single dependency, providing standardized scripts for development, building, and testing.

-   **`web-vitals`**: `"^2.1.4"`
    -   A small library for measuring real-user web performance metrics, such as Largest Contentful Paint (LCP), First Input Delay (FID), and Cumulative Layout Shift (CLS). It's used by Create React App to report these vitals.

## `scripts`

This object defines a set of command-line scripts that can be executed using `npm run <script-name>`. These are aliases for the underlying `react-scripts` commands.

-   **`start`**: `"react-scripts start"`
    -   Starts the development server with hot-reloading. This allows for real-time feedback as code is changed. It runs the application in development mode.

-   **`build`**: `"react-scripts build"`
    -   Bundles the application into static files for production. It transpiles the JavaScript, minifies the code, optimizes assets, and outputs the result into a `build` directory.

-   **`test`**: `"react-scripts test"`
    -   Launches the test runner (Jest) in an interactive watch mode. It automatically runs tests related to files changed since the last commit.

-   **`eject`**: `"react-scripts eject"`
    -   A one-way operation that removes the `react-scripts` dependency and copies all its configuration files (Webpack, Babel, etc.) and scripts directly into the project. This gives full control over the build configuration but is an advanced and irreversible action.

## `eslintConfig`

This object configures the ESLint linter for the project.

-   **`extends`**: `["react-app", "react-app/jest"]`
    -   Specifies that the project's ESLint configuration should inherit from the base rules provided by Create React App (`react-app`) and the specific rules for Jest tests (`react-app/jest`). This ensures code quality and consistency without manual setup.

## `browserslist`

This configuration is used by tools like Babel (for transpiling JavaScript) and Autoprefixer (for adding CSS vendor prefixes) to determine the target browsers for the compiled code.

-   **`production`**: `[">0.2%", "not dead", "not op_mini all"]`
    -   For the production build, the code will be compatible with:
        -   Browsers that have more than 0.2% market share.
        -   Browsers that are not "dead" (i.e., have not had official support or updates for 24 months).
        -   Excludes the Opera Mini browser.

-   **`development`**: `["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]`
    -   For the development environment, the code targets the latest version of the most common desktop browsers. This allows for faster builds as less transpilation is needed.