# Tech Stack Recommendations - Smarter Team

**Generated:** 2025-12-05 (Updated)
**Analysis Type:** Tech Stack & Testing Stack Modernization
**Focus Area:** ORM Decision & Overall Stack Assessment

---

## Executive Summary

Your question was: **"Do I need an ORM?"**

**Short Answer:** Yes, keep SQLAlchemy 2.0. It's the 2025 best practice for Python/PostgreSQL async applications.

**Research Finding:** SQLAlchemy dominates the Python ORM ecosystem in 2025, particularly when paired with FastAPI. While raw SQL can be ~30% faster for simple queries, SQLAlchemy 2.0's async support, type safety, and security benefits make it the recommended choice for multi-agent systems with complex data relationships.

---

## 1. Current State Summary

### Backend Tech Stack

| Component | Current Version | Status |
|-----------|-----------------|--------|
| Python | 3.11+ | Current (LTS until 2027) |
| FastAPI | 0.115.0+ | Current (Best 2025 choice) |
| SQLAlchemy | 2.0.0+ | Current (Async-first) |
| AsyncPG | 0.29.0+ | Current |
| Celery | 5.4.0+ | Current (Gold standard) |
| Redis | 5.0.0+ | Current (7.x in Docker) |
| Anthropic SDK | 0.37.0+ | Current |
| Pinecone | 3.0.0+ | Current |
| Ruff | 0.7.0+ | Current |
| MyPy | 1.11.0+ | Current (Strict mode) |

### Testing Stack

| Component | Current Version | Status |
|-----------|-----------------|--------|
| pytest | 8.0.0+ | Current |
| pytest-asyncio | 0.24.0+ | Current |
| pytest-cov | 5.0.0+ | Current |
| Vitest | 3.0.0 | Current (Best 2025 choice) |
| Playwright | Latest | Current (Best 2025 choice) |

### Frontend Stack

| Component | Current | Status |
|-----------|---------|--------|
| Next.js | 15.0.0 | Current (React 19) |
| React | 19.0.0 | Current |
| TypeScript | 5.6.0 | Current |
| Tailwind CSS | 3.4.0 | Current |

---

## 2. Research Findings (2025 Best Practices)

### Backend Framework

**Research Finding:** FastAPI remains the go-to choice for Python API development in 2025, used by OpenAI, Anthropic, and Microsoft. Litestar is emerging as a high-performance alternative with msgspec (12x faster than Pydantic V2), but FastAPI has better ecosystem maturity and real-world stability.

**Recommendation:** KEEP FastAPI - Your stack is already using the 2025 best practice. No changes needed.

