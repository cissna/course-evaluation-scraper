### Constant: `ALL_STAT_KEYS`

**Summary:**
An array containing every unique backend key present in `STATISTICS_CONFIG`.

**Big Picture:**
Provides a simple, derived list of all available statistic identifiers.

**Interaction Pattern:**
Used by other utility functions to iterate over the complete set of known statistics.

### Constant: `STAT_MAPPINGS`

**Summary:**
A legacy mapping object that translates every backend key directly to its corresponding display name.

**Big Picture:**
Maintained primarily for backward compatibility with older parts of the application that might expect a direct key-to-name lookup map, although direct use of `getDisplayName` is preferred.

**Interaction Pattern:**
Derived from `STATISTICS_CONFIG` via `Object.keys` and `Object.fromEntries`.

### Function: `getDisplayName(backendKey)`

**Summary:**
Retrieves the user-friendly display name associated with a given backend statistic key. If the key is unknown, it defaults to returning the key itself.

**Big Picture:**
Ensures that statistical data retrieved using technical keys is presented correctly to the user.

**Interaction Pattern:**
Called whenever a display name is needed for a specific statistic key (e.g., rendering labels in charts or tables).

### Function: `getAllStatistics()`

**Summary:**
Generates a comprehensive array of objects, one for each statistic, containing its `key`, `displayName`, and `defaultEnabled` state.

**Big Picture:**
Provides a structured list of all statistics suitable for rendering configuration UIs (like toggles or selection menus) where all metadata is required simultaneously.

**Interaction Pattern:**
Used to populate configuration screens or dynamic lists that need full context for every statistic.

### Function: `getInitialStatsState()`

**Summary:**
Constructs an object representing the default user preference state for statistics. The keys are the statistic keys, and the values are their respective `defaultEnabled` boolean states defined in `STATISTICS_CONFIG`.

**Big Picture:**
Crucial for initializing user settings or local storage caches to ensure a consistent default view before any user customization is applied.

**Interaction Pattern:**
Called during application bootstrapping or when resetting user preferences to establish the baseline configuration.