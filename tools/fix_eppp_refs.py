#!/usr/bin/env python3
"""
fix_eppp_refs.py — Remove EPPP exam name from content files.

Applies ordered regex replacements to HTML/JSON/JS content files.
Handles sentence-start capitalization and protects the brand name "PassEPPP".

Usage:
    python tools/fix_eppp_refs.py --dry-run          # preview changes
    python tools/fix_eppp_refs.py                     # apply changes
    python tools/fix_eppp_refs.py --cleanup-only      # only fix artifacts from previous commit
"""

import argparse
import glob
import json
import os
import re
import sys

# ── Directories to process ────────────────────────────────────────────────
CONTENT_GLOBS = [
    "content/**/*.html",
    "content/**/*.json",
    "content/enrichment/*.json",
    "content/enrichment/*.js",
    "content/lecture-topics.json",
    "content/section-registry.json",
    "pages/mastery/content/**/*.html",
    "pages/mastery/content/**/*.json",
    "pages/mastery/data/*.json",
    "pages/mastery/data/*.js",
    "pages/mastery/data/*.sql",
    "pages/mastery/data/_archive/*.json",
    "pages/mastery/data/_archive/*.js",
    "js/quiz-data/*.js",
    "js/va-data/*.js",
    "js/flashcards-data.js",
    "scripts/**/*.json",
    "scripts/**/*.js",
    "scripts/**/*.sql",
    "scripts/**/*.md",
    "sql/*.sql",
    "pages/practice.html",
    "pages/strategies.html",
    "pages/textbook-v2-viewer.html",
    "index.html",
    "membership.html",
    "_archived/*.html",
]

# Files to never touch
SKIP_FILES = {
    "CLAUDE.md", "README.md", "package.json", "package-lock.json",
    "node_modules", ".git", "tools/fix_eppp_refs.py",
}

# ── Replacement rules (order matters — longest/most-specific first) ───────
# Each tuple: (pattern, replacement)
# Patterns are case-sensitive regex. Use (?i) for case-insensitive.
EPPP_REPLACEMENTS = [
    # Specific multi-word phrases first
    (r"The EPPP frequently tests", "Exams frequently test"),
    (r"the EPPP frequently tests", "exams frequently test"),
    (r"EPPP frequently tests", "exams frequently test"),
    (r"The EPPP tests", "Licensing exams test"),
    (r"the EPPP tests", "licensing exams test"),
    (r"A common EPPP trap", "A common exam trap"),
    (r"a common EPPP trap", "a common exam trap"),
    (r"common EPPP trap", "common exam trap"),
    (r"EPPP trap", "exam trap"),
    (r"EPPP Distinction", "Key Distinction"),
    (r"EPPP distinction", "key distinction"),
    (r"high-yield EPPP fact", "high-yield fact"),
    (r"High-Yield EPPP fact", "high-yield fact"),
    (r"high-yield EPPP", "high-yield exam"),
    (r"High-Yield EPPP", "high-yield exam"),
    (r"High-Yield fact", "high-yield fact"),
    (r"EPPP question", "exam question"),
    (r"EPPP-relevant", "exam-relevant"),
    (r"EPPP preparation journey", "exam preparation journey"),
    (r"EPPP preparation", "exam preparation"),
    (r"EPPP test content", "exam-focused content"),
    (r"EPPP differential diagnos", "key differential diagnos"),
    (r"EPPP pharmacology", "pharmacology"),
    (r"EPPP content", "exam content"),
    (r"EPPP exam", "licensing exam"),
    # "tested on the EPPP" variants (should be mostly gone from previous commit)
    (r"tested on the EPPP", "frequently tested on licensing exams"),
    (r"heavily tested on the EPPP", "heavily tested on licensing exams"),
    (r"frequently tested EPPP", "frequently tested exam"),
    (r"high-frequency EPPP topic", "high-frequency exam topic"),
    (r"high-frequency EPPP", "high-frequency exam"),
    # Positional phrases
    (r"[Oo]n the EPPP,", "On licensing exams,"),
    (r"[Oo]n the EPPP\.", "on licensing exams."),
    (r"[Oo]n the EPPP ", "on licensing exams "),
    (r"[Ff]or the EPPP,", "for licensing exams,"),
    (r"[Ff]or the EPPP\.", "for licensing exams."),
    (r"[Ff]or the EPPP ", "for licensing exams "),
    (r"[Ff]or EPPP purposes", "for exam purposes"),
    (r"(?<!\w)the EPPP itself", "the licensing exam itself"),
    (r"(?<!\w)the EPPP(?![\w-])", "the licensing exam"),
    (r"(?<!\w)The EPPP(?![\w-])", "The licensing exam"),
    # Standalone "EPPP" that isn't part of "PassEPPP" or a compound
    # This is the broadest catch-all — applied last
    (r"(?<!Pass)(?<![\w-])EPPP(?![\w-])", "licensing exam"),
]

