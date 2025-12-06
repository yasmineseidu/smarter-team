import redis.asyncio as redis
from config.settings import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)


async def get_redis():
    return redis_client


class RedisKeys:
    """Centralized Redis key prefixes for the application."""

    # Agent state
    AGENT_STATE = "agent:state:{agent_name}:{session_id}"
    AGENT_LOCK = "agent:lock:{agent_name}"

    # Task tracking
    TASK_STATUS = "task:status:{task_id}"
    TASK_RESULT = "task:result:{task_id}"

    # Rate limiting
    RATE_LIMIT = "ratelimit:{service}:{identifier}"

    # Caching
    CACHE_LEAD = "cache:lead:{lead_id}"
    CACHE_CLIENT = "cache:client:{client_id}"
    CACHE_INTEGRATION = "cache:integration:{service}:{key}"

    # Pub/Sub channels
    CHANNEL_AGENT_EVENTS = "channel:agent:events"
    CHANNEL_WEBHOOK_EVENTS = "channel:webhook:events"
    CHANNEL_HANDOFF = "channel:handoff:{from_agent}:{to_agent}"

    # Dead letter queue
    DLQ_FAILED_TASKS = "dlq:failed_tasks"
    DLQ_FAILED_WEBHOOKS = "dlq:failed_webhooks"
