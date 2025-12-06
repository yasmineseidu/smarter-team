# Duplicate Detection Agent

## Category
Lead Generation & Data

## Purpose
Prevent duplicate leads across databases

## Matching Criteria (Fuzzy)
- Exact email match
- Name + company match (fuzzy)
- LinkedIn URL match
- Phone number match

## Process
1. Check new leads against existing database
2. Score match confidence
3. Auto-merge exact matches
4. Flag fuzzy matches for human review
5. Log all duplicate decisions

## Database Tables
- `duplicate_checks`
- `merge_logs`

## Integrations
- None (internal database operations)

## Priority
Phase 1 - MVP Foundation (part of Lead List Builder)

## Dependencies
- Lead List Builder Agent (runs during import)

## Human-in-the-Loop
- Fuzzy matches require human approval before merge

## Algorithm
- Use Levenshtein distance for name matching
- Domain normalization for email matching
- Confidence threshold: 85% for auto-merge, 60-84% for review
