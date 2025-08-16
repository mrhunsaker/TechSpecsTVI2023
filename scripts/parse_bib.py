import bibtexparser
import json
import os
import re

def parse_bib_file(bib_file_path):
    """
    Parses a BibTeX file to extract citation keys and their associated metadata,
    paying special attention to the 'note' and 'notes' fields.

    Args:
        bib_file_path (str): The path to the BibTeX file.

    Returns:
        list: A list of dictionaries, where each dictionary contains the
              citation key and the content of the 'note' or 'notes' field.
    """
    entries_data = []
    if not os.path.exists(bib_file_path):
        print(f"Error: The file '{bib_file_path}' was not found.")
        return entries_data

    # Bibtexparser can be strict. A custom, more lenient parsing approach
    # might be necessary if the file has formatting issues.
    # For now, we will try with the standard library.
    try:
        with open(bib_file_path, 'r', encoding='utf-8') as bibtex_file:
            # Using a permissive parser
            parser = bibtexparser.bparser.BibTexParser(common_strings=True)
            bib_database = bibtexparser.load(bibtex_file, parser=parser)

        for entry in bib_database.entries:
            key = entry.get('ID')
            # Per instructions, prioritize the 'notes' field over 'note'
            note_content = entry.get('notes', entry.get('note', ''))

            if key and note_content:
                # Clean up the note content for better matching
                cleaned_note = re.sub(r'\s+', ' ', note_content).strip()
                entries_data.append({
                    'key': key,
                    'note': cleaned_note,
                    'cited': False
                })
    except Exception as e:
        print(f"An error occurred while parsing the BibTeX file: {e}")
        # Fallback to regex-based parsing if bibtexparser fails
        print("Attempting fallback parsing with regex...")
        try:
            with open(bib_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Regex to capture each entry block
            entry_blocks = re.findall(r'@\w+\{([^,]+),((?:.|\n)*?)\n\}', content)

            for key, fields_block in entry_blocks:
                key = key.strip()
                note_content = ''

                # Search for 'notes' field first
                notes_match = re.search(r'notes\s*=\s*\{(.*?)\}', fields_block, re.DOTALL)
                if notes_match:
                    note_content = notes_match.group(1)
                else:
                    # Fallback to 'note' field
                    note_match = re.search(r'note\s*=\s*\{(.*?)\}', fields_block, re.DOTALL)
                    if note_match:
                        note_content = note_match.group(1)

                if key and note_content:
                    cleaned_note = re.sub(r'\s+', ' ', note_content).strip()
                    entries_data.append({
                        'key': key,
                        'note': cleaned_note,
                        'cited': False
                    })
        except Exception as re_e:
            print(f"Fallback regex parsing also failed: {re_e}")
            return []


    return entries_data

def main():
    """
    Main function to run the BibTeX parsing process.
    """
    # Assuming the script is in TechSpecsTVI/scripts and uncited.bib is in TechSpecsTVI/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    bib_file = os.path.join(project_root, 'uncited.bib')
    output_file = os.path.join(script_dir, 'bib_data.json')

    print(f"Parsing BibTeX file: {bib_file}")
    parsed_entries = parse_bib_file(bib_file)

    if parsed_entries:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(parsed_entries, f, indent=4)
        print(f"Successfully parsed {len(parsed_entries)} entries.")
        print(f"Parsed data has been saved to {output_file}")
    else:
        print("Could not parse any entries from the BibTeX file.")

if __name__ == '__main__':
    main()
