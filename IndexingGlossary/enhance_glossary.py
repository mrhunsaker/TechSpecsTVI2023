#!/usr/bin/env python3
"""
Enhanced Glossary Definition Script
Improves glossary definitions with domain-specific knowledge for assistive technology
"""

import json
import re
from typing import Dict, Any

class GlossaryEnhancer:
    def __init__(self):
        self.enhanced_definitions = {
            # Assistive Technology Hardware
            "3dprinter": "A device that creates three-dimensional objects from digital files, used in assistive technology to create tactile models and adaptive devices",
            "3dprinting": "The process of creating three-dimensional objects from digital files, widely used in assistive technology for creating tactile learning materials",
            "brailledisplay": "A tactile electronic device that displays braille characters by raising and lowering pins, allowing blind users to read screen content",
            "brailleembosser": "A printer that creates braille text on paper by embossing raised dots, essential for producing hard-copy braille materials",
            "laptop": "A portable computer that, when properly configured, serves as the primary computing platform for students using assistive technology",
            "tablet": "A portable touchscreen computing device that offers accessible interfaces and specialized apps for users with visual impairments",
            "videomagnifier": "A device that uses a camera and display to magnify text and objects for users with low vision",

            # Software and Screen Readers
            "screenreader": "Software that reads screen content aloud and provides keyboard navigation for users who are blind or have low vision",
            "jaws": "Job Access With Speech - a commercial screen reader software developed by Freedom Scientific",
            "nvda": "NonVisual Desktop Access - a free, open-source screen reader for Windows",
            "voiceover": "Apple's built-in screen reader software for macOS, iOS, and iPadOS devices",
            "narrator": "Microsoft's built-in screen reader for Windows operating systems",
            "talkback": "Google's built-in screen reader for Android devices",
            "dolphinscreenreader": "A screen reader software developed by Dolphin Computer Access",

            # Technical Concepts
            "accessibility": "The design of products, devices, services, or environments to be usable by people with disabilities",
            "assistivetechnology": "Any item, piece of equipment, or system used to increase, maintain, or improve functional capabilities of individuals with disabilities",
            "ocr": "Optical Character Recognition - technology that converts images of text into machine-readable and screen reader accessible text",
            "tts": "Text-to-Speech - technology that converts written text into spoken audio output",
            "ai": "Artificial Intelligence - computer systems that perform tasks typically requiring human intelligence, increasingly used in accessibility applications",
            "ram": "Random Access Memory - computer memory that significantly impacts screen reader performance and responsiveness",
            "cpu": "Central Processing Unit - the main processor of a computer, critical for smooth assistive technology operation",
            "latency": "The delay between user input and system response, particularly critical for screen reader users who rely on immediate audio feedback",

            # File Formats and Standards
            "pdf": "Portable Document Format - a file format that can be made accessible through proper tagging and structure",
            "pdfua": "PDF/UA (Universal Accessibility) - an ISO standard for accessible PDF documents",
            "mathml": "Mathematical Markup Language - a markup language for describing mathematical notation in a screen reader accessible way",
            "latex": "A document preparation system used for high-quality typesetting, particularly useful for mathematical and scientific documents",
            "daisy": "Digital Accessible Information System - a standard for creating accessible digital talking books",
            "html": "HyperText Markup Language - the standard markup language for creating accessible web pages",
            "wcag": "Web Content Accessibility Guidelines - international standards for making web content accessible to people with disabilities",
            "aria": "Accessible Rich Internet Applications - a set of attributes that make web content more accessible to screen readers",

            # Educational and Legal
            "educationalequity": "The principle that all students, including those with disabilities, should have equal access to educational opportunities and resources",
            "stem": "Science, Technology, Engineering, and Mathematics - educational disciplines that require specialized accessibility considerations",
            "nimas": "National Instructional Materials Accessibility Standard - a US standard for creating accessible instructional materials",
            "ada": "Americans with Disabilities Act - US civil rights law prohibiting discrimination based on disability",
            "section508": "A US law requiring federal agencies to make electronic and information technology accessible",

            # Braille and Tactile
            "braille": "A tactile writing system using raised dots that allows people who are blind to read and write through touch",
            "ueb": "Unified English Braille - the standard braille code for English-speaking countries",
            "nemethcode": "A braille code used for mathematical and scientific notation",
            "bana": "Braille Authority of North America - organization that promotes braille literacy and standardization",
            "tactilegraphics": "Raised images and diagrams that can be read through touch, providing visual information to users who are blind",
            "brailleliteracy": "The ability to read and write braille, essential for academic success of blind students",

            # Navigation and Mobility
            "gps": "Global Positioning System - satellite-based navigation technology adapted for use by people with visual impairments",
            "indoornavigation": "Technology systems that provide navigation assistance inside buildings where GPS is not available",
            "situationalawareness": "The perception and understanding of one's environment, supported by assistive technology for users with visual impairments",

            # Operating Systems
            "operatingsystem": "System software that manages computer hardware and provides services for applications, with built-in accessibility features",
            "windows": "Microsoft's operating system with built-in accessibility features including Narrator screen reader",
            "macos": "Apple's operating system with comprehensive accessibility features including VoiceOver",
            "ios": "Apple's mobile operating system with built-in accessibility features",
            "android": "Google's mobile operating system with TalkBack screen reader and accessibility services",
            "chromeos": "Google's operating system with built-in accessibility features for web-based computing",
            "linux": "Open-source operating system with various screen reader options including Orca",

            # Communication and Feedback
            "auditoryfeedback": "Sound-based responses that provide information about system status and user actions",
            "hapticfeedback": "Touch-based feedback through vibration or force, providing non-visual information to users",
            "sonification": "The use of sound to convey information, particularly useful for representing data to users who are blind",

            # Assessment and Frameworks
            "settframework": "Student, Environment, Tasks, and Tools - a framework for assistive technology assessment and selection",
            "cognitiveload": "The amount of mental effort required to complete a task, which can be increased by poorly designed interfaces",

            # Document and Content Creation
            "markdown": "A lightweight markup language that can be easily converted to accessible formats including braille",
            "documentstructure": "The organization and markup of documents to ensure they are navigable by assistive technology",
            "alternativetext": "Text descriptions of images that provide the same information to screen reader users",
            "taggedpdf": "PDF documents with structural markup that makes them accessible to screen readers",

            # Testing and Quality Assurance
            "accessibilitytesting": "The process of evaluating digital content and applications for accessibility compliance",
            "manualtesting": "Human evaluation of accessibility, often performed using assistive technology",
            "screenreaderuser": "A person who uses screen reading software to access digital content",

            # Hardware Specifications
            "refreshablebraille": "Electronic devices that display braille characters through movable pins, updated in real-time",
            "braillenotetaker": "Portable devices combining braille display, keyboard, and computing functions for note-taking and productivity",
            "magnification": "Technology that enlarges visual content for users with low vision",

            # Visual Impairments
            "visualimpairment": "A condition affecting vision that requires adaptive techniques or assistive technology for accessing information",
            "lowvision": "A visual impairment that cannot be fully corrected with glasses, contact lenses, or surgery",
            "cvi": "Cortical Visual Impairment - a visual impairment caused by damage to the visual pathways in the brain",

            # Independence and Daily Living
            "independence": "The ability to perform tasks and make decisions without assistance, supported by appropriate assistive technology",
            "dailylivingaids": "Assistive devices that help people with disabilities perform everyday tasks independently",
            "independentlivingskills": "Abilities needed to live independently, often supported by assistive technology",

            # File and Data Management
            "fileformats": "Different ways of encoding and storing digital information, with varying levels of accessibility",
            "characterencoding": "The way text characters are represented in digital files, affecting screen reader compatibility",
            "datavisualization": "The presentation of data in visual formats, requiring alternative accessible representations",

            # Fonts and Typography
            "fonts": "Typeface designs that affect readability for users with visual impairments",
            "accessiblefonts": "Typefaces designed or selected for optimal readability by users with visual impairments",
            "typography": "The art and technique of arranging type to make written language legible and appealing",

            # Web and Digital Accessibility
            "webaccessibility": "The practice of making websites usable by people with disabilities",
            "digitalaccessibility": "The design of digital technology to be usable by people with disabilities",
            "accessiblelinks": "Hyperlinks that provide clear context and purpose for screen reader users",
            "headinglevels": "Hierarchical structure of content that enables efficient navigation with assistive technology",
            "landmarks": "Structural elements that help users navigate web content with screen readers",

            # Quality and Performance
            "performance": "The speed and efficiency of technology systems, particularly important for assistive technology users",
            "responsiveness": "How quickly a system responds to user input, critical for screen reader effectiveness",
            "troubleshooting": "The process of identifying and resolving problems with assistive technology",

            # Music and Audio
            "musicbraille": "A braille code system for representing musical notation tactilely",
            "musicxml": "A digital format for representing musical notation that can be converted to accessible formats",
            "audiobook": "Digital audio recordings of books, providing accessible reading alternatives",

            # Programming and Development
            "programminglanguages": "Computer languages used to create software, including accessibility-focused applications",
            "api": "Application Programming Interface - protocols that enable software accessibility features",
            "sdk": "Software Development Kit - tools for creating accessible applications",
            "gui": "Graphical User Interface - visual interfaces that require accessible alternatives for screen reader users",
            "cli": "Command Line Interface - text-based interfaces often more accessible than graphical ones"
        }

    def enhance_glossary(self, input_file: str = "glossary_terms.json", output_file: str = "glossary_terms.json"):
        """Enhance existing glossary with better definitions"""

        # Load existing glossary
        with open(input_file, 'r', encoding='utf-8') as f:
            glossary = json.load(f)

        enhanced_count = 0

        # Enhance definitions
        for key, entry in glossary.items():
            if key in self.enhanced_definitions:
                entry['definition'] = self.enhanced_definitions[key]
                enhanced_count += 1
            elif entry['definition'] == "A technical term related to assistive technology and accessibility":
                # Try to infer a better definition from variants
                entry['definition'] = self._infer_definition_from_variants(key, entry['variants'])
                enhanced_count += 1

        # Save enhanced glossary
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(glossary, f, indent=2, ensure_ascii=False, sort_keys=True)

        print(f"Enhanced {enhanced_count} definitions in {output_file}")
        return glossary

    def _infer_definition_from_variants(self, key: str, variants: list) -> str:
        """Infer definition from variant names and context"""

        # Look for clues in variants
        variant_text = " ".join(variants).lower()

        if any(word in variant_text for word in ['microsoft', 'office', 'word', 'excel']):
            return "Microsoft Office suite applications with accessibility features for document creation and editing"
        elif any(word in variant_text for word in ['google', 'workspace', 'docs']):
            return "Google Workspace applications providing cloud-based document creation with accessibility features"
        elif any(word in variant_text for word in ['apple', 'ipad', 'iphone']):
            return "Apple devices and software with built-in accessibility features including VoiceOver"
        elif any(word in variant_text for word in ['samsung', 'android']):
            return "Android-based devices and applications with accessibility features including TalkBack"
        elif any(word in variant_text for word in ['freedom', 'scientific']):
            return "Freedom Scientific assistive technology products for users with visual impairments"
        elif any(word in variant_text for word in ['orbit', 'research']):
            return "Orbit Research assistive technology devices, particularly braille displays and DAISY players"
        elif any(word in variant_text for word in ['humanware']):
            return "HumanWare assistive technology products for users with visual impairments"
        elif 'embosser' in variant_text:
            return "Braille embosser device or manufacturer producing tactile braille printing equipment"
        elif 'magnifier' in variant_text:
            return "Video magnification device or software for users with low vision"
        elif 'notetaker' in variant_text:
            return "Braille notetaker device combining braille display with note-taking and computing functions"
        elif any(word in variant_text for word in ['support', 'help', 'assistance']):
            return "Support resources and assistance for assistive technology users"
        elif 'printer' in variant_text:
            return "3D printer manufacturer or model used for creating tactile materials and adaptive devices"
        elif 'filament' in variant_text:
            return "3D printing material supplier providing filaments for creating assistive technology objects"
        else:
            return "A specialized term in assistive technology and accessibility"

    def generate_latex_glossary(self, glossary: Dict[str, Any], output_file: str = "glossary_definitions.tex"):
        """Generate LaTeX newglossaryentry commands"""

        latex_entries = []
        latex_entries.append("% Generated glossary definitions for LaTeX")
        latex_entries.append("% Include this file in your LaTeX preamble after \\usepackage{glossaries}")
        latex_entries.append("% Use \\gls{key} in your text to reference terms")
        latex_entries.append("")

        for key, data in sorted(glossary.items()):
            # Get the primary variant (first one without hierarchy markers)
            name = None
            for variant in data['variants']:
                if '!' not in variant:  # Skip hierarchical index entries
                    name = variant
                    break

            if not name:
                name = data['variants'][0].split('!')[0]  # Fallback to first part of hierarchical entry

            description = data['definition']

            # Escape LaTeX special characters
            name = self._escape_latex(name)
            description = self._escape_latex(description)

            entry = f"\\newglossaryentry{{{key}}}{{\n    name={{{name}}},\n    description={{{description}}}\n}}"
            latex_entries.append(entry)

        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(latex_entries))

        print(f"Generated LaTeX glossary definitions in {output_file}")

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
            '~': '\\textasciitilde{}',
            '\\': '\\textbackslash{}'
        }

        for char, replacement in replacements.items():
            text = text.replace(char, replacement)

        return text

if __name__ == "__main__":
    enhancer = GlossaryEnhancer()

    # Enhance the glossary
    glossary = enhancer.enhance_glossary()

    # Generate LaTeX definitions
    enhancer.generate_latex_glossary(glossary)

    print(f"Glossary enhancement complete. Total terms: {len(glossary)}")
