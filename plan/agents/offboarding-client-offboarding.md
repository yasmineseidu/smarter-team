# Client Offboarding Agent

## Category
Offboarding & Nurture

## Purpose
Handle project completion and client exit

## Checklist
- All deliverables handed off
- Final invoice sent and paid
- Access credentials returned/revoked
- Files organized and shared
- Knowledge transfer complete
- Final feedback collected
- Testimonial requested

## Process
1. Run offboarding checklist
2. Send final deliverables
3. Collect final payment
4. Revoke access
5. Archive project
6. Move to long-term nurture

## Database Tables
- `offboarding_progress`
- `offboarding_checklist`

## Integrations
- Google Drive (file handoff)
- Stripe (final payment)
- Access management systems
- Email sending

## Priority
Phase 5 - Retention & Growth

## Dependencies
- Project Management (provides completion status)
- Invoice Generation (provides final invoice)
- Testimonial Request Agent (requests testimonial)

## Human-in-the-Loop
- Final deliverables reviewed before handoff
- Custom offboarding requirements handled manually

## Offboarding Checklist

### Deliverables
- [ ] All project deliverables complete
- [ ] Final versions uploaded to Drive
- [ ] Client has access to all files
- [ ] Handoff email sent with links

### Financial
- [ ] Final invoice generated
- [ ] Invoice sent to client
- [ ] Payment received
- [ ] Books closed on project

### Access
- [ ] Client credentials returned (if applicable)
- [ ] Our access to client systems revoked
- [ ] Shared tool access removed
- [ ] API keys rotated

### Documentation
- [ ] Project wrap-up notes created
- [ ] Lessons learned documented
- [ ] Client preferences noted for future

### Relationship
- [ ] Final satisfaction survey sent
- [ ] Testimonial requested (if eligible)
- [ ] Thank you sent
- [ ] Added to long-term nurture list

## Offboarding Email Sequence

### 1. Final Deliverable Handoff
```
Subject: 🎉 Project complete: {{project_name}}

Hi {{first_name}},

Congratulations - {{project_name}} is complete!

FINAL DELIVERABLES
{{deliverable_links}}

WHAT'S INCLUDED
{{deliverable_summary}}

DOCUMENTATION
{{documentation_links}}

Please review and let me know if you have any questions.
```

### 2. Final Invoice
```
Subject: Final invoice for {{project_name}}

Hi {{first_name}},

Attached is the final invoice for {{project_name}}.

Amount: ${{amount}}
Due: {{due_date}}
Pay here: {{payment_link}}

Thank you for your business!
```

### 3. Project Wrap-Up
```
Subject: Thank you for working with us!

Hi {{first_name}},

It's been a pleasure working with you on {{project_name}}!

A few things:
1. All files are in your Drive folder
2. Please complete our brief feedback survey: {{survey_link}}
3. We'd love a testimonial if you're willing: {{testimonial_link}}

Stay in touch - I'll reach out occasionally with helpful content.

If you ever need anything, just reply to this email.

Best,
```

## State Transitions
- Project completed: ACTIVE_PROJECT → PROJECT_COMPLETED
- Offboarding complete: PROJECT_COMPLETED → LONG_TERM_NURTURE
- Testimonial given: Add tag "testimonial_provided"

## Archive Process
```
1. Export project data to archive
2. Update project status to ARCHIVED
3. Close ClickUp project
4. Move Drive folder to Archive
5. Update Airtable record
6. Clear sensitive client data per retention policy
```
