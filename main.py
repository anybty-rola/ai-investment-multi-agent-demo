from __future__ import annotations

import argparse
import os
from pathlib import Path

from src.llm import LLMConfig
from src.orchestrator import run_research


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI 投研决策 Multi-Agent Demo")
    parser.add_argument("--topic", default="AI semiconductor supply chain", help="研究主题，例如 AI semiconductor supply chain")
    parser.add_argument("--region", default="global", help="区域，例如 global / China / US / HK")
    parser.add_argument("--tickers", default="", help="逗号分隔的股票代码，例如 NVDA,AMD,TSM,MU")
    parser.add_argument("--output-dir", default="outputs", help="输出目录")
    parser.add_argument("--deepseek-api-key", default="", help="DeepSeek API Key；也可使用环境变量 DEEPSEEK_API_KEY")
    parser.add_argument("--deepseek-base-url", default="https://api.deepseek.com/v1", help="DeepSeek OpenAI-compatible base URL")
    parser.add_argument("--deepseek-model", default="deepseek-chat", help="模型名，例如 deepseek-chat / deepseek-reasoner")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tickers = [item.strip() for item in args.tickers.split(",") if item.strip()]
    api_key = args.deepseek_api_key or os.getenv("DEEPSEEK_API_KEY", "")
    llm_config = None
    if api_key:
        llm_config = LLMConfig(
            api_key=api_key,
            base_url=args.deepseek_base_url,
            model=args.deepseek_model,
        )
    state, report_path = run_research(
        topic=args.topic,
        region=args.region,
        tickers=tickers,
        output_dir=Path(args.output_dir),
        llm_config=llm_config,
    )
    decision = state.get("DebateAndDecisionAgent")
    print(f"Report generated: {report_path}")
    if decision:
        print(decision.summary)


if __name__ == "__main__":
    main()
