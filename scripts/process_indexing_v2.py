#!/usr/bin/env python3
"""
LaTeX Index Processing Script v2 - Steps 3 and 4
Safely inserts \\index{} commands based on normalized terms and removes redundant entries.
Avoids placement within LaTeX structural commands, labels, and other problematic locations.
"""

import json
import re
import os
from typing import Dict, List, Tuple, Set
from collections import defaultdict

class SafeLaTeXIndexProcessor:
    def __init__(self, index_terms_file: str):
        """Initialize with the normalized index terms JSON file."""
        self.index_terms = self._load_index_terms(index_terms_file)
        self.term_mappings = self._build_term_mappings()
        self.min_word_distance = 150  # Minimum words between same index terms

        # Patterns for areas where index commands should NOT be placed
        self.forbidden_patterns = [
            r'\\chapter\s*\{[^}]*\}',
            r'\\section\s*\{[^}]*\}',
            r'\\subsection\s*\{[^}]*\}',
            r'\\subsubsection\s*\{[^}]*\}',
            r'\\paragraph\s*\{[^}]*\}',
            r'\\subparagraph\s*\{[^}]*\}',
            r'\\part\s*\{[^}]*\}',
            r'\\title\s*\{[^}]*\}',
            r'\\author\s*\{[^}]*\}',
            r'\\label\s*\{[^}]*\}',
            r'\\ref\s*\{[^}]*\}',
            r'\\cite[a-z]*\s*\{[^}]*\}',
            r'\\hypertarget\s*\{[^}]*\}',
            r'\\href\s*\{[^}]*\}',
            r'\\url\s*\{[^}]*\}',
            r'\\textbf\s*\{[^}]*\}',
            r'\\textit\s*\{[^}]*\}',
            r'\\emph\s*\{[^}]*\}',
            r'\\begin\s*\{[^}]*\}',
            r'\\end\s*\{[^}]*\}',
            r'\$[^$]*\$',  # Inline math
            r'\$\$[^$]*\$\$',  # Display math
            r'\\[.*?\\]',  # Display math
            r'%.*$',  # Comments
        ]

    def _load_index_terms(self, filename: str) -> Dict:
        """Load the normalized index terms from JSON."""
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _build_term_mappings(self) -> Dict[str, str]:
        """Build a mapping from all term variants to their canonical forms."""
        mappings = {}

        def extract_terms(data, parent_key=""):
            """Recursively extract terms from nested structure."""
            if isinstance(data, dict):
                if 'terms' in data and data['terms']:
                    # Use the first term as canonical form
                    canon_form = data['terms'][0]

                    # For nested terms, create subentry format
                    if parent_key and canon_form.lower() != parent_key.lower():
                        canon_form = f"{parent_key}!{canon_form}"

                    # Map all variants to canonical form
                    for term in data['terms']:
                        if term.strip():  # Only non-empty terms
                            mappings[term.lower()] = canon_form
                            mappings[term] = canon_form

                # Process nested entries
                for key, value in data.items():
                    if key not in ['terms', 'see also'] and isinstance(value, dict):
                        new_parent = parent_key if parent_key else key
                        extract_terms(value, new_parent)

        for main_key, data in self.index_terms.items():
            extract_terms(data, main_key)

        return mappings

    def _find_forbidden_regions(self, text: str) -> List[Tuple[int, int]]:
        """Find all regions where index commands should not be inserted."""
        forbidden_regions = []

        for pattern in self.forbidden_patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                forbidden_regions.append((match.start(), match.end()))

        # Sort and merge overlapping regions
        forbidden_regions.sort()
        merged_regions = []

        for start, end in forbidden_regions:
            if merged_regions and start <= merged_regions[-1][1]:
                # Overlapping region, merge
                merged_regions[-1] = (merged_regions[-1][0], max(merged_regions[-1][1], end))
            else:
                merged_regions.append((start, end))

        return merged_regions

    def _is_safe_position(self, text: str, position: int, forbidden_regions: List[Tuple[int, int]]) -> bool:
        """Check if position is safe for index insertion."""
        # Check against forbidden regions
        for start, end in forbidden_regions:
            if start <= position <= end:
                return False

        # Additional safety checks
        # Check if we're inside braces of any command
        before_pos = max(0, position - 100)
        after_pos = min(len(text), position + 100)
        context = text[before_pos:after_pos]
        rel_pos = position - before_pos

        # Look for unmatched opening braces before position
        brace_count = 0
        backslash_found = False

        for i in range(rel_pos - 1, -1, -1):
            if context[i] == '}':
                brace_count += 1
            elif context[i] == '{':
                brace_count -= 1
                if brace_count < 0:
                    # We have an unmatched opening brace
                    # Check if there's a backslash before it (LaTeX command)
                    for j in range(i - 1, max(0, i - 20), -1):
                        if context[j] == '\\' and context[j+1:i].replace(' ', '').replace('\n', '').replace('\t', '').isalpha():
                            return False
                        elif not context[j].isspace():
                            break
                    break

        return True

    def _count_words_between_positions(self, text: str, pos1: int, pos2: int) -> int:
        """Count words between two positions in text."""
        start, end = min(pos1, pos2), max(pos1, pos2)
        segment = text[start:end]
        # Remove LaTeX commands and count words
        clean_segment = re.sub(r'\\[a-zA-Z]+\s*\{[^}]*\}', '', segment)
        clean_segment = re.sub(r'\\[a-zA-Z]+', '', clean_segment)
        words = [w for w in clean_segment.split() if w.strip() and not w.startswith('\\')]
        return len(words)

    def _insert_index_commands(self, text: str) -> str:
        """Insert \\index{} commands based on term mappings."""
        result = text

        # Find forbidden regions first
        forbidden_regions = self._find_forbidden_regions(result)

        # Sort terms by length (longest first) to avoid partial matches
        sorted_terms = sorted(self.term_mappings.keys(), key=len, reverse=True)

        insertions = []  # Track what we insert for distance checking

        for term in sorted_terms:
            if len(term.strip()) < 3:  # Skip very short terms
                continue

            canonical = self.term_mappings[term]

            # Create regex pattern for whole word matching
            pattern = r'\b' + re.escape(term) + r'\b'

            matches = list(re.finditer(pattern, result, re.IGNORECASE))

            for match in reversed(matches):  # Process in reverse to maintain positions
                pos = match.start()
                end_pos = match.end()

                # Check if position is safe
                if not self._is_safe_position(result, pos, forbidden_regions):
                    continue

                # Check if there's already an index command nearby
                nearby_start = max(0, end_pos - 50)
                nearby_end = min(len(result), end_pos + 50)
                nearby_text = result[nearby_start:nearby_end]

                if '\\index{' in nearby_text:
                    continue

                # Insert index command after the term
                index_cmd = f"\\index{{{canonical}}}"

                # Track insertion
                insertions.append({
                    'position': end_pos,
                    'term': canonical,
                    'original_length': len(index_cmd)
                })

                result = result[:end_pos] + index_cmd + result[end_pos:]

                # Update forbidden regions for subsequent insertions
                offset = len(index_cmd)
                forbidden_regions = [(start + offset if start >= end_pos else start,
                                    end + offset if end >= end_pos else end)
                                   for start, end in forbidden_regions]

        return result

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

    def _remove_existing_malformed_indexes(self, text: str) -> str:
        """Remove existing malformed index commands."""
        # Remove index commands that appear in labels or other problematic places
        patterns_to_clean = [
            r'\\label\{[^}]*\\index\{[^}]*\}[^}]*\}',
            r'\\index\{[^}]*\\index\{[^}]*\}[^}]*\}',  # Nested indexes
            r'\\index\{[^}]*![^}]*![^}]*\}',  # Triple-nested indexes
        ]

        result = text
        for pattern in patterns_to_clean:
            # For labels, remove just the index part
            if 'label' in pattern:
                def replace_label(match):
                    label_content = match.group(0)
                    # Remove index commands from within label
                    cleaned = re.sub(r'\\index\{[^}]*\}', '', label_content)
                    return cleaned
                result = re.sub(pattern, replace_label, result)
            else:
                # For other malformed indexes, try to fix them
                result = re.sub(pattern, '', result)

        return result

    def process_file(self, filepath: str) -> Tuple[str, Dict]:
        """Process a single LaTeX file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # First, clean up any existing malformed indexes
        cleaned_content = self._remove_existing_malformed_indexes(original_content)

        # Step 3: Insert index commands
        content_with_indexes = self._insert_index_commands(cleaned_content)

        # Step 4: Cleanup redundant commands
        final_content = self._cleanup_redundant_indexes(content_with_indexes)

        # Count changes
        original_indexes = len(re.findall(r'\\index\{[^}]*\}', original_content))
        cleaned_indexes = len(re.findall(r'\\index\{[^}]*\}', cleaned_content))
        inserted_indexes = len(re.findall(r'\\index\{[^}]*\}', content_with_indexes))
        final_indexes = len(re.findall(r'\\index\{[^}]*\}', final_content))

        stats = {
            'original_indexes': original_indexes,
            'cleaned_indexes': cleaned_indexes,
            'inserted_indexes': inserted_indexes,
            'final_indexes': final_indexes,
            'net_added': final_indexes - original_indexes,
            'removed_malformed': original_indexes - cleaned_indexes,
            'removed_redundant': inserted_indexes - final_indexes
        }

        return final_content, stats

    def process_all_files(self, file_list: List[str]) -> Dict:
        """Process all LaTeX files and return comprehensive stats."""
        all_stats = {}
        total_stats = {
            'files_processed': 0,
            'total_indexes_added': 0,
            'total_malformed_removed': 0,
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
                    total_stats['total_malformed_removed'] += stats['removed_malformed']
                    total_stats['total_redundant_removed'] += stats['removed_redundant']

                    print(f"  Net added: {stats['net_added']} index commands")
                    print(f"  Removed malformed: {stats['removed_malformed']}")
                    print(f"  Removed redundant: {stats['removed_redundant']}")

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

    processor = SafeLaTeXIndexProcessor(index_terms_file)

    print("Starting Safe LaTeX Index Processing v2 (Steps 3 & 4)")
    print("=" * 60)
    print(f"Loaded {len(processor.term_mappings)} term mappings")
    print(f"Minimum word distance: {processor.min_word_distance}")
    print()

    # Process all files
    results = processor.process_all_files(latex_files)

    # Print summary
    print("\nProcessing Summary:")
    print("=" * 60)
    totals = results.get('_totals', {})
    print(f"Files processed: {totals.get('files_processed', 0)}")
    print(f"Total net index commands added: {totals.get('total_indexes_added', 0)}")
    print(f"Total malformed commands removed: {totals.get('total_malformed_removed', 0)}")
    print(f"Total redundant commands removed: {totals.get('total_redundant_removed', 0)}")

    # Save detailed results
    with open('indexing_results_v2.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed results saved to indexing_results_v2.json")

if __name__ == "__main__":
    main()
