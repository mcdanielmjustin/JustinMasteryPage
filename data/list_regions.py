"""List all region IDs used in brain_data.js (targets + distractors)."""
import re

with open('C:/Users/mcdan/mastery-page/data/brain_data.js', encoding='utf-8') as f:
    content = f.read()

all_regions = set()
all_regions.update(re.findall(r'"target_region":\s*"([a-z_]+)"', content))
for m in re.findall(r'"distractor_regions":\s*\[([^\]]+)\]', content):
    all_regions.update(re.findall(r'"([a-z_]+)"', m))

print(f"All available regions ({len(all_regions)}):")
for r in sorted(all_regions):
    print(f"  {r}")
