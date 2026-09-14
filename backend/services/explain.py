from typing import Optional


TEMPLATES = {
    "charge_battery": (
        "Solar generation expected at {gen_kw:.1f} kW, exceeding export limit of {export_limit:.1f} kW. "
        "Battery at {soc_pct:.0f}% capacity. Charging now to store {surplus:.1f} kWh surplus — "
        "avoids curtailment and preserves energy for evening discharge."
    ),
    "curtail": (
        "Solar generation expected at {gen_kw:.1f} kW, surplus of {surplus:.1f} kWh over export limit. "
        "Battery full at {soc_pct:.0f}%. Curtailment recommended — potential loss of ₹{loss_inr:.0f}."
    ),
    "discharge_battery": (
        "Generation forecast ({gen_kw:.1f} kW) below demand ({demand:.1f} kW). "
        "Battery at {soc_pct:.0f}% — discharging {deficit:.1f} kWh to cover shortfall."
    ),
    "activate_backup": (
        "Generation at {gen_kw:.1f} kW, demand at {demand:.1f} kW, deficit of {deficit:.1f} kWh. "
        "Battery depleted to minimum SOC. Backup power activation recommended."
    ),
    "hold": (
        "Generation ({gen_kw:.1f} kW) roughly matches demand ({demand:.1f} kW). "
        "No action needed — battery holding at {soc_pct:.0f}%."
    ),
}


def generate_explanation(
    action: str,
    gen_kw: float,
    export_limit: float,
    battery_soc: float,
    battery_capacity: float,
    demand_kw: float,
    surplus: float = 0.0,
    deficit: float = 0.0,
    loss_inr: float = 0.0,
) -> str:
    soc_pct = (battery_soc / battery_capacity * 100) if battery_capacity > 0 else 0
    template = TEMPLATES.get(action, "No recommendation available.")
    return template.format(
        gen_kw=gen_kw,
        export_limit=export_limit,
        soc_pct=soc_pct,
        surplus=surplus,
        deficit=deficit,
        demand=demand_kw,
        loss_inr=loss_inr,
    )
