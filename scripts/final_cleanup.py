#!/usr/bin/env python3
"""
Final cleanup script to remove index commands from problematic locations
where they shouldn't appear (inside \ref{}, table notes, etc.)
"""

import re
import os
from typing import List

def clean_problematic_indexes(text: str) -> str:
    """Remove index commands from problematic locations."""
    result = text

    # Pattern 1: Remove index commands from inside \ref{} commands
    def clean_ref(match):
        ref_content = match.group(0)
        # Remove any index commands from within the ref
        cleaned = re.sub(r'\\index\{[^}]*\}', '', ref_content)
        return cleaned

    result = re.sub(r'\\ref\{[^}]*\\index\{[^}]*\}[^}]*\}', clean_ref, result)

    # Pattern 2: Remove index commands from table notes
    def clean_note(match):
        note_content = match.group(0)
        # Remove index commands from within note
        cleaned = re.sub(r'\\index\{[^}]*\}', '', note_content)
        return cleaned

    result = re.sub(r'note\s*=\s*\{[^}]*\\index\{[^}]*\}[^}]*\}', clean_note, result)

    # Pattern 3: Remove index commands from captions
    def clean_caption(match):
        caption_content = match.group(0)
        # Remove index commands from within caption
        cleaned = re.sub(r'\\index\{[^}]*\}', '', caption_content)
        return cleaned

    result = re.sub(r'caption\s*=\s*\{[^}]*\\index\{[^}]*\}[^}]*\}', clean_caption, result)

    # Pattern 4: Remove nested or malformed index commands
    # Remove double nested indexes like \index{term!\index{other}}
    while re.search(r'\\index\{[^}]*\\index\{[^}]*\}[^}]*\}', result):
        result = re.sub(r'\\index\{([^}]*)\\index\{[^}]*\}([^}]*)\}', r'\\index{\1\2}', result)

    # Pattern 5: Remove index commands from labels (shouldn't be any left, but just in case)
    result = re.sub(r'(\\label\{[^}]*)\\index\{[^}]*\}([^}]*\})', r'\1\2', result)

    # Pattern 6: Clean up any remaining malformed patterns
    # Remove empty index commands
    result = re.sub(r'\\index\{\s*\}', '', result)

    # Remove index commands with only punctuation or spaces
    result = re.sub(r'\\index\{[^a-zA-Z0-9]*\}', '', result)

    return result

def process_file(filepath: str) -> dict:
    """Process a single file and return statistics."""
    with open(filepath, 'r', encoding='utf-8') as f:
        original_content = f.read()

    # Count original problematic patterns
    original_ref_indexes = len(re.findall(r'\\ref\{[^}]*\\index\{[^}]*\}[^}]*\}', original_content))
    original_note_indexes = len(re.findall(r'note\s*=\s*\{[^}]*\\index\{[^}]*\}[^}]*\}', original_content))
    original_nested_indexes = len(re.findall(r'\\index\{[^}]*\\index\{[^}]*\}[^}]*\}', original_content))
    original_total_indexes = len(re.findall(r'\\index\{[^}]*\}', original_content))

    # Clean the content
    cleaned_content = clean_problematic_indexes(original_content)

    # Count remaining
    final_ref_indexes = len(re.findall(r'\\ref\{[^}]*\\index\{[^}]*\}[^}]*\}', cleaned_content))
    final_note_indexes = len(re.findall(r'note\s*=\s*\{[^}]*\\index\{[^}]*\}[^}]*\}', cleaned_content))
    final_nested_indexes = len(re.findall(r'\\index\{[^}]*\\index\{[^}]*\}[^}]*\}', cleaned_content))
    final_total_indexes = len(re.findall(r'\\index\{[^}]*\}', cleaned_content))

    # Write back if changes were made
    if cleaned_content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)

    stats = {
        'original_total_indexes': original_total_indexes,
        'final_total_indexes': final_total_indexes,
        'removed_from_refs': original_ref_indexes - final_ref_indexes,
        'removed_from_notes': original_note_indexes - final_note_indexes,
        'removed_nested': original_nested_indexes - final_nested_indexes,
        'total_removed': original_total_indexes - final_total_indexes,
        'changes_made': cleaned_content != original_content
    }

    return stats

def main():
    """Main execution function."""
    # List of LaTeX files to process
    latex_files = [
        "Chapters/Chapter01.tex", "Chapters/Chapter02.tex", "Chapters/Chapter03.tex",
        "Chapters/Chapter04.tex", "Chapters/Chapter05.tex", "Chapters/Chapter06.tex",
        "Chapters/Chapter07.tex", "Chapters/Chapter08.tex", "Chapters/Chapter09.tex",
        "Chapters/Chapter10.tex", "Chapters/Chapter11.tex", "Chapters/Chapter12.tex",
        "Chapters/Chapter13.tex", "Chapters/Chapter14.tex", "Chapters/Chapter15.tex",
        "Chapters/Chapter16.tex", "Chapters/Chapter17.tex", "Chapters/Chapter18.tex",
        "Chapters/Chapter19.tex", "Chapters/Chapter20.tex", "Chapters/Chapter21.tex",
        "Chapters/Chapter22.tex", "Chapters/Chapter23.tex", "Chapters/Chapter24.tex",
        "Chapters/Introduction.tex", "Chapters/Conclusion.tex",
        "Chapters/Appendix00.tex", "Chapters/Appendix01.tex", "Chapters/Appendix02.tex",
        "Chapters/Appendix03.tex", "Chapters/Appendix04.tex", "Chapters/Appendix05.tex",
        "Chapters/Appendix06.tex"
    ]

    print("Final Index Cleanup - Removing Problematic Placements")
    print("=" * 60)

    total_stats = {
        'files_processed': 0,
        'files_changed': 0,
        'total_indexes_removed': 0,
        'removed_from_refs': 0,
        'removed_from_notes': 0,
        'removed_nested': 0
    }

    for filepath in latex_files:
        if os.path.exists(filepath):
            print(f"Processing {filepath}...")
            try:
                stats = process_file(filepath)

                total_stats['files_processed'] += 1
                if stats['changes_made']:
                    total_stats['files_changed'] += 1
                total_stats['total_indexes_removed'] += stats['total_removed']
                total_stats['removed_from_refs'] += stats['removed_from_refs']
                total_stats['removed_from_notes'] += stats['removed_from_notes']
                total_stats['removed_nested'] += stats['removed_nested']

                if stats['changes_made']:
                    print(f"  Removed {stats['total_removed']} problematic index commands")
                    if stats['removed_from_refs'] > 0:
                        print(f"    - {stats['removed_from_refs']} from \\ref{{}}")
                    if stats['removed_from_notes'] > 0:
                        print(f"    - {stats['removed_from_notes']} from table notes")
                    if stats['removed_nested'] > 0:
                        print(f"    - {stats['removed_nested']} nested indexes")
                else:
                    print(f"  No problematic index commands found")

            except Exception as e:
                print(f"Error processing {filepath}: {e}")
        else:
            print(f"File not found: {filepath}")

    print(f"\nFinal Cleanup Summary:")
    print("=" * 60)
    print(f"Files processed: {total_stats['files_processed']}")
    print(f"Files changed: {total_stats['files_changed']}")
    print(f"Total problematic indexes removed: {total_stats['total_indexes_removed']}")
    print(f"  - From \\ref{{}}: {total_stats['removed_from_refs']}")
    print(f"  - From table notes: {total_stats['removed_from_notes']}")
    print(f"  - Nested indexes: {total_stats['removed_nested']}")

if __name__ == "__main__":
    main()
