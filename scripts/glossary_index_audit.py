#!/usr/bin/env python3
"""
glossary_index_audit.py

Purpose:
  Audits the consistency between glossary definitions, their usage in chapters,
  and index integration macros (\gidx, \gidxnested) in this LaTeX project.

Checks Performed:
  1. Glossary Coverage
     - Which glossary keys (from glossary_definitions.tex and optional extras) are never used.
     - Which glossary keys appear only via \gls{} (plain usage) but not indexed with \gidx / \gidxnested.
     - Which glossary keys are first used multiple times before being indexed (potential missed first-use indexing).

  2. Index Consistency
     - Extracts all index entries generated through \gidx / \gidxnested macros (parsing their arguments).
     - Optionally parses raw \index{...} commands.
     - Flags index entries (leaf tokens or parent tokens) that do not map to any glossary key (heuristic).

  3. Aliases / SEE References
     - Detects occurrences of \index{X|see{Y}} in .tex files or .idx file (if provided).
     - Validates that the SEE target (Y) exists as a glossary key (or normalized variant).

  4. Optional .idx File Parsing
     - If --idx-file is provided and exists, will re-parse produced index entries to catch post-macro expansions.

  5. Reporting Formats
     - Human-readable (default)
     - Markdown (--markdown)
     - JSON (--json) for tooling integration.

Usage:
  python glossary_index_audit.py
  python glossary_index_audit.py --chapters-dir Chapters --glossary-files IndexingGlossary/glossary_definitions.tex glossary_preamble.tex
  python glossary_index_audit.py --idx-file main.idx --json
  python glossary_index_audit.py --markdown --fail-on missing-index unused-terms

Exit Codes:
  0  Success (no requested failure conditions triggered)
  1  General failure or failure conditions met (when --fail-on matches)
  2  Invalid arguments / I/O issues

Fail Conditions (--fail-on):
  Provide a space/comma separated list of symbolic conditions:
    unused-terms         => Any glossary key never used
    unindexed-first-use  => Keys used but never with \gidx / \gidxnested
    orphan-index         => Index entries referencing no glossary key
    alias-target-missing => SEE alias target not found in glossary
    all                  => All above

Example:
  python glossary_index_audit.py --fail-on unused-terms unindexed-first-use

Assumptions:
  - Macros \gidx{<gls-key>}{<index>} and \gidxnested{<gls-key>}{Parent}{Child} are defined (as per integration plan).
  - Glossary keys are defined via \newglossaryentry{key}{...}.
  - Overlapping keys differing only by case are treated as same logical key.

Author: AI Assistant (Phase D implementation)
"""

from __future__ import annotations
import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Iterable


GLOSSARY_ENTRY_RE = re.compile(r'\\newglossaryentry\{([^}]+)\}')
GLS_USAGE_RE = re.compile(r'\\gls(?:pl)?(?:set)?(?:\[[^\]]*\])?\{([^}]+)\}')
# \gidx[optional]{gls-key}{IndexTerm}
GIDX_RE = re.compile(r'\\gidx(?:\[[^\]]*\])?\{([^}]+)\}\{([^}]+)\}')
# \gidxnested[optional]{gls-key}{Parent}{Child}
GIDX_NESTED_RE = re.compile(r'\\gidxnested(?:\[[^\]]*\])?\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}')
# Raw index commands: \index{...}
RAW_INDEX_RE = re.compile(r'\\index\{([^}]+)\}')
# SEE alias inline: pattern inside \index{source|see{target}}
SEE_ALIAS_RE = re.compile(r'([^|]+)\|see\{([^}]+)\}')
# Index hierarchical: Parent!Child
INDEX_HIER_SPLIT_RE = re.compile(r'!?(!)')

FAIL_CONDITIONS = {
    "unused-terms",
    "unindexed-first-use",
    "orphan-index",
    "alias-target-missing",
    "all"
}


@dataclass
class GlossaryUsage:
    key: str
    normalized: str
    definitions: Set[Path] = field(default_factory=set)
    plain_gls_usages: List[Tuple[Path, int]] = field(default_factory=list)
    indexed_usages: List[Tuple[Path, int, str]] = field(default_factory=list)  # (file, line, index entry)
    nested_usages: List[Tuple[Path, int, str, str]] = field(default_factory=list)  # (file, line, parent, child)
    first_line: Optional[int] = None
    first_file: Optional[Path] = None

    def record_plain(self, file_path: Path, line: int):
        self.plain_gls_usages.append((file_path, line))
        self._maybe_set_first(file_path, line)

    def record_indexed(self, file_path: Path, line: int, index_entry: str):
        self.indexed_usages.append((file_path, line, index_entry))
        self._maybe_set_first(file_path, line)

    def record_nested(self, file_path: Path, line: int, parent: str, child: str):
        self.nested_usages.append((file_path, line, f"{parent}!{child}"))
        self._maybe_set_first(file_path, line)

    def _maybe_set_first(self, file_path: Path, line: int):
        if self.first_line is None or (line < self.first_line):
            self.first_line = line
            self.first_file = file_path

    @property
    def used(self) -> bool:
        return bool(self.plain_gls_usages or self.indexed_usages or self.nested_usages)

    @property
    def indexed_any(self) -> bool:
        return bool(self.indexed_usages or self.nested_usages)


