from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from typing import Any, Literal
@dataclass
class LLMTurn:
    text: str | None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    stop_reason: Literal["end_turn", "tool_use", "other"] = "end_turn"
    raw_assistant_message: Any = None  
class LLMClient:
    provider: str
    def run_turn(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> LLMTurn:
        raise NotImplementedError
    def format_tool_result(self, tool_call_id: str, result: Any) -> dict[str, Any]:
        raise NotImplementedError
class AnthropicClient(LLMClient):
    provider = "anthropic"
    def __init__(self, model: str | None = None) -> None:
        import anthropic
        self._anthropic = anthropic
        self.client = anthropic.Anthropic()
        self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
    def run_turn(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> LLMTurn:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            tools=tools,
            messages=messages,
        )
        text_parts: list[str] = []
        tool_calls: list[dict[str, Any]] = []
        for block in resp.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(
                    {"id": block.id, "name": block.name, "arguments": dict(block.input)}
                )
        stop: Literal["end_turn", "tool_use", "other"]
        if resp.stop_reason == "tool_use":
            stop = "tool_use"
        elif resp.stop_reason == "end_turn":
            stop = "end_turn"
        else:
            stop = "other"
        assistant_msg = {
            "role": "assistant",
            "content": [block.model_dump() for block in resp.content],
        }
        return LLMTurn(
            text="\n".join(text_parts) if text_parts else None,
            tool_calls=tool_calls,
            stop_reason=stop,
            raw_assistant_message=assistant_msg,
        )
    def format_tool_result(self, tool_call_id: str, result: Any) -> dict[str, Any]:
        return {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_call_id,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                }
            ],
        }
class OpenAIClient(LLMClient):
    provider = "openai"
    def __init__(self, model: str | None = None) -> None:
        from openai import OpenAI
        self.client = OpenAI()
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o")
    def run_turn(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> LLMTurn:
        full_messages = [{"role": "system", "content": system}, *messages]
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            tools=tools,
            tool_choice="auto",
        )
        choice = resp.choices[0]
        msg = choice.message
        tool_calls: list[dict[str, Any]] = []
        for tc in msg.tool_calls or []:
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}
            tool_calls.append({"id": tc.id, "name": tc.function.name, "arguments": args})
        if choice.finish_reason == "tool_calls":
            stop: Literal["end_turn", "tool_use", "other"] = "tool_use"
        elif choice.finish_reason == "stop":
            stop = "end_turn"
        else:
            stop = "other"
        assistant_msg: dict[str, Any] = {"role": "assistant", "content": msg.content}
        if msg.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]
        return LLMTurn(
            text=msg.content,
            tool_calls=tool_calls,
            stop_reason=stop,
            raw_assistant_message=assistant_msg,
        )
    def format_tool_result(self, tool_call_id: str, result: Any) -> dict[str, Any]:
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": json.dumps(result, ensure_ascii=False, default=str),
        }
def build_llm() -> LLMClient:
    provider = os.environ.get("LLM_PROVIDER", "").lower().strip()
    if not provider:
        if os.environ.get("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        elif os.environ.get("OPENAI_API_KEY"):
            provider = "openai"
        else:
            raise RuntimeError(
                "No LLM provider configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY."
            )
    if provider == "anthropic":
        return AnthropicClient()
    if provider == "openai":
        return OpenAIClient()
    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}")