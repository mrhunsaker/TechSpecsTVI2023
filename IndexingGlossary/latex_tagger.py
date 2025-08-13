import os
import re
import json
import pathlib
from collections import defaultdict

# Load configuration
CONFIG_PATH = "latex_tagger_config.json"
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

LATEX_DIR = pathlib.Path(config["latex_directory"])
OUTPUT_DIR = pathlib.Path(config["processed_directory"])
OUTPUT_DIR.mkdir(exist_ok=True)

GLOSSARY_FILE = config["glossary_terms_file"]
INDEX_FILE = config["index_terms_file"]
STRUCTURAL_COMMANDS = config["structural_commands"]
MIN_INDEX_REPEAT_DISTANCE = config["min_index_repeat_distance"]

# Load glossary and index terms
def load_json_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

glossary_map = load_json_file(GLOSSARY_FILE) if config["glossary_enabled"] else {}
index_map = load_json_file(INDEX_FILE) if config["index_enabled"] else {}

# Helper functions
def is_inside_structural_command(line):
    return any(line.strip().startswith(cmd) for cmd in STRUCTURAL_COMMANDS)

def tokenize_words(text):
    return re.findall(r'\b\w+\b', text)

def insert_gls_and_index(lines, glossary_map, index_map):
    modified_lines = []
    last_index_positions = defaultdict(lambda: -99999)
    word_count = 0

    for line in lines:
        original_line = line
        if is_inside_structural_command(line):
            modified_lines.append(line)
            continue

        tokens = tokenize_words(line)
        new_line = line
        for key, entry in glossary_map.items():
            for variant in entry["variants"]:
                if re.search(rf'\b{re.escape(variant)}\b', line, re.IGNORECASE):
                    new_line = re.sub(
                        rf'\b({re.escape(variant)})\b',
                        rf'\\gls{{{key}}}',
                        new_line,
                        count=1
                    )
                    break

        for key, variants in index_map.items():
            for variant in variants:
                match = re.search(rf'\b{re.escape(variant)}\b', line, re.IGNORECASE)
                if match and (word_count - last_index_positions[key] >= MIN_INDEX_REPEAT_DISTANCE):
                    pos = match.start()
                    insert_pos = line.find(variant, pos)
                    new_line = new_line[:insert_pos + len(variant)] + f"\\index{{{key}}}" + new_line[insert_pos + len(variant):]
                    last_index_positions[key] = word_count
                    break

        word_count += len(tokens)
        modified_lines.append(new_line)

    return modified_lines

# Interactive TUI
def prompt_continue(file):
    resp = input(f"\nProcess file: {file.name}? [y/n]: ").strip().lower()
    return resp == "y"

def process_latex_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated_lines = insert_gls_and_index(lines, glossary_map, index_map)

    output_path = OUTPUT_DIR / file_path.name
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)

    print(f"✓ Processed and saved: {output_path}")

def main():
    tex_files = sorted(LATEX_DIR.glob("*.tex"))
    print("LaTeX Glossary + Index Tagger")
    print("=============================")
    print(f"Found {len(tex_files)} LaTeX files in '{LATEX_DIR}'")

    for file in tex_files:
        if prompt_continue(file):
            process_latex_file(file)

    print("\n✅ All selected files processed.")
    print(f"Results saved in: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