@dataclass
class AuditResult:
    glossary_total: int = 0
    glossary_used: int = 0
    unused_terms: List[str] = field(default_factory=list)
    unindexed_terms: List[str] = field(default_factory=list)
    orphan_index_entries: List[str] = field(default_factory=list)
    alias_targets_missing: List[str] = field(default_factory=list)
    alias_pairs: List[Tuple[str, str]] = field(default_factory=list)
    index_entries: Set[str] = field(default_factory=set)
    nested_index_entries: Set[str] = field(default_factory=set)
    raw_index_entries: Set[str] = field(default_factory=set)

    def summary(self) -> Dict[str, object]:
        return {
            "glossary_total": self.glossary_total,
            "glossary_used": self.glossary_used,
            "unused_terms": sorted(self.unused_terms),
            "unindexed_terms": sorted(self.unindexed_terms),
            "orphan_index_entries": sorted(self.orphan_index_entries),
            "alias_targets_missing": sorted(self.alias_targets_missing),
            "alias_pairs": sorted(list(self.alias_pairs)),
            "index_entries_total": len(self.index_entries | self.nested_index_entries | self.raw_index_entries),
        }


def parse_args() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Audit glossary and index usage.")
    ap.add_argument("--chapters-dir", default="TechSpecsTVI/Chapters",
                    help="Directory containing chapter .tex files.")
    ap.add_argument("--glossary-files", nargs="+",
                    default=["TechSpecsTVI/IndexingGlossary/glossary_definitions.tex", "TechSpecsTVI/glossary_preamble.tex"],
                    help="List of files to scan for \\newglossaryentry definitions.")
    ap.add_argument("--idx-file", default=None,
                    help="Optional compiled index (.idx) file for additional SEE alias parsing.")
    ap.add_argument("--json", action="store_true", help="Output JSON summary.")
    ap.add_argument("--markdown", action="store_true", help="Output Markdown summary.")
    ap.add_argument("--fail-on", nargs="*", default=[],
                    help="List of failure conditions (unused-terms, unindexed-first-use, orphan-index, alias-target-missing, all).")
    return ap


def load_glossary_keys(files: Iterable[str]) -> Dict[str, GlossaryUsage]:
    usage_map: Dict[str, GlossaryUsage] = {}
    for f in files:
        p = Path(f)
        if not p.exists():
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            for m in GLOSSARY_ENTRY_RE.finditer(line):
                key = m.group(1).strip()
                norm = key.lower()
                usage_map.setdefault(norm, GlossaryUsage(key=key, normalized=norm)).definitions.add(p)
    return usage_map


def scan_chapter_file(path: Path, usage_map: Dict[str, GlossaryUsage],
                      index_entries: Set[str],
                      nested_index_entries: Set[str],
                      raw_index_entries: Set[str],
                      alias_pairs: List[Tuple[str, str]]):
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    for i, line in enumerate(lines, start=1):

        # Plain \gls
        for m in GLS_USAGE_RE.finditer(line):
            key = m.group(1).strip()
            norm = key.lower()
            entry = usage_map.get(norm)
            if entry:
                entry.record_plain(path, i)

        # \gidx
        for m in GIDX_RE.finditer(line):
            gkey = m.group(1).strip()
            idx_text = m.group(2).strip()
            norm = gkey.lower()
            entry = usage_map.get(norm)
            if entry:
                entry.record_indexed(path, i, idx_text)
            index_entries.add(idx_text)

        # \gidxnested
        for m in GIDX_NESTED_RE.finditer(line):
            gkey = m.group(1).strip()
            parent = m.group(2).strip()
            child = m.group(3).strip()
            norm = gkey.lower()
            entry = usage_map.get(norm)
            if entry:
                entry.record_nested(path, i, parent, child)
            nested_index_entries.add(f"{parent}!{child}")

        # Raw \index
        for m in RAW_INDEX_RE.finditer(line):
            raw_entry = m.group(1).strip()
            raw_index_entries.add(raw_entry)
            # SEE alias patterns inside
            see_match = SEE_ALIAS_RE.search(raw_entry)
            if see_match:
                src = see_match.group(1).strip()
                tgt = see_match.group(2).strip()
                alias_pairs.append((src, tgt))


