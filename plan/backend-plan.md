# Yumba.ai - Ultimate Sales & Client Delivery System

## Table of Contents

1. [System Overview](#system-overview)
2. [Lead State Machine](#lead-state-machine)
3. [Complete Feature List](#complete-feature-list)
4. [Agent Definitions & Handoffs](#agent-definitions--handoffs)
5. [Database Schema](#database-schema)
6. [Cron Jobs & Scheduled Tasks](#cron-jobs--scheduled-tasks)
7. [Webhook Integrations](#webhook-integrations)
8. [Human-in-the-Loop Checkpoints](#human-in-the-loop-checkpoints)
9. [Feedback Loops](#feedback-loops)
10. [Implementation Phases](#implementation-phases)

---

## System Overview

Yumba.ai is an AI-first sales automation platform that handles the entire sales lifecycle from niche research through client delivery and retention. The system uses Pydantic AI agents with pydantic-graph orchestration, FastAPI backend, and Next.js frontend.

### Core Philosophy

- **Human-in-the-loop** for critical decisions (proposals, campaign launches, complex responses)
- **Continuous learning** from human corrections
- **Multi-channel outreach** (email primary, LinkedIn secondary, SMS for hot leads)
- **Quality over quantity** in personalization and outreach

### Tech Stack Reference

| Category | Tool | Purpose |
|----------|------|---------|
| CRM | GoHighLevel | Leads and clients |
| CRM Visual | Airtable | Visual pipeline management |
| Database | Postgres (Supabase) | Large lead storage, all system data |
| Automation | n8n | Workflow automation |
| Cold Email | Instantly.ai | Email campaigns and sending |
| LinkedIn | Heyreach | LinkedIn automation |
| Email Verification | Reoon | Primary verification |
| Email Enrichment | Tomba, Muraena, Findymail, Icypeas, Voila Norbert, Anymail Finder | Waterfall enrichment |
| Meeting Notes | Fathom | AI notetaker |
| Documents | PandaDoc | Proposals and contracts |
| Forms | Deformity.ai | Client intake forms |
| Tasks | Todoist | Task management |
| Projects | ClickUp | Project management |
| Payments | Stripe | Payment processing |
| Bookkeeping | QuickBooks | Financial tracking |

---

## Lead State Machine

### Visual Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LEAD LIFECYCLE                                  │
└─────────────────────────────────────────────────────────────────────────────┘

[NEW] → [ENRICHING] → [VERIFIED] → [IN_CAMPAIGN] → [ENGAGED] → [MEETING_BOOKED]
                           │              │             │
                           ▼              ▼             ▼
                    [INVALID_EMAIL]  [BOUNCED]    [UNSUBSCRIBED]
                           │              │             │
                           └──────────────┴─────────────┘
                                          │
                                          ▼
                                   [DEAD_LEAD]

[MEETING_BOOKED] → [MEETING_COMPLETED] → [PROPOSAL_SENT] → [NEGOTIATING]
                           │                    │               │
                           ▼                    ▼               │
                    [MEETING_NO_SHOW]    [PROPOSAL_EXPIRED]     │
                           │                    │               │
                           ▼                    ▼               ▼
                    [REACTIVATION_POOL] ←──────┴───────────────┘
                                                               │
                    ┌──────────────────────────────────────────┤
                    │                                          │
                    ▼                                          ▼
             [CLOSED_LOST]                              [CLOSED_WON]
                    │                                          │
                    ▼                                          ▼
             [NURTURE_POOL]                            [ONBOARDING]
                    │                                          │
                    │                                          ▼
                    │                                   [ACTIVE_PROJECT]
                    │                                          │
                    │                                          ▼
                    │                                   [PROJECT_COMPLETED]
                    │                                          │
                    │                     ┌────────────────────┼────────────────────┐
                    │                     ▼                    ▼                    ▼
                    │              [MAINTENANCE]        [UPSELL_OPPORTUNITY]  [TESTIMONIAL_REQUEST]
                    │                     │                    │                    │
                    │                     └────────────────────┴────────────────────┘
                    │                                          │
                    └──────────────────────────────────────────┴──────► [LONG_TERM_NURTURE]
```

### State Definitions

| State | Description | Entry Trigger | Exit Trigger | Max Time in State |
|-------|-------------|---------------|--------------|-------------------|
| `NEW` | Lead just added to system | Apify scrape, manual add, inbound | Enrichment starts | 1 hour |
| `ENRICHING` | Email finding and data gathering | Automatic after NEW | Enrichment complete | 24 hours |
| `VERIFIED` | Has valid email, ready for campaign | Email verified | Added to campaign | 48 hours |
| `IN_CAMPAIGN` | Active in email sequence | Campaign assignment | Reply received OR sequence complete | 30 days |
| `ENGAGED` | Replied to email (any response) | Reply webhook from Instantly | Meeting booked OR marked lost | 7 days |
| `MEETING_BOOKED` | Call scheduled | Calendar event created | Meeting occurs | Until meeting time |
| `MEETING_COMPLETED` | Call happened | Fathom webhook | Proposal sent OR marked lost | 48 hours |
| `PROPOSAL_SENT` | Proposal delivered | PandaDoc sent | Signed OR expired | 14 days |
| `NEGOTIATING` | Back and forth on terms | Client requests changes | Agreement reached | 14 days |
| `CLOSED_WON` | Deal signed | Contract executed | Onboarding starts | 24 hours |
| `CLOSED_LOST` | Deal lost | Rejection or timeout | Move to nurture | Immediate |
| `ONBOARDING` | New client setup | Contract signed | Kickoff complete | 7 days |
| `ACTIVE_PROJECT` | Work in progress | Kickoff complete | Project delivered | Per project |
| `PROJECT_COMPLETED` | Deliverables handed off | Final delivery | Feedback received | 14 days |
| `MAINTENANCE` | Ongoing retainer | Client opts in | Contract ends | Per agreement |
| `NURTURE_POOL` | Lost deals for future | Marked closed lost | Trigger event | Indefinite |
| `REACTIVATION_POOL` | No response after 14 check-ins | Max check-ins reached | Trigger event | Indefinite |
| `LONG_TERM_NURTURE` | All past contacts | Project complete OR nurture | Re-engagement | Indefinite |

### State Transition Rules

```python
# Example state transition logic

ALLOWED_TRANSITIONS = {
    "NEW": ["ENRICHING", "DEAD_LEAD"],
    "ENRICHING": ["VERIFIED", "INVALID_EMAIL", "DEAD_LEAD"],
    "VERIFIED": ["IN_CAMPAIGN", "DEAD_LEAD"],
    "IN_CAMPAIGN": ["ENGAGED", "BOUNCED", "UNSUBSCRIBED", "REACTIVATION_POOL"],
    "ENGAGED": ["MEETING_BOOKED", "CLOSED_LOST", "REACTIVATION_POOL"],
    "MEETING_BOOKED": ["MEETING_COMPLETED", "MEETING_NO_SHOW"],
    "MEETING_NO_SHOW": ["MEETING_BOOKED", "REACTIVATION_POOL"],
    "MEETING_COMPLETED": ["PROPOSAL_SENT", "CLOSED_LOST"],
    "PROPOSAL_SENT": ["NEGOTIATING", "CLOSED_WON", "CLOSED_LOST", "PROPOSAL_EXPIRED"],
    "NEGOTIATING": ["CLOSED_WON", "CLOSED_LOST"],
    "PROPOSAL_EXPIRED": ["REACTIVATION_POOL", "CLOSED_LOST"],
    "CLOSED_WON": ["ONBOARDING"],
    "CLOSED_LOST": ["NURTURE_POOL"],
    "ONBOARDING": ["ACTIVE_PROJECT", "ONBOARDING_STUCK"],
    "ONBOARDING_STUCK": ["ONBOARDING", "CLOSED_LOST"],
    "ACTIVE_PROJECT": ["PROJECT_COMPLETED", "PROJECT_PAUSED", "PROJECT_CANCELLED"],
    "PROJECT_COMPLETED": ["MAINTENANCE", "UPSELL_OPPORTUNITY", "LONG_TERM_NURTURE"],
    "MAINTENANCE": ["LONG_TERM_NURTURE", "UPSELL_OPPORTUNITY"],
    "NURTURE_POOL": ["IN_CAMPAIGN"],  # Re-engagement
    "REACTIVATION_POOL": ["IN_CAMPAIGN"],  # Re-engagement
    "LONG_TERM_NURTURE": ["IN_CAMPAIGN", "ENGAGED"],  # Re-engagement
}
```

---

## Complete Feature List

### 1. RESEARCH & INTELLIGENCE

#### 1.1 Niche Research Agent

**Purpose:** Identify profitable niches to prospect

**Inputs:**
- Industry keywords
- Revenue/employee size criteria
- Geographic focus
- Service offering match criteria

**Outputs:**
- Scored niche recommendations
- Market size estimates
- Competition analysis
- Pain point summaries
- Recommended personas per niche

**Process:**
1. Search Reddit, LinkedIn, forums for pain points in target industry
2. Analyze job postings for common problems
3. Research competitor offerings and gaps
4. Score niche on: market size, pain intensity, ability to pay, competition level
5. Generate niche report with recommendations

**Database Tables:** `niches`, `niche_scores`, `niche_research_sources`

---

#### 1.2 Persona Research Agent

**Purpose:** Deep understanding of target personas for messaging

**Inputs:**
- Job title/role
- Industry
- Company size range

**Outputs:**
- Day-in-the-life summary
- Common frustrations
- Goals and KPIs they're measured on
- Language they use (jargon, phrases)
- Where they hang out online
- What they read/follow
- Buying triggers
- Objection patterns

**Process:**
1. Scrape LinkedIn profiles matching persona
2. Analyze Reddit/forum discussions from this persona
3. Review industry publications they'd read
4. Compile behavioral patterns
5. Generate persona document

**Database Tables:** `personas`, `persona_research`, `persona_language_patterns`

---

#### 1.3 Lead Research Agent

**Purpose:** Research individual leads for personalization

**Inputs:**
- Lead name
- Company
- LinkedIn URL
- Email

**Outputs:**
- Recent LinkedIn posts/activity
- News mentions
- Podcast appearances
- Speaking engagements
- Awards/recognition
- Career history highlights
- Mutual connections
- Shared interests
- Recent achievements

**Process:**
1. Scrape LinkedIn profile (via Apify)
2. Search news for name + company
3. Search podcasts/YouTube for appearances
4. Check company press releases
5. Compile research summary
6. Flag best personalization angles

**Database Tables:** `lead_research`, `lead_research_sources`, `personalization_angles`

---

#### 1.4 Company Research Agent

**Purpose:** Research companies for context and triggers

**Inputs:**
- Company name
- Website
- LinkedIn company page

**Outputs:**
- Recent news (funding, acquisitions, leadership changes)
- Job postings (growth signals, pain signals)
- Tech stack (via BuiltWith/Wappalyzer)
- Company size and growth rate
- Recent LinkedIn posts
- Press releases
- Competitive positioning
- Trigger events

**Process:**
1. Scrape company LinkedIn page
2. Search news for company name
3. Check job boards for their postings
4. Analyze tech stack
5. Review recent press/blog posts
6. Identify trigger events
7. Generate company brief

**Database Tables:** `company_research`, `company_news`, `company_jobs`, `company_tech_stack`, `trigger_events`

---

#### 1.5 Intent Signal Tracking Agent

**Purpose:** Detect buying signals from prospect behavior

**Signals to Track:**
- New job postings (hiring for roles you solve)
- Leadership changes (new decision makers)
- Funding announcements (budget available)
- Expansion news (new locations, markets)
- Technology changes (new tools, migrations)
- Competitor mentions (shopping around)
- Content engagement (reading relevant topics)

**Process:**
1. Daily scan of tracked companies for signals
2. Score signal strength (1-10)
3. Update lead priority based on signals
4. Trigger outreach for high-intent signals
5. Log all signals for pattern analysis

**Database Tables:** `intent_signals`, `signal_types`, `lead_intent_scores`

---

#### 1.6 Competitive Intelligence Agent

**Purpose:** Track competitor mentions and positioning from conversations

**Inputs:**
- Email conversations
- Call transcripts
- Proposal feedback

**Outputs:**
- Competitor mention log
- Pricing intelligence
- Feature comparisons mentioned
- Win/loss reasons by competitor
- Competitive positioning recommendations

**Process:**
1. Parse all prospect communications for competitor names
2. Extract context around mentions
3. Categorize: pricing, features, reputation, relationship
4. Update competitive database
5. Generate weekly competitive report

**Database Tables:** `competitors`, `competitor_mentions`, `competitive_intelligence`

---

### 2. LEAD GENERATION & DATA

#### 2.1 Lead List Building Agent

**Purpose:** Scrape and import leads from Apify

**Inputs:**
- Search criteria (title, industry, location, company size)
- Source (LinkedIn, Apollo, etc.)
- Volume needed

**Outputs:**
- Raw lead records
- Deduplication report
- Data quality report

**Process:**
1. Trigger Apify scrape with criteria
2. Receive webhook with results
3. Normalize data format
4. Check for duplicates against existing database
5. Flag incomplete records
6. Import valid leads as NEW status
7. Generate import report

**Database Tables:** `leads`, `lead_sources`, `import_logs`

---

#### 2.2 Email Verification Agent

**Purpose:** Verify email addresses with Reoon

**Inputs:**
- List of emails to verify

**Outputs:**
- Verification results (valid, invalid, risky, unknown)
- Updated lead records

**Process:**
1. Batch emails to Reoon API
2. Process results
3. Mark valid emails as VERIFIED
4. Mark invalid as INVALID_EMAIL
5. Queue risky/unknown for waterfall enrichment

**Database Tables:** `email_verifications`, `verification_results`

---

#### 2.3 Waterfall Email Enrichment Agent

**Purpose:** Find valid emails for leads without them

**Inputs:**
- Leads with invalid/missing emails
- Lead name, company, domain

**Outputs:**
- Found emails with confidence scores
- Enrichment source tracking

**Process (Waterfall Order):**
1. Try Muraena → if found, verify with Reoon
2. Try Tomba → if found, verify with Reoon
3. Try Nimbler → if found, verify with Reoon
4. Try Voila Norbert → if found, verify with Reoon
5. Try Icypeas → if found, verify with Reoon
6. Try Anymail Finder → if found, verify with Reoon
7. Try Findymail → if found, verify with Reoon
8. If all fail, mark as UNENRICHABLE

**Database Tables:** `enrichment_attempts`, `enrichment_results`, `enrichment_costs`

---

#### 2.4 Data Validation Agent

**Purpose:** Ensure data quality before campaigns

**Validation Rules:**

| Field | Rule | Action if Failed |
|-------|------|------------------|
| first_name | Not empty, not "N/A", not "Unknown" | Block from campaign |
| company_name | Not empty | Block from campaign |
| email | Valid format, verified status | Block from campaign |
| domain | Matches company | Flag for review |
| linkedin_url | Valid LinkedIn URL format | Optional, continue |
| job_title | Not empty | Optional, continue |

**Process:**
1. Run validation rules on leads before campaign assignment
2. Generate validation report
3. Block invalid leads from campaigns
4. Queue incomplete leads for enrichment
5. Log all validation failures

**Database Tables:** `validation_logs`, `validation_rules`

---

#### 2.5 Duplicate Detection Agent

**Purpose:** Prevent duplicate leads across databases

**Matching Criteria (Fuzzy):**
- Exact email match
- Name + company match (fuzzy)
- LinkedIn URL match
- Phone number match

**Process:**
1. Check new leads against existing database
2. Score match confidence
3. Auto-merge exact matches
4. Flag fuzzy matches for human review
5. Log all duplicate decisions

**Database Tables:** `duplicate_checks`, `merge_logs`

---

#### 2.6 Progressive Enrichment Agent

**Purpose:** Fill data gaps over time

**Fields to Enrich:**
- Phone number
- LinkedIn URL
- Company size
- Industry
- Revenue range
- Tech stack
- Recent news

**Process:**
1. Identify leads with missing fields
2. Prioritize by engagement level (enriched engaged leads first)
3. Attempt enrichment via APIs
4. Update records
5. Track enrichment costs per lead

**Database Tables:** `enrichment_queue`, `enrichment_history`

---

#### 2.7 Technographic Data Agent

**Purpose:** Identify prospect tech stack

**Data Points:**
- CRM used
- Marketing automation
- Website platform
- Analytics tools
- Payment processors
- Communication tools

**Sources:**
- BuiltWith API
- Wappalyzer
- Job posting analysis
- Website scraping

**Process:**
1. Query tech detection APIs
2. Parse job postings for tool mentions
3. Update company tech stack record
4. Flag relevant tech signals (e.g., using competitor tools)

**Database Tables:** `company_tech_stack`, `tech_signals`

---

### 3. CAMPAIGN & OUTREACH

#### 3.1 Campaign Creation Agent

**Purpose:** Set up campaigns in Instantly

**Inputs:**
- Campaign name
- Target niche/persona
- Email sequence
- Sending schedule
- Daily send limits

**Outputs:**
- Campaign ID
- Configuration confirmation

**Process:**
1. Create campaign in Instantly via API
2. Configure sending settings
3. Set up warmup parameters
4. Link tracking domain
5. Store campaign ID and config in database

**Database Tables:** `campaigns`, `campaign_configs`

---

#### 3.2 Cold Email Copywriting Agent

**Purpose:** Write email sequences for campaigns

**Inputs:**
- Niche/persona research
- Pain points
- Offer/service
- Tone guidelines
- Character limits (max 125 chars per email)

**Outputs:**
- Email sequence (3-5 emails)
- Subject lines
- A/B variants

**Constraints:**
- Must sound ultra human
- Non-salesy, not pushy
- Max 125 characters per email
- No corporate jargon
- Conversational tone

**Process:**
1. Pull persona and niche research
2. Generate email drafts
3. Create 2-3 variants per email for A/B testing
4. Human review queue
5. Store approved copy in database
6. Push to Instantly campaign

**Database Tables:** `email_copy`, `email_variants`, `copy_performance`

---

#### 3.3 Personalization Line Agent

**Purpose:** Create personalized opening lines for each lead

**Inputs:**
- Lead research
- Company research
- Personalization angles

**Outputs:**
- Personalization line (1 sentence)
- Confidence score
- Source citation

**Requirements:**
- Must reference specific, verifiable information
- Sound like you spent 10 minutes researching them
- Relevant but not creepy
- Include citation: "Based on your [LinkedIn post from Nov 15 / recent podcast appearance / etc.]"

**Process:**
1. Pull lead and company research
2. Identify top 3 personalization angles
3. Generate personalization line with highest-quality angle
4. Include source citation for grounding
5. Score confidence (0-100)
6. Low confidence (<80) → Send Agent review queue
7. Store and map to {{personalization}} variable in Instantly

**Hallucination Prevention:**
- Only use facts from research data
- Require source citation
- Confidence scoring
- Send Agent review for quality control
- Blacklist vague claims ("your impressive growth", "your recent award" without specifics)

**Database Tables:** `personalization_lines`, `personalization_sources`, `personalization_performance`

---

#### 3.4 Send Agent (Personalization Reviewer)

**Purpose:** Review and correct personalization before sending

**Inputs:**
- Personalization lines with confidence scores
- Source research data
- Lead batch ready to send

**Process:**
1. Review all personalization lines for batch
2. Verify claims against source data
3. Correct any issues
4. Approve or reject each line
5. Log corrections for learning
6. Release approved leads to campaign

**Database Tables:** `send_agent_reviews`, `correction_logs`

---

#### 3.5 Send Time Optimization Agent

**Purpose:** Optimize email send times for each lead

**Phase 1 (MVP):**
- Detect timezone from company location
- Send during business hours (9 AM - 5 PM local)
- Avoid Monday before 10 AM, Friday after 3 PM

**Phase 2:**
- Track engagement patterns per lead
- Build individual engagement profiles
- Adjust send times based on patterns

**Phase 3:**
- Cohort analysis by industry/role
- Apply patterns: "CFOs in SaaS respond best 6-8 AM"

**Phase 4:**
- A/B testing send times per campaign
- Continuous optimization

**Database Tables:** `lead_timezones`, `engagement_patterns`, `send_time_optimization`

---

#### 3.6 A/B Testing Framework

**Purpose:** Test and optimize email performance

**Test Variables:**
- Subject lines
- Email body copy
- Personalization approaches
- Send times
- Sequence length

**Process:**
1. Create variant sets
2. Randomly assign leads to variants
3. Track performance per variant
4. Statistical significance testing
5. Auto-promote winners after threshold
6. Log all test results

**Database Tables:** `ab_tests`, `ab_variants`, `ab_results`

---

#### 3.7 Email Deliverability Monitor

**Purpose:** Track and maintain sender reputation

**Metrics:**
- Bounce rate (target: <2%)
- Spam complaint rate (target: <0.1%)
- Open rate (benchmark tracking)
- Domain health score

**Process:**
1. Monitor bounce webhooks from Instantly
2. Track spam complaints
3. Alert if thresholds exceeded
4. Auto-pause campaigns at risk
5. Generate weekly deliverability report

**Database Tables:** `deliverability_metrics`, `domain_health`, `deliverability_alerts`

---

#### 3.8 Email Warmup Monitor

**Purpose:** Track warmup progress for sending domains

**Process:**
1. Track warmup emails sent/received
2. Monitor warmup engagement rates
3. Alert on warmup issues
4. Track domain reputation progression
5. Recommend when domain is ready for volume

**Database Tables:** `domain_warmup`, `warmup_metrics`

---

#### 3.9 LinkedIn Automation Agent

**Purpose:** Multi-channel outreach via Heyreach

**Triggers:**
- Hot lead (high intent score)
- No email response after sequence
- High-value target accounts

**Actions:**
- Connection request with note
- Follow-up message after connection
- Profile view (awareness)

**Process:**
1. Identify leads for LinkedIn outreach
2. Check if already connected
3. Send connection request via Heyreach
4. Track connection acceptance
5. Send follow-up message
6. Sync activity back to lead record

**Database Tables:** `linkedin_outreach`, `linkedin_connections`, `linkedin_messages`

---

#### 3.10 SMS Agent

**Purpose:** Text message follow-ups for hot leads

**Triggers:**
- Phone number available
- High intent score (70+)
- Meeting no-show
- Proposal expiring

**Process:**
1. Verify phone number validity
2. Check SMS consent
3. Send SMS via API
4. Track delivery and response
5. Log in conversation history

**Database Tables:** `sms_messages`, `sms_consent`

---

#### 3.11 Voice Message Agent

**Purpose:** Voicemail drops for solopreneur outreach

**Triggers:**
- Hot lead not responding to email
- Post-meeting follow-up
- Proposal follow-up

**Process:**
1. Generate call task for you
2. Provide talking points
3. Log call attempt
4. Track outcome
5. Update lead status

**Database Tables:** `call_tasks`, `call_logs`

---

### 4. RESPONSE HANDLING

#### 4.1 Email Response Handler Agent

**Purpose:** Process and respond to email replies

**Triggered By:** Webhook from Instantly on reply

**Response Tiers:**

| Tier | Type | Action |
|------|------|--------|
| Auto-Send | Meeting confirmations, thank you, simple calendar links | Send immediately |
| Approval | Questions, objections, pricing discussions | Draft → Slack/Telegram → Wait for approval |
| Escalation | Complaints, complex technical, custom requests | Immediate notification + human handle |

**Process:**
1. Receive reply webhook
2. Classify response type (positive, negative, question, objection, out-of-office)
3. Check knowledge base and FAQ for relevant info
4. Draft response based on tier
5. For Approval tier: Send to Slack/Telegram
6. Wait for human approval/edit
7. Send approved response
8. Log everything in conversation history

**Special Handling:**
- Out-of-office: Parse return date, schedule follow-up
- Unsubscribe: Remove from campaigns, update status
- Referral: Create new lead from referral
- "Not the right person": Request correct contact

**Database Tables:** `email_responses`, `response_drafts`, `response_approvals`, `conversation_history`

---

#### 4.2 Knowledge Base Agent

**Purpose:** Maintain and query FAQ/knowledge base

**Contents:**
- Service descriptions
- Pricing information
- Process explanations
- Common objection responses
- Case studies
- Testimonials

**Process:**
1. Query knowledge base for relevant info
2. Use in response drafting
3. Flag questions not in knowledge base
4. Add new Q&A pairs after human answers
5. Track which knowledge base items are used most

**Database Tables:** `knowledge_base`, `faq`, `kb_usage_logs`

---

#### 4.3 Conversation Intelligence Agent

**Purpose:** Analyze conversations for insights

**Analysis:**
- Sentiment tracking per message
- Objection patterns
- Winning response patterns
- Buying signals
- Churn risk signals

**Process:**
1. Analyze all conversations
2. Tag with sentiment, intent, objections
3. Identify patterns
4. Generate weekly insights report
5. Feed patterns back to copywriting agent

**Database Tables:** `conversation_analysis`, `objection_patterns`, `winning_patterns`

---

#### 4.4 Check-In Agent

**Purpose:** Follow up with silent prospects

**Triggers:**
- No response in 2 days from last conversation
- Engaged but went silent

**Process:**
1. Check conversation history
2. Identify last interaction
3. Draft check-in email
4. Send if auto-approved
5. Track check-in count
6. After 14 check-ins → Move to reactivation pool

**Database Tables:** `check_in_logs`, `check_in_templates`

---

### 5. MEETING MANAGEMENT

#### 5.1 Meeting Scheduler Agent

**Purpose:** Book meetings naturally via conversation

**Process:**
1. Detect meeting intent in conversation
2. Pull available slots from Cal.com
3. Offer 3-5 time options
4. Confirm booking
5. Create calendar event
6. Send confirmation
7. Update lead status to MEETING_BOOKED

**Database Tables:** `meeting_requests`, `available_slots`

---

#### 5.2 Meeting Reminder Agent

**Purpose:** Reduce no-shows with reminders

**Reminder Schedule:**
- 24 hours before: Email + SMS (if phone available)
- 2 hours before: Email
- 15 minutes before: SMS (if phone available)

**Process:**
1. Query upcoming meetings
2. Send reminders at scheduled times
3. Track reminder delivery
4. Log reminder engagement

**Database Tables:** `meeting_reminders`, `reminder_logs`

---

#### 5.3 Meeting Prep Agent

**Purpose:** Prepare materials before calls

**Triggered By:** 1 hour before scheduled meeting

**Outputs:**
- Lead research summary
- Company research summary
- Conversation history summary
- Recommended talking points
- Questions to ask
- Potential objections to prepare for
- Gamma presentation slides

**Process:**
1. Pull all research for lead and company
2. Summarize conversation history
3. Generate talking points based on their pain points
4. Create Gamma slides
5. Deliver prep package via email/Slack
6. Log prep delivery

**Database Tables:** `meeting_prep`, `talking_points`

---

#### 5.4 Meeting No-Show Handler

**Purpose:** Handle missed meetings

**Triggered By:** Meeting time + 10 minutes, no join

**Process:**
1. Wait 10 minutes past start time
2. Send "missed you" email
3. Offer reschedule options
4. If no response in 24 hours, send follow-up
5. After 3 no-shows → Move to reactivation pool

**Database Tables:** `no_show_logs`, `reschedule_attempts`

---

### 6. PROPOSAL & CLOSING

#### 6.1 Call Transcript Processor Agent

**Purpose:** Extract insights from meeting recordings

**Triggered By:** Fathom webhook after call

**Outputs:**
- Call summary
- Key points discussed
- Pain points identified
- Budget/timeline mentioned
- Decision makers identified
- Objections raised
- Next steps agreed
- Action items (auto-created in Todoist/ClickUp)

**Process:**
1. Receive transcript from Fathom
2. Parse and analyze with AI
3. Extract structured data
4. Create action items in task management
5. Update lead record with insights
6. Generate call summary
7. Feed insights to proposal creation

**Database Tables:** `call_transcripts`, `call_insights`, `call_action_items`

---

#### 6.2 Call Improvement Agent

**Purpose:** Learn from calls to improve sales skills

**Analysis:**
- Talk time ratio (aim for <40% you talking)
- Question quality
- Objection handling effectiveness
- Closing attempts
- Next step clarity

**Process:**
1. Analyze transcript patterns
2. Score call quality
3. Identify improvement areas
4. Generate coaching suggestions
5. Track improvement over time

**Database Tables:** `call_scores`, `improvement_suggestions`

---

#### 6.3 Proposal Creation Agent

**Purpose:** Generate proposals after calls

**Triggered By:**
- Deformity form submission OR
- Status change in Airtable OR
- 15-30 minutes after call (auto)

**Inputs:**
- Call transcript insights
- Service selected
- Pricing tier
- Timeline discussed
- Custom requirements

**Outputs:**
- PandaDoc proposal
- Pricing breakdown
- Timeline/milestones
- Terms and conditions

**Process:**
1. Pull call insights and requirements
2. Select appropriate template
3. Customize with client details
4. Calculate pricing
5. Generate proposal draft
6. Human review queue
7. Send via PandaDoc after approval

**Database Tables:** `proposals`, `proposal_templates`, `proposal_versions`

---

#### 6.4 Proposal Negotiation Agent

**Purpose:** Handle proposal back-and-forth

**Common Scenarios:**
- Price negotiation
- Scope changes
- Payment term requests
- Timeline adjustments
- Custom additions

**Process:**
1. Receive negotiation request
2. Classify request type
3. Check approval authority (pre-approved discounts, etc.)
4. Generate counter-proposal or acceptance
5. Route to human for approval if needed
6. Update proposal
7. Track all changes

**Database Tables:** `negotiations`, `negotiation_history`, `approval_authority`

---

#### 6.5 Proposal Tracking Agent

**Purpose:** Follow up on sent proposals

**Tracking:**
- Proposal views (PandaDoc webhook)
- Time spent on sections
- Multiple viewers
- Download/print events

**Follow-up Cadence:**
- Day 1: "Just sent it over"
- Day 3: Check in if no view
- Day 5: "Any questions?"
- Day 7: Value add content
- Day 10: Deadline reminder
- Day 14: Final push

**Process:**
1. Track proposal activity via webhooks
2. Trigger appropriate follow-up
3. Adjust strategy based on activity
4. 20-30 touchpoints total
5. Move to reactivation if no response after cadence

**Database Tables:** `proposal_tracking`, `proposal_views`, `proposal_followups`

---

### 7. PAYMENT & FINANCIAL

#### 7.1 Invoice Generation Agent

**Purpose:** Create and send invoices

**Triggered By:**
- Contract signed (deposit invoice)
- Milestone completed (milestone invoice)
- Project completed (final invoice)
- Monthly retainer due

**Process:**
1. Pull contract/proposal details
2. Generate invoice in Stripe
3. Send invoice to client
4. Log in QuickBooks
5. Update database

**Database Tables:** `invoices`, `invoice_items`, `invoice_status`

---

#### 7.2 Payment Collection Agent

**Purpose:** Track and collect payments

**Reminder Schedule:**
- Due date: Send invoice
- 3 days overdue: Gentle reminder
- 7 days overdue: Firmer reminder
- 14 days overdue: Escalation warning
- 30 days overdue: Pause work, final notice
- 60 days overdue: Collections consideration

**Process:**
1. Monitor invoice due dates
2. Send reminders per schedule
3. Track payment status
4. Alert on overdue
5. Escalate as needed

**Database Tables:** `payment_reminders`, `payment_status`

---

#### 7.3 Payment Processing Agent

**Purpose:** Handle Stripe payments

**Triggered By:** Stripe webhooks

**Events:**
- Payment successful → Update invoice, notify, proceed
- Payment failed → Retry logic, notify client
- Dispute/chargeback → Alert, pause work, investigate

**Database Tables:** `payments`, `payment_failures`, `disputes`

---

#### 7.4 Revenue Tracking Agent

**Purpose:** Track financial metrics

**Metrics:**
- MRR (Monthly Recurring Revenue)
- ARR (Annual Recurring Revenue)
- Revenue per client
- Revenue per campaign
- Revenue per niche
- Cost per acquisition
- Lifetime value

**Process:**
1. Track all revenue events
2. Calculate metrics
3. Generate weekly/monthly reports
4. Dashboard updates

**Database Tables:** `revenue_events`, `revenue_metrics`, `financial_reports`

---

### 8. CLIENT ONBOARDING

#### 8.1 Onboarding Orchestrator Agent

**Purpose:** Manage new client onboarding

**Triggered By:** Contract signed

**Onboarding Steps:**
1. Welcome email
2. Client questionnaire/intake form (Deformity)
3. Access provisioning request
4. Kickoff call scheduling
5. Internal project setup
6. Kickoff call
7. Project scope documentation
8. Onboarding complete

**Process:**
1. Send welcome email immediately
2. Send intake form
3. Monitor form completion
4. Request access credentials
5. Create internal workspace
6. Schedule kickoff
7. Conduct kickoff
8. Document scope
9. Mark onboarding complete
10. Transition to ACTIVE_PROJECT

**Database Tables:** `onboarding_progress`, `onboarding_steps`, `intake_responses`

---

#### 8.2 Onboarding Stuck Detector Agent

**Purpose:** Catch stalled onboardings

**Triggers:**
- Intake form not completed in 3 days
- No response to access requests in 2 days
- Kickoff call not scheduled in 5 days
- No communication in 5 days

**Process:**
1. Check onboarding progress daily
2. Identify stuck onboardings
3. Send reminder to client
4. Alert you after 2 reminders
5. Escalate if no progress in 7 days

**Database Tables:** `onboarding_alerts`, `stuck_onboardings`

---

#### 8.3 Internal Setup Agent

**Purpose:** Create internal project infrastructure

**Creates:**
- ClickUp project/workspace
- Google Drive folder structure
- Slack channel (if applicable)
- Airtable project record
- GHL record

**Process:**
1. Create all internal infrastructure
2. Set up folder templates
3. Configure project settings
4. Link all systems
5. Confirm setup complete

**Database Tables:** `project_infrastructure`, `setup_logs`

---

### 9. PROJECT DELIVERY

#### 9.1 Project Management Agent

**Purpose:** Track and update project progress

**Runs:** Every 2 hours

**Process:**
1. Sync Airtable, ClickUp, Todoist
2. Check milestone progress
3. Update project status
4. Identify blockers
5. Generate status summary

**Database Tables:** `projects`, `project_milestones`, `project_status`

---

#### 9.2 Client Update Agent

**Purpose:** Send progress updates to clients

**Schedule:**
- Weekly progress email
- Milestone completion notifications
- Blocker alerts

**Process:**
1. Generate progress summary
2. Create update email
3. Send to client
4. Log communication

**Database Tables:** `client_updates`, `update_logs`

---

#### 9.3 Client Approval Workflow Agent

**Purpose:** Get client sign-off on deliverables

**Process:**
1. Submit deliverable for review
2. Send review request to client
3. Track review status
4. Handle revision requests
5. Get final approval
6. Mark deliverable complete

**Database Tables:** `approval_requests`, `revision_requests`, `approvals`

---

#### 9.4 Scope Tracker Agent

**Purpose:** Detect and handle scope creep

**Process:**
1. Compare requests against original scope
2. Flag out-of-scope requests
3. Alert for review
4. Create change order if needed
5. Track scope changes

**Database Tables:** `scope_definitions`, `scope_changes`, `change_orders`

---

#### 9.5 Project Delay Handler Agent

**Purpose:** Manage and communicate delays

**Triggered By:** Milestone overdue

**Process:**
1. Detect delay
2. Assess impact
3. Generate revised timeline
4. Draft client communication
5. Send after approval
6. Update project schedule

**Database Tables:** `project_delays`, `delay_communications`

---

#### 9.6 Quality Assurance Agent

**Purpose:** Review deliverables before client sees them

**Checklist:**
- Completeness check
- Quality standards met
- Branding correct
- Links working
- No placeholder content
- Spell check

**Process:**
1. Run QA checklist
2. Flag issues
3. Request fixes
4. Re-check
5. Approve for client delivery

**Database Tables:** `qa_checklists`, `qa_results`

---

### 10. CLIENT SUCCESS & RETENTION

#### 10.1 Satisfaction Survey Agent

**Purpose:** Gather client feedback

**Survey Points:**
- Week 1 of project: "How's onboarding going?"
- Mid-project: "How are things progressing?"
- Project completion: "How did we do?"
- 30 days post-completion: "How's the deliverable working?"

**Process:**
1. Send survey at trigger points
2. Collect responses
3. Analyze sentiment
4. Alert on negative feedback
5. Track satisfaction trends

**Database Tables:** `satisfaction_surveys`, `survey_responses`, `satisfaction_scores`

---

#### 10.2 Churn Risk Detector Agent

**Purpose:** Identify at-risk clients

**Risk Signals:**
- Low engagement (not responding)
- Missed meetings
- Payment delays
- Negative survey responses
- Reduced communication
- Scope complaints

**Process:**
1. Monitor risk signals
2. Calculate churn risk score
3. Alert on high risk
4. Trigger intervention

**Database Tables:** `churn_risk_scores`, `risk_signals`

---

#### 10.3 Upsell Detector Agent

**Purpose:** Identify expansion opportunities

**Signals:**
- Client asks about other services
- High satisfaction scores
- Successful project delivery
- Mentions other pain points
- Company growth signals

**Process:**
1. Monitor for upsell signals
2. Score opportunity
3. Generate upsell recommendation
4. Create outreach task

**Database Tables:** `upsell_opportunities`, `upsell_signals`

---

#### 10.4 Testimonial Request Agent

**Purpose:** Collect case studies and testimonials

**Triggered By:**
- Project completed successfully
- High satisfaction score
- 2 weeks post-completion

**Process:**
1. Assess client relationship
2. Send testimonial request
3. Collect response
4. Format for use
5. Send thank you

**Database Tables:** `testimonial_requests`, `testimonials`

---

#### 10.5 Contract Renewal Agent

**Purpose:** Manage retainer renewals

**Reminders:**
- 90 days before: Internal alert
- 60 days before: Client touchpoint
- 30 days before: Renewal proposal
- 14 days before: Final reminder

**Process:**
1. Track contract end dates
2. Send reminders per schedule
3. Generate renewal proposal
4. Handle negotiations
5. Process renewal or offboarding

**Database Tables:** `contract_renewals`, `renewal_reminders`

---

### 11. OFFBOARDING & NURTURE

#### 11.1 Client Offboarding Agent

**Purpose:** Handle project completion and client exit

**Checklist:**
- All deliverables handed off
- Final invoice sent and paid
- Access credentials returned/revoked
- Files organized and shared
- Knowledge transfer complete
- Final feedback collected
- Testimonial requested

**Process:**
1. Run offboarding checklist
2. Send final deliverables
3. Collect final payment
4. Revoke access
5. Archive project
6. Move to long-term nurture

**Database Tables:** `offboarding_progress`, `offboarding_checklist`

---

#### 11.2 Knowledge Transfer Agent

**Purpose:** Train clients on deliverables

**Process:**
1. Create training documentation
2. Record walkthrough videos
3. Schedule training call if needed
4. Confirm client understands
5. Provide ongoing support window

**Database Tables:** `knowledge_transfers`, `training_materials`

---

#### 11.3 Long-Term Nurture Agent

**Purpose:** Stay in touch with past clients/prospects

**Nurture Content:**
- Newsletter/updates
- Value-add content
- Holiday greetings
- Industry news
- Case studies

**Process:**
1. Segment nurture list
2. Send appropriate content
3. Track engagement
4. Watch for re-engagement signals
5. Route back to active pipeline when ready

**Database Tables:** `nurture_list`, `nurture_sends`, `nurture_engagement`

---

#### 11.4 Trigger-Based Reactivation Agent

**Purpose:** Re-engage cold leads based on triggers

**Triggers:**
- Job change (new role = new budget/authority)
- Funding round (company has money)
- Company growth (hiring, expansion)
- Leadership change (new decision maker)
- Competitor mentioned (shopping again)
- Industry event (relevant timing)

**Process:**
1. Monitor all leads in reactivation/nurture pools
2. Detect trigger events
3. Generate relevant outreach
4. Move back to campaign
5. Track reactivation results

**Database Tables:** `reactivation_triggers`, `reactivation_campaigns`

---

#### 11.5 Referral Request Agent

**Purpose:** Ask for referrals from all contacts

**Timing:**
- Post-project completion
- After positive testimonial
- Closed-lost deals (they may know others)
- Annual touchpoint for past clients

**Process:**
1. Identify referral candidates
2. Send personalized referral request
3. Track referrals received
4. Thank referrers
5. Process referred leads

**Database Tables:** `referral_requests`, `referrals`, `referral_sources`

---

### 12. SYSTEM & ADMINISTRATION

#### 12.1 Database Manager Agent

**Purpose:** Maintain database health

**Tasks:**
- Daily cleanup of orphaned records
- Index optimization
- Backup verification
- Data integrity checks
- Archive old records

**Database Tables:** `maintenance_logs`, `backup_status`

---

#### 12.2 API Rate Limit Manager

**Purpose:** Prevent API throttling

**Limits to Track:**

| Service | Limit | Threshold | Action at Threshold |
|---------|-------|-----------|---------------------|
| Instantly | 50k/day | 90% | Throttle |
| Apollo | 1k/month | 90% | Switch to backup |
| Hunter | 5k/month | 90% | Switch to backup |
| Reoon | 10k/month | 90% | Alert |
| OpenAI | 10k tokens/min | 80% | Queue requests |

**Process:**
1. Track all API calls
2. Monitor usage against limits
3. Throttle at 90%
4. Queue at 95%
5. Alert on approaching limits

**Database Tables:** `api_usage`, `api_limits`, `api_alerts`

---

#### 12.3 Error Monitor Agent

**Purpose:** Track and alert on system errors

**Monitoring:**
- Agent failures
- API errors
- Webhook failures
- Database errors
- Integration issues

**Process:**
1. Log all errors
2. Classify severity
3. Alert on critical errors
4. Track error patterns
5. Generate daily error report

**Database Tables:** `error_logs`, `error_alerts`

---

#### 12.4 Health Check Agent

**Purpose:** Verify all integrations working

**Checks (Hourly):**
- Instantly API connection
- Reoon API connection
- Cal.com API connection
- Fathom webhook receiving
- PandaDoc API connection
- Stripe API connection
- All database connections

**Process:**
1. Run health checks hourly
2. Log results
3. Alert on failures
4. Track uptime metrics

**Database Tables:** `health_checks`, `uptime_metrics`

---

#### 12.5 Audit Log Agent

**Purpose:** Track all automated actions

**Logged Actions:**
- Lead status changes
- Emails sent
- Proposals sent
- Database modifications
- API calls
- Human approvals
- System configuration changes

**Process:**
1. Log every significant action
2. Include timestamp, actor, details
3. Retain for compliance period
4. Enable audit queries

**Database Tables:** `audit_logs`

---

#### 12.6 Learning & Feedback Agent

**Purpose:** Improve system from human corrections

**Learning Sources:**
- Email response corrections
- Personalization edits
- Proposal modifications
- Send Agent feedback
- Copy performance data

**Process:**
1. Collect all human corrections
2. Analyze patterns
3. Identify improvement areas
4. Suggest prompt/template updates
5. Track improvement over time

**Database Tables:** `correction_logs`, `learning_events`, `improvement_metrics`

---

## Agent Definitions & Handoffs

### Agent Interaction Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AGENT ORCHESTRATION                                │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │  ORCHESTRATOR │
                              │    AGENT      │
                              └──────┬───────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
         ▼                           ▼                           ▼
┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
│   RESEARCH      │        │   OUTREACH      │        │   DELIVERY      │
│   TEAM          │        │   TEAM          │        │   TEAM          │
├─────────────────┤        ├─────────────────┤        ├─────────────────┤
│ • Niche         │        │ • Campaign      │        │ • Onboarding    │
│ • Persona       │        │ • Copywriting   │        │ • Project Mgmt  │
│ • Lead          │        │ • Personalization│       │ • Client Success│
│ • Company       │        │ • Send Agent    │        │ • QA            │
│ • Intent        │        │ • Response      │        │ • Offboarding   │
│ • Competitive   │        │ • Meeting       │        └─────────────────┘
└─────────────────┘        │ • Proposal      │
                           └─────────────────┘
```

### Handoff Definitions

| From Agent | To Agent | Trigger | Data Passed |
|------------|----------|---------|-------------|
| Lead List Builder | Email Verification | New leads imported | lead_id, email |
| Email Verification | Waterfall Enrichment | Email invalid/unknown | lead_id, name, company |
| Waterfall Enrichment | Data Validation | Enrichment complete | lead_id, email, confidence |
| Data Validation | Campaign Creation | Lead validated | lead_id, campaign_id |
| Lead Research | Personalization | Research complete | lead_id, research_data |
| Company Research | Personalization | Research complete | company_id, research_data |
| Personalization | Send Agent | Lines generated | lead_id, personalization, confidence |
| Send Agent | Campaign (Instantly) | Lines approved | lead_id, final_personalization |
| Instantly Webhook | Response Handler | Reply received | lead_id, email_content, timestamp |
| Response Handler | Knowledge Base | Question detected | question_text |
| Response Handler | Meeting Scheduler | Meeting intent | lead_id, availability |
| Meeting Scheduler | Meeting Prep | Meeting booked | meeting_id, lead_id |
| Fathom Webhook | Transcript Processor | Call ended | transcript, meeting_id |
| Transcript Processor | Proposal Creation | Action items created | lead_id, call_insights |
| Proposal Creation | Proposal Tracking | Proposal sent | proposal_id, lead_id |
| Contract Signed | Onboarding Orchestrator | Signature received | client_id, contract_details |
| Onboarding Complete | Project Management | Kickoff done | project_id, client_id |
| Project Complete | Offboarding | Delivery accepted | project_id, client_id |
| Offboarding Complete | Long-Term Nurture | All tasks done | contact_id |

---

## Database Schema

### Core Tables

#### leads

```sql
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Basic Info
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_status VARCHAR(50), -- valid, invalid, risky, unknown
    phone VARCHAR(50),
    linkedin_url VARCHAR(500),

    -- Company Info
    company_id UUID REFERENCES companies(id),
    job_title VARCHAR(200),

    -- State Machine
    status VARCHAR(50) DEFAULT 'NEW',
    previous_status VARCHAR(50),
    status_changed_at TIMESTAMPTZ,

    -- Scoring
    lead_score INTEGER DEFAULT 0,
    intent_score INTEGER DEFAULT 0,
    engagement_score INTEGER DEFAULT 0,
    fit_score INTEGER DEFAULT 0,

    -- Campaign
    current_campaign_id UUID REFERENCES campaigns(id),
    campaign_entered_at TIMESTAMPTZ,

    -- Source
    source VARCHAR(100),
    source_campaign VARCHAR(100),
    import_batch_id UUID,

    -- Enrichment
    enrichment_complete BOOLEAN DEFAULT FALSE,
    last_enriched_at TIMESTAMPTZ,

    -- Personalization
    personalization_line TEXT,
    personalization_confidence INTEGER,
    personalization_source TEXT,

    -- Timezone
    timezone VARCHAR(50),
    optimal_send_time TIME,

    -- Flags
    do_not_contact BOOLEAN DEFAULT FALSE,
    unsubscribed BOOLEAN DEFAULT FALSE,
    bounced BOOLEAN DEFAULT FALSE,

    -- Metadata
    tags TEXT[],
    custom_fields JSONB
);
```

#### companies

```sql
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Basic Info
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    website VARCHAR(500),
    linkedin_url VARCHAR(500),

    -- Details
    industry VARCHAR(100),
    employee_count VARCHAR(50),
    revenue_range VARCHAR(50),
    founded_year INTEGER,
    headquarters_city VARCHAR(100),
    headquarters_country VARCHAR(100),

    -- Research
    description TEXT,
    last_researched_at TIMESTAMPTZ,

    -- Tech Stack
    tech_stack TEXT[],

    -- Metadata
    tags TEXT[],
    custom_fields JSONB
);
```

#### campaigns

```sql
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Basic Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'DRAFT', -- DRAFT, ACTIVE, PAUSED, COMPLETED

    -- Targeting
    niche_id UUID REFERENCES niches(id),
    persona_id UUID REFERENCES personas(id),

    -- Instantly Config
    instantly_campaign_id VARCHAR(100),

    -- Settings
    daily_send_limit INTEGER DEFAULT 50,
    sending_schedule JSONB,

    -- Email Sequence
    email_sequence JSONB, -- Array of email templates

    -- A/B Testing
    ab_test_enabled BOOLEAN DEFAULT FALSE,
    ab_test_config JSONB,

    -- Performance
    total_leads INTEGER DEFAULT 0,
    emails_sent INTEGER DEFAULT 0,
    opens INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    positive_replies INTEGER DEFAULT 0,
    meetings_booked INTEGER DEFAULT 0,
    deals_won INTEGER DEFAULT 0,
    revenue_generated DECIMAL(12,2) DEFAULT 0,

    -- Metadata
    tags TEXT[],
    custom_fields JSONB
);
```

#### conversations

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    lead_id UUID REFERENCES leads(id),

    -- Thread Info
    thread_id VARCHAR(255), -- Instantly thread ID
    subject VARCHAR(500),
    channel VARCHAR(50), -- email, linkedin, sms

    -- Status
    status VARCHAR(50), -- active, resolved, pending_human
    last_message_at TIMESTAMPTZ,
    last_message_direction VARCHAR(10), -- inbound, outbound

    -- Sentiment
    overall_sentiment VARCHAR(50),
    sentiment_score INTEGER,

    -- Metadata
    tags TEXT[]
);
```

#### messages

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    conversation_id UUID REFERENCES conversations(id),
    lead_id UUID REFERENCES leads(id),

    -- Message Details
    direction VARCHAR(10), -- inbound, outbound
    channel VARCHAR(50), -- email, linkedin, sms
    subject VARCHAR(500),
    body TEXT,
    html_body TEXT,

    -- Classification
    message_type VARCHAR(50), -- initial, follow_up, reply, check_in
    response_type VARCHAR(50), -- positive, negative, question, objection, ooo, unsubscribe

    -- Handling
    tier VARCHAR(50), -- auto_send, approval, escalation
    status VARCHAR(50), -- sent, delivered, pending_approval, approved, rejected
    approved_by VARCHAR(100),
    approved_at TIMESTAMPTZ,

    -- Draft Info (for outbound)
    draft_body TEXT,
    edited BOOLEAN DEFAULT FALSE,
    original_draft TEXT,

    -- Sentiment
    sentiment VARCHAR(50),
    sentiment_score INTEGER,

    -- Metadata
    external_id VARCHAR(255), -- Instantly message ID
    metadata JSONB
);
```

#### meetings

```sql
CREATE TABLE meetings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    lead_id UUID REFERENCES leads(id),

    -- Meeting Details
    title VARCHAR(255),
    scheduled_at TIMESTAMPTZ,
    duration_minutes INTEGER DEFAULT 30,
    meeting_type VARCHAR(50), -- discovery, demo, closing

    -- Cal.com
    cal_event_id VARCHAR(255),
    cal_booking_uid VARCHAR(255),
    meeting_link VARCHAR(500),

    -- Status
    status VARCHAR(50), -- scheduled, completed, no_show, cancelled, rescheduled

    -- Prep
    prep_sent BOOLEAN DEFAULT FALSE,
    prep_sent_at TIMESTAMPTZ,
    talking_points TEXT,

    -- Outcome
    outcome VARCHAR(50), -- positive, negative, follow_up_needed
    outcome_notes TEXT,

    -- Transcript
    fathom_recording_id VARCHAR(255),
    transcript TEXT,
    transcript_summary TEXT,

    -- Reminders
    reminder_24h_sent BOOLEAN DEFAULT FALSE,
    reminder_2h_sent BOOLEAN DEFAULT FALSE,
    reminder_15m_sent BOOLEAN DEFAULT FALSE,

    -- No-show handling
    no_show_count INTEGER DEFAULT 0,
    reschedule_count INTEGER DEFAULT 0
);
```

#### proposals

```sql
CREATE TABLE proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    lead_id UUID REFERENCES leads(id),
    meeting_id UUID REFERENCES meetings(id),

    -- Proposal Details
    title VARCHAR(255),
    description TEXT,

    -- Pricing
    total_amount DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'USD',
    pricing_breakdown JSONB,
    payment_terms VARCHAR(100),

    -- Scope
    scope_summary TEXT,
    deliverables JSONB,
    timeline TEXT,
    milestones JSONB,

    -- PandaDoc
    pandadoc_id VARCHAR(255),
    pandadoc_status VARCHAR(50),
    document_url VARCHAR(500),

    -- Status
    status VARCHAR(50), -- draft, sent, viewed, signed, expired, rejected
    sent_at TIMESTAMPTZ,
    viewed_at TIMESTAMPTZ,
    signed_at TIMESTAMPTZ,
    expired_at TIMESTAMPTZ,

    -- Tracking
    view_count INTEGER DEFAULT 0,
    last_viewed_at TIMESTAMPTZ,
    time_spent_seconds INTEGER,

    -- Follow-up
    followup_count INTEGER DEFAULT 0,
    last_followup_at TIMESTAMPTZ,

    -- Negotiation
    negotiation_count INTEGER DEFAULT 0,
    original_amount DECIMAL(12,2),
    discount_applied DECIMAL(12,2),
    discount_reason TEXT
);
```

#### clients

```sql
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Link to Lead
    lead_id UUID REFERENCES leads(id),
    company_id UUID REFERENCES companies(id),

    -- Client Info
    name VARCHAR(255),
    primary_contact_name VARCHAR(255),
    primary_contact_email VARCHAR(255),
    primary_contact_phone VARCHAR(50),

    -- Status
    status VARCHAR(50), -- onboarding, active, paused, churned, completed

    -- Contract
    contract_start_date DATE,
    contract_end_date DATE,
    contract_value DECIMAL(12,2),
    contract_type VARCHAR(50), -- one-time, retainer, milestone

    -- Financial
    total_revenue DECIMAL(12,2) DEFAULT 0,
    total_paid DECIMAL(12,2) DEFAULT 0,
    outstanding_balance DECIMAL(12,2) DEFAULT 0,

    -- Health
    satisfaction_score INTEGER,
    churn_risk_score INTEGER,
    last_engagement_at TIMESTAMPTZ,

    -- External IDs
    ghl_contact_id VARCHAR(255),
    airtable_record_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),

    -- Metadata
    tags TEXT[],
    custom_fields JSONB
);
```

#### projects

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    client_id UUID REFERENCES clients(id),
    proposal_id UUID REFERENCES proposals(id),

    -- Project Info
    name VARCHAR(255),
    description TEXT,
    project_type VARCHAR(100),

    -- Status
    status VARCHAR(50), -- setup, active, on_hold, completed, cancelled

    -- Timeline
    start_date DATE,
    target_end_date DATE,
    actual_end_date DATE,

    -- Scope
    original_scope TEXT,
    current_scope TEXT,
    scope_changes_count INTEGER DEFAULT 0,

    -- Progress
    progress_percentage INTEGER DEFAULT 0,
    current_phase VARCHAR(100),

    -- Financial
    budget DECIMAL(12,2),
    actual_cost DECIMAL(12,2),

    -- External IDs
    clickup_project_id VARCHAR(255),
    airtable_record_id VARCHAR(255),
    drive_folder_id VARCHAR(255),

    -- Metadata
    tags TEXT[]
);
```

#### project_milestones

```sql
CREATE TABLE project_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    project_id UUID REFERENCES projects(id),

    -- Milestone Info
    name VARCHAR(255),
    description TEXT,
    sequence_order INTEGER,

    -- Timeline
    target_date DATE,
    actual_completion_date DATE,

    -- Status
    status VARCHAR(50), -- pending, in_progress, review, approved, completed

    -- Approval
    requires_client_approval BOOLEAN DEFAULT TRUE,
    approved_by VARCHAR(255),
    approved_at TIMESTAMPTZ,

    -- Revision
    revision_count INTEGER DEFAULT 0,
    max_revisions INTEGER DEFAULT 3,

    -- Payment
    payment_trigger BOOLEAN DEFAULT FALSE,
    payment_amount DECIMAL(12,2),
    payment_status VARCHAR(50)
);
```

#### invoices

```sql
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    client_id UUID REFERENCES clients(id),
    project_id UUID REFERENCES projects(id),
    milestone_id UUID REFERENCES project_milestones(id),

    -- Invoice Info
    invoice_number VARCHAR(50) UNIQUE,
    description TEXT,

    -- Amounts
    subtotal DECIMAL(12,2),
    tax_amount DECIMAL(12,2),
    discount_amount DECIMAL(12,2),
    total_amount DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'USD',

    -- Dates
    issue_date DATE,
    due_date DATE,
    paid_date DATE,

    -- Status
    status VARCHAR(50), -- draft, sent, viewed, paid, overdue, cancelled

    -- Stripe
    stripe_invoice_id VARCHAR(255),
    stripe_payment_intent_id VARCHAR(255),

    -- Reminders
    reminder_count INTEGER DEFAULT 0,
    last_reminder_at TIMESTAMPTZ,

    -- Line Items
    line_items JSONB
);
```

#### onboarding_progress

```sql
CREATE TABLE onboarding_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    client_id UUID REFERENCES clients(id),

    -- Overall Status
    status VARCHAR(50), -- in_progress, stuck, completed
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Steps
    welcome_email_sent BOOLEAN DEFAULT FALSE,
    welcome_email_sent_at TIMESTAMPTZ,

    intake_form_sent BOOLEAN DEFAULT FALSE,
    intake_form_sent_at TIMESTAMPTZ,
    intake_form_completed BOOLEAN DEFAULT FALSE,
    intake_form_completed_at TIMESTAMPTZ,

    access_requested BOOLEAN DEFAULT FALSE,
    access_requested_at TIMESTAMPTZ,
    access_received BOOLEAN DEFAULT FALSE,
    access_received_at TIMESTAMPTZ,

    kickoff_scheduled BOOLEAN DEFAULT FALSE,
    kickoff_scheduled_at TIMESTAMPTZ,
    kickoff_meeting_id UUID REFERENCES meetings(id),
    kickoff_completed BOOLEAN DEFAULT FALSE,
    kickoff_completed_at TIMESTAMPTZ,

    internal_setup_complete BOOLEAN DEFAULT FALSE,
    internal_setup_at TIMESTAMPTZ,

    scope_documented BOOLEAN DEFAULT FALSE,
    scope_documented_at TIMESTAMPTZ,

    -- Stuck Detection
    stuck_alert_sent BOOLEAN DEFAULT FALSE,
    stuck_alert_sent_at TIMESTAMPTZ,
    stuck_reminder_count INTEGER DEFAULT 0
);
```

### Research Tables

#### niches

```sql
CREATE TABLE niches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    name VARCHAR(255),
    description TEXT,
    industry VARCHAR(100),

    -- Scoring
    market_size_score INTEGER,
    pain_intensity_score INTEGER,
    ability_to_pay_score INTEGER,
    competition_score INTEGER,
    overall_score INTEGER,

    -- Research
    pain_points TEXT[],
    common_objections TEXT[],
    buying_triggers TEXT[],
    recommended_messaging TEXT,

    -- Performance
    leads_generated INTEGER DEFAULT 0,
    deals_won INTEGER DEFAULT 0,
    revenue_generated DECIMAL(12,2) DEFAULT 0,

    -- Status
    status VARCHAR(50) -- researching, validated, active, paused
);
```

#### personas

```sql
CREATE TABLE personas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    niche_id UUID REFERENCES niches(id),

    name VARCHAR(255),
    job_titles TEXT[],

    -- Profile
    day_in_life TEXT,
    goals TEXT[],
    kpis TEXT[],
    frustrations TEXT[],

    -- Communication
    language_patterns TEXT[],
    jargon TEXT[],
    preferred_channels TEXT[],

    -- Behavior
    where_they_hang_out TEXT[],
    what_they_read TEXT[],
    influencers TEXT[],

    -- Buying
    buying_triggers TEXT[],
    objection_patterns TEXT[],
    decision_criteria TEXT[],

    -- Performance
    leads_generated INTEGER DEFAULT 0,
    deals_won INTEGER DEFAULT 0,
    revenue_generated DECIMAL(12,2) DEFAULT 0
);
```

#### lead_research

```sql
CREATE TABLE lead_research (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    lead_id UUID REFERENCES leads(id),

    -- LinkedIn
    linkedin_headline TEXT,
    linkedin_summary TEXT,
    linkedin_recent_posts JSONB,
    linkedin_activity_summary TEXT,

    -- Career
    career_history JSONB,
    education JSONB,
    skills TEXT[],

    -- Media
    news_mentions JSONB,
    podcast_appearances JSONB,
    speaking_engagements JSONB,
    awards JSONB,

    -- Social
    twitter_handle VARCHAR(100),
    twitter_recent_posts JSONB,

    -- Personalization
    personalization_angles JSONB,
    recommended_angle TEXT,

    -- Metadata
    research_sources TEXT[],
    last_updated_at TIMESTAMPTZ
);
```

#### company_research

```sql
CREATE TABLE company_research (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    company_id UUID REFERENCES companies(id),

    -- News
    recent_news JSONB,
    funding_history JSONB,
    acquisitions JSONB,
    leadership_changes JSONB,

    -- LinkedIn
    linkedin_recent_posts JSONB,
    linkedin_follower_count INTEGER,
    linkedin_employee_count INTEGER,

    -- Jobs
    current_job_postings JSONB,
    hiring_trends TEXT,

    -- Analysis
    growth_signals TEXT[],
    pain_signals TEXT[],
    trigger_events JSONB,

    -- Metadata
    research_sources TEXT[],
    last_updated_at TIMESTAMPTZ
);
```

#### intent_signals

```sql
CREATE TABLE intent_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    lead_id UUID REFERENCES leads(id),
    company_id UUID REFERENCES companies(id),

    -- Signal
    signal_type VARCHAR(100),
    signal_description TEXT,
    signal_strength INTEGER, -- 1-10
    signal_source VARCHAR(100),

    -- Context
    raw_data JSONB,

    -- Action
    action_taken VARCHAR(100),
    action_taken_at TIMESTAMPTZ
);
```

### Communication Tables

#### email_copy

```sql
CREATE TABLE email_copy (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    campaign_id UUID REFERENCES campaigns(id),

    -- Copy
    sequence_position INTEGER,
    subject VARCHAR(255),
    body TEXT,

    -- Variants
    variant_name VARCHAR(50),
    is_control BOOLEAN DEFAULT FALSE,

    -- Status
    status VARCHAR(50), -- draft, review, approved, active
    approved_by VARCHAR(100),
    approved_at TIMESTAMPTZ,

    -- Performance
    sends INTEGER DEFAULT 0,
    opens INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    positive_replies INTEGER DEFAULT 0
);
```

#### personalization_lines

```sql
CREATE TABLE personalization_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    lead_id UUID REFERENCES leads(id),

    -- Content
    line TEXT,
    source_citation TEXT,
    confidence_score INTEGER,

    -- Review
    status VARCHAR(50), -- generated, pending_review, approved, rejected, edited
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMPTZ,

    -- Edits
    original_line TEXT,
    edited BOOLEAN DEFAULT FALSE,
    edit_reason TEXT,

    -- Performance
    email_sent BOOLEAN DEFAULT FALSE,
    response_received BOOLEAN DEFAULT FALSE,
    response_type VARCHAR(50)
);
```

#### knowledge_base

```sql
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Content
    category VARCHAR(100),
    question TEXT,
    answer TEXT,

    -- Usage
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,

    -- Status
    status VARCHAR(50), -- active, review, archived
    source VARCHAR(100) -- manual, learned
);
```

### Tracking Tables

#### lead_status_history

```sql
CREATE TABLE lead_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    lead_id UUID REFERENCES leads(id),

    from_status VARCHAR(50),
    to_status VARCHAR(50),

    changed_by VARCHAR(100), -- agent name or 'human'
    change_reason TEXT,

    metadata JSONB
);
```

#### check_in_logs

```sql
CREATE TABLE check_in_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    lead_id UUID REFERENCES leads(id),
    conversation_id UUID REFERENCES conversations(id),

    check_in_number INTEGER,
    message_sent TEXT,

    response_received BOOLEAN DEFAULT FALSE,
    response_received_at TIMESTAMPTZ
);
```

#### proposal_tracking

```sql
CREATE TABLE proposal_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    proposal_id UUID REFERENCES proposals(id),

    event_type VARCHAR(50), -- viewed, downloaded, printed, signed
    event_at TIMESTAMPTZ,

    -- For views
    viewer_email VARCHAR(255),
    time_spent_seconds INTEGER,
    sections_viewed JSONB
);
```

#### followup_logs

```sql
CREATE TABLE followup_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    lead_id UUID REFERENCES leads(id),
    proposal_id UUID REFERENCES proposals(id),

    followup_number INTEGER,
    followup_type VARCHAR(50), -- email, sms, linkedin, call
    message_sent TEXT,

    response_received BOOLEAN DEFAULT FALSE,
    response_received_at TIMESTAMPTZ
);
```

### System Tables

#### api_usage

```sql
CREATE TABLE api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    service VARCHAR(100),
    endpoint VARCHAR(255),

    request_count INTEGER DEFAULT 1,
    tokens_used INTEGER,

    period_start TIMESTAMPTZ,
    period_end TIMESTAMPTZ,

    cost_usd DECIMAL(10,4)
);
```

#### error_logs

```sql
CREATE TABLE error_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    agent_name VARCHAR(100),
    error_type VARCHAR(100),
    error_message TEXT,
    stack_trace TEXT,

    severity VARCHAR(50), -- low, medium, high, critical

    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,

    metadata JSONB
);
```

#### audit_logs

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    actor VARCHAR(100), -- agent name or user id
    action VARCHAR(100),
    resource_type VARCHAR(100),
    resource_id UUID,

    old_values JSONB,
    new_values JSONB,

    ip_address VARCHAR(50),
    user_agent TEXT
);
```

