#!/usr/bin/env python3
"""
Task Reorganization Script
Renames task files according to priority and dependency-based ordering.
"""

import os
import shutil
from pathlib import Path

# Base directories
BACKEND_PENDING = Path("/Users/yasmineseidu/Desktop/Coding/smarter-team/tasks/backend/pending")
DEPLOYMENT_PENDING = Path("/Users/yasmineseidu/Desktop/Coding/smarter-team/tasks/deployment/pending")
TEMP_DIR = Path("/Users/yasmineseidu/Desktop/Coding/smarter-team/tasks/_temp_reorganize")

# Mapping: old_filename -> new_number
TASK_MAPPING = {
    # PHASE 1: Foundation (001-015)
    # Critical Integrations
    "214-implement-stripe-client.md": "001",
    "193-implement-instantly-client.md": "002",
    "201-implement-apify-client.md": "003",
    "200-implement-reoon-client.md": "004",
    "176-implement-perplexity-client.md": "005",
    "189-implement-firecrawl-client.md": "006",

    # Research Agents (Entry Points)
    "154-implement-research-niche-research.md": "007",
    "155-implement-research-persona-research.md": "008",
    "150-implement-research-company-research.md": "009",
    "152-implement-research-lead-research.md": "010",

    # Foundation Agents
    "120-implement-leadgen-lead-list-builder.md": "011",
    "119-implement-leadgen-email-verification.md": "012",
    "117-implement-leadgen-data-validation.md": "013",
    "118-implement-leadgen-duplicate-detection.md": "014",
    "121-implement-leadgen-waterfall-enrichment.md": "015",

    # PHASE 2: Campaign Pipeline (016-030)
    "102-implement-campaign-copywriting.md": "016",
    "101-implement-campaign-campaign-creation.md": "017",
    "106-implement-campaign-send-agent.md": "018",
    "105-implement-campaign-personalization.md": "019",
    "100-implement-campaign-ab-testing.md": "020",
    "107-implement-campaign-send-time-optimization.md": "021",
    "103-implement-campaign-deliverability-monitor.md": "022",
    "110-implement-campaign-warmup-monitor.md": "023",
    "156-implement-response-email-handler.md": "024",
    "159-implement-response-knowledge-base.md": "025",
    "157-implement-response-conversation-intelligence.md": "026",
    "158-implement-response-check-ins.md": "027",
    "160-implement-response-faq-evolution.md": "028",
    "207-implement-gmail-client.md": "029",
    "212-implement-calcom-client.md": "030",

    # PHASE 3: Meeting Management (031-042)
    "213-implement-fathom-client.md": "031",
    "181-implement-gamma-client.md": "032",
    "208-implement-google-calendar-client.md": "033",
    "125-implement-meeting-lifecycle-orchestrator.md": "034",
    "130-implement-meeting-scheduler.md": "035",
    "129-implement-meeting-reminders.md": "036",
    "128-implement-meeting-prep.md": "037",
    "124-implement-meeting-fathom-integration.md": "038",
    "127-implement-meeting-notes-manager.md": "039",
    "131-implement-meeting-task-automation.md": "040",
    "126-implement-meeting-no-show-handler.md": "041",
    "132-implement-meeting-sales-call-analytics.md": "042",

    # PHASE 4: Proposal & Payment (043-053)
    "216-implement-pandadoc-client.md": "043",
    "215-implement-quickbooks-client.md": "044",
    "149-implement-proposal-transcript-processor.md": "045",
    "146-implement-proposal-creation.md": "046",
    "147-implement-proposal-negotiation.md": "047",
    "148-implement-proposal-tracking.md": "048",
    "145-implement-proposal-call-improvement.md": "049",
    "142-implement-payment-invoice-generation.md": "050",
    "143-implement-payment-processing.md": "051",
    "141-implement-payment-collection.md": "052",
    "144-implement-payment-revenue-tracking.md": "053",

    # PHASE 5: Onboarding & Delivery (054-065)
    "204-implement-clickup-client.md": "054",
    "203-implement-notion-client.md": "055",
    "202-implement-airtable-client.md": "056",
    "139-implement-onboarding-orchestrator.md": "057",
    "138-implement-onboarding-internal-setup.md": "058",
    "140-implement-onboarding-stuck-detector.md": "059",
    "114-implement-delivery-project-management.md": "060",
    "112-implement-delivery-client-update.md": "061",
    "111-implement-delivery-approval-workflow.md": "062",
    "116-implement-delivery-scope-tracker.md": "063",
    "113-implement-delivery-delay-handler.md": "064",
    "115-implement-delivery-qa.md": "065",

    # PHASE 6: Retention & Growth (066-078)
    "162-implement-retention-churn-risk.md": "066",
    "165-implement-retention-upsell-detector.md": "067",
    "163-implement-retention-satisfaction-surveys.md": "068",
    "164-implement-retention-testimonial-requests.md": "069",
    "161-implement-retention-contract-renewal.md": "070",
    "133-implement-offboarding-client-offboarding.md": "071",
    "134-implement-offboarding-knowledge-transfer.md": "072",
    "136-implement-offboarding-referral-request.md": "073",
    "135-implement-offboarding-long-term-nurture.md": "074",
    "137-implement-offboarding-reactivation.md": "075",
    "153-implement-research-intent-signals.md": "076",
    "151-implement-research-competitive-intelligence.md": "077",
    "122-implement-leadgen-progressive-enrichment.md": "078",

    # PHASE 7: Advanced Features (079-100)
    "104-implement-campaign-linkedin-automation.md": "079",
    "195-implement-heyreach-client.md": "080",
    "108-implement-campaign-sms-agent.md": "081",
    "109-implement-campaign-voice-message.md": "082",
    "194-implement-autobound-client.md": "083",
    "123-implement-leadgen-technographic-data.md": "084",
    "196-implement-icypeas-client.md": "085",
    "197-implement-findymail-client.md": "086",
    "198-implement-anymailfinder-client.md": "087",
    "199-implement-tomba-client.md": "088",
    "177-implement-elevenlabs-client.md": "089",
    "178-implement-retell-client.md": "090",
    "179-implement-fal-client.md": "091",
    "180-implement-replicate-client.md": "092",
    "182-implement-openai-client.md": "093",
    "183-implement-gemini-client.md": "094",
    "184-implement-openrouter-client.md": "095",
    "185-implement-deepseek-client.md": "096",
    "186-implement-serper-client.md": "097",
    "187-implement-exa-client.md": "098",
    "188-implement-brave-search-client.md": "099",
    "190-implement-newsapi-client.md": "100",

    # PHASE 8: System Administration (101-115)
    "167-implement-system-database-manager.md": "101",
    "166-implement-system-api-rate-limit-manager.md": "102",
    "168-implement-system-error-monitor.md": "103",
    "169-implement-system-health-check.md": "104",
    "170-implement-system-audit-log.md": "105",
    "171-implement-system-learning-feedback.md": "106",
    "172-implement-system-knowledge-base-manager.md": "107",
    "173-implement-system-response-outcome-tracker.md": "108",
    "174-implement-system-agent-performance-analyst.md": "109",
    "175-implement-system-correction-approval.md": "110",
    "191-implement-reddit-client.md": "111",
    "192-implement-kuration-client.md": "112",
    "217-implement-signaturely-client.md": "113",
    "210-implement-google-drive-client.md": "114",
    "211-implement-google-sheets-client.md": "115",

    # PHASE 9: Memory & Advanced AI (116-121)
    "209-implement-google-tasks-client.md": "116",
    "205-implement-todoist-client.md": "117",
    "206-implement-gohighlevel-client.md": "118",
    "218-implement-pinecone-client.md": "119",
    "219-implement-zep-client.md": "120",
    "220-implement-rube-mcp-client.md": "121",
}

