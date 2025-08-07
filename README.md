# Technology Specifications for Students with Visual Impairments

This repository contains the LaTeX source for a document describing technology needs for students with visual impairments. The project is built with a strong emphasis on creating a highly accessible PDF output that conforms to modern standards.

## Table of Contents
- [Formatting and Tagging Parameters](#formatting-and-tagging-parameters)
- [Accessibility Audit](#accessibility-audit)
  - [Screen Reader Accessibility](#screen-reader-accessibility)
  - [PDF Accessibility Standards](#pdf-accessibility-standards)
- [Glossary System](#glossary-system)
- [How to Compile](#how-to-compile)
- [License](#license)

## Formatting and Tagging Parameters

The document is structured using LaTeX with several packages and configurations to ensure proper formatting and, most importantly, a well-tagged and accessible final PDF.

### Document Setup

- **Document Class**: `report` class with `11pt` font size, `letterpaper` size, and `twoside` layout.
- **Main Font**: [Atkinson Hyperlegible](https://brailleinstitute.org/freefont) is used as the main document font for its high legibility.
- **Monospace Font**: [JetBrains Mono](https://www.jetbrains.com/lp/mono/) is used for monospaced text.
- **Bibliography**: The `biblatex` package is used for managing citations with a numeric-compressive style.

### Core Accessibility Configuration

The following settings are configured in `main.tex` to produce a tagged and accessible PDF:

- **PDF Metadata**:
  - `lang = en-US`: Sets the document's primary language to US English.
  - `pdfstandard = ua-2, a-4f`: Specifies that the PDF should conform to both **PDF/UA-2** (Universal Accessibility) and **PDF/A-4f** (Archiving with embedded files) standards.
  - `pdfversion = 2.0`: Uses the modern PDF 2.0 version.
  - `tagging=on`: This is the master switch to enable the creation of a tagged PDF.

- **`tagpdf` Package Setup**: The `tagpdf` package is the primary engine for creating the tagged structure.
  - `activate-all`: Enables all available tagging features for environments like lists, tables, and headings.
  - `uncompress`: Keeps the PDF's internal structure uncompressed. This is useful for debugging the tag tree but should be disabled for final production to reduce file size.
  - `interwordspace=true`: Ensures that spaces between words are correctly tagged, which is crucial for proper screen reader text flow.
  - `table/tagging=true`: Enables automatic tagging for tables created with supported packages.
  - `table/header-rows=1`: Automatically tags the first row of a table as a header row (`<TH>`).

- **Image Accessibility**:
  - A custom command, `\imgalt{alt_text}{image_command}`, is used to provide alternative text for all images. This wraps the image in an `AccSupp` block, making the alt text available to screen readers.

- **Math Accessibility**:
  - `tagging-setup={math/setup=mathml-SE}`: This experimental feature from `tagpdf` embeds MathML representations of equations, making complex math accessible to screen readers that support it.

## Accessibility Audit

This project is designed to meet high accessibility standards.

### Screen Reader Accessibility

The generated PDF is optimized for screen readers (like JAWS, NVDA, or VoiceOver) in the following ways:

1.  **Logical Reading Order**: The tagged structure ensures that content is read in the correct order, following headings, paragraphs, lists, and tables as a human would.
2.  **Alternative Text for Images**: Every image is provided with descriptive alternative text, allowing users to understand its content and purpose.
3.  **Navigable Structure**: The use of standard tags for headings (`<H1>`, `<H2>`, etc.), tables of contents, and other document elements allows users to easily navigate the document by jumping between sections.
4.  **Proper Table Reading**: Tables are tagged with header rows, allowing screen readers to announce the column header for each cell as a user navigates through the table. This provides essential context for tabular data.
5.  **Language Identification**: The document's language is set, allowing screen readers to use the correct pronunciation engine.
6.  **Accessible Math**: By embedding MathML, mathematical equations can be read and navigated in a structured way, rather than being announced as a jumble of symbols.

### PDF Accessibility Standards

The project targets two key PDF standards:

-   **PDF/UA (Universal Accessibility)**: This is the international standard for accessible PDF technology. Conformance with PDF/UA ensures that the document is technically sound and usable for people with disabilities. The configuration `pdfstandard = ua-2` targets the latest version of this standard.
-   **PDF/A (Archival)**: This standard ensures that the document can be reliably reproduced and viewed in the long term. The `a-4f` variant allows for file attachments, which is useful for embedding source files or data. This makes the document self-contained and future-proof.

## Glossary System

This project includes a comprehensive glossary system with 115 specialized terms in assistive technology and accessibility. The glossary provides:

- **Consistent Terminology**: Unified definitions across all chapters
- **Enhanced Navigation**: LaTeX glossary linking for easy reference
- **Accessibility Support**: Screen reader compatible glossary structure
- **Educational Value**: Clear explanations of technical concepts

### Glossary Integration

The glossary system is pre-configured and ready to use:
- **Glossary Database**: `glossary_terms.json` - Master database with all terms
- **LaTeX Definitions**: `glossary_preamble.tex` - Pre-generated glossary entries
- **Document Integration**: `\gls{}` commands already inserted throughout text

## How to Compile

To compile this project, you will need a modern LaTeX distribution that includes the `lualatex` engine, as `fontspec` and `tagpdf` rely on it.

### Prerequisites
- **Engine**: `lualatex` (required for fontspec and tagpdf)
- **Bibliography**: `biber` (for processing citations)
- **Glossary**: `makeglossaries` (for processing glossary terms)
- **Index**: `makeindex` (for processing index entries)

### Complete Compilation Sequence

This project requires multiple processing steps to generate the bibliography, glossary, and index:

```bash
# First LaTeX pass - generates auxiliary files
lualatex main.tex

# Process bibliography
biber main

# Process glossary (115 terms)
makeglossaries main

# Process index
makeindex main.idx

# Second LaTeX pass - incorporates bibliography, glossary, and index
lualatex main.tex

# Final LaTeX pass - resolves all cross-references
lualatex main.tex
```

### Quick Compilation Script

For convenience, you can use this one-liner:

```bash
lualatex main && biber main && makeglossaries main && makeindex main.idx && lualatex main && lualatex main
```

### Compilation Notes

- **First run**: Generates `.aux`, `.glo`, `.idx`, and other auxiliary files
- **biber**: Processes bibliography from `global_bibliography.bib`
- **makeglossaries**: Processes 115 glossary terms with `\gls{}` references
- **makeindex**: Creates index from extensive `\index{}` entries
- **Final runs**: Incorporate all processed elements and resolve cross-references

### Output Files

The compilation process generates:
- `main.pdf` - Final accessible PDF document
- `main.gls` - Processed glossary
- `main.ind` - Processed index
- Various auxiliary files for cross-referencing

## License

This project is licensed under the **Apache License 2.0**.

You may obtain a copy of the License at:

> http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.