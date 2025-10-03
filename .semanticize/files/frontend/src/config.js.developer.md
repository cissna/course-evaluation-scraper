# Configuration Module (`frontend/src/config.js`)

This module centralizes environment-specific configuration constants for the frontend application, primarily focusing on defining the base URL for backend API interactions.

## Core Export

### Constant: `API_BASE_URL`

**Summary:**
This constant determines the root endpoint for all API calls made by the frontend application. It is dynamically set based on the deployment environment (`NODE_ENV`).

**Big-Picture Understanding:**
This configuration acts as the switchboard connecting the client-side code to the appropriate server-side service. In development, it points to a local server instance (e.g., Flask running on port 5000). In production (e.g., deployed on Vercel or similar platforms), it defaults to an empty string, relying on relative paths to ensure the API requests are routed correctly to the corresponding backend service running on the same origin.

**High-Level Interaction Patterns:**
Any service or utility layer responsible for fetching data (e.g., an Axios instance or a dedicated API client) should prepend this value to relative endpoint paths (e.g., `/users`) to construct the full request URL (e.g., `http://127.0.0.1:5000/users` in dev, or `/users` in prod).

**Exported Members:**
*   `API_BASE_URL`: String representing the base URL for the backend API.