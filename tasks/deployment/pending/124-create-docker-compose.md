# Task 223: Create docker-compose.yml for Local Testing

**Status:** Pending
**Domain:** deployment
**Source:** Coolify deployment requirements
**Created:** 2025-12-06

## Summary

Create a comprehensive docker-compose.yml file that orchestrates all services (FastAPI, Celery worker, Celery beat, Redis, Next.js frontend) for local testing before Coolify deployment. This validates the entire stack works together.

## Prerequisites

- [ ] Task 221 completed (FastAPI Dockerfile)
- [ ] Task 222 completed (Next.js Dockerfile)
- [ ] Docker and Docker Compose installed
- [ ] Environment variables configured

## Files to Create/Modify

- [ ] `docker-compose.yml` (root directory)
- [ ] `docker-compose.override.yml` (for local development overrides)
- [ ] `.env.docker` (Docker-specific environment variables)

## Implementation Checklist

### Phase 1: Create Main docker-compose.yml
- [ ] Define all services (backend, worker, beat, redis, frontend)
- [ ] Configure service dependencies
- [ ] Set up health checks for all services
- [ ] Configure networks for service communication
- [ ] Set up volumes for persistent data

### Phase 2: Create Development Override
- [ ] Create `docker-compose.override.yml` for hot-reload
- [ ] Mount source code as volumes
- [ ] Expose debugging ports
- [ ] Add development tools

### Phase 3: Create Environment Configuration
- [ ] Create `.env.docker` with Docker-specific values
- [ ] Document required environment variables
- [ ] Set up service URLs (internal Docker network)

## Configuration Details

### docker-compose.yml Content

```yaml
version: '3.9'

services:
  # Redis - Message broker and cache
  redis:
    image: redis:7-alpine
    container_name: smarter-team-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - smarter-team-network
    restart: unless-stopped

  # FastAPI Backend
  backend:
    build:
      context: ./app/backend
      dockerfile: Dockerfile
    container_name: smarter-team-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - smarter-team-network
    restart: unless-stopped

  # Celery Worker
  celery-worker:
    build:
      context: ./app/backend
      dockerfile: Dockerfile
    container_name: smarter-team-worker
    command: celery -A src.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    depends_on:
      redis:
        condition: service_healthy
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "celery -A src.celery_app inspect ping -d celery@$$HOSTNAME"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    networks:
      - smarter-team-network
    restart: unless-stopped

  # Celery Beat (Scheduler)
  celery-beat:
    build:
      context: ./app/backend
      dockerfile: Dockerfile
    container_name: smarter-team-beat
    command: celery -A src.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    depends_on:
      redis:
        condition: service_healthy
      backend:
        condition: service_healthy
    networks:
      - smarter-team-network
    restart: unless-stopped

  # Next.js Frontend
  frontend:
    build:
      context: ./app/frontend
      dockerfile: Dockerfile
    container_name: smarter-team-frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
      - NODE_ENV=production
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "node -e \"require('http').get('http://localhost:3000/api/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})\""]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - smarter-team-network
    restart: unless-stopped

networks:
  smarter-team-network:
    driver: bridge

volumes:
  redis-data:
    driver: local
```

### docker-compose.override.yml (Development)

```yaml
version: '3.9'

services:
  # Backend with hot-reload
  backend:
    build:
      context: ./app/backend
      dockerfile: Dockerfile.dev
    volumes:
      - ./app/backend/src:/app/src:ro
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

  # Worker with auto-restart
  celery-worker:
    volumes:
      - ./app/backend/src:/app/src:ro
    environment:
      - ENVIRONMENT=development
    command: watchmedo auto-restart --directory=/app/src --pattern="*.py" --recursive -- celery -A src.celery_app worker --loglevel=debug

  # Frontend with hot-reload
  frontend:
    build:
      context: ./app/frontend
      dockerfile: Dockerfile.dev
    volumes:
      - ./app/frontend/app:/app/app:ro
      - ./app/frontend/components:/app/components:ro
    environment:
      - NODE_ENV=development
    command: npm run dev

  # Redis Commander (GUI for Redis)
  redis-commander:
    image: rediscommander/redis-commander:latest
    container_name: redis-commander
    ports:
      - "8081:8081"
    environment:
      - REDIS_HOSTS=local:redis:6379
    networks:
      - smarter-team-network
```

### .env.docker Content

```bash
# Database (Supabase - external)
DATABASE_URL=postgresql://user:password@host:port/database

# Redis (internal Docker network)
REDIS_URL=redis://redis:6379/0

# API Keys
ANTHROPIC_API_KEY=sk-ant-...
SECRET_KEY=your-secret-key-here

# Service Configuration
ENVIRONMENT=production
DEBUG=false
UVICORN_WORKERS=4
CELERY_WORKER_CONCURRENCY=4

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Verification

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f celery-worker

# Test backend health
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000

# Test Redis
docker-compose exec redis redis-cli ping

# Test Celery worker
docker-compose exec celery-worker celery -A src.celery_app inspect active

# Test Celery beat
docker-compose exec celery-beat celery -A src.celery_app inspect scheduled

# Run tests in backend container
docker-compose exec backend pytest

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild and restart
docker-compose up -d --build
```

## Service Communication

**Internal Docker Network:**
- Backend: `http://backend:8000`
- Frontend: `http://frontend:3000`
- Redis: `redis://redis:6379/0`

**External Access (host machine):**
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- Redis: `redis://localhost:6379/0`
- Redis Commander (dev): `http://localhost:8081`

## Notes

- **Health checks** ensure services start in correct order
- **Depends_on with conditions** prevent startup race conditions
- **Named volumes** persist Redis data across restarts
- **Bridge network** enables service discovery by name
- **Restart policies** ensure services recover from failures
- **Override file** automatically merged in development

## Development Workflow

```bash
# Development (with hot-reload)
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

# Production (no hot-reload)
docker-compose up -d

# View resource usage
docker stats

# Clean up everything
docker-compose down -v --remove-orphans
docker system prune -f
```

## Troubleshooting

**Services fail to start:**
```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs backend

# Restart specific service
docker-compose restart backend
```

**Cannot connect to backend from frontend:**
- Verify services are on same network
- Use service name, not localhost: `http://backend:8000`
- Check backend health: `docker-compose exec backend curl localhost:8000/health`

**Celery worker not processing tasks:**
```bash
# Check worker is running
docker-compose exec celery-worker celery -A src.celery_app inspect active

# Check Redis connection
docker-compose exec celery-worker celery -A src.celery_app inspect ping

# Restart worker
docker-compose restart celery-worker
```

**Database connection fails:**
- Verify DATABASE_URL is correct
- Check Supabase firewall allows Docker host IP
- Test connection: `docker-compose exec backend python -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); print(engine.connect())"`

## Coolify Migration Notes

This docker-compose setup closely mirrors Coolify deployment:
1. Same service definitions
2. Same health checks
3. Same networking pattern
4. Validates entire stack works together

**Differences in Coolify:**
- Coolify manages service orchestration
- Built-in SSL termination
- Automatic service discovery
- Centralized logging
- GUI-based configuration
