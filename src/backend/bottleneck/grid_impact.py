"""
Bottleneck — Grid Impact Engine.

Computes operational consequence of an asset failure:
  - Customers affected
  - Critical facilities at risk
  - Feeder/substation importance
  - Downstream asset count
  - Composite grid_impact_score (0–1)
"""
from __future__ import annotations

from backend.bottleneck.contracts import Asset, GridImpact
from backend.bottleneck.mock_data import get_grid_impact_meta

# Normalisation constants (calibrated against the 30-asset demo fleet)
_MAX_CUSTOMERS = 15000.0
_MAX_CRITICAL  = 20.0
_MAX_DOWNSTREAM = 25.0
_MAX_CAPACITY_MVA = 35.0


def compute_grid_impact(asset: Asset) -> GridImpact:
    """
    Estimate operational impact if this asset fails.

    Score formula:
        grid_impact = 0.35 × customer_score
                    + 0.30 × critical_facility_score
                    + 0.20 × capacity_score
                    + 0.15 × downstream_score

    Amplified by asset criticality and penalised by redundancy.
    """
    customers, critical_fac, downstream = get_grid_impact_meta(asset.id)

    customer_score   = min(1.0, customers     / _MAX_CUSTOMERS)
    facility_score   = min(1.0, critical_fac  / _MAX_CRITICAL)
    capacity_score   = min(1.0, asset.capacity_mva / _MAX_CAPACITY_MVA)
    downstream_score = min(1.0, downstream    / _MAX_DOWNSTREAM)

    raw = (
        0.35 * customer_score
        + 0.30 * facility_score
        + 0.20 * capacity_score
        + 0.15 * downstream_score
    )

    # Amplify by asset criticality (high-criticality = higher consequence)
    # Penalise by redundancy (more redundancy = lower realised impact)
    amplified = raw * (0.6 + 0.4 * asset.criticality) * (1.2 - 0.4 * asset.redundancy_level)
    impact_score = round(min(1.0, max(0.0, amplified)), 4)

    return GridImpact(
        asset_id=asset.id,
        customers_at_risk=customers,
        critical_facilities_at_risk=critical_fac,
        capacity_mva=asset.capacity_mva,
        grid_impact_score=impact_score,
        downstream_assets=downstream,
    )
