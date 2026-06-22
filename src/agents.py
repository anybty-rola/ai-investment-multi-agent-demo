from __future__ import annotations

import math
import re
from collections import Counter

from .data_sources import DEFAULT_SOURCE_CATALOG, fetch_google_news_rss, source_plan_for_topic
from .llm import DeepSeekClient, LLMConfig
from .models import AgentResult, ResearchState, SourceItem


POSITIVE_TERMS = {
    "surge",
    "beat",
    "growth",
    "upgrade",
    "strong",
    "record",
    "demand",
    "partnership",
    "approval",
    "subsidy",
    "breakthrough",
    "expansion",
    "rally",
    "上调",
    "增长",
    "突破",
    "需求",
    "补贴",
    "政策支持",
    "景气",
    "创新",
    "扩产",
    "盈利",
    "复苏",
}

NEGATIVE_TERMS = {
    "miss",
    "decline",
    "risk",
    "probe",
    "ban",
    "lawsuit",
    "slowdown",
    "cut",
    "weak",
    "shortage",
    "inflation",
    "tariff",
    "下滑",
    "风险",
    "调查",
    "禁令",
    "诉讼",
    "放缓",
    "降价",
    "裁员",
    "通胀",
    "关税",
    "短缺",
}

EVENT_PATTERNS = {
    "policy": r"policy|regulation|subsidy|tariff|ban|export control|政策|监管|补贴|关税|禁令|出口管制",
    "earnings": r"earnings|revenue|profit|margin|guidance|财报|收入|利润|毛利率|指引",
    "supply_chain": r"supply chain|capacity|shipment|inventory|供应链|产能|出货|库存",
    "technology": r"ai|chip|gpu|hbm|model|compute|semiconductor|人工智能|芯片|算力|半导体",
    "macro": r"rate|inflation|fed|cpi|pmi|weather|oil|利率|通胀|美联储|天气|能源|原油",
    "capital_market": r"ipo|buyback|valuation|multiple|analyst|fund|估值|回购|基金|投行|评级",
}

INDUSTRY_KEYWORDS = {
    "AI算力与半导体": ["ai", "gpu", "hbm", "semiconductor", "chip", "nvidia", "算力", "半导体", "芯片", "英伟达"],
    "新能源与电力设备": ["energy", "battery", "solar", "ev", "grid", "新能源", "电池", "光伏", "电网"],
    "医药与医疗器械": ["healthcare", "drug", "fda", "medical", "device", "医药", "医疗器械", "创新药"],
    "消费电子": ["consumer electronics", "smartphone", "wearable", "headphone", "消费电子", "耳机", "手机"],
    "低空经济与机器人": ["drone", "robot", "evtol", "automation", "机器人", "无人机", "低空经济"],
}

COMPANY_UNIVERSE = {
    "AI算力与半导体": ["NVDA", "AMD", "TSM", "ASML", "MU", "AVGO", "SMIC", "寒武纪", "中际旭创"],
    "新能源与电力设备": ["TSLA", "CATL", "BYD", "ENPH", "隆基绿能", "阳光电源"],
    "医药与医疗器械": ["PFE", "LLY", "MRNA", "ISRG", "联影医疗", "迈瑞医疗"],
    "消费电子": ["AAPL", "SONY", "SAMSUNG", "BASEUS", "安克创新", "小米集团"],
    "低空经济与机器人": ["DJI", "IRBT", "TER", "优必选", "亿航智能"],
}


def clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


class SourceDiscoveryAgent:
    name = "SourceDiscoveryAgent"

    def run(self, state: ResearchState) -> AgentResult:
        plan = source_plan_for_topic(state.topic)
        evidence = []
        for bucket, source_types in plan.items():
            readable = "、".join(
                f"{source_type}({DEFAULT_SOURCE_CATALOG[source_type]['weight']})" for source_type in source_types
            )
            evidence.append(f"{bucket}: {readable}")
        result = AgentResult(
            agent=self.name,
            summary="建立分层数据源计划：官方/机构/新闻为核心，社媒作为辅助信号而非直接决策依据。",
            score=0.8,
            evidence=evidence,
            data={"plan": plan, "catalog": DEFAULT_SOURCE_CATALOG},
        )
        state.add_result(result)
        return result


