from celery import Celery
from config.settings import settings

celery_app = Celery(
    "smarter-team-worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.backend.src.tasks.lead_generation_tasks",
        "app.backend.src.tasks.sales_tasks",
        "app.backend.src.tasks.project_manager_tasks",
        "app.backend.src.tasks.developer_tasks",
        "app.backend.src.tasks.marketing_tasks",
        "app.backend.src.tasks.support_tasks",
        "app.backend.src.tasks.finance_tasks",
        "app.backend.src.tasks.research_tasks",
        "app.backend.src.tasks.orchestration_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    timezone="UTC",
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # Soft limit at 9 minutes
    worker_prefetch_multiplier=1,  # One task at a time for agents
    task_acks_late=True,  # Acknowledge after completion
    task_reject_on_worker_lost=True,  # Requeue if worker dies
)

celery_app.conf.beat_schedule = {
    # Lead Generation
    "daily-prospecting": {
        "task": "app.backend.src.tasks.lead_generation_tasks.daily_prospecting",
        "schedule": 32400,  # 9am daily (crontab preferred in production)
    },
    "hourly-campaign-monitor": {
        "task": "app.backend.src.tasks.lead_generation_tasks.monitor_campaigns",
        "schedule": 3600,  # Every hour
    },
    # Research
    "daily-industry-news": {
        "task": "app.backend.src.tasks.research_tasks.gather_industry_news",
        "schedule": 28800,  # Every 8 hours
    },
    # Finance
    "daily-invoice-check": {
        "task": "app.backend.src.tasks.finance_tasks.check_overdue_invoices",
        "schedule": 86400,  # Daily
    },
    # Support
    "daily-client-checkin": {
        "task": "app.backend.src.tasks.support_tasks.proactive_checkins",
        "schedule": 86400,  # Daily
    },
}
