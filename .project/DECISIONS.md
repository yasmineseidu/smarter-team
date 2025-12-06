# Decisions

Technical and architectural decisions for Smarter Team.

---

## 2024-12-05 - Agent Framework: Claude Agent SDK

**Context**: Needed to choose between LangChain, LangGraph, CrewAI, and Claude Agent SDK.

**Decision**: Use Claude Agent SDK (Python).

**Why**:
- Official Anthropic SDK with first-class support
- Built-in subagent orchestration
- Production patterns included (deny-all permissions, hooks)
- Tighter Claude integration than third-party frameworks
- Growing ecosystem and documentation

---

## 2024-12-05 - Task Queue: Celery over ARQ

**Context**: Needed async task queue for background processing.

**Decision**: Use Celery with Redis broker.

**Why**:
- 15+ years battle-tested in production
- Better monitoring (Flower)
- More mature ecosystem
- Scales to 10+ workers easily
- ARQ is lighter but Celery's maturity wins for critical operations

---

## 2024-12-05 - Database: Supabase PostgreSQL

**Context**: Needed reliable database with real-time capabilities.

**Decision**: Use Supabase managed PostgreSQL.

**Why**:
- PostgreSQL reliability (30+ year track record)
- Real-time subscriptions built-in
- Auth and storage included
- $5B valuation, 250% YoY growth
- Reduces DevOps burden

---

## 2024-12-05 - Memory: Zep for Long-Term Memory

**Context**: Agents need to remember context across sessions.

**Decision**: Use Zep for temporal knowledge graphs.

**Why**:
- Purpose-built for agent memory
- Temporal knowledge graphs (not just vector search)
- Session + long-term memory layers
- Better than Pinecone-only approach for conversation context

**Risk**: Pre-release status. Have fallback plan to Pinecone + PostgreSQL.

---

## 2024-12-05 - Deployment: Coolify Self-Hosted

**Context**: Need deployment platform for Docker containers.

**Decision**: Use Coolify on own VPS.

**Why**:
- Full control over infrastructure
- No vendor lock-in
- Zero-downtime deployments
- Auto SSL with Let's Encrypt
- Cost-effective for 40+ integrations
- Docker Compose native

**Trade-off**: Self-hosted = own responsibility for ops. Acceptable for this use case.

---

## 2024-12-05 - Project Structure: Screaming Architecture

**Context**: How to organize the codebase.

**Decision**: Use screaming architecture with domain-focused folders.

**Why**:
- Folder names describe purpose, not technology
- Easy to navigate for new contributors
- Clear separation: `agents/`, `tasks/`, `webhooks/`
- Config centralized in `config/`
- Task tracking with `tasks/pending/` → `_completed/` workflow

---

## Template

```markdown
## YYYY-MM-DD - [Decision Title]

**Context**: [Why was this decision needed?]

**Decision**: [What was decided?]

**Why**: [Reasoning and trade-offs]
```
