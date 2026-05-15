# Agentic IT Firm

This folder contains a production-oriented foundation for a custom multi-agent AI operating system built on `praisonaiagents.Agent` and NVIDIA NIM-compatible model configuration.

Default model:

```text
nvidia_nim/meta/llama3-70b-instruct
```

## Architecture

- `agents/` reusable PraisonAI agent wrapper and registry
- `agents/base_agent.py` enterprise `BaseAgent` with metadata, memory hooks, execution, validation, self-checks, escalation and approval metadata, and tool permission controls
- `configs/` JSON agent team and route configuration
- `workflows/` task routing and orchestration
- `memory/` JSONL shared memory for cross-agent coordination
- `memory/` semantic project, agent, workflow, client, and conversation memory with local vector search and PostgreSQL pgvector support
- `tools/` human approvals, output writing, and runtime logging
- `approvals/` persistent human approval queue, audit log, risk scoring, and terminal approval manager
- `llm_config.py` centralized NVIDIA NIM model manager with retry, timeout, streaming, token usage logging, fallback models, and connection testing
- `outputs/` generated task outputs
- `logs/` runtime logs

## Setup

```powershell
cd "C:\Users\QCS\Desktop\agentic services\PraisonAI"
python -m pip install -r custom_agents/agentic_it_firm/requirements.txt
Copy-Item custom_agents/agentic_it_firm/.env.example custom_agents/agentic_it_firm/.env
```

Edit `.env`:

```env
NVIDIA_NIM_API_KEY=nvapi-your-key-here
NVIDIA_NIM_API_BASE=https://integrate.api.nvidia.com/v1
NVIDIA_NIM_MODEL=nvidia_nim/meta/llama3-70b-instruct
AGENTIC_MEMORY_BACKEND=local
AGENTIC_MEMORY_DATABASE_URL=postgresql://user:password@localhost:5432/agentic_it_firm
```

## Run a Dry-Run Workflow

Dry-run mode initializes real `praisonaiagents.Agent` objects but does not call NVIDIA NIM.

```powershell
python custom_agents/agentic_it_firm/startup.py --task "Plan a secure client portal MVP" --auto-approve --dry-run
```

## Validate NVIDIA NIM

This makes a live API request using the configured NVIDIA key:

```powershell
python custom_agents/agentic_it_firm/startup.py --validate-connection
```

Or run the standalone test utility:

```powershell
python custom_agents/agentic_it_firm/test_nvidia_connection.py
```

The utility prints environment status, latency, token usage, model, and response text.

## Run Live

```powershell
python custom_agents/agentic_it_firm/startup.py --task "Create a deployment plan for a client portal" --auto-approve
```

Without `--auto-approve`, approval-controlled tasks such as deployment, billing, production changes, secrets, and external messages ask for human approval.

## Human Approvals

Agents pause for approval before production deployment, deleting files, modifying secrets, sending client emails, spending money, changing databases, or changing credentials. Approval requests are stored in `memory/approval_queue.json`, and audit events are appended to `memory/approval_audit.jsonl`.

The approval system provides:

- Approval request summaries
- Risk scoring
- Terminal approval/rejection handling
- JSON persistence
- Approval history
- Human-readable audit logs

The Human Approval Agent lives at `agents/orchestrator/human_approval_agent.py` and summarizes the requested action, why it is needed, possible risks, rollback considerations, and recommended action.

## Memory And Knowledge System

The memory system supports:

- Project memory
- Agent memory and learning history
- Workflow memory
- Client memory
- Conversation memory
- Semantic search and vector retrieval
- Long-running workflow session tracking
- Cross-agent shared context
- Persistent project state

Local development uses durable JSONL vector storage at `memory/semantic_memory.jsonl`. Production deployments can use PostgreSQL with pgvector through `PostgresPgVectorMemoryStore`; set `AGENTIC_MEMORY_DATABASE_URL` and call `initialize_schema()` once during database setup.

Example:

```python
from custom_agents.agentic_it_firm.memory import MemoryManager, MemoryScope, ProjectContextLoader

memory = MemoryManager.local("custom_agents/agentic_it_firm/memory/semantic_memory.jsonl")
session = memory.sessions.start_session(project_id="client_portal", client_id="acme", workflow_id="wf-001")
memory.remember(
    scope=MemoryScope.PROJECT,
    text="Client portal uses FastAPI, PostgreSQL, Supabase auth, and a Next.js dashboard.",
    project_id="client_portal",
    client_id="acme",
    session_id=session.session_id,
)
context = ProjectContextLoader(memory).load("client_portal", "database auth dashboard")
print(context["context_text"])
```

