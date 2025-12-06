# Meeting Reminder Agent

## Category
Meeting Management

## Purpose
Reduce no-shows with reminders

## Reminder Schedule
- 24 hours before: Email + SMS (if phone available)
- 2 hours before: Email
- 15 minutes before: SMS (if phone available)

## Process
1. Query upcoming meetings
2. Send reminders at scheduled times
3. Track reminder delivery
4. Log reminder engagement

## Database Tables
- `meeting_reminders`
- `reminder_logs`

## Integrations
- Email sending (Instantly or direct)
- SMS provider
- Calendar system (Cal.com)

## Priority
Phase 1 - MVP Foundation

## Dependencies
- Meeting Scheduler Agent (provides meeting data)
- SMS Agent (for SMS reminders)

## Human-in-the-Loop
- Reminder templates approved in advance
- No per-reminder approval needed

## Reminder Content

### 24 Hours Before (Email)
```
Subject: Looking forward to our call tomorrow!

Hi {{first_name}},

Just a friendly reminder about our call tomorrow at {{time}} {{timezone}}.

Here's your meeting link: {{meeting_link}}

Looking forward to chatting!
```

### 24 Hours Before (SMS)
```
Reminder: Call with [Your Name] tomorrow at {{time}}. Link: {{meeting_link}}
```

### 2 Hours Before (Email)
```
Subject: See you in 2 hours!

Quick reminder - we're meeting at {{time}} today.
Link: {{meeting_link}}
```

### 15 Minutes Before (SMS)
```
Starting in 15 min! Join here: {{meeting_link}}
```

## Cron Schedule
- Every hour - Check for meetings needing reminders
