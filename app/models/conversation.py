from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime,timezone
import uuid


class Conversation(SQLModel, table=True):
    __tablename__ = "conversation_rumr_app"  # Explicit table name as requested

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    conversation_type: str = Field(nullable=False, max_length=255)
    name: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    user_id: str = Field(nullable=False,foreign_key="user_rumr_app.UserID")
    group_image: Optional[str] = Field(default=None, max_length=255)