#### correction_logs

```sql
CREATE TABLE correction_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    agent_name VARCHAR(100),
    correction_type VARCHAR(100),

    original_output TEXT,
    corrected_output TEXT,
    correction_reason TEXT,

    corrected_by VARCHAR(100),

    learning_applied BOOLEAN DEFAULT FALSE
);
```

#### health_checks

```sql
CREATE TABLE health_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    service VARCHAR(100),
    endpoint VARCHAR(255),

    status VARCHAR(50), -- healthy, degraded, down
    response_time_ms INTEGER,

    error_message TEXT
);
```

### Performance Tables

#### campaign_performance

```sql
CREATE TABLE campaign_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    campaign_id UUID REFERENCES campaigns(id),
    date DATE,

    emails_sent INTEGER DEFAULT 0,
    opens INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    positive_replies INTEGER DEFAULT 0,
    bounces INTEGER DEFAULT 0,
    unsubscribes INTEGER DEFAULT 0,

    meetings_booked INTEGER DEFAULT 0,
    proposals_sent INTEGER DEFAULT 0,
    deals_won INTEGER DEFAULT 0,
    revenue DECIMAL(12,2) DEFAULT 0
);
```

#### revenue_attribution

```sql
CREATE TABLE revenue_attribution (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    deal_id UUID,
    client_id UUID REFERENCES clients(id),

    -- Attribution
    first_touch_campaign_id UUID REFERENCES campaigns(id),
    last_touch_campaign_id UUID REFERENCES campaigns(id),
    multi_touch_campaigns JSONB,

    -- Revenue
    deal_value DECIMAL(12,2),
    currency VARCHAR(3),

    -- Timeline
    first_touch_at TIMESTAMPTZ,
    conversion_at TIMESTAMPTZ,
    days_to_close INTEGER
);
```

