"""Parallel visual-aid generator — 20 concurrent workers.
Wraps generate_visual_aids.py logic with ThreadPoolExecutor.

Usage:
  python scripts/generate_visual_aids_parallel.py --resume --workers 20
"""

import json, pathlib, sys, os, re, time, datetime, threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Reuse everything from the original script
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from generate_visual_aids import (
    discover_chapters, generate_for_chapter, build_visual_aid_html,
    load_api_key, OUTPUT_FILE, DEFAULT_CONTENT_DIR, DEFAULT_MODEL,
    SYSTEM_PROMPT,
)

import anthropic

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CONTENT_DIR = pathlib.Path(r"C:\Users\Admin\JustinMasteryPage\content")
MAX_PER_CHAPTER = 3

# Thread-safe file writing
_lock = threading.Lock()
_all_vas = []


def process_chapter(client, model, ch, idx, total):
    """Process one chapter — called from thread pool."""
    rel = ch["rel_path"]
    items = generate_for_chapter(client, model, ch, MAX_PER_CHAPTER)

    if not items:
        print(f"  [{idx}/{total}] {rel}: 0 visual aids")
        return []

    chapter_slug = ch["path"].stem
    chapter_vas = []

    for j, item in enumerate(items):
        required = {"title", "layout_type", "anchor_heading", "inner_html"}
        if not required.issubset(item.keys()):
            continue

        va_id = f"va-{ch['domain_code']}-{chapter_slug}-{j+1:03d}"
        full_html = build_visual_aid_html(va_id, item["title"], item["inner_html"])

        va_record = {
            "id": va_id,
            "chapter_file": rel,
            "domain_code": ch["domain_code"],
            "anchor_heading": item["anchor_heading"],
            "title": item["title"],
            "layout_type": item["layout_type"],
            "html": full_html,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        chapter_vas.append(va_record)

    layout_types = set(v["layout_type"] for v in chapter_vas)
    print(f"  [{idx}/{total}] {rel}: {len(chapter_vas)} aids ({', '.join(layout_types)})")

    # Thread-safe save
    with _lock:
        _all_vas.extend(chapter_vas)
        OUTPUT_FILE.write_text(
            json.dumps(_all_vas, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return chapter_vas


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--api-key", type=str)
    args = parser.parse_args()

    global _all_vas

    api_key = load_api_key(args.api_key)
    client = anthropic.Anthropic(api_key=api_key)

    # Load existing
    existing_chapters = set()
    if OUTPUT_FILE.exists():
        _all_vas = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        existing_chapters = {va["chapter_file"] for va in _all_vas}

    # Discover chapters
    chapters = discover_chapters(CONTENT_DIR)
    if args.resume:
        todo = [ch for ch in chapters if ch["rel_path"] not in existing_chapters]
    else:
        todo = chapters

    print(f"Total chapters: {len(chapters)}, already done: {len(existing_chapters)}, remaining: {len(todo)}")
    print(f"Workers: {args.workers}, model: {args.model}\n")

    if not todo:
        print("Nothing to do!")
        return

    total = len(todo)
    generated = 0

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {}
        for i, ch in enumerate(todo, 1):
            f = executor.submit(process_chapter, client, args.model, ch, i, total)
            futures[f] = ch

        for f in as_completed(futures):
            try:
                result = f.result()
                generated += len(result)
            except Exception as e:
                ch = futures[f]
                print(f"  ERROR on {ch['rel_path']}: {e}")

    # Final stats
    from collections import Counter
    layouts = Counter(v["layout_type"] for v in _all_vas)
    print(f"\n{'='*60}")
    print(f"Generated {generated} new visual aids ({len(_all_vas)} total)")
    print(f"\nLayout distribution:")
    for l, c in layouts.most_common():
        print(f"  {l:<20} {c:>3} ({c*100//len(_all_vas)}%)")
    domains = Counter(v["domain_code"] for v in _all_vas)
    print(f"\nBy domain:")
    for d, c in sorted(domains.items()):
        print(f"  {d}: {c}")


if __name__ == "__main__":
    main()
