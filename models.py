"""SQLAlchemy ORM models for the Vehicle Auction System."""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean,
    DateTime, Numeric, ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    username   = Column(String(50), unique=True, nullable=False, index=True)
    email      = Column(String(120), unique=True, nullable=False)
    password   = Column(String(255), nullable=False)
    is_admin   = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    bids            = relationship("Bid", back_populates="user", cascade="all, delete-orphan")
    owned_vehicles  = relationship("Vehicle", back_populates="owner", foreign_keys="Vehicle.owner_id")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id             = Column(Integer, primary_key=True, index=True)
    title          = Column(String(120), nullable=False)
    description    = Column(Text)
    image_url      = Column(String(500), nullable=True)          # NULL → placeholder
    starting_price = Column(Numeric(12, 2), nullable=False)
    current_price  = Column(Numeric(12, 2), nullable=False)
    auction_end    = Column(DateTime, nullable=False)
    is_active      = Column(Boolean, default=True)
    owner_id       = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at     = Column(DateTime, server_default=func.now())

    bids  = relationship("Bid", back_populates="vehicle", cascade="all, delete-orphan")
    owner = relationship("User", back_populates="owned_vehicles", foreign_keys=[owner_id])


class Bid(Base):
    __tablename__ = "bids"

    id         = Column(Integer, primary_key=True, index=True)
    amount     = Column(Numeric(12, 2), nullable=False)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user    = relationship("User", back_populates="bids")
    vehicle = relationship("Vehicle", back_populates="bids")
