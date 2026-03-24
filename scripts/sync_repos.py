"""
sync_repos.py  (Phase 6 — content-only sync)

Sync <section class="content-section"> bodies from mastery-page/content
to PassEPPP-website/content WITHOUT overwriting PassEPPP HTML shells
(branding, layout, scripts, nav).

Run:
  python scripts/sync_repos.py --all
  python scripts/sync_repos.py --domain PMET
  python scripts/sync_repos.py --dry-run --all
"""

import pathlib, argparse, sys, re

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
MASTERY_CONTENT = SCRIPTS_DIR.parent / "content"
PASSEPPP_CONTENT = pathlib.Path("C:/Users/mcdan/PassEPPP-website/content")

DOMAIN_DIRS = [f"domain{i}" for i in range(1, 10)]

# PassEPPP shell markers — at least one must survive in output
PASSEPPP_MARKERS = ["PassEPPP", "1100px", "dashboard.html"]

CONTENT_START_PATTERN = 'class="content-section"'  # matches both <section> and <div>
NAV_BUTTONS_PATTERN = '<div class="nav-buttons">'


def _find_content_boundaries(lines):
    """Find start/end line indices of the content body.

    Returns (start_idx, end_idx) or (None, None) if boundaries not found.
    start_idx = first line containing class="content-section" as an HTML element
    end_idx   = last non-blank line before <div class="nav-buttons">

    This captures all content sections (whether <section> or <div> based)
    and everything between them, stopping right before the nav-buttons div.
    """
    start_idx = None
    nav_idx = None

    # Forward-scan for first content section (must be an opening tag, not CSS)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if CONTENT_START_PATTERN in stripped and (
            stripped.startswith("<section") or stripped.startswith("<div")
        ):
            start_idx = i
            break

    if start_idx is None:
        return None, None

    # Forward-scan from start for nav-buttons
    for i in range(start_idx + 1, len(lines)):
        if NAV_BUTTONS_PATTERN in lines[i]:
            nav_idx = i
            break

    if nav_idx is None:
        # Fallback: look for </main>
        for i in range(start_idx + 1, len(lines)):
            if "</main>" in lines[i]:
                nav_idx = i
                break

    if nav_idx is None:
        return None, None

    # Backward-scan from nav_idx to find last non-blank, non-comment line
    end_idx = nav_idx - 1
    while end_idx > start_idx and lines[end_idx].strip() in ("", "<!-- Navigation -->"):
        end_idx -= 1

    return start_idx, end_idx


def extract_content_body(file_path):
    """Extract the content body (all <section class="content-section"> blocks).

    Returns the content as a string, or None if boundaries not found.
    """
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    start_idx, end_idx = _find_content_boundaries(lines)
    if start_idx is None or end_idx is None:
        return None

    content = "".join(lines[start_idx:end_idx + 1])

    # Validate: must contain at least one content section and ≥10 lines
    line_count = end_idx - start_idx + 1
    if line_count < 10:
        return None

    return content


def inject_content_body(dst_path, new_content):
    """Replace the content body in dst_path with new_content.

    Returns the reconstructed full file text, or None if boundaries not found.
    """
    text = dst_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    start_idx, end_idx = _find_content_boundaries(lines)
    if start_idx is None or end_idx is None:
        return None

    # Preserve everything before start_idx and from end_idx+1 onward
    before = lines[:start_idx]
    after = lines[end_idx + 1:]

    # Ensure new_content ends with a newline for clean joining
    if new_content and not new_content.endswith("\n"):
        new_content += "\n"

    return "".join(before) + new_content + "".join(after)


def _normalize_whitespace(text):
    """Collapse whitespace for comparison."""
    return re.sub(r'\s+', ' ', text).strip()


def content_bodies_match(src_path, dst_path):
    """Return True if content bodies are identical after whitespace normalization."""
    src_body = extract_content_body(src_path)
    dst_body = extract_content_body(dst_path)

    if src_body is None or dst_body is None:
        return False  # Can't compare — treat as different

    return _normalize_whitespace(src_body) == _normalize_whitespace(dst_body)


def _check_shell_integrity(output_text):
    """Verify at least one PassEPPP marker exists in the output."""
    for marker in PASSEPPP_MARKERS:
        if marker in output_text:
            return True
    return False