#### satisfaction_surveys

```sql
CREATE TABLE satisfaction_surveys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    client_id UUID REFERENCES clients(id),
    project_id UUID REFERENCES projects(id),

    survey_type VARCHAR(50), -- onboarding, mid_project, completion, post_30_days

    sent_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    score INTEGER, -- 1-10
    feedback TEXT,

    follow_up_needed BOOLEAN DEFAULT FALSE,
    follow_up_completed BOOLEAN DEFAULT FALSE
);
```

---

## Cron Jobs & Scheduled Tasks

### Hourly Jobs

| Job | Time | Description |
|-----|------|-------------|
| Integration Sync | Every hour | Sync data between Postgres, Airtable, GHL |
| Health Check | Every hour | Check all API connections |
| Stuck Onboarding Check | Every hour | Alert on stalled onboardings |
| Meeting Reminder Check | Every hour | Send upcoming meeting reminders |

### Daily Jobs

| Job | Time | Description |
|-----|------|-------------|
| Data Hygiene | 1:00 AM | Clean orphaned records, normalize data |
| Database Backup | 2:00 AM | Full database backup |
| Lead Scoring | 3:00 AM | Recalculate all lead scores |
| Email Verification Queue | 4:00 AM | Process pending verifications |
| Intent Signal Scan | 5:00 AM | Scan all tracked companies for signals |
| Daily Digest | 7:00 AM | Generate daily summary report |
| Reminder Generation | 10:00 AM | Create daily task reminders |
| Churn Risk Scan | 11:00 AM | Calculate client churn risk scores |
| Check-In Agent | 2:00 PM | Send check-ins to silent engaged leads |
| Proposal Follow-Up | 3:00 PM | Send daily proposal follow-ups |
| Invoice Reminder | 9:00 AM | Send payment reminders for due invoices |

