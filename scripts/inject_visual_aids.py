"""
inject_visual_aids.py

Injects generated visual-aid HTML blocks into chapter HTML files.
Idempotent: uses comment markers <!-- visual-aid:ID --> to skip already-injected blocks.
Addition-only: never modifies or deletes existing content.

Run:
  python scripts/inject_visual_aids.py --all
  python scripts/inject_visual_aids.py --domain PMET
  python scripts/inject_visual_aids.py --dry-run --all
  python scripts/inject_visual_aids.py --target-dir C:/Users/Admin/PassEPPP-website/content --all
"""

import json, pathlib, argparse, re, sys, shutil
from collections import Counter

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
DATA_DIR = SCRIPTS_DIR / "data"
INPUT_FILE = DATA_DIR / "visual_aids_generated.json"
DEFAULT_CONTENT_DIR = pathlib.Path("C:/Users/Admin/JustinMasteryPage/content")
BACKUP_DIR = DATA_DIR / "backup_va"


# ══════════════════════════════════════════════════════════════════════
# Heading matching (consistent with inject_anchor_content.py)
# ══════════════════════════════════════════════════════════════════════

def normalize_ws(text):
    return re.sub(r"\s+", " ", text).strip().lower()


def strip_tags(html):
    return re.sub(r"<[^>]+>", "", html).strip()


def find_heading_line(lines, heading_text):
    """Find line index of an h2 or h3 heading matching heading_text."""
    target = normalize_ws(heading_text)

    for i, line in enumerate(lines):
        m = re.search(r'<(h[23])[^>]*>(.*?)</\1>', line, re.DOTALL | re.IGNORECASE)
        if m:
            content = normalize_ws(strip_tags(m.group(2)))
            if (content == target
                    or target in content
                    or content in target):
                return i
    return None


def already_injected(lines, va_id):
    """Check if this visual aid was already injected."""
    marker = f"<!-- visual-aid:{va_id} -->"
    return any(marker in line for line in lines)


# ══════════════════════════════════════════════════════════════════════
# Injection point logic
# ══════════════════════════════════════════════════════════════════════

def find_section_end(lines, heading_idx):
    """Find insertion point at end of section (before next h2/h3 heading).
    Visual aids go at the END of the section they belong to."""
    for i in range(heading_idx + 1, len(lines)):
        line = lines[i].strip()
        if re.search(r'<h[23][^>]*>', line, re.IGNORECASE):
            # Back up past trailing blank lines
            j = i
            while j > heading_idx + 1 and lines[j - 1].strip() == "":
                j -= 1
            return j
    # No next heading — insert before end of file (before closing tags)
    # Back up past blank lines and closing tags
    j = len(lines)
    while j > heading_idx + 1 and lines[j - 1].strip() in ("", "</div>", "</body>", "</html>"):
        j -= 1
    return j + 1


# ══════════════════════════════════════════════════════════════════════
# Pre/post injection snapshot & validation
# ══════════════════════════════════════════════════════════════════════

def take_snapshot(lines):
    """Capture structural element counts for validation."""
    text = "".join(lines)
    return {
        "section_comments": len(re.findall(r'<!-- Section \d+:', text)),
        "upgrade_modal": text.count('id="upgradeModal"'),
        "definition_box": text.count('class="definition-box"'),
        "example_box": text.count('class="example-box"'),
        "clinical_note": text.count('class="clinical-note"'),
        "onclick_count": len(re.findall(r'onclick=', text)),
        "anchor_markers": len(re.findall(r'<!-- anchor:\S+ ', text)),
    }


def validate_injection(pre_snap, post_lines, file_path):
    """Verify that injection didn't break anything."""
    post_snap = take_snapshot(post_lines)
    issues = []

    if pre_snap["section_comments"] != post_snap["section_comments"]:
        issues.append(f"Section comment count changed: {pre_snap['section_comments']} → {post_snap['section_comments']}")

    if pre_snap["upgrade_modal"] != post_snap["upgrade_modal"]:
        issues.append(f"upgradeModal count changed")

    for key in ("definition_box", "example_box", "clinical_note"):
        if post_snap[key] < pre_snap[key]:
            issues.append(f"{key} count decreased: {pre_snap[key]} → {post_snap[key]}")

    if pre_snap["onclick_count"] != post_snap["onclick_count"]:
        issues.append(f"onclick count changed: {pre_snap['onclick_count']} → {post_snap['onclick_count']}")

    # Anchor markers must not decrease
    if post_snap["anchor_markers"] < pre_snap["anchor_markers"]:
        issues.append(f"Anchor markers decreased: {pre_snap['anchor_markers']} → {post_snap['anchor_markers']}")

    # Check visual-aid marker pairs match
    post_text = "".join(post_lines)
    opens = re.findall(r'<!-- visual-aid:(\S+) -->', post_text)
    closes = re.findall(r'<!-- /visual-aid:(\S+) -->', post_text)
    if Counter(opens) != Counter(closes):
        issues.append(f"Mismatched visual-aid markers: opens={len(opens)}, closes={len(closes)}")

    if len(opens) != len(set(opens)):
        dupes = [vid for vid, cnt in Counter(opens).items() if cnt > 1]
        issues.append(f"Duplicate visual-aid IDs: {dupes}")

    return len(issues) == 0, issues


