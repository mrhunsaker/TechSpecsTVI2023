#!/usr/bin/env python3
"""
LaTeX Index Processing Script for Steps 3 and 4
Inserts \\index{} commands based on normalized terms and removes redundant entries.
"""

import json
import re
import os
from typing import Dict, List, Tuple, Set
from collections import defaultdict

class LaTeXIndexProcessor:
    def __init__(self, index_terms_file: str):
        """Initialize with the normalized index terms JSON file."""
        self.index_terms = self._load_index_terms(index_terms_file)
        self.term_mappings = self._build_term_mappings()
        # Structural commands where \index{} should NOT be inserted
        self.structural_commands = {
            'part', 'chapter', 'section', 'subsection', 'subsubsection',
            'paragraph', 'subparagraph', 'title', 'author', 'date'
        }
        self.min_word_distance = 150  # Minimum words between same index terms

    def _load_index_terms(self, filename: str) -> Dict:
        """Load the normalized index terms from JSON."""
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _build_term_mappings(self) -> Dict[str, str]:
        """Build a mapping from all term variants to their canonical forms."""
        mappings = {}

        def extract_terms(data, canonical_key=""):
            """Recursively extract terms from nested structure."""
            if isinstance(data, dict):
                if 'terms' in data:
                    # Use the first term as canonical form
                    terms_list = data['terms']
                    if terms_list:
                        canon_form = terms_list[0]
                        if canonical_key:
                            # For nested terms, use parent!child format
                            canon_form = f"{canonical_key}!{canon_form}"

                        # Map all variants to canonical form
                        for term in terms_list:
                            # Case-insensitive mapping
                            mappings[term.lower()] = canon_form
                            mappings[term] = canon_form

                # Process nested entries
                for key, value in data.items():
                    if key != 'terms' and key != 'see also':
                        parent_key = canonical_key if canonical_key else key
                        if isinstance(value, dict):
                            if 'terms' in value:
                                # This is a sub-entry
                                extract_terms(value, parent_key)
                            else:
                                # This might be another level of nesting
                                extract_terms(value, f"{parent_key}!{key}" if parent_key != key else key)

        for main_key, data in self.index_terms.items():
            extract_terms(data, main_key)

        return mappings

    def _count_words_between_positions(self, text: str, pos1: int, pos2: int) -> int:
        """Count words between two positions in text."""
        start, end = min(pos1, pos2), max(pos1, pos2)
        segment = text[start:end]
        # Simple word count - split on whitespace and filter empty strings
        words = [w for w in segment.split() if w.strip()]
        return len(words)

    def _is_in_structural_command(self, text: str, position: int) -> bool:
        """Check if position is within a structural LaTeX command or label."""
        # Look backwards from position to find context
        search_start = max(0, position - 1000)
        segment = text[search_start:position + 200]
        relative_pos = position - search_start

        # Check if in a label
        label_pattern = r'\\label\s*\{[^}]*'
        for match in re.finditer(label_pattern, segment):
            if match.start() <= relative_pos <= match.end():
                return True

        # Check if in any LaTeX command argument
        cmd_pattern = r'\\[a-zA-Z]+\s*\{[^}]*'
        for match in re.finditer(cmd_pattern, segment):
            if match.start() <= relative_pos <= match.end():
                # Get the command name
                cmd_match = re.match(r'\\([a-zA-Z]+)', match.group())
                if cmd_match and cmd_match.group(1) in self.structural_commands:
                    return True

        # Check if inside any braced argument of structural commands
        struct_pattern = r'\\(' + '|'.join(self.structural_commands) + r')\s*\{'
        matches = list(re.finditer(struct_pattern, segment))

        for match in matches:
            cmd_start = match.start()
            brace_start = match.end() - 1  # Position of opening brace

            # Find matching closing brace
            brace_count = 0
            for i, char in enumerate(segment[brace_start:]):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        cmd_end = brace_start + i
                        if cmd_start <= relative_pos <= cmd_end:
                            return True
                        break
        return False

    def _insert_index_commands(self, text: str) -> str:
        """Insert \\index{} commands based on term mappings."""
        result = text
        insertions = []  # Track insertions for cleanup

        # Find plain text regions (not inside LaTeX commands, comments, or math)
        plain_text_regions = self._find_plain_text_regions(result)

        # Sort terms by length (longest first) to avoid partial matches
        sorted_terms = sorted(self.term_mappings.keys(), key=len, reverse=True)

        for term in sorted_terms:
            canonical = self.term_mappings[term]

            # Create regex pattern for the term (word boundaries)
            pattern = r'\b' + re.escape(term) + r'\b'

            matches = list(re.finditer(pattern, result, re.IGNORECASE))

            for match in reversed(matches):  # Process in reverse to maintain positions
                pos = match.start()
                end_pos = match.end()

                # Check if match is in a plain text region
                in_plain_text = any(start <= pos < end for start, end in plain_text_regions)
                if not in_plain_text:
                    continue

                # Skip if in structural command (additional check)
                if self._is_in_structural_command(result, pos):
                    continue

                # Skip if already has an index command nearby
                nearby_index = re.search(r'\\index\{[^}]*\}',
                                       result[max(0, pos-50):pos+len(term)+50])
                if nearby_index:
                    continue

                # Insert index command after the term
                index_cmd = f"\\index{{{canonical}}}"

                # Record this insertion for distance checking
                insertions.append({
                    'position': end_pos,
                    'term': canonical,
                    'length': len(index_cmd)
                })

                result = result[:end_pos] + index_cmd + result[end_pos:]

        return result

    def _find_plain_text_regions(self, text: str) -> List[Tuple[int, int]]:
        """Find regions of plain text where index commands can be safely inserted."""
        regions = []
        i = 0
        while i < len(text):
            # Skip LaTeX commands
            if text[i] == '\\':
                # Find end of command
                i += 1
                while i < len(text) and text[i].isalpha():
                    i += 1
                # Skip any following whitespace and braced arguments
                while i < len(text) and text[i].isspace():
                    i += 1
                if i < len(text) and text[i] == '{':
                    brace_count = 1
                    i += 1
                    while i < len(text) and brace_count > 0:
                        if text[i] == '{':
                            brace_count += 1
                        elif text[i] == '}':
                            brace_count -= 1
                        i += 1
                continue

            # Skip comments
            if text[i] == '%':
                while i < len(text) and text[i] != '\n':
                    i += 1
                continue

            # Skip math environments
            if i < len(text) - 1 and text[i:i+2] in ['$$', '\\[']:
                delimiter = '$$' if text[i:i+2] == '$$' else '\\]'
                i += 2
                while i < len(text) - len(delimiter) + 1:
                    if text[i:i+len(delimiter)] == delimiter:
                        i += len(delimiter)
                        break
                    i += 1
                continue

            if text[i] == '$':
                i += 1
                while i < len(text) and text[i] != '$':
                    i += 1
                if i < len(text):
                    i += 1
                continue

            # This is plain text - find the end
            start = i
            while i < len(text) and text[i] not in ['\\', '%', '$']:
                # Check for math environment start
                if i < len(text) - 1 and text[i:i+2] == '\\[':
                    break
                if i < len(text) - 1 and text[i:i+2] == '$$':
                    break
                i += 1

            if i > start:
                regions.append((start, i))

        return regions

    def _cleanup_redundant_indexes(self, text: str) -> str:
        """Remove redundant \\index{} commands that are too close together."""
        # Find all index commands
        index_pattern = r'\\index\{([^}]*)\}'
        matches = list(re.finditer(index_pattern, text))

        # Group by term
        term_positions = defaultdict(list)
        for match in matches:
            term = match.group(1)
            term_positions[term].append({
                'match': match,
                'position': match.start(),
                'end': match.end()
            })

        # Find indexes to remove
        to_remove = []
        for term, positions in term_positions.items():
            if len(positions) < 2:
                continue

            # Sort by position
            positions.sort(key=lambda x: x['position'])

            # Keep first occurrence, check distances for others
            kept_positions = [positions[0]]

            for i in range(1, len(positions)):
                current_pos = positions[i]['position']

                # Check distance from all kept positions
                too_close = False
                for kept in kept_positions:
                    word_distance = self._count_words_between_positions(
                        text, kept['position'], current_pos
                    )
                    if word_distance < self.min_word_distance:
                        too_close = True
                        break

                if too_close:
                    to_remove.append(positions[i])
                else:
                    kept_positions.append(positions[i])

        # Remove redundant indexes (in reverse order to maintain positions)
        to_remove.sort(key=lambda x: x['position'], reverse=True)
        result = text

        for item in to_remove:
            start, end = item['match'].span()
            result = result[:start] + result[end:]

        return result

    def process_file(self, filepath: str) -> Tuple[str, Dict]:
        """Process a single LaTeX file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # Step 3: Insert index commands
        content_with_indexes = self._insert_index_commands(original_content)

        # Step 4: Cleanup redundant commands
        final_content = self._cleanup_redundant_indexes(content_with_indexes)

        # Count changes
        original_indexes = len(re.findall(r'\\index\{[^}]*\}', original_content))
        inserted_indexes = len(re.findall(r'\\index\{[^}]*\}', content_with_indexes))
        final_indexes = len(re.findall(r'\\index\{[^}]*\}', final_content))

        stats = {
            'original_indexes': original_indexes,
            'inserted_indexes': inserted_indexes,
            'final_indexes': final_indexes,
            'net_added': final_indexes - original_indexes,
            'removed_redundant': inserted_indexes - final_indexes
        }

        return final_content, stats

    def process_all_files(self, file_list: List[str]) -> Dict:
        """Process all LaTeX files and return comprehensive stats."""
        all_stats = {}
        total_stats = {
            'files_processed': 0,
            'total_indexes_added': 0,
            'total_redundant_removed': 0
        }

        for filepath in file_list:
            if os.path.exists(filepath):
                print(f"Processing {filepath}...")
                try:
                    new_content, stats = self.process_file(filepath)

                    # Write back to file
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)

                    all_stats[filepath] = stats
                    total_stats['files_processed'] += 1
                    total_stats['total_indexes_added'] += stats['net_added']
                    total_stats['total_redundant_removed'] += stats['removed_redundant']

                    print(f"  Added {stats['net_added']} index commands, "
                          f"removed {stats['removed_redundant']} redundant")

                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
                    all_stats[filepath] = {'error': str(e)}
            else:
                print(f"File not found: {filepath}")
                all_stats[filepath] = {'error': 'File not found'}

        all_stats['_totals'] = total_stats
        return all_stats

def main():
    """Main execution function."""
    # File paths
    index_terms_file = "index_terms.json"

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

    # Initialize processor
    if not os.path.exists(index_terms_file):
        print(f"Error: {index_terms_file} not found!")
        return

    processor = LaTeXIndexProcessor(index_terms_file)

    print("Starting LaTeX Index Processing (Steps 3 & 4)")
    print("=" * 50)
    print(f"Loaded {len(processor.term_mappings)} term mappings")
    print(f"Minimum word distance: {processor.min_word_distance}")
    print()

    # Process all files
    results = processor.process_all_files(latex_files)

    # Print summary
    print("\nProcessing Summary:")
    print("=" * 50)
    totals = results.get('_totals', {})
    print(f"Files processed: {totals.get('files_processed', 0)}")
    print(f"Total index commands added: {totals.get('total_indexes_added', 0)}")
    print(f"Total redundant commands removed: {totals.get('total_redundant_removed', 0)}")

    # Save detailed results
    with open('indexing_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print("\nDetailed results saved to indexing_results.json")

if __name__ == "__main__":
    main()
