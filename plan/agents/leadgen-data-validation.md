# Data Validation Agent

## Category
Lead Generation & Data

## Purpose
Ensure data quality before campaigns

## Validation Rules

| Field | Rule | Action if Failed |
|-------|------|------------------|
| first_name | Not empty, not "N/A", not "Unknown" | Block from campaign |
| company_name | Not empty | Block from campaign |
| email | Valid format, verified status | Block from campaign |
| domain | Matches company | Flag for review |
| linkedin_url | Valid LinkedIn URL format | Optional, continue |
| job_title | Not empty | Optional, continue |

## Process
1. Run validation rules on leads before campaign assignment
2. Generate validation report
3. Block invalid leads from campaigns
4. Queue incomplete leads for enrichment
5. Log all validation failures

## Database Tables
- `validation_logs`
- `validation_rules`

## Integrations
- None (internal validation)

## Priority
Phase 1 - MVP Foundation

## Dependencies
- Email Verification Agent (provides verified status)

## Human-in-the-Loop
- Validation failures flagged for review may require manual fix
