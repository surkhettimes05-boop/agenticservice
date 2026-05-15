import json
import logging
from pathlib import Path

import pytest

from custom_agents.agentic_it_firm.configs.loader import load_firm_config
from custom_agents.agentic_it_firm.llm_config import LLMRequest, ModelManager


class FakeUsage:
    prompt_tokens = 3
    completion_tokens = 5
    total_tokens = 8


class FakeMessage:
    content = "NVIDIA NIM is configured."


class FakeChoice:
    message = FakeMessage()


class FakeResponse:
    choices = [FakeChoice()]
    usage = FakeUsage()


class FakeChunkDelta:
    content = "chunk"


class FakeChunkChoice:
    delta = FakeChunkDelta()


class FakeChunk:
    choices = [FakeChunkChoice()]
    usage = None


class FakeChatCompletions:
    def __init__(self, failures_before_success=0):
        self.calls = []
        self.failures_before_success = failures_before_success

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.failures_before_success > 0:
            self.failures_before_success -= 1
            raise TimeoutError("temporary timeout")
        if kwargs.get("stream"):
            return iter([FakeChunk(), FakeChunk()])
        return FakeResponse()


class FakeClient:
    def __init__(self, failures_before_success=0):
        self.chat = type(
            "FakeChat",
            (),
            {"completions": FakeChatCompletions(failures_before_success)},
        )()


def write_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "agents.json"
    config_path.write_text(
        json.dumps(
            {
                "system": {
                    "name": "Agentic IT Firm",
                    "default_model": "nvidia_nim/meta/llama3-70b-instruct",
                    "approval_required_for": [],
                    "fallback_models": ["nvidia_nim/meta/llama3-8b-instruct"],
                    "timeout_seconds": 9,
                    "max_retries": 2,
                    "streaming": True,
                },
                "agents": [
                    {
                        "id": "project_manager",
                        "name": "Project Manager",
                        "role": "Project Manager",
                        "goal": "Plan work",
                        "instructions": "Plan clearly.",
                        "capabilities": ["planning"],
                    }
                ],
                "routes": [{"keywords": ["plan"], "agent_id": "project_manager"}],
            }
        ),
        encoding="utf-8",
    )
    return config_path


def test_model_manager_loads_nvidia_defaults_and_agent_config(tmp_path, monkeypatch):
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "nvapi-test")
    monkeypatch.setenv("NVIDIA_NIM_API_BASE", "https://integrate.api.nvidia.com/v1")
    config = load_firm_config(write_config(tmp_path))
    manager = ModelManager.from_config(config, client_factory=lambda cfg: FakeClient())

    assert manager.config.default_model == "nvidia_nim/meta/llama3-70b-instruct"
    assert manager.config.api_base == "https://integrate.api.nvidia.com/v1"
    assert manager.agent_model_config()["model"] == "nvidia_nim/meta/llama3-70b-instruct"
    assert manager.agent_model_config()["base_url"] == "https://integrate.api.nvidia.com/v1"


def test_complete_retries_and_records_token_usage(tmp_path, monkeypatch, caplog):
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "nvapi-test")
    monkeypatch.setenv("NVIDIA_NIM_API_BASE", "https://integrate.api.nvidia.com/v1")
    config = load_firm_config(write_config(tmp_path))
    fake_client = FakeClient(failures_before_success=1)
    manager = ModelManager.from_config(config, client_factory=lambda cfg: fake_client)

    with caplog.at_level(logging.INFO, logger="agentic_it_firm.llm"):
        result = manager.complete(LLMRequest(prompt="Say hello", agent_id="project_manager"))

    assert result.content == "NVIDIA NIM is configured."
    assert result.usage.total_tokens == 8
    assert result.latency_ms >= 0
    assert len(fake_client.chat.completions.calls) == 2
    assert "llm_token_usage" in caplog.text


def test_stream_returns_chunks_and_uses_timeout(tmp_path, monkeypatch):
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "nvapi-test")
    monkeypatch.setenv("NVIDIA_NIM_API_BASE", "https://integrate.api.nvidia.com/v1")
    config = load_firm_config(write_config(tmp_path))
    fake_client = FakeClient()
    manager = ModelManager.from_config(config, client_factory=lambda cfg: fake_client)

    chunks = list(manager.stream(LLMRequest(prompt="Stream please", agent_id="project_manager")))

    assert chunks == ["chunk", "chunk"]
    call = fake_client.chat.completions.calls[0]
    assert call["stream"] is True
    assert call["timeout"] == 9


def test_connection_test_reports_latency_and_usage(tmp_path, monkeypatch):
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "nvapi-test")
    monkeypatch.setenv("NVIDIA_NIM_API_BASE", "https://integrate.api.nvidia.com/v1")
    config = load_firm_config(write_config(tmp_path))
    manager = ModelManager.from_config(config, client_factory=lambda cfg: FakeClient())

    result = manager.test_connection("Confirm connection")

    assert result.ok is True
    assert result.response_text == "NVIDIA NIM is configured."
    assert result.usage.total_tokens == 8
    assert result.environment["NVIDIA_NIM_API_KEY"] == "loaded"
    assert result.environment["NVIDIA_NIM_API_BASE"] == "https://integrate.api.nvidia.com/v1"


def test_fallback_model_is_used_after_primary_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "nvapi-test")
    monkeypatch.setenv("NVIDIA_NIM_API_BASE", "https://integrate.api.nvidia.com/v1")
    config = load_firm_config(write_config(tmp_path))
    fake_client = FakeClient(failures_before_success=3)
    manager = ModelManager.from_config(config, client_factory=lambda cfg: fake_client)

    result = manager.complete(LLMRequest(prompt="Use fallback", agent_id="project_manager"))

    assert result.model == "nvidia_nim/meta/llama3-8b-instruct"
    attempted_models = [call["model"] for call in fake_client.chat.completions.calls]
    assert attempted_models == [
        "nvidia_nim/meta/llama3-70b-instruct",
        "nvidia_nim/meta/llama3-70b-instruct",
        "nvidia_nim/meta/llama3-70b-instruct",
        "nvidia_nim/meta/llama3-8b-instruct",
    ]
