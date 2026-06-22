# GitHub 开源投研 Agent 项目调研

## 1. mcy1123/ms-agent / FinResearch

定位：金融研究报告自动生成系统。

可借鉴点：

- 多章节并行生成。
- RAG 检索：BM25 + 向量检索 + RRF 融合 + Rerank。
- 表格检索与财务数据检索分离。
- DeepSeek 兼容 OpenAI API。

对本项目的启发：

- 报告生成不要只靠一个 Agent，应拆成行业、公司、估值、风险、结论多个章节。
- 后续可以加入 RAG，把投行会议纪要、路演材料、财报、行业报告放入知识库。

## 2. RUC-NLPIR/FinSight

定位：面向真实金融深度研究的一键式报告系统。

可借鉴点：

- Data Collector -> Deep Search -> Data Analyzer -> Report Generator 的多阶段流程。
- 支持多搜索源、网页抓取、图表和报告生成。
- 强调 source validation 和 publication-ready report。

对本项目的启发：

- 你的系统必须重视来源验证，尤其是社媒、小红书、微博、X、YouTube 等数据。
- 需要把“信息抓取”和“投资判断”分开，中间增加数据清洗、事件抽取、置信度评分。

## 3. TradingAgents

定位：模拟交易公司中的分析师、研究员、交易员、风险经理和组合经理。

可借鉴点：

- Fundamental Analyst、Sentiment Analyst、Technical Analyst、Bull Researcher、Bear Researcher、Risk Manager、Portfolio Manager。
- Bull/Bear 辩论机制，最后由 Research Manager 或 Portfolio Manager 裁决。
- 使用 LangGraph 维护共享状态。

对本项目的启发：

- 投资建议应由多空辩论后产生，而不是单一 LLM 直接输出。
- 需要显式保留 Bull、Bear、PM 三种视角，让面试官看到你的“决策流程”。

## 4. AI4Finance FinRobot / FinGPT

定位：金融 AI Agent 平台与金融大模型/NLP 框架。

可借鉴点：

- 金融 Chain-of-Thought。
- 多源 LLM、FinGPT、FinRL、金融 NLP。
- 适合做情绪分析、市场预测、风险评估。

对本项目的启发：

- 你研究生期间做过 MD&A tone analysis，可以和 FinGPT/FinNLP 思路结合，形成“财报文本 + 新闻情绪 + 行业事件”的统一情绪分析层。

## 5. Agentic-Analyst/stock-analyst

定位：自动化股票分析与 DCF 模型生成。

可借鉴点：

- Financial Data Agent、Financial Model Agent、News Intelligence Agent、Report Generator Agent、Recommendation Engine。
- 覆盖 DCF、新闻催化、风险、推荐和价格目标。

对本项目的启发：

- 公司分析部分必须补完整估值：DCF、可比公司、EV/EBITDA、P/S、反向 DCF、敏感性分析。
- 你的 MVP 可以先有估值框架，第二阶段补真实 Excel/模型。

## 6. Abelian-Analysis/Agentic-Investing-Framework

定位：基于 Claude Code 和 MCP 工具的投资研究平台。

可借鉴点：

- 60+ 金融工具，包括 SEC filings、options data、patents、clinical trials、Monte Carlo。
- `/bull-v-bear`、`/comps` 等命令化投研工作流。
- Bull/Bear 分别做 DCF，Judge 做 reverse DCF。

对本项目的启发：

- 可以把你的系统做成几个命令：
  - `/discover-industry AI算力`
  - `/screen AI算力 NVDA,AMD,TSM`
  - `/bull-bear NVDA`
  - `/report AI算力`

## 设计取舍

你的原想法非常完整，但如果直接做“全网社媒 + 宏观 + 行业 + 多因子 + 公司 + 估值 + 风险”，工程量会过大，且容易被质疑数据合法性和结论可靠性。

所以本 MVP 采用以下策略：

- 先做投研流程闭环，而不是做全量数据爬虫。
- 社媒先作为“可接入源”，不作为第一版核心数据。
- 决策必须经过风险审查和多空辩论。
- 所有结果保留来源、分数和置信度。
- 后续再补真实财务数据、RAG、回测和 PDF 研报。