## Coding Department

The Coding Department lives under `agents/coding/` and uses `BaseAgent` for all department specialists:

- Coding Team Leader Agent
- Frontend Engineer Agent
- Backend Engineer Agent
- Database Engineer Agent
- API Integration Agent
- Refactoring Agent
- Code Review Agent

Supporting modules:

- `RepositoryContextLoader` scans project files while skipping secrets and generated folders.
- `ArchitecturePlanner` produces stack-aware architecture plans for Next.js, React, Tailwind, FastAPI, PostgreSQL, and Supabase.
- `ImplementationWorkflow` creates the coding delivery workflow.
- `CodeReviewPipeline` detects code smells, risk patterns, hardcoded secrets, unsafe `eval`, broad exception handling, and large-file risks.

Example:

```python
from custom_agents.agentic_it_firm.agents.coding import CodeReviewPipeline

report = CodeReviewPipeline().review(".")
print(report["summary"])
```

## QA Department

The QA Department lives under `agents/qa/` and uses `BaseAgent` for all department specialists:

- QA Team Leader Agent
- Test Case Agent
- QA Validator Agent
- Bug Detection Agent
- Regression Testing Agent

Supporting modules:

- `TestCaseGenerator` creates structured acceptance test cases.
- `AcceptanceCriteriaValidator` produces pass/fail validation results and quality scores.
- `BugReportBuilder` converts failed checks into structured bug logs.
- `QARegressionWorkflow` runs baseline regression checks.
- `QAReleaseReadinessScorer` produces release readiness scores and recommendations.
- `QAReportWriter` renders markdown QA reports.

Example:

```python
from custom_agents.agentic_it_firm.agents.qa import QARegressionWorkflow, QAReportWriter

report = QARegressionWorkflow().run(
    "client portal release",
    ["user can log in", "dashboard loads"],
    {"user can log in": True, "dashboard loads": False},
)
print(QAReportWriter().to_markdown(report))
```

## Agent Team

The default firm includes:

- Chief Orchestrator
- Project Manager
- Business Analyst
- Solution Architect
- Coding Team Leader
- Backend Engineer
- Frontend Engineer
- Database Engineer
- API Integration Agent
- Refactoring Agent
- Code Review Agent
- QA Engineer
- QA Team Leader
- Test Case Agent
- QA Validator
- Bug Detection Agent
- Regression Testing Agent
- DevOps Engineer
- Security Reviewer
- Documentation Specialist

Tasks are routed by keyword in `configs/agents.json`. Add agents by inserting a new agent definition and route entry.

## Chief Orchestrator

The Chief Orchestrator lives at `agents/orchestrator/chief_orchestrator.py` and acts as the AI COO / Executive Orchestrator. It receives project requests, breaks them into JSON structured execution plans, assigns departments, routes work to agents, tracks dependencies, queues tasks by priority, records inter-agent messages, saves project context memory, and escalates approval-controlled work.

Example use:

```python
from custom_agents.agentic_it_firm.agents.orchestrator import ChiefOrchestratorAgent
from custom_agents.agentic_it_firm.configs.loader import load_firm_config
from custom_agents.agentic_it_firm.llm_config import ModelManager

config = load_firm_config()
definition = next(agent for agent in config.agents if agent.id == "chief_orchestrator")
chief = ChiefOrchestratorAgent(
    definition=definition,
    model_manager=ModelManager.from_config(config),
    routes=config.routes,
    approval_required_for=config.system.approval_required_for,
    dry_run=True,
)
plan = chief.create_execution_plan("Build a secure client portal with dashboard, API, tests, and deployment plan")
```

Agent definitions can include enterprise metadata:

```json
{
  "department": "Engineering",
  "expertise": ["backend", "api design"],
  "years_of_experience": 8,
  "allowed_actions": ["test", "review", "build"],
  "restricted_actions": ["deploy", "delete"],
  "escalation_rules": ["Escalate security findings to security_reviewer"],
  "approval_rules": ["Require human approval before production changes"],
  "memory_enabled": true,
  "reviewer_agent": "security_reviewer",
  "reporting_agent": "project_manager"
}
```

## LLM Manager

All firm agents receive a shared `ModelManager`. Live task execution uses the manager's OpenAI-compatible NVIDIA NIM client rather than each agent creating its own provider client. This keeps retries, timeouts, token usage logging, fallback model selection, streaming behavior, and cost-estimation hooks centralized.
