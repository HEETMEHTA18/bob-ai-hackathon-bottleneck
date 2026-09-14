# Problem Statement — Bottleneck AI

## IBM Bob Hackathon 2026 — Track U1: Power Outage Prediction & Grid Equipment Failure Advisor

---

## The Problem

Electric power grids are aging. In India and worldwide, utility operators manage fleets of
transformers, feeders, breakers, and switching equipment that are decades old, operating under
increasing load, and exposed to more frequent extreme weather events.

**Today's operational reality:**
- Failures are discovered reactively — after the outage has started
- Maintenance is calendar-driven, not condition-driven
- Crew dispatch happens after failure, not before
- Risk assessment is manual and siloed — weather, telemetry, and incident data are rarely
  combined in a single decision view

The result: **unnecessary outages, delayed restoration, and significant customer impact** —
especially for critical facilities like hospitals, emergency services, and water treatment plants.

---

## Scale of the Challenge

| Metric | Context |
|--------|---------|
| India grid | ~1.4 billion people served |
| Average outage duration | 5–8 hours in urban areas, much longer rural |
| Transformer failures | Leading cause of outages (thermal, aging, overload) |
| Annual economic impact | Billions in lost productivity and grid repair costs |
| Extreme weather trend | Heatwaves, storms, and flooding events increasing year-over-year |

---

## Why Existing Approaches Fall Short

1. **SCADA systems** monitor in real time but do not predict or explain
2. **Standalone anomaly detectors** raise alerts but don't rank by customer impact
3. **Manual maintenance scheduling** misses the combined risk from weather + degradation + load
4. **Crew dispatch systems** are reactive — they respond to failures, not risk scores

---

## What Is Needed

A platform that:

1. **Predicts** which asset is likely to fail in the next 24–72 hours
2. **Explains** *why* — citing the actual telemetry, weather, and incident drivers
3. **Prioritizes** not just by failure probability, but by **operational impact** (customers, critical facilities, redundancy)
4. **Positions** field crews *before* failures occur, reducing restoration time

This is the Bottleneck mission: **PREDICT → EXPLAIN → PRIORITIZE → POSITION**

---

## Official Hackathon Problem (U1)

> Build an AI-powered solution that:
> - Ingests asset-health sensor data, weather forecasts, and historical incident records
> - Predicts outage-prone areas and at-risk equipment
> - Ranks assets by grid-impact severity
> - Generates prioritised maintenance plans
> - Generates crew pre-positioning plans

Bottleneck addresses all five requirements end-to-end.
