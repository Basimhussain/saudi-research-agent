from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from agent.llm import LLMClient
from memory.store import MemoryStore
from tools.registry import ToolRegistry
SYSTEM_PROMPT = """You are a Saudi business research agent.
Your job: answer questions about Saudi Arabian companies, markets, regulations,
and economics with rigor and structured output.
Rules:
1. Detect the language of the user's query. If Arabic, respond in Arabic. If
   English, respond in English. Never mix.
2. Use tools aggressively. For anything time-sensitive (prices, news, regulations)
   use web_search. For Tadawul quotes use tadawul_lookup. For VAT math use vat_calc.
   For SAMA interest rates and USD/SAR peg use sama_lookup.
3. Plan before you act. In your first reasoning turn, briefly state what you
   need to find out and which tools you'll use.
4. Cite sources. Every non-obvious claim in the final report needs a citation.
5. Finish with generate_report. This is mandatory — it validates your output.
   Do NOT write the final answer as free text; call generate_report exactly once
   at the end.
6. Be honest about uncertainty. Put data-freshness notes and gaps in `caveats`.
"""
MAX_STEPS = 10
@dataclass
class AgentResult:
    conversation_id: str
    report: dict[str, Any] | None
    transcript: list[dict[str, Any]]
    steps: int
    stopped_reason: str
class Agent:
    def __init__(
        self,
        llm: LLMClient,
        registry: ToolRegistry,
        memory: MemoryStore,
    ) -> None:
        self.llm = llm
        self.registry = registry
        self.memory = memory
    def _tool_schema(self) -> list[dict[str, Any]]:
        if self.llm.provider == "anthropic":
            return self.registry.anthropic_schema()
        return self.registry.openai_schema()
    def run(
        self,
        user_message: str,
        conversation_id: str | None = None,
        max_steps: int = MAX_STEPS,
        verbose: bool = True,
    ) -> AgentResult:
        cid = conversation_id or self.memory.new_conversation(title=user_message[:80])
        history = self.memory.load_messages(cid) if conversation_id else []
        history.append({"role": "user", "content": user_message})
        self.memory.append_message(cid, "user", user_message)
        tools_schema = self._tool_schema()
        final_report: dict[str, Any] | None = None
        stopped = "max_steps_reached"
        for step in range(1, max_steps + 1):
            if verbose:
                print(f"\n── step {step} ──")
            turn = self.llm.run_turn(
                system=SYSTEM_PROMPT,
                messages=history,
                tools=tools_schema,
            )
            history.append(turn.raw_assistant_message)
            self.memory.append_message(cid, "assistant", turn.raw_assistant_message)
            if turn.text and verbose:
                print(f"[assistant] {turn.text}")
            if turn.stop_reason != "tool_use" or not turn.tool_calls:
                stopped = "end_turn"
                break
            for call in turn.tool_calls:
                if verbose:
                    print(f"[tool_use] {call['name']}({call['arguments']})")
                try:
                    result = self.registry.dispatch(call["name"], call["arguments"])
                except Exception as e:
                    result = {"error": type(e).__name__, "message": str(e)}
                if verbose:
                    preview = str(result)
                    print(f"[tool_result] {preview[:300]}{'…' if len(preview) > 300 else ''}")
                if call["name"] == "generate_report" and isinstance(result, dict):
                    if result.get("status") == "ok":
                        final_report = result.get("report")
                tool_msg = self.llm.format_tool_result(call["id"], result)
                history.append(tool_msg)
                self.memory.append_message(cid, tool_msg["role"], tool_msg["content"])
            if final_report is not None:
                stopped = "report_generated"
                break
        else:
            stopped = "max_steps_reached"
        return AgentResult(
            conversation_id=cid,
            report=final_report,
            transcript=history,
            steps=step,
            stopped_reason=stopped,
        )