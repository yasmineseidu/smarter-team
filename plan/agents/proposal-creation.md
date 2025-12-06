# Proposal Creation Agent

## Category
Proposal & Closing

## Purpose
Generate proposals after calls

## Triggered By
- Deformity form submission OR
- Status change in Airtable OR
- 15-30 minutes after call (auto)

## Inputs
- Call transcript insights
- Service selected
- Pricing tier
- Timeline discussed
- Custom requirements

## Outputs
- PandaDoc proposal
- Pricing breakdown
- Timeline/milestones
- Terms and conditions

## Process
1. Pull call insights and requirements
2. Select appropriate template
3. Customize with client details
4. Calculate pricing
5. Generate proposal draft
6. Human review queue
7. Send via PandaDoc after approval

## Database Tables
- `proposals`
- `proposal_templates`
- `proposal_versions`

## Integrations
- PandaDoc API
- Deformity webhooks
- Airtable webhooks
- Claude API (for customization)

## Priority
Phase 3 - Closing & Proposals

## Dependencies
- Call Transcript Processor (provides call insights)
- Deformity integration (provides form data)

## Human-in-the-Loop
- All proposals require human review before sending (Gate 4)
- Review: pricing accuracy, scope completeness, timeline realism, terms

## Webhook
- Receives: `deformity/form_submitted` (client intake)

## Proposal Template Variables
```
{{client_name}}
{{company_name}}
{{project_name}}
{{service_description}}
{{deliverables}}
{{timeline}}
{{milestones}}
{{pricing_breakdown}}
{{total_amount}}
{{payment_terms}}
{{terms_and_conditions}}
{{valid_until}}
```

## Pricing Rules
- Standard pricing from template
- Custom work calculated hourly
- Volume discounts applied automatically
- Human approval required for discounts >15%
