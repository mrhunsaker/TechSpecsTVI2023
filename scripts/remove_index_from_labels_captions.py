#!/usr/bin/env python3
"""
Remove all \index{} commands from inside \label{} and \caption{} commands.
These are structural LaTeX elements where index commands should not appear.
"""

import re
import os
from typing import List, Dict

def remove_index_from_labels_and_captions(text: str) -> str:
    """Remove \index{} commands from inside \label{} and \caption{} commands."""
    result = text

    # Pattern 1: Remove index commands from inside \label{} commands
    def clean_label(match):
        label_content = match.group(0)
        # Remove any \index{} commands from within the label
        cleaned = re.sub(r'\\index\{[^}]*\}', '', label_content)
        return cleaned

    # Find all \label{...} that contain \index{...}
    result = re.sub(r'\\label\{[^{}]*\\index\{[^}]*\}[^{}]*\}', clean_label, result)

    # Handle nested braces in labels more carefully
    def clean_complex_label(match):
        full_match = match.group(0)
        # Remove all \index{...} patterns
        cleaned = re.sub(r'\\index\{[^}]*\}', '', full_match)
        return cleaned

    # More complex pattern for labels with potential nested braces
    label_pattern = r'\\label\{'
    pos = 0
    while True:
        match = re.search(label_pattern, result[pos:])
        if not match:
            break

        start_pos = pos + match.start()
        brace_pos = pos + match.end() - 1  # Position of opening brace

        # Find matching closing brace
        brace_count = 1
        end_pos = brace_pos + 1

        while end_pos < len(result) and brace_count > 0:
            if result[end_pos] == '{':
                brace_count += 1
            elif result[end_pos] == '}':
                brace_count -= 1
            end_pos += 1

        if brace_count == 0:  # Found matching brace
            label_content = result[start_pos:end_pos]
            if '\\index{' in label_content:
                cleaned_label = re.sub(r'\\index\{[^}]*\}', '', label_content)
                result = result[:start_pos] + cleaned_label + result[end_pos:]
                pos = start_pos + len(cleaned_label)
            else:
                pos = end_pos
        else:
            pos += match.end()

    # Pattern 2: Remove index commands from inside \caption{} commands
    def clean_caption(match):
        caption_content = match.group(0)
        # Remove any \index{} commands from within the caption
        cleaned = re.sub(r'\\index\{[^}]*\}', '', caption_content)
        return cleaned

    # Simple captions first
    result = re.sub(r'\\caption\{[^{}]*\\index\{[^}]*\}[^{}]*\}', clean_caption, result)

    # Handle complex captions with nested braces
    caption_pattern = r'\\caption\{'
    pos = 0
    while True:
        match = re.search(caption_pattern, result[pos:])
        if not match:
            break

        start_pos = pos + match.start()
        brace_pos = pos + match.end() - 1  # Position of opening brace

        # Find matching closing brace
        brace_count = 1
        end_pos = brace_pos + 1

        while end_pos < len(result) and brace_count > 0:
            if result[end_pos] == '{':
                brace_count += 1
            elif result[end_pos] == '}':
                brace_count -= 1
            end_pos += 1

        if brace_count == 0:  # Found matching brace
            caption_content = result[start_pos:end_pos]
            if '\\index{' in caption_content:
                cleaned_caption = re.sub(r'\\index\{[^}]*\}', '', caption_content)
                result = result[:start_pos] + cleaned_caption + result[end_pos:]
                pos = start_pos + len(cleaned_caption)
            else:
                pos = end_pos
        else:
            pos += match.end()

    # Pattern 3: Handle caption= in table environments
    def clean_table_caption(match):
        caption_content = match.group(0)
        # Remove any \index{} commands from within the caption
        cleaned = re.sub(r'\\index\{[^}]*\}', '', caption_content)
        return cleaned

    result = re.sub(r'caption\s*=\s*\{[^{}]*\\index\{[^}]*\}[^{}]*\}', clean_table_caption, result)

    # Handle complex table captions
    table_caption_pattern = r'caption\s*=\s*\{'
    pos = 0
    while True:
        match = re.search(table_caption_pattern, result[pos:])
        if not match:
            break

        start_pos = pos + match.start()
        brace_pos = pos + match.end() - 1  # Position of opening brace

        # Find matching closing brace
        brace_count = 1
        end_pos = brace_pos + 1

        while end_pos < len(result) and brace_count > 0:
            if result[end_pos] == '{':
                brace_count += 1
            elif result[end_pos] == '}':
                brace_count -= 1
            end_pos += 1

        if brace_count == 0:  # Found matching brace
            caption_content = result[start_pos:end_pos]
            if '\\index{' in caption_content:
                cleaned_caption = re.sub(r'\\index\{[^}]*\}', '', caption_content)
                result = result[:start_pos] + cleaned_caption + result[end_pos:]
                pos = start_pos + len(cleaned_caption)
            else:
                pos = end_pos
        else:
            pos += match.end()

    return result

