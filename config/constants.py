# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Timeouts
DEFAULT_TIMEOUT = 30
AGENT_TASK_TIMEOUT = 600  # 10 minutes
WEBHOOK_TIMEOUT = 30

# Lead Scoring
LEAD_SCORE_THRESHOLD_HIGH = 80
LEAD_SCORE_THRESHOLD_MEDIUM = 50
LEAD_SCORE_THRESHOLD_LOW = 20

# Agent Handoff
MAX_HANDOFF_DEPTH = 5  # Prevent infinite agent loops
HANDOFF_TIMEOUT = 300  # 5 minutes

# Retry Configuration
MAX_RETRIES = 3
RETRY_DELAY_BASE = 5  # seconds
RETRY_DELAY_MAX = 300  # 5 minutes

# Rate Limiting
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 100

# Agent Names
AGENT_NAMES = [
    "lead_generation",
    "sales",
    "project_manager",
    "developer",
    "marketing",
    "support",
    "finance",
    "research",
]

# Task Priorities
PRIORITY_CRITICAL = 0
PRIORITY_HIGH = 1
PRIORITY_MEDIUM = 2
PRIORITY_LOW = 3

# Webhook Event Types
WEBHOOK_EVENTS = {
    "instantly": [
        "email.replied",
        "email.bounced",
        "email.unsubscribed",
        "campaign.completed",
    ],
    "stripe": [
        "payment_intent.succeeded",
        "payment_intent.failed",
        "invoice.paid",
        "invoice.payment_failed",
        "customer.subscription.created",
        "customer.subscription.deleted",
    ],
    "gohighlevel": [
        "contact.created",
        "contact.updated",
        "opportunity.created",
        "opportunity.status_changed",
    ],
    "calcom": [
        "booking.created",
        "booking.cancelled",
        "booking.rescheduled",
    ],
    "clickup": [
        "task.created",
        "task.updated",
        "task.status_changed",
        "task.completed",
    ],
}