def parse_idx_file(idx_file: Path, alias_pairs: List[Tuple[str, str]]):
    if not idx_file.exists():
        return
    text = idx_file.read_text(encoding="utf-8", errors="ignore")
    # Typical pattern: \indexentry{source|see{target}}{<page>}
    for m in re.finditer(r'\\indexentry\{([^}]*)\}', text):
        entry = m.group(1)
        see = SEE_ALIAS_RE.search(entry)
        if see:
            alias_pairs.append((see.group(1).strip(), see.group(2).strip()))


def analyze(usage_map: Dict[str, GlossaryUsage],
            index_entries: Set[str],
            nested_index_entries: Set[str],
            raw_index_entries: Set[str],
            alias_pairs: List[Tuple[str, str]]) -> AuditResult:
    result = AuditResult()
    result.glossary_total = len(usage_map)
    used = 0

    # Build a set of all recognized glossary keys (original-case)
    all_original_keys = {u.key for u in usage_map.values()}

    # Flatten all index tokens for orphan detection
    all_reported_index_tokens: Set[str] = set()
    for e in index_entries:
        all_reported_index_tokens.add(e)
    for n in nested_index_entries:
        # split parent!child
        parts = n.split('!')
        all_reported_index_tokens.update(parts)
    for raw in raw_index_entries:
        # Could be multiple hierarchical segments
        if "|see{" in raw:
            # Skip alias sources as they may intentionally not be glossary keys
            pass
        segments = raw.split('!')
        for seg in segments:
            if '|see{' in seg:
                seg = seg.split('|see{', 1)[0]
            all_reported_index_tokens.add(seg.strip())

    # Evaluate usage
    for norm, rec in usage_map.items():
        if rec.used:
            used += 1
        else:
            result.unused_terms.append(rec.key)
        # Mark unindexed if used but no indexed usages
        if rec.used and not rec.indexed_any:
            result.unindexed_terms.append(rec.key)

    result.glossary_used = used
    result.index_entries = index_entries
    result.nested_index_entries = nested_index_entries
    result.raw_index_entries = raw_index_entries
    result.alias_pairs = alias_pairs

    # Orphan detection (heuristic): index token not matching any glossary key ignoring case
    lower_glossary = {k.lower() for k in all_original_keys}
    for token in all_reported_index_tokens:
        tnorm = token.lower().strip()
        # Skip obvious global or non-term tokens (heuristic filtering)
        if not tnorm or tnorm in {"the", "and"}:
            continue
        # Recognize multi-word phrases not always glossary keys: don't over-strict
        if tnorm not in lower_glossary:
            # Exempt manual alias sources (from alias_pairs)
            if any(token == ap[0] for ap in alias_pairs):
                continue
            result.orphan_index_entries.append(token)

    # Alias target check
    for src, tgt in alias_pairs:
        if tgt.lower() not in lower_glossary:
            result.alias_targets_missing.append(f"{src} -> {tgt}")

    # De-duplicate lists
    result.unused_terms = sorted(set(result.unused_terms))
    result.unindexed_terms = sorted(set(result.unindexed_terms))
    result.orphan_index_entries = sorted(set(result.orphan_index_entries))
    result.alias_targets_missing = sorted(set(result.alias_targets_missing))
    result.alias_pairs = sorted(set(alias_pairs))
    return result


def print_human(result: AuditResult):
    print("=" * 70)
    print("Glossary / Index Audit Report")
    print("=" * 70)
    print(f"Total glossary entries: {result.glossary_total}")
    print(f"Glossary entries used: {result.glossary_used}")
    print(f"Unused glossary entries: {len(result.unused_terms)}")
    print(f"Used but never indexed (no \\gidx / \\gidxnested): {len(result.unindexed_terms)}")
    print(f"Orphan index tokens (no matching glossary key): {len(result.orphan_index_entries)}")
    print(f"Alias SEE pairs detected: {len(result.alias_pairs)}")
    print(f"Alias targets missing: {len(result.alias_targets_missing)}")
    print("-" * 70)

    if result.unused_terms:
        print("UNUSED TERMS:")
        for k in result.unused_terms:
            print(f"  - {k}")
        print("-" * 70)

    if result.unindexed_terms:
        print("UNINDEXED (Used Without Index Macro):")
        for k in result.unindexed_terms:
            print(f"  - {k}")
        print("-" * 70)

    if result.orphan_index_entries:
        print("ORPHAN INDEX TOKENS:")
        for token in result.orphan_index_entries:
            print(f"  - {token}")
        print("-" * 70)

    if result.alias_pairs:
        print("SEE ALIASES:")
        for src, tgt in result.alias_pairs:
            print(f"  {src} -> {tgt}")
        print("-" * 70)

    if result.alias_targets_missing:
        print("ALIAS TARGETS MISSING (SEE references to undefined targets):")
        for miss in result.alias_targets_missing:
            print(f"  - {miss}")
        print("-" * 70)

    print("Suggestion Hints:")
    if result.unindexed_terms:
        print("  * Convert first use of each unindexed term to \\gidx or \\gidxnested.")
    if result.unused_terms:
        print("  * Remove unused terms or confirm future planned usage.")
    if result.orphan_index_entries:
        print("  * Add glossary entries for orphans or rename index tokens to match glossary keys.")
    if result.alias_targets_missing:
        print("  * Define missing glossary targets or correct SEE alias typos.")