### Weekly Jobs

| Job | Day/Time | Description |
|-----|----------|-------------|
| Campaign Performance Report | Monday 8:00 AM | Weekly campaign stats |
| Deliverability Report | Monday 8:30 AM | Domain health summary |
| Competitive Intelligence | Monday 9:00 AM | Weekly competitive summary |
| A/B Test Analysis | Monday 9:30 AM | Analyze and promote winners |
| Client Update Emails | Friday 3:00 PM | Weekly client progress updates |
| Pipeline Review Prep | Friday 4:00 PM | Generate pipeline summary |
| Reactivation Trigger Scan | Sunday 8:00 PM | Scan for reactivation opportunities |

### Monthly Jobs

| Job | Day/Time | Description |
|-----|----------|-------------|
| Revenue Attribution Report | 1st, 8:00 AM | Monthly revenue analysis |
| Niche Performance Analysis | 1st, 9:00 AM | ROI by niche |
| Contract Renewal Scan | 1st, 10:00 AM | Identify upcoming renewals |
| Learning Analysis | 15th, 10:00 AM | Analyze corrections for improvements |
| API Cost Analysis | Last day, 5:00 PM | Monthly API spend report |

---

## Webhook Integrations

### Incoming Webhooks

| Source | Event | Handler | Action |
|--------|-------|---------|--------|
| Instantly | email_replied | Response Handler | Process reply, classify, draft response |
| Instantly | email_bounced | Deliverability Monitor | Update lead status, alert if threshold |
| Instantly | email_unsubscribed | Lead Manager | Update lead status, remove from campaigns |
| Cal.com | booking_created | Meeting Scheduler | Create meeting record, send confirmation |
| Cal.com | booking_cancelled | Meeting Handler | Update status, trigger rebooking flow |
| Cal.com | booking_rescheduled | Meeting Handler | Update meeting time |
| Fathom | recording_ready | Transcript Processor | Process transcript, extract insights |
| PandaDoc | document_viewed | Proposal Tracking | Log view, update tracking |
| PandaDoc | document_signed | Proposal Handler | Close deal, trigger onboarding |
| PandaDoc | document_expired | Proposal Handler | Trigger follow-up sequence |
| Stripe | payment_succeeded | Payment Processor | Update invoice, notify, proceed |
| Stripe | payment_failed | Payment Processor | Retry, notify client |
| Stripe | invoice_paid | Payment Processor | Update records, thank client |
| Heyreach | connection_accepted | LinkedIn Agent | Log connection, send follow-up |
| Heyreach | message_received | LinkedIn Agent | Process message, sync to conversation |
| Apify | scrape_completed | Lead List Builder | Import leads to database |
| Deformity | form_submitted | Relevant Agent | Route based on form type |
| Google Drive | file_uploaded | File Manager | Organize, notify relevant party |

