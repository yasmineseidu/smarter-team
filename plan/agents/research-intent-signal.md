# Intent Signal Tracking Agent

## Category
Research & Intelligence

## Purpose
Detect buying signals from prospect behavior

## Signals to Track
- New job postings (hiring for roles you solve)
- Leadership changes (new decision makers)
- Funding announcements (budget available)
- Expansion news (new locations, markets)
- Technology changes (new tools, migrations)
- Competitor mentions (shopping around)
- Content engagement (reading relevant topics)

## Process
1. Daily scan of tracked companies for signals
2. Score signal strength (1-10)
3. Update lead priority based on signals
4. Trigger outreach for high-intent signals
5. Log all signals for pattern analysis

## Database Tables
- `intent_signals`
- `signal_types`
- `lead_intent_scores`

## Integrations
- News APIs
- Job board APIs
- LinkedIn monitoring
- Funding databases (Crunchbase)

## Priority
Phase 6 - Multi-Channel & Advanced

## Dependencies
- Company Research Agent (provides company context)
- Lead List Builder Agent (provides leads to track)

## Human-in-the-Loop
- High-intent signals may trigger notification for immediate action

## Cron Schedule
- Daily at 5:00 AM - Scan all tracked companies for signals
