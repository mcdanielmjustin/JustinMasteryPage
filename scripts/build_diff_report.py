"""Build a self-contained HTML before/after diff report from prose_rewrites.json."""
import json, pathlib, sys, html as html_mod

DATA_DIR = pathlib.Path(__file__).resolve().parent / "data"


def main():
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    rewrites = json.loads((DATA_DIR / "prose_rewrites.json").read_text(encoding="utf-8"))

    items = []
    for r in rewrites:
        fp = r.get("file_path", "").replace("\\", "/")
        items.append({
            "d": r["domain_code"],
            "ch": r.get("chapter_title", ""),
            "h": r["heading_text"],
            "p": r["problem_type"],
            "f": fp,
            "o": r["section_html"],
            "n": r["rewritten_html"],
        })

    js_data = json.dumps(items, ensure_ascii=False)

    template = (DATA_DIR / "prose_diff_template.html").read_text(encoding="utf-8")
    output = template.replace("__DATA_PLACEHOLDER__", js_data)
    out_path = DATA_DIR / "prose_diff_report.html"
    out_path.write_text(output, encoding="utf-8")
    print(f"Wrote {len(items)} diffs to {out_path}")


if __name__ == "__main__":
    main()
