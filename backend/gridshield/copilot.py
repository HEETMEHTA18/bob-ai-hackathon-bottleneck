"""
GridShield — Grid Operations Advisor Copilot.

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

from backend.gridshield.contracts import RiskRankingEntry, RiskAssessment


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


# ─── System prompt for GridShield domain ─────────────────────────────────────

GRIDSHIELD_SYSTEM_PROMPT = """You are GridShield AI — an expert Grid Operations Advisor for a power utility.
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
    """Call Gemini with GridShield grounded context."""
    if not _has_llm_key():
        return None
    try:
        import google.generativeai as genai
        full_system = f"{GRIDSHIELD_SYSTEM_PROMPT}\n\n## Current Data\n{context}"
        gemini_history = []
        for msg in history[-6:]:
            role = "user" if msg.get("role") == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg.get("content", "")]})
        model = genai.GenerativeModel("gemini-2.0-flash-lite", system_instruction=full_system)
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(
            message,
            generation_config=genai.GenerationConfig(
                temperature=0.2, top_p=0.85, max_output_tokens=512
            ),
        )
        return response.text
    except Exception as e:
        print(f"[GridShield Copilot Gemini error] {e}")
        return None


# ─── Intent detection (GridShield domain) ────────────────────────────────────

_INTENT_ASSET     = re.compile(r'\b(TR|BR|FD|RC|SW|CB)-\d+\b', re.I)
_INTENT_OUTAGE    = re.compile(r'\b(outage|power\s*cut|blackout|power\s*loss|no\s*power|service\s*disruption)\b', re.I)
_INTENT_COMPARE   = re.compile(r'\b(compare|versus|vs\.?|difference|better|worse|higher|lower)\b', re.I)
_INTENT_RISK      = re.compile(r'\b(risk|score|critical|danger|fail|probability|predict)\b', re.I)
_INTENT_MAINT     = re.compile(r'\b(maintenance|inspect|repair|action|recommend|schedule|prevent)\b', re.I)
_INTENT_CREW      = re.compile(r'\b(crew|team|dispatch|position|assign|who|technician|engineer)\b', re.I)
_INTENT_WEATHER   = re.compile(r'\b(weather|storm|temperature|heat|wind|rain|flood|cyclone)\b', re.I)
_INTENT_SCENARIO  = re.compile(r'\b(scenario|what[.\s]*if|what\s*happens\s*if|simulat|happen\s*if|suppose)\b', re.I)
_INTENT_SUMMARY   = re.compile(r'\b(summary|overview|status|dashboard|how\s*many|count|total|number\s*of)\b', re.I)
_INTENT_HELP      = re.compile(r'\b(help|what\s*can|capabilities|how\s*do|hi|hello|hey|greetings)\b', re.I)
_INTENT_OUT_OF_SCOPE = re.compile(r'\b(stock|weather\s*(?:in|of)\s+(?!north|south|east|west|central)|movie|recipe|sport|music|football|cricket|election|crypto|bitcoin|nft)\b', re.I)


def _detect_intent(msg: str) -> str:
    if _INTENT_OUT_OF_SCOPE.search(msg):
        return "out_of_scope"
    if _INTENT_HELP.search(msg):
        return "help"
    if _INTENT_OUTAGE.search(msg):
        return "outage"
    if _INTENT_COMPARE.search(msg):
        return "comparison"
    if _INTENT_SCENARIO.search(msg):
        return "scenario"
    if _INTENT_SUMMARY.search(msg):
        return "summary"
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
    return "general"


# ─── Deterministic fallback responses ────────────────────────────────────────

def _model_line(entry) -> str:
    """Transparency footer: which ML pipeline produced these numbers."""
    try:
        mv = entry.prediction.model_version
        conf = entry.prediction.confidence
        real = "real XGBoost" if "mock" not in mv else "deterministic mock"
        return f"\n\n*Model: {real} ({mv}, confidence {conf:.0%}) · telemetry 48h + Open-Meteo exposure.*"
    except Exception:
        return ""


