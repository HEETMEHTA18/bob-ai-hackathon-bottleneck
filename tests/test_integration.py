import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from backend.api.database import create_site, get_site, list_sites, init_db
from backend.optimization.dispatch import decide_action, estimate_financial_impact, estimate_co2_impact, generate_optimization_schedule
from backend.services.explain import generate_explanation
from backend.forecasting.uncertainty import compute_quantile_bands, validate_coverage
from backend.forecasting.evaluate import evaluate

print("=" * 60)
print("GridMind AI — Integration Test Suite")
print("=" * 60)

# Test 1: Database operations
print("\n[1/6] Testing database operations...")
init_db()
site = create_site(
    name="Test Solar Plant",
    latitude=28.6139, longitude=77.2090,
    capacity_kw=100, battery_capacity_kwh=50, export_limit_kw=80,
)
assert site is not None, "Site creation failed"
assert site["name"] == "Test Solar Plant", "Site name mismatch"
print(f"  ✓ Created site: {site['name']} (ID: {site['id']})")

sites = list_sites()
assert len(sites) > 0, "No sites found"
print(f"  ✓ Listed {len(sites)} sites")

# Test 2: Decision engine
print("\n[2/6] Testing decision engine...")
d1 = decide_action(120, 80, 25, 50, 70)
assert d1["action"] == "charge_battery", f"Expected charge_battery, got {d1['action']}"
print(f"  ✓ Surplus → {d1['action']} (risk: {d1['risk']})")

d2 = decide_action(30, 80, 5, 50, 70)
assert d2["action"] == "activate_backup", f"Expected activate_backup, got {d2['action']}"
print(f"  ✓ Deficit → {d2['action']} (risk: {d2['risk']})")

d3 = decide_action(60, 80, 25, 50, 50)
assert d3["action"] == "hold", f"Expected hold, got {d3['action']}"
print(f"  ✓ Balanced → {d3['action']} (risk: {d3['risk']})")

# Test 3: Financial & CO2 impact
print("\n[3/6] Testing impact estimation...")
fi = estimate_financial_impact("charge_battery", 20)
assert fi > 0, "Charge should have positive financial impact"
print(f"  ✓ Charge 20kWh: ₹{fi:.0f}")

fi_curtailed = estimate_financial_impact("curtail", 20)
assert fi_curtailed < 0, "Curtailment should have negative financial impact"
print(f"  ✓ Curtail 20kWh: ₹{fi_curtailed:.0f}")

co2 = estimate_co2_impact("discharge_battery", 20)
print(f"  ✓ Discharge 20kWh: {co2:.4f} tCO₂")

# Test 4: Uncertainty bands
print("\n[4/6] Testing uncertainty bands...")
point = np.array([50, 60, 70, 80, 90])
residuals = np.random.normal(0, 5, 100)
bands = compute_quantile_bands(point, residuals)
assert all(bands["p10"] <= bands["p50"]), "P10 should be <= P50"
assert all(bands["p50"] <= bands["p90"]), "P50 should be <= P90"
print(f"  ✓ Bands valid: P10={bands['p10'][2]:.1f}, P50={bands['p50'][2]:.1f}, P90={bands['p90'][2]:.1f}")

y_true = np.random.normal(70, 5, 5)
coverage = validate_coverage(y_true, bands["p10"], bands["p90"])
print(f"  ✓ Coverage: {coverage:.1%}")

# Test 5: Explainability
print("\n[5/6] Testing explainability...")
expl = generate_explanation(
    action="charge_battery", gen_kw=120, export_limit=80,
    battery_soc=25, battery_capacity=50, demand_kw=70,
    surplus=40,
)
assert len(expl) > 20, "Explanation too short"
print(f"  ✓ Explanation: {expl[:80]}...")

# Test 6: Optimization schedule
print("\n[6/6] Testing optimization schedule...")
forecast = np.array([0, 0, 0, 0, 0, 10, 30, 60, 80, 100, 100, 100, 100, 80, 60, 30, 10, 0, 0, 0, 0, 0, 0, 0])
schedule = generate_optimization_schedule(forecast, forecast * 0.8, forecast * 1.2, 80, 25, 50, 70)
assert len(schedule) == 24, f"Expected 24 hours, got {len(schedule)}"
actions = set(s["action"] for s in schedule)
print(f"  ✓ Generated {len(schedule)}h schedule with actions: {actions}")

total_fi = sum(s["financial_impact_inr"] for s in schedule)
total_co2 = sum(s["co2_impact_tonnes"] for s in schedule)
print(f"  ✓ Total financial: ₹{total_fi:.0f}, CO₂: {total_co2:.4f} t")

print("\n" + "=" * 60)
print("All tests passed ✓")
print("=" * 60)
