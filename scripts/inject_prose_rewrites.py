"""
inject_prose_rewrites.py

Reads prose_rewrites.json and applies rewritten sections to HTML files.
Backs up originals first. Supports --dry-run for QA review.

Run:
  python scripts/inject_prose_rewrites.py --dry-run  # review diffs first
  python scripts/inject_prose_rewrites.py             # apply rewrites
"""

import json, pathlib, argparse, shutil, re, sys, html as html_mod

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
DATA_DIR = SCRIPTS_DIR / "data"
CONTENT_DIR = SCRIPTS_DIR.parent / "content"
REWRITES_FILE = DATA_DIR / "prose_rewrites.json"
BACKUP_DIR = DATA_DIR / "backup_prose"
DIFF_REPORT = DATA_DIR / "prose_diff_report.html"


def normalize_ws(text: str) -> str:
    """Collapse whitespace for comparison."""
    return re.sub(r"\s+", " ", text).strip()


def strip_tags(html: str) -> str:
    """Remove all HTML tags."""
    return re.sub(r"<[^>]+>", "", html).strip()


def find_section_content_end(lines: list[str], h2_idx: int) -> int:
    """Find the exclusive end index of h2 section content.

    Scans forward from h2 for the next h2 or </section>, whichever first.
    """
    for i in range(h2_idx + 1, len(lines)):
        stripped = lines[i].strip()
        # Next h2 — end before it
        if re.search(r"<h2[\s>]", stripped, re.I):
            # Trim trailing blanks and <section> tags
            end = i
            while end > h2_idx + 1:
                s = lines[end - 1].strip()
                if not s or s.startswith("<section"):
                    end -= 1
                else:
                    break
            return end
        # </section> — end before it
        if stripped == "</section>":
            return i

    # No next h2 or </section> found — return end of file
    return len(lines)


def normalize_indentation(original_lines: list[str], rewrite_lines: list[str]) -> list[str]:
    """Adjust rewrite indentation to match the original file's h2 indent."""
    # Detect original indent from h2 line
    orig_indent = ""
    for line in original_lines:
        if re.search(r"<h2[\s>]", line, re.I):
            orig_indent = line[: len(line) - len(line.lstrip())]
            break

    # Detect rewrite indent from h2 line
    rw_indent = ""
    for line in rewrite_lines:
        if re.search(r"<h2[\s>]", line, re.I):
            rw_indent = line[: len(line) - len(line.lstrip())]
            break

    if orig_indent == rw_indent:
        return rewrite_lines

    # Adjust each line
    result = []
    for line in rewrite_lines:
        if not line.strip():
            result.append(line)
            continue
        content = line.lstrip()
        current_indent = line[: len(line) - len(content)]
        if rw_indent and current_indent.startswith(rw_indent):
            extra = current_indent[len(rw_indent) :]
            result.append(orig_indent + extra + content)
        else:
            result.append(orig_indent + content)
    return result


def inject_rewrites_into_file(
    file_path: pathlib.Path,
    rewrites: list[dict],
    dry_run: bool = False,
) -> tuple[int, list[dict]]:
    """Replace h2 sections with rewritten versions.

    Returns (count_injected, list_of_diff_dicts_for_report).
    """
    lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
    count = 0
    diffs = []

    # Sort by heading_line descending so edits don't shift later targets
    rewrites_sorted = sorted(rewrites, key=lambda x: x["heading_line"], reverse=True)

    for rw in rewrites_sorted:
        target_line = rw["heading_line"] - 1  # 0-based

        # Verify h2 matches at target line
        if target_line < 0 or target_line >= len(lines):
            print(f"  WARNING: Line {rw['heading_line']} out of range in {file_path.name}")
            continue

        h2_match = re.search(
            r"<h2[^>]*>(.*?)</h2>", lines[target_line], re.DOTALL | re.I
        )
        found_at = target_line

        if not h2_match or normalize_ws(strip_tags(h2_match.group(1))) != normalize_ws(rw["heading_text"]):
            # Search outward from target line, then fall back to full-file scan
            found = False
            for offset in range(1, len(lines)):
                for sign in (-1, 1):
                    adj = target_line + sign * offset
                    if 0 <= adj < len(lines):
                        m = re.search(r"<h2[^>]*>(.*?)</h2>", lines[adj], re.DOTALL | re.I)
                        if m and normalize_ws(strip_tags(m.group(1))) == normalize_ws(rw["heading_text"]):
                            found_at = adj
                            found = True
                            break
                if found:
                    break
            if not found:
                print(
                    f"  WARNING: h2 not found near line {rw['heading_line']} "
                    f"for '{rw['heading_text']}'"
                )
                continue

        # Find section end
        section_end = find_section_content_end(lines, found_at)

        # Original section lines
        original_lines_slice = lines[found_at:section_end]
        original_html = "".join(original_lines_slice)

        # Prepare rewrite lines
        rewrite_text = rw["rewritten_html"]
        rewrite_lines_raw = rewrite_text.splitlines(keepends=True)
        # Ensure last line has newline
        if rewrite_lines_raw and not rewrite_lines_raw[-1].endswith("\n"):
            rewrite_lines_raw[-1] += "\n"
        # Add trailing blank line for readability (match original style)
        if original_lines_slice and not original_lines_slice[-1].strip():
            if rewrite_lines_raw and rewrite_lines_raw[-1].strip():
                rewrite_lines_raw.append("\n")

        # Normalize indentation to match original
        rewrite_lines_final = normalize_indentation(original_lines_slice, rewrite_lines_raw)

        if dry_run:
            diffs.append({
                "file": str(file_path.name),
                "heading": rw["heading_text"],
                "line": rw["heading_line"],
                "original": original_html,
                "rewritten": "".join(rewrite_lines_final),
            })
            count += 1
            continue

        # Replace the section
        lines[found_at:section_end] = rewrite_lines_final
        count += 1

    if count > 0 and not dry_run:
        file_path.write_text("".join(lines), encoding="utf-8", newline="\n")

    return count, diffs


