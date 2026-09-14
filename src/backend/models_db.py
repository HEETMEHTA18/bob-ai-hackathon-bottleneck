import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Boolean, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.database import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

class SiteType(str, enum.Enum):
    SOLAR = "solar"
    WIND = "wind"
    HYBRID = "hybrid"

def gen_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    company_name = Column(String(255))
    role = Column(String(20), default=UserRole.VIEWER.value)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sites = relationship("Site", back_populates="owner")

class Site(Base):
    __tablename__ = "sites"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    site_type = Column(String(20), default=SiteType.SOLAR.value)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, default=0)
    capacity_kw = Column(Float, nullable=False)
    surface_tilt = Column(Float, default=28)
    surface_azimuth = Column(Float, default=180)
    battery_capacity_kwh = Column(Float, default=0)
    export_limit_kw = Column(Float, default=0)
    hub_height_m = Column(Float, default=80)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="sites")
    forecasts = relationship("Forecast", back_populates="site")
    weather_data = relationship("WeatherData", back_populates="site")
    anomalies = relationship("Anomaly", back_populates="site")

class WeatherData(Base):
    __tablename__ = "weather_data"
    __table_args__ = (
        UniqueConstraint("site_id", "timestamp", name="uq_weather_site_timestamp"),
    )

    id = Column(String(36), primary_key=True, default=gen_uuid)
    site_id = Column(String(36), ForeignKey("sites.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    ghi = Column(Float)
    dni = Column(Float)
    dhi = Column(Float)
    temperature = Column(Float)
    wind_speed = Column(Float)
    wind_direction = Column(Float)
    humidity = Column(Float)
    cloud_cover = Column(Float)
    pressure = Column(Float)
    source = Column(String(50), default="open-meteo")
    created_at = Column(DateTime, default=datetime.utcnow)

    site = relationship("Site", back_populates="weather_data")

class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    site_id = Column(String(36), ForeignKey("sites.id"), nullable=False)
    forecast_type = Column(String(50), nullable=False)
    horizon_hours = Column(Integer, default=24)
    data_json = Column(Text)
    metrics_json = Column(Text)
    model_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    site = relationship("Site", back_populates="forecasts")

class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    site_id = Column(String(36), ForeignKey("sites.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    anomaly_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    metric = Column(String(100))
    value = Column(Float)
    expected_value = Column(Float)
    description = Column(Text)
    auto_fixed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    site = relationship("Site", back_populates="anomalies")

class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    model_name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    metrics_json = Column(Text)
    artifact_path = Column(String(500))
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
