"""
GridShield — Deterministic synthetic data layer.

All data is seeded so every call returns identical results.
30 assets across 6 types, with varied risk profiles designed for demo.
TR-1042 is the "hero" critical asset.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, List

from backend.gridshield.contracts import (
    Asset, Location, TelemetryRecord, Incident, MaintenanceRecord, Crew,
)

# ─── Assets ──────────────────────────────────────────────────────────────────

ASSETS: List[Asset] = [
    # ── Critical / degraded ─────────────────────────────────────────────────
    Asset(id="TR-1042", name="North Feeder Transformer 1042", asset_type="transformer",
          substation_id="SUB-NORTH-01", location=Location(lat=23.0225, lon=72.5714),
          criticality=0.92, capacity_mva=25.0, age_years=17.0, redundancy_level=0.30,
          status="degraded", region="North"),
    Asset(id="TR-1019", name="North Feeder Transformer 1019", asset_type="transformer",
          substation_id="SUB-NORTH-01", location=Location(lat=23.0280, lon=72.5760),
          criticality=0.85, capacity_mva=20.0, age_years=14.0, redundancy_level=0.40,
          status="degraded", region="North"),
    Asset(id="BR-2201", name="South Grid Breaker 2201", asset_type="breaker",
          substation_id="SUB-SOUTH-02", location=Location(lat=22.9920, lon=72.5540),
          criticality=0.88, capacity_mva=30.0, age_years=20.0, redundancy_level=0.20,
          status="critical", region="South"),
    Asset(id="FD-3310", name="East Industrial Feeder 3310", asset_type="feeder",
          substation_id="SUB-EAST-03", location=Location(lat=23.0410, lon=72.6100),
          criticality=0.78, capacity_mva=15.0, age_years=11.0, redundancy_level=0.55,
          status="degraded", region="East"),
    # ── High risk ────────────────────────────────────────────────────────────
    Asset(id="TR-2055", name="West Distribution Transformer 2055", asset_type="transformer",
          substation_id="SUB-WEST-04", location=Location(lat=23.0110, lon=72.5100),
          criticality=0.80, capacity_mva=18.0, age_years=12.0, redundancy_level=0.45,
          status="degraded", region="West"),
    Asset(id="RC-4401", name="Central Recloser 4401", asset_type="recloser",
          substation_id="SUB-CENTRAL-05", location=Location(lat=23.0300, lon=72.5850),
          criticality=0.70, capacity_mva=12.0, age_years=9.0, redundancy_level=0.60,
          status="healthy", region="Central"),
    Asset(id="BR-1175", name="North Substation Breaker 1175", asset_type="breaker",
          substation_id="SUB-NORTH-01", location=Location(lat=23.0205, lon=72.5690),
          criticality=0.82, capacity_mva=22.0, age_years=16.0, redundancy_level=0.35,
          status="degraded", region="North"),
    Asset(id="SW-5520", name="South Sector Switch 5520", asset_type="switch",
          substation_id="SUB-SOUTH-02", location=Location(lat=22.9990, lon=72.5610),
          criticality=0.65, capacity_mva=8.0, age_years=7.0, redundancy_level=0.70,
          status="healthy", region="South"),
    # ── Medium risk ──────────────────────────────────────────────────────────
    Asset(id="TR-3088", name="East Residential Transformer 3088", asset_type="transformer",
          substation_id="SUB-EAST-03", location=Location(lat=23.0450, lon=72.6200),
          criticality=0.60, capacity_mva=10.0, age_years=8.0, redundancy_level=0.65,
          status="healthy", region="East"),
    Asset(id="CB-6601", name="West Capacitor Bank 6601", asset_type="capacitor_bank",
          substation_id="SUB-WEST-04", location=Location(lat=23.0150, lon=72.5050),
          criticality=0.55, capacity_mva=5.0, age_years=6.0, redundancy_level=0.75,
          status="healthy", region="West"),
    Asset(id="FD-2280", name="South Residential Feeder 2280", asset_type="feeder",
          substation_id="SUB-SOUTH-02", location=Location(lat=22.9850, lon=72.5480),
          criticality=0.62, capacity_mva=10.0, age_years=9.0, redundancy_level=0.60,
          status="healthy", region="South"),
    Asset(id="RC-3320", name="Central Recloser 3320", asset_type="recloser",
          substation_id="SUB-CENTRAL-05", location=Location(lat=23.0350, lon=72.5900),
          criticality=0.58, capacity_mva=9.0, age_years=5.0, redundancy_level=0.80,
          status="healthy", region="Central"),
    # ── Weather-sensitive ────────────────────────────────────────────────────
    Asset(id="TR-5099", name="Storm-Exposed Transformer 5099", asset_type="transformer",
          substation_id="SUB-NORTH-01", location=Location(lat=23.0500, lon=72.5800),
          criticality=0.75, capacity_mva=16.0, age_years=10.0, redundancy_level=0.50,
          status="healthy", region="North"),
    Asset(id="FD-1140", name="Coastal Feeder 1140", asset_type="feeder",
          substation_id="SUB-SOUTH-02", location=Location(lat=22.9800, lon=72.5400),
          criticality=0.70, capacity_mva=12.0, age_years=8.0, redundancy_level=0.55,
          status="healthy", region="South"),
    # ── Healthy / low risk ───────────────────────────────────────────────────
    Asset(id="TR-7001", name="New North Transformer 7001", asset_type="transformer",
          substation_id="SUB-NORTH-01", location=Location(lat=23.0350, lon=72.5750),
          criticality=0.50, capacity_mva=15.0, age_years=2.0, redundancy_level=0.85,
          status="healthy", region="North"),
    Asset(id="BR-7110", name="East Breaker 7110", asset_type="breaker",
          substation_id="SUB-EAST-03", location=Location(lat=23.0500, lon=72.6050),
          criticality=0.48, capacity_mva=12.0, age_years=3.0, redundancy_level=0.90,
          status="healthy", region="East"),
    Asset(id="SW-7220", name="West Switch 7220", asset_type="switch",
          substation_id="SUB-WEST-04", location=Location(lat=23.0100, lon=72.5030),
          criticality=0.42, capacity_mva=6.0, age_years=2.0, redundancy_level=0.92,
          status="healthy", region="West"),
    Asset(id="CB-7330", name="Central Capacitor Bank 7330", asset_type="capacitor_bank",
          substation_id="SUB-CENTRAL-05", location=Location(lat=23.0320, lon=72.5820),
          criticality=0.40, capacity_mva=4.0, age_years=1.5, redundancy_level=0.95,
          status="healthy", region="Central"),
    # ── Degrading (moderate now, will worsen) ────────────────────────────────
    Asset(id="TR-4060", name="South Industrial Transformer 4060", asset_type="transformer",
          substation_id="SUB-SOUTH-02", location=Location(lat=23.0010, lon=72.5590),
          criticality=0.72, capacity_mva=20.0, age_years=13.0, redundancy_level=0.48,
          status="degraded", region="South"),
    Asset(id="FD-4480", name="West Agri Feeder 4480", asset_type="feeder",
          substation_id="SUB-WEST-04", location=Location(lat=23.0200, lon=72.5150),
          criticality=0.60, capacity_mva=11.0, age_years=10.0, redundancy_level=0.58,
          status="healthy", region="West"),
    # ── High-impact moderate-prob ────────────────────────────────────────────
    Asset(id="TR-9001", name="Hospital District Transformer 9001", asset_type="transformer",
          substation_id="SUB-CENTRAL-05", location=Location(lat=23.0380, lon=72.5870),
          criticality=0.95, capacity_mva=30.0, age_years=7.0, redundancy_level=0.55,
          status="healthy", region="Central"),
    Asset(id="BR-9010", name="Data Centre Breaker 9010", asset_type="breaker",
          substation_id="SUB-CENTRAL-05", location=Location(lat=23.0360, lon=72.5860),
          criticality=0.93, capacity_mva=28.0, age_years=5.0, redundancy_level=0.60,
          status="healthy", region="Central"),
    # ── Mixed ────────────────────────────────────────────────────────────────
    Asset(id="RC-2210", name="South Recloser 2210", asset_type="recloser",
          substation_id="SUB-SOUTH-02", location=Location(lat=22.9950, lon=72.5550),
          criticality=0.65, capacity_mva=9.0, age_years=6.0, redundancy_level=0.70,
          status="healthy", region="South"),
    Asset(id="SW-3301", name="East Switch 3301", asset_type="switch",
          substation_id="SUB-EAST-03", location=Location(lat=23.0430, lon=72.6150),
          criticality=0.55, capacity_mva=7.0, age_years=4.0, redundancy_level=0.82,
          status="healthy", region="East"),
    Asset(id="CB-2240", name="North Capacitor Bank 2240", asset_type="capacitor_bank",
          substation_id="SUB-NORTH-01", location=Location(lat=23.0260, lon=72.5730),
          criticality=0.50, capacity_mva=5.0, age_years=3.0, redundancy_level=0.88,
          status="healthy", region="North"),
    Asset(id="TR-6050", name="Airport Zone Transformer 6050", asset_type="transformer",
          substation_id="SUB-EAST-03", location=Location(lat=23.0600, lon=72.6300),
          criticality=0.88, capacity_mva=22.0, age_years=9.0, redundancy_level=0.50,
          status="healthy", region="East"),
    Asset(id="FD-6060", name="Airport Feeder 6060", asset_type="feeder",
          substation_id="SUB-EAST-03", location=Location(lat=23.0580, lon=72.6280),
          criticality=0.86, capacity_mva=18.0, age_years=8.0, redundancy_level=0.55,
          status="healthy", region="East"),
    Asset(id="BR-5511", name="West Industrial Breaker 5511", asset_type="breaker",
          substation_id="SUB-WEST-04", location=Location(lat=23.0180, lon=72.5120),
          criticality=0.75, capacity_mva=20.0, age_years=11.0, redundancy_level=0.45,
          status="degraded", region="West"),
    Asset(id="RC-6600", name="South Recloser 6600", asset_type="recloser",
          substation_id="SUB-SOUTH-02", location=Location(lat=22.9900, lon=72.5510),
          criticality=0.62, capacity_mva=10.0, age_years=7.0, redundancy_level=0.68,
          status="healthy", region="South"),
    Asset(id="TR-8080", name="South-West Border Transformer 8080", asset_type="transformer",
          substation_id="SUB-WEST-04", location=Location(lat=23.0050, lon=72.5080),
          criticality=0.68, capacity_mva=14.0, age_years=12.0, redundancy_level=0.52,
          status="degraded", region="West"),
]

ASSET_MAP: Dict[str, Asset] = {a.id: a for a in ASSETS}


# ─── Telemetry (last 48 h, hourly) ──────────────────────────────────────────

# Per-asset telemetry seed values (base values that define the risk profile)
_TELEMETRY_BASE: Dict[str, dict] = {
    "TR-1042": dict(oil_temp=92, load=88, vib=4.8, unbal=7.2, vdev=6.5, pd=0.82, amb=38),
    "TR-1019": dict(oil_temp=78, load=76, vib=3.2, unbal=5.1, vdev=4.8, pd=0.55, amb=37),
    "BR-2201": dict(oil_temp=84, load=91, vib=5.1, unbal=8.0, vdev=7.2, pd=0.78, amb=36),
    "FD-3310": dict(oil_temp=68, load=72, vib=2.8, unbal=4.2, vdev=3.5, pd=0.42, amb=36),
    "TR-2055": dict(oil_temp=74, load=70, vib=3.0, unbal=4.8, vdev=4.1, pd=0.48, amb=35),
    "RC-4401": dict(oil_temp=52, load=55, vib=1.2, unbal=2.1, vdev=1.8, pd=0.18, amb=33),
    "BR-1175": dict(oil_temp=80, load=78, vib=3.8, unbal=5.8, vdev=5.2, pd=0.62, amb=37),
    "SW-5520": dict(oil_temp=44, load=48, vib=0.9, unbal=1.5, vdev=1.2, pd=0.10, amb=33),
    "TR-3088": dict(oil_temp=60, load=60, vib=2.0, unbal=3.0, vdev=2.5, pd=0.28, amb=34),
    "CB-6601": dict(oil_temp=42, load=45, vib=0.8, unbal=1.2, vdev=1.0, pd=0.08, amb=33),
    "FD-2280": dict(oil_temp=55, load=58, vib=1.8, unbal=2.8, vdev=2.2, pd=0.22, amb=34),
    "RC-3320": dict(oil_temp=48, load=50, vib=1.0, unbal=1.8, vdev=1.5, pd=0.12, amb=32),
    "TR-5099": dict(oil_temp=65, load=62, vib=2.5, unbal=3.5, vdev=3.0, pd=0.35, amb=34),
    "FD-1140": dict(oil_temp=58, load=60, vib=2.0, unbal=3.2, vdev=2.8, pd=0.30, amb=33),
    "TR-7001": dict(oil_temp=45, load=42, vib=0.7, unbal=1.0, vdev=0.8, pd=0.05, amb=32),
    "BR-7110": dict(oil_temp=40, load=38, vib=0.6, unbal=0.9, vdev=0.7, pd=0.04, amb=31),
    "SW-7220": dict(oil_temp=38, load=35, vib=0.5, unbal=0.8, vdev=0.6, pd=0.03, amb=31),
    "CB-7330": dict(oil_temp=36, load=32, vib=0.4, unbal=0.7, vdev=0.5, pd=0.02, amb=30),
    "TR-4060": dict(oil_temp=71, load=68, vib=2.7, unbal=4.0, vdev=3.8, pd=0.45, amb=35),
    "FD-4480": dict(oil_temp=56, load=55, vib=1.6, unbal=2.5, vdev=2.0, pd=0.20, amb=33),
    "TR-9001": dict(oil_temp=58, load=64, vib=1.5, unbal=2.2, vdev=1.9, pd=0.22, amb=33),
    "BR-9010": dict(oil_temp=52, load=58, vib=1.2, unbal=1.8, vdev=1.5, pd=0.16, amb=32),
    "RC-2210": dict(oil_temp=50, load=52, vib=1.1, unbal=1.9, vdev=1.6, pd=0.14, amb=32),
    "SW-3301": dict(oil_temp=42, load=44, vib=0.8, unbal=1.3, vdev=1.1, pd=0.07, amb=31),
    "CB-2240": dict(oil_temp=40, load=40, vib=0.7, unbal=1.1, vdev=0.9, pd=0.06, amb=31),
    "TR-6050": dict(oil_temp=62, load=65, vib=2.2, unbal=3.3, vdev=2.8, pd=0.32, amb=34),
    "FD-6060": dict(oil_temp=60, load=63, vib=2.0, unbal=3.0, vdev=2.5, pd=0.28, amb=34),
    "BR-5511": dict(oil_temp=75, load=74, vib=3.4, unbal=5.5, vdev=4.9, pd=0.58, amb=36),
    "RC-6600": dict(oil_temp=51, load=53, vib=1.1, unbal=1.9, vdev=1.6, pd=0.14, amb=32),
    "TR-8080": dict(oil_temp=70, load=67, vib=2.6, unbal=3.8, vdev=3.6, pd=0.44, amb=35),
}


def get_telemetry(asset_id: str, hours: int = 48) -> List[TelemetryRecord]:
    """Return deterministic hourly telemetry for the past `hours` hours."""
    base = _TELEMETRY_BASE.get(asset_id, dict(
        oil_temp=55, load=55, vib=1.5, unbal=2.5, vdev=2.0, pd=0.20, amb=33
    ))
    now = datetime(2025, 6, 15, 12, 0, 0)
    records = []
    # Use a simple hash seed per asset for determinism
    seed = sum(ord(c) for c in asset_id)
    for i in range(hours, 0, -1):
        ts = now - timedelta(hours=i)
        # Slow sinusoidal drift (+/- 5%) — deterministic, no random
        drift = 0.05 * (((seed + i) % 17) / 8.5 - 1.0)
        records.append(TelemetryRecord(
            asset_id=asset_id,
            timestamp=ts,
            oil_temperature=round(base["oil_temp"] * (1 + drift * 0.6), 1),
            load_percentage=round(min(100, base["load"] * (1 + drift * 0.4)), 1),
            vibration=round(max(0, base["vib"] * (1 + drift * 0.8)), 2),
            current_unbalance=round(max(0, base["unbal"] * (1 + drift * 0.5)), 2),
            voltage_deviation=round(max(0, base["vdev"] * (1 + drift * 0.5)), 2),
            partial_discharge=round(min(1, max(0, base["pd"] * (1 + drift * 0.7))), 3),
            ambient_temperature=round(base["amb"] + drift * 3, 1),
        ))
    return records


def get_latest_telemetry(asset_id: str) -> TelemetryRecord:
    return get_telemetry(asset_id, hours=1)[0]


# ─── Incidents ───────────────────────────────────────────────────────────────

_INCIDENT_TEMPLATES: Dict[str, List[dict]] = {
    "TR-1042": [
        dict(id="INC-1042-A", days_ago=12, desc="Overheating event — oil temp reached 105°C; emergency cooling activated", sev="critical"),
        dict(id="INC-1042-B", days_ago=45, desc="Partial discharge anomaly detected during routine inspection", sev="major"),
        dict(id="INC-1042-C", days_ago=120, desc="Vibration spike — bushing inspection required", sev="moderate"),
    ],
    "TR-1019": [
        dict(id="INC-1019-A", days_ago=20, desc="Load exceeded rated capacity for 3 hours during peak demand", sev="major"),
        dict(id="INC-1019-B", days_ago=90, desc="Oil sample showed elevated dissolved gases", sev="moderate"),
    ],
    "BR-2201": [
        dict(id="INC-2201-A", days_ago=8, desc="Trip operation failure — breaker required manual reset", sev="critical"),
        dict(id="INC-2201-B", days_ago=35, desc="Contact resistance out of specification", sev="major"),
        dict(id="INC-2201-C", days_ago=150, desc="Arc flash incident during switching operation", sev="critical"),
    ],
    "FD-3310": [
        dict(id="INC-3310-A", days_ago=30, desc="Phase imbalance causing customer complaints", sev="moderate"),
        dict(id="INC-3310-B", days_ago=80, desc="Cable insulation degradation noted on inspection", sev="moderate"),
    ],
    "TR-2055": [
        dict(id="INC-2055-A", days_ago=25, desc="Cooling fan failure — temperature elevated for 6 hours", sev="major"),
        dict(id="INC-2055-B", days_ago=100, desc="Winding resistance measurement out of tolerance", sev="moderate"),
    ],
    "BR-1175": [
        dict(id="INC-1175-A", days_ago=18, desc="Spurious tripping event during normal load conditions", sev="major"),
    ],
    "TR-4060": [
        dict(id="INC-4060-A", days_ago=40, desc="Oil leak detected at gasket — minor but increasing", sev="moderate"),
    ],
    "TR-9001": [
        dict(id="INC-9001-A", days_ago=60, desc="Planned maintenance overdue — inspection not yet scheduled", sev="minor"),
    ],
    "BR-5511": [
        dict(id="INC-5511-A", days_ago=22, desc="Contact wear exceeds threshold — replacement recommended", sev="major"),
    ],
    "TR-8080": [
        dict(id="INC-8080-A", days_ago=35, desc="OLTC (on-load tap changer) noise during operation", sev="moderate"),
    ],
}


def get_incidents(asset_id: str) -> List[Incident]:
    templates = _INCIDENT_TEMPLATES.get(asset_id, [])
    base_dt = datetime(2025, 6, 15, 12, 0, 0)
    return [
        Incident(
            incident_id=t["id"],
            asset_id=asset_id,
            timestamp=base_dt - timedelta(days=t["days_ago"]),
            description=t["desc"],
            severity=t["sev"],
        )
        for t in templates
    ]


# ─── Maintenance records ─────────────────────────────────────────────────────

_MAINTENANCE_TEMPLATES: Dict[str, List[dict]] = {
    "TR-1042": [
        dict(id="MNT-1042-1", days_ago=180, work="Full inspection — oil sample, winding resistance, insulation test", tech="Team Alpha"),
        dict(id="MNT-1042-2", days_ago=420, work="Bushing replacement and OLTC service", tech="Team Alpha"),
    ],
    "TR-1019": [
        dict(id="MNT-1019-1", days_ago=200, work="Oil filtration and thermal imaging", tech="Team Beta"),
    ],
    "BR-2201": [
        dict(id="MNT-2201-1", days_ago=90, work="Contact inspection and lubrication", tech="Team Gamma"),
        dict(id="MNT-2201-2", days_ago=400, work="Full mechanism overhaul", tech="Team Gamma"),
    ],
    "FD-3310": [
        dict(id="MNT-3310-1", days_ago=150, work="Cable insulation test and IR thermography", tech="Team Delta"),
    ],
    "TR-2055": [
        dict(id="MNT-2055-1", days_ago=160, work="Cooling system service and oil sample", tech="Team Beta"),
    ],
    "BR-1175": [
        dict(id="MNT-1175-1", days_ago=220, work="Trip coil replacement and functional test", tech="Team Gamma"),
    ],
    "TR-7001": [
        dict(id="MNT-7001-1", days_ago=30, work="Commissioning inspection — all parameters normal", tech="Team Alpha"),
    ],
    "TR-9001": [
        dict(id="MNT-9001-1", days_ago=300, work="Annual inspection — passed all tests", tech="Team Alpha"),
    ],
    "TR-4060": [
        dict(id="MNT-4060-1", days_ago=250, work="Oil sample and gasket check — minor wear noted", tech="Team Beta"),
    ],
}


def get_maintenance_records(asset_id: str) -> List[MaintenanceRecord]:
    templates = _MAINTENANCE_TEMPLATES.get(asset_id, [])
    base_dt = datetime(2025, 6, 15, 12, 0, 0)
    return [
        MaintenanceRecord(
            record_id=t["id"],
            asset_id=asset_id,
            date=base_dt - timedelta(days=t["days_ago"]),
            work_done=t["work"],
            technician=t["tech"],
        )
        for t in templates
    ]


# ─── Crews ───────────────────────────────────────────────────────────────────

CREWS: List[Crew] = [
    Crew(crew_id="CREW-01", name="Alpha Transformer Team", specialty="transformer",
         region="North", availability="available", capacity=2),
    Crew(crew_id="CREW-02", name="Beta Transformer Team", specialty="transformer",
         region="South", availability="available", capacity=2),
    Crew(crew_id="CREW-03", name="Gamma Breaker Specialists", specialty="breaker",
         region="North", availability="available", capacity=3),
    Crew(crew_id="CREW-04", name="Delta Feeder Crew", specialty="feeder",
         region="East", availability="available", capacity=3),
    Crew(crew_id="CREW-05", name="Epsilon Switch Crew", specialty="switch",
         region="West", availability="busy", capacity=2),
    Crew(crew_id="CREW-06", name="Zeta Recloser Team", specialty="recloser",
         region="Central", availability="available", capacity=2),
    Crew(crew_id="CREW-07", name="Eta Central Transformer", specialty="transformer",
         region="Central", availability="available", capacity=2),
    Crew(crew_id="CREW-08", name="Theta South Breaker", specialty="breaker",
         region="South", availability="available", capacity=2),
    Crew(crew_id="CREW-09", name="Iota West Transformer", specialty="transformer",
         region="West", availability="offline", capacity=2),
    Crew(crew_id="CREW-10", name="Kappa East Feeder", specialty="feeder",
         region="East", availability="available", capacity=3),
]

CREW_MAP: Dict[str, Crew] = {c.crew_id: c for c in CREWS}


# ─── Grid impact metadata ────────────────────────────────────────────────────

# customers, critical_facilities, downstream_assets
_GRID_IMPACT_META: Dict[str, tuple] = {
    "TR-1042": (8420, 7, 12),
    "TR-1019": (5200, 4, 8),
    "BR-2201": (11000, 10, 18),
    "FD-3310": (3400, 3, 6),
    "TR-2055": (4100, 3, 7),
    "RC-4401": (1800, 1, 4),
    "BR-1175": (6300, 5, 10),
    "SW-5520": (900,  0, 2),
    "TR-3088": (2200, 1, 5),
    "CB-6601": (500,  0, 1),
    "FD-2280": (1600, 1, 3),
    "RC-3320": (1100, 0, 3),
    "TR-5099": (3100, 2, 6),
    "FD-1140": (2700, 2, 5),
    "TR-7001": (2800, 2, 5),
    "BR-7110": (1500, 1, 3),
    "SW-7220": (700,  0, 2),
    "CB-7330": (400,  0, 1),
    "TR-4060": (5800, 5, 9),
    "FD-4480": (1900, 1, 4),
    "TR-9001": (12000, 15, 20),
    "BR-9010": (9500, 12, 16),
    "RC-2210": (1400, 0, 3),
    "SW-3301": (800,  0, 2),
    "CB-2240": (600,  0, 1),
    "TR-6050": (7200, 8, 13),
    "FD-6060": (6100, 7, 11),
    "BR-5511": (4800, 4, 8),
    "RC-6600": (1300, 0, 3),
    "TR-8080": (3600, 3, 6),
}


def get_grid_impact_meta(asset_id: str) -> tuple:
    """Return (customers, critical_facilities, downstream_assets)."""
    return _GRID_IMPACT_META.get(asset_id, (1000, 0, 2))
