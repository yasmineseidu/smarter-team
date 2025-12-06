# Task Reorganization Map

**Date:** 2025-12-06
**Reason:** Priority and dependency-based reorganization for logical implementation order

---

## Reorganization Summary

**Old Structure:** Tasks organized by category (agents, integrations, deployment)
**New Structure:** Tasks organized by business priority and dependencies

**Total Tasks:** 140 (consolidated from 144)
**Methodology:** Business flow (Research → Leads → Campaigns → Meetings → Closing → Delivery → Retention → Infrastructure)

---

## Task Number Mapping (Old → New)

### PHASE 1: Foundation (001-015)

#### Critical Integrations
```
176-implement-stripe-client.md              → 001-implement-stripe-client.md
193-implement-instantly-client.md           → 002-implement-instantly-client.md
201-implement-apify-client.md               → 003-implement-apify-client.md
200-implement-reoon-client.md               → 004-implement-reoon-client.md
176-implement-perplexity-client.md          → 005-implement-perplexity-client.md
189-implement-firecrawl-client.md           → 006-implement-firecrawl-client.md
```

#### Research Agents (Entry Points)
```
154-implement-research-niche-research.md              → 007-implement-research-niche-research.md
155-implement-research-persona-research.md            → 008-implement-research-persona-research.md
150-implement-research-company-research.md            → 009-implement-research-company-research.md
152-implement-research-lead-research.md               → 010-implement-research-lead-research.md
```

#### Foundation Agents
```
120-implement-leadgen-lead-list-builder.md            → 011-implement-leadgen-lead-list-builder.md
119-implement-leadgen-email-verification.md           → 012-implement-leadgen-email-verification.md
117-implement-leadgen-data-validation.md              → 013-implement-leadgen-data-validation.md
118-implement-leadgen-duplicate-detection.md          → 014-implement-leadgen-duplicate-detection.md
121-implement-leadgen-waterfall-enrichment.md         → 015-implement-leadgen-waterfall-enrichment.md
```

### PHASE 2: Campaign Pipeline (016-030)

#### Campaign Agents
```
102-implement-campaign-copywriting.md                 → 016-implement-campaign-copywriting.md
101-implement-campaign-campaign-creation.md           → 017-implement-campaign-campaign-creation.md
106-implement-campaign-send-agent.md                  → 018-implement-campaign-send-agent.md
105-implement-campaign-personalization.md             → 019-implement-campaign-personalization.md
100-implement-campaign-ab-testing.md                  → 020-implement-campaign-ab-testing.md
107-implement-campaign-send-time-optimization.md      → 021-implement-campaign-send-time-optimization.md
103-implement-campaign-deliverability-monitor.md      → 022-implement-campaign-deliverability-monitor.md
110-implement-campaign-warmup-monitor.md              → 023-implement-campaign-warmup-monitor.md
```

#### Response Management
```
156-implement-response-email-handler.md               → 024-implement-response-email-handler.md
159-implement-response-knowledge-base.md              → 025-implement-response-knowledge-base.md
157-implement-response-conversation-intelligence.md   → 026-implement-response-conversation-intelligence.md
158-implement-response-check-ins.md                   → 027-implement-response-check-ins.md
160-implement-response-faq-evolution.md               → 028-implement-response-faq-evolution.md
```

#### Additional Campaign Integrations
```
207-implement-gmail-client.md                         → 029-implement-gmail-client.md
213-implement-calcom-client.md                        → 030-implement-calcom-client.md
```

### PHASE 3: Meeting Management (031-042)

#### Critical Meeting Integrations
```
214-implement-fathom-client.md                        → 031-implement-fathom-client.md
181-implement-gamma-client.md                         → 032-implement-gamma-client.md
208-implement-google-calendar-client.md               → 033-implement-google-calendar-client.md
```

#### Meeting Agents (Master Coordinator First)
```
125-implement-meeting-lifecycle-orchestrator.md       → 034-implement-meeting-lifecycle-orchestrator.md
130-implement-meeting-scheduler.md                    → 035-implement-meeting-scheduler.md
129-implement-meeting-reminders.md                    → 036-implement-meeting-reminders.md
128-implement-meeting-prep.md                         → 037-implement-meeting-prep.md
124-implement-meeting-fathom-integration.md           → 038-implement-meeting-fathom-integration.md
127-implement-meeting-notes-manager.md                → 039-implement-meeting-notes-manager.md
131-implement-meeting-task-automation.md              → 040-implement-meeting-task-automation.md
126-implement-meeting-no-show-handler.md              → 041-implement-meeting-no-show-handler.md
132-implement-meeting-sales-call-analytics.md         → 042-implement-meeting-sales-call-analytics.md
```

### PHASE 4: Proposal & Payment (043-053)

#### Document Integrations
```
216-implement-pandadoc-client.md                      → 043-implement-pandadoc-client.md
215-implement-quickbooks-client.md                    → 044-implement-quickbooks-client.md
```

