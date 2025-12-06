# Call Improvement Agent

## Category
Proposal & Closing

## Purpose
Learn from calls to improve sales skills

## Analysis
- Talk time ratio (aim for <40% you talking)
- Question quality
- Objection handling effectiveness
- Closing attempts
- Next step clarity

## Process
1. Analyze transcript patterns
2. Score call quality
3. Identify improvement areas
4. Generate coaching suggestions
5. Track improvement over time

## Database Tables
- `call_scores`
- `improvement_suggestions`

## Integrations
- Claude API (for analysis)
- Internal transcript database

## Priority
Phase 3 - Closing & Proposals

## Dependencies
- Call Transcript Processor (provides transcripts)

## Human-in-the-Loop
- Coaching suggestions are informational
- Weekly improvement report reviewed

## Scoring Criteria

### Talk Time Ratio (25 points)
- <30%: 25 points
- 30-40%: 20 points
- 40-50%: 15 points
- 50-60%: 10 points
- >60%: 5 points

### Question Quality (25 points)
- Open-ended questions used: +5 each (max 15)
- Discovery questions asked: +5
- Pain-focused questions: +5

### Objection Handling (25 points)
- Acknowledged objection: +5
- Asked clarifying question: +5
- Provided relevant response: +10
- Confirmed resolution: +5

### Next Steps (25 points)
- Clear next step defined: +10
- Specific date/time set: +10
- Both parties agreed: +5

## Output Format
```
CALL SCORE: {{score}}/100

STRENGTHS:
- {{strength_1}}
- {{strength_2}}

IMPROVEMENT AREAS:
- {{area_1}}: {{suggestion_1}}
- {{area_2}}: {{suggestion_2}}

SPECIFIC MOMENTS:
- At {{timestamp}}: {{feedback}}
- At {{timestamp}}: {{feedback}}
```
