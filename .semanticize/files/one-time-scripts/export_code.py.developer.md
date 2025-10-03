# `one-time-scripts/export_code.py` Developer Documentation

This script is a utility designed to recursively traverse the current directory structure and export the source code of selected files. The primary use case is likely generating a comprehensive, documented snapshot of the project's source code, often for external review, documentation generation, or LLM context provision.

## Constants

The script relies on several global constants to define what should be included or excluded from the export process.

| Constant | Type | Purpose |
| :--- | :--- | :--- |
| `EXCLUDE_PARTS` | `set` of `str` | Directories or filenames that, if encountered, cause the traversal to skip that path entirely (e.g., dependency folders, build artifacts, version control). |
| `EXTENSIONS` | `set` of `str` | File extensions that are considered source code and should be included in the export (e.g., `.py`, `.js`, `.html`). |
| `KEEP_SPECIFIC` | `list` of `str` | A curated list of file paths to include when the `--specific` flag is used. These files are generally related to core dataflow or application logic. |

## Functions

### `should_include_file(filepath)`

**Summary:**
Determines whether a given file path should be included in the final export list based on a complex set of exclusion and inclusion rules. This function acts as the primary filter during directory traversal.

**Component Role:**
It checks the path against excluded directories (`EXCLUDE_PARTS`), validates the file extension against allowed types (`EXTENSIONS`), and applies several specific, hardcoded exclusion rules (e.g., excluding test files, `__init__.py`, or certain root-level utility scripts).

**Big-Picture Understanding:**
This function encapsulates all the business logic for filtering source code files, ensuring that noise, dependencies, and generated artifacts are omitted from the final output.

**High-Level Interaction Patterns:**
Called repeatedly by `os.walk` within `main()` for every discovered file to decide its fate before it's added to the processing list.

### `main()`

**Summary:**
The entry point of the script. It handles argument parsing, initiates the recursive file discovery, applies final filtering based on command-line flags, and formats the output either as a plain list of filenames or as complete code blocks formatted in Markdown.

**Component Role:**
1.  **Argument Parsing:** Accepts flags for output format (`--name-only`) and scope (`--specific`).
2.  **Traversal & Initial Filtering:** Uses `os.walk` to traverse the directory, modifying the `dirs` list in place to skip excluded directories specified in `EXCLUDE_PARTS` immediately during traversal. It calls `should_include_file` for every file encountered.
3.  **Specific Filtering:** If `--specific` is set, the collected list is further filtered against the `KEEP_SPECIFIC` list.
4.  **Output Generation:** Prints results. If `--name-only`, it prints paths; otherwise, it prints each file wrapped in Markdown headers (`### path/to/file`) and fenced code blocks (```).

**Big-Picture Understanding:**
This function orchestrates the entire export process, managing configuration via CLI arguments and translating the resulting file list into the desired output format.

**High-Level Interaction Patterns:**
1.  Receives command-line arguments.
2.  Drives the file system traversal via `os.walk`.
3.  Applies post-processing filters based on `args.specific`.
4.  Executes the final print loop based on `args.name_only`.