#### Proposal Agents
```
149-implement-proposal-transcript-processor.md        → 045-implement-proposal-transcript-processor.md
146-implement-proposal-creation.md                    → 046-implement-proposal-creation.md
147-implement-proposal-negotiation.md                 → 047-implement-proposal-negotiation.md
148-implement-proposal-tracking.md                    → 048-implement-proposal-tracking.md
145-implement-proposal-call-improvement.md            → 049-implement-proposal-call-improvement.md
```

#### Payment Agents
```
142-implement-payment-invoice-generation.md           → 050-implement-payment-invoice-generation.md
143-implement-payment-processing.md                   → 051-implement-payment-processing.md
141-implement-payment-collection.md                   → 052-implement-payment-collection.md
144-implement-payment-revenue-tracking.md             → 053-implement-payment-revenue-tracking.md
```

### PHASE 5: Onboarding & Delivery (054-065)

#### Project Management Integrations
```
204-implement-clickup-client.md                       → 054-implement-clickup-client.md
203-implement-notion-client.md                        → 055-implement-notion-client.md
202-implement-airtable-client.md                      → 056-implement-airtable-client.md
```

#### Onboarding Agents
```
139-implement-onboarding-orchestrator.md              → 057-implement-onboarding-orchestrator.md
138-implement-onboarding-internal-setup.md            → 058-implement-onboarding-internal-setup.md
140-implement-onboarding-stuck-detector.md            → 059-implement-onboarding-stuck-detector.md
```

#### Delivery Agents
```
114-implement-delivery-project-management.md          → 060-implement-delivery-project-management.md
112-implement-delivery-client-update.md               → 061-implement-delivery-client-update.md
111-implement-delivery-approval-workflow.md           → 062-implement-delivery-approval-workflow.md
116-implement-delivery-scope-tracker.md               → 063-implement-delivery-scope-tracker.md
113-implement-delivery-delay-handler.md               → 064-implement-delivery-delay-handler.md
115-implement-delivery-qa.md                          → 065-implement-delivery-qa.md
```

### PHASE 6: Retention & Growth (066-078)

#### Retention Agents
```
162-implement-retention-churn-risk.md                 → 066-implement-retention-churn-risk.md
165-implement-retention-upsell-detector.md            → 067-implement-retention-upsell-detector.md
163-implement-retention-satisfaction-surveys.md       → 068-implement-retention-satisfaction-surveys.md
164-implement-retention-testimonial-requests.md       → 069-implement-retention-testimonial-requests.md
161-implement-retention-contract-renewal.md           → 070-implement-retention-contract-renewal.md
```

#### Offboarding & Nurture
```
133-implement-offboarding-client-offboarding.md       → 071-implement-offboarding-client-offboarding.md
134-implement-offboarding-knowledge-transfer.md       → 072-implement-offboarding-knowledge-transfer.md
136-implement-offboarding-referral-request.md         → 073-implement-offboarding-referral-request.md
135-implement-offboarding-long-term-nurture.md        → 074-implement-offboarding-long-term-nurture.md
137-implement-offboarding-reactivation.md             → 075-implement-offboarding-reactivation.md
```

#### Additional Intelligence
```
153-implement-research-intent-signals.md              → 076-implement-research-intent-signals.md
151-implement-research-competitive-intelligence.md    → 077-implement-research-competitive-intelligence.md
122-implement-leadgen-progressive-enrichment.md       → 078-implement-leadgen-progressive-enrichment.md
```

### PHASE 7: Advanced Features (079-100)

#### Additional Campaign Features
```
104-implement-campaign-linkedin-automation.md         → 079-implement-campaign-linkedin-automation.md
195-implement-heyreach-client.md                      → 080-implement-heyreach-client.md
108-implement-campaign-sms-agent.md                   → 081-implement-campaign-sms-agent.md
109-implement-campaign-voice-message.md               → 082-implement-campaign-voice-message.md
194-implement-autobound-client.md                     → 083-implement-autobound-client.md
123-implement-leadgen-technographic-data.md           → 084-implement-leadgen-technographic-data.md
```

#### Email Finder Integrations
```
196-implement-icypeas-client.md                       → 085-implement-icypeas-client.md
197-implement-findymail-client.md                     → 086-implement-findymail-client.md
198-implement-anymailfinder-client.md                 → 087-implement-anymailfinder-client.md
199-implement-tomba-client.md                         → 088-implement-tomba-client.md
```

#### Additional AI Services
```
177-implement-elevenlabs-client.md                    → 089-implement-elevenlabs-client.md
178-implement-retell-client.md                        → 090-implement-retell-client.md
179-implement-fal-client.md                           → 091-implement-fal-client.md
180-implement-replicate-client.md                     → 092-implement-replicate-client.md
182-implement-openai-client.md                        → 093-implement-openai-client.md
183-implement-gemini-client.md                        → 094-implement-gemini-client.md
184-implement-openrouter-client.md                    → 095-implement-openrouter-client.md
185-implement-deepseek-client.md                      → 096-implement-deepseek-client.md
```

