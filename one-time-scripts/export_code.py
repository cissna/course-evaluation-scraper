#!/usr/bin/env python3
import os
import sys
import argparse

# Directories to exclude
EXCLUDE_DIRS = {'.vercel', 'node_modules', '.git', 'one-time-scripts', 'frontend/build'}

# File extensions to include
EXTENSIONS = {'.py', '.js', '.html'}

def should_include_file(filepath):
    # Check if file is in excluded directories
    parts = filepath.split(os.sep)
    for part in parts[:-1]:  # exclude the filename itself
        if part in EXCLUDE_DIRS:
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
    args = parser.parse_args()

    # Find all files recursively
    code_files = []
    for root, dirs, files in os.walk('.'):
        # Modify dirs in place to skip excluded
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            filepath = os.path.join(root, file)
            if should_include_file(filepath):
                code_files.append(filepath)

    # Sort for consistent output
    code_files.sort()

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