# Niche Research Agent

## Category
Research & Intelligence

## Purpose
Identify profitable niches to prospect

## Inputs
- Industry keywords
- Revenue/employee size criteria
- Geographic focus
- Service offering match criteria

## Outputs
- Scored niche recommendations
- Market size estimates
- Competition analysis
- Pain point summaries
- Recommended personas per niche

## Process
1. Search Reddit, LinkedIn, forums for pain points in target industry
2. Analyze job postings for common problems
3. Research competitor offerings and gaps
4. Score niche on: market size, pain intensity, ability to pay, competition level
5. Generate niche report with recommendations

## Database Tables
- `niches`
- `niche_scores`
- `niche_research_sources`

## Integrations
- Apify (Reddit scraping)
- Serper (web search)
- LinkedIn scraping

## Priority
Phase 2 - Intelligence Layer

## Dependencies
None (standalone research agent)

## Human-in-the-Loop
- Niche selection requires approval before targeting