#### Additional Search Tools
```
186-implement-serper-client.md                        → 097-implement-serper-client.md
187-implement-exa-client.md                           → 098-implement-exa-client.md
188-implement-brave-search-client.md                  → 099-implement-brave-search-client.md
190-implement-newsapi-client.md                       → 100-implement-newsapi-client.md
```

### PHASE 8: System Administration (101-115)

#### System Agents
```
167-implement-system-database-manager.md              → 101-implement-system-database-manager.md
166-implement-system-api-rate-limit-manager.md        → 102-implement-system-api-rate-limit-manager.md
168-implement-system-error-monitor.md                 → 103-implement-system-error-monitor.md
169-implement-system-health-check.md                  → 104-implement-system-health-check.md
170-implement-system-audit-log.md                     → 105-implement-system-audit-log.md
171-implement-system-learning-feedback.md             → 106-implement-system-learning-feedback.md
172-implement-system-knowledge-base-manager.md        → 107-implement-system-knowledge-base-manager.md
173-implement-system-response-outcome-tracker.md      → 108-implement-system-response-outcome-tracker.md
174-implement-system-agent-performance-analyst.md     → 109-implement-system-agent-performance-analyst.md
175-implement-system-correction-approval.md           → 110-implement-system-correction-approval.md
```

#### Additional Integrations
```
191-implement-reddit-client.md                        → 111-implement-reddit-client.md
192-implement-kuration-client.md                      → 112-implement-kuration-client.md
217-implement-signaturely-client.md                   → 113-implement-signaturely-client.md
210-implement-google-drive-client.md                  → 114-implement-google-drive-client.md
211-implement-google-sheets-client.md                 → 115-implement-google-sheets-client.md
```

### PHASE 9: Memory & Advanced AI (116-121)

```
209-implement-google-tasks-client.md                  → 116-implement-google-tasks-client.md
205-implement-todoist-client.md                       → 117-implement-todoist-client.md
206-implement-gohighlevel-client.md                   → 118-implement-gohighlevel-client.md
218-implement-pinecone-client.md                      → 119-implement-pinecone-client.md
219-implement-zep-client.md                           → 120-implement-zep-client.md
220-implement-rube-mcp-client.md                      → 121-implement-rube-mcp-client.md
```

### PHASE 10: Deployment (122-140)

#### Docker Configuration
```
task-221-create-fastapi-dockerfile.md                 → 122-create-fastapi-dockerfile.md
task-222-create-nextjs-dockerfile.md                  → 123-create-nextjs-dockerfile.md
task-223-create-docker-compose.md                     → 124-create-docker-compose.md
```

#### Coolify Setup
```
task-224-setup-coolify-project.md                     → 125-setup-coolify-project.md
task-225-configure-environment-variables.md           → 126-configure-environment-variables.md
task-226-setup-git-repository.md                      → 127-setup-git-repository.md
task-227-configure-build-deployment-settings.md       → 128-configure-build-deployment-settings.md
```

#### Service Configuration
```
task-228-configure-fastapi-service.md                 → 129-configure-fastapi-service.md
task-229-configure-celery-services.md                 → 130-configure-celery-services.md
task-230-configure-redis-service.md                   → 131-configure-redis-service.md
task-231-configure-nextjs-frontend.md                 → 132-configure-nextjs-frontend.md
```

#### CI/CD Pipeline
```
task-232-setup-github-actions-deployment.md           → 133-setup-github-actions-deployment.md
task-233-configure-deployment-webhooks.md             → 134-configure-deployment-webhooks.md
task-234-setup-staging-production-environments.md     → 135-setup-staging-production-environments.md
```

#### Monitoring & Production
```
task-235-configure-health-check-endpoints.md          → 136-configure-health-check-endpoints.md
task-236-setup-logging-monitoring.md                  → 137-setup-logging-monitoring.md
task-237-configure-alerts-notifications.md            → 138-configure-alerts-notifications.md
task-238-configure-domain-ssl.md                      → 139-configure-domain-ssl.md
task-239-configure-cors-security-headers.md           → 140-configure-cors-security-headers.md
```

---

## Tasks Consolidated/Removed

The following duplicate or redundant tasks were consolidated:
- Stripe client appeared twice (kept one instance)
- Perplexity client appeared twice (kept one instance)
- Some integration tasks were merged based on similarity

**Total reduction:** 144 → 140 tasks

---

## Next Available Task Number

**141** - Use for next new task

---

## Reorganization Benefits

1. **Logical Implementation Order**: Build foundation before dependent systems
2. **Business Flow Alignment**: Tasks follow actual client lifecycle
3. **Testable Milestones**: Each phase produces a working subsystem
4. **Dependency Clarity**: Can't build meetings before campaigns
5. **Priority Focus**: Critical path (P0) tasks come first

---

## Migration Status

- [ ] Mapping file created
- [ ] Backend task files renamed
- [ ] Deployment task files renamed
- [ ] Documentation updated
- [ ] CLAUDE.md updated
- [ ] TASK-LOG.md preserved

**Date Completed:** TBD
