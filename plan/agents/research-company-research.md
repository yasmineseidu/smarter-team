# Company Research Agent

## Category
Research & Intelligence

## Purpose
Research companies for context and triggers

## Inputs
- Company name
- Website
- LinkedIn company page

## Outputs
- Recent news (funding, acquisitions, leadership changes)
- Job postings (growth signals, pain signals)
- Tech stack (via BuiltWith/Wappalyzer)
- Company size and growth rate
- Recent LinkedIn posts
- Press releases
- Competitive positioning
- Trigger events

## Process
1. Scrape company LinkedIn page
2. Search news for company name
3. Check job boards for their postings
4. Analyze tech stack
5. Review recent press/blog posts
6. Identify trigger events
7. Generate company brief

## Database Tables
- `company_research`
- `company_news`
- `company_jobs`
- `company_tech_stack`
- `trigger_events`

## Integrations
- Apify (LinkedIn scraping)
- Serper (web search)
- BuiltWith API
- Job board APIs

## Priority
Phase 2 - Intelligence Layer

## Dependencies
- Lead List Builder Agent (provides companies to research)

## Human-in-the-Loop
- None (automated research)
