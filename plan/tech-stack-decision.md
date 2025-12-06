# Tech Stack Decision

Generated: 2024-12-05
Status: **Approved**

---

## Requirements Summary

**Project:** Smarter Team - Multi-Agent AI Agency Automation
**Type:** AI/ML Application (Multi-Agent System)
**Scale:** Medium (10-50 clients), Full Production
**Target:** 8 autonomous agents, 40+ integrations, webhooks, cron jobs, background tasks

---

## Approved Stack

### Backend

| Component | Technology | Version | Reasoning |
|-----------|------------|---------|-----------|
| **Language** | Python | 3.11+ | Best AI/ML ecosystem, Claude SDK native support |
| **Agent Framework** | Claude Agent SDK | Latest | Official Anthropic SDK, subagent support, production patterns |
| **API Framework** | FastAPI | 0.115+ | Async-first, excellent DX, 9M monthly downloads |
| **Task Queue** | Celery | 5.4+ | Battle-tested (15+ years), scales to 10+ workers, mature ecosystem |
| **Message Broker** | Redis (Upstash) | - | Celery broker + result backend, serverless |

### Database & Storage

| Component | Technology | Reasoning |
|-----------|------------|-----------|
| **Primary Database** | Supabase PostgreSQL | Managed, real-time subscriptions, auto-generated APIs |
| **Cache / Queue** | Upstash Redis | Serverless, global edge, Celery broker |
| **Vector Database** | Pinecone | Production-grade, scales to billions of vectors |
| **Long-Term Memory** | Zep | Temporal knowledge graphs, agent memory management |

### Infrastructure

| Component | Technology | Reasoning |
|-----------|------------|-----------|
| **Deployment** | Coolify | Self-hosted PaaS, Docker-based, zero-downtime deploys |
| **Containerization** | Docker + Docker Compose | Standard, Coolify-native |
| **SSL/TLS** | Let's Encrypt (via Coolify) | Auto-renewal |

---

## Multi-Perspective Analysis Summary

### The Pragmatist (Ship Speed)
**Score: 7.5/10**
- Time to MVP: 4-6 weeks
- Developer experience is excellent (FastAPI + Claude SDK)
- 40+ integrations have Python SDKs
- Risk: Celery adds complexity vs ARQ, but scales better

### The Performance Engineer (Load Handling)
**Score: PASS**
- Webhook response: 50-400ms (target: <5s) ✓
- Memory usage: 5-10GB at peak ✓
- Scales to 50 clients with proper connection pooling
- Critical: Add PgBouncer for database connection management

### The Future-Focused (2027 Viability)
**Score: 7.2/10**
- Claude Agent SDK: 99% confidence (Anthropic $183B valuation)
- FastAPI: 98% confidence (91K GitHub stars, industry standard)
- Supabase: 95% confidence ($5B valuation, 250% YoY growth)
- Zep: 75% confidence (pre-release but explosive adoption)

### The Devil's Advocate (Risks)
**Critical Risks Identified:**
1. **Single Points of Failure:** Redis queue, Pinecone vectors, Supabase data
2. **Idempotency:** Celery at-least-once delivery requires idempotency keys
3. **Observability:** Claude SDK hides from standard monitoring - need custom logging
4. **Solopreneur Operations:** 8 services = complex incident response

**Mitigations:**
- Implement circuit breakers for external APIs
- Daily Supabase backups to S3
- Dead-letter queues for failed Celery tasks
- OpenTelemetry from day 1

### The Maintainer (Long-Term Support)
**Score: 6.5/10**
- FastAPI: Excellent (5 years stable, mature testing)
- Supabase: Excellent (PostgreSQL reliability)
- Celery: Excellent (15+ years, widely documented)
- Zep: Moderate (pre-release, community edition deprecated)
- Coolify: Adequate (self-hosted = your responsibility)

---

