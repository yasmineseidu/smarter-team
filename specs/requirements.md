# Smarter Team Requirements

Generated: 2024-12-05
Status: Draft

---

## Overview

**Problem:** Running an AI agency as a solopreneur requires managing lead generation, sales, project management, development, marketing, customer support, finance, and research - all simultaneously. This is unsustainable manually and limits growth potential.

**Solution:** Build an autonomous team of AI agents that handle all agency operations from lead generation to client delivery, enabling a single person to scale an AI agency from 0 to 8 figures.

**Target Audience:** Internal team (you as solopreneur/admin, with contractors when needed)

---

## Project Type

**Type:** AI/ML Application (Multi-Agent System)

**Phase:** Full Production

**Scale:** Medium (10-50 clients)

---

## Core Agent Roles

### 1. Lead Generation Agent
- Find and research prospects
- Scrape and validate contact information
- Qualify leads based on criteria
- Automated outreach via Instantly.ai
- Monitor Reddit, social media for opportunities

### 2. Sales/Closer Agent
- Handle inbound inquiries
- Conduct discovery calls (Retell AI)
- Create and send proposals (PandaDoc)
- Follow up and negotiate
- Close deals and handoff to PM

### 3. Project Manager Agent
- Onboard new clients
- Create project plans (ClickUp, Todoist)
- Assign tasks to appropriate agents
- Track progress and deadlines
- Client communication and updates

### 4. Developer Agent
- Write code for client projects
- Build AI solutions and integrations
- Code review and quality assurance
- Deploy and maintain solutions
- Documentation

### 5. Marketing/Content Agent
- Create content (blog posts, social media)
- Generate presentations (Gamma)
- Manage campaigns
- Brand consistency
- Social proof and case studies

### 6. Customer Support Agent
- Handle client questions
- Onboarding assistance
- Issue resolution
- Knowledge base maintenance
- Proactive check-ins

### 7. Finance/Billing Agent
- Create and send invoices (Stripe, QuickBooks)
- Track payments
- Financial reporting
- Contract management (Signaturley)
- Expense tracking

### 8. Research Agent
- Market research (Perplexity, Brave, Exa)
- Competitive analysis
- Technology trends
- Client industry research
- Opportunity identification

---

## Orchestration Requirements

### Trigger Types
- **Webhooks:** React to external events (Gmail, Instantly, GoHighLevel, etc.)
- **Cron Jobs:** Scheduled tasks (daily reports, weekly outreach, etc.)
- **Background Tasks:** Long-running operations (research, content generation)
- **Agent Handoffs:** Seamless transfer between agents with context preservation

### State Management
- Conversation history per client/lead
- Agent execution states
- Task queues and priorities
- Checkpointing for long operations
- Human-in-the-loop checkpoints

### Event-Driven Architecture
- Event bus for inter-agent communication
- Pub/sub for notifications
- Dead letter queues for failed operations
- Retry mechanisms with exponential backoff

---

## Integrations Needed

### AI/LLM Services
| Integration | Purpose | Priority |
|-------------|---------|----------|
| Anthropic Claude | Core agent intelligence | Critical |
| Perplexity | Research and search | High |
| ElevenLabs | Voice synthesis | High |
| Retell AI | Voice calls | High |
| Fal AI | Image/media generation | Medium |
| Replicate | Model hosting | Medium |

### Lead Generation & Email
| Integration | Purpose | Priority |
|-------------|---------|----------|
| Instantly.ai | Cold email campaigns | Critical |
| Autobound | Email personalization | High |
| Icypeas | Email finding | High |
| Findymail | Email verification | High |
| Anymailfinder | Email discovery | Medium |
| Tomba | Email lookup | Medium |
| Reoon | Email validation | Medium |

### CRM & Project Management
| Integration | Purpose | Priority |
|-------------|---------|----------|
| GoHighLevel | CRM and automation | Critical |
| Notion | Knowledge base | High |
| Airtable | Database/tracking | High |
| ClickUp | Project management | High |
| Todoist | Task management | Medium |

### Communication
| Integration | Purpose | Priority |
|-------------|---------|----------|
| Gmail | Email communication | Critical |
| Google Calendar | Scheduling | High |
| Cal.com | Meeting booking | High |

### Search & Research
| Integration | Purpose | Priority |
|-------------|---------|----------|
| Serper | Google search API | High |
| Exa | Neural search | High |
| Firecrawl | Web scraping | High |
| Brave Search | Search API | Medium |
| Reddit | Social listening | Medium |
| News API | Industry news | Medium |

