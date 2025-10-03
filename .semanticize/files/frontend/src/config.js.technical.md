# File: frontend/src/config.js

This file is responsible for defining and exporting the base URL for the backend API, dynamically configuring it based on the current execution environment (development or production). This pattern is crucial for ensuring the frontend application correctly targets the backend service regardless of where it is deployed.

## Overview

The module exports a single constant, `API_BASE_URL`, which resolves to either an empty string (for production environments, typically allowing for relative path resolution) or a specific local host address (for development environments, pointing to a local Flask server).

## Implementation Details

### Environment Variable Check and Conditional Logic

The configuration relies on the standard Node.js/frontend environment variable `process.env.NODE_ENV`.

1.  **`process.env.NODE_ENV`**: This global variable holds a string indicating the execution environment. Common values are `'development'` and `'production'`.
2.  **Ternary Operator (`? :`)**: A conditional expression is used to assign the value to `API_BASE_URL`.

    ```javascript
    process.env.NODE_ENV === 'production' ? (Value if true) : (Value if false)
    ```

### Configuration Logic Breakdown

| Condition (`process.env.NODE_ENV === 'production'`) | Assigned Value | Rationale |
| :--- | :--- | :--- |
| `true` (Production Environment) | `''` (Empty String) | When deployed (e.g., on Vercel or a static host), using an empty string results in **relative URLs**. If the frontend is hosted at `https://myapp.com/`, an API call to `/users` will correctly resolve to `https://myapp.com/users`. This is the standard practice for modern deployments where the frontend and backend might share the same domain or where a proxy handles routing. |
| `false` (Development Environment) | `'http://127.0.0.1:5000'` | During local development, the frontend (often running on a default port like 3000 or 5173) needs to explicitly target the backend server, which is assumed to be running locally on port 5000 (common for Flask/Python backends). |

## Line-by-Line Analysis

| Line | Code | Description |
| :--- | :--- | :--- |
| 1 | `// API configuration` | Comment indicating the purpose of the subsequent configuration block. |
| 2 | `const API_BASE_URL = process.env.NODE_ENV === 'production'` | **Declaration**: Declares a constant variable `API_BASE_URL`. **Condition Check**: Begins a ternary operation comparing the environment variable `process.env.NODE_ENV` against the string literal `'production'`. |
| 3 | `? ''` | **True Case**: If the environment is production, `API_BASE_URL` is set to an empty string (`''`). This facilitates relative path resolution in the deployed environment. |
| 4 | `: 'http://127.0.0.1:5000';` | **False Case**: If the environment is *not* production (i.e., development or testing), `API_BASE_URL` is set to the hardcoded address of the local backend server. |
| 5 | | Empty line for separation. |
| 6 | `export { API_BASE_URL };` | **Export**: Exports the configured `API_BASE_URL` constant, making it available for import by other modules within the frontend application (e.g., Axios instances or service layers). |

## Exported Interface

### Constant: `API_BASE_URL`

| Type | Description |
| :--- | :--- |
| `string` | The base URL endpoint for backend API requests. |

**Function Signatures (N/A - It is a constant):**
No functions are defined or exported.

**Parameters (N/A):**
None.

**Return Value (N/A):**
The value is a constant exported directly.