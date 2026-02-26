"""
retag_questions.py
Retags all vignette and contrast questions from the old 11-domain structure
into the new 9-domain structure, then writes organized JSON files to mastery-page/data/.
"""

import json
import os
from collections import defaultdict

# ── New domain registry ──────────────────────────────────────────────────────
NEW_DOMAINS = {
    'PMET': 'Psychometrics & Research Methods',
    'LDEV': 'Lifespan & Developmental Stages',
    'CPAT': 'Clinical Psychopathology',
    'PTHE': 'Psychotherapy Models, Interventions & Prevention',
    'SOCU': 'Social & Cultural Psychology',
    'WDEV': 'Workforce Development & Leadership',
    'BPSY': 'Biopsychology',
    'CASS': 'Clinical Assessment & Interpretation',
    'PETH': 'Psychopharmacology & Ethics',
}

# ── Simple 1-to-1 domain mappings ────────────────────────────────────────────
SIMPLE = {
    'ETH': 'PETH',   # Ethics, Legal & Professional  → Psychopharmacology & Ethics
    'LIF': 'LDEV',   # Lifespan Development           → Lifespan & Developmental Stages
    'ORG': 'WDEV',   # Industrial/Org Psychology      → Workforce Development & Leadership
    'PHY': 'BPSY',   # Biological Bases of Behavior   → Biopsychology
    'PPA': 'CPAT',   # Psychopathology & Personality  → Clinical Psychopathology
    'RMS': 'PMET',   # Research Methods & Statistics  → Psychometrics & Research Methods
    'SOC': 'SOCU',   # Social Psychology              → Social & Cultural Psychology
}

# ── Subdomain-level mappings for split domains ───────────────────────────────
CLI_MAP = {
    'Cross-Cultural Issues - Terms and Concepts':        'SOCU',
    'Cross-Cultural Issues - Identity Development Models': 'SOCU',
    'Prevention, Consultation, and Psychotherapy Research': 'PTHE',
    'Family Therapies and Group Therapies':              'PTHE',
    'Family and Group Therapies':                        'PTHE',
    'Cognitive-Behavioral Therapies':                    'PTHE',
    'Brief Therapies':                                   'PTHE',
    'Psychodynamic and Humanistic Therapies':            'PTHE',
    'Psychodynamic & Humanistic Therapies':              'PTHE',
}

LEA_MAP = {
    'Memory and Forgetting':                        'BPSY',
    'Operant Conditioning':                         'PMET',
    'Classical Conditioning':                       'PMET',
    'Interventions Based on Operant Conditioning':  'PTHE',
    'Interventions Based on Classical Conditioning': 'PTHE',
}

PAS_MAP = {
    'Stanford-Binet and Wechsler Tests':   'CASS',
    'Clinical Tests':                      'CASS',
    'Other Measures of Cognitive Ability': 'CASS',
    'Other Measures of Personality':       'CASS',
    'MMPI-2':                              'CASS',
    'Interest Inventories':                'CASS',
}

TES_MAP = {
    'Item Analysis and Test Reliability':         'PMET',
    'Test Validity - Criterion-Related Validity': 'PMET',
    'Test Validity - Content and Construct Validity': 'PMET',
    'Test Score Interpretation':                  'CASS',
}

SPLIT_MAPS = {
    'CLI': CLI_MAP,
    'LEA': LEA_MAP,
    'PAS': PAS_MAP,
    'TES': TES_MAP,
}


def assign_new_domain(old_code, subdomain):
    """Return the new domain code for a question given its old code + subdomain."""
    if old_code in SIMPLE:
        return SIMPLE[old_code]
    if old_code in SPLIT_MAPS:
        mapping = SPLIT_MAPS[old_code]
        if subdomain in mapping:
            return mapping[subdomain]
        # Fallback: print warning and use best-guess
        print(f'  WARNING: unmapped subdomain [{old_code}] "{subdomain}" — defaulting to PMET')
        return 'PMET'
    print(f'  WARNING: unknown old domain code "{old_code}"')
    return 'PMET'


# ── Process vignette files ───────────────────────────────────────────────────
VIGNETTE_DIR = 'C:/Users/mcdan/JustinQuestionsDatabase/data/vignettes/'
OUT_DIR = 'C:/Users/mcdan/mastery-page/data/'

