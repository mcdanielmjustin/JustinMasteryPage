#!/usr/bin/env python3
"""
narrow_eppp_fix.py — Remove ONLY phrases that claim to have EPPP test content.

This is the narrow version. It targets ONLY:
- "frequently tested on the EPPP" and variants
- "EPPP test content" (marketing disclosure)
- "EPPP-testable" (implies insider knowledge)

It does NOT touch:
- "EPPP Tip", "EPPP Distinction", "EPPP scenarios" (study guidance)
- "EPPP domains", "EPPP difficulty", "EPPP format" (exam descriptions)
- "the EPPP expects", "the EPPP rewards" (study advice)
- "EPPP preparation" (general prep language)
"""

import glob
import json
import os
import re
import sys

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

SKIP_FILES = {"CLAUDE.md", "README.md", "node_modules", ".git", "tools/"}

# NARROW replacements — only phrases that claim test content knowledge
NARROW_RULES = [
    # "tested on the EPPP" variants (implies knowing what's on the exam)
    (r"(?:This distinction is )?[Hh]eavily tested on the EPPP\.?", "This distinction is clinically important."),
    (r"[Tt]his is frequently tested on the EPPP\.?", "This is frequently tested."),
    (r"[Tt]ested on the EPPP", "frequently tested"),
    # "EPPP test content" (marketing claim about having exam content)
    (r"EPPP test content", "exam-focused content"),
    # "EPPP-testable" (implies insider knowledge)
    (r"EPPP-testable", "commonly tested"),
    # Fix the "distinctiin practice" artifacts from the April 14 commit
    (r"distinctiin practice", "distinction that exams"),
]


def should_skip(filepath):
    for skip in SKIP_FILES:
        if skip in filepath:
            return True
    return False


def process_file(filepath, dry_run=False):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original = f.read()
    except (UnicodeDecodeError, PermissionError):
        return False, []

    modified = original
    diffs = []
    for pattern, replacement in NARROW_RULES:
        new = re.sub(pattern, replacement, modified)
        if new != modified:
            diffs.append(f"  {pattern} → {replacement}")
            modified = new

    if modified == original:
        return False, []

    if not dry_run:
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.write(modified)

    return True, diffs


def main():
    dry_run = '--dry-run' in sys.argv
    verbose = '-v' in sys.argv
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    all_files = set()
    for pattern in CONTENT_GLOBS:
        all_files.update(glob.glob(pattern, recursive=True))

    files = sorted(f for f in all_files if not should_skip(f))
    print(f"Scanning {len(files)} files...")

    changed = 0
    total_replacements = 0
    for f in files:
        ok, diffs = process_file(f, dry_run)
        if ok:
            changed += 1
            total_replacements += len(diffs)
            prefix = "[DRY] " if dry_run else ""
            print(f"  {prefix}Fixed: {os.path.relpath(f)} ({len(diffs)} rules)")
            if verbose:
                for d in diffs:
                    print(f"    {d}")

    # Validate JSON
    if not dry_run:
        broken = 0
        for f in files:
            if f.endswith('.json'):
                try:
                    json.load(open(f, encoding='utf-8'))
                except json.JSONDecodeError as e:
                    print(f"  ** JSON BROKEN: {f}: {e}")
                    broken += 1
        if broken == 0:
            print("All JSON valid.")

    mode = "DRY RUN" if dry_run else "APPLIED"
    print(f"\n{mode}: {changed} files, {total_replacements} narrow replacements")


if __name__ == '__main__':
    main()
