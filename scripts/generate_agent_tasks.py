#!/usr/bin/env python3
"""
Generate implementation task files for all agent specifications.

This script reads all agent spec files and generates corresponding
task files in tasks/backend/pending/ with comprehensive checklists.
"""

import re
from pathlib import Path
from datetime import datetime


def extract_agent_metadata(spec_path: Path) -> dict:
    """Extract metadata from an agent specification file."""
    content = spec_path.read_text()

    # Extract agent name
    agent_name_match = re.search(r'\*\*Agent Name:\*\*\s+`([^`]+)`', content)
    agent_name = agent_name_match.group(1) if agent_name_match else spec_path.stem

    # Extract category
    category_match = re.search(r'\*\*Category:\*\*\s+(.+)', content)
    category = category_match.group(1).strip() if category_match else "Unknown"

    # Extract priority/phase
    priority_match = re.search(r'\*\*Priority:\*\*\s+(.+)', content)
    priority = priority_match.group(1).strip() if priority_match else "Phase 1"

    # Extract dependencies
    deps_match = re.search(r'\*\*Dependencies:\*\*\s+(.+)', content)
    dependencies = deps_match.group(1).strip() if deps_match else "None"

    # Extract tools (look for ### followed by tool name)
    tools = []
    tool_pattern = r'###\s+\d+\.\s+`([^`]+)`'
    tool_matches = re.finditer(tool_pattern, content)
    for match in tool_matches:
        tools.append(match.group(1))

    # Extract integrations (look for Integration: section or integration mentions)
    integrations = []
    integration_section = re.search(r'## Integration[s]?:?\s+([^\n]+)', content)
    if integration_section:
        integrations.append(integration_section.group(1).strip())

    # Also search for integration client classes
    integration_client_pattern = r'class\s+(\w+Client)\(BaseIntegrationClient\)'
    for match in re.finditer(integration_client_pattern, content):
        client_name = match.group(1).replace('Client', '')
        if client_name not in integrations:
            integrations.append(client_name)

    # Extract database tables
    tables = []
    table_pattern = r'###\s+`([^`]+)`\s+Table'
    table_matches = re.finditer(table_pattern, content)
    for match in table_matches:
        tables.append(match.group(1))

    # Also check for CREATE TABLE statements
    create_table_pattern = r'CREATE TABLE\s+([^\s(]+)'
    for match in re.finditer(create_table_pattern, content):
        table_name = match.group(1).strip()
        if table_name not in tables:
            tables.append(table_name)

    return {
        "agent_name": agent_name,
        "category": category,
        "priority": priority,
        "dependencies": dependencies,
        "tools": tools,
        "integrations": integrations,
        "tables": tables,
        "spec_filename": spec_path.name
    }


