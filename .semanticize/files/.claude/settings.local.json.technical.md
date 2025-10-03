---

### 2.1. `outputStyle` Parameter

-   **Line:** `2`
-   **Key:** `outputStyle`
-   **Type:** `String`
-   **Value:** `"Explanatory"`

#### Description

This parameter controls the verbosity and nature of the AI's responses.

-   **`"Explanatory"`**: This value instructs the AI to provide detailed, thorough, and educational responses. Instead of just providing a direct answer or code, it will aim to explain the context, implementation details, and reasoning behind its response. This is the highest level of verbosity.

---

### 2.2. `permissions` Object

-   **Line:** `3`
-   **Key:** `permissions`
-   **Type:** `Object`

#### Description

This object defines the security and access control rules that the AI must adhere to within the project. It contains lists of rules that either allow or deny specific actions on files and directories.

---

### 2.3. `permissions.deny` Array

-   **Line:** `4`
-   **Key:** `deny`
-   **Type:** `Array<String>`

#### Description

This array contains a list of rules that explicitly forbid the AI from performing certain actions. The rules are expressed as strings, where each string follows a `Verb(GlobPattern)` format.

-   **`Verb`**: The action to be denied (e.g., `Read`).
-   **`GlobPattern`**: A file path pattern that specifies the target of the rule. The `**/` pattern is used to match files in any subdirectory of the project.

#### Rules

1.  **`"Read(**/data.json/**)"`**
    -   **Line:** `5`
    -   **Description:** This rule prevents the AI from reading any file named `data.json`, regardless of its location within the project. This is a security measure to protect potentially large, sensitive, or deprecated data that was part of the old file-based system.

2.  **`"Read(**/failed.json/**)"`**
    -   **Line:** `6`
    -   **Description:** This rule prevents the AI from reading any file named `failed.json`. This file likely contains logs or records of failed scraping attempts, which are not relevant for most development tasks.

3.  **`"Read(**/metadata.json/**)"`**
    -   **Line:** `7`
    -   **Description:** This rule prevents the AI from reading any file named `metadata.json`. Similar to `data.json`, this file is a remnant of the previous architecture. Denying access ensures the AI interacts with the current database-driven system via its API rather than relying on stale, file-based metadata.