class NewsAndEventCollectorAgent:
    name = "NewsAndEventCollectorAgent"

    def run(self, state: ResearchState) -> AgentResult:
        query = f"{state.topic} investment industry outlook"
        sources = fetch_google_news_rss(query, region=state.region, limit=12)
        if not sources:
            sources = self._fallback_sources(state)
        state.sources.extend(sources)
        evidence = [f"{item.source}: {item.title}" for item in sources[:8]]
        result = AgentResult(
            agent=self.name,
            summary=f"收集到 {len(sources)} 条公开新闻/事件候选信息。",
            score=min(1.0, len(sources) / 10),
            evidence=evidence,
            data={"source_count": len(sources)},
        )
        state.add_result(result)
        return result

    def _fallback_sources(self, state: ResearchState) -> list[SourceItem]:
        return [
            SourceItem(
                title=f"{state.topic}: AI infrastructure demand remains a key market theme",
                url="demo://fallback/ai-infrastructure",
                source="Demo fallback",
                summary="Fallback item used when live RSS is unavailable.",
                credibility=0.45,
            ),
            SourceItem(
                title=f"Policy and supply chain risks remain important for {state.topic}",
                url="demo://fallback/policy-risk",
                source="Demo fallback",
                summary="Fallback item used when live RSS is unavailable.",
                credibility=0.45,
            ),
        ]


class SentimentAndEventAgent:
    name = "SentimentAndEventAgent"

    def run(self, state: ResearchState) -> AgentResult:
        text_units = [f"{item.title} {item.summary}" for item in state.sources]
        pos = 0
        neg = 0
        event_counts: Counter[str] = Counter()
        evidence = []
        for text in text_units:
            lower = text.lower()
            p = sum(1 for term in POSITIVE_TERMS if term.lower() in lower)
            n = sum(1 for term in NEGATIVE_TERMS if term.lower() in lower)
            pos += p
            neg += n
            for event, pattern in EVENT_PATTERNS.items():
                if re.search(pattern, lower, flags=re.I):
                    event_counts[event] += 1
            if p or n:
                direction = "正向" if p >= n else "负向"
                evidence.append(f"{direction}: {text[:140]}")
        score = clamp((pos - neg) / max(1, pos + neg))
        result = AgentResult(
            agent=self.name,
            summary=f"情绪分数 {score:.2f}；正向词 {pos}，负向词 {neg}；高频事件：{dict(event_counts.most_common(5))}",
            score=score,
            evidence=evidence[:8],
            data={"positive_terms": pos, "negative_terms": neg, "events": dict(event_counts)},
        )
        state.add_result(result)
        return result


class MacroAgent:
    name = "MacroAgent"

    def run(self, state: ResearchState) -> AgentResult:
        topic = state.topic.lower()
        factors = {
            "policy_support": 0.2,
            "rate_pressure": -0.1,
            "geopolitical_risk": -0.1,
            "weather_or_supply_shock": 0.0,
            "technology_cycle": 0.2,
        }
        if any(k in topic for k in ["ai", "chip", "semiconductor", "gpu", "算力", "半导体"]):
            factors["policy_support"] += 0.15
            factors["technology_cycle"] += 0.25
            factors["geopolitical_risk"] -= 0.15
        if any(k in topic for k in ["energy", "agriculture", "weather", "能源", "农业", "天气"]):
            factors["weather_or_supply_shock"] += 0.2
        score = clamp(sum(factors.values()) / len(factors) * 2)
        evidence = [f"{k}: {v:+.2f}" for k, v in factors.items()]
        result = AgentResult(
            agent=self.name,
            summary=f"宏观环境综合评分 {score:.2f}，科技周期和政策支持是主要正向项，利率/地缘是约束项。",
            score=score,
            evidence=evidence,
            data={"factors": factors},
        )
        state.add_result(result)
        return result


class IndustryThesisAgent:
    name = "IndustryThesisAgent"

    def run(self, state: ResearchState) -> AgentResult:
        corpus = " ".join([state.topic] + [s.title + " " + s.summary for s in state.sources]).lower()
        industry_scores: dict[str, float] = {}
        for industry, keywords in INDUSTRY_KEYWORDS.items():
            keyword_hits = sum(1 for kw in keywords if kw.lower() in corpus)
            industry_scores[industry] = keyword_hits / max(1, len(keywords))
        sentiment = state.get("SentimentAndEventAgent")
        macro = state.get("MacroAgent")
        for industry in industry_scores:
            industry_scores[industry] += 0.25 * (sentiment.score if sentiment and sentiment.score else 0)
            industry_scores[industry] += 0.20 * (macro.score if macro and macro.score else 0)
        ranked = sorted(industry_scores.items(), key=lambda x: x[1], reverse=True)
        top_industry, top_score = ranked[0]
        thesis = f"{top_industry} 当前具备较高关注度，主要由主题热度、政策/技术周期和新闻情绪共同驱动。"
        result = AgentResult(
            agent=self.name,
            summary=thesis,
            score=clamp(top_score, 0, 1),
            evidence=[f"{name}: {score:.2f}" for name, score in ranked],
            data={"top_industry": top_industry, "industry_scores": dict(ranked)},
        )
        state.add_result(result)
        return result