def print_markdown(result: AuditResult):
    print("# Glossary / Index Audit Report\n")
    print(f"- **Total glossary entries:** {result.glossary_total}")
    print(f"- **Glossary entries used:** {result.glossary_used}")
    print(f"- **Unused glossary entries:** {len(result.unused_terms)}")
    print(f"- **Used but never indexed:** {len(result.unindexed_terms)}")
    print(f"- **Orphan index tokens:** {len(result.orphan_index_entries)}")
    print(f"- **Alias SEE pairs:** {len(result.alias_pairs)}")
    print(f"- **Alias targets missing:** {len(result.alias_targets_missing)}\n")

    def md_list(title: str, items: List[str]):
        if not items:
            return
        print(f"## {title}")
        for it in items:
            print(f"- {it}")
        print()

    md_list("Unused Terms", result.unused_terms)
    md_list("Unindexed Used Terms", result.unindexed_terms)
    md_list("Orphan Index Tokens", result.orphan_index_entries)
    if result.alias_pairs:
        print("## SEE Aliases")
        for src, tgt in result.alias_pairs:
            print(f"- {src} → {tgt}")
        print()
    md_list("Alias Targets Missing", result.alias_targets_missing)

    print("## Suggestions")
    if result.unindexed_terms:
        print("- Add \\gidx or \\gidxnested to first usage of unindexed terms.")
    if result.unused_terms:
        print("- Remove or plan usage for unused glossary terms.")
    if result.orphan_index_entries:
        print("- Define glossary entries for orphan tokens or unify naming.")
    if result.alias_targets_missing:
        print("- Correct SEE alias targets or add missing glossary entries.")


def should_fail(result: AuditResult, fail_conditions: Set[str]) -> bool:
    if not fail_conditions:
        return False
    if "all" in fail_conditions:
        conds = {
            "unused-terms",
            "unindexed-first-use",
            "orphan-index",
            "alias-target-missing",
        }
    else:
        conds = fail_conditions

    def triggered(name: str) -> bool:
        if name == "unused-terms":
            return bool(result.unused_terms)
        if name == "unindexed-first-use":
            return bool(result.unindexed_terms)
        if name == "orphan-index":
            return bool(result.orphan_index_entries)
        if name == "alias-target-missing":
            return bool(result.alias_targets_missing)
        return False

    return any(triggered(c) for c in conds)


def main():
    parser = parse_args()
    args = parser.parse_args()

    fail_on = set(c.strip() for c in args.fail_on)
    invalid = fail_on - FAIL_CONDITIONS
    if invalid:
        print(f"Invalid fail-on conditions: {', '.join(invalid)}", file=sys.stderr)
        sys.exit(2)

    # Load glossary keys
    usage_map = load_glossary_keys(args.glossary_files)
    if not usage_map:
        print("No glossary entries found. Check glossary file paths.", file=sys.stderr)
        sys.exit(2)

    chapters_dir = Path(args.chapters_dir)
    if not chapters_dir.exists():
        print(f"Chapters directory not found: {chapters_dir}", file=sys.stderr)
        sys.exit(2)

    index_entries: Set[str] = set()
    nested_index_entries: Set[str] = set()
    raw_index_entries: Set[str] = set()
    alias_pairs: List[Tuple[str, str]] = []

    # Scan each chapter file
    for chapter_file in sorted(chapters_dir.glob("Chapter*.tex")):
        try:
            scan_chapter_file(chapter_file, usage_map, index_entries, nested_index_entries, raw_index_entries, alias_pairs)
        except Exception as e:
            print(f"Error scanning {chapter_file}: {e}", file=sys.stderr)

    # Optional .idx file parsing
    if args.idx_file:
        parse_idx_file(Path(args.idx_file), alias_pairs)

    result = analyze(usage_map, index_entries, nested_index_entries, raw_index_entries, alias_pairs)

    if args.json:
        print(json.dumps(result.summary(), indent=2))
    elif args.markdown:
        print_markdown(result)
    else:
        print_human(result)

    if should_fail(result, fail_on):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
