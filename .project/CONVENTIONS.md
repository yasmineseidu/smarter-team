# Conventions

Coding and workflow conventions for Smarter Team.

## Python

### Style

- Python 3.11+ with full type hints
- Line length: 100 characters
- Quotes: Double quotes for strings
- Imports: isort ordering (stdlib, third-party, local)

### Naming

| Type | Convention | Example |
|------|------------|---------|
| Files | snake_case | `lead_generation_agent.py` |
| Classes | PascalCase | `LeadGenerationAgent` |
| Functions | snake_case | `qualify_lead` |
| Constants | SCREAMING_SNAKE | `MAX_RETRIES` |
| Variables | snake_case | `lead_score` |

### Async

All I/O operations must be async:

```python
# Good
async def fetch_lead(lead_id: str) -> Lead:
    return await db.get(Lead, lead_id)

# Bad
def fetch_lead(lead_id: str) -> Lead:
    return db.get(Lead, lead_id)  # Blocking!
```

## File Organization

### Agent Structure

```
agents/[agent_name]/
├── __init__.py      # Exports
├── agent.py         # Agent class
├── tools.py         # @tool functions
├── prompts.py       # System prompts
├── schemas.py       # Pydantic models
└── exceptions.py    # Custom exceptions
```

### Integration Structure

```
integrations/
├── __init__.py
├── base.py          # Base client class
├── instantly.py     # Instantly.ai client
├── stripe.py        # Stripe client
└── ...
```

## Git

### Branch Naming

```
feature/add-lead-gen-agent
fix/webhook-signature-validation
refactor/celery-task-structure
docs/api-documentation
```

### Commit Messages

```
feat: add lead generation agent tools
fix: correct webhook signature verification
refactor: extract base agent class
docs: add API endpoint documentation
test: add integration tests for sales agent
chore: update dependencies
```

## API

### Endpoint Naming

```
# Resources
GET    /api/leads           # List leads
POST   /api/leads           # Create lead
GET    /api/leads/{id}      # Get lead
PATCH  /api/leads/{id}      # Update lead
DELETE /api/leads/{id}      # Delete lead

# Actions
POST   /api/leads/{id}/qualify    # Qualify lead
POST   /api/agents/trigger        # Trigger agent

# Webhooks
POST   /webhooks/stripe           # Stripe webhook
POST   /webhooks/instantly        # Instantly webhook
```

### Response Format

```json
{
  "data": {...},
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 20
  }
}
```

### Error Format

```json
{
  "error": {
    "code": "LEAD_NOT_FOUND",
    "message": "Lead with ID xyz not found",
    "details": {...}
  }
}
```

## Task Management

### File Naming

```
tasks/backend/pending/
├── 001-implement-base-agent.md
├── 002-lead-gen-agent-tools.md
├── 003-instantly-integration.md
```

### Workflow

1. Pick from `pending/`
2. Move to `_in-progress/`
3. Complete work
4. Move to `_completed/`
5. Update `TASK-LOG.md`

## Documentation

### Docstrings

```python
async def qualify_lead(
    lead_id: str,
    criteria: QualificationCriteria,
) -> LeadScore:
    """
    Qualify a lead based on ICP criteria.

    Args:
        lead_id: Unique identifier for the lead
        criteria: Qualification criteria

    Returns:
        LeadScore with score and status

    Raises:
        LeadNotFoundError: If lead doesn't exist
    """
```

### Comments

- Explain WHY, not WHAT
- No commented-out code
- TODO format: `# TODO(username): description`
