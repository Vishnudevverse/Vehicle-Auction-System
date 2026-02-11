"""Pydantic schemas for request / response validation."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


# ── User ──────────────────────────────────────
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Vehicle ───────────────────────────────────
class VehicleOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    starting_price: Decimal
    current_price: Decimal
    auction_end: datetime
    is_active: bool
    owner_id: Optional[int] = None

    class Config:
        from_attributes = True


# ── Bid ───────────────────────────────────────
class BidCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    vehicle_id: int


class BidOut(BaseModel):
    id: int
    amount: Decimal
    user_id: int
    vehicle_id: int
    created_at: datetime

    class Config:
        from_attributes = True