## Stack Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SMARTER TEAM ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ENTRY POINTS                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Webhooks   │  │  Cron Jobs   │  │   API Calls  │          │
│  │  (FastAPI)   │  │  (Celery)    │  │  (FastAPI)   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    FASTAPI APPLICATION                   │   │
│  │  • Webhook receivers    • REST API endpoints            │   │
│  │  • Request validation   • Authentication                │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               CELERY TASK QUEUE (Redis)                  │   │
│  │  • Task scheduling      • Retry logic                   │   │
│  │  • Dead-letter queues   • Priority queues               │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│         ┌───────────────────┼───────────────────┐               │
│         ▼                   ▼                   ▼               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ Lead Gen    │    │   Sales     │    │     PM      │         │
│  │   Agent     │    │   Agent     │    │   Agent     │         │
│  │ (Claude SDK)│    │ (Claude SDK)│    │ (Claude SDK)│         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  Research   │    │  Developer  │    │  Marketing  │         │
│  │   Agent     │    │   Agent     │    │   Agent     │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌─────────────┐    ┌─────────────┐                            │
│  │  Support    │    │  Finance    │                            │
│  │   Agent     │    │   Agent     │                            │
│  └─────────────┘    └─────────────┘                            │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                     SHARED INFRASTRUCTURE                        │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │    Supabase    │  │     Redis      │  │    Pinecone    │    │
│  │   PostgreSQL   │  │   (Upstash)    │  │  Vector Store  │    │
│  │                │  │                │  │                │    │
│  │ • Agent state  │  │ • Celery broker│  │ • Embeddings   │    │
│  │ • Client data  │  │ • Caching      │  │ • RAG context  │    │
│  │ • Audit logs   │  │ • Pub/sub      │  │ • Similarity   │    │
│  └────────────────┘  └────────────────┘  └────────────────┘    │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │      Zep       │  │    Claude      │  │  40+ External  │    │
│  │  Long-Term     │  │     API        │  │  Integrations  │    │
│  │    Memory      │  │                │  │                │    │
│  │                │  │ • Agent brain  │  │ • Gmail        │    │
│  │ • Temporal KG  │  │ • Tool calls   │  │ • Stripe       │    │
│  │ • Session mem  │  │ • Subagents    │  │ • Instantly    │    │
│  └────────────────┘  └────────────────┘  └────────────────┘    │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                      DEPLOYMENT (COOLIFY)                        │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Docker Compose → VPS → Auto SSL → Zero-Downtime       │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Alternatives Considered

| Alternative | Why Not Chosen |
|-------------|----------------|
| **ARQ (async queue)** | Celery more battle-tested for 8+ workers, better monitoring |
| **LangChain/LangGraph** | Claude Agent SDK is official, tighter Claude integration |
| **CrewAI** | Less flexible than Claude SDK for custom orchestration |
| **Mem0** | Zep has better temporal knowledge graphs for agent memory |
| **Qdrant/Weaviate** | Pinecone is fully managed, no infrastructure |
| **Railway/Render** | Coolify gives full control on own VPS, better for 40+ integrations |
| **Kubernetes** | Overkill for 10-50 clients, Docker Compose sufficient |

---

## Cost Estimates (Monthly)

| Service | Tier | Estimated Cost |
|---------|------|----------------|
| Supabase | Pro | $25-100 |
| Upstash Redis | Pro (10GB) | $50-100 |
| Pinecone | Standard | $70-150 |
| Zep | Starter/Growth | $19-249 |
| Anthropic Claude | API usage | $100-500 |
| Coolify VPS | 8 CPU, 16GB RAM | $100-200 |
| **Total** | | **$364-1,299/month** |

---

## Implementation Priorities

### Phase 1: Core Infrastructure (Week 1-2)
1. Set up Coolify on VPS
2. Deploy FastAPI skeleton
3. Configure Supabase + Redis
4. Implement Celery task queue
5. Add OpenTelemetry logging

### Phase 2: Agent Foundation (Week 2-3)
1. Create base agent class with Claude SDK
2. Implement first agent (Lead Generation)
3. Add Pinecone for RAG context
4. Configure Zep for long-term memory

### Phase 3: Integration Layer (Week 3-4)
1. Build integration middleware pattern
2. Connect 10 priority integrations
3. Implement webhook receivers
4. Add circuit breakers

### Phase 4: Full Agent Team (Week 4-6)
1. Deploy all 8 agents
2. Implement agent handoff protocol
3. Add cron job scheduling
4. Complete remaining integrations

---

## User Decision

**Approved by:** User
**Date:** 2024-12-05
**Stack Choice:** Recommended Stack with Celery + Zep

**Notes:**
- Celery chosen over ARQ for battle-tested scaling
- Zep confirmed for long-term agent memory
- All original preferences validated

---

## Next Steps

1. **planning-generator** - Create comprehensive planning documents
2. **project-structure-creator** - Generate 100+ file project structure
3. **project-initializer** - Initialize Git, dependencies, database

---

**Tech Stack Status:** Approved → Ready for Planning
