"""Crop master data."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.db import list_crops

router = APIRouter(prefix="/api/crops", tags=["crops"])


class CropOut(BaseModel):
    id: str
    name: str
    unit: str


@router.get("", response_model=list[CropOut])
async def get_crops() -> list[CropOut]:
    """All crops the platform tracks (dropdown/reference data for the frontend)."""
    crops = await list_crops()
    return [CropOut(**c) for c in crops]
