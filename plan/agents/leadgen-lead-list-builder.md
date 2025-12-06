# Lead List Builder Agent

## Category
Lead Generation & Data

## Purpose
Scrape and import leads from Apify

## Inputs
- Search criteria (title, industry, location, company size)
- Source (LinkedIn, Apollo, etc.)
- Volume needed

## Outputs
- Raw lead records
- Deduplication report
- Data quality report

## Process
1. Trigger Apify scrape with criteria
2. Receive webhook with results
3. Normalize data format
4. Check for duplicates against existing database
5. Flag incomplete records
6. Import valid leads as NEW status
7. Generate import report

## Database Tables
- `leads`
- `lead_sources`
- `import_logs`

## Integrations
- Apify (LinkedIn scraper, Apollo scraper)
- Webhook receiver

## Priority
Phase 1 - MVP Foundation

## Dependencies
None (entry point agent)

## Human-in-the-Loop
- Search criteria approved before scraping
- Import report reviewed for quality

## Webhook
- Receives: `apify/scrape_completed`
