# Meeting Scheduler Agent

## Category
Meeting Management

## Purpose
Book meetings naturally via conversation

## Process
1. Detect meeting intent in conversation
2. Pull available slots from Cal.com
3. Offer 3-5 time options
4. Confirm booking
5. Create calendar event
6. Send confirmation
7. Update lead status to MEETING_BOOKED

## Database Tables
- `meetings`
- `meeting_requests`
- `available_slots`

## Integrations
- Cal.com API

## Priority
Phase 1 - MVP Foundation

## Dependencies
- Response Handler Agent (detects meeting intent)

## Human-in-the-Loop
- None for standard bookings
- Complex scheduling requests escalated

## Webhook
- Receives: `cal.com/booking_created`
- Receives: `cal.com/booking_cancelled`
- Receives: `cal.com/booking_rescheduled`

## Conversation Flow
1. Detect: "Let's schedule a call" / "Can we talk?" / "When are you free?"
2. Respond: "I'd love to chat! Here are some times that work: [options]"
3. Confirm: "Great, you're confirmed for [time]. Looking forward to it!"
4. Send calendar invite automatically
