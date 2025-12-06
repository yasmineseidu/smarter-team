# Task 232: Set Up GitHub Actions for Automated Deployments

**Status:** Pending
**Domain:** deployment
**Source:** Coolify deployment requirements
**Created:** 2025-12-06

## Summary

Configure GitHub Actions to run tests, build Docker images, and trigger Coolify deployments automatically on push to main and develop branches.

## Prerequisites

- [ ] Task 226 completed (Git repository connected)
- [ ] Coolify webhook URL obtained
- [ ] GitHub repository secrets configured

## Implementation Checklist

- [ ] Create deployment workflow
- [ ] Configure branch-specific deployments
- [ ] Set up deployment notifications
- [ ] Test automated deployment
- [ ] Configure rollback workflow

## Configuration Details

### Create `.github/workflows/deploy.yml`

```yaml
name: Deploy to Coolify

on:
  push:
    branches:
      - main
      - develop
  workflow_dispatch:

env:
  DOCKER_BUILDKIT: 1
  COMPOSE_DOCKER_CLI_BUILD: 1

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Run backend tests
        run: |
          cd app/backend
          pip install -e ".[dev]"
          pytest --cov=src

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Run frontend tests
        run: |
          cd app/frontend
          npm ci
          npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Determine environment
        id: env
        run: |
          if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            echo "environment=production" >> $GITHUB_OUTPUT
            echo "webhook_url=${{ secrets.COOLIFY_WEBHOOK_PROD }}" >> $GITHUB_OUTPUT
          else
            echo "environment=staging" >> $GITHUB_OUTPUT
            echo "webhook_url=${{ secrets.COOLIFY_WEBHOOK_STAGING }}" >> $GITHUB_OUTPUT
          fi

      - name: Trigger Coolify deployment
        run: |
          curl -X POST "${{ steps.env.outputs.webhook_url }}" \
            -H "Authorization: Bearer ${{ secrets.COOLIFY_TOKEN }}" \
            -H "Content-Type: application/json"

      - name: Wait for deployment
        run: sleep 120

      - name: Health check
        run: |
          if [[ "${{ steps.env.outputs.environment }}" == "production" ]]; then
            curl -f https://api.smarter-team.com/health
            curl -f https://smarter-team.com/api/health
          else
            curl -f https://staging-api.smarter-team.com/health
            curl -f https://staging.smarter-team.com/api/health
          fi

      - name: Notify deployment success
        if: success()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Deployment to ${{ steps.env.outputs.environment }} succeeded!'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}

      - name: Notify deployment failure
        if: failure()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Deployment to ${{ steps.env.outputs.environment }} failed!'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### GitHub Secrets Required

```bash
# In GitHub repository → Settings → Secrets and variables → Actions

COOLIFY_WEBHOOK_PROD=https://coolify.your-domain.com/webhooks/deploy/prod-id
COOLIFY_WEBHOOK_STAGING=https://coolify.your-domain.com/webhooks/deploy/staging-id
COOLIFY_TOKEN=your-coolify-api-token
SLACK_WEBHOOK=https://hooks.slack.com/services/... (optional)
```

## Verification

```bash
# Trigger deployment manually
gh workflow run deploy.yml

# Monitor workflow
gh run watch

# Check deployment status
gh run list --workflow=deploy.yml
```

## Notes

- **Tests first**: Deployment only if tests pass
- **Branch-specific**: Different webhooks for prod/staging
- **Health checks**: Verify deployment succeeded
- **Notifications**: Slack alerts for deploy status
