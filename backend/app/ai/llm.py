"""Provider-neutral LLM interface plus the Groq implementation (OpenAI-compatible chat completions).

Services depend only on ``LLM``; tests substitute a scripted fake. Model turns keep the
provider's raw assistant message so tool-call turns are replayed exactly as the API returned them.
"""

import json
import logging
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Protocol

import httpx

from ..core.config import get_settings

logger = logging.getLogger(__name__)


class LLMUnavailable(Exception):
    """The model could not produce a usable reply (no key, timeout, provider error, empty output)."""

    def __init__(self, message: str, *, busy: bool = False):
        super().__init__(message)
        self.busy = busy  # the provider's own rate limit was hit; worth retrying shortly


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: dict[str, Any]
    id: str = ""  # provider's call id; tool results are matched to calls by it


@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(self.prompt_tokens + other.prompt_tokens, self.completion_tokens + other.completion_tokens)


@dataclass
class LLMReply:
    text: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: Any = None
    usage: TokenUsage = field(default_factory=TokenUsage)


@dataclass
class UserMessage:
    text: str


@dataclass
class ModelMessage:
    reply: LLMReply


@dataclass
class ToolResultMessage:
    results: list[tuple[ToolCall, dict[str, Any]]]


Message = UserMessage | ModelMessage | ToolResultMessage


class LLM(Protocol):
    def generate(
        self,
        *,
        system: str,
        messages: list[Message],
        timeout: float,
        tools: list[ToolSpec] | None = None,
        json_schema: dict[str, Any] | None = None,
    ) -> LLMReply: ...


class GroqLLM:
    """Groq's OpenAI-compatible ``/chat/completions`` endpoint, with tool calling and JSON mode."""

    # Groq rejects a malformed tool call the model produced with this error code; a retry usually succeeds.
    RETRYABLE_ERROR = "tool_use_failed"
    # Models that think before answering; their hidden reasoning counts toward max_tokens.
    REASONING_MODEL_PREFIXES = ("openai/gpt-oss",)

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        max_output_tokens: int = 1500,
        reasoning_effort: str = "low",
        transport: httpx.BaseTransport | None = None,
    ):
        self._model = model
        self._max_output_tokens = max_output_tokens
        self._reasoning_effort = reasoning_effort if model.startswith(self.REASONING_MODEL_PREFIXES) else None
        self._http = httpx.Client(
            base_url=base_url, headers={"Authorization": f"Bearer {api_key}"}, transport=transport
        )

    @staticmethod
    def _to_api(message: Message) -> list[dict[str, Any]]:
        if isinstance(message, UserMessage):
            return [{"role": "user", "content": message.text}]
        if isinstance(message, ModelMessage):
            return [message.reply.raw or {"role": "assistant", "content": message.reply.text or ""}]
        return [
            {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result, default=str)}
            for call, result in message.results
        ]

    def generate(self, *, system, messages, timeout, tools=None, json_schema=None) -> LLMReply:
        body: dict[str, Any] = {
            "model": self._model,
            "temperature": 0.2,
            "max_tokens": self._max_output_tokens,
            **({"reasoning_effort": self._reasoning_effort} if self._reasoning_effort else {}),
            "messages": [{"role": "system", "content": system}] + [m for msg in messages for m in self._to_api(msg)],
        }
        if tools:
            body["tools"] = [
                {"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.parameters}}
                for t in tools
            ]
            body["tool_choice"] = "auto"
        if json_schema:
            # JSON mode; the prompt describes the shape and the service validates it against the schema.
            body["response_format"] = {"type": "json_object"}

        data = self._complete(body, timeout)
        message = data["choices"][0]["message"]
        usage = data.get("usage") or {}

        calls = []
        for call in message.get("tool_calls") or []:
            try:
                args = json.loads(call["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            calls.append(ToolCall(name=call["function"]["name"], args=args if isinstance(args, dict) else {}, id=call["id"]))

        raw = {"role": "assistant", "content": message.get("content") or ""}
        if message.get("tool_calls"):
            raw["tool_calls"] = message["tool_calls"]
        text = None if calls else (message.get("content") or "").strip() or None
        return LLMReply(
            text=text,
            tool_calls=calls,
            raw=raw,
            usage=TokenUsage(usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)),
        )

    def _complete(self, body: dict[str, Any], timeout: float) -> dict[str, Any]:
        for attempt in range(2):
            try:
                response = self._http.post("/chat/completions", json=body, timeout=timeout)
                response.raise_for_status()
                data = response.json()
                if not data.get("choices"):
                    raise ValueError("response has no choices")
                return data
            except httpx.HTTPStatusError as exc:
                detail = exc.response.text[:300]
                if attempt == 0 and self.RETRYABLE_ERROR in detail:
                    logger.info("Groq rejected a generated tool call; retrying once")
                    continue
                logger.warning("Groq request failed: %s", detail)
                raise LLMUnavailable(detail, busy=exc.response.status_code == 429) from exc
            except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
                logger.warning("Groq request failed: %s", exc)
                raise LLMUnavailable(str(exc)) from exc
        raise AssertionError("unreachable")


@lru_cache
def _groq(api_key: str, model: str, base_url: str, max_output_tokens: int, reasoning_effort: str) -> GroqLLM:
    return GroqLLM(api_key, model, base_url, max_output_tokens, reasoning_effort)


def get_llm() -> LLM | None:
    """FastAPI dependency. ``None`` when no AI key is configured (features fall back gracefully)."""
    settings = get_settings()
    if not settings.ai_api_key:
        return None
    return _groq(
        settings.ai_api_key,
        settings.ai_model,
        settings.ai_base_url,
        settings.ai_max_output_tokens,
        settings.ai_reasoning_effort,
    )