def generate_diff_report(all_diffs: list[dict]):
    """Generate an HTML diff report for QA review."""
    sections = []
    for i, d in enumerate(all_diffs, 1):
        orig_escaped = html_mod.escape(d["original"])
        new_escaped = html_mod.escape(d["rewritten"])
        sections.append(f"""
    <div class="diff-section">
      <h3>{i}. {html_mod.escape(d['file'])}:{d['line']} — {html_mod.escape(d['heading'])}</h3>
      <div class="diff-row">
        <div class="diff-col">
          <h4>Original</h4>
          <pre>{orig_escaped}</pre>
        </div>
        <div class="diff-col">
          <h4>Rewritten</h4>
          <pre>{new_escaped}</pre>
        </div>
      </div>
    </div>""")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Prose Rewrite Diff Report</title>
  <style>
    body {{ font-family: -apple-system, sans-serif; margin: 24px; background: #1a1a2e; color: #e0e0e0; }}
    h1 {{ color: #f59e0b; }}
    h3 {{ color: #3b82f6; margin-top: 32px; border-bottom: 1px solid #333; padding-bottom: 8px; }}
    h4 {{ margin: 8px 0 4px; color: #a1a1aa; }}
    .diff-section {{ margin-bottom: 48px; }}
    .diff-row {{ display: flex; gap: 16px; }}
    .diff-col {{ flex: 1; min-width: 0; }}
    pre {{ background: #0f0f11; border: 1px solid #333; border-radius: 8px; padding: 16px;
           white-space: pre-wrap; word-wrap: break-word; font-size: 0.85rem; line-height: 1.5;
           max-height: 600px; overflow-y: auto; }}
    .summary {{ background: #18181b; padding: 16px; border-radius: 8px; margin-bottom: 24px; }}
  </style>
</head>
<body>
  <h1>Prose Rewrite Diff Report</h1>
  <div class="summary">
    <p><strong>{len(all_diffs)}</strong> sections rewritten</p>
  </div>
  {"".join(sections)}
</body>
</html>"""

    DIFF_REPORT.write_text(html_content, encoding="utf-8")
    print(f"Diff report saved to {DIFF_REPORT}")


def main():
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Inject prose rewrites into HTML files")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be changed without modifying files",
    )
    args = parser.parse_args()

    if not REWRITES_FILE.exists():
        print(f"ERROR: {REWRITES_FILE} not found. Run elevate_prose.py first.")
        sys.exit(1)

    rewrites = json.loads(REWRITES_FILE.read_text(encoding="utf-8"))
    rewrites = [item for item in rewrites if "rewritten_html" in item]

    if not rewrites:
        print("No rewrites to inject.")
        return

    print(f"Injecting {len(rewrites)} prose rewrites"
          f"{' (DRY RUN)' if args.dry_run else ''}...\n")

    # Group by file path
    by_file: dict[str, list[dict]] = {}
    for item in rewrites:
        by_file.setdefault(item["file_path"], []).append(item)

    total_injected = 0
    all_diffs: list[dict] = []

    for rel_path, items in sorted(by_file.items()):
        file_path = CONTENT_DIR.parent / rel_path
        if not file_path.exists():
            print(f"  WARNING: File not found: {file_path}")
            continue

        # Backup original (only when actually modifying)
        if not args.dry_run:
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            backup_name = rel_path.replace("/", "_").replace("\\", "_")
            backup_path = BACKUP_DIR / backup_name
            if not backup_path.exists():
                shutil.copy2(file_path, backup_path)

        count, diffs = inject_rewrites_into_file(file_path, items, dry_run=args.dry_run)
        total_injected += count
        all_diffs.extend(diffs)
        print(f"  {file_path.name}: {count} rewrite(s)")

    print(f"\nTotal: {total_injected} injections across {len(by_file)} files")

    if args.dry_run and all_diffs:
        generate_diff_report(all_diffs)
    elif not args.dry_run and total_injected > 0:
        print(f"Backups saved to {BACKUP_DIR}")


if __name__ == "__main__":
    main()