def _fallback_help() -> str:
    return (
        "### GridShield AI — Grid Operations Advisor\n\n"
        "I can help with:\n\n"
        "| Topic | Example |\n|---|---|\n"
        "| Asset risk | \"Why is TR-1042 critical?\" |\n"
        "| Outage risk | \"Will there be a power outage?\" |\n"
        "| Maintenance | \"What action is needed for TR-1042?\" |\n"
        "| Crew plan | \"Which crew is assigned to TR-1042?\" |\n"
        "| Weather | \"How does the storm affect North assets?\" |\n"
        "| Compare | \"Compare TR-1042 and BR-2201\" |\n"
        "| Dashboard | \"What are the top 5 critical assets?\" |\n"
        "| Scenarios | \"What happens if a severe storm hits?\" |\n\n"
        "I only use verified backend data — I never invent statistics."
    )


def _fallback_outage(ranking: list) -> str:
    critical = [e for e in ranking if e.risk.risk_level == "critical"]
    high = [e for e in ranking if e.risk.risk_level == "high"]
    total_customers = sum(e.grid_impact.customers_at_risk for e in critical + high)
    total_fac = sum(e.grid_impact.critical_facilities_at_risk for e in critical + high)

    worst = ranking[0] if ranking else None
    if not worst:
        return "No outage risk data available."

    lines = []
    for e in critical[:5]:
        lines.append(
            f"| {e.asset.name} ({e.asset.id}) | **{e.risk.failure_probability_24h:.0%}** | "
            f"{e.grid_impact.customers_at_risk:,} | {e.grid_impact.critical_facilities_at_risk} |"
        )
    rows = "\n".join(lines)

    return (
        f"### Power Outage Risk Assessment — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"**Yes, outage risk is elevated.**\n\n"
        f"| Asset | 24h Failure Prob | Customers | Critical Facilities |\n"
        f"|---|---|---|---|\n{rows}\n\n"
        f"**Total exposure:** {len(critical)} critical + {len(high)} high-risk assets | "
        f"{total_customers:,} customers | {total_fac} critical facilities\n\n"
        f"**Immediate action:** Deploy crew to **{worst.asset.name}** — "
        f"{worst.risk.failure_probability_24h:.0%} failure probability within 24h.\n"
        f"**Window:** {worst.maintenance.recommended_window} | "
        f"Crew: {worst.maintenance.assigned_crew_id or 'TBD'}"
        + _model_line(worst)
    )


def _fallback_summary(ranking: list) -> str:
    critical = [e for e in ranking if e.risk.risk_level == "critical"]
    high     = [e for e in ranking if e.risk.risk_level == "high"]
    total_customers = sum(e.grid_impact.customers_at_risk for e in critical + high)
    total_fac       = sum(e.grid_impact.critical_facilities_at_risk for e in critical + high)

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
        + (_model_line(top3[0]) if top3 else "")
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
        + _model_line(entry)
    )


def _fallback_maintenance(entry: RiskRankingEntry) -> str:
    m = entry.maintenance
    r = entry.risk
    g = entry.grid_impact
    return (
        f"### Maintenance Plan — {entry.asset.name} ({entry.asset.id})\n\n"
        f"- **Priority:** {m.priority_level.upper()} #{m.priority}\n"
        f"- **Action:** {m.recommended_action}\n"
        f"- **Window:** {m.recommended_window}\n"
        f"- **Duration:** ~{m.estimated_duration_hours:.0f} hours\n"
        f"- **Crew:** {m.assigned_crew_id or 'Unassigned'}\n"
        f"- **Reason:** {m.reason}\n\n"
        f"**Impact if deferred:** {g.customers_at_risk:,} customers, "
        f"{g.critical_facilities_at_risk} critical facilities at risk.\n\n"
        f"Risk score: {r.risk_score:.0f}/100 | 24h failure probability: {r.failure_probability_24h:.0%}"
    )


