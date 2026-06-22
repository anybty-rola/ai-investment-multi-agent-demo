# AI 投研决策系统架构

## 你的原始想法存在的问题

1. 数据源过宽

微信公众号、小红书、X、Facebook、YouTube、抖音、微博、百度、新闻媒体、投行会议、基金路演全部接入，第一版会失控。很多平台有登录、反爬、版权、API 限制，不适合作为系统原型的核心依赖。

建议：

- 第一阶段：公开新闻 RSS、公司公告、SEC/交易所公告、央行/政策官网、少量人工导入会议纪要。
- 第二阶段：YouTube Data API、GDELT、FRED、OpenBB、FMP、SEC EDGAR。
- 第三阶段：合规接入 X、微博、小红书、微信公众号数据，或人工导入导出的文本。

2. 情绪不等于投资结论

“正向/负向情绪”只能说明短期市场叙事，不能直接推出买入卖出。

建议增加中间层：

- 事件类型：政策、业绩、供需、技术、竞争、融资、监管。
- 影响方向：正向/负向。
- 影响强度：低/中/高。
- 影响期限：短期、3-12 个月、长期。
- 证据质量：官方、机构、媒体、专家、普通社媒。

3. 宏观信息需要分层

天气、民生、小道新闻确实可能影响经济，但要防止噪声过大。

建议：

- 核心宏观：利率、通胀、PMI、就业、汇率、财政政策、产业政策。
- 行业宏观：能源价格、物流、库存、资本开支、订单周期。
- 辅助另类数据：天气、招聘、社媒热度、搜索指数。

4. 多因子分析不能只靠 LLM

相关性、影响程度、时间预测需要量化验证。

建议：

- MVP：启发式评分。
- 第二阶段：事件研究、滞后相关、滚动回归、Granger causality。
- 第三阶段：因子回测、IC/RankIC、行业轮动模型。

5. 公司估值不能“市面上流行的估值都来一遍”而不筛选

不同公司适合不同估值：

- 成熟盈利公司：DCF、P/E、EV/EBITDA。
- 高成长 SaaS/AI 公司：P/S、Rule of 40、EV/Sales、反向 DCF。
- 周期公司：PB、EV/EBITDA、周期归一化盈利。
- 银行/保险：PB、ROE、净息差、资本充足率。

## MVP 架构

```text
User Topic
  |
  v
SourceDiscoveryAgent
  |
  v
NewsAndEventCollectorAgent
  |
  v
SentimentAndEventAgent
  |
  +--> MacroAgent
  |
  v
IndustryThesisAgent
  |
  v
FactorImpactAgent
  |
  v
CompanyScreeningAgent
  |
  v
FundamentalValuationAgent
  |
  v
RiskAgent
  |
  v
DebateAndDecisionAgent
  |
  v
ReportAgent
```

## 数据源建议

### 第一阶段优先源

- Google News RSS / Bing News Search
- 公司公告 / SEC EDGAR / HKEX / 巨潮资讯
- 央行、发改委、工信部、统计局、财政部、NDRC、MIIT
- FRED、World Bank、IMF、OECD
- Yahoo Finance / Stooq / OpenBB

### 第二阶段增强源

- YouTube Data API：英伟达、AMD、TSMC、基金经理访谈、投行会议公开视频
- GDELT：全球新闻事件数据库
- Serper / Tavily / Bocha：搜索 API
- FMP / Alpha Vantage：财务报表和估值数据
- Open-Meteo：天气和气候变量

### 第三阶段社媒源

- 微信公众号：建议人工导出文章链接/文本，或使用合规内容 API。
- 小红书/抖音/微博：建议作为舆情热度，不直接作为投资事实。
- X/Facebook/Reddit：可用于专家观点、散户情绪和风险预警，但需要 API 与风控。

## 后续迭代路线

### V0.1：当前系统原型

- 公开新闻抓取。
- 正则/词典情绪。
- 行业评分。
- 候选公司池。
- 估值框架。
- 风险审查。
- 多空辩论。
- Markdown 报告。

### V0.2：接入 DeepSeek

- 每个 Agent 从规则摘要升级为 LLM 推理。
- 加入 Prompt 模板。
- 强制输出 JSON。
- 加入引用和置信度。

### V0.3：财务数据与估值

- 接入 yfinance / FMP / OpenBB。
- 拉取利润表、资产负债表、现金流。
- 生成 DCF、可比公司、反向 DCF。
- 输出估值区间。

### V0.4：RAG 知识库

- 导入财报、路演、会议纪要、行业研报。
- 使用 BM25 + 向量检索。
- 加入 Fact Checker Agent。

### V0.5：多因子和回测

- 构建行业/公司因子库。
- 计算事件滞后影响。
- 输出 IC、RankIC、收益、最大回撤、夏普比率。

### V1.0：可演示的投研决策平台

- Streamlit 或 Next.js 前端。
- 一键生成 HTML/PDF 报告。
- 支持中英文。
- 支持 `/industry`、`/company`、`/bull-bear`、`/report` 命令。