### Outgoing Webhooks/API Calls

| Destination | Trigger | Payload |
|-------------|---------|---------|
| Instantly | Campaign ready | Campaign config, leads, emails |
| Cal.com | Availability request | Date range, duration |
| PandaDoc | Proposal ready | Template, variables, recipient |
| Stripe | Invoice needed | Client, amount, description |
| Heyreach | LinkedIn action needed | Lead, message, action type |
| Slack | Approval needed | Draft, lead context, action buttons |
| Telegram | Alert | Alert type, details |
| n8n | Automation trigger | Event type, data payload |

---

## Human-in-the-Loop Checkpoints

### Gate 1: Campaign Launch

**Trigger:** AI completes campaign setup

**Review Items:**
- Niche/persona fit
- Email copy quality
- Personalization strategy
- Sending schedule
- Target list validation

**Approval Flow:**
1. AI generates campaign config
2. Draft sent to Slack with preview
3. Human reviews and approves/rejects
4. If approved, campaign launches
5. If rejected, revision notes sent back to AI

---

### Gate 2: Personalization Review (Send Agent)

**Trigger:** Batch of personalization lines generated

**Review Process:**
- First 20 lines: 100% human review
- After validation: 10% random sampling
- All low confidence (<80): human review

**Review Items:**
- Accuracy (claims match research)
- Tone (human, not creepy)
- Relevance (actually personalized, not generic)
- Source citation present

