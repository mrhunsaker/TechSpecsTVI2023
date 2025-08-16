#!/usr/bin/env python3
"""
LaTeX Glossary Command Insertion Script
Inserts \gls{} commands into LaTeX files based on glossary terms
"""

import json
import re
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
import shutil

class GlossaryInserter:
    def __init__(self, glossary_file: str = "glossary_terms.json", chapters_dir: str = "Chapters"):
        self.glossary_file = glossary_file
        self.chapters_dir = Path(chapters_dir)
        self.glossary = {}
        self.term_mapping = {}  # Maps variant text to canonical key
        self.files_processed = set()

    def load_glossary(self):
        """Load glossary terms and create variant mapping"""
        with open(self.glossary_file, 'r', encoding='utf-8') as f:
            self.glossary = json.load(f)

        # Create mapping from all variants to canonical keys
        for key, data in self.glossary.items():
            for variant in data['variants']:
                # Clean variant (remove index hierarchy markers)
                clean_variant = variant.split('!')[0].strip()
                if clean_variant:
                    self.term_mapping[clean_variant.lower()] = key

        print(f"Loaded {len(self.glossary)} glossary terms with {len(self.term_mapping)} variants")

    def backup_file(self, file_path: Path) -> Path:
        """Create backup of original file"""
        backup_path = file_path.with_suffix(file_path.suffix + '.backup')
        shutil.copy2(file_path, backup_path)
        return backup_path

    def is_structural_command(self, line: str) -> bool:
        """Check if line contains structural LaTeX commands where \gls{} should not be inserted"""
        structural_patterns = [
            r'\\chapter\{',
            r'\\section\{',
            r'\\subsection\{',
            r'\\subsubsection\{',
            r'\\paragraph\{',
            r'\\subparagraph\{',
            r'\\part\{',
            r'\\title\{',
            r'\\author\{',
            r'\\date\{',
            r'\\caption\{',
            r'\\label\{',
            r'\\ref\{',
            r'\\cite\{',
            r'\\index\{',
            r'\\footnote\{',
            r'\\href\{',
            r'\\url\{',
            r'\\textbf\{',
            r'\\textit\{',
            r'\\emph\{',
            r'\\item\[',
        ]

        for pattern in structural_patterns:
            if re.search(pattern, line):
                return True
        return False

    def find_term_in_text(self, text: str, term: str) -> List[Tuple[int, int, str]]:
        """Find all occurrences of term in text, returning (start, end, matched_text)"""
        matches = []

        # Create regex pattern for the term (case insensitive, word boundaries)
        pattern = r'\b' + re.escape(term) + r'\b'

        for match in re.finditer(pattern, text, re.IGNORECASE):
            matches.append((match.start(), match.end(), match.group()))

        return matches

    def insert_gls_in_line(self, line: str, used_terms: Set[str]) -> Tuple[str, Set[str]]:
        """Insert \gls{} commands in a single line, avoiding structural commands"""

        # Skip if this is a structural command line
        if self.is_structural_command(line):
            return line, used_terms

        # Skip if line already contains \gls{} commands
        if r'\gls{' in line:
            return line, used_terms

        # Skip comment lines
        if line.strip().startswith('%'):
            return line, used_terms

        modified_line = line
        offset = 0  # Track position changes due to insertions
        line_used_terms = set()

        # Find all potential terms in this line, sorted by position
        all_matches = []
        for variant, key in self.term_mapping.items():
            matches = self.find_term_in_text(line, variant)
            for start, end, matched_text in matches:
                all_matches.append((start, end, matched_text, variant, key))

        # Sort by position (earliest first)
        all_matches.sort(key=lambda x: x[0])

        # Process matches, avoiding overlaps and limiting to first occurrence per file
        for start, end, matched_text, variant, key in all_matches:
            # Skip if we've already used this term in this file
            if key in used_terms:
                continue

            # Skip if this would overlap with a previous insertion
            adjusted_start = start + offset
            adjusted_end = end + offset

            # Check if this position is still valid after previous insertions
            if adjusted_start >= len(modified_line) or modified_line[adjusted_start:adjusted_end] != matched_text:
                continue

            # Insert \gls{} command
            gls_command = f"\\gls{{{key}}}"
            modified_line = modified_line[:adjusted_start] + gls_command + modified_line[adjusted_end:]

            # Update offset for future insertions
            offset += len(gls_command) - len(matched_text)

            # Mark this term as used
            line_used_terms.add(key)

            print(f"  Inserted \\gls{{{key}}} for '{matched_text}'")

        return modified_line, line_used_terms

    def process_file(self, file_path: Path) -> bool:
        """Process a single LaTeX file"""
        print(f"\nProcessing {file_path.name}...")

        # Create backup
        backup_path = self.backup_file(file_path)
        print(f"  Created backup: {backup_path.name}")

        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            # Track terms used in this file
            used_terms = set()
            modified_lines = []
            insertions_made = 0

            # Process each line
            for i, line in enumerate(lines):
                modified_line, line_used_terms = self.insert_gls_in_line(line, used_terms)
                modified_lines.append(modified_line)

                # Update used terms
                used_terms.update(line_used_terms)
                if line_used_terms:
                    insertions_made += len(line_used_terms)

            # Write modified file if changes were made
            if insertions_made > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(modified_lines)
                print(f"  Made {insertions_made} glossary insertions")
                return True
            else:
                print(f"  No glossary terms found to insert")
                # Remove backup if no changes made
                backup_path.unlink()
                return False

        except Exception as e:
            print(f"  Error processing {file_path}: {e}")
            # Restore from backup on error
            if backup_path.exists():
                shutil.copy2(backup_path, file_path)
            return False

    def create_preamble_file(self, output_file: str = "glossary_preamble.tex"):
        """Create a file with all \newglossaryentry commands for inclusion in preamble"""

        preamble_lines = [
            "% Glossary definitions for TechSpecsTVI project",
            "% Include this file in your main document preamble after \\usepackage{glossaries}",
            "% Use \\makeglossaries after including this file",
            "",
        ]

        # Add all glossary entries
        for key, data in sorted(self.glossary.items()):
            # Get the primary variant (first one without hierarchy markers)
            name = None
            for variant in data['variants']:
                if '!' not in variant:  # Skip hierarchical index entries
                    name = variant
                    break

            if not name:
                name = data['variants'][0].split('!')[0]  # Fallback to first part

            description = data['definition']

            # Escape LaTeX special characters
            name = self._escape_latex(name)
            description = self._escape_latex(description)

            entry = f"\\newglossaryentry{{{key}}}{{\n    name={{{name}}},\n    description={{{description}}}\n}}"
            preamble_lines.append(entry)
            preamble_lines.append("")

        # Write preamble file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(preamble_lines))

        print(f"Created glossary preamble file: {output_file}")

    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters"""
        replacements = {
            '&': '\\&',
            '%': '\\%',
            '$': '\\$',
            '#': '\\#',
            '^': '\\textasciicircum{}',
            '_': '\\_',
            '{': '\\{',
            '}': '\\}',
            '~': '\\textasciitilde{}'
        }

        for char, replacement in replacements.items():
            text = text.replace(char, replacement)

        return text

    def process_all_files(self, file_list: List[str] = None):
        """Process all specified LaTeX files"""

        if file_list is None:
            # Use default file list from task specification
            file_list = [
                "Introduction.tex", "Conclusion.tex",
                "Chapter01.tex", "Chapter02.tex", "Chapter03.tex", "Chapter04.tex",
                "Chapter05.tex", "Chapter06.tex", "Chapter07.tex", "Chapter08.tex",
                "Chapter09.tex", "Chapter10.tex", "Chapter11.tex", "Chapter12.tex",
                "Chapter13.tex", "Chapter14.tex", "Chapter15.tex", "Chapter16.tex",
                "Chapter17.tex", "Chapter18.tex", "Chapter19.tex", "Chapter20.tex",
                "Chapter21.tex", "Chapter22.tex", "Chapter23.tex", "Chapter24.tex",
                "Appendix00.tex", "Appendix01.tex", "Appendix02.tex", "Appendix03.tex",
                "Appendix04.tex", "Appendix05.tex", "Appendix06.tex"
            ]

        total_files = 0
        successful_files = 0

        for filename in file_list:
            file_path = self.chapters_dir / filename
            if file_path.exists():
                total_files += 1
                if self.process_file(file_path):
                    successful_files += 1
            else:
                print(f"Warning: File not found: {file_path}")

        print(f"\nProcessing complete:")
        print(f"  Total files processed: {total_files}")
        print(f"  Files with glossary insertions: {successful_files}")

    def run(self):
        """Main execution method"""
        print("Starting glossary command insertion...")

        # Load glossary
        self.load_glossary()

        # Create preamble file
        self.create_preamble_file()

        # Process all files
        self.process_all_files()

        print("\nGlossary insertion complete!")
        print("\nNext steps:")
        print("1. Include 'glossary_preamble.tex' in your main LaTeX document preamble")
        print("2. Add \\makeglossaries after including the preamble file")
        print("3. Add \\printglossaries where you want the glossary to appear")
        print("4. Compile with: pdflatex -> makeglossaries -> pdflatex -> pdflatex")

if __name__ == "__main__":
    inserter = GlossaryInserter()
    inserter.run()
