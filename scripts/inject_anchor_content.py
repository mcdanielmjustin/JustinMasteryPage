"""
inject_anchor_content.py  (Phase 4 — REVISED)

Inject generated anchor content into HTML chapter files.
Addition-only: never modifies or deletes existing lines.

Insertion modes:
  - "missing": insert after the relevant heading (existing behavior)
  - "partial": insert at END of existing section (before next heading)

Safety features:
  - Pre-injection snapshot of structural elements
  - Post-injection validation (section comments, CSS classes, onclick, ids)
  - Automatic revert from backup on any validation failure
  - embed_eligible check (belt-and-suspenders)

Output: Modified HTML files in mastery-page/content/domain1-9/

Run:
  python scripts/inject_anchor_content.py --all
  python scripts/inject_anchor_content.py --domain PMET
  python scripts/inject_anchor_content.py --dry-run --all
  python scripts/inject_anchor_content.py --verify --all
"""

import json, pathlib, re, sys, argparse, shutil
from collections import Counter

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
DATA_DIR = SCRIPTS_DIR / "data"
CONTENT_DIR = SCRIPTS_DIR.parent / "content"
GENERATED_FILE = DATA_DIR / "anchor_content_generated.json"
BACKUP_DIR = DATA_DIR / "backup"


# ══════════════════════════════════════════════════════════════════════
# Heading matching
# ══════════════════════════════════════════════════════════════════════

def normalize_ws(text):
    return re.sub(r"\s+", " ", text).strip().lower()


def strip_tags(html):
    return re.sub(r"<[^>]+>", "", html).strip()


def find_heading_line(lines, heading_text, start_hint=0):
    """Find line index of an h2 or h3 heading matching heading_text.
    Returns (line_index, heading_level) or (None, None).
    """
    target = normalize_ws(heading_text)

    search_order = list(range(len(lines)))
    if start_hint > 0:
        search_order = sorted(search_order, key=lambda i: abs(i - start_hint))

    for i in search_order:
        line = lines[i]
        m = re.search(r'<(h[23])[^>]*>(.*?)</\1>', line, re.DOTALL | re.IGNORECASE)
        if m:
            heading_content = normalize_ws(strip_tags(m.group(2)))
            if (heading_content == target
                    or target in heading_content
                    or heading_content in target):
                return i, m.group(1)

    return None, None


def anchor_already_injected(lines, anchor_id):
    """Check if this anchor's content was already injected."""
    marker = f"<!-- anchor:{anchor_id} "
    return any(marker in line for line in lines)


# ══════════════════════════════════════════════════════════════════════
# Injection point logic (partial vs missing)
# ══════════════════════════════════════════════════════════════════════

def find_injection_point_missing(lines, heading_line_idx):
    """For 'missing' coverage: insert after the heading (+ skip intro paragraph).
    Returns line index for insertion.
    """
    insert_at = heading_line_idx + 1
    # Skip blank lines after heading
    while insert_at < len(lines) and lines[insert_at].strip() == "":
        insert_at += 1

    # Skip one intro paragraph if present (not an anchor block)
    if insert_at < len(lines):
        line = lines[insert_at].strip()
        if line.startswith("<p>") and "<!-- anchor:" not in line:
            while insert_at < len(lines) and lines[insert_at].strip() != "":
                insert_at += 1
                if insert_at < len(lines) and re.search(r'<h[234]', lines[insert_at], re.IGNORECASE):
                    break

    return insert_at


def find_injection_point_partial(lines, heading_line_idx):
    """For 'partial' coverage: insert at END of section (before next heading).
    Returns line index for insertion.
    """
    insert_at = heading_line_idx + 1

    # Walk forward until we hit the next heading or EOF
    while insert_at < len(lines):
        line = lines[insert_at].strip()
        if re.search(r'<h[23][^>]*>', line, re.IGNORECASE):
            break
        insert_at += 1

    # Back up past trailing blank lines to insert just before next heading
    while insert_at > heading_line_idx + 1 and lines[insert_at - 1].strip() == "":
        insert_at -= 1

    return insert_at


# ══════════════════════════════════════════════════════════════════════
# Pre/post injection snapshot & validation
# ══════════════════════════════════════════════════════════════════════

def take_snapshot(lines):
    """Capture structural element counts for validation."""
    text = "".join(lines)
    return {
        "section_comments": re.findall(r'<!-- Section \d+:', text),
        "upgrade_modal": text.count('id="upgradeModal"'),
        "definition_box": text.count('class="definition-box"'),
        "example_box": text.count('class="example-box"'),
        "clinical_note": text.count('class="clinical-note"'),
        "key_term": text.count('class="key-term"'),
        "onclick_count": len(re.findall(r'onclick=', text)),
        "total_lines": len(lines),
    }


