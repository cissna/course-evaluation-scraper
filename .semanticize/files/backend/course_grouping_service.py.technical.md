-   `department_patterns`: A dictionary where each key is a department prefix (e.g., `"EN.601"`) and the value is an object specifying rules for that department.
    -   `equivalent_levels`: A list of integers representing the "hundreds" level of a course (e.g., `400`, `600`). Courses within this department whose numbers fall into these levels are grouped if their last two digits match.
-   `explicit_groupings`: A list of objects, where each object defines a hardcoded group of courses.
    -   `courses`: A list of full course codes (e.g., `"AS.050.375"`) that belong together.
    -   `description`: A human-readable string describing the group.
    -   `primary`: An unused field, reserved for future use.

---

### 2.2. `__init__(self, config_path=None)`

The constructor initializes the `CourseGroupingService` instance.

-   **Signature**: `def __init__(self, config_path=None):`
-   **Parameters**:
    -   `config_path` (str, optional): The file path to a JSON configuration file. If `None`, the `DEFAULT_CONFIG` will be used.
-   **Implementation Details**:
    -   Stores the `config_path`.
    -   Initializes `self.department_patterns` and `self.explicit_groupings` as empty containers.
    -   Calls `self._load_config()` to populate these containers.

---

### 2.3. `_load_config(self)`

This method loads the grouping rules from either an external file or the embedded default configuration.

-   **Signature**: `def _load_config(self):`
-   **Logic**:
    1.  It checks if `self.config_path` was provided and if the file at that path exists.
    2.  **File-based Config**: If the file exists, it attempts to open, read, and parse the JSON content.
        -   It populates `self.department_patterns` and `self.explicit_groupings` from the corresponding keys in the JSON file. If a key is missing, it defaults to an empty container.
        -   If any error occurs during file reading or JSON parsing, it raises a `ValueError`.
    3.  **Default Config**: If no `config_path` was given or the file doesn't exist, it falls back to using `self.DEFAULT_CONFIG`.
        -   It populates `self.department_patterns` and `self.explicit_groupings` from the default object.

---

### 2.4. `_parse_course_code(self, code: str)`

A private helper method to validate and deconstruct a course code into its constituent parts.

-   **Signature**: `def _parse_course_code(self, code: str) -> tuple[str | None, str | None]:`
-   **Parameters**:
    -   `code` (str): The full course code, expected in the format `XX.###.###` (e.g., `"EN.601.485"`).
-   **Returns**:
    -   A tuple `(department, number)` if the code matches the pattern.
        -   `department` (str): The school and department prefix (e.g., `"EN.601"`).
        -   `number` (str): The final three-digit course number (e.g., `"485"`).
    -   A tuple `(None, None)` if the code does not match the expected format.
-   **Implementation Details**:
    -   It uses the regular expression `r'^([A-Z]{2,}\.\d{3})\.(\d{3})$'` to match and capture the two parts of the course code.

---

### 2.5. `_get_department_equivalents(self, dept: str, number: str)`

Finds equivalent courses based on the `department_patterns` configuration.

-   **Signature**: `def _get_department_equivalents(self, dept: str, number: str) -> List[str]:`
-   **Parameters**:
    -   `dept` (str): The department prefix of the course (e.g., `"EN.553"`).
    -   `number` (str): The three-digit number of the course (e.g., `"492"`).
-   **Returns**:
    -   A list of full course codes that are considered equivalent based on department-level rules. Returns an empty list if no pattern applies.
-   **Algorithm**:
    1.  Looks up the `dept` in `self.department_patterns`. If not found, returns `[]`.
    2.  Determines the level of the input course `number` (e.g., for "492", the level is 400). This is done via integer division: `(int(number) // 100) * 100`.
    3.  It checks if this course's level is present in the `equivalent_levels` list defined for that department pattern. If not, this specific course is not part of a pattern-based group, and the method returns `[]`.
    4.  If the level matches, it proceeds to generate the full list of equivalents. It iterates through each `lvl` in the `equivalent_levels` list.
    5.  For each `lvl`, it constructs a new course number by adding the last two digits of the original number (`course_level % 100`).
    6.  The new course code is formatted (e.g., `f"{dept}.{new_number:03d}"`) and added to a list of `equivalents`.
    7.  The final list of generated course codes is returned.

---

### 2.6. `_find_explicit_group(self, course_code: str)`

Finds if a course is part of a manually defined group in `explicit_groupings`.

-   **Signature**: `def _find_explicit_group(self, course_code: str) -> Dict | None:`
-   **Parameters**:
    -   `course_code` (str): The course code to search for.
-   **Returns**:
    -   The dictionary object for the group if found.
    -   `None` if the course is not in any explicit group.
-   **Implementation Details**:
    -   Performs a linear search through the `self.explicit_groupings` list.
    -   For each group, it checks if the `course_code` is present in the `group["courses"]` list.

---

### 2.7. `get_grouped_courses(self, course_code: str)`

The main public method to get all equivalent courses for a given course code. It combines results from both explicit and department-pattern groupings.

-   **Signature**: `def get_grouped_courses(self, course_code: str) -> List[str]:`
-   **Parameters**:
    -   `course_code` (str): The course code to find groups for.
-   **Returns**:
    -   A sorted list of unique course codes belonging to the group.
    -   If no group is found, it returns a list containing only the original `course_code`.
-   **Algorithm**:
    1.  Initializes an empty `set` named `grouped_courses` to automatically handle duplicate entries.
    2.  Calls `_find_explicit_group()`. If a group is found, all courses from that group are added to the set.
    3.  Calls `_parse_course_code()` to get the `dept` and `number`.
    4.  If `dept` and `number` are valid, it calls `_get_department_equivalents()` and adds any returned courses to the set. It also explicitly adds the original course code to ensure it's included.
    5.  After checking both grouping types, if the `grouped_courses` set is empty, it means no groups were found. In this case, it returns `[course_code]`.
    6.  Otherwise, it converts the set to a list, sorts it alphabetically, and returns the result.

---

### 2.8. `is_course_grouped(self, course_code: str)`

Checks if a course belongs to any group.

-   **Signature**: `def is_course_grouped(self, course_code: str) -> bool:`
-   **Parameters**:
    -   `course_code` (str): The course code to check.
-   **Returns**:
    -   `True` if the course is part of either a department-pattern group or an explicit group.
    -   `False` otherwise.
-   **Implementation Details**:
    -   It first checks for department equivalents. If any are found, it returns `True`.
    -   It then checks for an explicit group. If one is found, it returns `True`.
    -   If neither check succeeds, it returns `False`.

---

### 2.9. `get_group_info(self, course_code: str)`

Retrieves the full group information (courses and description) for a given course.

-   **Signature**: `def get_group_info(self, course_code: str) -> Dict:`
-   **Parameters**:
    -   `course_code` (str): The course code to get info for.
-   **Returns**:
    -   A dictionary containing `courses` (a sorted list) and a `description` (string).
    -   An empty dictionary `{}` if no group is found.
-   **Logic**:
    1.  It prioritizes explicit groups. It calls `_find_explicit_group()`. If a group is found, it returns a dictionary with the sorted list of courses and the group's description.
    2.  If no explicit group is found, it checks for a department-pattern group by calling `_get_department_equivalents()`.
    3.  If department equivalents are found, it returns a dictionary with the sorted list of all equivalent courses (including the original) and an empty string for the `description`, as descriptions are not defined for these patterns.
    4.  If no groups of any kind are found, it returns an empty dictionary.