# Testimonial Request Agent

## Category
Client Success & Retention

## Purpose
Collect case studies and testimonials

## Triggered By
- Project completed successfully
- High satisfaction score
- 2 weeks post-completion

## Process
1. Assess client relationship
2. Send testimonial request
3. Collect response
4. Format for use
5. Send thank you

## Database Tables
- `testimonial_requests`
- `testimonials`

## Integrations
- Email sending
- Survey tools (for structured collection)
- CRM (for tracking)

## Priority
Phase 5 - Retention & Growth

## Dependencies
- Satisfaction Survey Agent (provides scores)
- Project Management (provides completion status)

## Human-in-the-Loop
- Testimonial request timing may be adjusted
- Testimonials reviewed before publishing

## Qualification Criteria
```
Eligible for testimonial request IF:
- Project status = COMPLETED
- Satisfaction score >= 8
- No outstanding issues/complaints
- Payment complete
- Relationship = POSITIVE
```

## Request Templates

### Standard Request
```
Subject: Would you share a few words about working with us?

Hi {{first_name}},

It's been great working with you on {{project_name}}!

Would you be willing to share a brief testimonial about your experience? It would mean a lot and help others know what to expect.

Just a few sentences about:
- What we helped you with
- The results or impact
- What it was like working together

You can reply directly to this email, or use this quick form: {{form_link}}

No pressure at all - I appreciate you either way!
```

### Video Testimonial Request
```
Subject: Quick favor: 2-minute video testimonial?

Hi {{first_name}},

Would you be open to recording a quick video testimonial about our work together?

Just 2 minutes on your phone sharing:
- What challenge you faced
- How we helped
- The outcome

Here's a simple recording link: {{video_link}}

If you're camera-shy, a written testimonial works great too!
```

### Case Study Request
```
Subject: Feature your success story?

Hi {{first_name}},

{{project_name}} was such a great project. Would you be open to being featured in a case study?

We'd highlight:
- The challenge you faced
- Our approach
- The results (with your approval on specifics)

I'd send you a draft before publishing.

Interested? Just reply and I'll send over some quick questions.
```

## Collection Form Questions
1. What challenge were you facing before working with us?
2. How did we help solve it?
3. What results did you see?
4. What was it like working with us?
5. Would you recommend us? Why?
6. Anything else you'd like to add?

## Thank You Response
```
Subject: Thank you for the kind words! 🙏

Hi {{first_name}},

Thank you so much for the testimonial! I really appreciate you taking the time.

{{if_incentive}}
As a thank you, here's {{incentive}} for your next project.
{{/if_incentive}}

If there's ever anything I can help with, just reach out.

Best,
```

## Usage Rights
```
Standard usage rights requested:
- Website testimonial page
- Social media
- Marketing materials
- Case studies

Always get explicit approval before using:
- Company name
- Full name
- Photo
- Specific metrics/numbers
```

## Tracking
- Request sent date
- Response received (yes/no)
- Testimonial type (written/video/case study)
- Usage locations
