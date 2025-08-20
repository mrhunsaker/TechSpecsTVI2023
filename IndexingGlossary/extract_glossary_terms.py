#!/usr/bin/env python3
"""
Glossary Term Extraction Script for LaTeX Project
Extracts terms from \index{} entries and content analysis
"""

import re
import json
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

class GlossaryExtractor:
    def __init__(self, chapters_dir: str = "Chapters"):
        self.chapters_dir = Path(chapters_dir)
        self.existing_glossary = {}
        self.index_terms = defaultdict(set)
        self.content_terms = defaultdict(set)
        self.definitions = {}

    def load_existing_glossary(self, glossary_file: str = "glossary_terms.json"):
        """Load existing glossary terms if file exists"""
        if os.path.exists(glossary_file):
            with open(glossary_file, 'r', encoding='utf-8') as f:
                self.existing_glossary = json.load(f)
                print(f"Loaded {len(self.existing_glossary)} existing terms")

    def extract_index_terms(self, content: str) -> List[str]:
        """Extract all \index{} entries from LaTeX content"""
        pattern = r'\\index\{([^}]+)\}'
        matches = re.findall(pattern, content)
        return matches

    def normalize_term_key(self, term: str) -> str:
        """Create normalized key for glossary term"""
        # Handle hierarchical index entries like "screen reader!JAWS"
        if '!' in term:
            term = term.split('!')[0]  # Use main term

        # Normalize to lowercase, alphanumeric only
        normalized = re.sub(r'[^a-zA-Z0-9\s]', '', term.lower())
        normalized = re.sub(r'\s+', '', normalized)  # Remove spaces
        return normalized

    def extract_content_terms(self, content: str) -> Set[str]:
        """Extract potential glossary terms from content"""
        # Common technical terms that should be in glossary
        technical_patterns = [
            r'\b(?:API|SDK|IDE|GUI|CLI|USB|HDMI|WiFi|Bluetooth)\b',
            r'\b(?:artificial intelligence|machine learning|neural network)\b',
            r'\b(?:accessibility|inclusive design|universal design)\b',
            r'\b(?:screen reader|voice over|narrator|JAWS|NVDA)\b',
            r'\b(?:braille|tactile|haptic|audio)\b',
            r'\b(?:magnification|zoom|enlargement)\b',
            r'\b(?:navigation|orientation|mobility)\b',
            r'\b(?:OCR|optical character recognition)\b',
            r'\b(?:TTS|text-to-speech|speech synthesis)\b',
            r'\b(?:PDF|HTML|XML|LaTeX|MathML)\b',
            r'\b(?:WCAG|Section 508|ADA)\b'
        ]

        terms = set()
        for pattern in technical_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            terms.update(match.lower() for match in matches)

        return terms

    def infer_definition(self, term: str, contexts: List[str]) -> str:
        """Infer definition from context around term usage"""
        # Simple definition inference based on common patterns
        definitions = {
            'ocr': 'Optical Character Recognition - technology that converts images of text into machine-readable text',
            'screenreader': 'Software that reads screen content aloud for users with visual impairments',
            'jaws': 'Job Access With Speech - a popular screen reader software',
            'nvda': 'NonVisual Desktop Access - a free, open-source screen reader',
            'voiceover': 'Apple\'s built-in screen reader for macOS and iOS devices',
            'braille': 'A tactile writing system used by people who are blind or visually impaired',
            'brailledisplay': 'A tactile electronic device that displays braille characters',
            'ram': 'Random Access Memory - computer memory used for temporary data storage',
            'cpu': 'Central Processing Unit - the main processor of a computer',
            'assistivetechnology': 'Technology designed to help people with disabilities',
            'accessibility': 'The design of products, devices, services, or environments for people with disabilities',
            'pdf': 'Portable Document Format - a file format for presenting documents',
            'latex': 'A document preparation system for high-quality typesetting',
            'mathml': 'Mathematical Markup Language - a markup language for mathematical notation',
            'wcag': 'Web Content Accessibility Guidelines - international standards for web accessibility',
            'daisy': 'Digital Accessible Information System - a format for accessible digital books',
            'stem': 'Science, Technology, Engineering, and Mathematics education',
            'gps': 'Global Positioning System - satellite-based navigation system',
            'tts': 'Text-to-Speech - technology that converts text into spoken audio',
            'ai': 'Artificial Intelligence - computer systems that can perform tasks requiring human intelligence',
            'api': 'Application Programming Interface - a set of protocols for building software',
            'gui': 'Graphical User Interface - visual interface for interacting with software',
            'html': 'HyperText Markup Language - standard markup language for web pages',
            'xml': 'eXtensible Markup Language - markup language for encoding documents',
            'usb': 'Universal Serial Bus - standard for connecting devices to computers',
            'bluetooth': 'Wireless communication technology for short-range connections',
            'wifi': 'Wireless Fidelity - wireless networking technology',
            'sdk': 'Software Development Kit - collection of software development tools',
            'ide': 'Integrated Development Environment - software for writing code',
            'cli': 'Command Line Interface - text-based interface for operating systems'
        }

        return definitions.get(term, f"A technical term related to assistive technology and accessibility")

    def process_file(self, file_path: Path) -> None:
        """Process a single LaTeX file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Extract index terms
            index_terms = self.extract_index_terms(content)
            for term in index_terms:
                key = self.normalize_term_key(term)
                self.index_terms[key].add(term)

            # Extract content terms
            content_terms = self.extract_content_terms(content)
            for term in content_terms:
                key = self.normalize_term_key(term)
                self.content_terms[key].add(term)

            print(f"Processed {file_path.name}: {len(index_terms)} index terms, {len(content_terms)} content terms")

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    def process_all_files(self) -> None:
        """Process all LaTeX files in the chapters directory"""
        tex_files = list(self.chapters_dir.glob("*.tex"))
        print(f"Found {len(tex_files)} LaTeX files")

        for file_path in tex_files:
            self.process_file(file_path)

    def build_glossary(self) -> Dict:
        """Build comprehensive glossary from extracted terms"""
        glossary = {}

        # Start with existing glossary
        glossary.update(self.existing_glossary)

        # Process index terms
        all_terms = set(self.index_terms.keys()) | set(self.content_terms.keys())

        for key in all_terms:
            if key in glossary:
                # Merge variants
                existing_variants = set(glossary[key].get('variants', []))
                new_variants = self.index_terms[key] | self.content_terms[key]
                glossary[key]['variants'] = sorted(list(existing_variants | new_variants))
            else:
                # Create new entry
                variants = sorted(list(self.index_terms[key] | self.content_terms[key]))
                definition = self.infer_definition(key, [])

                glossary[key] = {
                    'variants': variants,
                    'definition': definition
                }

        return glossary

    def save_glossary(self, glossary: Dict, output_file: str = "glossary_terms.json") -> None:
        """Save glossary to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(glossary, f, indent=2, ensure_ascii=False, sort_keys=True)
        print(f"Saved {len(glossary)} terms to {output_file}")

    def generate_latex_definitions(self, glossary: Dict) -> str:
        """Generate LaTeX \newglossaryentry commands"""
        latex_entries = []

        for key, data in sorted(glossary.items()):
            # Get the primary variant (usually the first one)
            name = data['variants'][0] if data['variants'] else key
            description = data['definition']

            # Escape LaTeX special characters
            name = name.replace('&', '\\&').replace('%', '\\%').replace('$', '\\$')
            description = description.replace('&', '\\&').replace('%', '\\%').replace('$', '\\$')

            entry = f"\\newglossaryentry{{{key}}}{{\n    name={{{name}}},\n    description={{{description}}}\n}}"
            latex_entries.append(entry)

        return '\n\n'.join(latex_entries)

    def run(self) -> None:
        """Main execution method"""
        print("Starting glossary extraction...")

        # Load existing glossary
        self.load_existing_glossary()

        # Process all files
        self.process_all_files()

        # Build comprehensive glossary
        glossary = self.build_glossary()

        # Save results
        self.save_glossary(glossary)

        # Generate LaTeX definitions
        latex_defs = self.generate_latex_definitions(glossary)
        with open('glossary_definitions.tex', 'w', encoding='utf-8') as f:
            f.write("% Generated glossary definitions\n")
            f.write("% Include this file in your LaTeX preamble\n\n")
            f.write(latex_defs)

        print(f"Generated LaTeX definitions in glossary_definitions.tex")
        print(f"Total terms: {len(glossary)}")

        # Print summary
        print("\nTop 20 terms by variant count:")
        term_counts = [(key, len(data['variants'])) for key, data in glossary.items()]
        term_counts.sort(key=lambda x: x[1], reverse=True)
        for key, count in term_counts[:20]:
            print(f"  {key}: {count} variants")

if __name__ == "__main__":
    extractor = GlossaryExtractor()
    extractor.run()