def validate_injection(pre_snap, post_lines, file_path):
    """Compare post-injection file against pre-injection snapshot.
    Returns (is_valid, issues_list).
    """
    post_snap = take_snapshot(post_lines)
    issues = []

    # Section comments: same count and same text
    if len(pre_snap["section_comments"]) != len(post_snap["section_comments"]):
        issues.append(
            f"Section comment count changed: {len(pre_snap['section_comments'])} → "
            f"{len(post_snap['section_comments'])}")
    elif pre_snap["section_comments"] != post_snap["section_comments"]:
        issues.append("Section comment text changed")

    # upgradeModal must be unchanged
    if pre_snap["upgrade_modal"] != post_snap["upgrade_modal"]:
        issues.append(f"upgradeModal count changed: {pre_snap['upgrade_modal']} → {post_snap['upgrade_modal']}")

    # EXISTING semantic CSS classes must not decrease
    # (injected blocks may ADD new ones, so we check >= not ==)
    for cls_key in ("definition_box", "example_box", "clinical_note", "key_term"):
        if post_snap[cls_key] < pre_snap[cls_key]:
            issues.append(f"{cls_key} count decreased: {pre_snap[cls_key]} → {post_snap[cls_key]}")

    # onclick handlers must be unchanged
    if pre_snap["onclick_count"] != post_snap["onclick_count"]:
        issues.append(f"onclick count changed: {pre_snap['onclick_count']} → {post_snap['onclick_count']}")

    # Check that all injected anchor blocks have matching open/close markers
    post_text = "".join(post_lines)
    opens = re.findall(r'<!-- anchor:(\S+) ', post_text)
    closes = re.findall(r'<!-- /anchor:(\S+) -->', post_text)
    if Counter(opens) != Counter(closes):
        issues.append(f"Mismatched anchor markers: opens={Counter(opens)}, closes={Counter(closes)}")

    # No duplicate anchor IDs
    if len(opens) != len(set(opens)):
        dupes = [aid for aid, cnt in Counter(opens).items() if cnt > 1]
        issues.append(f"Duplicate anchor IDs: {dupes}")

    return len(issues) == 0, issues


# ══════════════════════════════════════════════════════════════════════
# Core injection
# ══════════════════════════════════════════════════════════════════════

def inject_into_file(file_path, injections, dry_run=False):
    """Inject generated HTML content into a chapter file.
    Returns (count_injected, post_lines_or_None).
    """
    lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
    count = 0
    injections_done = []

    for inj in injections:
        anchor_id = inj["anchor_id"]
        heading_text = inj.get("inject_after")
        generated_html = inj.get("generated_html", "").strip()
        coverage = inj.get("coverage", "missing")

        if not generated_html:
            continue

        # Belt-and-suspenders: skip if not embed_eligible
        if not inj.get("embed_eligible", True):
            print(f"    SKIP [{anchor_id}]: not embed_eligible")
            continue

        # Skip validation failures
        if inj.get("validation_passed") is False:
            print(f"    SKIP [{anchor_id}]: failed content validation")
            continue

        if anchor_already_injected(lines, anchor_id):
            if dry_run:
                print(f"    SKIP [{anchor_id}]: already injected")
            continue

        if not heading_text:
            for i, line in enumerate(lines):
                if re.search(r'<h2[^>]*>', line, re.IGNORECASE):
                    heading_line = i
                    break
            else:
                print(f"    WARNING: No heading for [{anchor_id}], skipping")
                continue
        else:
            heading_line, _ = find_heading_line(lines, heading_text)

        if heading_line is None:
            print(f"    WARNING: Heading '{heading_text}' not found for [{anchor_id}]")
            continue

        # Choose insertion strategy based on coverage type
        if coverage == "partial":
            insert_at = find_injection_point_partial(lines, heading_line)
        else:
            insert_at = find_injection_point_missing(lines, heading_line)

        if dry_run:
            mode = "END-of-section" if coverage == "partial" else "after-heading"
            preview = generated_html[:80].replace("\n", "\\n")
            print(f"    DRY RUN [{anchor_id}] ({coverage}, {mode}): "
                  f"line {insert_at + 1} after '{heading_text}' → {preview}...")
            count += 1
            continue

        # Build indented block
        html_lines = []
        for html_line in generated_html.split("\n"):
            stripped = html_line.strip()
            if stripped:
                html_lines.append(f"        {stripped}\n")
            else:
                html_lines.append("\n")

        block = ["\n"] + html_lines + ["\n"]
        injections_done.append((insert_at, block, anchor_id))
        count += 1

    if not dry_run and injections_done:
        # Sort descending to prevent index drift
        injections_done.sort(key=lambda x: x[0], reverse=True)

        for insert_at, block, anchor_id in injections_done:
            for j, new_line in enumerate(block):
                lines.insert(insert_at + j, new_line)

        return count, lines

    return count, None