---

### Gate 3: Email Response Tiers

| Tier | Types | Action |
|------|-------|--------|
| Auto-Send | Meeting confirmations, calendar links, simple thanks | Send immediately |
| Approval | Questions, objections, pricing, complex replies | Draft → Slack → Wait |
| Escalation | Complaints, legal, technical, custom requests | Alert → Human handles |

**Approval Flow:**
1. Response classified by tier
2. For Approval tier: Draft sent to Slack/Telegram
3. Human can: Approve, Edit then Approve, Reject with notes
4. Response sent after approval
5. All edits logged for learning

---

### Gate 4: Proposal Generation

**Trigger:** Proposal draft ready

**Review Items:**
- Pricing accuracy
- Scope completeness
- Timeline realism
- Terms and conditions
- Deliverables clarity

**Approval Flow:**
1. AI generates proposal draft
2. Preview sent to you
3. Review and edit in PandaDoc
4. Approve for sending
5. PandaDoc sends to client

---

### Gate 5: Database Operations

**Requires Approval:**
- Bulk deletions > 50 records
- Campaign reassignments > 100 leads
- Status changes to "Closed Lost" (weekly review)
- Lead merges (fuzzy matches)

---

### Gate 6: Weekly Quality Review

**Manual Process:**
1. Sample 10 random conversations
2. Review AI decisions end-to-end
3. Check tone, accuracy, appropriateness
4. Identify patterns for improvement
5. Log findings for learning agent

