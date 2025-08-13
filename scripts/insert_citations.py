import json
import os
import re
import sys

def get_tex_files_from_prompt():
    """
    Returns the list of TeX files provided in the initial prompt.
    """
    # This list is taken directly from the user's request.
    return [
        "./Chapters/Appendix00.tex",
        "./Chapters/Appendix01.tex",
        "./Chapters/Appendix02.tex",
        "./Chapters/Appendix03.tex",
        "./Chapters/Appendix04.tex",
        "./Chapters/Appendix05.tex",
        "./Chapters/Appendix06.tex",
        "./Chapters/BackMatter.tex",
        "./Chapters/Chapter01.tex",
        "./Chapters/Chapter02.tex",
        "./Chapters/Chapter03.tex",
        "./Chapters/Chapter04.tex",
        "./Chapters/Chapter05.tex",
        "./Chapters/Chapter06.tex",
        "./Chapters/Chapter07.tex",
        "./Chapters/Chapter08.tex",
        "./Chapters/Chapter09.tex",
        "./Chapters/Chapter10.tex",
        "./Chapters/Chapter11.tex",
        "./Chapters/Chapter12.tex",
        "./Chapters/Chapter13.tex",
        "./Chapters/Chapter14.tex",
        "./Chapters/Chapter15.tex",
        "./Chapters/Chapter16.tex",
        "./Chapters/Chapter17.tex",
        "./Chapters/Chapter18.tex",
        "./Chapters/Chapter19.tex",
        "./Chapters/Chapter20.tex",
        "./Chapters/Chapter21.tex",
        "./Chapters/Chapter23.tex",
        "./Chapters/Chapter24.tex",
        "./Chapters/Chapter25.tex",
        "./Chapters/Chapter26.tex",
        "./Chapters/Chapter27.tex",
        "./Chapters/Chapter28.tex",
        "./Chapters/Conclusion.tex",
        "./Chapters/Introduction.tex"
    ]

def is_safe_to_cite(context):
    """
    Checks if the surrounding text is a safe place to insert a citation.
    Avoids inserting inside headings, captions, or other commands.
    """
    # Regex to find unsafe contexts like \section{...}, \caption{...}, etc.
    unsafe_patterns = [
        r'\\(chapter|section|subsection|subsubsection)\s*\{[^}]*$',
        r'\\caption\s*\{[^}]*$',
        r'\\label\s*\{[^}]*$',
        r'\\title\s*\{[^}]*$',
        r'\\author\s*\{[^}]*$'
    ]
    for pattern in unsafe_patterns:
        # Check if the context string matches the start of an unsafe command
        if re.search(pattern, context, re.IGNORECASE):
            return False
    return True

def find_best_insertion_point(match_start, text):
    """
    Finds the best point to insert a citation, typically at the end of a sentence.
    """
    # Search for the end of the sentence (., !, ?) after the match
    sentence_end_match = re.search(r'[.!?]', text[match_start:])
    if sentence_end_match:
        # Insert before the punctuation
        return match_start + sentence_end_match.start()

    # Fallback: search for a newline or paragraph break
    line_end_match = re.search(r'(\n\n|\s*$)', text[match_start:])
    if line_end_match:
        return match_start + line_end_match.start()

    # If no clear end is found, place it right after the matched text.
    # This is a last resort.
    return match_start + len(text.split()[0]) # approx end of word

