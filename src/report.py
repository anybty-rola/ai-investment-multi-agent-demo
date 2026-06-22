from __future__ import annotations

from .models import ResearchState


def build_markdown_report(state: ResearchState) -> str:
    decision = state.get("DebateAndDecisionAgent")
    industry = state.get("IndustryThesisAgent")
    company = state.get("CompanyScreeningAgent")
    valuation = state.get("FundamentalValuationAgent")
    risk = state.get("RiskAgent")
    llm = state.get("DeepSeekSynthesisAgent")

    lines: list[str] = []
    lines.append(f"# AI 投研决策报告：{state.topic}")
    lines.append("")
    lines.append(f"- 区域：{state.region}")
    lines.append(f"- 生成时间：{state.created_at}")
    if state.tickers:
        lines.append(f"- 输入公司：{', '.join(state.tickers)}")
    lines.append("- 免责声明：本报告仅用于学习和研究流程演示，不构成投资建议。")
    lines.append("")

    lines.append("## 1. 最终结论")
    if decision:
        lines.append(f"- 决策：{decision.data.get('decision')}")
        lines.append(f"- 置信度：{decision.data.get('confidence')}")
        lines.append(f"- 摘要：{decision.summary}")
        for item in decision.evidence:
            lines.append(f"- {item}")
    lines.append("")

    lines.append("## 2. 行业判断")
    if industry:
        lines.append(f"- 推荐行业：{industry.data.get('top_industry')}")
        lines.append(f"- 行业评分：{industry.score:.2f}" if industry.score is not None else "- 行业评分：N/A")
        lines.append(f"- 投资假设：{industry.summary}")
        lines.append("")
        lines.append("### 行业评分明细")
        for item in industry.evidence:
            lines.append(f"- {item}")
    lines.append("")

    lines.append("## 3. 公司候选池")
    if company:
        for item in company.evidence:
            lines.append(f"- {item}")
    lines.append("")

    lines.append("## 4. 基本面与估值框架")
    if valuation:
        lines.append(f"- {valuation.summary}")
        for item in valuation.evidence:
            lines.append(f"- {item}")
    lines.append("")

    lines.append("## 5. 风险审查")
    if risk:
        lines.append(f"- {risk.summary}")
        for item in risk.evidence:
            lines.append(f"- {item}")
    lines.append("")

    if llm:
        lines.append("## 6. DeepSeek 大模型增强研判")
        content = llm.data.get("content")
        if content:
            lines.append(content)
        else:
            lines.append(f"- {llm.summary}")
        lines.append("")

    lines.append("## 7. Agent 输出记录")
    for result in state.results:
        lines.append(f"### {result.agent}")
        lines.append(f"- Summary: {result.summary}")
        if result.score is not None:
            lines.append(f"- Score: {result.score:.2f}")
        if result.evidence:
            lines.append("- Evidence:")
            for evidence in result.evidence[:8]:
                lines.append(f"  - {evidence}")
        lines.append("")

    lines.append("## 8. 信息源")
    for source in state.sources[:20]:
        title = source.title.replace("\n", " ")
        lines.append(f"- [{title}]({source.url}) | {source.source} | credibility={source.credibility:.2f}")
    lines.append("")

    lines.append("## 9. 下一步增强")
    lines.append("- 用 DeepSeek / Qwen / GPT 接入各 Agent 的推理层，替换当前规则评分。")
    lines.append("- 接入 SEC EDGAR、FRED、OpenBB、FMP、Yahoo Finance、GDELT、YouTube Data API 等合规数据源。")
    lines.append("- 对行业因子做事件研究、Granger causality、滞后相关、回归和回测，避免只依赖新闻共现。")
    lines.append("- 对候选公司生成 DCF、可比公司、反向 DCF、情景分析和敏感性分析。")
    lines.append("- 增加 Fact Checker Agent，要求所有关键结论必须有来源引用和置信度。")
    return "\n".join(lines)
