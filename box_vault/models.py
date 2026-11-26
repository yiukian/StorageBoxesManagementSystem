"""Database models and view schemas for BoxVault (Storage Boxes Management System).

Uses SQLModel for SQLite persistence and Pydantic for strongly-typed UI view structures.
Supports multi-user box sharing (BoxAccess link table) and soft-delete box archiving.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship


# ==============================================================================
# Database Persistence Entities (SQLModel)
# ==============================================================================

class BoxAccess(SQLModel, table=True):
    """Many-to-Many association model linking users with shared boxes."""
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    box_id: Optional[int] = Field(default=None, foreign_key="box.id", primary_key=True)


class User(SQLModel, table=True):
    """User account model for standard members and administrators."""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, nullable=False)
    password_hash: str = Field(default="", nullable=False)
    is_admin: bool = Field(default=False, nullable=False)
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    )

    # SQLModel Relationships
    owned_boxes: List["Box"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    shared_boxes: List["Box"] = Relationship(
        back_populates="shared_users",
        link_model=BoxAccess
    )


class Box(SQLModel, table=True):
    """Physical storage box model with ownership, sharing, and soft-delete archiving."""
    id: Optional[int] = Field(default=None, primary_key=True)
    label_name: str = Field(nullable=False, index=True)
    location: Optional[str] = Field(default="", nullable=True)
    owner_id: int = Field(foreign_key="user.id", index=True, nullable=False)
    is_public: bool = Field(default=True, nullable=False)
    is_archived: bool = Field(default=False, nullable=False)
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    )

    # SQLModel Relationships
    owner: Optional[User] = Relationship(back_populates="owned_boxes")
    shared_users: List[User] = Relationship(
        back_populates="shared_boxes",
        link_model=BoxAccess
    )
    items: List["Item"] = Relationship(
        back_populates="box",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
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

    # SQLModel Relationship
    box: Optional[Box] = Relationship(back_populates="items")


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
    owner_id: int
    owner_username: str = ""
    is_public: bool = True
    is_archived: bool = False
    item_count: int = 0
    box_items: List[ItemView] = []
    access_type: str = "Public"  # "Public", "Shared", or "Private"
    shared_with_usernames: str = ""
    is_owner: bool = False


class UserView(BaseModel):
    """View model for user accounts rendered in the admin panel."""
    id: int
    username: str
    is_admin: bool = False
    created_at: str = ""
    box_count: int = 0
    item_count: int = 0
