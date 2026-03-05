"""
Scan brain_data.js for duplicate answer choices and truncated questions.
"""
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

BRAIN_DATA_JS = r"C:\Users\mcdan\mastery-page\data\brain_data.js"

with open(BRAIN_DATA_JS, encoding='utf-8') as f:
    content = f.read()


def find_block(content, qid):
    idx = content.find('"id": "' + qid + '"')
    if idx == -1:
        idx = content.find('"id":"' + qid + '"')
    if idx == -1:
        return None
    brace = content.rfind('{', 0, idx)
    depth, pos = 0, brace
    while pos < len(content):
        if content[pos] == '{':
            depth += 1
        elif content[pos] == '}':
            depth -= 1
            if depth == 0:
                break
        pos += 1
    return content[brace:pos+1]


def get_string_field(block, name):
    idx = block.find('"' + name + '":')
    if idx == -1:
        return ''
    colon = block.index(':', idx)
    val_start = block.index('"', colon) + 1
    pos = val_start
    while pos < len(block):
        c = block[pos]
        if c == '\\':
            pos += 2
            continue
        if c == '"':
            break
        pos += 1
    return block[val_start:pos]


def get_string_array(block, name):
    """Extract a JSON array of strings from a block."""
    idx = block.find('"' + name + '":')
    if idx == -1:
        return []
    bracket = block.index('[', idx)
    # Find matching close bracket
    depth, pos = 0, bracket
    while pos < len(block):
        if block[pos] == '[':
            depth += 1
        elif block[pos] == ']':
            depth -= 1
            if depth == 0:
                break
        pos += 1
    arr_str = block[bracket:pos+1]
    # Parse quoted strings (handling escape sequences)
    results = []
    i = 1  # skip opening [
    while i < len(arr_str) - 1:
        # skip whitespace and commas
        if arr_str[i] in ' \t\n\r,':
            i += 1
            continue
        if arr_str[i] == '"':
            i += 1
            start = i
            while i < len(arr_str):
                if arr_str[i] == '\\':
                    i += 2
                    continue
                if arr_str[i] == '"':
                    break
                i += 1
            results.append(arr_str[start:i])
        i += 1
    return results


ids = re.findall(r'"id":\s*"(BRAIN-\d+)"', content)
print(f"Total questions: {len(ids)}\n")

issues = []
for qid in ids:
    block = find_block(content, qid)
    if not block:
        issues.append(f"{qid}: block not found!")
        continue

    qtype = get_string_field(block, 'type')
    question = get_string_field(block, 'question')

    if qtype in ('deficit_to_location', 'case_to_location'):
        target = get_string_field(block, 'target_region')
        distractors = get_string_array(block, 'distractor_regions')
        all_choices = [target] + distractors

        # Duplicate check
        seen = Counter(all_choices)
        dups = [k for k, v in seen.items() if v > 1]
        if dups:
            issues.append(f"{qid} [{qtype}]: DUPLICATE region IDs: {dups}")
            issues.append(f"  target={target}, distractors={distractors}")

        # Wrong count
        if len(all_choices) != 4:
            issues.append(f"{qid}: WRONG choice count ({len(all_choices)}): target={target}, distractors={distractors}")

    elif qtype == 'location_to_deficit':
        opts = get_string_array(block, 'options')
        seen = Counter(opts)
        dups = [k for k, v in seen.items() if v > 1]
        if dups:
            issues.append(f"{qid} [location_to_deficit]: DUPLICATE options: {dups}")
        if len(opts) != 4:
            issues.append(f"{qid}: WRONG option count ({len(opts)})")

    else:
        issues.append(f"{qid}: UNKNOWN type: {repr(qtype)}")

print(f"Issues found: {len(issues)}")
for i in issues:
    print(i)
