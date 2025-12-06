# Scope Tracker Agent

## Category
Project Delivery

## Purpose
Detect and handle scope creep

## Process
1. Compare requests against original scope
2. Flag out-of-scope requests
3. Alert for review
4. Create change order if needed
5. Track scope changes

## Database Tables
- `scope_definitions`
- `scope_changes`
- `change_orders`

## Integrations
- Claude API (for request analysis)
- Email (for change order communication)
- Project Management systems

## Priority
Phase 4 - Client Delivery

## Dependencies
- Project Management Agent (provides request context)
- Proposal data (provides original scope)

## Human-in-the-Loop
- Scope change determination requires human judgment
- Change order terms require approval

## Scope Detection Logic

### Step 1: Parse Request
```
Extract from client communication:
- What they're asking for
- Context/reason
- Urgency level
```

### Step 2: Compare to Scope
```
Compare against:
- Original proposal deliverables
- Signed contract scope
- Any approved change orders
```

### Step 3: Classification
```
IN_SCOPE: Request matches original deliverables
MINOR_ADDITION: Small request, <2 hours work
SIGNIFICANT_ADDITION: Larger request, >2 hours
DIFFERENT_PROJECT: Entirely new scope
```

### Step 4: Response

**In Scope:**
```
Log request, proceed with work, no client communication needed
```

**Minor Addition:**
```
Flag for review, may include as goodwill
```

**Significant Addition:**
```
Generate change order, send to client for approval
```

**Different Project:**
```
Suggest separate project/proposal
```

## Change Order Template
```
Subject: Change Order: {{change_description}}

Hi {{first_name}},

Thanks for the request! I've reviewed it against our original scope.

REQUESTED CHANGE
{{change_description}}

ORIGINAL SCOPE
{{relevant_original_scope}}

IMPACT
- Additional time: {{hours}} hours
- Additional cost: ${{amount}}
- Timeline impact: {{timeline_impact}}

To proceed, please reply approving this change order, and I'll add it to the project.

Let me know if you have any questions!
```

## Scope Creep Metrics
- Track: Number of change requests per project
- Track: Revenue from change orders
- Track: Scope creep by client type
- Flag: Clients with >3 change requests

## Alerts
- Scope creep detected: Immediate alert to owner
- Change order approved: Update project timeline/budget
- Pattern detected: Weekly summary of scope issues