# ── Artifact cleanup from previous commit ─────────────────────────────────
ARTIFACT_FIXES = [
    # Fix "High-Yield" mid-sentence (but not at start of sentence or in headings)
    (r'(?<=[a-z,;] )High-Yield(?= )', "high-yield"),
    # Fix lowercase "in practice" at sentence starts (after . or >)
    (r'(?<=\. )in practice', "In practice"),
    (r'(?<=>)in practice', "In practice"),
    # Fix "one of the most" at sentence starts
    (r'(?<=\. )one of the most', "One of the most"),
    (r'(?<=>)one of the most', "One of the most"),
]


def should_skip(filepath):
    """Check if file should be skipped."""
    for skip in SKIP_FILES:
        if skip in filepath:
            return True
    return False


def apply_replacements(text, rules):
    """Apply ordered replacement rules to text."""
    for pattern, replacement in rules:
        text = re.sub(pattern, replacement, text)
    return text


def fix_sentence_caps(text):
    """Fix capitalization at sentence boundaries after replacements."""
    # After ". " or ".\n" or "> ", ensure next char is uppercase
    def cap_after_period(m):
        return m.group(0)[:-1] + m.group(0)[-1].upper()
    # Fix lowercase after period-space at sentence boundary
    text = re.sub(r'\. [a-z]', cap_after_period, text)
    return text


def process_file(filepath, dry_run=False, cleanup_only=False):
    """Process a single file. Returns (changed, diff_lines)."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original = f.read()
    except (UnicodeDecodeError, PermissionError):
        return False, []

    # Skip if file contains no EPPP references and no artifacts
    if not cleanup_only and 'EPPP' not in original and 'High-Yield' not in original and 'in practice' not in original:
        return False, []
    if cleanup_only and 'High-Yield' not in original and 'in practice' not in original and 'one of the most' not in original:
        return False, []

    # Skip lines with PassEPPP brand name — process line by line
    lines = original.split('\n')
    new_lines = []
    diff_lines = []

    for i, line in enumerate(lines, 1):
        new_line = line

        if not cleanup_only:
            # Apply EPPP replacements (skip lines with PassEPPP brand)
            if 'EPPP' in line and 'PassEPPP' not in line:
                new_line = apply_replacements(new_line, EPPP_REPLACEMENTS)

        # Apply artifact fixes regardless
        new_line = apply_replacements(new_line, ARTIFACT_FIXES)

        if new_line != line:
            diff_lines.append(f"  L{i}: - {line.strip()[:120]}")
            diff_lines.append(f"  L{i}: + {new_line.strip()[:120]}")

        new_lines.append(new_line)

    modified = '\n'.join(new_lines)

    if modified == original:
        return False, []

    if not dry_run:
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.write(modified)

    return True, diff_lines


def validate_json(filepath):
    """Validate a JSON file parses correctly."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            json.load(f)
        return True
    except json.JSONDecodeError as e:
        return str(e)


def main():
    parser = argparse.ArgumentParser(description='Fix EPPP references in content files')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing')
    parser.add_argument('--cleanup-only', action='store_true', help='Only fix artifacts from previous commit')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show per-line diffs')
    args = parser.parse_args()

    # Collect all matching files
    all_files = set()
    for pattern in CONTENT_GLOBS:
        all_files.update(glob.glob(pattern, recursive=True))

    # Filter
    files = sorted(f for f in all_files if not should_skip(f))
    print(f"Scanning {len(files)} files...")

    changed_count = 0
    total_diffs = 0
    broken_json = []

    for filepath in files:
        changed, diffs = process_file(filepath, dry_run=args.dry_run, cleanup_only=args.cleanup_only)
        if changed:
            changed_count += 1
            total_diffs += len(diffs) // 2
            rel = os.path.relpath(filepath)
            print(f"  {'[DRY] ' if args.dry_run else ''}Changed: {rel} ({len(diffs)//2} replacements)")
            if args.verbose:
                for d in diffs:
                    print(f"    {d}")

            # Validate JSON files after modification
            if not args.dry_run and filepath.endswith('.json'):
                result = validate_json(filepath)
                if result is not True:
                    broken_json.append((filepath, result))
                    print(f"  ** JSON BROKEN: {filepath}: {result}")

    mode = "DRY RUN" if args.dry_run else "APPLIED"
    print(f"\n{mode}: {changed_count} files, {total_diffs} replacements")

    if broken_json:
        print(f"\n** WARNING: {len(broken_json)} JSON files failed validation:")
        for f, e in broken_json:
            print(f"  {f}: {e}")
        sys.exit(1)

    # Final EPPP count check
    if not args.dry_run and not args.cleanup_only:
        remaining = 0
        for filepath in files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Count EPPP not in PassEPPP
                hits = len(re.findall(r'(?<!Pass)(?<![\w-])EPPP(?![\w-])', content))
                if hits:
                    remaining += hits
                    print(f"  Remaining: {os.path.relpath(filepath)} ({hits})")
            except:
                pass
        print(f"\nRemaining EPPP references (excluding PassEPPP): {remaining}")


if __name__ == '__main__':
    # Fix Windows cp1252 stdout encoding
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    main()
