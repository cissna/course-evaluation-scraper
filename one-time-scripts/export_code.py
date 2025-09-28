#!/usr/bin/env python3
import os
import argparse

# Directories to exclude
EXCLUDE_PARTS = {'.vercel', 'node_modules', '.git', 'one-time-scripts', 'frontend/build', 'metadata.json', 'data.json',
                 '__pycache__'}

# File extensions to include
EXTENSIONS = {'.py', '.js', '.html', '.json', '.sql'}

# Specific files to keep when using --specific flag (dataflow-related only)
KEEP_SPECIFIC = [
    'backend/app.py',
    'backend/analysis.py',
    'backend/db_utils.py',
    'backend/course_grouping_service.py',
    'backend/config.py',
    'frontend/src/App.js',
    'frontend/src/components/DataDisplay.js',
    'frontend/src/components/AdvancedOptions.js',
    'frontend/src/components/CourseSearch.js',
    'frontend/src/utils/statsMapping.js',
    'frontend/src/utils/yearUtils.js',
    'frontend/src/config.js'
]

def should_include_file(filepath):
    # Check if file is in excluded directories/is excluded
    for part in filepath.split(os.sep):
        if part in EXCLUDE_PARTS:
            return False
    # Check extension
    _, ext = os.path.splitext(filepath)
    if ext not in EXTENSIONS:
        return False

    # Exclude specific files
    filename = os.path.basename(filepath)
    dirname = os.path.dirname(filepath)

    # Exclude files in frontend/build
    if 'frontend/build' in filepath:
        return False

    # Exclude __init__.py files
    if filename == '__init__.py':
        return False

    # Exclude .test.js files
    if filename.endswith('.test.js'):
        return False

    # Exclude root-level scripts and data files
    if dirname == '.' and filename in [
        'migrate_data.py', 'run_all.sh', 'db_setup.py', 'export_data.py',
        'db_schema.sql', 'backend_import_helper.py'
    ]:
        return False

    return True

def main():
    parser = argparse.ArgumentParser(description="Export code files in markdown format or list names only.")
    parser.add_argument('--name-only', action='store_true', help="Print only the filenames, one per line.")
    parser.add_argument('--specific', action='store_true', help="Export only the specific dataflow-related files listed in KEEP_SPECIFIC.")
    args = parser.parse_args()

    # Find all files recursively
    code_files = []
    for root, dirs, files in os.walk('.'):
        # Modify dirs in place to skip excluded
        dirs[:] = [d for d in dirs if d not in EXCLUDE_PARTS]
        for file in files:
            filepath = os.path.join(root, file)
            if should_include_file(filepath):
                code_files.append(filepath)

    # Sort for consistent output
    code_files.sort()

    # Filter to specific files if --specific flag is used
    if args.specific:
        code_files = [f for f in code_files if f.lstrip('./') in KEEP_SPECIFIC]

    if args.name_only:
        # Print filenames only, one per line
        for filepath in code_files:
            display_path = filepath.lstrip('./')
            print(display_path)
    else:
        # Output in markdown format
        for filepath in code_files:
            # Remove leading ./
            display_path = filepath.lstrip('./')
            print(f"### {display_path}")
            print()
            print("```")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(content)
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
            print("```")
            print()

if __name__ == "__main__":
    main()