def _fallback_crew(entry: RiskRankingEntry, ranking: list) -> str:
    from backend.gridshield.mock_data import CREWS
    m = entry.maintenance
    crew = next((c for c in CREWS if c.crew_id == m.assigned_crew_id), None)
    others = [
        f"| {e.maintenance.assigned_crew_id} | {e.asset.name} ({e.asset.id}) | "
        f"{e.risk.risk_score:.0f} | {e.maintenance.priority_level.upper()} |"
        for e in ranking[:5] if e.maintenance.assigned_crew_id
    ]
    crew_line = (
        f"- **Crew:** {crew.crew_id} — {crew.name} ({crew.specialty}, {crew.region})\n"
        if crew else "- **Crew:** Unassigned — no available crew matched\n"
    )
    return (
        f"### Crew Assignment — {entry.asset.name} ({entry.asset.id})\n\n"
        f"{crew_line}"
        f"- **Assignment type:** "
        f"{'Dispatch' if m.priority_level == 'immediate' else 'Pre-position' if m.priority_level == 'high' else 'Standby'}\n"
        f"- **Reason:** {m.reason}\n"
        f"- **Window:** {m.recommended_window}\n\n"
        f"**Top-5 crew postings:**\n\n"
        f"| Crew | Asset | Risk | Priority |\n|---|---|---|---|\n"
        + "\n".join(others)
    )


def _fallback_weather(entry: RiskRankingEntry | None, ranking: list, message: str) -> str:
    import re as _re
    region_m = _re.search(r'\b(north|south|east|west|central)\b', message, _re.I)
    if region_m:
        region = region_m.group(1).capitalize()
        entries = [e for e in ranking if e.asset.region == region][:5]
        title = f"Weather Exposure — {region} region"
    elif entry:
        entries = [entry]
        title = f"Weather Exposure — {entry.asset.name}"
    else:
        entries = ranking[:5]
        title = "Weather Exposure — highest-risk assets"
    rows = "\n".join(
        f"| {e.asset.name} ({e.asset.id}) | {e.weather.temperature:.1f}°C | "
        f"{e.weather.wind_speed:.1f} m/s | {e.weather.storm_severity:.2f} | "
        f"{'Yes' if e.weather.severe_weather_indicator else 'No'} | {e.weather.weather_exposure_score:.2f} |"
        for e in entries
    )
    return (
        f"### {title}\n\n"
        f"| Asset | Temp | Wind | Storm | Severe | Exposure |\n"
        f"|---|---|---|---|---|---|\n{rows}\n\n"
        f"**Source:** live Open-Meteo feed when reachable, otherwise deterministic "
        f"regional profile. Exposure blends thermal, wind, precipitation and storm signals."
    )


def _fallback_scenario(ranking: list) -> str:
    from backend.gridshield import service as _svc
    lines = []
    for scenario in ("severe_storm", "heatwave", "asset_degradation"):
        results = _svc.run_scenario(scenario)
        worst = results[0] if results else None
        if worst:
            lines.append(
                f"- **{scenario}:** worst impact {worst.asset_id} "
                f"({worst.risk_before:.0f} → {worst.risk_after:.0f}, "
                f"{worst.risk_level_before} → {worst.risk_level_after})"
            )
    detail = "\n".join(lines) if lines else "- No scenario delta computed."
    return (
        f"### What-If Scenarios (simulated on live ranking)\n\n{detail}\n\n"
        f"Open **Scenarios** to simulate per-asset storm, heatwave or degradation "
        f"effects with before/after risk comparison."
    )


