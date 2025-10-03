# `frontend/package.json` Developer Documentation

## Overview

This file defines the project metadata, dependencies, and scripts for the React-based frontend application. It serves as the manifest for the Node.js package manager (npm), outlining everything needed to build, run, and test the user-facing single-page application (SPA). The project is configured using `react-scripts` (from Create React App), which abstracts away complex build configurations.

## Key Sections

### `dependencies`

This section lists the libraries the application relies on to function.

-   **`react`, `react-dom`**: The core libraries for building the user interface with the React framework.
-   **`react-scripts`**: A set of scripts and configurations from Create React App used to run, build, and test the application. It provides a standardized development environment.
-   **`@testing-library/*`**: A suite of packages (`dom`, `jest-dom`, `react`, `user-event`) used for writing unit and integration tests that simulate user behavior and interactions with the React components.
-   **`@vercel/analytics`**: A library for integrating with Vercel's analytics service to track application usage and performance metrics when deployed.
-   **`web-vitals`**: A small library for measuring and reporting on key web performance metrics (e.g., LCP, FID, CLS).

### `scripts`

These are the command-line tasks that can be executed using `npm run <script_name>`.

-   **`start`**: Starts the development server with hot-reloading. This is the primary command used during development to view changes live at `http://localhost:3000`.
-   **`build`**: Compiles and bundles the application (HTML, CSS, JS) into a `build` directory for production deployment. It optimizes the assets for performance.
-   **`test`**: Runs the test suite using Jest, the test runner included with Create React App. It will execute all `*.test.js` files.
-   **`eject`**: A one-way operation that removes the `react-scripts` dependency and copies all its configuration files (like Webpack, Babel, ESLint) directly into the project. This allows for full customization of the build process but is an advanced and irreversible step.

### `eslintConfig`

This object configures the ESLint linter to enforce code quality and style. The configuration extends the recommended rules from `react-app` and `react-app/jest`, ensuring the code adheres to the standards set by the Create React App team.

### `browserslist`

This section defines the range of browsers the application is intended to support. It is used by tools like Babel and Autoprefixer to generate CSS and JavaScript that is compatible with the specified browsers.
-   **`production`**: Specifies the target browsers for the production build, focusing on modern, widely-used versions.
-   **`development`**: Specifies the target browsers for the development environment, typically the latest versions of major browsers.