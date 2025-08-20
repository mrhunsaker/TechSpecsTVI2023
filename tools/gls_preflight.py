#!/usr/bin/env python3
"""
gls_preflight.py

Preflight scanner for LaTeX projects using glossaries / glossaries-extra.
Reports potentially problematic \gls{...} usages so you can normalize before build.

Checks performed:
  1. Spaced keys: \gls{Braille Ready Format}  (glossary keys must not contain spaces)
  2. Uppercase / CamelCase keys (e.g., \gls{AI}, \gls{MusicXML}) intended to move toward lowercase canonical keys.
  3. Undefined keys (used but not found in loaded glossary definition files).
  4. Alias recommendation: suggests alias= approach or direct replacement with lowercase.
  5. Optional auto-fix (case normalization only) with --fix-case flag.

Exit codes:
  0 = no issues
  1 = issues found (or fixes applied that changed files)
  2 = fatal error (bad arguments, missing root, etc.)

Usage examples:
  python tools/gls_preflight.py
  python tools/gls_preflight.py --root Chapters
  python tools/gls_preflight.py --include '**/*.tex' --exclude 'IndexingGlossary/*.tex'
  python tools/gls_preflight.py --fix-case

Auto-fix behavior (--fix-case):
  - For each \gls{Key} whose lowercase version (key.lower()) is defined and Key != key.lower(), replaces
    \gls{Key} with \gls{key.lower()} in source files.
  - Does NOT fix spaced keys (reported only).
  - Creates a .bak backup before modifying a file (unless --no-backup).

Limitations:
  - Heuristic regex scanning; does not parse TeX fully.
  - Assumes glossary definition keys are provided via \newglossaryentry{key}{...}.
  - Does not modify alias definitions; only usage sites.
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple


GLOS_ENTRY_RE = re.compile(r'\\newglossaryentry\{([^}]+)\}')
GLS_USE_RE    = re.compile(r'\\gls(?:\[[^\]]*\])?\{([^}]+)\}')
# Simpler \gidx pattern if needed for future extension:
GIDX_USE_RE   = re.compile(r'\\gidx(?:\[[^\]]*\])?\{([^}]+)\}\{([^}]+)\}')

# Keys we intentionally allow to be uppercase (acronyms) even if normalization planned.
# You can extend or empty this list depending on policy.
UPPER_ALLOWED = {
    # If you prefer all lowercase, empty this set.
    # 'OCR', 'CPU', 'API', 'PDF/UA'
}

@dataclass
class Issue:
    category: str
    key: str
    file: Path
    line_no: int
    line: str

@dataclass
class ScanReport:
    spaced: List[Issue] = field(default_factory=list)
    uppercase: List[Issue] = field(default_factory=list)
    undefined: List[Issue] = field(default_factory=list)
    fixed: int = 0
    files_modified: int = 0


def collect_defined_keys(def_files: List[Path]) -> Set[str]:
    keys: Set[str] = set()
    for f in def_files:
        try:
            text = f.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        for m in GLOS_ENTRY_RE.finditer(text):
            keys.add(m.group(1))
    return keys


def find_tex_files(root: Path, include_glob: str, exclude_patterns: List[str]) -> List[Path]:
    results: List[Path] = []
    for p in root.rglob('*'):
        if not p.is_file():
            continue
        rel = str(p.relative_to(root))
        if not fnmatch.fnmatch(rel, include_glob):
            continue
        excluded = any(fnmatch.fnmatch(rel, pat) for pat in exclude_patterns)
        if excluded:
            continue
        results.append(p)
    return sorted(results)


def scan_file(path: Path,
              defined: Set[str],
              report: ScanReport,
              normalize_case: bool,
              create_backup: bool) -> None:
    try:
        original = path.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        print(f"[WARN] Could not read {path}: {e}", file=sys.stderr)
        return

    modified = original
    lines = original.splitlines()
    made_change = False

    for idx, line in enumerate(lines, start=1):
        for m in GLS_USE_RE.finditer(line):
            key = m.group(1)
            # Skip empty or macro expansions inside braces
            if not key.strip():
                continue

            # 1. Spaced key
            if any(c.isspace() for c in key):
                report.spaced.append(Issue('spaced', key, path, idx, line))
                continue

            # 2. Uppercase / CamelCase (first char uppercase or contains uppercase beyond typical)
            if (key != key.lower()) and (key not in UPPER_ALLOWED):
                report.uppercase.append(Issue('uppercase', key, path, idx, line))
                if normalize_case:
                    lower_key = key.lower()
                    if lower_key in defined:
                        # Replace this occurrence only; careful not to alter other same-key uses on line multiple times
                        # Build a precise pattern for this match occurrence using span.
                        span = m.span(1)  # only the key part
                        # Apply replacement in the 'modified' master string; adjust offset for prior changes.
                        # Simpler approach: run a re.sub on whole file only after collecting replacements.
                        # We'll record a placeholder and do a second pass.
                        pass
            # 3. Undefined
            if key not in defined:
                # If we already flagged as spaced or uppercase, still record undefined separately.
                report.undefined.append(Issue('undefined', key, path, idx, line))

    # Second pass for case normalization if requested
    if normalize_case:
        # Replace only \gls{Key} -> \gls{key} where lowercase defined
        def repl_case(match: re.Match) -> str:
            k = match.group(1)
            if (k != k.lower()) and (k.lower() in defined) and (k not in UPPER_ALLOWED):
                new = k.lower()
                nonlocal made_change
                made_change = True
                report.fixed += 1
                return match.group(0).replace(k, new, 1)
            return match.group(0)

        modified = GLS_USE_RE.sub(repl_case, modified)

    if made_change:
        if create_backup:
            backup = path.with_suffix(path.suffix + '.bak')
            if not backup.exists():
                try:
                    backup.write_text(original, encoding='utf-8')
                except Exception as e:
                    print(f"[WARN] Could not create backup for {path}: {e}", file=sys.stderr)
        try:
            path.write_text(modified, encoding='utf-8')
            report.files_modified += 1
        except Exception as e:
            print(f"[ERROR] Failed writing modified file {path}: {e}", file=sys.stderr)


def summarize(report: ScanReport, verbose: bool) -> int:
    def header(title: str):
        print("\n" + title)
        print("-" * len(title))

    issues_found = any([report.spaced, report.uppercase, report.undefined])

    if report.spaced:
        header("Spaced Glossary Keys (INVALID - must rename or alias)")
        for i in report.spaced:
            print(f"{i.file}:{i.line_no}: \\gls{{{i.key}}}")
        print("Suggestion: replace uses with a canonical key (e.g. BrailleReadyFormat) and add alias entry if needed:")
        print(r"  \newglossaryentry{BrailleReadyFormat}{alias=brf,name={Braille Ready Format},description={}}")

    if report.uppercase:
        header("Uppercase / CamelCase Keys (candidates for normalization)")
        for i in report.uppercase:
            print(f"{i.file}:{i.line_no}: \\gls{{{i.key}}}")
        print("Suggestion: either:")
        print("  (a) convert usage to lowercase if canonical entry exists (preferred long-term), or")
        print("  (b) provide alias entries: \\newglossaryentry{Key}{alias=key,name={Key},description={}}")

    if report.undefined:
        header("Undefined Keys (used but not defined)")
        for i in report.undefined:
            print(f"{i.file}:{i.line_no}: \\gls{{{i.key}}}")
        print("Action: add \\newglossaryentry or an alias, OR correct the key spelling.")

    if report.fixed:
        header("Automatic Case Normalization Applied")
        print(f"Occurrences converted: {report.fixed}")
        print(f"Files modified: {report.files_modified}")

    if not issues_found and not report.fixed:
        print("No glossary key issues detected.")

    # Exit code: 1 if issues found or modifications done; otherwise 0
    return 1 if (issues_found or report.fixed) else 0


def parse_args(argv: List[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Preflight scan for \\gls{...} key normalization.")
    ap.add_argument("--root", default=".", help="Project root (default: current dir).")
    ap.add_argument("--include", default="*.tex",
                    help="Glob (relative to root) for files to include (default: *.tex)")
    ap.add_argument("--exclude", action="append", default=[],
                    help="Glob(s) to exclude (can repeat). Example: --exclude 'IndexingGlossary/*.tex'")
    ap.add_argument("--defs", action="append", default=[
        "IndexingGlossary/glossary_definitions.tex"
    ], help="Glossary definition file(s) relative to root (can repeat).")
    ap.add_argument("--fix-case", action="store_true",
                    help="Automatically convert \\gls{Key} to lowercase if lowercase variant is defined.")
    ap.add_argument("--no-backup", action="store_true",
                    help="Do not create .bak backups for modified files.")
    ap.add_argument("-v", "--verbose", action="store_true")
    return ap.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if not root.exists():
        print(f"[ERROR] Root path does not exist: {root}", file=sys.stderr)
        return 2

    # Collect defined glossary keys
    def_files = [root / d for d in args.defs]
    defined = collect_defined_keys(def_files)

    if args.verbose:
        print(f"[INFO] Loaded {len(defined)} defined glossary keys from {len(def_files)} file(s).")

    tex_files = find_tex_files(root, args.include, args.exclude)
    if args.verbose:
        print(f"[INFO] Scanning {len(tex_files)} file(s).")

    report = ScanReport()
    for f in tex_files:
        scan_file(f, defined, report, normalize_case=args.fix_case, create_backup=not args.no_backup)

    return summarize(report, args.verbose)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
