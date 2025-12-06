# Technographic Data Agent

## Category
Lead Generation & Data

## Purpose
Identify prospect tech stack

## Data Points
- CRM used
- Marketing automation
- Website platform
- Analytics tools
- Payment processors
- Communication tools

## Sources
- BuiltWith API
- Wappalyzer
- Job posting analysis
- Website scraping

## Process
1. Query tech detection APIs
2. Parse job postings for tool mentions
3. Update company tech stack record
4. Flag relevant tech signals (e.g., using competitor tools)

## Database Tables
- `company_tech_stack`
- `tech_signals`

## Integrations
- BuiltWith API
- Wappalyzer API
- Job board APIs

## Priority
Phase 6 - Multi-Channel & Advanced

## Dependencies
- Company Research Agent (provides company context)

## Human-in-the-Loop
- None (fully automated)

## Use Cases
- Target companies using competitor tools
- Identify companies with compatible tech stack
- Personalization based on tools they use
