"""Database models for BoxVault (Storage Boxes Management System).

Uses Reflex's built-in SQLModel configuration for SQLite persistence.
"""
from datetime import datetime
from typing import Optional
import reflex as rx
from sqlmodel import Field


class User(rx.Model, table=True):
    """User account model for standard members and administrators."""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, nullable=False)
    password_hash: str = Field(default="", nullable=False)
    is_admin: bool = Field(default=False, nullable=False)
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    )


class Box(rx.Model, table=True):
    """Physical storage box model owned by a user."""
    id: Optional[int] = Field(default=None, primary_key=True)
    label_name: str = Field(nullable=False, index=True)
    location: Optional[str] = Field(default="", nullable=True)
    user_id: int = Field(foreign_key="user.id", index=True, nullable=False)
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    )


class Item(rx.Model, table=True):
    """Individual item stored inside a storage box."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False, index=True)
    description: Optional[str] = Field(default="", nullable=True)
    quantity: int = Field(default=1, nullable=False)
    box_id: int = Field(foreign_key="box.id", index=True, nullable=False)
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    )