def _fallback_comparison(message: str, ranking: list) -> str:
    """Compare two assets mentioned in the query."""
    asset_matches = _INTENT_ASSET.findall(message.upper())
    entries = []
    for aid in asset_matches:
        found = next((e for e in ranking if e.asset.id == aid), None)
        if found:
            entries.append(found)
    if len(entries) < 2:
        entries = ranking[:2]

    a1, a2 = entries[0], entries[1]
    def row(label, v1, v2):
        return f"| {label} | {v1} | {v2} |"

    return (
        f"### Asset Comparison — {a1.asset.name} vs {a2.asset.name}\n\n"
        f"| Metric | {a1.asset.name} ({a1.asset.id}) | {a2.asset.name} ({a2.asset.id}) |\n"
        f"|---|---|---|\n"
        f"{row('Risk Score', f'{a1.risk.risk_score:.0f}/100', f'{a2.risk.risk_score:.0f}/100')}\n"
        f"{row('Risk Level', a1.risk.risk_level.upper(), a2.risk.risk_level.upper())}\n"
        f"{row('24h Failure Prob', f'{a1.risk.failure_probability_24h:.0%}', f'{a2.risk.failure_probability_24h:.0%}')}\n"
        f"{row('72h Failure Prob', f'{a1.risk.failure_probability_72h:.0%}', f'{a2.risk.failure_probability_72h:.0%}')}\n"
        f"{row('Health Score', f'{a1.risk.health_score:.0f}/100', f'{a2.risk.health_score:.0f}/100')}\n"
        f"{row('Customers at Risk', f'{a1.grid_impact.customers_at_risk:,}', f'{a2.grid_impact.customers_at_risk:,}')}\n"
        f"{row('Critical Facilities', str(a1.grid_impact.critical_facilities_at_risk), str(a2.grid_impact.critical_facilities_at_risk))}\n"
        f"{row('Anomaly Score', f'{a1.risk.anomaly_score:.2f}', f'{a2.risk.anomaly_score:.2f}')}\n\n"
        f"**Verdict:** {a1.asset.name} is {'more' if a1.risk.risk_score > a2.risk.risk_score else 'less'} "
        f"critical ({a1.risk.risk_score:.0f} vs {a2.risk.risk_score:.0f}). "
        f"{'Prioritise inspection of ' + a1.asset.name + '.' if a1.risk.risk_score > a2.risk.risk_score else 'Both assets need attention.'}"
    )


def _fallback_general(message: str, ranking: list) -> str:
    """Handle queries that don't match any specific domain intent."""
    # Check if it mentions any asset
    asset_match = _INTENT_ASSET.search(message.upper())
    if asset_match:
        aid = asset_match.group(0).upper()
        entry = next((e for e in ranking if e.asset.id == aid), None)
        if entry:
            return _fallback_asset(entry)

    return (
        "### GridShield AI — How Can I Help?\n\n"
        "I specialise in grid equipment health, failure prediction, and maintenance planning.\n\n"
        "**Try asking about:**\n"
        "- Any asset by ID (e.g. \"What's wrong with TR-1042?\")\n"
        "- Outage risk (\"Will there be a power outage?\")\n"
        "- Maintenance plans (\"What action is needed?\")\n"
        "- Weather impact (\"How does the storm affect North?\")\n"
        "- Asset comparison (\"Compare TR-1042 and BR-2201\")\n"
        "- Scenarios (\"What if a severe storm hits?\")\n\n"
        "I only answer grid operations questions — I don't have data on other topics."
    )


def _fallback_out_of_scope() -> str:
    return (
        "### GridShield AI — Grid Operations Only\n\n"
        "I'm a specialised grid operations advisor. I can only help with:\n\n"
        "- Equipment health and failure prediction\n"
        "- Maintenance prioritisation\n"
        "- Crew assignment and dispatch\n"
        "- Weather impact on grid assets\n"
        "- What-if scenario analysis\n\n"
        "I don't have data on topics outside grid operations. "
        "Please ask about an asset, risk level, or maintenance plan."
    )


# ─── Main advisor function ────────────────────────────────────────────────────

def gridshield_advisor(
    message: str,
    ranking: list,
    history: Optional[list] = None,
) -> str:
    """
    Main entry point for GridShield AI Copilot.

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
    if intent == "out_of_scope":
        return _fallback_out_of_scope()
    if intent == "help":
        return _fallback_help()
    if intent == "outage":
        return _fallback_outage(ranking)
    if intent == "comparison":
        return _fallback_comparison(message, ranking)
    if intent == "summary":
        return _fallback_summary(ranking)
    if intent == "crew" and entry:
        return _fallback_crew(entry, ranking)
    if intent == "weather":
        return _fallback_weather(entry, ranking, message)
    if intent == "scenario":
        return _fallback_scenario(ranking)
    if entry:
        if intent in ("maintenance",):
            return _fallback_maintenance(entry)
        return _fallback_asset(entry)
    if intent == "general":
        return _fallback_general(message, ranking)
    return _fallback_summary(ranking)