class FactorImpactAgent:
    name = "FactorImpactAgent"

    def run(self, state: ResearchState) -> AgentResult:
        events = state.get("SentimentAndEventAgent").data.get("events", {}) if state.get("SentimentAndEventAgent") else {}
        impacts = {}
        for event, count in events.items():
            direction = 1 if event in {"technology", "earnings", "capital_market"} else -0.2
            if event == "policy":
                direction = 0.4
            if event == "macro":
                direction = -0.1
            strength = min(1.0, count / max(1, len(state.sources) / 2))
            impacts[event] = {
                "direction": direction,
                "strength": round(strength, 2),
                "horizon": "1-3个月" if event in {"policy", "macro"} else "3-12个月",
                "explanation": "事件频次和方向由新闻标题/摘要关键词启发式估计，后续应替换为历史数据回归或事件研究。",
            }
        score = sum(v["direction"] * v["strength"] for v in impacts.values()) / max(1, len(impacts))
        result = AgentResult(
            agent=self.name,
            summary=f"识别 {len(impacts)} 类影响因子，综合影响分数 {score:.2f}。",
            score=clamp(score),
            evidence=[f"{k}: direction={v['direction']:+.1f}, strength={v['strength']}, horizon={v['horizon']}" for k, v in impacts.items()],
            data={"impacts": impacts},
        )
        state.add_result(result)
        return result


class CompanyScreeningAgent:
    name = "CompanyScreeningAgent"

    def run(self, state: ResearchState) -> AgentResult:
        industry_result = state.get("IndustryThesisAgent")
        industry = industry_result.data.get("top_industry", "AI算力与半导体") if industry_result else "AI算力与半导体"
        candidates = state.tickers or COMPANY_UNIVERSE.get(industry, [])[:6]
        scored = []
        topic_text = state.topic.lower()
        for ticker in candidates:
            score = 0.5
            if ticker.lower() in topic_text:
                score += 0.2
            if ticker in COMPANY_UNIVERSE.get(industry, []):
                score += 0.2
            scored.append((ticker, round(min(1.0, score), 2)))
        result = AgentResult(
            agent=self.name,
            summary=f"围绕 {industry} 生成候选公司池：{', '.join(t for t, _ in scored)}。",
            score=max([s for _, s in scored], default=0.5),
            evidence=[f"{ticker}: relevance={score}" for ticker, score in scored],
            data={"industry": industry, "candidates": scored},
        )
        state.add_result(result)
        return result


class FundamentalValuationAgent:
    name = "FundamentalValuationAgent"

    def run(self, state: ResearchState) -> AgentResult:
        candidates = state.get("CompanyScreeningAgent").data.get("candidates", []) if state.get("CompanyScreeningAgent") else []
        analyses = {}
        for ticker, relevance in candidates[:6]:
            growth_score = 0.55 + 0.25 * relevance
            valuation_pressure = 0.35 + 0.2 * relevance
            quality_score = 0.5 + 0.2 * relevance
            fair_value_signal = growth_score + quality_score - valuation_pressure
            analyses[ticker] = {
                "business_quality": round(quality_score, 2),
                "growth": round(growth_score, 2),
                "valuation_pressure": round(valuation_pressure, 2),
                "methods_to_apply": ["DCF", "可比公司 P/E", "EV/EBITDA", "P/S", "反向 DCF"],
                "fair_value_signal": round(fair_value_signal, 2),
            }
        best = max(analyses.items(), key=lambda x: x[1]["fair_value_signal"], default=("N/A", {}))
        result = AgentResult(
            agent=self.name,
            summary=f"估值框架已覆盖 DCF、可比公司、EV/EBITDA、P/S、反向 DCF；当前相对最优候选：{best[0]}。",
            score=clamp(best[1].get("fair_value_signal", 0.5), 0, 1) if best[1] else 0.5,
            evidence=[f"{ticker}: {data}" for ticker, data in analyses.items()],
            data={"company_analysis": analyses, "preferred_company": best[0]},
        )
        state.add_result(result)
        return result


