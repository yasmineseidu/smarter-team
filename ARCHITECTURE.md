# Architecture

## Overview

Smarter Team uses an event-driven multi-agent architecture where specialized AI agents handle different business functions autonomously.

## Flow

```
plan/ → specs/ → tasks/ → app/ → docs/
```

## Key Folders

| Folder | Purpose |
|--------|---------|
| `.claude/` | Agent configuration, commands, skills, hooks |
| `.project/` | Project info, decisions, conventions |
| `config/` | All configuration (settings, database, celery, redis) |
| `app/backend/src/agents/` | Claude Agent SDK agent implementations |
| `app/backend/src/tasks/` | Celery background tasks |
| `app/backend/src/webhooks/` | Webhook handlers |
| `app/backend/src/integrations/` | Third-party API clients |
| `specs/` | Build specifications |
| `tasks/` | Task tracking (pending → in-progress → completed) |
| `planning/` | Architecture and design documents |

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SMARTER TEAM ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ENTRY POINTS                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Webhooks   │  │  Cron Jobs   │  │   Admin API  │          │
│  │  (FastAPI)   │  │  (Celery)    │  │  (FastAPI)   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 CELERY TASK QUEUE                        │   │
│  │              (Redis Broker + Backend)                    │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│         ┌───────────────────┼───────────────────┐               │
│         ▼                   ▼                   ▼               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ Lead Gen    │    │   Sales     │    │     PM      │         │
│  │   Agent     │    │   Agent     │    │   Agent     │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  Research   │    │  Developer  │    │  Marketing  │         │
│  │   Agent     │    │   Agent     │    │   Agent     │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
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
│  └────────────────┘  └────────────────┘  └────────────────┘    │
│  ┌────────────────┐  ┌────────────────┐                        │
│  │      Zep       │  │    Claude      │                        │
│  │  Long-Term     │  │     API        │                        │
│  │    Memory      │  │                │                        │
│  └────────────────┘  └────────────────┘                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Communication

### Event-Driven Handoffs

```python
# Agent A completes task and hands off to Agent B
await handoff_to_agent(
    from_agent="lead_generation",
    to_agent="sales",
    payload={"lead_id": "...", "context": "..."},
    priority="high"
)
```

### Shared Memory (Zep)

```python
# Store fact in long-term memory
await memory.add_fact(
    session_id="client_123",
    fact="Client prefers email communication",
    source="support_agent"
)

# Retrieve context for any agent
context = await memory.get_context(session_id="client_123")
```

## Data Flow

### Lead to Client Journey

```
1. Research Agent → identifies opportunity
2. Lead Gen Agent → finds and qualifies lead
3. Sales Agent → outreach and discovery call
4. Sales Agent → proposal and closing
5. PM Agent → client onboarding
6. Developer Agent → project delivery
7. Finance Agent → invoicing
8. Support Agent → ongoing relationship
```

## Configuration Architecture

All configuration lives in `/config/`:

```
config/
├── settings.py      # Environment variables (Pydantic)
├── database.py      # SQLAlchemy async setup
├── celery.py        # Celery app + beat schedule
├── redis.py         # Redis client + key patterns
├── cors.py          # CORS middleware
├── webhooks.py      # Webhook configurations
├── integrations.py  # Third-party API configs
├── constants.py     # App constants
└── logging.py       # Logging configuration
```

## Security Model

### API Security
- JWT authentication for admin endpoints
- Webhook signature verification
- Rate limiting per endpoint

### Agent Security
- Deny-all baseline for tool access
- Per-agent allowlists
- Audit logging for all actions
- Human-in-the-loop for sensitive operations

### Data Security
- Encrypted at rest (Supabase)
- TLS for all connections
- API key rotation support
- No secrets in agent context

## Scaling Strategy

### Horizontal Scaling

```
Phase 1 (10-20 clients):
- 1 FastAPI instance
- 4-8 Celery workers
- Supabase Pro
- Upstash Pro

Phase 2 (20-50 clients):
- 4 FastAPI instances + load balancer
- 16-24 Celery workers
- Connection pooling (PgBouncer)
- Redis clustering
```

### Vertical Scaling

- Agent task timeout: 10 minutes max
- Connection pooling: 100-200 connections
- Memory per worker: 2-4GB
- Vector index optimization
