"""Database models and view schemas for BoxVault (Storage Boxes Management System).

Uses SQLModel for SQLite persistence and Pydantic for strongly-typed UI view structures.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from sqlmodel import SQLModel, Field


# ==============================================================================
# Database Persistence Entities (SQLModel)
# ==============================================================================

class User(SQLModel, table=True):
    """User account model for standard members and administrators."""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, nullable=False)
    password_hash: str = Field(default="", nullable=False)
    is_admin: bool = Field(default=False, nullable=False)
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    )


class Box(SQLModel, table=True):
    """Physical storage box model owned by a user."""
    id: Optional[int] = Field(default=None, primary_key=True)
    label_name: str = Field(nullable=False, index=True)
    location: Optional[str] = Field(default="", nullable=True)
    user_id: int = Field(foreign_key="user.id", index=True, nullable=False)
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    )


class Item(SQLModel, table=True):
    """Individual item stored inside a storage box."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False, index=True)
    description: Optional[str] = Field(default="", nullable=True)
    quantity: int = Field(default=1, nullable=False)
    box_id: int = Field(foreign_key="box.id", index=True, nullable=False)
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    )


# ==============================================================================
# Strongly Typed UI View Models (Ensures type safety in rx.foreach)
# ==============================================================================

class ItemView(BaseModel):
    """View model for items rendered inside box cards."""
    id: int
    name: str
    quantity: int = 1
    description: str = ""
    box_id: int


class BoxView(BaseModel):
    """View model for physical storage boxes rendered in the grid."""
    id: int
    label_name: str
    location: str = "General Storage"
    item_count: int = 0
    box_items: List[ItemView] = []


class UserView(BaseModel):
    """View model for user accounts rendered in the admin panel."""
    id: int
    username: str
    is_admin: bool = False
    created_at: str = ""
    box_count: int = 0
    item_count: int = 0