# ══════════════════════════════════════════════════════════════════════
# Core injection
# ══════════════════════════════════════════════════════════════════════

def inject_into_file(file_path, vas, dry_run=False):
    """Inject visual-aid blocks into a chapter file.
    Returns (count_injected, post_lines_or_None).
    """
    lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
    count = 0
    insertions = []

    for va in vas:
        va_id = va["id"]

        if already_injected(lines, va_id):
            if dry_run:
                print(f"    SKIP [{va_id}]: already injected")
            continue

        heading_idx = find_heading_line(lines, va["anchor_heading"])
        if heading_idx is None:
            print(f"    WARNING: heading '{va['anchor_heading']}' not found for [{va_id}]")
            continue

        insert_at = find_section_end(lines, heading_idx)

        if dry_run:
            print(f"    DRY RUN [{va_id}] ({va['layout_type']}): "
                  f"line {insert_at + 1} after '{va['anchor_heading']}'")
            count += 1
            continue

        # Build the block as lines
        html_block = va["html"]
        block_lines = []
        block_lines.append("\n")
        for html_line in html_block.split("\n"):
            stripped = html_line.strip()
            if stripped:
                block_lines.append(f"        {stripped}\n")
            else:
                block_lines.append("\n")
        block_lines.append("\n")

        insertions.append((insert_at, block_lines, va_id))
        count += 1

    if not dry_run and insertions:
        # Sort descending to prevent index drift
        insertions.sort(key=lambda x: x[0], reverse=True)

        for insert_at, block, va_id in insertions:
            for j, new_line in enumerate(block):
                lines.insert(insert_at + j, new_line)

        return count, lines

    return count, None


# ══════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════

def main():
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Inject visual aids into chapter HTML files")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--domain", type=str, help="Single domain code (e.g. PMET)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--target-dir", type=str,
                        help="Override content directory")
    args = parser.parse_args()

    content_dir = DEFAULT_CONTENT_DIR
    backup_dir = BACKUP_DIR

    if args.target_dir:
        content_dir = pathlib.Path(args.target_dir).resolve()
        if not content_dir.is_dir():
            print(f"ERROR: --target-dir {content_dir} is not a directory")
            sys.exit(1)
        target_label = content_dir.parent.name
        backup_dir = DATA_DIR / "backup_va" / target_label

    if not INPUT_FILE.exists():
        print(f"ERROR: {INPUT_FILE} not found. Run generate_visual_aids.py first.")
        sys.exit(1)

    vas = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    print(f"Loaded {len(vas)} visual aids from manifest")

    if args.domain:
        vas = [v for v in vas if v["domain_code"] == args.domain.upper()]
        print(f"  Filtered to {len(vas)} for domain {args.domain.upper()}")

    if not vas:
        print("No visual aids to inject.")
        return

    # Group by chapter file
    by_file = {}
    for va in vas:
        by_file.setdefault(va["chapter_file"], []).append(va)

    print(f"Injecting into {len(by_file)} files"
          f"{' (DRY RUN)' if args.dry_run else ''}...\n")

    total_injected = 0
    total_reverted = 0

    for rel_path, items in sorted(by_file.items()):
        file_path = content_dir / rel_path
        if not file_path.exists():
            print(f"  WARNING: {file_path} not found")
            continue

        # Backup before modification
        if not args.dry_run:
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_name = rel_path.replace("/", "_").replace("\\", "_")
            backup_path = backup_dir / backup_name
            if not backup_path.exists():
                shutil.copy2(file_path, backup_path)

        # Pre-injection snapshot
        pre_lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
        pre_snap = take_snapshot(pre_lines)

        count, post_lines = inject_into_file(file_path, items, dry_run=args.dry_run)

        if not args.dry_run and post_lines is not None:
            is_valid, issues = validate_injection(pre_snap, post_lines, file_path)

            if is_valid:
                file_path.write_text("".join(post_lines), encoding="utf-8", newline="\n")
                print(f"  {rel_path}: {count} injection(s) — validated OK")
            else:
                print(f"  {rel_path}: VALIDATION FAILED — reverting")
                for issue in issues:
                    print(f"    - {issue}")
                backup_name = rel_path.replace("/", "_").replace("\\", "_")
                backup_path = backup_dir / backup_name
                if backup_path.exists():
                    shutil.copy2(backup_path, file_path)
                count = 0
                total_reverted += 1
        else:
            if count > 0:
                print(f"  {rel_path}: {count} injection(s)")

        total_injected += count

    print(f"\nTotal: {total_injected} injections across {len(by_file)} files")
    if total_reverted:
        print(f"  {total_reverted} file(s) reverted due to validation failure")
    if not args.dry_run and total_injected > 0:
        print(f"Backups saved to {backup_dir}")


if __name__ == "__main__":
    main()
