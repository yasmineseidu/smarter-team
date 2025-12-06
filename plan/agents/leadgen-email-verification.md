# Email Verification Agent

## Category
Lead Generation & Data

## Purpose
Verify email addresses with Reoon

## Inputs
- List of emails to verify

## Outputs
- Verification results (valid, invalid, risky, unknown)
- Updated lead records

## Process
1. Batch emails to Reoon API
2. Process results
3. Mark valid emails as VERIFIED
4. Mark invalid as INVALID_EMAIL
5. Queue risky/unknown for waterfall enrichment

## Database Tables
- `email_verifications`
- `verification_results`

## Integrations
- Reoon API

## Priority
Phase 1 - MVP Foundation

## Dependencies
- Lead List Builder Agent (provides leads with emails)

## Human-in-the-Loop
- None (fully automated)

## Rate Limits
- Reoon: 10k/month - Alert at 90%
