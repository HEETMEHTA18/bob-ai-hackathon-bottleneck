"""
Bottleneck — Grid Operations Advisor Copilot.

Transforms the Gridkavach Gemini copilot into a grounded Grid Operations Advisor.

Rules:
  - Must ONLY use structured backend data — never invent sensor values,
    predictions, incidents, or operational actions.
  - Falls back to deterministic template responses when no LLM key is available.
  - The application must work without any external LLM key.
"""
from __future__ import annotations
import os
import re
from typing import Optional
from datetime import datetime

from backend.bottleneck.contracts import RiskRankingEntry, RiskAssessment


# ─── LLM key detection (reuse Gridkavach pattern) ────────────────────────────

_GEMINI_KEY: Optional[str] = None
_GEMINI_CONFIGURED = False


def _ensure_gemini():
    global _GEMINI_KEY, _GEMINI_CONFIGURED
    if _GEMINI_CONFIGURED:
        return
    _GEMINI_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if _GEMINI_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=_GEMINI_KEY)
        except Exception:
            _GEMINI_KEY = None
    _GEMINI_CONFIGURED = True


def _has_llm_key() -> bool:
    _ensure_gemini()
    return bool(_GEMINI_KEY)


# ─── System prompt for Bottleneck domain ─────────────────────────────────────

GRIDSHIELD_SYSTEM_PROMPT = """You are Bottleneck AI — an expert Grid Operations Advisor for a power utility.
You help field supervisors and control-room engineers make fast, accurate decisions about grid equipment failures.

## Response Format
1. Use markdown: headers (###), tables, **bold** key numbers.
2. Be direct and actionable. Lead with the most critical finding.
3. Never invent sensor values, statistics, probabilities, or operational actions.
4. Reference only the structured data provided in context.
5. End each response with a clear recommended action.
6. Keep responses under 250 words — operators need fast answers.

## Your expertise covers
- Transformer, breaker, feeder, recloser, switch, capacitor bank failure patterns
- Grid impact assessment (customers, critical facilities)
- Weather-related risk (thermal stress, storm exposure)
- Maintenance prioritisation and crew pre-positioning
- Incident history interpretation

## Tone
Professional, concise, operational. Like a senior reliability engineer briefing the control room.
Do NOT use renewable energy (solar/wind/battery) terminology."""


def _build_asset_context(entry: RiskRankingEntry) -> str:
    r = entry.risk
    a = entry.asset
    p = entry.prediction
    g = entry.grid_impact
    w = entry.weather
    m = entry.maintenance

    ctx = f"""## Asset: {a.name} ({a.id})
- Type: {a.asset_type} | Region: {a.region} | Age: {a.age_years:.0f} years
- Status: {a.status} | Criticality: {a.criticality:.2f} | Redundancy: {a.redundancy_level:.2f}

## Risk Assessment
- **Risk Score: {r.risk_score:.0f}/100 — {r.risk_level.upper()}**
- 24h Failure Probability: {r.failure_probability_24h:.0%}
- 72h Failure Probability: {r.failure_probability_72h:.0%}
- Health Score: {r.health_score:.0f}/100
- Anomaly Score: {r.anomaly_score:.2f}

## Grid Impact
- Customers at Risk: {g.customers_at_risk:,}
- Critical Facilities at Risk: {g.critical_facilities_at_risk}
- Downstream Assets: {g.downstream_assets}
- Grid Impact Score: {g.grid_impact_score:.2f}

## Weather Exposure
- Temperature: {w.temperature:.1f}°C | Wind: {w.wind_speed:.1f} m/s
- Storm Severity: {w.storm_severity:.2f} | Heatwave: {w.heatwave_indicator}
- Severe Weather: {w.severe_weather_indicator}
- Exposure Score: {w.weather_exposure_score:.2f}

## Top Risk Factors
{chr(10).join(f'- {f}' for f in p.top_factors)}

## Recommended Action
- Priority: {m.priority_level.upper()} #{m.priority}
- Action: {m.recommended_action}
- Window: {m.recommended_window}
- Assigned Crew: {m.assigned_crew_id or 'Unassigned'}
"""
    return ctx


