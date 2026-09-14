import numpy as np
from typing import Optional


TARIFF_RATE_INR_PER_KWH = 5.0
GRID_EMISSION_FACTOR_TCO2_PER_MWH = 0.82


def decide_action(
    generation_forecast_p50: float,
    export_limit: float,
    battery_soc: float,
    battery_capacity: float,
    demand_forecast: float,
    min_soc: float = 0.1,
    surplus_threshold_high: float = 0.3,
) -> dict:
    if generation_forecast_p50 > export_limit:
        surplus = generation_forecast_p50 - export_limit
        if battery_soc < battery_capacity:
            action = "charge_battery"
            risk = "LOW"
        else:
            action = "curtail"
            surplus_ratio = surplus / export_limit if export_limit > 0 else 0
            risk = "HIGH" if surplus_ratio > surplus_threshold_high else "MEDIUM"
    elif generation_forecast_p50 < demand_forecast:
        deficit = demand_forecast - generation_forecast_p50
        if battery_soc > min_soc * battery_capacity:
            action = "discharge_battery"
            risk = "LOW"
        else:
            action = "activate_backup"
            risk = "HIGH"
    else:
        action = "hold"
        risk = "LOW"

    return {
        "action": action,
        "risk": risk,
        "surplus_kwh": max(0, generation_forecast_p50 - export_limit),
        "deficit_kwh": max(0, demand_forecast - generation_forecast_p50),
    }


def estimate_financial_impact(action: str, energy_kwh: float,
                              tariff_rate: float = TARIFF_RATE_INR_PER_KWH) -> float:
    if action == "curtail":
        return -energy_kwh * tariff_rate
    elif action == "charge_battery":
        return energy_kwh * tariff_rate * 0.5
    elif action == "discharge_battery":
        return energy_kwh * tariff_rate
    elif action == "activate_backup":
        return -energy_kwh * tariff_rate * 1.5
    return 0.0


def estimate_co2_impact(action: str, energy_kwh: float,
                        emission_factor: float = GRID_EMISSION_FACTOR_TCO2_PER_MWH) -> float:
    mwh = energy_kwh / 1000.0
    if action == "curtail":
        return -mwh * emission_factor
    elif action == "charge_battery":
        return 0.0
    elif action == "discharge_battery":
        return mwh * emission_factor
    elif action == "activate_backup":
        return -mwh * emission_factor * 1.2
    return 0.0


def generate_optimization_schedule(
    forecast_p50: np.ndarray,
    forecast_p10: np.ndarray,
    forecast_p90: np.ndarray,
    export_limit: float,
    battery_soc: float,
    battery_capacity: float,
    demand_forecast: float,
) -> list:
    schedule = []
    current_soc = battery_soc
    for i in range(len(forecast_p50)):
        gen = forecast_p50[i]
        decision = decide_action(
            generation_forecast_p50=gen,
            export_limit=export_limit,
            battery_soc=current_soc,
            battery_capacity=battery_capacity,
            demand_forecast=demand_forecast,
        )
        energy_mismatch = decision["surplus_kwh"] - decision["deficit_kwh"]
        if decision["action"] == "charge_battery":
            current_soc = min(battery_capacity, current_soc + energy_mismatch)
        elif decision["action"] == "discharge_battery":
            current_soc = max(0, current_soc - decision["deficit_kwh"])

        financial = estimate_financial_impact(decision["action"], abs(energy_mismatch))
        co2 = estimate_co2_impact(decision["action"], abs(energy_mismatch))

        schedule.append({
            "hour": i,
            "generation_kw": float(gen),
            "p10_kw": float(forecast_p10[i]),
            "p90_kw": float(forecast_p90[i]),
            "action": decision["action"],
            "risk": decision["risk"],
            "battery_soc_kwh": float(current_soc),
            "financial_impact_inr": float(financial),
            "co2_impact_tonnes": float(co2),
        })
    return schedule
