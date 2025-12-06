# Internal Setup Agent

## Category
Client Onboarding

## Purpose
Create internal project infrastructure

## Creates
- ClickUp project/workspace
- Google Drive folder structure
- Slack channel (if applicable)
- Airtable project record
- GHL record

## Process
1. Create all internal infrastructure
2. Set up folder templates
3. Configure project settings
4. Link all systems
5. Confirm setup complete

## Database Tables
- `project_infrastructure`
- `setup_logs`

## Integrations
- ClickUp API
- Google Drive API
- Slack API (optional)
- Airtable API
- GoHighLevel API

## Priority
Phase 4 - Client Delivery

## Dependencies
- Onboarding Orchestrator Agent (triggers setup)

## Human-in-the-Loop
- None (fully automated)
- Custom setup requirements flagged for manual handling

## Infrastructure Checklist

### ClickUp Project
- [ ] Create project from template
- [ ] Set project name: {{client_name}} - {{project_name}}
- [ ] Add due dates based on timeline
- [ ] Assign team members
- [ ] Configure automations

### Google Drive
- [ ] Create client folder: Clients/{{client_name}}
- [ ] Create subfolders:
  - /Contracts
  - /Deliverables
  - /Assets (from client)
  - /Meeting Notes
  - /Research
- [ ] Move signed contract to /Contracts
- [ ] Set sharing permissions

### Airtable
- [ ] Create project record
- [ ] Link to client record
- [ ] Set project status: Active
- [ ] Add timeline dates
- [ ] Link to ClickUp

### GoHighLevel (GHL)
- [ ] Create/update contact record
- [ ] Add client tag
- [ ] Update pipeline stage
- [ ] Link to opportunity

### Slack (Optional)
- [ ] Create client channel: #client-{{client_slug}}
- [ ] Invite team members
- [ ] Post welcome message with links

## Folder Structure Template
```
Clients/
└── {{client_name}}/
    ├── 01-Contracts/
    │   ├── proposal.pdf
    │   └── signed-contract.pdf
    ├── 02-Deliverables/
    │   ├── phase-1/
    │   ├── phase-2/
    │   └── final/
    ├── 03-Assets/
    │   ├── logos/
    │   ├── brand-guidelines/
    │   └── content/
    ├── 04-Meeting-Notes/
    │   └── kickoff-notes.md
    └── 05-Research/
        └── initial-research.md
```

## Setup Confirmation
```json
{
  "client_id": "uuid",
  "project_id": "uuid",
  "infrastructure": {
    "clickup_project_id": "123456",
    "drive_folder_id": "abc123",
    "airtable_record_id": "rec123",
    "ghl_contact_id": "ghl123",
    "slack_channel_id": "C123456"
  },
  "setup_completed_at": "2025-01-15T10:00:00Z",
  "checklist_complete": true
}
```
