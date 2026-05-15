# Agentic IT Firm MVP Workflow Design

## Goal

Build the first complete reusable workflow for the Agentic IT Firm MVP:

`Client Request -> Chief Orchestrator -> Research Department -> Coding Department -> QA Department -> Documentation Generation -> Revenue Packaging -> Human Approval -> Final Delivery`

The workflow must execute end to end, preserve state, support recovery, emit structured logs, and generate a packaged delivery folder under `D:\agentic services`.

## Scope

This MVP adds the missing reusable agents required by the workflow:

- Research Team Leader Agent
- Market Research Agent
- Technical Research Agent
- Revenue Packaging Agent

It reuses existing agents and systems already implemented:

- Chief Orchestrator
- Coding Department
- QA Department
- Documentation Specialist
- Human Approval System
- Shared and semantic memory
- Logging, output writing, and config loading

## Architecture

The implementation will add two new agent packages:

- `agents/research/`
- `agents/revenue/`

It will add `workflows/mvp_workflow.py` as a dedicated high-level coordinator rather than overloading the existing single-task `WorkflowOrchestrator`. The new workflow will own step sequencing, artifact handoff, progress visualization, state persistence, recovery, and packaged delivery creation.

The workflow will use explicit typed step records so each department receives prior outputs as context and each result can be resumed or inspected later.

## Workflow Stages

1. `client_request`
   - Normalize the incoming client request and create the workflow run directory.
2. `chief_orchestrator`
   - Produce the execution plan and department routing summary.
3. `research_department`
   - Generate market, business, and technical research notes.
4. `coding_department`
   - Produce implementation planning artifacts and implementation files.
5. `qa_department`
   - Generate test cases, validation results, bug logs, QA markdown report, and release recommendation.
6. `documentation_generation`
   - Generate user-facing and handoff documentation.
7. `revenue_packaging`
   - Package the offer, pricing rationale, deliverables, and value summary.
8. `human_approval`
   - Pause for approval before final delivery.
9. `final_delivery`
   - Create the final packaged delivery folder and manifest.

## Outputs

Each workflow run will create a delivery folder under:

`D:\agentic services\deliveries\<workflow_run_id>\`

The final folder will include:

- `project_summary.md`
- `implementation\`
- `qa_report.md`
- `documentation.md`
- `revenue_package.md`
- `delivery_manifest.json`
- `workflow_state.json`

Intermediate outputs will remain saved under the normal project output paths so the workflow is auditable and recoverable.

## State And Recovery

The workflow will persist a JSON state file after every stage. State will include:

- workflow id
- client request
- current stage
- completed stages
- failed stages
- department summaries
- artifact paths
- timestamps
- approval status

If a stage fails, the workflow records the failure and supports rerunning from the last incomplete stage instead of starting from zero.

## Inter-Agent Communication

Department handoff messages will be stored in workflow state and semantic memory. Each stage receives:

- original client request
- execution plan
- prior department summaries
- artifact paths
- retrieved project context

This keeps the system extensible for longer-running workflows and future departments.

## Terminal Experience

The CLI runner will expose:

- workflow start command
- terminal progress bar/status rows
- current department
- completed/failed stage counts
- saved artifact locations
- final delivery folder path

The first version will remain terminal-native and dependency-light rather than adding a web dashboard.

## Failure Handling

- Recoverable stage failures are captured in state and logged with the responsible department.
- Human approval rejection stops delivery cleanly and preserves all previous artifacts.
- Missing prior artifacts fail fast with clear errors.
- Resume mode reloads the state file and skips already completed stages.

## Testing

The test suite will cover:

- research and revenue agents
- happy-path full workflow execution
- artifact generation
- state persistence
- failure recovery/resume behavior
- human approval gating
- CLI runner invocation
- packaged delivery contents

## Non-Goals

- No web dashboard in this MVP
- No external billing system integration
- No real production deployment
- No attempt to fully automate every future department

## Success Criteria

- A local CLI command runs the complete MVP workflow end to end.
- All agents initialize successfully.
- Outputs, logs, memory, and workflow state are saved.
- The final delivery package is generated under `D:\agentic services`.
- Workflow recovery works from a saved failed state.
- The complete test suite passes before commit and push.
