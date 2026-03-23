"""
sync_repos.py  (Phase 6)

Copy modified HTML files from mastery-page/content to PassEPPP-website/content.
No API calls — pure file sync.

Run:
  python scripts/sync_repos.py --all
  python scripts/sync_repos.py --domain PMET
  python scripts/sync_repos.py --dry-run --all
"""

import pathlib, argparse, shutil, sys, filecmp

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
MASTERY_CONTENT = SCRIPTS_DIR.parent / "content"
PASSEPPP_CONTENT = pathlib.Path("C:/Users/mcdan/PassEPPP-website/content")

DOMAIN_DIRS = [f"domain{i}" for i in range(1, 10)]


def sync_domain(domain_dir, dry_run=False):
    """Sync all HTML files in a domain directory. Returns (copied, skipped, missing)."""
    src_dir = MASTERY_CONTENT / domain_dir
    dst_dir = PASSEPPP_CONTENT / domain_dir

    if not src_dir.exists():
        print(f"  WARNING: Source {src_dir} not found")
        return 0, 0, 1

    if not dst_dir.exists():
        if dry_run:
            print(f"  DRY RUN: Would create {dst_dir}")
        else:
            dst_dir.mkdir(parents=True, exist_ok=True)

    copied = 0
    skipped = 0

    for src_file in sorted(src_dir.glob("*.html")):
        dst_file = dst_dir / src_file.name

        # Skip if files are identical
        if dst_file.exists() and filecmp.cmp(src_file, dst_file, shallow=False):
            skipped += 1
            continue

        if dry_run:
            status = "NEW" if not dst_file.exists() else "MODIFIED"
            print(f"  DRY RUN: Would copy {domain_dir}/{src_file.name} [{status}]")
        else:
            shutil.copy2(src_file, dst_file)
            status = "NEW" if not dst_file.exists() else "updated"
            print(f"  {domain_dir}/{src_file.name} [{status}]")

        copied += 1

    return copied, skipped, 0


def main():
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Sync content from mastery-page to PassEPPP-website")
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

    print(f"Syncing mastery-page → PassEPPP-website{' (DRY RUN)' if args.dry_run else ''}...\n")

    total_copied = 0
    total_skipped = 0

    for domain_dir in domains:
        copied, skipped, _ = sync_domain(domain_dir, dry_run=args.dry_run)
        total_copied += copied
        total_skipped += skipped

    print(f"\nSync complete: {total_copied} files copied, {total_skipped} unchanged")

    if not args.dry_run and total_copied > 0:
        print("\nNext step: Re-run PassEPPP-website/scripts/backfill_db_intros.py "
              "to update Supabase DB")


if __name__ == "__main__":
    main()