class RiskAgent:
    name = "RiskAgent"

    def run(self, state: ResearchState) -> AgentResult:
        risk_map = {
            "数据风险": "社媒与新闻标题易噪声化，需加入来源可信度和交叉验证。",
            "估值风险": "AI/成长行业估值通常包含高预期，需做反向 DCF 和敏感性分析。",
            "政策风险": "出口管制、反垄断、数据安全、产业补贴变化会改变行业利润分配。",
            "周期风险": "库存周期、资本开支周期和利率周期可能导致短期回撤。",
            "模型风险": "LLM 可能幻觉，因果关系不能只由新闻共现判断。",
        }
        # More risks lower the score; mitigated by source credibility.
        avg_credibility = sum(s.credibility for s in state.sources) / max(1, len(state.sources))
        score = clamp(avg_credibility - 0.25, 0, 1)
        result = AgentResult(
            agent=self.name,
            summary=f"风险审查完成，平均来源可信度 {avg_credibility:.2f}；建议所有结论必须保留引用和置信度。",
            score=score,
            evidence=[f"{k}: {v}" for k, v in risk_map.items()],
            data={"risks": risk_map, "avg_credibility": avg_credibility},
        )
        state.add_result(result)
        return result


class DebateAndDecisionAgent:
    name = "DebateAndDecisionAgent"

    def run(self, state: ResearchState) -> AgentResult:
        industry = state.get("IndustryThesisAgent")
        factor = state.get("FactorImpactAgent")
        valuation = state.get("FundamentalValuationAgent")
        risk = state.get("RiskAgent")
        signal = 0.30
        for item, weight in [(industry, 0.25), (factor, 0.20), (valuation, 0.25), (risk, 0.15)]:
            if item and item.score is not None:
                signal += weight * item.score
        signal = clamp(signal, 0, 1)
        if signal >= 0.68:
            decision = "BUY / 积极关注"
        elif signal >= 0.48:
            decision = "WATCH / 建议跟踪"
        else:
            decision = "AVOID / 暂不建议"
        bull = "Bull: 行业技术周期与信息热度较强，若基本面验证成立，龙头公司具备超额收益机会。"
        bear = "Bear: 数据源仍偏新闻与启发式评分，估值、政策和周期风险需要用财务数据与历史回测进一步验证。"
        pm = f"PM: 综合评分 {signal:.2f}，结论为 {decision}。"
        result = AgentResult(
            agent=self.name,
            summary=pm,
            score=signal,
            evidence=[bull, bear, pm],
            data={"decision": decision, "confidence": round(signal, 2)},
        )
        state.add_result(result)
        return result


class DeepSeekSynthesisAgent:
    name = "DeepSeekSynthesisAgent"

    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config

    def run(self, state: ResearchState) -> AgentResult:
        if not self.llm_config.enabled:
            result = AgentResult(
                agent=self.name,
                summary="未启用 DeepSeek：未提供 API Key，已跳过大模型增强分析。",
                score=None,
                evidence=[],
                data={"enabled": False},
            )
            state.add_result(result)
            return result

        system_prompt = (
            "你是一名严谨的买方投研分析师和投资委员会秘书。"
            "你需要基于给定的多智能体输出做综合研判。"
            "不要编造未提供的数据；必须区分事实、推断和待验证项。"
            "输出中文，结构化、简洁、适合作为投研报告摘要。"
        )
        user_prompt = self._build_prompt(state)
        try:
            content = DeepSeekClient(self.llm_config).chat(system_prompt, user_prompt)
            result = AgentResult(
                agent=self.name,
                summary="DeepSeek 已完成综合研判。",
                score=None,
                evidence=[content],
                data={"enabled": True, "model": self.llm_config.model, "content": content},
            )
        except Exception as exc:
            result = AgentResult(
                agent=self.name,
                summary=f"DeepSeek 调用失败：{exc}",
                score=None,
                evidence=[],
                data={"enabled": True, "error": str(exc)},
            )
        state.add_result(result)
        return result

    def _build_prompt(self, state: ResearchState) -> str:
        agent_lines = []
        for result in state.results:
            agent_lines.append(f"## {result.agent}")
            agent_lines.append(f"Summary: {result.summary}")
            if result.score is not None:
                agent_lines.append(f"Score: {result.score:.2f}")
            if result.evidence:
                agent_lines.append("Evidence:")
                for evidence in result.evidence[:5]:
                    agent_lines.append(f"- {evidence}")
        source_lines = []
        for source in state.sources[:10]:
            source_lines.append(f"- {source.source}: {source.title} | credibility={source.credibility:.2f} | {source.url}")
        return f"""
研究主题：{state.topic}
区域：{state.region}
候选公司：{', '.join(state.tickers) if state.tickers else '未指定'}

请基于以下多智能体输出，生成：
1. 投研结论：BUY / WATCH / AVOID，并说明置信度。
2. 三条最关键的看多依据。
3. 三条最关键的看空/风险依据。
4. 对候选公司的优先级排序和理由。
5. 还需要补充验证的真实数据清单。
6. 适合放进作品集的项目亮点总结。

多智能体输出：
{chr(10).join(agent_lines)}

信息源：
{chr(10).join(source_lines)}
""".strip()