Sources:
- [FastAPI vs. Litestar: Which Python Web Framework Will Dominate 2025?](https://medium.com/top-python-libraries/fastapi-vs-litestar-which-python-web-framework-will-dominate-2025-1e63428268f2)
- [Litestar vs FastAPI | Better Stack](https://betterstack.com/community/guides/scaling-python/litestar-vs-fastapi/)

---

### Frontend Framework

**Research Finding:** Next.js dominates React-based enterprise projects (78% of new React apps use Next.js). The framework's App Router and Server Components have redefined modern web development. Svelte produces 60-70% smaller bundles but has smaller ecosystem.

**Recommendation:** IMPLEMENT Next.js - Your `.env.example` already references Next.js (ports 3000/8000), but no `package.json` exists. Need to set up the frontend.

**Implementation Scope:**
- Create `app/frontend/package.json` with Next.js 15.x
- Configure TypeScript, Tailwind CSS
- Set up testing with Vitest + React Testing Library
- Configure ESLint + Prettier

Sources:
- [Frontend Frameworks in 2025: What's Hot](https://www.leverture.com/post/frontend-frameworks-in-2025-whats-hot-whats-not-and-whats-next)
- [JavaScript Frameworks Comparison 2025](https://www.brilworks.com/blog/javascript-web-frameworks-comparison/)

---

### Database & ORM (YOUR QUESTION)

**Research Finding:** SQLAlchemy dominates the Python ORM ecosystem in 2025, particularly when paired with FastAPI.

**Performance Comparison:**
- Raw SQL (psycopg): ~0.85s for 1000 queries
- SQLAlchemy: ~1.23s for 1000 queries (~30% overhead)

**When to use SQLAlchemy (YOUR CASE):**
- Complex relationships (76 agents, 8+ migration files)
- Type safety requirements (mypy --strict)
- Security-sensitive operations (SQL injection protection by default)
- Team maintainability

**When to use Raw SQL:**
- Bulk inserts (>10k rows)
- Complex PostgreSQL-specific features (window functions, CTEs)
- Performance-critical hot paths

**Recommendation:** KEEP SQLAlchemy 2.0 - The 30% performance difference is negligible for your use case (API requests, agent handoffs). Your 76-agent system benefits from:
- Async support with asyncpg
- Database independence
- SQL injection protection
- Better code maintainability

Sources:
- [Medium - SQLAlchemy vs Raw SQL](https://medium.com/@melihcolpan/sqlalchemy-vs-raw-sql-queries-performance-comparison-and-best-practices-caba49125630)
- [Nucamp - Modern ORM Frameworks 2025](https://www.nucamp.co/blog/coding-bootcamp-backend-with-python-2025-modern-orm-frameworks-in-2025-django-orm-sqlalchemy-and-beyond)
- [InfoWorld - Best ORMs for Python](https://www.infoworld.com/article/2335270/6-orms-for-every-database-powered-python-app.html)

---

### Database

**Research Finding:** PostgreSQL is no longer "just" a relational database - with native JSONB indexing, parallel query execution, and pgvector for AI/ML workloads, it handles mixed workloads that used to be MongoDB's territory. Perfect for fintech, ERPs, and analytics.

**Recommendation:** KEEP PostgreSQL (Supabase) - Your stack is already using the 2025 best practice.

Sources:
- [MySQL vs PostgreSQL vs MongoDB: Which Database to Choose in 2025?](https://rameshfadatare.medium.com/mysql-vs-postgresql-vs-mongodb-which-database-to-choose-in-2025-fe209d749e88)
- [PostgreSQL vs. MongoDB in 2025](https://dev.to/hamzakhan/postgresql-vs-mongodb-in-2025-which-database-should-power-your-next-project-2h97)

---

### Python Testing Framework

**Research Finding:** pytest is the leading choice for Python testing in 2025 with 1300+ plugins, automatic discovery, and excellent async support. Pytest can run unittest suites out of the box.

**Recommendation:** KEEP pytest - Your stack is already using the 2025 best practice. However, you have 0 actual tests written (only fixtures).

**Action Required:**
- Write actual unit tests for `src/agents/`
- Write integration tests for API endpoints
- Target: 80%+ code coverage

Sources:
- [10 Best Python Testing Frameworks in 2025 - GeeksforGeeks](https://www.geeksforgeeks.org/python/best-python-testing-frameworks/)
- [Top 15 Python Testing Frameworks in 2025 | BrowserStack](https://www.browserstack.com/guide/top-python-testing-frameworks)

---

### TypeScript Testing Framework

**Research Finding:** Vitest runs 10-20x faster than Jest in watch mode, with native TypeScript and ESM support out of the box. Vitest 3 was released January 2025 with new features. It's a drop-in replacement for Jest.

**Recommendation:** USE Vitest (not Jest) for frontend testing.

**Migration Effort:** Low - Frontend has no tests yet, so this is a fresh setup, not a migration.

**Implementation:**
- Install Vitest 3.x, @testing-library/react, happy-dom
- Configure `vitest.config.ts`
- No Jest migration needed (no existing tests)

Sources:
- [Vitest vs Jest | Speakeasy](https://www.speakeasy.com/blog/vitest-vs-jest)
- [Vitest vs. Jest: Choosing The Right Testing Framework](https://saucelabs.com/resources/blog/vitest-vs-jest-comparison)

---

### E2E Testing Framework

**Research Finding:** Playwright is the fastest E2E framework (4.5s average vs Cypress 9.4s), supports multiple browsers (Chromium, Firefox, WebKit), parallel execution, and multi-language support. Microsoft-backed with monthly releases.

**Recommendation:** USE Playwright for E2E testing.

**Implementation:**
- Install @playwright/test
- Configure `playwright.config.ts`
- Set up test directory in `/tests/e2e/`
- Configure CI/CD integration

Sources:
- [Playwright vs. Cypress: The Ultimate 2025 E2E Testing Showdown](https://www.frugaltesting.com/blog/playwright-vs-cypress-the-ultimate-2025-e2e-testing-showdown)
- [Playwright vs Cypress: Key Differences | LambdaTest](https://www.lambdatest.com/blog/cypress-vs-playwright/)

---

### Task Queue

**Research Finding:** Celery remains battle-tested for heavy data pipelines with 10+ workers. Dramatiq and Huey are 10x faster in benchmarks but lack Celery's feature set (Beat scheduler, Flower monitoring, multiple brokers). ARQ is asyncio-native but struggles with scale.

**Recommendation:** KEEP Celery - Your multi-agent system needs Celery's features (Beat scheduler for cron jobs, priority queues, mature ecosystem). Performance difference is negligible for your use case.

Sources:
- [Choosing The Right Python Task Queue](https://judoscale.com/blog/choose-python-task-queue)
- [Exploring Python Task Queue Libraries with Load Test](https://stevenyue.com/blogs/exploring-python-task-queue-libraries-with-load-test)

---

### Caching / Message Broker

**Research Finding:** Dragonfly offers 25x more throughput and 30% less memory than Redis, with full Redis API compatibility. Valkey (Redis fork) achieved 1.19M RPS (230% increase over previous version) and is BSD-3 licensed. Both are drop-in replacements.

**Recommendation:** KEEP Redis for now, CONSIDER Valkey for cost optimization.

**Rationale:**
- Your current Redis 6.4.0 client works with Redis, Valkey, or Dragonfly (same API)
- Supabase/Upstash Redis is managed, reducing DevOps burden
- Migration to Valkey/Dragonfly can happen at infrastructure level without code changes

Sources:
- [Valkey vs Redis - Ultimate Comparison Guide 2025](https://www.dragonflydb.io/guides/valkey-vs-redis)
- [Redis 8.0 vs. Valkey 8.1: A Technical Comparison](https://www.dragonflydb.io/blog/redis-8-0-vs-valkey-8-1-a-technical-comparison)

---

## 3. Recommendations Summary

### Changes Required

| Component | Action | Priority | Effort |
|-----------|--------|----------|--------|
| Frontend (Next.js) | CREATE package.json, setup | Critical | 2-3 hours |
| Frontend Tests (Vitest) | SETUP with React Testing Library | High | 1-2 hours |
| E2E Tests (Playwright) | SETUP framework | High | 1-2 hours |
| **Backend Tests** | **WRITE comprehensive unit + integration tests** | **High** | **3-4 hours** |
| Pre-commit hooks | UPDATE ruff version in config | Low | 15 min |

### Backend Testing Breakdown

| Test Type | Files | Coverage Target |
|-----------|-------|-----------------|
| Unit: FastAPI endpoints | `test_main.py` | 100% |
| Unit: BaseAgent | `test_base_agent.py` | 90% |
| Unit: BaseIntegrationClient | `test_base_integration.py` | 85% |
| Integration: API | `test_health_api.py` | Full endpoint coverage |
| Integration: Celery | `test_agent_handoff.py` | Handoff workflow |
| Fixtures | `agent_fixtures.py`, `integration_fixtures.py` | Reusable mocks |

### No Changes Needed

| Component | Current | 2025 Best Practice | Status |
|-----------|---------|-------------------|--------|
| FastAPI | 0.123.10 | FastAPI | Already optimal |
| PostgreSQL | Supabase | PostgreSQL | Already optimal |
| pytest | 9.0.1 | pytest | Already optimal |
| Celery | 5.6.0 | Celery | Already optimal |
| Redis | 6.4.0 | Redis/Valkey | Keep (infra decision) |
| Ruff | 0.14.8 | Ruff | Already optimal |
| MyPy | 1.19.0 | MyPy | Already optimal |

---

## 4. Implementation Plan

### Phase 1: Frontend Setup (Critical)

**Files to create:**
1. `app/frontend/package.json` - Next.js 15.x, React 19, TypeScript 5.x
2. `app/frontend/tsconfig.json` - TypeScript configuration
3. `app/frontend/next.config.js` - Next.js configuration
4. `app/frontend/tailwind.config.ts` - Tailwind CSS setup
5. `app/frontend/postcss.config.js` - PostCSS for Tailwind
6. `app/frontend/.eslintrc.json` - ESLint configuration
7. `app/frontend/vitest.config.ts` - Vitest test configuration
8. `app/frontend/src/app/layout.tsx` - Root layout
9. `app/frontend/src/app/page.tsx` - Home page

### Phase 2: E2E Testing Setup (High Priority)

**Files to create:**
1. `playwright.config.ts` - Playwright configuration
2. `tests/e2e/health.spec.ts` - Basic health check test
3. Update `.github/workflows/ci.yml` - Add Playwright job

### Phase 3: Backend Testing (High Priority - Comprehensive)

**Current State:** 0 actual tests, only fixtures in conftest.py

**Files to create:**

**Unit Tests (src/ modules):**
1. `app/backend/__tests__/unit/test_main.py` - FastAPI app tests (health, root endpoints)
2. `app/backend/__tests__/unit/agents/test_base_agent.py` - BaseAgent abstract class tests
3. `app/backend/__tests__/unit/integrations/test_base_integration.py` - BaseIntegrationClient tests

**Integration Tests (API endpoints):**
4. `app/backend/__tests__/integration/test_health_api.py` - Health endpoint integration
5. `app/backend/__tests__/integration/test_agent_handoff.py` - Agent handoff via Celery

**Fixtures & Utilities:**
6. `app/backend/__tests__/fixtures/agent_fixtures.py` - Mock agents for testing
7. `app/backend/__tests__/fixtures/integration_fixtures.py` - Mock API responses

**Test Coverage Targets:**
- `src/main.py` - 100% (endpoints)
- `src/agents/base_agent.py` - 90% (core agent logic)
- `src/integrations/base.py` - 85% (HTTP client)
- Overall target: 80%+

### Phase 4: Pre-commit Hook Update (Low Priority)

**Files to update:**
1. `.pre-commit-config.yaml` - Update ruff-pre-commit from v0.1.6 to v0.7.0+

---

## 5. Estimated Total Effort

| Phase | Effort | Description |
|-------|--------|-------------|
| Frontend Setup | 2-3 hours | Create Next.js project with Vitest |
| E2E Setup | 1-2 hours | Configure Playwright |
| **Backend Tests** | **3-4 hours** | **Comprehensive unit + integration tests** |
| Pre-commit Update | 15 min | Update hook versions |
| **Total** | **6.5-9.5 hours** | Full implementation |

---

## 6. Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| Frontend setup complexity | Low | Standard Next.js setup, well-documented |
| Playwright CI integration | Low | GitHub Actions has native Playwright support |
| Pre-commit version mismatch | Low | Backward compatible update |

---

## 7. Rollback Plan

All changes are additive (new files) rather than modifications to existing code:
- Frontend: Delete `app/frontend/` contents and start over
- Playwright: Delete `playwright.config.ts` and `tests/e2e/`
- Pre-commit: Revert `.pre-commit-config.yaml` to previous version

---

## Approval Required

**Before implementing, please confirm:**

1. Do you want to proceed with the frontend setup (Next.js 15 + Vitest)?
2. Do you want to set up Playwright for E2E testing?
3. Do you want to update the pre-commit hooks?

Please respond with "yes, implement this plan" or specify which parts to implement.