---

## Feedback Loops

### Loop 1: Campaign → Sales Conversion

```
Campaign Performance Data
        │
        ▼
┌───────────────────┐
│   Analysis Agent  │
│   - Which niches  │
│     convert?      │
│   - Which personas│
│     close?        │
│   - Which copy    │
│     performs?     │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐     ┌───────────────────┐
│  Niche Research   │     │  Copywriting      │
│  Agent            │     │  Agent            │
│  - Prioritize     │     │  - Use winning    │
│    winning niches │     │    patterns       │
└───────────────────┘     └───────────────────┘
```

**Data Collected:**
- Reply rate by niche
- Meeting rate by persona
- Close rate by campaign
- Revenue by niche/persona

**Actions:**
- Deprioritize underperforming niches
- Double down on high-converting personas
- Replicate winning copy patterns
- Retire underperforming templates

---

### Loop 2: Human Corrections → AI Improvement

```
Human Edits/Corrections
        │
        ▼
┌───────────────────┐
│   Learning Agent  │
│   - Categorize    │
│     corrections   │
│   - Identify      │
│     patterns      │
│   - Suggest       │
│     improvements  │
└─────────┬─────────┘
          │
          ▼
┌───────────────────────────────────────────┐
│             Prompt/Template Updates        │
│   - Email copy templates                  │
│   - Personalization prompts               │
│   - Response drafting prompts             │
│   - Classification rules                  │
└───────────────────────────────────────────┘
```

