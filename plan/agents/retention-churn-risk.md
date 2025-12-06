# Churn Risk Detector Agent

## Category
Client Success & Retention

## Purpose
Identify at-risk clients

## Risk Signals
- Low engagement (not responding)
- Missed meetings
- Payment delays
- Negative survey responses
- Reduced communication
- Scope complaints

## Process
1. Monitor risk signals
2. Calculate churn risk score
3. Alert on high risk
4. Trigger intervention

## Database Tables
- `churn_risk_scores`
- `risk_signals`

## Integrations
- Internal communication tracking
- Payment status
- Survey responses
- Meeting attendance

## Priority
Phase 5 - Retention & Growth

## Dependencies
- Project Management Agent (provides communication data)
- Payment Processing Agent (provides payment status)
- Satisfaction Survey Agent (provides survey scores)
- Meeting Management (provides attendance)

## Human-in-the-Loop
- High risk alerts require human intervention
- Retention strategies require human execution

## Risk Score Calculation

### Signal Weights
```
communication_drop = 25 points
  - No response in 5 days: +5
  - No response in 10 days: +15
  - No response in 14+ days: +25

payment_issues = 25 points
  - Invoice 7 days overdue: +10
  - Invoice 14 days overdue: +20
  - Invoice 30+ days overdue: +25

meeting_attendance = 20 points
  - 1 no-show: +5
  - 2 no-shows: +15
  - 3+ no-shows: +20

satisfaction_score = 20 points
  - Survey score 7-8: +5
  - Survey score 5-6: +15
  - Survey score 1-4: +20

scope_issues = 10 points
  - 1 scope complaint: +3
  - 2 scope complaints: +7
  - 3+ scope complaints: +10

total_risk_score = sum of all signals (max 100)
```

### Risk Levels
```
0-20: Low risk - Continue normal operations
21-40: Medium risk - Proactive check-in
41-60: High risk - Immediate intervention
61-80: Critical risk - Escalate to owner
81-100: Severe risk - Emergency intervention
```

## Alert Format
```
🚨 CHURN RISK ALERT

Client: {{client_name}}
Project: {{project_name}}
Risk Score: {{score}}/100
Risk Level: {{level}}

RISK SIGNALS DETECTED
{{for signal in signals}}
- {{signal.type}}: {{signal.description}} (+{{signal.points}} pts)
{{/for}}

RECOMMENDED ACTIONS
1. {{action_1}}
2. {{action_2}}
3. {{action_3}}

HISTORY
- Last communication: {{last_comm_date}}
- Last payment: {{last_payment_date}}
- Survey scores: {{survey_history}}
```

## Intervention Strategies

### Medium Risk
- Personal check-in email
- Offer support call
- Review project progress together

### High Risk
- Phone call from owner
- Address specific concerns
- Offer adjustment/discount if appropriate

### Critical Risk
- Emergency call
- Exec-level involvement
- Consider proactive offboarding if relationship unsalvageable

## Cron Schedule
- Daily at 11:00 AM - Calculate client churn risk scores