def process_file(filepath: str) -> Dict:
    """Process a single LaTeX file to remove index commands from labels and captions."""
    with open(filepath, 'r', encoding='utf-8') as f:
        original_content = f.read()

    # Count original problematic patterns
    original_label_indexes = len(re.findall(r'\\label\{[^{}]*\\index\{[^}]*\}[^{}]*\}', original_content))
    original_caption_indexes = len(re.findall(r'\\caption\{[^{}]*\\index\{[^}]*\}[^{}]*\}', original_content))
    original_table_caption_indexes = len(re.findall(r'caption\s*=\s*\{[^{}]*\\index\{[^}]*\}[^{}]*\}', original_content))
    original_total_indexes = len(re.findall(r'\\index\{[^}]*\}', original_content))

    # Clean the content
    cleaned_content = remove_index_from_labels_and_captions(original_content)

    # Count remaining
    final_label_indexes = len(re.findall(r'\\label\{[^{}]*\\index\{[^}]*\}[^{}]*\}', cleaned_content))
    final_caption_indexes = len(re.findall(r'\\caption\{[^{}]*\\index\{[^}]*\}[^{}]*\}', cleaned_content))
    final_table_caption_indexes = len(re.findall(r'caption\s*=\s*\{[^{}]*\\index\{[^}]*\}[^{}]*\}', cleaned_content))
    final_total_indexes = len(re.findall(r'\\index\{[^}]*\}', cleaned_content))

    # Write back if changes were made
    changes_made = cleaned_content != original_content
    if changes_made:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)

    stats = {
        'original_total_indexes': original_total_indexes,
        'final_total_indexes': final_total_indexes,
        'removed_from_labels': original_label_indexes - final_label_indexes,
        'removed_from_captions': original_caption_indexes - final_caption_indexes,
        'removed_from_table_captions': original_table_caption_indexes - final_table_caption_indexes,
        'total_removed': original_total_indexes - final_total_indexes,
        'changes_made': changes_made
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

    print("Removing \\index{} commands from \\label{} and \\caption{} commands")
    print("=" * 70)

    total_stats = {
        'files_processed': 0,
        'files_changed': 0,
        'total_indexes_removed': 0,
        'removed_from_labels': 0,
        'removed_from_captions': 0,
        'removed_from_table_captions': 0
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
                total_stats['removed_from_labels'] += stats['removed_from_labels']
                total_stats['removed_from_captions'] += stats['removed_from_captions']
                total_stats['removed_from_table_captions'] += stats['removed_from_table_captions']

                if stats['changes_made']:
                    print(f"  Removed {stats['total_removed']} index commands from labels/captions")
                    if stats['removed_from_labels'] > 0:
                        print(f"    - {stats['removed_from_labels']} from \\label{{}}")
                    if stats['removed_from_captions'] > 0:
                        print(f"    - {stats['removed_from_captions']} from \\caption{{}}")
                    if stats['removed_from_table_captions'] > 0:
                        print(f"    - {stats['removed_from_table_captions']} from table captions")
                else:
                    print(f"  No index commands found in labels or captions")

            except Exception as e:
                print(f"Error processing {filepath}: {e}")
        else:
            print(f"File not found: {filepath}")

    print(f"\nLabel/Caption Cleanup Summary:")
    print("=" * 70)
    print(f"Files processed: {total_stats['files_processed']}")
    print(f"Files changed: {total_stats['files_changed']}")
    print(f"Total index commands removed: {total_stats['total_indexes_removed']}")
    print(f"  - From \\label{{}}: {total_stats['removed_from_labels']}")
    print(f"  - From \\caption{{}}: {total_stats['removed_from_captions']}")
    print(f"  - From table captions: {total_stats['removed_from_table_captions']}")

if __name__ == "__main__":
    main()
