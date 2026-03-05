"""Count case_to_location questions per category."""
import re, sys, collections
sys.stdout.reconfigure(encoding='utf-8')

BRAIN_DATA_JS = r"C:\Users\mcdan\mastery-page\data\brain_data.js"
with open(BRAIN_DATA_JS, encoding='utf-8') as f:
    content = f.read()

ids = re.findall(r'"id":\s*"(BRAIN-\d+)"', content)

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

def get_field(block, name):
    idx = block.find('"' + name + '":')
    if idx == -1:
        return ''
    colon = block.index(':', idx)
    vs = block.index('"', colon) + 1
    pos = vs
    while pos < len(block):
        c = block[pos]
        if c == '\\':
            pos += 2
            continue
        if c == '"':
            break
        pos += 1
    return block[vs:pos]

counts = collections.Counter()
for qid in ids:
    block = find_block(content, qid)
    if not block:
        continue
    if get_field(block, 'type') == 'case_to_location':
        counts[get_field(block, 'category')] += 1

print(f"case_to_location counts per category ({sum(counts.values())} total):\n")
for cat, n in sorted(counts.items(), key=lambda x: x[1]):
    flag = '  <-- UNDER 10' if n < 10 else ''
    print(f"  {cat:20s} {n}{flag}")
