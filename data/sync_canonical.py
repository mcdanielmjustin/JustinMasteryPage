"""
Sync updated questions from brain_data.js to the canonical JustinQuestionsDatabase store.
"""
import re
import json

BRAIN_DATA_JS = r"C:\Users\mcdan\mastery-page\data\brain_data.js"
CANONICAL_JSON = r"C:\Users\mcdan\JustinQuestionsDatabase\data\brain\brain_pathology_30.json"
TARGETS = ["BRAIN-108", "BRAIN-114", "BRAIN-122"]

with open(BRAIN_DATA_JS, encoding="utf-8") as f:
    content = f.read()

def get_field(block, name):
    """Extract a JSON string field value, handling escaped chars."""
    idx = block.find(f'"{name}":')
    if idx == -1:
        return ""
    colon = block.index(":", idx)
    val_start = block.index('"', colon) + 1
    pos = val_start
    while pos < len(block):
        c = block[pos]
        if c == "\\":
            pos += 2
            continue
        if c == '"':
            break
        pos += 1
    return block[val_start:pos]

def find_block(content, qid):
    """Find the full JSON object for a question ID."""
    idx = content.find(f'"id": "{qid}"')
    if idx == -1:
        idx = content.find(f'"id":"{qid}"')
    if idx == -1:
        return None
    brace = content.rfind("{", 0, idx)
    depth, pos = 0, brace
    while pos < len(content):
        if content[pos] == "{":
            depth += 1
        elif content[pos] == "}":
            depth -= 1
            if depth == 0:
                break
        pos += 1
    return content[brace : pos + 1]

# Extract updated fields from brain_data.js
updated = {}
for qid in TARGETS:
    block = find_block(content, qid)
    if block:
        updated[qid] = {
            "question": get_field(block, "question"),
            "explanation": get_field(block, "explanation"),
        }
        print(f"{qid}: extracted ({len(updated[qid]['question'])} chars Q)")
    else:
        print(f"{qid}: not found in brain_data.js!")

# Load canonical store
with open(CANONICAL_JSON, encoding="utf-8") as f:
    data = json.load(f)

qs = data if isinstance(data, list) else data.get("questions", [])
changes = 0
for q in qs:
    qid = q.get("id")
    if qid in updated:
        q["question"] = updated[qid]["question"]
        q["explanation"] = updated[qid]["explanation"]
        changes += 1
        print(f"  Updated {qid} in canonical store")

with open(CANONICAL_JSON, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nSaved {changes} updates to canonical store.")
