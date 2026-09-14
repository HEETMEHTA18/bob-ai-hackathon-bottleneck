from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)

class UserLogin(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    company_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenRefresh(BaseModel):
    refresh_token: str

class SiteCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    site_type: str = Field("solar", pattern="^(solar|wind|hybrid)$")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    altitude: float = Field(0, ge=-500, le=9000)
    capacity_kw: float = Field(..., gt=0, lt=10_000_000)
    surface_tilt: float = Field(28, ge=0, le=90)
    surface_azimuth: float = Field(180, ge=0, le=360)
    battery_capacity_kwh: float = Field(0, ge=0)
    export_limit_kw: float = Field(0, ge=0)
    hub_height_m: float = Field(80, ge=0, le=500)

class SiteResponse(BaseModel):
    id: str
    name: str
    site_type: str
    latitude: float
    longitude: float
    altitude: float = 0
    capacity_kw: float
    battery_capacity_kwh: float
    export_limit_kw: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ScenarioRequest(BaseModel):
    cloud_cover_delta: float = Field(0, ge=-100, le=100)
    wind_speed_delta: float = Field(0, ge=-100, le=100)
    battery_soc_override: Optional[float] = Field(None, ge=0)
