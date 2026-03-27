# JustinMasteryPage -- Source of Truth for EPPP Textbook

## What this repo is
The canonical EPPP exam prep textbook. 124 chapters across 9 domains. All other copies (PassEPPP-website) are downstream deployments of this content.

## Source of truth hierarchy

| Data | Location | Notes |
|---|---|---|
| **Textbook content** | `JustinMasteryPage/content/domain[1-9]/` | 124 chapters. This is THE textbook. |
| **Anchor manifest** | `JustinQuestionsDatabase-2.0/data/anchor_manifest.json` | 1,567 anchors, `in_book` field shows which have content (currently 1,081). |
| **In-book anchors** | `JustinQuestionsDatabase-2.0/data/anchor_map_v2.json` | 1,081 records -- the in-book subset. |
| **Domain design** | `EPPP-Domain-Design/anchor_points_by_domain/Domain_*.txt` | 9 files defining which anchors belong to which domain. This is the architecture. |
| **Anchor coverage stats** | `JustinQuestionsDatabase-2.0/data/anchor_coverage_source.json` | Per-domain summary. |
| **Per-domain anchor lists** | `JustinQuestionsDatabase-2.0/data/reference/anchors_domain*_*.json` | Per-domain splits of the manifest. |
| **Local script data** | `JustinMasteryPage/scripts/data/` | Copies of anchor_manifest.json, anchor_map_v2.json, anchor_coverage_source.json for local scripts. Keep in sync with JustinQuestionsDatabase-2.0. |

## DO NOT read from these locations

| Location | Why |
|---|---|
| `ethan-old-questions/` | Archive only. Contains stale anchor data, old textbook versions, and retired repos. |
| `ethan-old-questions/stale_anchor_data/` | Old coverage_audit.json (921 in-book), old anchors_parsed.json -- superseded by JustinQuestionsDatabase-2.0 data. |
| `PassEPPP-website/content/domain*/` | COPY of this repo's content, deployed to Vercel. Do not treat as source. Edit here, deploy there. |
| `PassEPPP-website/pages/mastery/content/domain*/` | COPY of this repo's content. Same rule. |

## Domain structure (9-domain system)

| # | Code | Name | Chapters |
|---|---|---|---|
| 1 | PMET | Psychometrics & Research Methods | 17 |
| 2 | LDEV | Lifespan Development | 11 |
| 3 | CPAT | Clinical Psychopathology | 14 |
| 4 | PTHE | Psychotherapy Models, Interventions & Prevention | 12 |
| 5 | SOCU | Social & Cultural Psychology | 12 |
| 6 | WDEV | Workforce Development & Leadership | 12 |
| 7 | BPSY | Biopsychology | 14 |
| 8 | CASS | Clinical Assessment & Interpretation | 15 |
| 9 | PETH | Psychopharmacology & Ethics | 17 |

## Domain content rules

- **D3 (Psychopathology)** teaches diagnoses, criteria, etiology, epidemiology, course/prognosis. Treatment content belongs in D4/D8/D9.
- **D4 (Psychotherapy)** teaches therapy models and intervention techniques.
- **D8 (Assessment)** teaches assessment instruments, score interpretation, and evidence-based treatment protocols (EBT chapters).
- **D9 (Pharma/Ethics)** teaches APA ethics standards and psychopharmacology.
- Content should only exist in a domain if it's backed by an anchor point assigned to that domain in EPPP-Domain-Design.
- Supplemental content (clinical context, brief cross-references) is acceptable. Full standalone treatment sections in the wrong domain are not.

## Anchor ID system

- Anchor IDs are **NOT globally unique** across domains. The same numeric ID (e.g., `001`) can exist in multiple domains.
- To identify a specific anchor, you need both the domain code and the anchor ID.
- `anchor_manifest.json` uses a `uid` field (e.g., `D1-LEA-020-fba878e3`) for global uniqueness.
- HTML files embed anchors as `<!-- anchor:XXX coverage:partial -->` where XXX is the domain-local ID.

## Deployment

- Edit textbook content in `JustinMasteryPage/content/domain*/`.
- Copy to both `PassEPPP-website/content/domain*/` and `PassEPPP-website/pages/mastery/content/domain*/` before deploying.
- PassEPPP-website auto-deploys via Vercel on push to `main`.
- Both `/textbook` and `/mastery/textbook` serve from their respective content directories.

## Active repos on this machine

| Repo | Purpose |
|---|---|
| `EPPP-Domain-Design` | Domain architecture, anchor-to-domain assignments |
| `JustinMasteryPage` | Textbook source of truth |
| `JustinQuestionsDatabase-2.0` | Anchor data, question generation pipeline |
| `JustinPipeline` | Lecture slide pipeline |
| `MiniPipeline` | Mini lecture pipeline |
| `P-Question-Database` | Supplemental exam questions |
| `PassEPPP-Database` | Supabase backend |
| `PassEPPP-website` | Deployed website (Vercel) |
| `ethan-old-questions` | Archive -- do not use as data source |
| `patient-encounter-dev` | 3D avatar project (separate) |
