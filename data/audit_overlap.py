"""
Find quiz questions where anatomically overlapping region pairs
appear as competing answer choices.
"""
import re
import sys

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


def get_str_array(block, name):
    idx = block.find('"' + name + '":')
    if idx == -1:
        return []
    bracket = block.index('[', idx)
    depth, pos = 0, bracket
    while pos < len(block):
        if block[pos] == '[':
            depth += 1
        elif block[pos] == ']':
            depth -= 1
            if depth == 0:
                break
        pos += 1
    arr = block[bracket:pos+1]
    return re.findall(r'"([a-z_]+)"', arr)


# These pairs share significant surface geometry in the atlas meshes
CONFLICT_PAIRS = [
    frozenset({'parietal_lobe', 'somatosensory_cortex'}),
    frozenset({'frontal_lobe', 'motor_cortex'}),
    frozenset({'frontal_lobe', 'prefrontal_cortex'}),
    frozenset({'frontal_lobe', 'brocas_area'}),
    frozenset({'temporal_lobe', 'wernickes_area'}),
    frozenset({'motor_cortex', 'somatosensory_cortex'}),
    frozenset({'prefrontal_cortex', 'brocas_area'}),
]

ids = re.findall(r'"id":\s*"(BRAIN-\d+)"', content)
print(f"Scanning {len(ids)} questions for overlapping answer pairs...\n")

found = []
for qid in ids:
    block = find_block(content, qid)
    if not block:
        continue
    qtype = get_string_field(block, 'type')
    if qtype not in ('deficit_to_location', 'case_to_location'):
        continue
    target = get_string_field(block, 'target_region')
    distractors = get_str_array(block, 'distractor_regions')
    all_ids = frozenset([target] + distractors)
    for pair in CONFLICT_PAIRS:
        if pair.issubset(all_ids):
            found.append((qid, sorted(pair), target, distractors))
            break

if found:
    for qid, pair, target, distractors in found:
        print(f"{qid}: OVERLAPPING PAIR {pair}")
        print(f"  target={target}")
        print(f"  distractors={distractors}")
else:
    print("No questions found with overlapping region pairs as answer choices.")
