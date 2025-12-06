# Persona Research Agent

## Category
Research & Intelligence

## Purpose
Deep understanding of target personas for messaging

## Inputs
- Job title/role
- Industry
- Company size range

## Outputs
- Day-in-the-life summary
- Common frustrations
- Goals and KPIs they're measured on
- Language they use (jargon, phrases)
- Where they hang out online
- What they read/follow
- Buying triggers
- Objection patterns

## Process
1. Scrape LinkedIn profiles matching persona
2. Analyze Reddit/forum discussions from this persona
3. Review industry publications they'd read
4. Compile behavioral patterns
5. Generate persona document

## Database Tables
- `personas`
- `persona_research`
- `persona_language_patterns`

## Integrations
- Apify (LinkedIn scraping)
- Serper (web search)
- Reddit API

## Priority
Phase 2 - Intelligence Layer

## Dependencies
- Niche Research Agent (provides niche context)

## Human-in-the-Loop
- Persona definitions reviewed before use in campaigns