### Documents & Storage
| Integration | Purpose | Priority |
|-------------|---------|----------|
| Google Drive | File storage | High |
| Google Sheets | Data/reporting | High |
| PandaDoc | Proposals/contracts | High |
| Signaturley | E-signatures | Medium |
| Gamma | Presentations | Medium |

### Payments & Finance
| Integration | Purpose | Priority |
|-------------|---------|----------|
| Stripe | Payment processing | Critical |
| QuickBooks | Accounting | High |

### Data & AI Infrastructure
| Integration | Purpose | Priority |
|-------------|---------|----------|
| Supabase | PostgreSQL database | Critical |
| Upstash | Redis caching/queues | Critical |
| Pinecone | Vector database | High |
| Zep | Memory/context | High |
| Kuration AI | Data enrichment | Medium |
| Rube MCP | MCP server | Medium |

---

## User Types & Permissions

### You (Solopreneur/Admin)
- Full system access
- Agent configuration and training
- Override any agent decision
- View all metrics and reports
- Human-in-the-loop approvals

### Agents (Autonomous)
- Execute assigned tasks
- Access required integrations
- Communicate with other agents
- Escalate when uncertain
- Log all actions

### Contractors/Freelancers
- Task-specific access
- View assigned work
- Submit deliverables
- Limited system visibility

---

## Technical Preferences

**Language:** Python (3.11+)

**Agent Framework:** Claude Agent SDK (Python)

**API Framework:** FastAPI

**Database:** Supabase PostgreSQL + Redis (Upstash)

**Vector Store:** Pinecone

**Memory:** Zep

**Deployment:** Coolify (self-hosted)

---

## Scale Requirements

**Expected Clients:** 10-50 active clients

**Performance Targets:**
- Webhook response: < 5 seconds
- Agent task completion: varies by task type
- Background job processing: near real-time

**Availability:** 99.9% uptime for critical paths

**Data Volume:**
- Thousands of leads
- Hundreds of conversations
- Extensive agent memory/context

---

## Success Criteria

**How do we know this project succeeded?**
1. Agents autonomously handle 80%+ of agency operations
2. Successfully close deals with minimal human intervention
3. Deliver client projects on time
4. Scale to 50+ clients without proportional effort increase
5. Generate revenue exceeding operational costs significantly

---

## Out of Scope (for now)

**Explicitly NOT included in current scope:**
- Client-facing dashboard (clients interact through normal channels)
- Multi-tenant SaaS (this is for your agency only)
- Mobile app
- White-label solution

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        SMARTER TEAM                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Webhooks   │  │  Cron Jobs   │  │  Manual Ops  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   EVENT BUS / QUEUE                      │   │
│  │                    (Redis/Upstash)                       │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│         ┌───────────────────┼───────────────────┐               │
│         ▼                   ▼                   ▼               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ Lead Gen    │◄──►│   Sales     │◄──►│     PM      │         │
│  │   Agent     │    │   Agent     │    │   Agent     │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         ▲                   ▲                   ▲               │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  Research   │◄──►│  Developer  │◄──►│  Marketing  │         │
│  │   Agent     │    │   Agent     │    │   Agent     │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         ▲                   ▲                   ▲               │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌─────────────┐    ┌─────────────┐                            │
│  │  Support    │◄──►│  Finance    │                            │
│  │   Agent     │    │   Agent     │                            │
│  └─────────────┘    └─────────────┘                            │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              SHARED INFRASTRUCTURE                        │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │  │
│  │  │  Supabase  │  │   Redis    │  │  Pinecone  │         │  │
│  │  │ PostgreSQL │  │  (Upstash) │  │   Vector   │         │  │
│  │  └────────────┘  └────────────┘  └────────────┘         │  │
│  │  ┌────────────┐  ┌────────────┐                         │  │
│  │  │    Zep     │  │   Claude   │                         │  │
│  │  │   Memory   │  │    API     │                         │  │
│  │  └────────────┘  └────────────┘                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Next Steps

1. **Tech Stack Research** - Use tech-stack-researcher skill to validate/refine choices
2. **Project Planning** - Use planning-generator skill to create implementation plan
3. **Project Initialization** - Use project-initializer skill to set up codebase

---

**Requirements Status:** Draft → Ready for Tech Stack Research
