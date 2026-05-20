from __future__ import annotations

from collections import Counter
from datetime import datetime

from app.config import get_settings


def has_llm_access() -> bool:
    return bool(get_settings().openai_api_key)


def fallback_case_extraction(user_input: str) -> dict:
    return {
        "title": user_input[:200],
        "company_name": "待补充",
        "industry": "",
        "city": "",
        "product": "",
        "deal_size": None,
        "summary": user_input,
        "key_points": [],
    }


def fallback_opening(customer, case=None) -> str:
    lines = [
        f"你好，我是你的业务助理，想和你快速确认一下 {customer.company or customer.name} 目前的重点。",
        f"我看到你现在的状态是 {customer.status or '未定义'}。",
    ]
    if case:
        lines.append(f"我们之前在 {case.company_name} 的 {case.title} 有类似经验。")
    lines.append("方便聊下最近最紧急的目标、卡点和时间表吗？")
    return "\n".join(lines)


def fallback_customer_intel(company_name: str, news: list[dict]) -> str:
    if not news:
        return f"未找到 {company_name} 的公开新闻，建议先从行业、组织架构和项目节点切入。"

    top_titles = "；".join(item.get("title", "") for item in news[:3] if item.get("title"))
    return (
        f"{company_name} 的公开信息可优先关注：{top_titles}。"
        "建议围绕近期动作、预算窗口、组织变化和采购周期继续追问。"
    )


def fallback_visit_summary(transcript: str) -> dict:
    summary = transcript[:240] if transcript else "未提供可总结内容"
    actions = []
    for part in transcript.splitlines():
        cleaned = part.strip("-• \t")
        if cleaned and len(actions) < 5:
            actions.append({"action": cleaned[:120], "status": "open"})
    return {
        "summary": summary,
        "key_people": [],
        "action_items": actions,
    }


def fallback_meddic_review(customer, records: list) -> dict:
    history = len(records)
    score = 40
    if customer.notes:
        score += 10
    if customer.meddic_json:
        score += 10
    if history:
        score += min(25, history * 5)
    if customer.status in {"negotiation", "won"}:
        score += 10
    score = min(score, 95)

    gaps = []
    actions = []
    if not customer.meddic_json or not customer.meddic_json.get("metrics"):
        gaps.append("metrics")
        actions.append("补齐业务指标和目标口径")
    if not customer.meddic_json or not customer.meddic_json.get("economic_buyer"):
        gaps.append("economic_buyer")
        actions.append("确认经济决策者和预算链路")
    if not customer.meddic_json or not customer.meddic_json.get("decision_process"):
        gaps.append("decision_process")
        actions.append("梳理决策流程和关键节点")
    if not customer.meddic_json or not customer.meddic_json.get("pain_points"):
        gaps.append("pain_points")
        actions.append("明确当前痛点和业务优先级")

    return {
        "metrics": customer.meddic_json.get("metrics", {}) if customer.meddic_json else {},
        "economic_buyer": customer.meddic_json.get("economic_buyer", {})
        if customer.meddic_json
        else {},
        "decision_criteria": customer.meddic_json.get("decision_criteria", {})
        if customer.meddic_json
        else {},
        "decision_process": customer.meddic_json.get("decision_process", {})
        if customer.meddic_json
        else {},
        "pain_points": customer.meddic_json.get("pain_points", {})
        if customer.meddic_json
        else {},
        "champion": customer.meddic_json.get("champion", {}) if customer.meddic_json else {},
        "health_score": score,
        "overall_gaps": gaps,
        "recommended_actions": actions,
        "last_review_at": datetime.utcnow().isoformat(),
    }


def fallback_business_summary(engagements: list, artifacts: list) -> dict:
    stage_counts = Counter(getattr(item, "stage", "") for item in engagements)
    artifact_counts = Counter(getattr(item, "artifact_type", "") for item in artifacts)
    active = [item for item in engagements if getattr(item, "status", "") not in {"closed", "lost"}]
    next_actions = []
    for item in active:
        for action in (getattr(item, "next_actions", None) or []):
            next_actions.append({"engagement_id": str(item.id), "name": item.name, **action})
    risks = []
    for item in active:
        for risk in (getattr(item, "risks", None) or []):
            risks.append({"engagement_id": str(item.id), "name": item.name, **risk})
    return {
        "stages": dict(stage_counts),
        "active_engagements": len(active),
        "open_risks": len(risks),
        "next_actions": next_actions[:20],
        "artifact_types": dict(artifact_counts),
    }