def generate_task_file(task_number: int, metadata: dict, output_dir: Path) -> Path:
    """Generate a task file from agent metadata."""
    agent_name = metadata["agent_name"]
    agent_slug = agent_name.replace("_", "-")

    # Create task filename
    task_filename = f"{task_number:03d}-implement-{agent_slug}.md"
    task_path = output_dir / task_filename

    # Generate human-readable agent name
    agent_title = agent_name.replace("_", " ").title()

    # Generate tools checklist
    tools_checklist = ""
    if metadata["tools"]:
        for tool in metadata["tools"]:
            tools_checklist += f"- [ ] Implement `{tool}()` tool\n"
    else:
        tools_checklist = "- [ ] Implement required tools (see spec)\n"

    # Generate integrations checklist
    integrations_checklist = ""
    if metadata["integrations"]:
        for integration in metadata["integrations"]:
            integrations_checklist += f"- [ ] Implement {integration} client integration\n"
            integrations_checklist += f"- [ ] Add error handling with retry logic for {integration}\n"
            integrations_checklist += f"- [ ] Add rate limiting for {integration}\n"
    else:
        integrations_checklist = "- [ ] No external integrations required\n"

    # Generate database checklist
    database_checklist = ""
    if metadata["tables"]:
        database_checklist += "- [ ] Create/verify database schema:\n"
        for table in metadata["tables"]:
            database_checklist += f"  - [ ] `{table}` table\n"
        database_checklist += "- [ ] Implement database operations (CRUD)\n"
        database_checklist += "- [ ] Add indexes for performance\n"
    else:
        database_checklist = "- [ ] Verify database schema (uses existing tables)\n"
        database_checklist += "- [ ] Implement database operations\n"

    # Generate task file content
    content = f"""# Task: Implement {agent_title} Agent

**Status:** Pending
**Domain:** backend
**Source:** specs/agents/{metadata["spec_filename"]}
**Created:** {datetime.now().strftime("%Y-%m-%d")}

## Summary

Implement the {agent_title} Agent with all tools, tests, and integrations as specified in the production spec.

## Agent Details

**Category:** {metadata["category"]}
**Phase:** {metadata["priority"]}
**Dependencies:** {metadata["dependencies"]}

## Files to Create/Modify

- [ ] `app/backend/src/agents/{agent_name}/__init__.py`
- [ ] `app/backend/src/agents/{agent_name}/agent.py`
- [ ] `app/backend/src/agents/{agent_name}/tools.py`
- [ ] `app/backend/__tests__/unit/agents/test_{agent_name}_agent.py`
- [ ] `app/backend/__tests__/integration/test_{agent_name}_integration.py`
- [ ] `app/backend/__tests__/fixtures/{agent_name}_fixtures.py`

## Implementation Checklist

### Phase 1: Agent Class Setup
- [ ] Create agent directory structure
- [ ] Implement `{agent_title.replace(" ", "")}Agent` class extending BaseAgent
- [ ] Define `system_prompt` property
- [ ] Implement `process_task()` method with task routing
- [ ] Register all tools in `_register_tools()`

### Phase 2: Tool Implementation
{tools_checklist}

### Phase 3: Integration
{integrations_checklist}

### Phase 4: Database
{database_checklist}

### Phase 5: Testing
- [ ] Write unit tests for agent class initialization
- [ ] Write unit tests for each tool (>90% coverage target)
- [ ] Write integration tests for complete workflows
- [ ] Create comprehensive test fixtures
- [ ] Mock external API calls appropriately
- [ ] Run `make test` - ensure all pass

### Phase 6: Quality Gates
- [ ] Run `make lint` - no errors
- [ ] Run `make typecheck` - no errors
- [ ] Run `make format-check` - properly formatted
- [ ] Run `make test` - >85% coverage for agent, >90% for tools
- [ ] Verify all acceptance criteria met (see spec)
- [ ] Test error handling for all failure scenarios
- [ ] Verify logging is structured and complete

## Verification Commands

```bash
# Run tests
cd app/backend
make test

# Check coverage for this agent
pytest --cov=src/agents/{agent_name} --cov-report=term-missing

# Run specific agent tests
pytest __tests__/unit/agents/test_{agent_name}_agent.py -v
pytest __tests__/integration/test_{agent_name}_integration.py -v

# Quality checks
make check
```

## Acceptance Criteria

All criteria from `specs/agents/{metadata["spec_filename"]}` must be met:

- [ ] All tools implemented and tested
- [ ] Error handling matrix covered
- [ ] Performance targets met
- [ ] Database schema created/updated
- [ ] Integration clients working with proper error handling
- [ ] >85% test coverage for agent code
- [ ] >90% test coverage for tools
- [ ] All quality gates pass (lint, typecheck, format)
- [ ] Structured logging implemented throughout
- [ ] Agent handoffs properly configured (if applicable)

## Notes

- See full specification in `specs/agents/{metadata["spec_filename"]}` for:
  - Detailed tool specifications with parameters and return types
  - Error handling matrix with all scenarios
  - Performance requirements and targets
  - Multi-agent handoff patterns (if applicable)
  - Security considerations
  - Monitoring and alerting requirements

- Follow BaseAgent pattern from `/app/backend/src/agents/base_agent.py`
- Use BaseIntegrationClient for all external APIs
- Implement async/await for all I/O operations
- Use structured logging via `get_agent_logger()`
- Add type hints for all functions and methods
- Follow project conventions in `CLAUDE.md`

## Related Tasks

This task may depend on or be related to other agent implementations. Check the agent dependencies listed above and coordinate accordingly.

---

**Task created by automated task generation script**
**Next available task number: {task_number + 1}**
"""

    # Write task file
    task_path.write_text(content)
    return task_path


def main():
    """Generate all agent task files."""
    # Setup paths
    project_root = Path("/Users/yasmineseidu/Desktop/Coding/smarter-team")
    specs_dir = project_root / "specs" / "agents"
    tasks_dir = project_root / "tasks" / "backend" / "pending"

    # Ensure tasks directory exists
    tasks_dir.mkdir(parents=True, exist_ok=True)

    # Get all spec files
    spec_files = sorted(specs_dir.glob("*.md"))

    print(f"Found {len(spec_files)} agent specifications")
    print(f"Generating task files in {tasks_dir}\n")

    # Starting task number
    task_number = 100

    generated_tasks = []

    # Process each spec file
    for spec_file in spec_files:
        print(f"Processing {spec_file.name}...")

        # Extract metadata
        metadata = extract_agent_metadata(spec_file)

        # Generate task file
        task_path = generate_task_file(task_number, metadata, tasks_dir)

        generated_tasks.append({
            "number": task_number,
            "path": task_path,
            "agent": metadata["agent_name"],
            "spec": spec_file.name
        })

        task_number += 1

    # Print summary
    print(f"\n{'='*60}")
    print(f"Successfully generated {len(generated_tasks)} task files!")
    print(f"{'='*60}\n")

    print("First 5 tasks:")
    for task in generated_tasks[:5]:
        print(f"  [{task['number']}] {task['agent']} ({task['spec']})")

    print("\nLast 5 tasks:")
    for task in generated_tasks[-5:]:
        print(f"  [{task['number']}] {task['agent']} ({task['spec']})")

    print(f"\nNext available task number: {task_number}")
    print(f"All tasks saved to: {tasks_dir}")


if __name__ == "__main__":
    main()
