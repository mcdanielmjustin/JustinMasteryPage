"""
inject_h3_intros.py

Reads h3_intros_generated.json and injects <p> tags after each matching <h3>
in the HTML files. Backs up originals first.

Run:
  python scripts/inject_h3_intros.py
  python scripts/inject_h3_intros.py --dry-run
"""

import json, pathlib, argparse, shutil, re, sys

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
DATA_DIR = SCRIPTS_DIR / "data"
CONTENT_DIR = SCRIPTS_DIR.parent / "content"
INTROS_FILE = DATA_DIR / "h3_intros_generated.json"
BACKUP_DIR = DATA_DIR / "backup"


def normalize_ws(text: str) -> str:
    """Collapse whitespace for comparison."""
    return re.sub(r"\s+", " ", text).strip()


def inject_intro_into_file(file_path: pathlib.Path, injections: list[dict],
                            dry_run: bool = False) -> int:
    """
    Inject <p> tags after matching <h3> lines.
    Returns count of successful injections.
    """
    lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
    count = 0

    # Sort injections by line number descending so insertions don't shift later targets
    injections_sorted = sorted(injections, key=lambda x: x["h3_line"], reverse=True)

    for inj in injections_sorted:
        target_line = inj["h3_line"] - 1  # Convert 1-based to 0-based
        intro_text = inj["generated_intro"]

        # Verify the h3 text matches at the target line (with some tolerance)
        if target_line < 0 or target_line >= len(lines):
            print(f"  WARNING: Line {inj['h3_line']} out of range in {file_path.name}")
            continue

        line_text = lines[target_line]
        # Extract text content from the h3 tag
        h3_match = re.search(r"<h3[^>]*>(.*?)</h3>", line_text, re.DOTALL | re.IGNORECASE)
        if not h3_match:
            # Try adjacent lines (±2) in case line numbers shifted slightly
            found = False
            for offset in [-1, 1, -2, 2]:
                adj = target_line + offset
                if 0 <= adj < len(lines):
                    h3_match = re.search(r"<h3[^>]*>(.*?)</h3>", lines[adj], re.DOTALL | re.IGNORECASE)
                    if h3_match:
                        h3_content = re.sub(r"<[^>]+>", "", h3_match.group(1)).strip()
                        if normalize_ws(h3_content) == normalize_ws(inj["h3_text"]):
                            target_line = adj
                            found = True
                            break
            if not found:
                print(f"  WARNING: No <h3> found near line {inj['h3_line']} for '{inj['h3_text']}'")
                continue
        else:
            h3_content = re.sub(r"<[^>]+>", "", h3_match.group(1)).strip()
            if normalize_ws(h3_content) != normalize_ws(inj["h3_text"]):
                print(f"  WARNING: h3 mismatch at line {inj['h3_line']}: "
                      f"expected '{inj['h3_text']}', found '{h3_content}'")
                continue

        # Detect indentation from the h3 line
        indent_match = re.match(r"(\s*)", line_text)
        indent = indent_match.group(1) if indent_match else "        "

        # Build the <p> line to insert
        p_line = f"{indent}<p>{intro_text}</p>\n"

        if dry_run:
            print(f"  DRY RUN: Would insert after line {target_line + 1}:")
            print(f"    {p_line.rstrip()}")
            count += 1
            continue

        # Insert after the h3 line (and any blank line after it)
        insert_at = target_line + 1
        # Skip blank lines between h3 and h4
        while insert_at < len(lines) and lines[insert_at].strip() == "":
            insert_at += 1

        # Insert the paragraph with a blank line before it for readability
        lines.insert(insert_at, "\n")
        lines.insert(insert_at + 1, p_line)
        count += 1

    if count > 0 and not dry_run:
        # Write back with LF line endings
        file_path.write_text("".join(lines), encoding="utf-8", newline="\n")

    return count


def main():
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Inject h3 intro paragraphs")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be injected without modifying files")
    args = parser.parse_args()

    if not INTROS_FILE.exists():
        print(f"ERROR: {INTROS_FILE} not found. Run generate_h3_intros.py first.")
        sys.exit(1)

    intros = json.loads(INTROS_FILE.read_text(encoding="utf-8"))
    intros = [item for item in intros if "generated_intro" in item]

    if not intros:
        print("No intros to inject.")
        return

    print(f"Injecting {len(intros)} h3 intros{' (DRY RUN)' if args.dry_run else ''}...")

    # Group by file path
    by_file: dict[str, list[dict]] = {}
    for item in intros:
        by_file.setdefault(item["file_path"], []).append(item)

    total_injected = 0

    for rel_path, items in sorted(by_file.items()):
        file_path = CONTENT_DIR.parent / rel_path
        if not file_path.exists():
            print(f"  WARNING: File not found: {file_path}")
            continue

        # Backup original
        if not args.dry_run:
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            backup_name = rel_path.replace("/", "_").replace("\\", "_")
            backup_path = BACKUP_DIR / backup_name
            if not backup_path.exists():
                shutil.copy2(file_path, backup_path)

        count = inject_intro_into_file(file_path, items, dry_run=args.dry_run)
        total_injected += count
        print(f"  {file_path.name}: {count} injection(s)")

    print(f"\nTotal: {total_injected} injections across {len(by_file)} files")

    if not args.dry_run and total_injected > 0:
        print(f"Backups saved to {BACKUP_DIR}")


if __name__ == "__main__":
    main()
