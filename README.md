# AI 投研决策系统

这是一个 AI 投研决策系统原型，参考了 FinResearch、FinSight、TradingAgents、FinRobot、Agentic-Analyst 等开源项目的设计思想，并做了轻量化实现：

- 不做自动交易，只做投研决策支持。
- 不直接依赖高风险社媒爬虫，优先使用公开 RSS、官方公告、新闻源和可替换连接器。
- 保留完整投研证据链：信息源 -> 事件/情绪 -> 宏观与行业 -> 多因子影响 -> 公司筛选 -> 基本面/估值 -> 风险 -> 多空辩论 -> 报告。
- 每个 Agent 都输出结构化结果，便于后续接入 DeepSeek、RAG、数据库、可视化前端和 PDF 研报生成。

## Agent 架构

1. `SourceDiscoveryAgent`
   - 判断给定主题应该优先关注哪些信息源。
   - 对官方来源、新闻媒体、社媒、论坛、短视频等设置可信度权重。

2. `NewsAndEventCollectorAgent`
   - 使用公开 RSS / Google News RSS 抓取新闻标题和摘要。
   - 当前版本不直接抓微信、小红书、X、Facebook、抖音等平台，后续可通过合规 API 或人工导入文件接入。

3. `SentimentAndEventAgent`
   - 使用正则、关键词词典和事件标签识别正向/负向投资情绪。
   - 输出情绪分数、事件类别、证据句。

4. `MacroAgent`
   - 汇总政策、利率、通胀、地缘、天气、能源、供应链等宏观因子。
   - 当前版本使用可解释的规则评分，后续可接 FRED、World Bank、央行公告、天气 API。

5. `IndustryThesisAgent`
   - 根据情绪、宏观、政策、需求、技术周期判断潜力行业。
   - 输出行业吸引力评分和投资假设。

6. `FactorImpactAgent`
   - 对新闻、政策、宏观因子与行业发展的相关性、影响方向、影响强度和时间维度进行评分。

7. `CompanyScreeningAgent`
   - 根据行业主题生成候选公司池。
   - 当前版本内置部分示例公司，后续可接 Wind、同花顺 iFinD、Yahoo Finance、SEC、OpenBB。

8. `FundamentalValuationAgent`
   - 做基本面、产业链位置、估值方法框架。
   - 覆盖 DCF、可比公司、P/E、P/S、EV/EBITDA、反向 DCF 的占位逻辑。

9. `RiskAgent`
   - 评估政策、估值、业绩、竞争、技术、流动性、地缘与数据可信度风险。

10. `DebateAndDecisionAgent`
    - 模拟 Bull / Bear / Portfolio Manager 的多智能体辩论。
    - 输出 BUY / WATCH / AVOID 和置信度。

11. `ReportAgent`
    - 生成 Markdown 研报。

## 快速运行

```bash
cd "e:\Users\cursor agent\ai_investment_multi_agent_demo"
python main.py --topic "AI semiconductor supply chain" --region "global" --tickers "NVDA,AMD,TSM,MU"
```

生成报告：

```text
outputs/research_report.md
```

可选 Streamlit：

```bash
pip install -r requirements-streamlit.txt
streamlit run app.py
```

打开页面后，在左侧栏可以输入：

- 研究主题
- 区域
- 候选股票/公司
- DeepSeek API Key
- DeepSeek Base URL
- 模型：`deepseek-chat` 或 `deepseek-reasoner`
- OpenRouter API Key 与 OpenRouter 模型，例如 `deepseek/deepseek-chat-v3-0324`

API Key 只在当前 Streamlit 会话中传给 DeepSeek 接口，不会写入项目文件。未填写 API Key 时，系统仍会使用规则 Agent 跑完整流程；填写后，会额外生成 `DeepSeekSynthesisAgent` 的大模型增强研判。

命令行也支持 DeepSeek：

```bash
python main.py --topic "AI semiconductor supply chain" --region "global" --tickers "NVDA,AMD,TSM,MU" --deepseek-api-key "你的key"
```

或使用环境变量：

```bash
set DEEPSEEK_API_KEY=你的key
python main.py --topic "AI semiconductor supply chain"
```

## 免责声明

本项目仅用于学习、研究和投研流程演示，不构成任何投资建议，也不应被用于自动交易或真实资金决策。
