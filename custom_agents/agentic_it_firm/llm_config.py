"""Central NVIDIA NIM model manager with LiteLLM-compatible configuration."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

from custom_agents.agentic_it_firm.configs.loader import (
    DEFAULT_NVIDIA_MODEL,
    FirmConfig,
)


logger = logging.getLogger("agentic_it_firm.llm")


@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    api_key: str
    api_base: str
    default_model: str = DEFAULT_NVIDIA_MODEL
    fallback_models: list[str] = field(default_factory=list)
    timeout_seconds: int = 60
    max_retries: int = 2
    streaming: bool = True


@dataclass(frozen=True)
class LLMRequest:
    prompt: str
    agent_id: str
    system_prompt: str | None = None
    model: str | None = None
    temperature: float = 0.2
    max_tokens: int = 1200


@dataclass(frozen=True)
class LLMResult:
    content: str
    model: str
    usage: TokenUsage
    latency_ms: float
    estimated_cost: float | None
    attempts: int


@dataclass(frozen=True)
class ConnectionTestResult:
    ok: bool
    response_text: str
    latency_ms: float
    usage: TokenUsage
    environment: dict[str, str]
    model: str


class ModelManager:
    """Single LLM entry point for agents, scripts, and connection tests."""

    def __init__(self, config: LLMConfig, client_factory: Callable[[LLMConfig], Any] | None = None):
        self.config = config
        self._client_factory = client_factory or self._default_client_factory
        self._client: Any | None = None

    @classmethod
    def from_config(
        cls,
        config: FirmConfig,
        client_factory: Callable[[LLMConfig], Any] | None = None,
    ) -> "ModelManager":
        return cls(
            LLMConfig(
                provider="nvidia_nim",
                api_key=config.nvidia.api_key,
                api_base=config.nvidia.api_base,
                default_model=config.system.default_model,
                fallback_models=config.system.fallback_models,
                timeout_seconds=config.system.timeout_seconds,
                max_retries=config.system.max_retries,
                streaming=config.system.streaming,
            ),
            client_factory=client_factory,
        )

    def agent_model_config(self, model: str | None = None) -> dict[str, str]:
        return {
            "model": model or self.config.default_model,
            "api_key": self.config.api_key,
            "base_url": self.config.api_base,
        }

    def complete(self, request: LLMRequest) -> LLMResult:
        last_error: Exception | None = None
        attempts = 0
        started = time.perf_counter()
        for model in self._candidate_models(request.model):
            for retry_index in range(self.config.max_retries + 1):
                attempts += 1
                try:
                    response = self._client_instance().chat.completions.create(
                        model=model,
                        messages=self._messages(request),
                        temperature=request.temperature,
                        max_tokens=request.max_tokens,
                        timeout=self.config.timeout_seconds,
                    )
                    latency_ms = (time.perf_counter() - started) * 1000
                    usage = self._extract_usage(response)
                    content = self._extract_content(response)
                    logger.info(
                        "llm_token_usage provider=%s model=%s agent_id=%s prompt_tokens=%s completion_tokens=%s total_tokens=%s latency_ms=%.2f estimated_cost=%s",
                        self.config.provider,
                        model,
                        request.agent_id,
                        usage.prompt_tokens,
                        usage.completion_tokens,
                        usage.total_tokens,
                        latency_ms,
                        self.estimate_cost(model, usage),
                    )
                    return LLMResult(
                        content=content,
                        model=model,
                        usage=usage,
                        latency_ms=latency_ms,
                        estimated_cost=self.estimate_cost(model, usage),
                        attempts=attempts,
                    )
                except Exception as exc:
                    last_error = exc
                    logger.warning(
                        "llm_request_failed provider=%s model=%s agent_id=%s attempt=%s error=%s",
                        self.config.provider,
                        model,
                        request.agent_id,
                        retry_index + 1,
                        exc,
                    )
                    if retry_index < self.config.max_retries:
                        time.sleep(min(0.25 * (retry_index + 1), 1.0))
        raise RuntimeError(f"NVIDIA NIM request failed after {attempts} attempts: {last_error}") from last_error

    def stream(self, request: LLMRequest) -> Iterable[str]:
        if not self.config.streaming:
            yield self.complete(request).content
            return
        model = request.model or self.config.default_model
        response = self._client_instance().chat.completions.create(
            model=model,
            messages=self._messages(request),
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            timeout=self.config.timeout_seconds,
            stream=True,
        )
        for chunk in response:
            content = self._extract_stream_content(chunk)
            if content:
                yield content

    def test_connection(self, prompt: str = "Reply with one short sentence confirming NVIDIA NIM works.") -> ConnectionTestResult:
        result = self.complete(LLMRequest(prompt=prompt, agent_id="connection_test", max_tokens=120))
        return ConnectionTestResult(
            ok=bool(result.content.strip()),
            response_text=result.content,
            latency_ms=result.latency_ms,
            usage=result.usage,
            environment={
                "NVIDIA_NIM_API_KEY": "loaded" if os.getenv("NVIDIA_NIM_API_KEY") else "missing",
                "NVIDIA_NIM_API_BASE": os.getenv("NVIDIA_NIM_API_BASE", self.config.api_base),
            },
            model=result.model,
        )

    def estimate_cost(self, model: str, usage: TokenUsage) -> float | None:
        # Placeholder: NVIDIA NIM pricing varies by deployment and account.
        _ = (model, usage)
        return None

    def _client_instance(self) -> Any:
        if self._client is None:
            self._client = self._client_factory(self.config)
        return self._client

    @staticmethod
    def _default_client_factory(config: LLMConfig) -> Any:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install openai to use NVIDIA NIM connection support.") from exc
        return OpenAI(api_key=config.api_key, base_url=config.api_base)

    def _candidate_models(self, requested_model: str | None) -> list[str]:
        primary = requested_model or self.config.default_model
        return [primary, *[model for model in self.config.fallback_models if model != primary]]

    @staticmethod
    def _messages(request: LLMRequest) -> list[dict[str, str]]:
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        return messages

    @staticmethod
    def _extract_usage(response: Any) -> TokenUsage:
        usage = getattr(response, "usage", None)
        if usage is None:
            return TokenUsage()
        return TokenUsage(
            prompt_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
            completion_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
            total_tokens=int(getattr(usage, "total_tokens", 0) or 0),
        )

    @staticmethod
    def _extract_content(response: Any) -> str:
        choices = getattr(response, "choices", [])
        if not choices:
            return ""
        message = getattr(choices[0], "message", None)
        return str(getattr(message, "content", "") or "")

    @staticmethod
    def _extract_stream_content(chunk: Any) -> str:
        choices = getattr(chunk, "choices", [])
        if not choices:
            return ""
        delta = getattr(choices[0], "delta", None)
        return str(getattr(delta, "content", "") or "")
