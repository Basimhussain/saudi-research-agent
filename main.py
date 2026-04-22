from __future__ import annotations
import argparse
import json
import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from agent.llm import build_llm
from agent.loop import Agent
from memory.store import MemoryStore
from tools.registry import ToolRegistry
from tools.report import TOOL as REPORT_TOOL
from tools.tadawul import TOOL as TADAWUL_TOOL
from tools.vat import TOOL as VAT_TOOL
from tools.web_search import TOOL as WEB_TOOL
from tools.sama import TOOL as SAMA_TOOL
console = Console()
def build_agent() -> Agent:
    load_dotenv()
    registry = ToolRegistry()
    for tool in (WEB_TOOL, TADAWUL_TOOL, VAT_TOOL, REPORT_TOOL, SAMA_TOOL):
        registry.register(tool)
    memory = MemoryStore(path=os.environ.get("DB_PATH", "./agent_memory.db"))
    llm = build_llm()
    console.print(f"[dim]LLM provider: {llm.provider} · DB: {memory.path}[/dim]")
    return Agent(llm=llm, registry=registry, memory=memory)
def render_report(report: dict) -> None:
    console.print(
        Panel.fit(
            Syntax(json.dumps(report, ensure_ascii=False, indent=2), "json", word_wrap=True),
            title="[bold green]Research Report[/bold green]",
        )
    )
def interactive(agent: Agent) -> None:
    console.print("[bold]Saudi Business Research Agent[/bold] — Ctrl-C to exit")
    cid: str | None = None
    while True:
        try:
            query = console.input("\n[bold cyan]you ›[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nbye")
            return
        if not query:
            continue
        result = agent.run(query, conversation_id=cid)
        cid = result.conversation_id
        if result.report:
            render_report(result.report)
        else:
            console.print(
                f"[yellow]No validated report produced "
                f"(stopped: {result.stopped_reason}, steps: {result.steps}).[/yellow]"
            )
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="*", help="One-shot query.")
    parser.add_argument("--resume", help="Resume conversation by id.")
    parser.add_argument("--list", action="store_true", help="List conversations.")
    args = parser.parse_args()
    agent = build_agent()
    if args.list:
        for conv in agent.memory.list_conversations():
            console.print(f"{conv['id']}  {conv['updated_at']}  {conv['title']}")
        return 0
    if args.query:
        result = agent.run(" ".join(args.query), conversation_id=args.resume)
        if result.report:
            render_report(result.report)
        else:
            console.print(f"[yellow]No report. Reason: {result.stopped_reason}[/yellow]")
        return 0
    interactive(agent)
    return 0
if __name__ == "__main__":
    main()