print('=== Processing vignettes ===')

# Bucket questions by new domain
vignette_buckets = defaultdict(list)
total_in = 0

for fname in sorted(os.listdir(VIGNETTE_DIR)):
    if not fname.endswith('.json'):
        continue
    with open(VIGNETTE_DIR + fname, encoding='utf-8') as f:
        d = json.load(f)

    old_code = d['domain_code']
    questions = d['vignette_questions']
    total_in += len(questions)
    print(f'  {old_code}: {len(questions)} questions')

    for q in questions:
        new_code = assign_new_domain(old_code, q['subdomain'])
        # Add new domain tags; preserve old ones
        q['legacy_domain_code'] = old_code
        q['legacy_domain_name'] = d['domain_name']
        q['domain_code'] = new_code
        q['domain_name'] = NEW_DOMAINS[new_code]
        vignette_buckets[new_code].append(q)

print(f'\n  Total in: {total_in}')

# Write one JSON file per new domain
total_out = 0
for code in sorted(NEW_DOMAINS.keys()):
    questions = vignette_buckets.get(code, [])
    total_out += len(questions)
    out = {
        'domain_code': code,
        'domain_name': NEW_DOMAINS[code],
        'question_type': 'vignette',
        'total': len(questions),
        'questions': questions,
    }
    out_path = f'{OUT_DIR}{code}_vignettes.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f'  Wrote {code}_vignettes.json — {len(questions)} questions')

print(f'\n  Total out: {total_out}')

# ── Process contrast (This or That) questions ────────────────────────────────
print('\n=== Processing contrast questions ===')

CONTRAST_FILE = 'C:/Users/mcdan/JustinQuestionsDatabase/data/contrast_questions/eppp_contrast_questions.json'
with open(CONTRAST_FILE, encoding='utf-8') as f:
    contrast_data = json.load(f)

contrast_qs = contrast_data['questions']
print(f'  Total in: {len(contrast_qs)}')

contrast_buckets = defaultdict(list)

for q in contrast_qs:
    old_code = q['domain_code']
    subdomain = q.get('subdomain', '')
    new_code = assign_new_domain(old_code, subdomain)
    q['legacy_domain_code'] = old_code
    q['legacy_domain_name'] = q['domain_name']
    q['domain_code'] = new_code
    q['domain_name'] = NEW_DOMAINS[new_code]
    contrast_buckets[new_code].append(q)

# Write one combined contrast file with all questions retagged
all_contrast_out = {
    'metadata': {
        **contrast_data['metadata'],
        'domain_structure': 'new_9_domain',
        'domains': list(NEW_DOMAINS.keys()),
    },
    'questions': contrast_qs,
}
combined_path = f'{OUT_DIR}contrast_questions.json'
with open(combined_path, 'w', encoding='utf-8') as f:
    json.dump(all_contrast_out, f, ensure_ascii=False, indent=2)
print(f'  Wrote contrast_questions.json — {len(contrast_qs)} questions')

# Also write per-domain contrast files
for code in sorted(NEW_DOMAINS.keys()):
    questions = contrast_buckets.get(code, [])
    if not questions:
        continue
    out = {
        'domain_code': code,
        'domain_name': NEW_DOMAINS[code],
        'question_type': 'contrast',
        'total': len(questions),
        'questions': questions,
    }
    out_path = f'{OUT_DIR}{code}_contrast.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f'  Wrote {code}_contrast.json — {len(questions)} questions')

# ── Summary ──────────────────────────────────────────────────────────────────
print('\n=== Domain distribution summary ===')
print(f'{"Code":<6} {"Name":<48} {"Vignettes":>10} {"Contrast":>9}')
print('-' * 76)
for code, name in NEW_DOMAINS.items():
    v_count = len(vignette_buckets.get(code, []))
    c_count = len(contrast_buckets.get(code, []))
    print(f'{code:<6} {name:<48} {v_count:>10} {c_count:>9}')

print('-' * 76)
v_total = sum(len(v) for v in vignette_buckets.values())
c_total = sum(len(v) for v in contrast_buckets.values())
print(f'{"TOTAL":<6} {"":<48} {v_total:>10} {c_total:>9}')
print('\nDone.')
