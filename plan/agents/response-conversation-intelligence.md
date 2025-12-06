# Conversation Intelligence Agent

## Category
Response Handling

## Purpose
Analyze conversations for insights

## Analysis
- Sentiment tracking per message
- Objection patterns
- Winning response patterns
- Buying signals
- Churn risk signals

## Process
1. Analyze all conversations
2. Tag with sentiment, intent, objections
3. Identify patterns
4. Generate weekly insights report
5. Feed patterns back to copywriting agent

## Database Tables
- `conversation_analysis`
- `objection_patterns`
- `winning_patterns`

## Integrations
- Claude API (for analysis)
- Internal conversation database

## Priority
Phase 2 - Intelligence Layer

## Dependencies
- Response Handler Agent (provides conversation data)

## Human-in-the-Loop
- Weekly insights report reviewed for strategic decisions

## Metrics Tracked
- Average sentiment score by campaign
- Common objections frequency
- Response patterns that lead to meetings
- Time to response correlation with outcomes

## Cron Schedule
- Continuous analysis on new messages
- Weekly report generation
