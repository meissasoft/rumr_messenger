from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid


class ConversationParticipant(SQLModel, table=True):
    __tablename__ = "conversation_participants_rumr_app"  # Explicit table name as requested

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    conversation_id: str = Field(nullable=False, foreign_key="conversation_rumr_app.id")
    user_id: str = Field(nullable=False, foreign_key="user_rumr_app.UserID")
    joined_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted: Optional[bool] = Field(default=False)
    deleted_at: Optional[datetime] = Field(default=None)
    is_conversation_mute: Optional[bool] = Field(default=False)
    is_conversation_pin: Optional[bool] = Field(default=False)