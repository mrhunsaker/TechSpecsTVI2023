#!/usr/bin/env python3
r"""
cleanup_gidx.py

Purpose:
    Automated cleanup of redundant or malformed glossary/index tagging patterns
    in a LaTeX project that uses the custom macro:

        \gidx[<optional gls opts>]{<glossary-key>}{<index-visible-text>}

    and related derived issues (duplicate consecutive tags, nested tags, etc.).

Operations Performed (default run):
    1. Flatten nested patterns like:
           \gidx{tactilegraphics}{\gidx{tactilegraphics}{tactile graphics}}
       -> \gidx{tactilegraphics}{tactile graphics}

    2. Collapse immediate identical duplicates:
           \gidx{magnification}{magnification}\gidx{magnification}{magnification}
       -> single occurrence.

    3. Collapse immediate duplicate keys with differing visible text variants:
           \gidx{brailledisplay}{Braille display}\gidx{brailledisplay}{braille display}
       Rule: keep first tagged form; if the second only differs by case, drop it;
             else append the second visible text untagged (space separated).

    4. Enforce “first occurrence per paragraph” (or table row) rule:
       Within each paragraph (separated by one or more blank lines), only the first
       \gidx for a given key is retained; subsequent occurrences are replaced by
       the visible text only (index/glossary suppressed).
       For tables / list-like lines (heuristic: line contains '&' or ends with '\\'),
       the scope is per line instead of the whole paragraph (avoids wiping legitimate
       first occurrences in separate rows).

    5. Visible textual duplicate word collapse (post tag removal) for a curated list
       (braille display, braille literacy, tactile graphics, magnification,
        independence, text-to-speech) to clean up doubled visible tokens created
       when collapsing tags.

    6. Generates .bak backups for each modified file unless --no-backup is provided.

Features:
    - Dry run mode to preview changes.
    - Verbose summary of every transformation category count.
    - Configurable root directory and file glob include/exclude patterns.

Usage:
    Basic:
        python cleanup_gidx.py

    Dry run (no file modifications):
        python cleanup_gidx.py --dry-run

    Verbose:
        python cleanup_gidx.py -v

    Custom root (default: ./Chapters):
        python cleanup_gidx.py --root Chapters

    Disable backups (not recommended first pass):
        python cleanup_gidx.py --no-backup

Limitations / Assumptions:
    - Does not attempt to parse full LaTeX syntax; operates via regex heuristics.
    - Optional argument form \gidx[options]{key}{text} is supported, but nested removal
      and some duplicate regexes are conservative.
    - If you intend multiple index variants (e.g., different capitalizations for
      distinct index entries) you must manually add explicit \index commands; this
      script assumes duplicates are accidental.

Exit Codes:
    0 on success
    1 on internal error

Author:
    Automated assistant script (2025)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Pattern, Tuple, Dict


# ---------------------------------------------------------------------------
# Regex Patterns
# ---------------------------------------------------------------------------

# Base pattern for \gidx with optional [options]:
GIDX_PATTERN = r'\\gidx(?:\[[^\]]*])?{(?P<key>[^}]+)}{(?P<vis>[^}]+)}'

RE_GIDX: Pattern = re.compile(GIDX_PATTERN)

# Nested pattern: \gidx{key}{\gidx{key}{visible}}
RE_NESTED: Pattern = re.compile(
    r'(\\gidx(?:\[[^\]]*])?{(?P<key>[A-Za-z0-9_-]+)}{)\\gidx(?:\[[^\]]*])?{(?P=key)}{(?P<vis>[^}]+)}(})'
)

# Immediate identical duplicates (collapse runs)
# Using a backreference to replicate pattern repeated 1+ times
# Base (unnamed) pattern for duplication detection to avoid repeated named groups
GIDX_PATTERN_BASE = r'\\gidx(?:\[[^\]]*])?{[^}]+}{[^}]+}'
RE_IMMEDIATE_IDENTICAL: Pattern = re.compile(
    rf'({GIDX_PATTERN_BASE})(?:{GIDX_PATTERN_BASE})+'
)

# Immediate duplicate with same key but different visible (case-insensitive compare)
RE_IMMEDIATE_VARIANT: Pattern = re.compile(
    r'(\\gidx(?:\[[^\]]*])?{(?P<k>[A-Za-z0-9_-]+)}{(?P<vis1>[^}]+)})'
    r'(\\gidx(?:\[[^\]]*])?{(?P=k)}{(?P<vis2>[^}]+)})'
)

# Visible duplicate word cleanup list
VISIBLE_DUP_WORDS = [
    'braille display',
    'braille literacy',
    'tactile graphics',
    'magnification',
    'independence',
    'text-to-speech',
]
RE_VISIBLE_DUP_PATTERNS: List[Tuple[str, Pattern]] = [
    (w, re.compile(rf'\b({re.escape(w)})\b\s+\b({re.escape(w)})\b', flags=re.IGNORECASE))
    for w in VISIBLE_DUP_WORDS
]

# Heuristic for "table-like" line (scope of duplicates limited to each line)
def is_table_like(line: str) -> bool:
    return ('&' in line) or line.rstrip().endswith(r'\\')


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class Counts:
    files_processed: int = 0
    files_modified: int = 0
    nested_flattened: int = 0
    immediate_identical_collapsed: int = 0
    immediate_variant_collapsed: int = 0
    paragraph_dedup_replacements: int = 0
    visible_word_collapses: int = 0
    per_file_changes: Dict[Path, Dict[str, int]] = field(default_factory=lambda: {})

    def add_file(self, path: Path):
        if path not in self.per_file_changes:
            self.per_file_changes[path] = {
                "nested_flattened": 0,
                "immediate_identical_collapsed": 0,
                "immediate_variant_collapsed": 0,
                "paragraph_dedup_replacements": 0,
                "visible_word_collapses": 0,
            }

    def inc(self, path: Path, field_name: str, amount: int = 1):
        self.add_file(path)
        self.per_file_changes[path][field_name] += amount
        setattr(self, field_name, getattr(self, field_name) + amount)


# ---------------------------------------------------------------------------
# Transformation Functions
# ---------------------------------------------------------------------------

def flatten_nested(text: str, counts: Counts, path: Path) -> str:
    def repl(m: re.Match) -> str:
        counts.inc(path, "nested_flattened")
        return f"{m.group(1)}{m.group('vis')}{m.group(4)}"
    return RE_NESTED.sub(repl, text)


def collapse_immediate_identical(text: str, counts: Counts, path: Path) -> str:
    # We repeatedly apply until no change because of potential runs > 2
    while True:
        new_text, n = RE_IMMEDIATE_IDENTICAL.subn(lambda m: m.group(1), text)
        if n == 0:
            return text
        counts.inc(path, "immediate_identical_collapsed", n)
        text = new_text


def collapse_immediate_variants(text: str, counts: Counts, path: Path) -> str:
    def repl(m: re.Match) -> str:
        vis1 = m.group('vis1')
        vis2 = m.group('vis2')
        key = m.group('k')
        if vis1.strip().lower() == vis2.strip().lower():
            # Keep first tagged only
            counts.inc(path, "immediate_variant_collapsed")
            return m.group(1)
        else:
            # Keep first tagged, append second plain
            counts.inc(path, "immediate_variant_collapsed")
            return f"{m.group(1)} {vis2}"
    return RE_IMMEDIATE_VARIANT.sub(repl, text)


def paragraph_first_occurrence_dedup(text: str, counts: Counts, path: Path) -> str:
    """
    Enforce first occurrence per paragraph (blank-line delimited).
    For table-like lines, scope is per line.
    """
    parts = re.split(r'(\n\s*\n)', text)
    total_replacements = 0

    for i in range(0, len(parts), 2):  # even indices are paragraphs
        para = parts[i]
        if not para.strip():
            continue

        seen_global = set()
        lines = para.splitlines()
        new_lines = []
        for line in lines:
            local_seen = set() if is_table_like(line) else None

            def repl(m: re.Match) -> str:
                nonlocal total_replacements
                key = m.group('key')
                vis = m.group('vis')
                container = local_seen if local_seen is not None else seen_global
                if key in container:
                    total_replacements += 1
                    return vis  # remove tag, keep visible text
                container.add(key)
                return m.group(0)

            line = re.sub(
                r'\\gidx(?:\[[^\]]*])?{(?P<key>[A-Za-z0-9_-]+)}{(?P<vis>[^}]+)}',
                repl,
                line
            )
            new_lines.append(line)
        parts[i] = "\n".join(new_lines)

    if total_replacements:
        counts.inc(path, "paragraph_dedup_replacements", total_replacements)
    return "".join(parts)


def visible_word_collapse(text: str, counts: Counts, path: Path) -> str:
    total = 0
    for word, pattern in RE_VISIBLE_DUP_PATTERNS:
        new_text, n = pattern.subn(r'\1', text)
        if n:
            total += n
            text = new_text
    if total:
        counts.inc(path, "visible_word_collapses", total)
    return text


def process_file(path: Path, args, counts: Counts):
    try:
        original = path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"[WARN] Skipping {path}: {e}", file=sys.stderr)
        return

    counts.files_processed += 1
    text = original

    # Apply transformations in defined sequence
    text = flatten_nested(text, counts, path)
    text = collapse_immediate_identical(text, counts, path)
    text = collapse_immediate_variants(text, counts, path)
    text = paragraph_first_occurrence_dedup(text, counts, path)
    text = visible_word_collapse(text, counts, path)

    if text != original:
        counts.files_modified += 1
        if args.dry_run:
            print(f"[DRY-RUN] Would modify: {path}")
        else:
            if not args.no_backup:
                backup = path.with_suffix(path.suffix + ".bak")
                if not backup.exists():
                    backup.write_text(original, encoding='utf-8')
            path.write_text(text, encoding='utf-8')
            if args.verbose:
                print(f"[MODIFIED] {path}")


# ---------------------------------------------------------------------------
# CLI / Main
# ---------------------------------------------------------------------------

def collect_files(root: Path, include_glob: str, exclude_glob: str | None) -> List[Path]:
    files = sorted(root.rglob(include_glob))
    if exclude_glob:
        excluded = {p for p in root.rglob(exclude_glob)}
        files = [p for p in files if p not in excluded]
    return [p for p in files if p.is_file()]


def parse_args(argv: List[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Cleanup redundant / malformed \\gidx usage in LaTeX sources."
    )
    ap.add_argument(
        "--root",
        default="Chapters",
        help="Root directory to scan (default: Chapters)"
    )
    ap.add_argument(
        "--include-glob",
        default="*.tex",
        help="Glob for files to include relative to root (default: *.tex)"
    )
    ap.add_argument(
        "--exclude-glob",
        default=None,
        help="Glob for files to exclude"
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not modify files; just report."
    )
    ap.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose per-file modification messages."
    )
    ap.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create .bak backups (NOT recommended on first run)."
    )
    return ap.parse_args(argv)


def print_summary(counts: Counts, verbose: bool):
    print("\n=== Cleanup Summary ===")
    print(f"Files processed:                 {counts.files_processed}")
    print(f"Files modified:                  {counts.files_modified}")
    print(f"Nested instances flattened:      {counts.nested_flattened}")
    print(f"Immediate identical collapsed:   {counts.immediate_identical_collapsed}")
    print(f"Immediate variant collapsed:     {counts.immediate_variant_collapsed}")
    print(f"Paragraph duplicate removals:    {counts.paragraph_dedup_replacements}")
    print(f"Visible word collapses:          {counts.visible_word_collapses}")
    if verbose and counts.per_file_changes:
        print("\nPer-file change breakdown:")
        for p, data in sorted(counts.per_file_changes.items()):
            if any(v > 0 for v in data.values()):
                print(f"  {p}: " + ", ".join(f"{k}={v}" for k, v in data.items() if v))


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root)
    if not root.exists():
        print(f"[ERROR] Root path not found: {root}", file=sys.stderr)
        return 1

    files = collect_files(root, args.include_glob, args.exclude_glob)
    if args.verbose:
        print(f"[INFO] Found {len(files)} files matching pattern under {root}")

    counts = Counts()
    for f in files:
        process_file(f, args, counts)

    print_summary(counts, args.verbose)
    if args.dry_run:
        print("Dry run complete. No files were modified.")
    else:
        print("Cleanup complete.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        print("\nAborted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as ex:
        print(f"[FATAL] {ex}", file=sys.stderr)
        sys.exit(1)
