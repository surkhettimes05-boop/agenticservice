"""Live NVIDIA NIM connection test utility."""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from custom_agents.agentic_it_firm.configs.loader import load_firm_config
from custom_agents.agentic_it_firm.llm_config import ModelManager


def main() -> int:
    config = load_firm_config()
    manager = ModelManager.from_config(config)
    result = manager.test_connection("Reply with one sentence: NVIDIA NIM connection is working.")

    print("NVIDIA NIM connection test")
    print(f"environment.NVIDIA_NIM_API_KEY={result.environment['NVIDIA_NIM_API_KEY']}")
    print(f"environment.NVIDIA_NIM_API_BASE={result.environment['NVIDIA_NIM_API_BASE']}")
    print(f"ok={result.ok}")
    print(f"model={result.model}")
    print(f"latency_ms={result.latency_ms:.2f}")
    print(f"prompt_tokens={result.usage.prompt_tokens}")
    print(f"completion_tokens={result.usage.completion_tokens}")
    print(f"total_tokens={result.usage.total_tokens}")
    print(f"response={result.response_text}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
