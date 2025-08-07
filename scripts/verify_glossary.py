import os
import re
import sys
from collections import defaultdict

def main():
    """
    Main function to verify glossary key usage in LaTeX files.
    """
    # The script is run from the project root (TechSpecsTVI)
    project_root = os.getcwd()
    glossary_file = os.path.join(project_root, 'glossary_preamble.tex')
    chapters_dir = os.path.join(project_root, 'Chapters')

    if not os.path.exists(glossary_file):
        print(f"Error: Glossary file not found at '{glossary_file}'")
        sys.exit(1)
    if not os.path.exists(chapters_dir):
        print(f"Error: Chapters directory not found at '{chapters_dir}'")
        sys.exit(1)

    # 1. Get all defined glossary keys from the preamble file.
    try:
        with open(glossary_file, 'r', encoding='utf-8') as f:
            content = f.read()
        defined_keys = set(re.findall(r'\\newglossaryentry\{(.*?)\}', content))
        defined_keys_lower = {key.lower() for key in defined_keys}
    except IOError as e:
        print(f"Error reading glossary file: {e}")
        sys.exit(1)

    print(f"Found {len(defined_keys)} unique glossary entries in '{os.path.basename(glossary_file)}'.")
    print("-" * 30)

    # Dictionaries to hold errors and warnings
    mismatches = defaultdict(list)
    undefined_keys = defaultdict(list)

    # 2. Iterate through all .tex files in the Chapters directory.
    for filename in sorted(os.listdir(chapters_dir)):
        if filename.endswith('.tex'):
            file_path = os.path.join(chapters_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()

                # Find all \gls{...} usages
                used_keys = re.findall(r'\\gls\{(.*?)\}', file_content)

                if not used_keys:
                    continue

                for key in set(used_keys): # Use set to check each unique key only once per file
                    if key in defined_keys:
                        continue  # Exact match, no issue.

                    # Check for case-insensitive match
                    if key.lower() in defined_keys_lower:
                        # Find the original casing
                        original_key = next((k for k in defined_keys if k.lower() == key.lower()), None)
                        mismatches[filename].append(f"'{key}' should be '{original_key}'")
                    else:
                        undefined_keys[filename].append(key)

            except IOError as e:
                print(f"Could not read file {filename}: {e}")

    # 3. Report the findings.
    print("Verification Complete. Results:\n")
    has_issues = False

    if mismatches:
        has_issues = True
        print("--- Capitalization Mismatches Found (Warnings) ---")
        for filename, issues in mismatches.items():
            print(f"\nFile: {filename}")
            for issue in issues:
                print(f"  - {issue}")

    if undefined_keys:
        has_issues = True
        print("\n--- Undefined Glossary Keys Found (Errors) ---")
        for filename, keys in undefined_keys.items():
            print(f"\nFile: {filename}")
            for key in keys:
                print(f"  - '{key}' is not defined in the glossary.")

    if not has_issues:
        print("Success! All `\\gls{key}` commands match their definitions in the glossary.")

if __name__ == "__main__":
    main()