**Data Collected:**
- Original AI output
- Human-corrected version
- Correction category (tone, accuracy, relevance, etc.)
- Context (lead type, situation)

**Actions:**
- Update prompts based on correction patterns
- Add examples to few-shot prompts
- Adjust classification rules
- Expand knowledge base

---

### Loop 3: Sales → Delivery Alignment

```
Project Outcomes
        │
        ▼
┌───────────────────┐
│   Analysis Agent  │
│   - Which promises│
│     are hard to   │
│     deliver?      │
│   - Which clients │
│     are profitable│
│   - Which projects│
│     run smoothest?│
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐     ┌───────────────────┐
│  Proposal Agent   │     │  Niche Research   │
│  - Adjust scope   │     │  - Target more    │
│    templates      │     │    profitable     │
│  - Update pricing │     │    client types   │
└───────────────────┘     └───────────────────┘
```

**Data Collected:**
- Project profitability (time spent vs revenue)
- Scope change frequency
- Client satisfaction by type
- Delivery challenges

**Actions:**
- Adjust proposal templates for realism
- Update pricing for high-effort projects
- Target client types with smooth deliveries
- Add scope guardrails

---

### Loop 4: Knowledge Base Evolution

```
Prospect Questions
        │
        ▼
┌───────────────────┐
│   Response Agent  │
│   - Check KB for  │
│     answer        │
│   - If not found, │
│     flag new Q    │
└─────────┬─────────┘
          │
     Not Found
          │
          ▼
┌───────────────────┐
│   Human Answers   │
│   Question        │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│   Add to KB       │
│   - Question      │
│   - Answer        │
│   - Category      │
└───────────────────┘
```

---

## Implementation Phases

### Phase 1: MVP Foundation (Weeks 1-4)

**Goal:** Basic lead gen to meeting booking flow

**Build:**
1. Core database schema (leads, companies, campaigns, conversations)
2. Lead List Builder Agent (Apify integration)
3. Email Verification Agent (Reoon)
4. Data Validation Agent
5. Campaign Creation Agent (Instantly)
6. Basic Copywriting Agent
7. Response Handler Agent (simple classification)
8. Basic Knowledge Base
9. Meeting Scheduler Agent (Cal.com)
10. Slack notifications for approvals

**Integrations:**
- Apify
- Reoon
- Instantly
- Cal.com
- Slack

**Human-in-the-Loop:**
- All email responses require approval
- Campaign launch requires approval

---

### Phase 2: Intelligence Layer (Weeks 5-8)

**Goal:** Smart personalization and response handling

**Build:**
1. Lead Research Agent
2. Company Research Agent
3. Personalization Line Agent
4. Send Agent (reviewer)
5. Response Handler v2 (tiered handling)
6. Check-In Agent
7. Meeting Prep Agent
8. Meeting Reminder Agent
9. Error monitoring
10. Health check system

**Integrations:**
- Fathom (receive transcripts)
- LinkedIn scraping via Apify

**Human-in-the-Loop:**
- First 20 personalizations: 100% review
- After: 10% sampling
- Approval tier responses

---

### Phase 3: Closing & Proposals (Weeks 9-12)

**Goal:** Complete sales cycle

**Build:**
1. Call Transcript Processor
2. Proposal Creation Agent
3. Proposal Tracking Agent
4. Proposal Negotiation Agent
5. No-Show Handler
6. A/B Testing Framework
7. Send Time Optimization (Phase 1)
8. Revenue Attribution tracking
9. Campaign Performance dashboard

**Integrations:**
- PandaDoc

**Human-in-the-Loop:**
- All proposals require approval
- Negotiation responses require approval

---

### Phase 4: Client Delivery (Weeks 13-16)

**Goal:** Onboarding through project completion

**Build:**
1. Onboarding Orchestrator Agent
2. Onboarding Stuck Detector
3. Internal Setup Agent
4. Project Management Agent
5. Client Update Agent
6. Scope Tracker Agent
7. QA Agent
8. Invoice Generation Agent
9. Payment Collection Agent
10. Milestone tracking

**Integrations:**
- ClickUp
- Google Drive
- Stripe
- QuickBooks
- Deformity

**Human-in-the-Loop:**
- Scope changes require approval
- Client communications (initially)

---

### Phase 5: Retention & Growth (Weeks 17-20)

**Goal:** Client success and revenue optimization

**Build:**
1. Satisfaction Survey Agent
2. Churn Risk Detector
3. Upsell Detector
4. Contract Renewal Agent
5. Testimonial Request Agent
6. Client Offboarding Agent
7. Knowledge Transfer Agent
8. Long-Term Nurture Agent
9. Reactivation Agent
10. Referral Request Agent

**Human-in-the-Loop:**
- Churn interventions
- Upsell conversations

---

### Phase 6: Multi-Channel & Advanced (Weeks 21-24)

**Goal:** Expand reach and optimize

**Build:**
1. LinkedIn Automation Agent (Heyreach)
2. SMS Agent
3. Voice Message Agent
4. Waterfall Email Enrichment
5. Progressive Enrichment Agent
6. Technographic Data Agent
7. Intent Signal Tracking
8. Competitive Intelligence Agent
9. Send Time Optimization (Phases 2-4)
10. Learning & Feedback Agent

**Integrations:**
- Heyreach
- SMS provider
- All waterfall enrichment tools

---

### Phase 7: Polish & Scale (Weeks 25+)

**Goal:** Optimization and automation refinement

**Build:**
1. Advanced A/B testing
2. Hallucination detection refinements
3. Prompt versioning system
4. Full audit logging
5. Advanced analytics dashboards
6. Capacity management
7. Lead routing logic
8. Auto-scaling rules
9. Performance optimization
10. Documentation and SOPs

**Focus:**
- Reduce human-in-the-loop where safe
- Improve AI accuracy from corrections
- Scale send volume
- Optimize costs

---

## Quick Reference: What to Build When

### Before You Can Send Any Emails

1. `leads` table
2. `companies` table
3. `campaigns` table
4. Lead List Builder Agent
5. Email Verification Agent
6. Data Validation Agent
7. Campaign Creation Agent

### Before You Can Handle Responses

1. `conversations` table
2. `messages` table
3. `knowledge_base` table
4. Response Handler Agent
5. Slack integration for approvals

### Before You Can Book Meetings

1. `meetings` table
2. Meeting Scheduler Agent
3. Cal.com integration

### Before You Can Send Proposals

1. `proposals` table
2. `call_transcripts` (for context)
3. Transcript Processor Agent
4. Proposal Creation Agent
5. PandaDoc integration

### Before You Can Onboard Clients

1. `clients` table
2. `onboarding_progress` table
3. `projects` table
4. Onboarding Orchestrator
5. Internal Setup Agent
6. Deformity integration

### Before You Can Collect Payment

1. `invoices` table
2. Invoice Generation Agent
3. Payment Collection Agent
4. Stripe integration
5. QuickBooks integration

---

## Next Steps

1. **Review this document** - Flag anything that seems wrong or missing
2. **Prioritize MVP features** - Confirm Phase 1 scope
3. **Set up development environment** - Pydantic AI, FastAPI, Postgres
4. **Create database schema** - Start with core tables
5. **Build first agent** - Lead List Builder is a good start
6. **Set up integrations** - Apify, Reoon, Instantly first

Ready to start building?
