# Quality Assurance Agent

## Category
Project Delivery

## Purpose
Review deliverables before client sees them

## Checklist
- Completeness check
- Quality standards met
- Branding correct
- Links working
- No placeholder content
- Spell check

## Process
1. Run QA checklist
2. Flag issues
3. Request fixes
4. Re-check
5. Approve for client delivery

## Database Tables
- `qa_checklists`
- `qa_results`

## Integrations
- Claude API (for content review)
- Link checker APIs
- Spell check APIs

## Priority
Phase 4 - Client Delivery

## Dependencies
- Project deliverables ready for review

## Human-in-the-Loop
- QA issues flagged for human fix
- Final approval before client delivery

## QA Checklist by Deliverable Type

### Website/Landing Page
- [ ] All pages load without errors
- [ ] All links work (no 404s)
- [ ] Images load and are optimized
- [ ] Mobile responsive
- [ ] Forms submit correctly
- [ ] Branding matches guidelines
- [ ] No placeholder text (Lorem ipsum)
- [ ] Contact info correct
- [ ] Legal pages present (privacy, terms)
- [ ] Analytics tracking installed
- [ ] SEO basics (titles, meta, alt tags)

### Document/Report
- [ ] Spell check passed
- [ ] Grammar check passed
- [ ] Branding consistent
- [ ] All sections complete
- [ ] Table of contents accurate
- [ ] Page numbers correct
- [ ] Images high quality
- [ ] Links work
- [ ] Client name/details correct

### Video Content
- [ ] Audio clear
- [ ] No visual glitches
- [ ] Branding present
- [ ] Call-to-action clear
- [ ] Captions accurate (if applicable)
- [ ] Correct duration
- [ ] Proper format/resolution

### Email Campaign
- [ ] Subject line present
- [ ] Personalization working
- [ ] Links work
- [ ] Unsubscribe present
- [ ] Preview text set
- [ ] Mobile renders correctly
- [ ] No spam triggers

## QA Result Format
```
QA REPORT: {{deliverable_name}}
Date: {{date}}
Reviewer: QA Agent

OVERALL STATUS: {{PASS/FAIL/NEEDS_FIXES}}

CHECKLIST RESULTS
✅ Completeness check - PASS
✅ Quality standards - PASS
❌ Links check - FAIL (2 broken links)
✅ Branding - PASS
❌ Placeholder content - FAIL (found on page 3)
✅ Spell check - PASS

ISSUES FOUND
1. Broken link: {{url}} on {{page}}
2. Placeholder text: "Lorem ipsum" on {{page}}

RECOMMENDATION
Fix {{count}} issues before client delivery.
```

## Automated Checks
- Link validation: Automated via API
- Spell check: Automated via API
- Placeholder detection: Automated regex
- Image loading: Automated via headless browser

## Manual Review Triggers
- QA fails automated checks
- High-value client
- First deliverable for client
- Complex deliverable type