def insert_citations(tex_files, bib_data, project_root, citation_command="\\supercite"):
    """
    Inserts citations into TeX files based on the notes in the BibTeX data.
    """
    changes_summary = []

    # --- FIRST PASS ---
    print("--- Starting First Pass ---")
    for tex_file_path in tex_files:
        full_path = os.path.join(project_root, tex_file_path.lstrip('./'))
        if not os.path.exists(full_path):
            print(f"Warning: TeX file not found: {full_path}")
            continue

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        for entry in bib_data:
            if entry['cited']:
                continue

            key = entry['key']
            note = entry['note']

            # Clean the note for searching: escape special LaTeX characters
            search_text = note.replace('{', '').replace('}', '')
            if not search_text or len(search_text) < 20: # Avoid short/generic notes
                continue

            # Check if citation already exists
            if f"{citation_command}{{{key}}}" in content:
                entry['cited'] = True
                continue

            try:
                # Find all occurrences of the note text
                for match in re.finditer(re.escape(search_text), content, re.IGNORECASE):
                    match_start = match.start()

                    # Check context before insertion point
                    context_window = content[max(0, match_start - 50):match_start]
                    if not is_safe_to_cite(context_window):
                        continue

                    # Find where to insert the citation
                    insertion_point = find_best_insertion_point(match.end(), content)
                    if insertion_point:
                        citation_text = f"{citation_command}{{{key}}}"
                        content = content[:insertion_point] + citation_text + content[insertion_point:]
                        entry['cited'] = True

                        line_number = original_content.count('\n', 0, insertion_point) + 1
                        change_info = {
                            "location": f"{tex_file_path}#L{line_number}",
                            "action": "inserted",
                            "citation": key,
                            "confidence": 0.95,
                            "reason": f"Matched content from 'note' field: '{search_text[:50]}...'"
                        }
                        changes_summary.append(change_info)
                        print(f"  + Cited '{key}' in {tex_file_path}")
                        break # Move to the next bib entry
            except re.error:
                # Handle cases where the note might form an invalid regex
                continue

        if content != original_content:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

    # --- IDENTIFY UNCITED ---
    uncited_entries = [entry for entry in bib_data if not entry['cited']]
    if not uncited_entries:
        print("\nAll entries cited in the first pass. No second pass needed.")
    else:
        print(f"\n--- {len(uncited_entries)} Uncited Entries After First Pass ---")
        for entry in uncited_entries:
            print(f"  - {entry['key']}")

        # --- SECOND PASS ---
        print("\n--- Starting Second Pass (Lenient Search) ---")
        for tex_file_path in tex_files:
            full_path = os.path.join(project_root, tex_file_path.lstrip('./'))
            if not os.path.exists(full_path):
                continue

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            for entry in uncited_entries:
                if entry['cited']:
                    continue

                key = entry['key']
                note = entry['note']

                # Lenient search: use significant parts of the note
                search_phrases = sorted(re.split(r'[;,.()]+', note), key=len, reverse=True)

                for phrase in search_phrases:
                    phrase = phrase.strip()
                    if len(phrase) < 25: # Require a reasonably long phrase
                        continue

                    if f"{citation_command}{{{key}}}" in content:
                        entry['cited'] = True
                        break

                    try:
                        if re.search(re.escape(phrase), content, re.IGNORECASE):
                            match = next(re.finditer(re.escape(phrase), content, re.IGNORECASE))
                            match_start = match.start()
                            context_window = content[max(0, match_start - 50):match_start]

                            if is_safe_to_cite(context_window):
                                insertion_point = find_best_insertion_point(match.end(), content)
                                if insertion_point:
                                    citation_text = f"{citation_command}{{{key}}}"
                                    content = content[:insertion_point] + citation_text + content[insertion_point:]
                                    entry['cited'] = True

                                    line_number = original_content.count('\n', 0, insertion_point) + 1
                                    change_info = {
                                        "location": f"{tex_file_path}#L{line_number}",
                                        "action": "inserted",
                                        "citation": key,
                                        "confidence": 0.75, # Lower confidence for second pass
                                        "reason": f"Matched partial content from 'note': '{phrase[:50]}...'"
                                    }
                                    changes_summary.append(change_info)
                                    print(f"  + Cited '{key}' in {tex_file_path} (second pass)")
                                    break # Phrase found, move to next entry
                    except re.error:
                        continue
                if entry['cited']:
                    continue

            if content != original_content:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)

    final_uncited = [entry for entry in bib_data if not entry['cited']]
    if final_uncited:
        print("\n--- Remaining Uncited Entries After Second Pass ---")
        for entry in final_uncited:
            print(f"  - {entry['key']}")
    else:
        print("\nSuccess! All BibTeX entries have been cited.")

    return changes_summary

def main():
    """
    Main function to run the citation insertion process.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    bib_data_file = os.path.join(script_dir, 'bib_data.json')
    summary_file = os.path.join(script_dir, 'changes_summary.json')

    if not os.path.exists(bib_data_file):
        print(f"Error: BibTeX data file not found at {bib_data_file}")
        print("Please run the parse_bib.py script first.")
        sys.exit(1)

    with open(bib_data_file, 'r', encoding='utf-8') as f:
        bib_data = json.load(f)

    tex_files = get_tex_files_from_prompt()

    print(f"Loaded {len(bib_data)} BibTeX entries.")
    print(f"Processing {len(tex_files)} TeX files.")

    summary = insert_citations(tex_files, bib_data, project_root)

    if summary:
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=4)
        print(f"\nCitation insertion process complete. Summary saved to {summary_file}")
    else:
        print("\nNo changes were made to the TeX files.")

if __name__ == '__main__':
    main()
