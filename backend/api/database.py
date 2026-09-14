import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "gridmind.db"


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            altitude REAL DEFAULT 0,
            capacity_kw REAL NOT NULL,
            surface_tilt REAL,
            surface_azimuth REAL DEFAULT 180,
            battery_capacity_kwh REAL DEFAULT 0,
            export_limit_kw REAL DEFAULT 0,
            hub_height_m REAL DEFAULT 80,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            forecast_type TEXT NOT NULL,
            data_json TEXT NOT NULL,
            metrics_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites(id)
        );
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            schedule_json TEXT NOT NULL,
            explanation_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites(id)
        );
    """)
    conn.commit()
    conn.close()


def create_site(name: str, latitude: float, longitude: float, capacity_kw: float,
                altitude: float = 0, surface_tilt: float = None, surface_azimuth: float = 180,
                battery_capacity_kwh: float = 0, export_limit_kw: float = 0,
                hub_height_m: float = 80) -> dict:
    conn = get_db()
    if surface_tilt is None:
        surface_tilt = latitude
    cursor = conn.execute(
        """INSERT INTO sites (name, latitude, longitude, altitude, capacity_kw,
           surface_tilt, surface_azimuth, battery_capacity_kwh, export_limit_kw, hub_height_m)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, latitude, longitude, altitude, capacity_kw,
         surface_tilt, surface_azimuth, battery_capacity_kwh, export_limit_kw, hub_height_m),
    )
    conn.commit()
    site_id = cursor.lastrowid
    site = get_site(site_id, conn=conn)
    conn.close()
    return site


def get_site(site_id: int, conn=None) -> dict:
    close = False
    if conn is None:
        conn = get_db()
        close = True
    row = conn.execute("SELECT * FROM sites WHERE id = ?", (site_id,)).fetchone()
    if close:
        conn.close()
    if row is None:
        return None
    return dict(row)


def list_sites() -> list:
    conn = get_db()
    rows = conn.execute("SELECT * FROM sites ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_forecast(site_id: int, forecast_type: str, data: dict, metrics: dict = None) -> int:
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO forecasts (site_id, forecast_type, data_json, metrics_json) VALUES (?, ?, ?, ?)",
        (site_id, forecast_type, json.dumps(data), json.dumps(metrics) if metrics else None),
    )
    conn.commit()
    fid = cursor.lastrowid
    conn.close()
    return fid


def save_decision(site_id: int, schedule: list, explanation: dict = None) -> int:
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO decisions (site_id, schedule_json, explanation_json) VALUES (?, ?, ?)",
        (site_id, json.dumps(schedule), json.dumps(explanation) if explanation else None),
    )
    conn.commit()
    did = cursor.lastrowid
    conn.close()
    return did


init_db()
