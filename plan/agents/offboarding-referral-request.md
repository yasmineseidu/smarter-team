# Referral Request Agent

## Category
Offboarding & Nurture

## Purpose
Ask for referrals from all contacts

## Timing
- Post-project completion
- After positive testimonial
- Closed-lost deals (they may know others)
- Annual touchpoint for past clients

## Process
1. Identify referral candidates
2. Send personalized referral request
3. Track referrals received
4. Thank referrers
5. Process referred leads

## Database Tables
- `referral_requests`
- `referrals`
- `referral_sources`

## Integrations
- Email sending
- CRM (for tracking)
- Lead import (for referred leads)

## Priority
Phase 5 - Retention & Growth

## Dependencies
- Client Offboarding Agent (triggers post-completion)
- Testimonial Request Agent (triggers after testimonial)
- Satisfaction Survey Agent (provides relationship quality)

## Human-in-the-Loop
- Referral requests sent automatically
- Referred leads processed normally
- High-value referrals trigger personal thank you

## Referral Request Criteria
```
Eligible for referral request IF:
- Satisfaction score >= 8 OR
- Testimonial provided OR
- Project completed successfully OR
- Long-term positive relationship

NOT eligible IF:
- Outstanding issues
- Payment problems
- Negative feedback
- Recent referral request (<6 months)
```

## Referral Request Templates

### Post-Project Completion
```
Subject: Know anyone who could use our help?

Hi {{first_name}},

Now that we've wrapped up {{project_name}}, I wanted to ask:

Do you know anyone else who could benefit from {{our_service}}?

A warm intro goes a long way, and I'd take great care of anyone you send my way.

No pressure at all - just thought I'd ask!

{{if_incentive}}
PS: As a thank you, I'll {{incentive}} for any referral that becomes a client.
{{/if_incentive}}
```

### After Testimonial
```
Subject: Quick follow-up + a favor

Hi {{first_name}},

Thank you again for the kind testimonial! It really means a lot.

Since you've had a great experience, I wanted to ask:

Is there anyone in your network who might benefit from similar help?

I'd be happy to have an intro conversation with anyone you think might be a fit.

Thanks again!
```

### Annual Touchpoint (Past Clients)
```
Subject: Happy {{occasion}}! + a quick ask

Hi {{first_name}},

Hope you're doing well! It's been {{time_since_project}} since we worked together on {{project_name}}.

I'm looking to work with more companies like {{company}}.

If you know anyone who could use help with {{service}}, I'd really appreciate an intro.

Hope all is well!
```

### To Closed-Lost Deals
```
Subject: A favor, even though we didn't work together

Hi {{first_name}},

I know we didn't end up working together, but I hope we left things on good terms.

If you happen to know anyone looking for help with {{service}}, I'd really appreciate the introduction.

And if your situation ever changes, I'd love to chat again.

Best,
```

## Referral Tracking

### When Referral Received
```
1. Create new lead with source = "referral"
2. Link to referrer contact
3. Send thank you to referrer
4. Add referral bonus note (if applicable)
5. Prioritize referral in pipeline
```

### Thank You Email
```
Subject: Thank you for the referral!

Hi {{first_name}},

Thank you so much for introducing me to {{referred_name}} at {{referred_company}}!

I've reached out and will take great care of them.

{{if_incentive}}
I'll send over your {{incentive}} once we kick things off.
{{/if_incentive}}

I really appreciate the trust!
```

## Referral Incentives (Optional)
```
Options:
- Discount on future work
- Gift card
- Donation to charity of choice
- Free consultation/audit
- Cash bonus

Track:
- Cost per referral
- Referral conversion rate
- Revenue from referrals
- ROI of incentive program
```

## Referral Metrics
- Referral requests sent
- Referrals received
- Referral conversion rate
- Revenue from referrals
- Top referral sources
- Referral program ROI
