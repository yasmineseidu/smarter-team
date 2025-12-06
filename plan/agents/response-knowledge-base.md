# Knowledge Base Agent

## Category
Response Handling

## Purpose
Maintain and query FAQ/knowledge base

## Contents
- Service descriptions
- Pricing information
- Process explanations
- Common objection responses
- Case studies
- Testimonials

## Process
1. Query knowledge base for relevant info
2. Use in response drafting
3. Flag questions not in knowledge base
4. Add new Q&A pairs after human answers
5. Track which knowledge base items are used most

## Database Tables
- `knowledge_base`
- `faq`
- `kb_usage_logs`

## Integrations
- Vector database (Pinecone) for semantic search
- Claude API (for query understanding)

## Priority
Phase 1 - MVP Foundation

## Dependencies
- None (standalone utility agent)

## Human-in-the-Loop
- New knowledge base entries reviewed before adding
- Flagged questions routed to human for initial answer

## Query Flow
1. Receive question from Response Handler
2. Semantic search in vector DB
3. Return top 3 relevant entries
4. If no match (confidence < 70%), flag for human

## Learning
- Track which KB entries lead to positive outcomes
- Update entries based on human corrections
