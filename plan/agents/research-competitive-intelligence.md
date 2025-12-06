# Competitive Intelligence Agent

## Category
Research & Intelligence

## Purpose
Track competitor mentions and positioning from conversations

## Inputs
- Email conversations
- Call transcripts
- Proposal feedback

## Outputs
- Competitor mention log
- Pricing intelligence
- Feature comparisons mentioned
- Win/loss reasons by competitor
- Competitive positioning recommendations

## Process
1. Parse all prospect communications for competitor names
2. Extract context around mentions
3. Categorize: pricing, features, reputation, relationship
4. Update competitive database
5. Generate weekly competitive report

## Database Tables
- `competitors`
- `competitor_mentions`
- `competitive_intelligence`

## Integrations
- Internal conversation database
- Call transcript processor

## Priority
Phase 6 - Multi-Channel & Advanced

## Dependencies
- Response Handler Agent (provides conversation data)
- Call Transcript Processor (provides call data)

## Human-in-the-Loop
- Weekly competitive report reviewed for strategic decisions

## Cron Schedule
- Weekly on Monday 9:00 AM - Generate competitive summary
