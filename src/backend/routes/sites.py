from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from backend.database import get_db
from backend.models_db import User, Site
from backend.schemas import SiteCreate, SiteResponse
from backend.dependencies import get_current_user

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

router = APIRouter(prefix="/sites", tags=["Sites"])

@router.post("/", response_model=SiteResponse)
async def create_site(
    data: SiteCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    site = Site(
        owner_id=user.id,
        **data.model_dump(),
    )
    db.add(site)
    await db.flush()
    await db.refresh(site)
    return SiteResponse.model_validate(site)

@router.get("/", response_model=List[SiteResponse])
async def list_sites(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Site).where(Site.owner_id == user.id, Site.is_active == True)
    )
    sites = result.scalars().all()
    return [SiteResponse.model_validate(s) for s in sites]

@router.get("/{site_id}", response_model=SiteResponse)
async def get_site(
    site_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Site).where(Site.id == site_id, Site.owner_id == user.id)
    )
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return SiteResponse.model_validate(site)

@router.delete("/{site_id}")
async def delete_site(
    site_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Site).where(Site.id == site_id, Site.owner_id == user.id)
    )
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    site.is_active = False
    return {"message": "Site deleted"}

@router.post("/{site_id}/upload")
async def upload_csv(
    site_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Site).where(Site.id == site_id, Site.owner_id == user.id)
    )
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    import pandas as pd
    import io
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
    df = pd.read_csv(io.BytesIO(content))
    if len(df) > 1_000_000:
        raise HTTPException(status_code=413, detail="Too many rows (max 1,000,000)")

    if "timestamp" not in df.columns and "date" in df.columns:
        df.rename(columns={"date": "timestamp"}, inplace=True)

    return {"rows": len(df), "columns": list(df.columns), "site_id": str(site_id)}
