from __future__ import annotations

import argparse
from pathlib import Path

from custom_agents.agentic_it_firm.workflows.mvp_workflow import MVPWorkflow, STAGES


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Agentic IT Firm MVP workflow.")
    parser.add_argument("--request", required=True)
    parser.add_argument("--deliveries-root", default="deliveries")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--require-approval", action="store_true")
    args = parser.parse_args()

    workflow = MVPWorkflow.local(
        deliveries_root=Path(args.deliveries_root),
        dry_run=not args.live,
        auto_approve=not args.require_approval,
    )
    result = workflow.run(args.request)
    completed = set(result.state.completed_stages)
    print("MVP Workflow Progress")
    for stage in STAGES:
        marker = "[x]" if stage in completed else "[ ]"
        print(f"{marker} {stage}")
    print(f"status={result.status}")
    print(f"delivery_dir={result.delivery_dir}")
    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
