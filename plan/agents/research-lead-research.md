# Lead Research Agent

## Category
Research & Intelligence

## Purpose
Research individual leads for personalization

## Inputs
- Lead name
- Company
- LinkedIn URL
- Email

## Outputs
- Recent LinkedIn posts/activity
- News mentions
- Podcast appearances
- Speaking engagements
- Awards/recognition
- Career history highlights
- Mutual connections
- Shared interests
- Recent achievements

## Process
1. Scrape LinkedIn profile (via Apify)
2. Search news for name + company
3. Search podcasts/YouTube for appearances
4. Check company press releases
5. Compile research summary
6. Flag best personalization angles

## Database Tables
- `lead_research`
- `lead_research_sources`
- `personalization_angles`

## Integrations
- Apify (LinkedIn scraping)
- Serper (web search)
- News APIs

## Priority
Phase 2 - Intelligence Layer

## Dependencies
- Lead List Builder Agent (provides leads to research)

## Human-in-the-Loop
- None (automated research, reviewed at personalization stage)
