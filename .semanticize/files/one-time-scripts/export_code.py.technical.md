| Argument | Type | Description | Default Behavior |
| :--- | :--- | :--- | :--- |
| `--name-only` | Flag | If set, outputs only the relative paths of included files, one per line. | Output is formatted Markdown blocks. |
| `--specific` | Flag | If set, *only* files listed in `KEEP_SPECIFIC` that also passed initial filtering are included. | All filtered files are included. |

## 4. Near Line-by-Line Documentation

| Line(s) | Code | Description |
| :--- | :--- | :--- |
| 1-2 | `#!/usr/bin/env python3` | Shebang line specifying the interpreter. |
| 3-4 | `import os`, `import argparse` | Imports necessary modules for OS interaction and argument parsing. |
| 6-11 | `EXCLUDE_PARTS = {...}` | Defines a set of directory names or specific files/paths to ignore during traversal and filtering. |
| 14-15 | `EXTENSIONS = {...}` | Defines a set of valid file extensions to include. |
| 18-31 | `KEEP_SPECIFIC = [...]` | Defines a hardcoded list of critical files to keep when `--specific` is active. |
| 33 | `def should_include_file(filepath):` | Function definition for file inclusion logic. |
| 35-37 | `for part in filepath.split(os.sep): ... return False` | **Directory Exclusion Check:** Splits the path and checks if any segment is in `EXCLUDE_PARTS`. |
| 39-41 | `_, ext = os.path.splitext(filepath); if ext not in EXTENSIONS: return False` | **Extension Check:** Ensures the file has an allowed extension. |
| 44-45 | `filename = os.path.basename(filepath)`, `dirname = os.path.dirname(filepath)` | Extracts filename and directory name for specific checks. |
| 48-49 | `if 'frontend/build' in filepath: return False` | Excludes content within the frontend build directory. |
| 52-53 | `if filename == '__init__.py': return False` | Excludes Python package initializer files. |
| 56-57 | `if filename.endswith('.test.js'): return False` | Excludes JavaScript test files. |
| 60-64 | `if dirname == '.' and filename in [...] : return False` | Excludes specific root-level utility/script files. |
| 66 | `return True` | If all checks pass, the file is included. |
| 68 | `def main():` | Main execution function. |
| 69-71 | `parser = argparse.ArgumentParser(...)`, `parser.add_argument(...)` | Sets up argument parsing for `--name-only` and `--specific`. |
| 72 | `args = parser.parse_args()` | Parses arguments provided by the user. |
| 75 | `code_files = []` | Initializes list to store discovered files. |
| 76 | `for root, dirs, files in os.walk('.'):` | Starts recursive directory traversal from the current directory. |
| 78 | `dirs[:] = [d for d in dirs if d not in EXCLUDE_PARTS]` | **Directory Pruning:** Modifies `dirs` in place to skip excluded directories in subsequent recursion levels. |
| 79-82 | `for file in files: ... code_files.append(filepath)` | Iterates through files in the current directory, constructs the path, checks inclusion, and appends if necessary. |
| 85 | `code_files.sort()` | Sorts the list for deterministic output. |
| 88-89 | `if args.specific: code_files = [f for f in code_files if f.lstrip('./') in KEEP_SPECIFIC]` | Applies the `--specific` filter if requested. |
| 91 | `if args.name_only:` | Checks if only names should be printed. |
| 93-95 | `for filepath in code_files: ... print(display_path)` | Prints filenames only, stripping leading `./`. |
| 97 | `else:` | Executes if Markdown output is requested. |
| 100-101 | `display_path = filepath.lstrip('./')`, `print(f"### {display_path}")` | Prints the file path as an H3 header. |
| 105-111 | `try: ... except Exception as e: ...` | Opens file in read mode (`utf-8`), reads content, prints content, and handles potential read errors. |
| 112 | `print("```")` | Closes the Markdown code block. |
| 113 | `print()` | Adds a final newline separator. |
| 115 | `if __name__ == "__main__":` | Standard Python entry point guard. |
| 116 | `main()` | Executes the main logic. |