def _ask_gemini_gridshield(message: str, context: str, history: list) -> Optional[str]:
    """Call Gemini with Bottleneck grounded context."""
    if not _has_llm_key():
        return None
    try:
        import google.generativeai as genai
        full_system = f"{GRIDSHIELD_SYSTEM_PROMPT}\n\n## Current Data\n{context}"
        gemini_history = []
        for msg in history[-6:]:
            role = "user" if msg.get("role") == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg.get("content", "")]})
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=full_system)
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(
            message,
            generation_config=genai.GenerationConfig(
                temperature=0.2, top_p=0.85, max_output_tokens=512
            ),
        )
        return response.text
    except Exception as e:
        print(f"[Bottleneck Copilot Gemini error] {e}")
        return None


# ─── Intent detection (Bottleneck domain) ────────────────────────────────────

_INTENT_ASSET    = re.compile(r'\b(TR|BR|FD|RC|SW|CB)-\d+\b', re.I)
_INTENT_RISK     = re.compile(r'\b(risk|score|critical|danger|fail|probability|predict)\b', re.I)
_INTENT_MAINT    = re.compile(r'\b(maintenance|inspect|repair|action|recommend|schedule)\b', re.I)
_INTENT_CREW     = re.compile(r'\b(crew|team|dispatch|position|assign|who)\b', re.I)
_INTENT_WEATHER  = re.compile(r'\b(weather|storm|temperature|heat|wind|rain)\b', re.I)
_INTENT_SCENARIO = re.compile(r'\b(scenario|what.if|storm|heatwave|degrad)\b', re.I)
_INTENT_SUMMARY  = re.compile(r'\b(summary|overview|status|dashboard|all|top|worst|how many)\b', re.I)
_INTENT_HELP     = re.compile(r'\b(help|what can|capabilities|how do|hi|hello|hey)\b', re.I)


def _detect_intent(msg: str) -> str:
    if _INTENT_HELP.search(msg):
        return "help"
    if _INTENT_SCENARIO.search(msg):
        return "scenario"
    if _INTENT_CREW.search(msg):
        return "crew"
    if _INTENT_MAINT.search(msg):
        return "maintenance"
    if _INTENT_WEATHER.search(msg):
        return "weather"
    if _INTENT_ASSET.search(msg):
        return "asset"
    if _INTENT_RISK.search(msg):
        return "risk"
    if _INTENT_SUMMARY.search(msg):
        return "summary"
    return "general"


# ─── Deterministic fallback responses ────────────────────────────────────────

def _fallback_help() -> str:
    return (
        "### Bottleneck AI — Grid Operations Advisor\n\n"
        "I can help with:\n\n"
        "| Topic | Example |\n|---|---|\n"
        "| Asset risk | \"Why is TR-1042 critical?\" |\n"
        "| Maintenance | \"What action is needed for TR-1042?\" |\n"
        "| Crew plan | \"Which crew is assigned to TR-1042?\" |\n"
        "| Weather | \"How does the storm affect North assets?\" |\n"
        "| Dashboard | \"What are the top 5 critical assets?\" |\n"
        "| Scenarios | \"What happens if a severe storm hits?\" |\n\n"
        "I only use verified backend data — I never invent statistics."
    )


def _fallback_summary(ranking: list) -> str:
    critical = [e for e in ranking if e.risk.risk_level == "critical"]
    high     = [e for e in ranking if e.risk.risk_level == "high"]
    total_customers = sum(e.risk.customers_at_risk for e in critical + high)
    total_fac       = sum(e.risk.critical_facilities_at_risk for e in critical + high)

    top3 = ranking[:3]
    lines = "\n".join(
        f"| {e.rank} | {e.asset.name} ({e.asset.id}) | {e.risk.risk_score:.0f} | "
        f"{e.risk.failure_probability_24h:.0%} | {e.maintenance.priority_level.upper()} |"
        for e in top3
    )
    return (
        f"### Grid Status Summary — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"- **Critical assets:** {len(critical)}\n"
        f"- **High-risk assets:** {len(high)}\n"
        f"- **Customers at risk:** {total_customers:,}\n"
        f"- **Critical facilities at risk:** {total_fac}\n\n"
        f"**Top 3 Assets by Risk:**\n\n"
        f"| Rank | Asset | Risk | 24h Prob | Action |\n|---|---|---|---|---|\n"
        f"{lines}\n\n"
        f"**Recommended:** Prioritise immediate inspection of {top3[0].asset.name if top3 else 'N/A'}."
    )