# ══════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════

def main():
    global CONTENT_DIR, BACKUP_DIR

    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Inject anchor content into HTML files")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--domain", type=str, help="Single domain code (e.g. PMET)")
    group.add_argument("--verify", action="store_true",
                       help="Verify already-injected files against backups")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--target-dir", type=str,
                        help="Override content directory (e.g. path to PassEPPP-website/content)")
    args = parser.parse_args()

    if args.target_dir:
        CONTENT_DIR = pathlib.Path(args.target_dir).resolve()
        if not CONTENT_DIR.is_dir():
            print(f"ERROR: --target-dir {CONTENT_DIR} is not a directory")
            sys.exit(1)
        target_label = CONTENT_DIR.parent.name
        BACKUP_DIR = DATA_DIR / "backup" / target_label

    if not GENERATED_FILE.exists():
        print(f"ERROR: {GENERATED_FILE} not found. Run generate_anchor_content.py first.")
        sys.exit(1)

    generated = json.loads(GENERATED_FILE.read_text(encoding="utf-8"))
    generated = [g for g in generated if g.get("generated_html")]

    if args.domain:
        generated = [g for g in generated if g["domain_code"] == args.domain.upper()]

    if not generated and not args.verify:
        print("No content to inject.")
        return

    # ── Verify mode: check existing files against backups ─────────────
    if args.verify:
        print("Verifying injected files...\n")
        by_file = {}
        for item in generated:
            by_file.setdefault(item["chapter_file"], []).append(item)

        all_ok = True
        for rel_path in sorted(by_file):
            file_path = CONTENT_DIR / rel_path
            if not file_path.exists():
                continue

            backup_name = rel_path.replace("/", "_").replace("\\", "_")
            backup_path = BACKUP_DIR / backup_name
            if not backup_path.exists():
                print(f"  {rel_path}: no backup found, skipping verify")
                continue

            pre_lines = backup_path.read_text(encoding="utf-8").splitlines(keepends=True)
            post_lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)

            pre_snap = take_snapshot(pre_lines)
            is_valid, issues = validate_injection(pre_snap, post_lines, file_path)

            if is_valid:
                print(f"  {rel_path}: OK")
            else:
                print(f"  {rel_path}: FAILED")
                for issue in issues:
                    print(f"    - {issue}")
                all_ok = False

        print(f"\n{'All files passed validation.' if all_ok else 'Some files failed — review above.'}")
        return

    # ── Injection mode ────────────────────────────────────────────────
    print(f"Injecting {len(generated)} anchor blocks"
          f"{' (DRY RUN)' if args.dry_run else ''}...\n")

    by_file = {}
    for item in generated:
        by_file.setdefault(item["chapter_file"], []).append(item)

    total_injected = 0
    total_reverted = 0

    for rel_path, items in sorted(by_file.items()):
        file_path = CONTENT_DIR / rel_path
        if not file_path.exists():
            print(f"  WARNING: {file_path} not found")
            continue

        # Backup (before any modification)
        if not args.dry_run:
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            backup_name = rel_path.replace("/", "_").replace("\\", "_")
            backup_path = BACKUP_DIR / backup_name
            if not backup_path.exists():
                shutil.copy2(file_path, backup_path)

        # Pre-injection snapshot
        pre_lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
        pre_snap = take_snapshot(pre_lines)

        count, post_lines = inject_into_file(file_path, items, dry_run=args.dry_run)

        if not args.dry_run and post_lines is not None:
            # Post-injection validation
            is_valid, issues = validate_injection(pre_snap, post_lines, file_path)

            if is_valid:
                file_path.write_text("".join(post_lines), encoding="utf-8", newline="\n")
                print(f"  {rel_path}: {count} injection(s) — validated OK")
            else:
                # REVERT: restore from backup
                print(f"  {rel_path}: VALIDATION FAILED — reverting")
                for issue in issues:
                    print(f"    - {issue}")
                shutil.copy2(backup_path, file_path)
                count = 0
                total_reverted += 1
        else:
            print(f"  {rel_path}: {count} injection(s)")

        total_injected += count

    print(f"\nTotal: {total_injected} injections across {len(by_file)} files")
    if total_reverted:
        print(f"  {total_reverted} file(s) reverted due to validation failure")
    if not args.dry_run and total_injected > 0:
        print(f"Backups saved to {BACKUP_DIR}")


if __name__ == "__main__":
    main()
