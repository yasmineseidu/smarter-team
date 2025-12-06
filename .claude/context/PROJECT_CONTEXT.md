# Project Context

## Overview

**Smarter Team** is a multi-agent system that autonomously runs an AI agency. 76+ specialized agents orchestrate the complete client lifecycle from prospecting to delivery, retention, offboarding, and system maintenance.

## Tech Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Runtime |
| FastAPI | 0.115.0+ | Web framework |
| Celery | 5.4.0+ | Task queue |
| Redis | 5.0.0+ | Cache + Celery broker |
| SQLAlchemy | 2.0.0+ | Async ORM |
| asyncpg | 0.29.0+ | PostgreSQL driver |
| Anthropic | 0.37.0+ | Claude API |
| Pinecone | 3.0.0+ | Vector database |
| httpx | 0.27.0+ | HTTP client |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 15.0.0 | React framework |
| React | 19.0.0 | UI library |
| TypeScript | 5.6.0 | Type safety |
| Tailwind CSS | 3.4.0 | Styling |
| Vitest | 3.0.0 | Unit testing |
| Playwright | (CI only) | E2E testing |

## Directory Structure

```
smarter-team/
├── app/
│   ├── backend/           # Python/FastAPI backend
│   │   ├── src/
│   │   │   ├── agents/    # Agent implementations
│   │   │   ├── integrations/  # API clients
│   │   │   ├── tasks/     # Celery tasks
│   │   │   ├── webhooks/  # Webhook handlers
│   │   │   ├── config.py  # Settings
│   │   │   └── main.py    # FastAPI app
│   │   ├── __tests__/     # Pytest tests
│   │   ├── pyproject.toml
│   │   └── Makefile
│   └── frontend/          # Next.js frontend
│       ├── app/           # App Router pages
│       ├── components/    # React components
│       ├── __tests__/     # Vitest tests
│       └── package.json
├── plan/
│   ├── agents/            # 76 agent plans (rough designs)
│   └── database/          # Database plans
├── specs/
│   ├── agents/            # 76 locked-in agent specs
│   └── database-schema/
│       └── migrations/    # 8 SQL migration files
├── tasks/
│   ├── backend/           # pending/_in-progress/_completed
│   ├── frontend/
│   ├── database/
│   ├── deployment/
│   └── TASK-LOG.md
└── .github/workflows/
    └── ci.yml             # GitHub Actions CI
```

## Core Abstractions

### BaseAgent (src/agents/base_agent.py)
Abstract base class for all 76+ agents.

**Key methods:**
- `system_prompt` (property, abstract) - Agent's system prompt
- `process_task(task)` (async, abstract) - Task processing logic
- `handoff_to(target, payload, priority)` - Inter-agent handoffs via Celery
- `register_tool(tool, name, description)` - Tool registration
- `log_action(action, details)` - Audit logging
- `get_memory_context(session_id)` - Zep memory retrieval (TODO)
- `store_memory(session_id, fact, metadata)` - Zep memory storage (TODO)

**Usage:**
```python
from src.agents.base_agent import BaseAgent

class LeadQualificationAgent(BaseAgent):
    @property
    def system_prompt(self) -> str:
        return "You qualify leads based on ICP criteria..."

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        lead_id = task["lead_id"]
        # Qualify lead logic
        return {"status": "qualified", "score": 85}
```

### BaseIntegrationClient (src/integrations/base.py)
Abstract base class for all third-party API clients.

**Key features:**
- Lazy HTTP client creation with httpx
- Bearer token authentication
- Rate limit tracking
- Async request methods (get, post, put, patch, delete)

**Usage:**
```python
from src.integrations.base import BaseIntegrationClient

class InstantlyClient(BaseIntegrationClient):
    def __init__(self, api_key: str):
        super().__init__(
            name="instantly",
            base_url="https://api.instantly.ai",
            api_key=api_key,
        )

    async def send_email(self, data: dict) -> dict:
        return await self.post("/v1/emails", json=data)
```

## Database Architecture

### Migration Files (8 total)
| Migration | Purpose |
|-----------|---------|
| 001_core_tables.sql | UUID extension, ENUMs, core tables |
| 002_lead_entities.sql | Leads and related entities |
| 003_communication_tables.sql | Conversations, messages |
| 004_sales_process_tables.sql | Meetings, proposals, clients |
| 005_system_tables.sql | Audit, errors, health checks |
| 006_functions_and_triggers.sql | DB functions, triggers |
| 007_learning_system.sql | Learning & improvement system |
| 008_meeting_management_system.sql | Meeting management (31KB, comprehensive) |

### Key Tables
- **Core**: `leads`, `companies`, `campaigns`, `conversations`, `messages`
- **Sales**: `meetings`, `proposals`, `clients`, `projects`, `invoices`
- **System**: `audit_logs`, `error_logs`, `health_checks`, `api_usage`
- **Learning (007)**: `knowledge_base`, `response_tracking`, `agent_learning`, `faq_management`
- **Meetings (008)**: `meeting_participants`, `fathom_integrations`, `meeting_notes`, `call_performance_analytics`

## Agent Categories (76 agents)

| Category | Count | Key Agents |
|----------|-------|------------|
| Research | 6 | niche, persona, lead, company, competitive intelligence |
| Lead Generation | 7 | lead list builder (Apify), email verification, data validation |
| Campaign | 11 | A/B testing, copywriting, personalization, send-time optimization |
| Response | 5+ | email handler, knowledge base, conversation intelligence |
| Meeting | 9 | lifecycle orchestrator, scheduler, Fathom integration |
| Proposal | 5 | transcript processing, proposal creation (PandaDoc) |
| Payment | 4 | invoice generation, Stripe processing |
| Onboarding | 3 | orchestrator, stuck detector |
| Delivery | 6 | project management, QA |
| Retention | 5 | churn risk, upsell detection |
| Offboarding | 5 | knowledge transfer, reactivation |
| System | 10+ | database manager, error monitoring |

## Development Workflow

### Before Building
1. Read task from `tasks/[domain]/pending/`
2. Read relevant spec from `specs/`
3. Check existing patterns in codebase

### During Building
1. Write tests first (TDD approach)
2. Implement with full type hints
3. Run `make check` continuously

### After Building
1. All quality checks pass (`make check`)
2. Tests written and passing
3. Move task to `_completed/`
4. Update `tasks/TASK-LOG.md`

### Quality Gates (MUST pass)
- [ ] All tests pass (`pytest`)
- [ ] No linting errors (`ruff check`)
- [ ] No type errors (`mypy`)
- [ ] No formatting issues (`ruff format --check`)
- [ ] Coverage requirements met

## Integrations (40+ planned)

### AI Services
- Claude (Anthropic) - Primary AI
- Perplexity - Research
- ElevenLabs - Voice synthesis
- Retell - Voice calls

### Lead Generation
- Instantly, Icypeas, Findymail - Email discovery
- Apify - Lead scraping
- Firecrawl - Web scraping

### CRM & PM
- GoHighLevel, Notion, Airtable, ClickUp

### Communication
- Cal.com - Scheduling
- Gmail, Google Calendar/Tasks

### Payments & Documents
- Stripe, QuickBooks
- PandaDoc, Google Drive/Sheets

### Memory & Vector DB
- Pinecone - Vector storage
- Zep - Agent memory

## Environment Variables

**Required:**
```bash
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
```

See `.env.example` for full list of 40+ optional integrations.
