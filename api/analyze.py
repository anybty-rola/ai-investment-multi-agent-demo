from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents import DeepSeekSynthesisAgent  # noqa: E402
from src.llm import LLMConfig  # noqa: E402
from src.orchestrator import DEFAULT_PIPELINE  # noqa: E402
from src.report import build_markdown_report  # noqa: E402
from src.models import ResearchState  # noqa: E402


def run_state(payload: dict) -> ResearchState:
    state = ResearchState(
        topic=payload.get("topic") or "AI semiconductor supply chain",
        region=payload.get("region") or "global",
        tickers=payload.get("tickers") or [],
    )
    for agent in DEFAULT_PIPELINE:
        agent.run(state)

    provider = payload.get("provider") or "deepseek"
    env_key = "OPENROUTER_API_KEY" if provider == "openrouter" else "DEEPSEEK_API_KEY"
    api_key = (payload.get("api_key") or os.getenv(env_key, "")).strip()
    if api_key:
        extra_headers = {}
        if provider == "openrouter":
            extra_headers = {
                "HTTP-Referer": "https://vercel.app",
                "X-Title": "AI Investment Multi-Agent System",
            }
        DeepSeekSynthesisAgent(
            LLMConfig(
                api_key=api_key,
                base_url=(payload.get("base_url") or "https://api.deepseek.com/v1").strip(),
                model=(payload.get("model") or "deepseek-chat").strip(),
                provider=provider,
                extra_headers=extra_headers,
            )
        ).run(state)
    return state


def response_body(state: ResearchState) -> dict:
    decision = state.get("DebateAndDecisionAgent")
    industry = state.get("IndustryThesisAgent")
    risk = state.get("RiskAgent")
    llm = state.get("DeepSeekSynthesisAgent")
    return {
        "metrics": {
            "decision": decision.data.get("decision") if decision else None,
            "industry": industry.data.get("top_industry") if industry else None,
            "risk_score": round(risk.score, 2) if risk and risk.score is not None else None,
            "llm_enabled": bool(llm and llm.data.get("enabled")),
        },
        "agents": [
            {
                "agent": item.agent,
                "summary": item.summary,
                "score": round(item.score, 2) if item.score is not None else None,
            }
            for item in state.results
        ],
        "report": build_markdown_report(state),
    }


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, body: dict) -> None:
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self) -> None:
        self._send_json(200, {"ok": True})

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw or "{}")
            state = run_state(payload)
            self._send_json(200, response_body(state))
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})
