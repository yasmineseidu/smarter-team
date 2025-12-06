# Meeting No-Show Handler Agent

## Category
Meeting Management

## Purpose
Handle missed meetings

## Triggered By
Meeting time + 10 minutes, no join

## Process
1. Wait 10 minutes past start time
2. Send "missed you" email
3. Offer reschedule options
4. If no response in 24 hours, send follow-up
5. After 3 no-shows → Move to reactivation pool

## Database Tables
- `no_show_logs`
- `reschedule_attempts`

## Integrations
- Video meeting platform (detect join status)
- Email sending
- Cal.com (for rescheduling)

## Priority
Phase 2 - Intelligence Layer

## Dependencies
- Meeting Scheduler Agent (provides meeting data)
- Cal.com integration (provides available slots)

## Human-in-the-Loop
- No-show email templates approved in advance
- Third no-show may trigger human notification

## No-Show Email Templates

### First No-Show
```
Subject: Missed you on our call

Hi {{first_name}},

I was looking forward to our call at {{time}}, but I didn't see you join.

No worries at all - I know things come up! Would you like to reschedule?

Here are some times that work: {{reschedule_link}}

Talk soon!
```

### Second No-Show
```
Subject: Let's try again

Hi {{first_name}},

We've had a couple of scheduling hiccups. I'd still love to connect when the timing is better for you.

If now isn't the right time, just let me know and we can revisit later.

Otherwise, grab a new time here: {{reschedule_link}}
```

### Third No-Show
```
Subject: Following up

Hi {{first_name}},

I've tried to connect a few times but haven't been able to catch you.

I don't want to keep bothering you, so I'll step back for now. If you'd like to chat in the future, just reply and we can set something up.

Best,
```

## State Transitions
- First no-show: MEETING_NO_SHOW → Reschedule offered
- Reschedule accepted: MEETING_NO_SHOW → MEETING_BOOKED
- Third no-show: MEETING_NO_SHOW → REACTIVATION_POOL