def sync_domain(domain_dir, dry_run=False):
    """Sync content sections for all HTML files in a domain directory.

    Returns (synced, skipped, extract_failures, inject_failures, safety_failures).
    """
    src_dir = MASTERY_CONTENT / domain_dir
    dst_dir = PASSEPPP_CONTENT / domain_dir

    if not src_dir.exists():
        print(f"  WARNING: Source {src_dir} not found")
        return 0, 0, 0, 0, 0

    synced = 0
    skipped = 0
    extract_fails = []
    inject_fails = []
    safety_fails = []

    for src_file in sorted(src_dir.glob("*.html")):
        dst_file = dst_dir / src_file.name
        label = f"{domain_dir}/{src_file.name}"

        # Step 1: Extract content body from source
        src_body = extract_content_body(src_file)
        if src_body is None:
            extract_fails.append(label)
            continue

        # Step 2: Skip if destination doesn't exist (no shell to inject into)
        if not dst_file.exists():
            extract_fails.append(f"{label} [no destination]")
            continue

        # Step 3: Compare content bodies — skip if identical
        if content_bodies_match(src_file, dst_file):
            skipped += 1
            continue

        # Step 4: Inject source content into destination shell
        output_text = inject_content_body(dst_file, src_body)
        if output_text is None:
            inject_fails.append(label)
            continue

        # Step 5: Pre-write safety checks
        # 5a: Shell integrity — output must contain PassEPPP markers
        if not _check_shell_integrity(output_text):
            safety_fails.append(f"{label} [missing PassEPPP markers]")
            continue

        # 5b: Size sanity — output must be ≥50% of original destination size
        original_size = dst_file.stat().st_size
        new_size = len(output_text.encode("utf-8"))
        if new_size < original_size * 0.5:
            safety_fails.append(f"{label} [size dropped to {new_size}/{original_size} bytes]")
            continue

        # Step 6: Write or report
        if dry_run:
            src_lines = src_body.count("\n")
            dst_body = extract_content_body(dst_file)
            dst_lines = dst_body.count("\n") if dst_body else 0
            print(f"  DRY RUN: {label} [content: {dst_lines}→{src_lines} lines]")
        else:
            dst_file.write_text(output_text, encoding="utf-8")
            print(f"  {label} [content synced]")

        synced += 1

    return synced, skipped, extract_fails, inject_fails, safety_fails


def main():
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Sync content sections from mastery-page to PassEPPP-website "
                    "(preserves PassEPPP HTML shell)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--domain", type=str, help="Single domain code (e.g. PMET)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    domain_code_map = {
        "PMET": "domain1", "LDEV": "domain2", "CPAT": "domain3", "PTHE": "domain4",
        "SOCU": "domain5", "WDEV": "domain6", "BPSY": "domain7", "CASS": "domain8",
        "PETH": "domain9",
    }

    if args.domain:
        code = args.domain.upper()
        if code not in domain_code_map:
            print(f"ERROR: Unknown domain {code}")
            sys.exit(1)
        domains = [domain_code_map[code]]
    else:
        domains = DOMAIN_DIRS

    if not PASSEPPP_CONTENT.parent.exists():
        print(f"ERROR: PassEPPP-website not found at {PASSEPPP_CONTENT.parent}")
        sys.exit(1)

    mode = " (DRY RUN)" if args.dry_run else ""
    print(f"Content-only sync: mastery-page → PassEPPP-website{mode}")
    print(f"  (preserves PassEPPP shell: branding, layout, scripts)\n")

    total_synced = 0
    total_skipped = 0
    all_extract_fails = []
    all_inject_fails = []
    all_safety_fails = []

    for domain_dir in domains:
        synced, skipped, ef, ij, sf = sync_domain(domain_dir, dry_run=args.dry_run)
        total_synced += synced
        total_skipped += skipped
        all_extract_fails.extend(ef)
        all_inject_fails.extend(ij)
        all_safety_fails.extend(sf)

    # Summary
    print(f"\n{'─' * 50}")
    print(f"  Synced:   {total_synced} files {'(would sync)' if args.dry_run else '(content updated)'}")
    print(f"  Skipped:  {total_skipped} files (content identical)")

    if all_extract_fails:
        print(f"  Extract failures: {len(all_extract_fails)}")
        for f in all_extract_fails:
            print(f"    - {f}")

    if all_inject_fails:
        print(f"  Inject failures: {len(all_inject_fails)}")
        for f in all_inject_fails:
            print(f"    - {f}")

    if all_safety_fails:
        print(f"  Safety check failures: {len(all_safety_fails)}")
        for f in all_safety_fails:
            print(f"    - {f}")

    if not args.dry_run and total_synced > 0:
        print(f"\nNext step: Re-run PassEPPP-website/scripts/backfill_db_intros.py "
              "to update Supabase DB")


if __name__ == "__main__":
    main()
