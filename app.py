from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.llm import LLMConfig
from src.orchestrator import run_research


st.set_page_config(page_title="AI 投研决策 Multi-Agent Demo", layout="wide")

st.title("AI 投研决策 Multi-Agent Demo")
st.caption("信息源发现 -> 情绪事件 -> 宏观行业 -> 多因子影响 -> 公司筛选 -> 估值风险 -> 多空辩论 -> 投研报告")

with st.sidebar:
    st.header("研究任务")
    topic = st.text_input("研究主题", value="AI semiconductor supply chain")
    region = st.selectbox("区域", ["global", "US", "China", "HK"], index=0)
    tickers_raw = st.text_input("候选公司/股票代码", value="NVDA,AMD,TSM,MU")
    st.divider()
    st.header("大模型增强")
    enable_llm = st.toggle("启用大模型增强分析", value=False)
    provider = st.selectbox("模型渠道", ["DeepSeek", "OpenRouter", "自定义 OpenAI-compatible"], index=0)
    if provider == "DeepSeek":
        api_key = st.text_input("DeepSeek API Key", value="", type="password", help="只在本次会话中使用，不会写入文件。")
        base_url = st.text_input("Base URL", value="https://api.deepseek.com/v1")
        model = st.selectbox("模型", ["deepseek-chat", "deepseek-reasoner"], index=0)
    elif provider == "OpenRouter":
        api_key = st.text_input("OpenRouter API Key", value="", type="password", help="只在本次会话中使用，不会写入文件。")
        base_url = st.text_input("Base URL", value="https://openrouter.ai/api/v1")
        model = st.text_input("模型", value="deepseek/deepseek-chat-v3-0324", help="例如 deepseek/deepseek-chat-v3-0324、deepseek/deepseek-r1、openai/gpt-4o-mini")
    else:
        api_key = st.text_input("API Key", value="", type="password", help="只在本次会话中使用，不会写入文件。")
        base_url = st.text_input("Base URL", value="https://api.openai.com/v1")
        model = st.text_input("模型", value="gpt-4o-mini")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.1)
    max_tokens = st.slider("Max tokens", 800, 4000, 1800, 200)
    st.caption("不填 API Key 时，平台仍会使用规则 Agent 跑通完整投研流程；填写后只增强最后的综合研判层。")
    st.divider()
    run = st.button("生成投研报告", type="primary")

if run:
    tickers = [item.strip() for item in tickers_raw.split(",") if item.strip()]
    llm_config = None
    if enable_llm and api_key.strip():
        extra_headers = {}
        if provider == "OpenRouter":
            extra_headers = {
                "HTTP-Referer": "http://localhost:8501",
                "X-Title": "AI Investment Multi-Agent Demo",
            }
        llm_config = LLMConfig(
            api_key=api_key.strip(),
            base_url=base_url.strip(),
            model=model.strip(),
            provider=provider,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_headers=extra_headers,
        )
    with st.spinner("Multi-agent pipeline running..."):
        state, report_path = run_research(topic=topic, region=region, tickers=tickers, llm_config=llm_config)
        report = Path(report_path).read_text(encoding="utf-8")

    decision = state.get("DebateAndDecisionAgent")
    industry = state.get("IndustryThesisAgent")
    risk = state.get("RiskAgent")
    llm = state.get("DeepSeekSynthesisAgent")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("最终决策", decision.data.get("decision") if decision else "N/A")
    c2.metric("推荐行业", industry.data.get("top_industry") if industry else "N/A")
    c3.metric("风险可信度", f"{risk.score:.2f}" if risk and risk.score is not None else "N/A")
    c4.metric("DeepSeek", "已启用" if llm and llm.data.get("enabled") else "未启用")

    if llm:
        st.subheader("DeepSeek 大模型增强研判")
        if llm.data.get("content"):
            st.markdown(llm.data["content"])
        else:
            st.warning(llm.summary)

    st.subheader("Agent 输出")
    for result in state.results:
        with st.expander(result.agent, expanded=result.agent in {"DebateAndDecisionAgent", "IndustryThesisAgent"}):
            st.write(result.summary)
            if result.score is not None:
                st.progress(max(0.0, min(1.0, result.score)))
            if result.evidence:
                st.write(result.evidence)

    st.subheader("Markdown 投研报告")
    st.markdown(report)
else:
    st.info("输入主题后点击生成。第一版 demo 使用公开 RSS 和规则评分，适合作品集演示；真实投研需接入合规 API、财务数据库和回测。")
