#!/usr/bin/env python3
"""
format_bib.py

Utility script to reformat (pretty-print) BibTeX files whose entries are currently
on a single line (or otherwise poorly formatted) into a conventional multi-line,
indented style.

Features:
- Parses BibTeX entries (@article, @misc, @book, @inproceedings, @string, @preamble, @comment).
- Converts one‑line entries into multi-line form:
    @type{key,
      field1 = {value},
      field2 = {value},
    }
- Preserves (or optionally reorders) field order.
- Optional field ordering heuristic (e.g., author, title, journal, booktitle, year, etc.).
- Optionally sorts fields according to a preferred order, leaving unspecified fields
  in their original order or sorted alphabetically.
- In‑place editing with optional backup.
- Adjustable indentation and maximum line width (simple wrapping for long non-braced text).
- Gracefully skips entries it cannot parse (emits them unchanged with a warning comment).
- Title capitalization normalization (Title Case / sentence / lower / upper) for the 'title' field.

This is a lightweight, dependency‑free parser intended for cleaning up typical BibTeX
export files (including those collapsed into one line per entry). It does not aim
for 100% BibTeX specification compliance (e.g., it assumes balanced braces within an entry
and does minimal macro handling).

Example usage:
  # Dry run to STDOUT
  python format_bib.py global_bibliography.bib

  # Write to new file (no trailing commas on last field by default)
  python format_bib.py global_bibliography.bib -o global_bibliography_formatted.bib

  # In place with backup
  python format_bib.py global_bibliography.bib --in-place --backup

  # Sort fields using default preference list
  python format_bib.py global_bibliography.bib --sort-fields

  # Custom field order (commas)
  python format_bib.py global_bibliography.bib --sort-fields --field-order author,title,year,note

  # Normalize title capitalization (default 'title')
  python format_bib.py global_bibliography.bib --title-style title

Limitations:
- Does not attempt to normalize case beyond simple configurable title normalization.
- Does not re-wrap content that already has internal line breaks (left as-is).
- Does not evaluate @string macros; it simply preserves them.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import textwrap
from typing import List, Tuple, Dict, Optional, Callable, Iterable

Entry = Dict[str, str]


DEFAULT_FIELD_ORDER = [
    "author",
    "editor",
    "title",
    "booktitle",
    "journal",
    "school",
    "institution",
    "organization",
    "publisher",
    "howpublished",
    "series",
    "volume",
    "number",
    "edition",
    "chapter",
    "pages",
    "address",
    "location",
    "doi",
    "url",
    "year",
    "month",
    "note",
    "abstract",
    "keywords",
]

# Common short words to keep lowercase in Title Case (unless first/last)
TITLE_SMALL_WORDS = {
    "a", "an", "the", "and", "or", "nor", "but", "for", "on", "in", "to", "of", "by",
    "at", "vs", "via", "per", "as", "with", "from", "into", "over", "under"
}


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Reformat BibTeX file into multi-line entries.")
    p.add_argument("input", type=Path, help="Input .bib file")
    p.add_argument("-o", "--output", type=Path, help="Output file (default: stdout or input if --in-place)")
    p.add_argument("--in-place", action="store_true", help="Modify the input file in place")
    p.add_argument("--backup", action="store_true", help="Make a .bak backup when using --in-place")
    p.add_argument("--indent", type=int, default=2, help="Indent spaces for fields (default: 2)")
    p.add_argument("--width", type=int, default=120, help="Maximum line width (simple wrapping; default: 120)")
    p.add_argument("--sort-fields", action="store_true", help="Sort fields using preferred order list")
    p.add_argument(
        "--field-order",
        type=str,
        help="Comma-separated custom field order (overrides default ordering if provided)",
    )
    p.add_argument(
        "--keep-trailing-comma",
        action="store_true",
        help="Keep a trailing comma after the last field (some styles prefer this)",
    )
    p.add_argument(
        "--title-style",
        choices=["title", "sentence", "lower", "upper", "none"],
        default="title",
        help="Normalization style for title field capitalization (default: title).",
    )
    return p.parse_args(argv)


def load_content(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def segment_entries(text: str) -> List[Tuple[str, bool]]:
    """
    Segment the raw file into a sequence of (chunk, is_entry).
    Non-entry chunks (whitespace/comments outside entries) are preserved verbatim.
    """
    chunks: List[Tuple[str, bool]] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == "@":
            # Potential entry
            start = i
            brace_pos = text.find("{", i)
            if brace_pos == -1:
                chunks.append((text[i:], False))
                break
            typetok = text[i + 1 : brace_pos].strip().lower()
            if not typetok or any(c.isspace() for c in typetok):
                chunks.append((text[i], False))
                i += 1
                continue
            depth = 0
            j = brace_pos
            in_string = False
            escape = False
            while j < n:
                c = text[j]
                if c == '"' and not escape:
                    in_string = not in_string
                if not in_string:
                    if c == "{" and not escape:
                        depth += 1
                    elif c == "}" and not escape:
                        depth -= 1
                        if depth == 0:
                            j += 1
                            break
                escape = (c == "\\" and not escape)
                j += 1
            entry_text = text[start:j]
            chunks.append((entry_text, True))
            i = j
        else:
            next_at = text.find("@", i)
            if next_at == -1:
                chunks.append((text[i:], False))
                break
            else:
                chunks.append((text[i:next_at], False))
                i = next_at
    return chunks


def split_key_and_fields(body: str) -> Tuple[str, str]:
    depth = 0
    in_string = False
    escape = False
    for idx, c in enumerate(body):
        if c == '"' and not escape:
            in_string = not in_string
        if not in_string:
            if c == "{" and not escape:
                depth += 1
            elif c == "}" and not escape:
                if depth > 0:
                    depth -= 1
            elif c == "," and depth == 0:
                key = body[:idx].strip()
                rest = body[idx + 1 :].strip()
                return key, rest
        escape = (c == "\\" and not escape)
    return body.strip(), ""


def split_fields(fields_str: str) -> List[str]:
    if not fields_str:
        return []
    parts = []
    depth = 0
    in_string = False
    escape = False
    start = 0
    for i, c in enumerate(fields_str):
        if c == '"' and not escape:
            in_string = not in_string
        if not in_string:
            if c == "{" and not escape:
                depth += 1
            elif c == "}" and not escape and depth > 0:
                depth -= 1
            elif c == "," and depth == 0:
                parts.append(fields_str[start:i].strip())
                start = i + 1
        escape = (c == "\\" and not escape)
    tail = fields_str[start:].strip()
    if tail:
        parts.append(tail)
    return [p for p in parts if p]


def parse_field(segment: str) -> Tuple[str, str]:
    if "=" not in segment:
        return segment.strip(), ""
    name, val = segment.split("=", 1)
    return name.strip().lower(), val.strip()


def parse_entry(entry_text: str) -> Dict:
    at_pos = entry_text.find("@")
    brace_pos = entry_text.find("{", at_pos)
    if at_pos == -1 or brace_pos == -1 or not entry_text.rstrip().endswith("}"):
        raise ValueError("Entry missing structure")
    header = entry_text[at_pos:brace_pos].strip()
    etype = header[1:].strip().lower()

    if etype in ("comment", "string", "preamble"):
        return {
            "raw": entry_text,
            "type": etype,
            "key": "",
            "fields": [],
            "header": header,
            "special": True,
        }

    inner = entry_text[brace_pos + 1 : -1].strip()
    key, fields_str = split_key_and_fields(inner)
    if not key:
        raise ValueError("Could not locate key")

    field_segments = split_fields(fields_str)
    fields = []
    for seg in field_segments:
        fname, fval = parse_field(seg)
        fields.append((fname, fname.lower(), fval))

    return {
        "raw": entry_text,
        "type": etype,
        "key": key.strip(),
        "fields": fields,
        "header": header,
        "special": False,
    }


def order_fields(fields, sort: bool, preferred_order: List[str]) -> List[Tuple[str, str, str]]:
    if not sort:
        return fields
    order_map = {name: idx for idx, name in enumerate(preferred_order)}
    recognized = []
    unknown = []
    for orig, lower, val in fields:
        if lower in order_map:
            recognized.append((order_map[lower], orig, lower, val))
        else:
            unknown.append((orig, lower, val))
    recognized.sort(key=lambda r: r[0])
    ordered = [(o, lname, v) for _, o, lname, v in recognized] + unknown
    return ordered


def wrap_value(value: str, indent: int, field_prefix_len: int, width: int) -> List[str]:
    r"""Wrap value if plain text (no internal newlines) and not containing typical URL markers; returns list of lines (no trailing newline)."""
    if "\n" in value or "\\url" in value or "http" in value:
        return [value]
    stripped = value.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        inner = stripped[1:-1]
        if len(inner) + field_prefix_len + indent <= width:
            return [value]
        wrapped_inner = textwrap.wrap(
            inner,
            width=width - field_prefix_len - indent,
            subsequent_indent="",
            break_long_words=False,
            break_on_hyphens=False,
        )
        if len(wrapped_inner) <= 1:
            return [value]
        lines = ["{" + wrapped_inner[0]]
        lines.extend(wrapped_inner[1:])
        lines[-1] = lines[-1] + "}"
        return lines
    else:
        if len(stripped) + field_prefix_len + indent <= width:
            return [value]
        wrapped = textwrap.wrap(
            stripped,
            width=width - field_prefix_len - indent,
            break_long_words=False,
            break_on_hyphens=False,
        )
        return wrapped


def normalize_title(value: str, style: str) -> str:
    """
    Normalize capitalization of a BibTeX title value (which may be braced).
    Attempts to avoid altering LaTeX macros (tokens starting with backslash),
    math segments ($...$), or explicit brace-protected substrings.
    """
    if style == "none":
        return value

    # Extract inner if fully braced
    trimmed = value.strip()
    has_outer_brace = trimmed.startswith("{") and trimmed.endswith("}")
    inner = trimmed[1:-1] if has_outer_brace else trimmed

    # Quick skip for macros only
    if inner.startswith("\\"):
        return value

    # Tokenize on spaces while preserving existing braces and punctuation
    tokens = inner.split()

    def is_macro(tok: str) -> bool:
        return tok.startswith("\\") or tok.startswith("$") or tok.endswith("$")

    if style == "lower":
        new_inner = " ".join(tok if is_macro(tok) else tok.lower() for tok in tokens)
    elif style == "upper":
        new_inner = " ".join(tok if is_macro(tok) else tok.upper() for tok in tokens)
    elif style == "sentence":
        lowered = [tok if is_macro(tok) else tok.lower() for tok in tokens]
        for i, tok in enumerate(lowered):
            if is_macro(tok):
                continue
            # First alphabetic token
            lowered[i] = tok[0].upper() + tok[1:] if tok and tok[0].isalpha() else tok
            break
        new_inner = " ".join(lowered)
    else:  # title case
        # Title Case with small word handling
        result = []
        last_index = len(tokens) - 1
        for i, tok in enumerate(tokens):
            if is_macro(tok):
                result.append(tok)
                continue
            base = tok
            # Strip surrounding braces for decision (but keep internal structure)
            leading = ""
            trailing = ""
            while base and base[0] in "{([":
                leading += base[0]
                base = base[1:]
            while base and base[-1] in "}])!?:;.,\"'":
                trailing = base[-1] + trailing
                base = base[:-1]
            core = base
            if not core:
                result.append(tok)
                continue
            lower_core = core.lower()
            if (
                i != 0
                and i != last_index
                and lower_core in TITLE_SMALL_WORDS
            ):
                new_core = lower_core
            else:
                # Preserve internal capitalization for acronyms / all-caps
                # Preserve original casing for:
                # - All caps (ACRONYMS)
                # - Leading cap then all caps (e.g., eBook style variants captured by core[1:].isupper())
                # - Mixed / branded camel or internal capitalization (MathJax, NimPro, iPad, eLearning)
                #   Detected by comparing against simple Title Case normalization.
                simple_title = core[0].upper() + core[1:].lower() if core else core
                if (
                    core.isupper()
                    or core[1:].isupper()
                    or core != simple_title
                ):
                    new_core = core
                else:
                    new_core = simple_title
            result.append(leading + new_core + trailing)
        new_inner = " ".join(result)

    if has_outer_brace:
        return "{" + new_inner + "}"
    else:
        return new_inner


def format_entry(
    entry: Dict,
    indent: int,
    width: int,
    sort_fields: bool,
    preferred_order: List[str],
    keep_trailing_comma: bool,
    title_style: str,
) -> str:
    if entry.get("special"):
        return entry["raw"].rstrip() + "\n"

    fields = order_fields(entry["fields"], sort_fields, preferred_order)

    lines = []
    header_line = f"@{entry['type']}{{{entry['key']},"
    lines.append(header_line)

    field_indent = " " * indent
    for idx, (orig_name, lower_name, value) in enumerate(fields):
        name_to_use = lower_name
        value_str = value
        if lower_name == "title" and title_style:
            value_str = normalize_title(value_str, title_style)
        field_prefix = f"{name_to_use} = "
        wrapped_lines = wrap_value(value_str, indent, len(field_prefix), width)

        if len(wrapped_lines) == 1:
            line = f"{field_indent}{field_prefix}{wrapped_lines[0]}"
            is_last = idx == len(fields) - 1
            if not is_last or keep_trailing_comma:
                line += ","
            lines.append(line)
        else:
            is_last = idx == len(fields) - 1
            if wrapped_lines[0].startswith("{"):
                lines.append(f"{field_indent}{field_prefix}{wrapped_lines[0]}")
                for sub in wrapped_lines[1:-1]:
                    lines.append(f"{field_indent}{' ' * len(field_prefix)}{sub}")
                last = wrapped_lines[-1]
                if not is_last or keep_trailing_comma:
                    last += ","
                lines.append(f"{field_indent}{' ' * len(field_prefix)}{last}")
            else:
                lines.append(f"{field_indent}{field_prefix}{wrapped_lines[0]}")
                for sub in wrapped_lines[1:]:
                    lines.append(f"{field_indent}{' ' * len(field_prefix)}{sub}")
                if not is_last or keep_trailing_comma:
                    lines[-1] = lines[-1] + ","

    lines.append("}")
    return "\n".join(lines) + "\n"


def process(text: str, args: argparse.Namespace) -> str:
    segments = segment_entries(text)
    preferred_order = (
        [f.strip().lower() for f in args.field_order.split(",")] if args.field_order else DEFAULT_FIELD_ORDER
    )
    out_parts = []
    for chunk, is_entry in segments:
        if not is_entry:
            out_parts.append(chunk)
            continue
        try:
            entry = parse_entry(chunk)
            formatted = format_entry(
                entry,
                indent=args.indent,
                width=args.width,
                sort_fields=args.sort_fields,
                preferred_order=preferred_order,
                keep_trailing_comma=args.keep_trailing_comma,
                title_style=args.title_style,
            )
            out_parts.append(formatted)
        except Exception as e:  # noqa
            out_parts.append(f"% WARNING: Failed to parse entry; leaving unchanged. Error: {e}\n{chunk}\n")
    return "".join(out_parts)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    if args.in_place and args.output:
        print("Cannot specify both --in-place and --output. Choose one.", file=sys.stderr)
        return 2

    if not args.input.exists():
        print(f"Input file not found: {args.input}", file=sys.stderr)
        return 1

    original = load_content(args.input)
    result = process(original, args)

    if args.in_place:
        if args.backup:
            backup_path = args.input.with_suffix(args.input.suffix + ".bak")
            backup_path.write_text(original, encoding="utf-8")
        args.input.write_text(result, encoding="utf-8")
    else:
        if args.output:
            args.output.write_text(result, encoding="utf-8")
        else:
            sys.stdout.write(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
