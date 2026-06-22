from __future__ import annotations

from pathlib import Path

from .agents import (
    CompanyScreeningAgent,
    DebateAndDecisionAgent,
    DeepSeekSynthesisAgent,
    FactorImpactAgent,
    FundamentalValuationAgent,
    IndustryThesisAgent,
    MacroAgent,
    NewsAndEventCollectorAgent,
    RiskAgent,
    SentimentAndEventAgent,
    SourceDiscoveryAgent,
)
from .llm import LLMConfig
from .models import ResearchState
from .report import build_markdown_report


DEFAULT_PIPELINE = [
    SourceDiscoveryAgent(),
    NewsAndEventCollectorAgent(),
    SentimentAndEventAgent(),
    MacroAgent(),
    IndustryThesisAgent(),
    FactorImpactAgent(),
    CompanyScreeningAgent(),
    FundamentalValuationAgent(),
    RiskAgent(),
    DebateAndDecisionAgent(),
]


def run_research(
    topic: str,
    region: str = "global",
    tickers: list[str] | None = None,
    output_dir: str | Path = "outputs",
    llm_config: LLMConfig | None = None,
) -> tuple[ResearchState, Path]:
    state = ResearchState(topic=topic, region=region, tickers=tickers or [])
    for agent in DEFAULT_PIPELINE:
        agent.run(state)
    if llm_config and llm_config.enabled:
        DeepSeekSynthesisAgent(llm_config).run(state)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "research_report.md"
    report_path.write_text(build_markdown_report(state), encoding="utf-8")
    return state, report_path
