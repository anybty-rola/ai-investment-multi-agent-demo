from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SourceItem:
    title: str
    url: str
    source: str = "unknown"
    summary: str = ""
    published: str = ""
    credibility: float = 0.5


@dataclass
class AgentResult:
    agent: str
    summary: str
    score: float | None = None
    evidence: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchState:
    topic: str
    region: str = "global"
    tickers: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    sources: list[SourceItem] = field(default_factory=list)
    results: list[AgentResult] = field(default_factory=list)

    def add_result(self, result: AgentResult) -> None:
        self.results.append(result)

    def get(self, agent_name: str) -> AgentResult | None:
        for result in reversed(self.results):
            if result.agent == agent_name:
                return result
        return None