DEPLOYMENT_MAPPING = {
    # PHASE 10: Deployment (122-140)
    "task-221-create-fastapi-dockerfile.md": "122",
    "task-222-create-nextjs-dockerfile.md": "123",
    "task-223-create-docker-compose.md": "124",
    "task-224-setup-coolify-project.md": "125",
    "task-225-configure-environment-variables.md": "126",
    "task-226-setup-git-repository.md": "127",
    "task-227-configure-build-deployment-settings.md": "128",
    "task-228-configure-fastapi-service.md": "129",
    "task-229-configure-celery-services.md": "130",
    "task-230-configure-redis-service.md": "131",
    "task-231-configure-nextjs-frontend.md": "132",
    "task-232-setup-github-actions-deployment.md": "133",
    "task-233-configure-deployment-webhooks.md": "134",
    "task-234-setup-staging-production-environments.md": "135",
    "task-235-configure-health-check-endpoints.md": "136",
    "task-236-setup-logging-monitoring.md": "137",
    "task-237-configure-alerts-notifications.md": "138",
    "task-238-configure-domain-ssl.md": "139",
    "task-239-configure-cors-security-headers.md": "140",
}


def reorganize_tasks():
    """Reorganize all task files according to new priority-based numbering."""

    # Create temp directory
    TEMP_DIR.mkdir(exist_ok=True)

    print("=" * 60)
    print("TASK REORGANIZATION SCRIPT")
    print("=" * 60)
    print()

    # Step 1: Move backend tasks to temp with new names
    print("Step 1: Renaming backend tasks...")
    renamed_count = 0
    missing_count = 0

    for old_name, new_number in TASK_MAPPING.items():
        old_path = BACKEND_PENDING / old_name

        if not old_path.exists():
            print(f"  ⚠️  Missing: {old_name}")
            missing_count += 1
            continue

        # Extract the suffix (everything after the number)
        suffix = "-".join(old_name.split("-")[1:])
        new_name = f"{new_number}-{suffix}"
        temp_path = TEMP_DIR / new_name

        shutil.copy2(old_path, temp_path)
        print(f"  ✓ {old_name} → {new_name}")
        renamed_count += 1

    print(f"\n  Backend tasks renamed: {renamed_count}")
    print(f"  Missing files: {missing_count}")

    # Step 2: Move deployment tasks to temp with new names
    print("\nStep 2: Renaming deployment tasks...")
    deployment_renamed = 0
    deployment_missing = 0

    for old_name, new_number in DEPLOYMENT_MAPPING.items():
        old_path = DEPLOYMENT_PENDING / old_name

        if not old_path.exists():
            print(f"  ⚠️  Missing: {old_name}")
            deployment_missing += 1
            continue

        # Extract the suffix (everything after task-XXX-)
        parts = old_name.replace("task-", "").split("-", 1)
        if len(parts) > 1:
            suffix = parts[1]
            new_name = f"{new_number}-{suffix}"
        else:
            new_name = f"{new_number}.md"

        temp_path = TEMP_DIR / new_name

        shutil.copy2(old_path, temp_path)
        print(f"  ✓ {old_name} → {new_name}")
        deployment_renamed += 1

    print(f"\n  Deployment tasks renamed: {deployment_renamed}")
    print(f"  Missing files: {deployment_missing}")

    # Step 3: Remove old files from backend
    print("\nStep 3: Removing old backend task files...")
    for old_name in TASK_MAPPING.keys():
        old_path = BACKEND_PENDING / old_name
        if old_path.exists():
            old_path.unlink()
            print(f"  ✓ Removed: {old_name}")

    # Step 4: Remove old files from deployment
    print("\nStep 4: Removing old deployment task files...")
    for old_name in DEPLOYMENT_MAPPING.keys():
        old_path = DEPLOYMENT_PENDING / old_name
        if old_path.exists():
            old_path.unlink()
            print(f"  ✓ Removed: {old_name}")

    # Step 5: Move renamed files from temp to final locations
    print("\nStep 5: Moving renamed files to final locations...")
    for temp_file in TEMP_DIR.glob("*.md"):
        new_number = int(temp_file.stem.split("-")[0])

        # Determine destination based on task number
        if new_number <= 121:
            dest_path = BACKEND_PENDING / temp_file.name
        else:
            dest_path = DEPLOYMENT_PENDING / temp_file.name

        shutil.move(str(temp_file), str(dest_path))
        print(f"  ✓ {temp_file.name} → {dest_path.parent.name}/{temp_file.name}")

    # Step 6: Clean up temp directory
    print("\nStep 6: Cleaning up...")
    TEMP_DIR.rmdir()
    print("  ✓ Temp directory removed")

    # Final summary
    print("\n" + "=" * 60)
    print("REORGANIZATION COMPLETE!")
    print("=" * 60)
    print(f"\nTotal tasks reorganized: {renamed_count + deployment_renamed}")
    print(f"Backend tasks: {renamed_count}")
    print(f"Deployment tasks: {deployment_renamed}")
    print(f"Missing files: {missing_count + deployment_missing}")
    print(f"\nNext available task number: 141")
    print("\nNew task structure:")
    print("  001-015: Foundation")
    print("  016-030: Campaign Pipeline")
    print("  031-042: Meeting Management")
    print("  043-053: Proposal & Payment")
    print("  054-065: Onboarding & Delivery")
    print("  066-078: Retention & Growth")
    print("  079-100: Advanced Features")
    print("  101-115: System Administration")
    print("  116-121: Memory & Advanced AI")
    print("  122-140: Deployment")
    print()


if __name__ == "__main__":
    try:
        reorganize_tasks()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
