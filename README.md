# Smarter Team

An autonomous AI agent team that runs an AI agency from lead generation to client delivery.

## Overview

Smarter Team is a multi-agent system powered by the Claude Agent SDK that automates all aspects of running an AI agency:

- **Lead Generation Agent** - Find and qualify prospects
- **Sales Agent** - Handle inquiries, calls, and deal closing
- **Project Manager Agent** - Client onboarding and project coordination
- **Developer Agent** - Build AI solutions for clients
- **Marketing Agent** - Content creation and campaigns
- **Support Agent** - Client communication and issue resolution
- **Finance Agent** - Invoicing and payment tracking
- **Research Agent** - Market research and competitive analysis

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.11+ |
| Agent Framework | Claude Agent SDK |
| API | FastAPI |
| Task Queue | Celery + Redis |
| Database | Supabase (PostgreSQL) |
| Cache | Upstash Redis |
| Vector DB | Pinecone |
| Memory | Zep |
| Deployment | Coolify (Docker) |

## Setup

### Prerequisites

- Python 3.11+
- Node.js 20+ (for frontend)
- Docker & Docker Compose
- Redis (local or Upstash)
- PostgreSQL (local or Supabase)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/smarter-team.git
cd smarter-team

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys

# Backend setup
cd app/backend
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install -e ".[dev]"

# Frontend setup (optional - no UI in MVP)
cd ../frontend
npm install

# Install pre-commit hooks
cd ../..
pre-commit install
```

### Running Locally

```bash
# Terminal 1: Start FastAPI
cd app/backend
uvicorn src.main:app --reload --port 8000

# Terminal 2: Start Celery worker
celery -A config.celery worker --loglevel=info

# Terminal 3: Start Celery beat (scheduler)
celery -A config.celery beat --loglevel=info

# Terminal 4: (Optional) Start frontend
cd app/frontend
npm run dev
```

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Project Structure

```
smarter-team/
├── .claude/           # AI agent configuration
├── .project/          # Project documentation
├── app/
│   ├── backend/       # FastAPI + Agents
│   └── frontend/      # Next.js (optional)
├── config/            # All configuration
├── specs/             # Build specifications
├── tasks/             # Task tracking
├── planning/          # Architecture plans
└── docs/              # Documentation
```

## Development Workflow

1. **Read task** from `tasks/backend/pending/`
2. **Read spec** from `specs/`
3. **Implement** in `app/backend/src/`
4. **Test** with `pytest`
5. **Move task** to `tasks/backend/_completed/`
6. **Update** `tasks/TASK-LOG.md`

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Webhooks

| Service | Endpoint | Purpose |
|---------|----------|---------|
| Instantly.ai | `/webhooks/instantly` | Email replies |
| Stripe | `/webhooks/stripe` | Payments |
| GoHighLevel | `/webhooks/gohighlevel` | CRM events |
| Cal.com | `/webhooks/calcom` | Bookings |
| ClickUp | `/webhooks/clickup` | Tasks |

## Environment Variables

See `.env.example` for all required and optional environment variables.

## License

Proprietary - All rights reserved
