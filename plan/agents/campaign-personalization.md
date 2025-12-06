# Personalization Line Agent

## Category
Campaign & Outreach

## Purpose
Create personalized opening lines for each lead

## Inputs
- Lead research
- Company research
- Personalization angles

## Outputs
- Personalization line (1 sentence)
- Confidence score
- Source citation

## Requirements
- Must reference specific, verifiable information
- Sound like you spent 10 minutes researching them
- Relevant but not creepy
- Include citation: "Based on your [LinkedIn post from Nov 15 / recent podcast appearance / etc.]"

## Process
1. Pull lead and company research
2. Identify top 3 personalization angles
3. Generate personalization line with highest-quality angle
4. Include source citation for grounding
5. Score confidence (0-100)
6. Low confidence (<80) → Send Agent review queue
7. Store and map to {{personalization}} variable in Instantly

## Hallucination Prevention
- Only use facts from research data
- Require source citation
- Confidence scoring
- Send Agent review for quality control
- Blacklist vague claims ("your impressive growth", "your recent award" without specifics)

## Database Tables
- `personalization_lines`
- `personalization_sources`
- `personalization_performance`

## Integrations
- Claude API (for generation)
- Instantly API (for variable mapping)

## Priority
Phase 2 - Intelligence Layer

## Dependencies
- Lead Research Agent (provides lead data)
- Company Research Agent (provides company data)

## Human-in-the-Loop
- First 20 lines: 100% human review
- After validation: 10% random sampling
- All low confidence (<80): human review
