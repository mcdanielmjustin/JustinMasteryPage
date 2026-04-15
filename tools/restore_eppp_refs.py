#!/usr/bin/env python3
"""
restore_eppp_refs.py — Restore EPPP references that were over-corrected.

Step 1 of revert-and-redo: puts "EPPP" back everywhere it was changed to
"licensing exam" / "exam" / etc. Then a narrow script re-removes only the
specific disclosure phrases.
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

# Reverse the over-broad replacements (order matters — longest first)
RESTORE_RULES = [
    # Restore compound phrases
    ("Exams frequently test", "The EPPP frequently tests"),
    ("exams frequently test", "the EPPP frequently tests"),
    ("Licensing exams test", "The EPPP tests"),
    ("licensing exams test", "the EPPP tests"),
    ("common exam trap", "common EPPP trap"),
    ("exam trap", "EPPP trap"),
    ("Key Distinction", "EPPP Distinction"),
    ("key distinction", "EPPP distinction"),
    ("high-yield exam", "high-yield EPPP"),
    ("high-yield fact", "high-yield EPPP fact"),
    ("exam question", "EPPP question"),
    ("exam-relevant", "EPPP-relevant"),
    ("exam preparation journey", "EPPP preparation journey"),
    ("exam preparation", "EPPP preparation"),
    ("exam-focused content", "EPPP test content"),
    ("key differential diagnos", "EPPP differential diagnos"),
    ("frequently tested on licensing exams", "tested on the EPPP"),
    ("heavily tested on licensing exams", "heavily tested on the EPPP"),
    ("frequently tested exam", "frequently tested EPPP"),
    ("high-frequency exam topic", "high-frequency EPPP topic"),
    ("high-frequency exam", "high-frequency EPPP"),
    ("exam-testable", "EPPP-testable"),
    ("On licensing exams,", "On the EPPP,"),
    ("on licensing exams.", "on the EPPP."),
    ("on licensing exams ", "on the EPPP "),
    ("for licensing exams,", "for the EPPP,"),
    ("for licensing exams.", "for the EPPP."),
    ("for licensing exams ", "for the EPPP "),
    ("for exam purposes", "for EPPP purposes"),
    ("the licensing exam itself", "the EPPP itself"),
    ("the licensing exam", "the EPPP"),
    ("The licensing exam", "The EPPP"),
    ("licensing exam", "EPPP"),
    # Fix artifacts from original April 14 commit
    ("Exam-Style Application", "EPPP-Style Application"),
    ("Key Heritability Estimates", "EPPP-Relevant Heritability Estimates"),
    ("exam-level knowledge", "EPPP-level knowledge"),
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
        return False, 0

    modified = original
    for old, new in RESTORE_RULES:
        modified = modified.replace(old, new)

    if modified == original:
        return False, 0

    count = sum(1 for o, n in RESTORE_RULES if o in original)

    if not dry_run:
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.write(modified)

    return True, count


def main():
    dry_run = '--dry-run' in sys.argv
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    all_files = set()
    for pattern in CONTENT_GLOBS:
        all_files.update(glob.glob(pattern, recursive=True))

    files = sorted(f for f in all_files if not should_skip(f))
    print(f"Scanning {len(files)} files...")

    changed = 0
    for f in files:
        ok, count = process_file(f, dry_run)
        if ok:
            changed += 1
            prefix = "[DRY] " if dry_run else ""
            print(f"  {prefix}Restored: {os.path.relpath(f)}")

    # Validate JSON
    if not dry_run:
        for f in files:
            if f.endswith('.json'):
                try:
                    json.load(open(f, encoding='utf-8'))
                except json.JSONDecodeError as e:
                    print(f"  ** JSON BROKEN: {f}: {e}")

    mode = "DRY RUN" if dry_run else "APPLIED"
    print(f"\n{mode}: {changed} files restored")


if __name__ == '__main__':
    main()
