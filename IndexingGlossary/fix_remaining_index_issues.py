#!/usr/bin/env python3
"""
Fix Remaining Index Issues Script
Fixes malformed index entries with floating parentheses and other formatting issues
"""

import re
import os
from pathlib import Path

class IndexFixer:
    def __init__(self, chapters_dir: str = "Chapters"):
        self.chapters_dir = Path(chapters_dir)
        self.fixes_applied = 0

    def fix_floating_parentheses(self, content: str) -> str:
        """Fix index entries with floating parentheses"""
        fixes_made = 0

        # Pattern: \index{...}(text) should be \index{...} (text)
        pattern = r'\\index\{([^}]+)\}\(([^)]+)\)'
        matches = re.finditer(pattern, content)

        for match in matches:
            original = match.group(0)
            index_content = match.group(1)
            paren_content = match.group(2)
            replacement = f'\\index{{{index_content}}} ({paren_content})'
            content = content.replace(original, replacement)
            fixes_made += 1
            print(f"  Fixed: {original} → {replacement}")

        return content, fixes_made

    def fix_malformed_braces(self, content: str) -> str:
        """Fix various malformed brace patterns"""
        fixes_made = 0

        # Fix patterns like ") \index{...} (" back to normal
        pattern = r'\) \\index\{([^}]+)\} \('
        matches = re.finditer(pattern, content)

        for match in matches:
            original = match.group(0)
            index_content = match.group(1)
            replacement = f'\\index{{{index_content}}}('
            content = content.replace(original, replacement)
            fixes_made += 1
            print(f"  Fixed malformed: {original} → {replacement}")

        return content, fixes_made

    def fix_duplicate_index_markers(self, content: str) -> str:
        """Fix duplicate or malformed index markers"""
        fixes_made = 0

        # Fix patterns like \index{braille!braille} to \index{braille}
        pattern = r'\\index\{([^!}]+)!\1\}'
        matches = re.finditer(pattern, content)

        for match in matches:
            original = match.group(0)
            term = match.group(1)
            replacement = f'\\index{{{term}}}'
            content = content.replace(original, replacement)
            fixes_made += 1
            print(f"  Fixed duplicate: {original} → {replacement}")

        return content, fixes_made

    def fix_malformed_voiceover_index(self, content: str) -> str:
        """Fix specific VoiceOver index issues"""
        fixes_made = 0

        # Fix \index{VoiceOver!VoiceOver} patterns
        content = content.replace('\\index{VoiceOver!VoiceOver}', '\\index{screen reader!VoiceOver}')
        if '\\index{VoiceOver!VoiceOver}' in content:
            fixes_made += 1
            print("  Fixed VoiceOver index pattern")

        return content, fixes_made

    def fix_common_malformed_patterns(self, content: str) -> str:
        """Fix other common malformed patterns"""
        fixes_made = 0

        # Fix patterns with extra closing braces
        patterns = [
            (r'\\index\{([^}]+)\}\s*display\}\s*display\}', r'\\index{\1}'),
            (r'\\index\{([^}]+)\}\s*embosser\}\s*embosser\}', r'\\index{\1}'),
            (r'\\index\{([^}]+)\}\s*reader\}\s*reader\}', r'\\index{\1}'),
        ]

        for pattern, replacement in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                original = match.group(0)
                new_content = re.sub(pattern, replacement, original)
                content = content.replace(original, new_content)
                fixes_made += 1
                print(f"  Fixed pattern: {original} → {new_content}")

        return content, fixes_made

    def process_file(self, file_path: Path) -> bool:
        """Process a single LaTeX file"""
        print(f"\nProcessing {file_path.name}...")

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            original_content = content
            total_fixes = 0

            # Apply all fixes
            content, fixes = self.fix_floating_parentheses(content)
            total_fixes += fixes

            content, fixes = self.fix_malformed_braces(content)
            total_fixes += fixes

            content, fixes = self.fix_duplicate_index_markers(content)
            total_fixes += fixes

            content, fixes = self.fix_malformed_voiceover_index(content)
            total_fixes += fixes

            content, fixes = self.fix_common_malformed_patterns(content)
            total_fixes += fixes

            # Write back if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  Applied {total_fixes} fixes to {file_path.name}")
                self.fixes_applied += total_fixes
                return True
            else:
                print(f"  No fixes needed for {file_path.name}")
                return False

        except Exception as e:
            print(f"  Error processing {file_path}: {e}")
            return False

    def run(self):
        """Main execution method"""
        print("Starting index issue fixes...")

        # Get all .tex files
        tex_files = list(self.chapters_dir.glob("*.tex"))
        print(f"Found {len(tex_files)} LaTeX files")

        files_modified = 0

        for file_path in sorted(tex_files):
            if self.process_file(file_path):
                files_modified += 1

        print(f"\nFixes complete:")
        print(f"  Files processed: {len(tex_files)}")
        print(f"  Files modified: {files_modified}")
        print(f"  Total fixes applied: {self.fixes_applied}")

if __name__ == "__main__":
    fixer = IndexFixer()
    fixer.run()
