# Send Time Optimization Agent

## Category
Campaign & Outreach

## Purpose
Optimize email send times for each lead

## Phase 1 (MVP)
- Detect timezone from company location
- Send during business hours (9 AM - 5 PM local)
- Avoid Monday before 10 AM, Friday after 3 PM

## Phase 2
- Track engagement patterns per lead
- Build individual engagement profiles
- Adjust send times based on patterns

## Phase 3
- Cohort analysis by industry/role
- Apply patterns: "CFOs in SaaS respond best 6-8 AM"

## Phase 4
- A/B testing send times per campaign
- Continuous optimization

## Database Tables
- `lead_timezones`
- `engagement_patterns`
- `send_time_optimization`

## Integrations
- Timezone detection APIs
- Instantly API (for scheduling)

## Priority
- Phase 1: MVP Foundation (basic timezone)
- Phase 2-4: Phase 6 - Multi-Channel & Advanced

## Dependencies
- Lead List Builder Agent (provides company location)
- Campaign metrics (provides engagement data)

## Human-in-the-Loop
- None (fully automated optimization)