def _fallback_asset(entry: RiskRankingEntry) -> str:
    r = entry.risk
    a = entry.asset
    m = entry.maintenance
    g = entry.grid_impact
    factors = "\n".join(f"- {f}" for f in r.top_factors)
    return (
        f"### {a.name} ({a.id}) — {r.risk_level.upper()} RISK\n\n"
        f"| Metric | Value |\n|---|---|\n"
        f"| Risk Score | **{r.risk_score:.0f}/100** |\n"
        f"| Health Score | {r.health_score:.0f}/100 |\n"
        f"| 24h Failure Prob | **{r.failure_probability_24h:.0%}** |\n"
        f"| 72h Failure Prob | {r.failure_probability_72h:.0%} |\n"
        f"| Customers at Risk | {g.customers_at_risk:,} |\n"
        f"| Critical Facilities | {g.critical_facilities_at_risk} |\n"
        f"| Anomaly Score | {r.anomaly_score:.2f} |\n\n"
        f"**Why risky:**\n{factors}\n\n"
        f"**Action:** {m.recommended_action}\n"
        f"**Window:** {m.recommended_window} | Crew: {m.assigned_crew_id or 'Unassigned'}"
    )


def _fallback_maintenance(entry: RiskRankingEntry) -> str:
    m = entry.maintenance
    r = entry.risk
    return (
        f"### Maintenance Plan — {entry.asset.name}\n\n"
        f"- **Priority:** {m.priority_level.upper()} #{m.priority}\n"
        f"- **Action:** {m.recommended_action}\n"
        f"- **Window:** {m.recommended_window}\n"
        f"- **Duration:** ~{m.estimated_duration_hours:.0f} hours\n"
        f"- **Crew:** {m.assigned_crew_id or 'Unassigned'}\n"
        f"- **Reason:** {m.reason}\n\n"
        f"Risk score: {r.risk_score:.0f}/100 | 24h failure probability: {r.failure_probability_24h:.0%}"
    )


# ─── Main advisor function ────────────────────────────────────────────────────

def bottleneck_advisor(
    message: str,
    ranking: list,
    history: Optional[list] = None,
) -> str:
    """
    Main entry point for Bottleneck AI Copilot.

    ranking: output of service.get_full_ranking()
    history: conversation history list[{role, content}]
    """
    intent = _detect_intent(message)
    history = history or []

    # Find referenced asset (if any)
    asset_match = _INTENT_ASSET.search(message.upper())
    entry: Optional[RiskRankingEntry] = None
    if asset_match:
        asset_id = asset_match.group(0).upper()
        entry = next((e for e in ranking if e.asset.id == asset_id), None)

    # If no specific asset and intent is asset-specific, default to #1 critical
    if not entry and intent in ("asset", "risk", "maintenance", "crew"):
        entry = ranking[0] if ranking else None

    # Build grounded context for LLM
    if entry:
        ctx = _build_asset_context(entry)
    else:
        top5 = ranking[:5]
        ctx = "\n".join(_build_asset_context(e) for e in top5)

    # Try LLM first
    llm_response = _ask_gemini_gridshield(message, ctx, history)
    if llm_response:
        return llm_response

    # Deterministic fallback
    if intent == "help":
        return _fallback_help()
    if intent == "summary":
        return _fallback_summary(ranking)
    if entry:
        if intent in ("maintenance",):
            return _fallback_maintenance(entry)
        return _fallback_asset(entry)
    return _fallback_summary(ranking)
