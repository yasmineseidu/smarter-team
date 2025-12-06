# Waterfall Email Enrichment Agent

## Category
Lead Generation & Data

## Purpose
Find valid emails for leads without them

## Inputs
- Leads with invalid/missing emails
- Lead name, company, domain

## Outputs
- Found emails with confidence scores
- Enrichment source tracking

## Process (Waterfall Order)
1. Try Muraena → if found, verify with Reoon
2. Try Tomba → if found, verify with Reoon
3. Try Nimbler → if found, verify with Reoon
4. Try Voila Norbert → if found, verify with Reoon
5. Try Icypeas → if found, verify with Reoon
6. Try Anymail Finder → if found, verify with Reoon
7. Try Findymail → if found, verify with Reoon
8. If all fail, mark as UNENRICHABLE

## Database Tables
- `enrichment_attempts`
- `enrichment_results`
- `enrichment_costs`

## Integrations
- Muraena API
- Tomba API
- Nimbler API
- Voila Norbert API
- Icypeas API
- Anymail Finder API
- Findymail API
- Reoon API (for verification)

## Priority
Phase 6 - Multi-Channel & Advanced

## Dependencies
- Email Verification Agent (triggers when email invalid/unknown)

## Human-in-the-Loop
- None (fully automated)

## Cost Tracking
- Track cost per enrichment attempt
- Track cost per successful enrichment
