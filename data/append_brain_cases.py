"""Append newly generated brain case questions from JDB into brain_data.js."""
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

JDB_FILE  = r'C:\Users\mcdan\JustinQuestionsDatabase\data\brain\brain_pathology_30.json'
BRAIN_JS  = r'C:\Users\mcdan\mastery-page\data\brain_data.js'

# IDs that need to be added (BRAIN-131 through BRAIN-207)
NEW_ID_RANGE = range(131, 208)

with open(JDB_FILE, encoding='utf-8') as f:
    jdb = json.load(f)

with open(BRAIN_JS, encoding='utf-8') as f:
    content = f.read()

# Find which IDs are already in brain_data.js
existing_ids = set(re.findall(r'"id":\s*"(BRAIN-\d+)"', content))

to_add = [q for q in jdb
          if int(q['id'].replace('BRAIN-', '')) in NEW_ID_RANGE
          and q['id'] not in existing_ids]

print(f'Questions to add: {len(to_add)}')
if not to_add:
    print('Nothing to do.')
    sys.exit(0)

# Build JS entries
entries = []
for q in to_add:
    dist = json.dumps(q['distractor_regions'])
    entry = (
        '  {\n'
        f'    "id": {json.dumps(q["id"])},\n'
        f'    "type": {json.dumps(q["type"])},\n'
        f'    "category": {json.dumps(q["category"])},\n'
        f'    "domain_source": {json.dumps(q.get("domain_source","PHY"))},\n'
        f'    "difficulty": {json.dumps(q.get("difficulty","hard"))},\n'
        f'    "question": {json.dumps(q["question"])},\n'
        f'    "target_region": {json.dumps(q["target_region"])},\n'
        f'    "distractor_regions": {dist},\n'
        f'    "explanation": {json.dumps(q["explanation"])}\n'
        '  }'
    )
    entries.append(entry)

insertion = ',\n' + ',\n'.join(entries)

# Find the closing pattern: \n  ]\n};
close_pat = '\n  ]\n};'
idx = content.rfind(close_pat)
if idx == -1:
    # Try alternate closing
    close_pat = '\n]\n};'
    idx = content.rfind(close_pat)
if idx == -1:
    print('ERROR: Could not locate closing ]\\n}; in brain_data.js')
    print('Last 50 chars:', repr(content[-50:]))
    sys.exit(1)

new_content = content[:idx] + insertion + content[idx:]

with open(BRAIN_JS, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f'Successfully appended {len(to_add)} questions to brain_data.js')
