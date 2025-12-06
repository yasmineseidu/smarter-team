# Send Agent (Personalization Reviewer)

## Category
Campaign & Outreach

## Purpose
Review and correct personalization before sending

## Inputs
- Personalization lines with confidence scores
- Source research data
- Lead batch ready to send

## Process
1. Review all personalization lines for batch
2. Verify claims against source data
3. Correct any issues
4. Approve or reject each line
5. Log corrections for learning
6. Release approved leads to campaign

## Database Tables
- `send_agent_reviews`
- `correction_logs`

## Integrations
- Instantly API (releases leads to campaign)

## Priority
Phase 2 - Intelligence Layer

## Dependencies
- Personalization Line Agent (provides lines to review)
- Lead Research Agent (provides source data for verification)

## Human-in-the-Loop
- Send Agent IS the human-in-the-loop checkpoint
- Reviews accuracy, tone, relevance
- All corrections logged for AI learning

## Review Criteria
- Accuracy: Claims match research data
- Tone: Human, not creepy
- Relevance: Actually personalized, not generic
- Source: Citation present and valid
